"""Image management for geoagent."""
from dataclasses import dataclass
from typing import Optional


@dataclass
class ImageLibrary:
    id: Optional[int] = None
    name: str = ""
    description: str = ""
    image_count: int = 0
    used_task_count: int = 0
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Image:
    id: Optional[int] = None
    library_id: int = 0
    filename: str = ""
    original_name: str = ""
    file_name: str = ""
    file_path: str = ""
    file_size: int = 0
    mime_type: str = ""
    width: int = 0
    height: int = 0
    tags: str = ""
    used_count: int = 0
    usage_count: int = 0
    created_at: Optional[str] = None
