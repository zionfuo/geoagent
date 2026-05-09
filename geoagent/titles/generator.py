"""AI title generation with 5 styles."""
import random
from dataclasses import dataclass
from typing import Optional

from geoagent.models.client import ModelClient


STYLE_MAP = {
    "professional": "专业严谨的",
    "attractive": "吸引眼球的",
    "seo": "SEO优化的",
    "creative": "创意新颖的",
    "question": "疑问式的",
}

MOCK_TEMPLATES = {
    "professional": [
        "{kw}的深度分析与研究",
        "关于{kw}的专业见解",
        "{kw}行业发展趋势报告",
    ],
    "attractive": [
        "你绝对不知道的{kw}秘密",
        "揭秘{kw}背后的故事",
        "{kw}让人意想不到的用途",
    ],
    "seo": [
        "{kw}完整指南：从入门到精通",
        "{kw}常见问题解答大全",
        "如何选择最适合的{kw}方案",
    ],
    "creative": [
        "重新定义{kw}的可能性",
        "如果{kw}会说话，它会告诉你什么？",
        "当{kw}遇上创新思维",
    ],
    "question": [
        "{kw}真的有用吗？",
        "为什么{kw}如此重要？",
        "{kw}的未来在哪里？",
    ],
}


@dataclass
class TitleResult:
    titles: list[str]
    style: str
    used_mock: bool = False


class TitleGenerator:
    """Generate AI titles in 5 styles with mock fallback."""

    def __init__(self, model_client: Optional[ModelClient] = None):
        self.model_client = model_client

    def generate(
        self,
        keywords: list[str],
        style: str = "professional",
        count: int = 3
    ) -> TitleResult:
        """Generate titles using AI or fallback to mock templates."""
        if not keywords:
            return TitleResult(titles=[], style=style, used_mock=True)

        keyword_text = "、".join(keywords)
        style_desc = STYLE_MAP.get(style, "专业严谨的")

        if not self.model_client:
            return self._mock_generate(keywords, style, count)

        try:
            system_prompt = (
                f"你是一个专业的内容标题生成专家。请根据提供的关键词生成{style_desc}文章标题。"
            )
            user_prompt = (
                f"请基于以下关键词生成 {count} 个{style_desc}文章标题：\n\n"
                f"关键词：{keyword_text}\n\n"
                f"每行一个标题，不要加编号或前缀，直接输出标题。"
            )

            messages = [{"role": "user", "content": user_prompt}]
            response = self.model_client.complete(
                "title_gen",
                messages,
                system=system_prompt,
                max_tokens=500
            )

            titles = self._parse_titles(response)
            if titles:
                return TitleResult(titles=titles, style=style, used_mock=False)
        except Exception:
            pass

        return self._mock_generate(keywords, style, count)

    def _mock_generate(
        self,
        keywords: list[str],
        style: str,
        count: int
    ) -> TitleResult:
        """Generate mock titles from templates when AI fails."""
        templates = MOCK_TEMPLATES.get(style, MOCK_TEMPLATES["professional"])
        kw = random.choice(keywords)
        titles = []
        for tmpl in templates[:count]:
            titles.append(tmpl.format(kw=kw))
        return TitleResult(titles=titles, style=style, used_mock=True)

    def _parse_titles(self, content: str) -> list[str]:
        """Parse generated titles: split on newlines, strip leading numbers/markers."""
        titles = []
        for line in content.split('\n'):
            line = line.strip()
            # Strip leading numbers/markers: 1. 1) 1、 1-
            line = re.sub(r'^[\d]+[.\)　\-、\s]+', '', line)
            line = line.strip()
            if line and len(line) > 2:
                titles.append(line)
        # Deduplicate while preserving order
        seen = set()
        unique = []
        for t in titles:
            if t not in seen:
                seen.add(t)
                unique.append(t)
        return unique

    def generate_with_retry(
        self,
        keywords: list[str],
        style: str = "professional",
        count: int = 3,
        max_retries: int = 2
    ) -> TitleResult:
        """Generate with retry on failure."""
        for _ in range(max_retries):
            result = self.generate(keywords, style, count)
            if result.titles:
                return result
        return result


# Need re for _parse_titles
import re
