"""CLI interface for geoagent."""
import os
import sys
import click
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from threading import Lock

from geoagent.config import Config
from geoagent.pipeline import Pipeline
from geoagent.geo.rules import GEORules
from geoagent.db.connection import Database
from geoagent.db.schema import initialize_schema
from geoagent.prompts.registry import PromptRegistry
from geoagent.admin.settings import SiteSettings


DEFAULT_CONFIG_PATH = os.path.expanduser("~/.geoagent/config.yaml")


def ensure_database(db_path: str = None):
    """Ensure database is initialized with schema and default templates."""
    config = load_config()
    db = Database.get_instance(db_path or config.db_path)
    conn = db.get_connection()
    initialize_schema(conn)
    # Initialize default templates after schema
    from geoagent.prompts.registry import PromptRegistry
    registry = PromptRegistry(db)
    registry.initialize_default_templates()
    return db


def load_config() -> Config:
    """Load configuration from default or custom path."""
    if os.path.exists(DEFAULT_CONFIG_PATH):
        return Config.from_file(DEFAULT_CONFIG_PATH)
    return Config.default()


@click.group()
@click.version_option(version="0.1.0")
def cli():
    """GeoAgent - GEO-optimized article transformation CLI."""
    pass


@cli.command()
@click.option('--db-path', default=None, help='Path to SQLite database')
def init_db(db_path):
    """Initialize the database with all tables and default prompts."""
    db = ensure_database(db_path)
    registry = PromptRegistry(db)
    registry.initialize_default_templates()
    click.echo("Database initialized with schema and default prompts.")


# ---- Prompts command group ----
@cli.group('prompts')
def prompts_group():
    """Prompt template management."""
    pass


@prompts_group.command('list')
@click.option('--db-path', default=None, help='Path to SQLite database')
def prompts_list(db_path):
    """List all prompt templates."""
    db = Database.get_instance(db_path)
    registry = PromptRegistry(db)
    templates = registry.list_templates()
    if not templates:
        click.echo("No prompt templates found. Run 'geoagent init-db' first.")
        return
    for t in templates:
        click.echo(f"  [{t.type}] {t.name}")


@prompts_group.command('show')
@click.argument('name')
@click.option('--db-path', default=None, help='Path to SQLite database')
def prompts_show(name, db_path):
    """Show a prompt template by name."""
    db = Database.get_instance(db_path)
    registry = PromptRegistry(db)
    template = registry.get_template(name)
    if not template:
        click.echo(f"Template not found: {name}")
        sys.exit(1)
    click.echo(f"Name: {template.name}")
    click.echo(f"Type: {template.type}")
    click.echo(f"Variables: {template.variables or '(none)'}")
    click.echo(f"---\n{template.content}")


@prompts_group.command('render')
@click.argument('name')
@click.option('--var', multiple=True, help='Variables in key=value format')
@click.option('--db-path', default=None, help='Path to SQLite database')
def prompts_render(name, var, db_path):
    """Render a prompt template with variables."""
    db = Database.get_instance(db_path)
    registry = PromptRegistry(db)
    template = registry.get_template(name)
    if not template:
        click.echo(f"Template not found: {name}")
        sys.exit(1)
    kwargs = {}
    for v in var:
        if '=' in v:
            k, val = v.split('=', 1)
            kwargs[k.strip()] = val.strip()
    rendered = registry.render(template, **kwargs)
    click.echo(rendered)


# ---- Article command group ----
@cli.group('article')
def article_group():
    """Article management."""
    pass


@article_group.command('new')
@click.argument('title')
@click.option('--content', default='', help='Article content')
@click.option('--category-id', default=1, help='Category ID')
@click.option('--author-id', default=1, help='Author ID')
@click.option('--keyword', default='', help='Original keyword')
@click.option('--db-path', default=None, help='Path to SQLite database')
def article_new(title, content, category_id, author_id, keyword, db_path):
    """Create a new article."""
    from geoagent.articles.models import Article
    import datetime
    slug = title.lower().replace(' ', '-')
    db = Database.get_instance(db_path)
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """INSERT INTO articles (title, slug, content, category_id, author_id, original_keyword, status, is_ai_generated, created_at, updated_at)
           VALUES (?, ?, ?, ?, ?, ?, 'draft', 1, datetime('now'), datetime('now'))""",
        (title, slug, content, category_id, author_id, keyword),
    )
    conn.commit()
    click.echo(f"Created article id={cursor.lastrowid}: {title}")


@article_group.command('list')
@click.option('--status', default=None, help='Filter by status')
@click.option('--db-path', default=None, help='Path to SQLite database')
def article_list(status, db_path):
    """List articles."""
    db = Database.get_instance(db_path)
    conn = db.get_connection()
    cursor = conn.cursor()
    if status:
        cursor.execute("SELECT * FROM articles WHERE status = ? AND deleted_at IS NULL ORDER BY created_at DESC", (status,))
    else:
        cursor.execute("SELECT * FROM articles WHERE deleted_at IS NULL ORDER BY created_at DESC")
    rows = cursor.fetchall()
    if not rows:
        click.echo("No articles found.")
        return
    for row in rows:
        click.echo(f"  [{row['status']}] id={row['id']} - {row['title']}")


@article_group.command('publish')
@click.argument('article_id', type=int)
@click.option('--db-path', default=None, help='Path to SQLite database')
def article_publish(article_id, db_path):
    """Publish an article."""
    db = Database.get_instance(db_path)
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        "UPDATE articles SET status = 'published', published_at = datetime('now'), updated_at = datetime('now') WHERE id = ?",
        (article_id,),
    )
    conn.commit()
    click.echo(f"Published article id={article_id}")


@article_group.command('hot')
@click.argument('article_id', type=int)
@click.option('--enable/--disable', default=True)
@click.option('--db-path', default=None, help='Path to SQLite database')
def article_hot(article_id, enable, db_path):
    """Set or unset hot flag on an article."""
    db = Database.get_instance(db_path)
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE articles SET is_hot = ? WHERE id = ?", (1 if enable else 0, article_id))
    conn.commit()
    action = "enabled" if enable else "disabled"
    click.echo(f"Hot flag {action} for article id={article_id}")


@article_group.command('featured')
@click.argument('article_id', type=int)
@click.option('--enable/--disable', default=True)
@click.option('--db-path', default=None, help='Path to SQLite database')
def article_featured(article_id, enable, db_path):
    """Set or unset featured flag on an article."""
    db = Database.get_instance(db_path)
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("UPDATE articles SET is_featured = ? WHERE id = ?", (1 if enable else 0, article_id))
    conn.commit()
    action = "enabled" if enable else "disabled"
    click.echo(f"Featured flag {action} for article id={article_id}")


# ---- Task command group ----
@cli.group('task')
def task_group():
    """Task management."""
    pass


@task_group.command('list')
@click.option('--db-path', default=None, help='Path to SQLite database')
def task_list(db_path):
    """List all tasks."""
    db = Database.get_instance(db_path)
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT * FROM tasks ORDER BY name")
    rows = cursor.fetchall()
    if not rows:
        click.echo("No tasks found.")
        return
    for row in rows:
        click.echo(f"  [{row['status']}] id={row['id']} - {row['name']} (articles: {row['created_count']}/{row['article_limit']})")


@task_group.command('run')
@click.argument('task_id', type=int)
@click.option('--db-path', default=None, help='Path to SQLite database')
def task_run(task_id, db_path):
    """Start a task in background."""
    db = Database.get_instance(db_path)
    from geoagent.tasks.scheduler import TaskRunner
    runner = TaskRunner(db)
    runner.start_task(task_id)
    click.echo(f"Task {task_id} started in background.")


@task_group.command('stop')
@click.argument('task_id', type=int)
@click.option('--db-path', default=None, help='Path to SQLite database')
def task_stop(task_id, db_path):
    """Stop a running task."""
    db = Database.get_instance(db_path)
    from geoagent.tasks.scheduler import TaskRunner
    runner = TaskRunner(db)
    runner.stop_task(task_id)
    click.echo(f"Task {task_id} stopped.")


# ---- URL Import command group ----
@cli.group('url-import')
def url_import_group():
    """URL import pipeline."""
    pass


@url_import_group.command('submit')
@click.argument('url')
@click.option('--created-by', default='', help='Created by user')
@click.option('--db-path', default=None, help='Path to SQLite database')
def url_import_submit(url, created_by, db_path):
    """Submit a URL for import."""
    db = Database.get_instance(db_path)
    ensure_database(db_path)
    from geoagent.url_import.job import ImportJobManager
    manager = ImportJobManager(db)
    job_id = manager.create_job(url, created_by)
    click.echo(f"Created import job id={job_id}: {url}")


@url_import_group.command('status')
@click.argument('job_id', type=int)
@click.option('--db-path', default=None, help='Path to SQLite database')
def url_import_status(job_id, db_path):
    """Check URL import job status."""
    db = Database.get_instance(db_path)
    from geoagent.url_import.job import ImportJobManager
    manager = ImportJobManager(db)
    job = manager.get_job(job_id)
    if not job:
        click.echo(f"Job not found: {job_id}")
        sys.exit(1)
    click.echo(f"Job {job_id}: {job.status}")
    click.echo(f"  Step: {job.current_step} ({job.progress_percent}%)")
    click.echo(f"  URL: {job.url}")
    if job.error_message:
        click.echo(f"  Error: {job.error_message}")


@url_import_group.command('logs')
@click.argument('job_id', type=int)
@click.option('--db-path', default=None, help='Path to SQLite database')
def url_import_logs(job_id, db_path):
    """Show URL import job logs."""
    db = Database.get_instance(db_path)
    from geoagent.url_import.job import ImportJobManager
    manager = ImportJobManager(db)
    logs = manager.get_job_logs(job_id)
    if not logs:
        click.echo("No logs found.")
        return
    for log in logs:
        click.echo(f"  [{log.level}] {log.step}: {log.message}")


# ---- Admin command group ----
@cli.group('admin')
def admin_group():
    """Admin settings."""
    pass


@admin_group.command('settings')
@click.option('--key', default=None, help='Setting key')
@click.option('--value', default=None, help='Setting value (to set)')
@click.option('--db-path', default=None, help='Path to SQLite database')
def admin_settings(key, value, db_path):
    """Get or set site settings."""
    db = Database.get_instance(db_path)
    settings = SiteSettings(db)
    if value is not None:
        settings.set(key, value)
        click.echo(f"Set {key} = {value}")
    else:
        val = settings.get(key)
        click.echo(f"{key} = {val}")


# ---- Title command group ----
@cli.group('title')
def title_group():
    """Title generation."""
    pass


@title_group.command('generate')
@click.option('--keyword', '-k', multiple=True, help='Keywords for title generation')
@click.option('--style', default='professional', type=click.Choice(['professional', 'attractive', 'seo', 'creative', 'question']), help='Title generation style')
@click.option('--count', default=3, help='Number of titles to generate')
@click.option('--model', default=None, help='Model to use')
@click.option('--db-path', default=None, help='Path to SQLite database')
def title_generate(keyword, style, count, model, db_path):
    """Generate AI titles in specified style."""
    config = load_config()
    provider, model_name = parse_model_option(model or config.default_model)
    api_key = os.environ.get(
        config.models.get(provider, config.models.get('minimax')).api_key_env,
        os.environ.get('ANTHROPIC_API_KEY', '')
    )
    if not api_key:
        click.echo("Error: API key not found.", err=True)
        sys.exit(1)
    model_client = config.get_model_client(provider, api_key)

    from geoagent.titles.generator import TitleGenerator
    gen = TitleGenerator(model_client)
    keywords = list(keyword) if keyword else ["默认主题"]
    result = gen.generate(keywords, style, count)
    click.echo(f"Style: {result.style} ({'AI' if not result.used_mock else 'Mock'})")
    for t in result.titles:
        click.echo(f"  - {t}")


# ---- Article generate command ----
@cli.group('article')
def article_generate_group():
    """Article generation."""
    pass


@article_generate_group.command('generate')
@click.argument('task_id', type=int)
@click.option('--keyword', default=None, help='Override keyword')
@click.option('--knowledge-base-id', type=int, default=None, help='Knowledge base ID for RAG')
@click.option('--style', default='professional', type=click.Choice(['professional', 'attractive', 'seo', 'creative', 'question']), help='Title style')
@click.option('--model', default=None, help='Model to use')
@click.option('--db-path', default=None, help='Path to SQLite database')
def article_generate_cmd(task_id, keyword, knowledge_base_id, style, model, db_path):
    """Generate an article for a task using full GEOFlow pipeline."""
    ensure_database(db_path)
    config = load_config()
    provider, model_name = parse_model_option(model or config.default_model)
    api_key = os.environ.get(
        config.models.get(provider, config.models.get('minimax')).api_key_env,
        os.environ.get('ANTHROPIC_API_KEY', '')
    )
    if not api_key:
        click.echo("Error: API key not found.", err=True)
        sys.exit(1)
    model_client = config.get_model_client(provider, api_key)
    db = Database.get_instance(db_path or config.db_path)

    from geoagent.articles.generator import ArticleGenerator
    gen = ArticleGenerator(db, model_client)
    result = gen.generate(task_id, keyword=keyword, knowledge_base_id=knowledge_base_id, style=style)
    if result.success:
        click.echo(f"Generated article id={result.article_id}: {result.title}")
    else:
        click.echo(f"Failed: {result.error}", err=True)
        sys.exit(1)


# ---- Worker command ----
@cli.command('worker')
@click.option('--task-id', type=int, default=None, help='Run a specific task')
@click.option('--poll-interval', default=60, help='Poll interval in seconds')
@click.option('--model', default=None, help='Model to use')
@click.option('--db-path', default=None, help='Path to SQLite database')
def worker_cmd(task_id, poll_interval, model, db_path):
    """Run the GEOFlow worker loop (background task execution)."""
    ensure_database(db_path)
    config = load_config()
    provider, model_name = parse_model_option(model or config.default_model)
    api_key = os.environ.get(
        config.models.get(provider, config.models.get('minimax')).api_key_env,
        os.environ.get('ANTHROPIC_API_KEY', '')
    )
    if not api_key:
        click.echo("Error: API key not found.", err=True)
        sys.exit(1)
    model_client = config.get_model_client(provider, api_key)
    db = Database.get_instance(db_path or config.db_path)

    from geoagent.tasks.scheduler import TaskScheduler, TaskRunner
    scheduler = TaskScheduler(db)
    runner = TaskRunner(db, model_client)

    click.echo("GEOFlow Worker started.")
    if task_id:
        click.echo(f"Running task {task_id} only")
        runner.start_task(task_id)
    else:
        click.echo(f"Polling every {poll_interval}s")
        while True:
            scheduler.recover_stale_jobs()
            enqueued = scheduler.poll_and_enqueue()
            for tid in enqueued:
                click.echo(f"Enqueued task {tid}")
                runner.start_task(tid)
            import time
            time.sleep(poll_interval)


def process_single_file(args, verbose=False):
    """Process a single file. Returns (success, filename, output_count, error)."""
    md_file, pipeline, output_dir, target_languages, resume, source_root = args

    try:
        output_files = pipeline.transform(str(md_file), output_dir, target_languages, resume, source_root=source_root)
        return (True, md_file.name, len(output_files), None)
    except Exception as e:
        return (False, md_file.name, 0, str(e))


@cli.command()
@click.argument('input_path', type=click.Path(exists=True))
@click.option('--model', default=None, help='Model to use (provider/model)')
@click.option('--output-dir', default='./output', help='Output directory')
@click.option('--geo-rules', default=None, help='Custom GEO rules file')
@click.option('--lang', default='en', help='Target languages (comma-separated)')
@click.option('--verbose', is_flag=True, help='Show detailed logs')
@click.option('--recursive', '-r', is_flag=True, help='Process directories recursively')
@click.option('--concurrency', '-c', default=4, help='Number of concurrent threads (default: 4)')
@click.option('--resume', is_flag=True, help='Resume interrupted job - skip completed language outputs')
@click.option('--geo-prompt', default=None, help='GEO prompt template name (e.g., "GEO Marketing · Trust-Based Article Generation (English)")')
@click.option('--template-type', default='trust', type=click.Choice(['trust', 'ranking']), help='Template type: trust or ranking')
def transform(input_path, model, output_dir, geo_rules, lang, verbose, recursive, concurrency, resume, geo_prompt, template_type):
    """Transform a markdown article or directory of articles into GEO-optimized versions."""
    config = load_config()
    ensure_database()

    provider, model_name = parse_model_option(model or config.default_model)

    api_key = os.environ.get(
        config.models.get(provider, config.models.get('minimax')).api_key_env,
        os.environ.get('ANTHROPIC_API_KEY', '')
    )

    if not api_key:
        click.echo("Error: API key not found. Set ANTHROPIC_API_KEY environment variable.", err=True)
        sys.exit(1)

    model_client = config.get_model_client(provider, api_key)

    rules_path = geo_rules or config.geo_rules_path or "shared/rubrics/content-quality-rubric.md"
    geo_rules_obj = GEORules.from_rubric_file(rules_path)

    pipeline = Pipeline(
        model_client=model_client,
        translation_client=model_client,
        geo_rules=geo_rules_obj,
        default_model=model_name,
        max_tokens_translate=config.max_tokens_translate,
        max_tokens_geo=config.max_tokens_geo,
        max_tokens_understand=config.max_tokens_understand,
        geo_prompt_template=geo_prompt,
        db_path=config.db_path,
        template_type=template_type
    )

    target_languages = [l.strip() for l in lang.split(',')]

    input_path_obj = Path(input_path)

    if input_path_obj.is_dir():
        md_files = find_markdown_files(input_path_obj, recursive)
        if not md_files:
            click.echo(f"No markdown files found in {input_path}")
            return

        click.echo(f"Found {len(md_files)} markdown file(s) to process")
        click.echo(f"Model: {provider}/{model_name}")
        click.echo(f"Target languages: {target_languages}")
        click.echo(f"Concurrency: {concurrency}")
        click.echo(f"Output directory: {output_dir}")
        click.echo("")

        total_files = 0
        success_count = 0
        failed_count = 0

        # Prepare work items
        source_root = str(input_path_obj.resolve())
        work_items = [(f, pipeline, output_dir, target_languages, resume, source_root) for f in md_files]

        with ThreadPoolExecutor(max_workers=concurrency) as executor:
            futures = {executor.submit(process_single_file, item, verbose): item[0] for item in work_items}

            for future in as_completed(futures):
                success, filename, count, error = future.result()
                if success:
                    success_count += 1
                    total_files += count
                    click.echo(f"  ✓ {filename} → {count} files")
                else:
                    failed_count += 1
                    click.echo(f"  ✗ {filename} failed: {error}", err=True)

        click.echo(f"\nTotal: {total_files} files generated ({success_count} succeeded, {failed_count} failed)")
    else:
        if verbose:
            click.echo(f"Input: {input_path}")
            click.echo(f"Model: {provider}/{model_name}")
            click.echo(f"Target languages: {target_languages}")
            click.echo(f"Output directory: {output_dir}")

        try:
            output_files = pipeline.transform(input_path, output_dir, target_languages, resume)
            click.echo(f"\nGenerated {len(output_files)} files:")
            for f in output_files:
                click.echo(f"  - {f}")
        except Exception as e:
            click.echo(f"Error: {e}", err=True)
            sys.exit(1)


def find_markdown_files(directory: Path, recursive: bool) -> list[Path]:
    """Find all markdown files in a directory."""
    if recursive:
        return sorted(directory.rglob("*.md"))
    return sorted(directory.glob("*.md"))


def parse_model_option(model_str: str) -> tuple[str, str]:
    """Parse model string like 'minimax/MiniMax-M2.7' into (provider, model)."""
    if '/' in model_str:
        provider, model = model_str.split('/', 1)
        return provider, model
    return "minimax", model_str


def main():
    cli()


if __name__ == "__main__":
    main()
