"""Article models for geoagent."""
from dataclasses import dataclass, field
from typing import Optional


@dataclass
class Article:
    id: Optional[int] = None
    title: str = ""
    slug: str = ""
    excerpt: str = ""
    content: str = ""
    category_id: int = 0
    author_id: int = 0
    task_id: Optional[int] = None
    original_keyword: str = ""
    keywords: str = ""
    meta_description: str = ""
    status: str = "draft"
    review_status: str = "pending"
    view_count: int = 0
    is_ai_generated: int = 0
    is_hot: int = 0
    is_featured: int = 0
    published_at: Optional[str] = None
    deleted_at: Optional[str] = None
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Author:
    id: Optional[int] = None
    name: str = ""
    bio: str = ""
    email: str = ""
    avatar: str = ""
    website: str = ""
    social_links: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


@dataclass
class Category:
    id: Optional[int] = None
    name: str = ""
    slug: str = ""
    description: str = ""
    sort_order: int = 0
    created_at: Optional[str] = None


@dataclass
class ArticleImage:
    id: Optional[int] = None
    article_id: int = 0
    image_id: int = 0
    position: int = 0
    created_at: Optional[str] = None
