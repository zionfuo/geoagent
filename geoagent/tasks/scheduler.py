"""Task scheduling system for geoagent."""
from dataclasses import dataclass
from typing import Optional
from concurrent.futures import ThreadPoolExecutor
import threading
import datetime
import time
import logging


logger = logging.getLogger(__name__)


@dataclass
class Task:
    id: Optional[int] = None
    name: str = ""
    title_library_id: int = 0
    image_library_id: Optional[int] = None
    image_count: int = 1
    prompt_id: int = 0
    ai_model_id: int = 0
    author_id: Optional[int] = None
    need_review: int = 1
    publish_interval: int = 3600
    author_type: str = "random"
    custom_author_id: Optional[int] = None
    auto_keywords: int = 1
    auto_description: int = 1
    draft_limit: int = 10
    article_limit: int = 10
    is_loop: int = 0
    model_selection_mode: str = "fixed"
    status: str = "active"
    created_count: int = 0
    published_count: int = 0
    loop_count: int = 0
    knowledge_base_id: Optional[int] = None
    category_mode: str = "smart"
    fixed_category_id: Optional[int] = None
    last_run_at: Optional[str] = None
    next_run_at: Optional[str] = None
    next_publish_at: Optional[str] = None
    last_success_at: Optional[str] = None
    last_error_at: Optional[str] = None
    last_error_message: str = ""
    schedule_enabled: int = 1
    max_retry_count: int = 3
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class TaskRun:
    id: Optional[int] = None
    task_id: int = 0
    status: str = ""
    article_id: Optional[int] = None
    error_message: str = ""
    duration_ms: int = 0
    meta: str = ""
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: Optional[str] = None


class TaskScheduler:
    """Schedules tasks for execution."""

    def __init__(self, db):
        self.db = db

    def _conn(self):
        return self.db.get_connection()

    def schedule_next_run(self, task_id: int):
        """Calculate and set next_run_at based on last_run_at + publish_interval."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT last_run_at, publish_interval FROM tasks WHERE id = ?", (task_id,))
        row = cursor.fetchone()
        if row and row["last_run_at"]:
            last_run = datetime.datetime.fromisoformat(row["last_run_at"].replace(" ", "T"))
            next_run = last_run + datetime.timedelta(seconds=row["publish_interval"])
            cursor.execute(
                "UPDATE tasks SET next_run_at = ? WHERE id = ?",
                (next_run.isoformat(), task_id),
            )
            conn.commit()

    def get_pending_tasks(self) -> list[Task]:
        """Get all tasks that are due to run (or need publishing)."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """SELECT * FROM tasks
               WHERE status = 'active' AND schedule_enabled = 1
               AND (next_run_at IS NULL OR next_run_at <= datetime('now'))
               ORDER BY next_run_at LIMIT 10"""
        )
        rows = cursor.fetchall()
        return [Task(**dict(row)) for row in rows]

    def poll_and_enqueue(self) -> list[int]:
        """Poll for due tasks, advance next_run_at by 60s, return task IDs to enqueue."""
        conn = self._conn()
        cursor = conn.cursor()
        tasks = self.get_pending_tasks()
        enqueued = []
        for task in tasks:
            cursor.execute(
                "UPDATE tasks SET next_run_at = datetime('now', '+60 seconds') WHERE id = ?",
                (task.id,)
            )
            conn.commit()
            enqueued.append(task.id)
        return enqueued

    def recover_stale_jobs(self):
        """Reset stale pending/running task_runs older than 1 hour."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE task_runs SET status = 'failed', error_message = 'Stale job recovered'
               WHERE status IN ('pending', 'running')
               AND started_at < datetime('now', '-1 hour')"""
        )
        conn.commit()


class TaskRunner:
    """Runs tasks in background threads with full GEOFlow worker logic."""

    def __init__(self, db, model_client=None):
        self.db = db
        self.model_client = model_client
        self._executor = ThreadPoolExecutor(max_workers=4)
        self._running_tasks: dict[int, threading.Event] = {}

    def _conn(self):
        return self.db.get_connection()

    def start_task(self, task_id: int):
        """Start a task in a background thread."""
        stop_event = threading.Event()
        self._running_tasks[task_id] = stop_event
        self._executor.submit(self._run_task_loop, task_id, stop_event)

    def stop_task(self, task_id: int):
        """Stop a running task."""
        if task_id in self._running_tasks:
            self._running_tasks[task_id].set()
            del self._running_tasks[task_id]

    def _run_task_loop(self, task_id: int, stop_event: threading.Event):
        """Run task loop until stopped or limits reached."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM tasks WHERE id = ?", (task_id,))
        task = Task(**dict(cursor.fetchone()))

        while not stop_event.is_set():
            article_limit = max(1, task.article_limit or task.draft_limit or 10)
            if task.created_count >= article_limit and not task.is_loop:
                logger.info(f"Task {task_id}: article limit reached, stopping")
                break

            cursor.execute(
                "UPDATE tasks SET last_run_at = datetime('now') WHERE id = ?",
                (task_id,),
            )
            conn.commit()

            start = time.time()
            error_msg = None
            try:
                from geoagent.articles.generator import ArticleGenerator
                gen = ArticleGenerator(self.db, self.model_client)
                result = gen.generate(task_id)
                if not result.success:
                    error_msg = result.error
            except Exception as e:
                error_msg = str(e)

            duration_ms = int((time.time() - start) * 1000)

            # Record task run
            now_iso = datetime.datetime.now().isoformat()
            status = "failed" if error_msg else "success"
            cursor.execute(
                """INSERT INTO task_runs (task_id, status, article_id, error_message, duration_ms, started_at, finished_at, created_at)
                   VALUES (?, ?, ?, ?, ?, ?, ?, ?)""",
                (task_id, status, result.article_id if result.success else None,
                 error_msg or "", duration_ms, now_iso, now_iso, now_iso)
            )
            conn.commit()

            if error_msg:
                cursor.execute(
                    "UPDATE tasks SET last_error_at = ?, last_error_message = ? WHERE id = ?",
                    (now_iso, error_msg, task_id)
                )
                conn.commit()

            if task.is_loop == 0:
                break

            # Advance next_run_at before sleeping
            cursor.execute(
                "UPDATE tasks SET next_run_at = datetime('now', '+60 seconds') WHERE id = ?",
                (task_id,)
            )
            conn.commit()

            stop_event.wait(timeout=task.publish_interval)
