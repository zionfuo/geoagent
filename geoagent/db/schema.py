"""Database schema for geoagent.

Mirrors the GEOFlow Laravel migrations translated to SQLite syntax.
"""

import sqlite3

SCHEMA_TABLES = [
    # ai_models - Third-party LLM configuration
    """CREATE TABLE IF NOT EXISTS ai_models (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        version TEXT DEFAULT '',
        api_key TEXT NOT NULL,
        model_id TEXT NOT NULL,
        model_type TEXT DEFAULT 'chat',
        api_url TEXT DEFAULT 'https://api.deepseek.com',
        failover_priority INTEGER DEFAULT 100,
        daily_limit INTEGER DEFAULT 0,
        used_today INTEGER DEFAULT 0,
        total_used INTEGER DEFAULT 0,
        status TEXT DEFAULT 'active',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""",

    # prompts - Prompt templates
    """CREATE TABLE IF NOT EXISTS prompts (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL UNIQUE,
        type TEXT NOT NULL,
        content TEXT NOT NULL,
        variables TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""",

    # keyword_libraries - Keyword library collections
    """CREATE TABLE IF NOT EXISTS keyword_libraries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        keyword_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""",

    # keywords - Individual keywords within libraries
    """CREATE TABLE IF NOT EXISTS keywords (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        library_id INTEGER NOT NULL,
        keyword TEXT NOT NULL,
        used_count INTEGER DEFAULT 0,
        usage_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (library_id) REFERENCES keyword_libraries(id) ON DELETE CASCADE,
        UNIQUE(library_id, keyword)
    )""",

    # title_libraries - Title library collections
    """CREATE TABLE IF NOT EXISTS title_libraries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        title_count INTEGER DEFAULT 0,
        generation_type TEXT DEFAULT 'manual',
        keyword_library_id INTEGER,
        ai_model_id INTEGER,
        prompt_id INTEGER,
        generation_rounds INTEGER DEFAULT 1,
        is_ai_generated INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (keyword_library_id) REFERENCES keyword_libraries(id) ON DELETE SET NULL,
        FOREIGN KEY (ai_model_id) REFERENCES ai_models(id) ON DELETE SET NULL,
        FOREIGN KEY (prompt_id) REFERENCES prompts(id) ON DELETE SET NULL
    )""",

    # titles - Individual titles within libraries
    """CREATE TABLE IF NOT EXISTS titles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        library_id INTEGER NOT NULL,
        title TEXT NOT NULL,
        keyword TEXT DEFAULT '',
        is_ai_generated INTEGER DEFAULT 0,
        used_count INTEGER DEFAULT 0,
        usage_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (library_id) REFERENCES title_libraries(id) ON DELETE CASCADE
    )""",

    # image_libraries - Image library collections
    """CREATE TABLE IF NOT EXISTS image_libraries (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        image_count INTEGER DEFAULT 0,
        used_task_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""",

    # images - Image file metadata
    """CREATE TABLE IF NOT EXISTS images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        library_id INTEGER NOT NULL,
        filename TEXT NOT NULL,
        original_name TEXT NOT NULL,
        file_name TEXT NOT NULL DEFAULT '',
        file_path TEXT NOT NULL,
        file_size INTEGER DEFAULT 0,
        mime_type TEXT DEFAULT '',
        width INTEGER DEFAULT 0,
        height INTEGER DEFAULT 0,
        tags TEXT DEFAULT '',
        used_count INTEGER DEFAULT 0,
        usage_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (library_id) REFERENCES image_libraries(id) ON DELETE CASCADE
    )""",

    # knowledge_bases - Knowledge base documents
    """CREATE TABLE IF NOT EXISTS knowledge_bases (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        description TEXT DEFAULT '',
        content TEXT NOT NULL,
        character_count INTEGER DEFAULT 0,
        used_task_count INTEGER DEFAULT 0,
        file_type TEXT DEFAULT 'markdown',
        file_path TEXT DEFAULT '',
        word_count INTEGER DEFAULT 0,
        usage_count INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""",

    # knowledge_chunks - Knowledge base chunks (vector-ready)
    """CREATE TABLE IF NOT EXISTS knowledge_chunks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        knowledge_base_id INTEGER NOT NULL,
        chunk_index INTEGER NOT NULL,
        content TEXT NOT NULL,
        content_hash TEXT DEFAULT '',
        token_count INTEGER DEFAULT 0,
        embedding_json TEXT DEFAULT '',
        embedding_model_id INTEGER,
        embedding_dimensions INTEGER DEFAULT 0,
        embedding_provider TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE CASCADE,
        UNIQUE(knowledge_base_id, chunk_index)
    )""",

    # authors - Article author display information
    """CREATE TABLE IF NOT EXISTS authors (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        bio TEXT DEFAULT '',
        email TEXT DEFAULT '',
        avatar TEXT DEFAULT '',
        website TEXT DEFAULT '',
        social_links TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""",

    # categories - Site article categories
    """CREATE TABLE IF NOT EXISTS categories (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        description TEXT DEFAULT '',
        sort_order INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now'))
    )""",

    # tasks - Content generation tasks
    """CREATE TABLE IF NOT EXISTS tasks (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        name TEXT NOT NULL,
        title_library_id INTEGER NOT NULL,
        image_library_id INTEGER,
        image_count INTEGER DEFAULT 1,
        prompt_id INTEGER NOT NULL,
        ai_model_id INTEGER NOT NULL,
        author_id INTEGER,
        need_review INTEGER DEFAULT 1,
        publish_interval INTEGER DEFAULT 3600,
        author_type TEXT DEFAULT 'random',
        custom_author_id INTEGER,
        auto_keywords INTEGER DEFAULT 1,
        auto_description INTEGER DEFAULT 1,
        draft_limit INTEGER DEFAULT 10,
        article_limit INTEGER DEFAULT 10,
        is_loop INTEGER DEFAULT 0,
        model_selection_mode TEXT DEFAULT 'fixed',
        status TEXT DEFAULT 'active',
        created_count INTEGER DEFAULT 0,
        published_count INTEGER DEFAULT 0,
        loop_count INTEGER DEFAULT 0,
        knowledge_base_id INTEGER,
        category_mode TEXT DEFAULT 'smart',
        fixed_category_id INTEGER,
        last_run_at TEXT,
        next_run_at TEXT,
        next_publish_at TEXT,
        last_success_at TEXT,
        last_error_at TEXT,
        last_error_message TEXT DEFAULT '',
        schedule_enabled INTEGER DEFAULT 1,
        max_retry_count INTEGER DEFAULT 3,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (title_library_id) REFERENCES title_libraries(id),
        FOREIGN KEY (image_library_id) REFERENCES image_libraries(id) ON DELETE SET NULL,
        FOREIGN KEY (prompt_id) REFERENCES prompts(id),
        FOREIGN KEY (ai_model_id) REFERENCES ai_models(id),
        FOREIGN KEY (author_id) REFERENCES authors(id) ON DELETE SET NULL,
        FOREIGN KEY (custom_author_id) REFERENCES authors(id) ON DELETE SET NULL,
        FOREIGN KEY (knowledge_base_id) REFERENCES knowledge_bases(id) ON DELETE SET NULL,
        FOREIGN KEY (fixed_category_id) REFERENCES categories(id) ON DELETE SET NULL
    )""",

    # articles - Site articles (soft delete)
    """CREATE TABLE IF NOT EXISTS articles (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        title TEXT NOT NULL,
        slug TEXT UNIQUE NOT NULL,
        excerpt TEXT DEFAULT '',
        content TEXT NOT NULL,
        category_id INTEGER NOT NULL,
        author_id INTEGER NOT NULL,
        task_id INTEGER,
        original_keyword TEXT DEFAULT '',
        keywords TEXT DEFAULT '',
        meta_description TEXT DEFAULT '',
        status TEXT DEFAULT 'draft',
        review_status TEXT DEFAULT 'pending',
        view_count INTEGER DEFAULT 0,
        is_ai_generated INTEGER DEFAULT 0,
        is_hot INTEGER DEFAULT 0,
        is_featured INTEGER DEFAULT 0,
        published_at TEXT,
        deleted_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (category_id) REFERENCES categories(id),
        FOREIGN KEY (author_id) REFERENCES authors(id),
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE SET NULL
    )""",

    # article_images - Many-to-many article-image association
    """CREATE TABLE IF NOT EXISTS article_images (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER NOT NULL,
        image_id INTEGER NOT NULL,
        position INTEGER DEFAULT 0,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
        FOREIGN KEY (image_id) REFERENCES images(id)
    )""",

    # sensitive_words - Sensitive word filter
    """CREATE TABLE IF NOT EXISTS sensitive_words (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        word TEXT NOT NULL UNIQUE,
        created_at TEXT DEFAULT (datetime('now'))
    )""",

    # task_schedules - Task scheduling plans
    """CREATE TABLE IF NOT EXISTS task_schedules (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        next_run_time TEXT NOT NULL,
        status TEXT DEFAULT 'pending',
        error_message TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE
    )""",

    # task_runs - Individual job execution records
    """CREATE TABLE IF NOT EXISTS task_runs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        task_id INTEGER NOT NULL,
        status TEXT NOT NULL,
        article_id INTEGER,
        error_message TEXT DEFAULT '',
        duration_ms INTEGER DEFAULT 0,
        meta TEXT DEFAULT '',
        started_at TEXT DEFAULT (datetime('now')),
        finished_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (task_id) REFERENCES tasks(id) ON DELETE CASCADE,
        FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE SET NULL
    )""",

    # url_import_jobs - URL import async jobs
    """CREATE TABLE IF NOT EXISTS url_import_jobs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        url TEXT NOT NULL,
        normalized_url TEXT NOT NULL,
        source_domain TEXT DEFAULT '',
        page_title TEXT DEFAULT '',
        status TEXT DEFAULT 'queued',
        current_step TEXT DEFAULT 'queued',
        progress_percent INTEGER DEFAULT 0,
        options_json TEXT DEFAULT '',
        result_json TEXT DEFAULT '',
        error_message TEXT DEFAULT '',
        created_by TEXT DEFAULT '',
        started_at TEXT,
        finished_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""",

    # url_import_job_logs - Import job step logs
    """CREATE TABLE IF NOT EXISTS url_import_job_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        job_id INTEGER NOT NULL,
        step TEXT DEFAULT 'queued',
        level TEXT DEFAULT 'info',
        message TEXT NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (job_id) REFERENCES url_import_jobs(id) ON DELETE CASCADE
    )""",

    # worker_heartbeats - Worker liveness
    """CREATE TABLE IF NOT EXISTS worker_heartbeats (
        worker_id TEXT PRIMARY KEY,
        status TEXT NOT NULL DEFAULT 'idle',
        last_seen_at TEXT NOT NULL DEFAULT (datetime('now')),
        meta TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""",

    # api_idempotency_keys - API idempotency cache
    """CREATE TABLE IF NOT EXISTS api_idempotency_keys (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        idempotency_key TEXT NOT NULL,
        route_key TEXT NOT NULL,
        request_hash TEXT NOT NULL,
        response_body TEXT NOT NULL,
        response_status INTEGER NOT NULL,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        UNIQUE(idempotency_key, route_key)
    )""",

    # site_settings - Key-value admin config
    """CREATE TABLE IF NOT EXISTS site_settings (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        setting_key TEXT UNIQUE NOT NULL,
        setting_value TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now'))
    )""",

    # system_logs - System-level logs
    """CREATE TABLE IF NOT EXISTS system_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        type TEXT NOT NULL,
        message TEXT NOT NULL,
        data TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now'))
    )""",

    # admins - Admin users
    """CREATE TABLE IF NOT EXISTS admins (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        username TEXT UNIQUE NOT NULL,
        password TEXT NOT NULL,
        email TEXT DEFAULT '',
        display_name TEXT DEFAULT '',
        role TEXT DEFAULT 'admin',
        status TEXT DEFAULT 'active',
        created_by INTEGER,
        last_login TEXT,
        welcome_seen_version TEXT,
        welcome_dismissed_at TEXT,
        created_at TEXT DEFAULT (datetime('now')),
        updated_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (created_by) REFERENCES admins(id) ON DELETE SET NULL
    )""",

    # admin_activity_logs - Admin operation audit trail
    """CREATE TABLE IF NOT EXISTS admin_activity_logs (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        admin_id INTEGER,
        admin_username TEXT NOT NULL,
        admin_role TEXT DEFAULT 'admin',
        action TEXT NOT NULL,
        request_method TEXT DEFAULT 'POST',
        page TEXT DEFAULT '',
        target_type TEXT DEFAULT '',
        target_id INTEGER,
        ip_address TEXT DEFAULT '',
        details TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (admin_id) REFERENCES admins(id) ON DELETE SET NULL
    )""",

    # article_reviews - Article review records
    """CREATE TABLE IF NOT EXISTS article_reviews (
        id INTEGER PRIMARY KEY AUTOINCREMENT,
        article_id INTEGER NOT NULL,
        admin_id INTEGER NOT NULL,
        review_status TEXT NOT NULL,
        review_note TEXT DEFAULT '',
        created_at TEXT DEFAULT (datetime('now')),
        FOREIGN KEY (article_id) REFERENCES articles(id) ON DELETE CASCADE,
        FOREIGN KEY (admin_id) REFERENCES admins(id)
    )""",
]

SCHEMA_INDEXES = [
    "CREATE INDEX IF NOT EXISTS idx_keywords_library ON keywords(library_id)",
    "CREATE INDEX IF NOT EXISTS idx_titles_library ON titles(library_id)",
    "CREATE INDEX IF NOT EXISTS idx_images_library ON images(library_id)",
    "CREATE INDEX IF NOT EXISTS idx_knowledge_chunks_base ON knowledge_chunks(knowledge_base_id, chunk_index)",
    "CREATE INDEX IF NOT EXISTS idx_articles_category ON articles(category_id)",
    "CREATE INDEX IF NOT EXISTS idx_articles_author ON articles(author_id)",
    "CREATE INDEX IF NOT EXISTS idx_articles_task ON articles(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_articles_status ON articles(status)",
    "CREATE INDEX IF NOT EXISTS idx_articles_deleted ON articles(deleted_at)",
    "CREATE INDEX IF NOT EXISTS idx_article_images_article ON article_images(article_id)",
    "CREATE INDEX IF NOT EXISTS idx_article_images_image ON article_images(image_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_runs_task ON task_runs(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_task_runs_status ON task_runs(status)",
    "CREATE INDEX IF NOT EXISTS idx_task_schedules_task ON task_schedules(task_id)",
    "CREATE INDEX IF NOT EXISTS idx_url_import_jobs_status ON url_import_jobs(status)",
    "CREATE INDEX IF NOT EXISTS idx_url_import_job_logs_job ON url_import_job_logs(job_id)",
    "CREATE INDEX IF NOT EXISTS idx_worker_heartbeats_last_seen ON worker_heartbeats(last_seen_at)",
    "CREATE INDEX IF NOT EXISTS idx_api_idempotency_created ON api_idempotency_keys(created_at)",
    "CREATE INDEX IF NOT EXISTS idx_admin_activity_logs_admin ON admin_activity_logs(admin_id, created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_admin_activity_logs_created ON admin_activity_logs(created_at DESC)",
    "CREATE INDEX IF NOT EXISTS idx_article_reviews_article ON article_reviews(article_id)",
    "CREATE INDEX IF NOT EXISTS idx_articles_hot_status_published ON articles(is_hot, status, published_at)",
    "CREATE INDEX IF NOT EXISTS idx_articles_featured_status_published ON articles(is_featured, status, published_at)",
]


def initialize_schema(conn: sqlite3.Connection):
    """Initialize all tables and indexes."""
    cursor = conn.cursor()
    for create_sql in SCHEMA_TABLES:
        cursor.execute(create_sql)
    for create_sql in SCHEMA_INDEXES:
        cursor.execute(create_sql)
    conn.commit()
