"""Title library system for geoagent."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class TitleLibrary:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    title_count: int = 0
    generation_type: str = "manual"
    keyword_library_id: Optional[int] = None
    ai_model_id: Optional[int] = None
    prompt_id: Optional[int] = None
    generation_rounds: int = 1
    is_ai_generated: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Title:
    id: Optional[int] = None
    library_id: int = 0
    title: str = ""
    keyword: str = ""
    is_ai_generated: int = 0
    used_count: int = 0
    usage_count: int = 0
    created_at: Optional[str] = None
