"""Article generator combining the full GEOFlow worker execution flow."""
import datetime
from dataclasses import dataclass
from typing import Optional

from geoagent.db.connection import Database
from geoagent.knowledge.retriever import KnowledgeRetriever
from geoagent.knowledge.embedder import Embedder
from geoagent.prompts.registry import PromptRegistry
from geoagent.titles.generator import TitleGenerator
from geoagent.images.inserter import insert_images_by_paragraph_interval, markdown_image, select_images_random
from geoagent.models.client import ModelClient


@dataclass
class GenerationResult:
    article_id: int
    title: str
    content: str
    model_used: str
    success: bool
    error: Optional[str] = None


class ArticleGenerator:
    """Generates articles following GEOFlow WorkerExecutionService flow.

    Steps:
    1. publishDueDraftArticle() — check if next_publish_at due
    2. getGenerationBlockReason() — check limits
    3. pickTitle() / pickAuthor() / pickCategory()
    4. resolveKnowledgeContext() — RAG retrieval
    5. buildContentPrompt() — render template with {{title}} {{keyword}} {{Knowledge}}
    6. generateContent() — call model
    7. insertTaskImagesIntoContent()
    8. buildExcerpt()
    9. Create Article record
    """

    def __init__(
        self,
        db: Optional[Database] = None,
        model_client: Optional[ModelClient] = None,
        db_path: Optional[str] = None
    ):
        self.db = db or Database.get_instance(db_path)
        self.model_client = model_client
        self.retriever = KnowledgeRetriever(self.db, Embedder(model_client))
        self.registry = PromptRegistry(self.db)
        self.title_gen = TitleGenerator(model_client)

    def _conn(self):
        return self.db.get_connection()

    def generate(
        self,
        task_id: int,
        keyword: Optional[str] = None,
        knowledge_base_id: Optional[int] = None,
        style: str = "professional"
    ) -> GenerationResult:
        """Full article generation for a task."""
        conn = self._conn()
        cursor = conn.cursor()

        # 1. Publish due drafts first
        self._publish_due_drafts(cursor, task_id)

        # 2. Check generation limits
        block_reason = self._get_generation_block_reason(cursor, task_id)
        if block_reason:
            return GenerationResult(
                article_id=0, title="", content="", model_used="",
                success=False, error=block_reason
            )

        # 3. Pick title (lowest used_count)
        title_row = cursor.execute(
            """SELECT t.id, t.title, t.keyword, t.is_ai_generated, t.used_count
               FROM titles t
               JOIN title_libraries tl ON t.library_id = tl.id
               WHERE tl.id = (SELECT title_library_id FROM tasks WHERE id = ?)
               LIMIT 5"""
        ).fetchall()
        if not title_row:
            return GenerationResult(
                article_id=0, title="", content="", model_used="",
                success=False, error="No titles available"
            )

        # Pick the one with lowest used_count
        title_record = min(title_row, key=lambda r: r["used_count"])
        title_text = title_record["title"]
        title_kw = title_record["keyword"] or keyword or ""

        # 4. Pick author
        author_id = cursor.execute(
            "SELECT author_id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        author_id = author_id["author_id"] if author_id else 1

        # 5. Pick category
        category_id = cursor.execute(
            "SELECT fixed_category_id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        category_id = category_id["fixed_category_id"] if category_id else 1

        # 6. Get knowledge context (RAG)
        knowledge_context = ""
        kb_id = knowledge_base_id or cursor.execute(
            "SELECT knowledge_base_id FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if kb_id and kb_id["knowledge_base_id"]:
            query = f"{title_text}\n{title_kw}"
            knowledge_context = self.retriever.fetch_knowledge_context(
                kb_id["knowledge_base_id"], query, limit=4, max_chars=2400
            )

        # 7. Build prompt
        task = cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return GenerationResult(
                article_id=0, title="", content="", model_used="",
                success=False, error="Task not found"
            )

        prompt = cursor.execute(
            "SELECT * FROM prompts WHERE id = ?", (task["prompt_id"],)
        ).fetchone()
        if not prompt:
            return GenerationResult(
                article_id=0, title="", content="", model_used="",
                success=False, error="Prompt not found"
            )

        prompt_template = self.registry.get_template(prompt["name"])
        if not prompt_template:
            return GenerationResult(
                article_id=0, title="", content="", model_used="",
                success=False, error=f"Prompt template not found: {prompt['name']}"
            )

        rendered_prompt = self.registry.render(
            prompt_template,
            title=title_text,
            keyword=title_kw,
            Knowledge=knowledge_context
        )

        # 8. Generate content
        try:
            content = self.model_client.complete(
                "generate",
                [{"role": "user", "content": rendered_prompt}],
                max_tokens=8192
            )
        except Exception as e:
            return GenerationResult(
                article_id=0, title="", content="", model_used="",
                success=False, error=f"Generation failed: {e}"
            )

        # 9. Insert images if task has image_library_id
        image_count = task["image_count"] or 0
        if image_count > 0 and task["image_library_id"]:
            images = select_images_random(conn, task["image_library_id"], image_count)
            md_images = [
                markdown_image(img["file_path"], img["original_name"])
                for img in images
            ]
            if md_images:
                content = insert_images_by_paragraph_interval(content, md_images)

        # 10. Build excerpt (first 200 chars)
        excerpt = content[:200].replace('\n', ' ').strip() + "..."

        # 11. Create article
        slug = title_text.lower().replace(' ', '-').replace('/', '-')[:100]
        now = datetime.datetime.now().isoformat()
        cursor.execute(
            """INSERT INTO articles
               (title, slug, excerpt, content, category_id, author_id, task_id,
                original_keyword, status, review_status, is_ai_generated, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, 'draft', 'pending', 1, ?, ?)""",
            (title_text, slug, excerpt, content, category_id, author_id, task_id, title_kw, now, now)
        )
        article_id = cursor.lastrowid

        # 12. Update title used_count
        cursor.execute(
            "UPDATE titles SET used_count = used_count + 1, usage_count = usage_count + 1 WHERE id = ?",
            (title_record["id"],)
        )

        # 13. Update task counters
        cursor.execute(
            "UPDATE tasks SET created_count = created_count + 1 WHERE id = ?",
            (task_id,)
        )

        # 14. Set next_publish_at
        publish_interval = task["publish_interval"] or 3600
        next_publish = datetime.datetime.now() + datetime.timedelta(seconds=publish_interval)
        cursor.execute(
            "UPDATE tasks SET next_publish_at = ? WHERE id = ?",
            (next_publish.isoformat(), task_id)
        )

        conn.commit()

        return GenerationResult(
            article_id=article_id,
            title=title_text,
            content=content,
            model_used="",
            success=True
        )

    def _publish_due_drafts(self, cursor, task_id: int):
        """Find and publish oldest approved draft if next_publish_at is due."""
        task = cursor.execute(
            "SELECT next_publish_at, published_count FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if not task or not task["next_publish_at"]:
            return

        next_publish = datetime.datetime.fromisoformat(task["next_publish_at"].replace(" ", "T"))
        if next_publish > datetime.datetime.now():
            return  # not yet due

        # Find oldest approved draft
        draft = cursor.execute(
            """SELECT id FROM articles
               WHERE task_id = ? AND status = 'draft'
               AND review_status IN ('approved', 'auto_approved')
               ORDER BY created_at ASC LIMIT 1""",
            (task_id,)
        ).fetchone()
        if not draft:
            return

        now = datetime.datetime.now().isoformat()
        cursor.execute(
            "UPDATE articles SET status = 'published', published_at = ?, updated_at = ? WHERE id = ?",
            (now, now, draft["id"])
        )
        cursor.execute(
            "UPDATE tasks SET published_count = published_count + 1 WHERE id = ?",
            (task_id,)
        )
        # Advance next_publish_at
        interval = cursor.execute(
            "SELECT publish_interval FROM tasks WHERE id = ?", (task_id,)
        ).fetchone()
        if interval and interval["publish_interval"]:
            next_p = datetime.datetime.now() + datetime.timedelta(seconds=interval["publish_interval"])
            cursor.execute(
                "UPDATE tasks SET next_publish_at = ? WHERE id = ?",
                (next_p.isoformat(), task_id)
            )

    def _get_generation_block_reason(self, cursor, task_id: int) -> Optional[str]:
        """Check if generation is blocked by limits."""
        task = cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,)).fetchone()
        if not task:
            return "Task not found"

        article_limit = task["article_limit"] or task["draft_limit"] or 10
        if task["created_count"] >= article_limit:
            return "已达到文章总数上限"

        draft_count = cursor.execute(
            "SELECT COUNT(*) as c FROM articles WHERE task_id = ? AND status = 'draft'",
            (task_id,)
        ).fetchone()["c"]
        if draft_count >= (task["draft_limit"] or 10):
            return "草稿池已满，等待审核或按间隔发布"

        return None
