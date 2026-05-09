"""URL import pipeline for geoagent."""
from dataclasses import dataclass
from typing import Optional
import datetime


@dataclass
class ImportJob:
    id: Optional[int] = None
    url: str = ""
    normalized_url: str = ""
    source_domain: str = ""
    page_title: str = ""
    status: str = "queued"
    current_step: str = "queued"
    progress_percent: int = 0
    options_json: str = ""
    result_json: str = ""
    error_message: str = ""
    created_by: str = ""
    started_at: Optional[str] = None
    finished_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class ImportJobLog:
    id: Optional[int] = None
    job_id: int = 0
    step: str = "queued"
    level: str = "info"
    message: str = ""
    created_at: Optional[str] = None


class ImportJobManager:
    """Manages URL import jobs with step-by-step logging."""

    def __init__(self, db):
        self.db = db

    def _conn(self):
        return self.db.get_connection()

    def create_job(self, url: str, created_by: str = "", options_json: str = "") -> int:
        """Create a new import job. Returns the job id."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc

        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO url_import_jobs
               (url, normalized_url, source_domain, status, current_step, progress_percent, options_json, created_by, created_at, updated_at)
               VALUES (?, ?, ?, 'queued', 'queued', 0, ?, ?, datetime('now'), datetime('now'))""",
            (url, url, domain, options_json, created_by),
        )
        conn.commit()
        return cursor.lastrowid

    def update_progress(self, job_id: int, step: str, progress: int, level: str = "info", message: str = ""):
        """Update job progress and log the step."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE url_import_jobs SET current_step = ?, progress_percent = ?, updated_at = datetime('now')
               WHERE id = ?""",
            (step, progress, job_id),
        )
        cursor.execute(
            """INSERT INTO url_import_job_logs (job_id, step, level, message, created_at)
               VALUES (?, ?, ?, ?, datetime('now'))""",
            (job_id, step, level, message),
        )
        conn.commit()

    def complete_job(self, job_id: int, result_json: str):
        """Mark job as completed."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE url_import_jobs
               SET status = 'completed', progress_percent = 100, result_json = ?, finished_at = datetime('now'), updated_at = datetime('now')
               WHERE id = ?""",
            (result_json, job_id),
        )
        conn.commit()

    def fail_job(self, job_id: int, error: str):
        """Mark job as failed."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute(
            """UPDATE url_import_jobs
               SET status = 'failed', error_message = ?, finished_at = datetime('now'), updated_at = datetime('now')
               WHERE id = ?""",
            (error, job_id),
        )
        conn.commit()

    def get_job(self, job_id: int) -> Optional[ImportJob]:
        """Get a job by id."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM url_import_jobs WHERE id = ?", (job_id,))
        row = cursor.fetchone()
        if row:
            return ImportJob(
                id=row["id"], url=row["url"], normalized_url=row["normalized_url"],
                source_domain=row["source_domain"], page_title=row["page_title"],
                status=row["status"], current_step=row["current_step"],
                progress_percent=row["progress_percent"],
                options_json=row["options_json"] or "",
                result_json=row["result_json"] or "",
                error_message=row["error_message"] or "",
                created_by=row["created_by"] or "",
                started_at=row["started_at"], finished_at=row["finished_at"],
                created_at=row["created_at"], updated_at=row["updated_at"],
            )
        return None

    def get_job_logs(self, job_id: int) -> list[ImportJobLog]:
        """Get all logs for a job."""
        conn = self._conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM url_import_job_logs WHERE job_id = ? ORDER BY created_at", (job_id,))
        rows = cursor.fetchall()
        return [
            ImportJobLog(
                id=row["id"], job_id=row["job_id"], step=row["step"] or "queued",
                level=row["level"] or "info", message=row["message"],
                created_at=row["created_at"],
            )
            for row in rows
        ]


class URLFetcher:
    """Fetch URL content using httpx."""

    def __init__(self, timeout: int = 30):
        self.timeout = timeout

    def fetch(self, url: str) -> tuple[str, str]:
        """Fetch URL content. Returns (html_content, page_title).

        Raises httpx.HTTPError on failure.
        """
        import httpx
        with httpx.Client(timeout=self.timeout, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()
            html = response.text

        from bs4 import BeautifulSoup
        soup = BeautifulSoup(html, 'html.parser')
        title = soup.title.string if soup.title else ""
        return html, title
