# geoagent/geo/optimizer.py
"""GEO optimization logic."""
import json
import logging
from typing import Optional
from geoagent.geo.rules import GEORules
from geoagent.models.client import ModelClient
from geoagent.models.document import MarkdownDocument, DocContext
from geoagent.prompts.registry import PromptRegistry
from geoagent.db.connection import Database


logger = logging.getLogger(__name__)

# Language code to template name mapping (for auto-selection)
LANG_TO_TEMPLATE = {
    "en": {
        "trust": "GEO Marketing · Trust-Based Article Generation (English)",
        "ranking": "GEO Ranking-Style Article Generation (English)",
    },
    "zh-TW": {
        "trust": "GEO Marketing · Trust-Based Article Generation (Traditional Chinese (Taiwan))",
        "ranking": "GEO Ranking-Style Article Generation (Traditional Chinese (Taiwan))",
    },
    "zh-HK": {
        "trust": "GEO Marketing · Trust-Based Article Generation (Traditional Chinese (Hong Kong))",
        "ranking": "GEO Ranking-Style Article Generation (Traditional Chinese (Hong Kong))",
    },
    "ja": {
        "trust": "GEO Marketing · Trust-Based Article Generation (Japanese)",
        "ranking": "GEO Ranking-Style Article Generation (Japanese)",
    },
    "ko": {
        "trust": "GEO Marketing · Trust-Based Article Generation (Korean)",
        "ranking": "GEO Ranking-Style Article Generation (Korean)",
    },
    "ar": {
        "trust": "GEO Marketing · Trust-Based Article Generation (Arabic)",
        "ranking": "GEO Ranking-Style Article Generation (Arabic)",
    },
    "fr": {
        "trust": "GEO Marketing · Trust-Based Article Generation (French)",
        "ranking": "GEO Ranking-Style Article Generation (French)",
    },
    "de": {
        "trust": "GEO Marketing · Trust-Based Article Generation (German)",
        "ranking": "GEO Ranking-Style Article Generation (German)",
    },
    "es": {
        "trust": "GEO Marketing · Trust-Based Article Generation (Spanish)",
        "ranking": "GEO Ranking-Style Article Generation (Spanish)",
    },
}

# Fallback to Chinese templates for unspecified languages
DEFAULT_TRUST_TEMPLATE = "GEO营销学·信任型正文生成"
DEFAULT_RANKING_TEMPLATE = "GEO榜单型正文生成"

UNDERSTAND_PROMPT = """分析以下文档，返回 JSON 格式：

{{
    "themes": ["主题1", "主题2"],
    "summary": "文档摘要"
}}

文档内容：
---
{content}
---

只返回 JSON 对象，无需其他文字。"""

GEO_OPTIMIZATION_PROMPT = """你是一位 GEO（生成式引擎优化）专家。请优化以下文档，提高其被 AI 搜索引擎（如 Perplexity、ChatGPT、Claude）引用的可能性。

{geo_rules}

优化规则：
1. 开头直接给出主要结论或答案
2. 添加具体数据、日期和权威来源
3. 使用清晰、事实性的语言，避免夸大
4. 用清晰的标题结构回答常见问题
5. 添加参考文献部分（如缺少）

内容过滤规则（必须执行）：
- 移除所有广告图片描述（如"立即购买"、"限时优惠"、"扫码购物"等推广内容）
- 移除关注/订阅号引导（如"长按扫码关注"、"扫码订阅"等）
- 移除活动诱导内容（如"立即参加"、"扫码参与"、"报名从速"等）
- 移除与文章主题无关的装饰性图片和元素
- 移除文末的微信公众号、社交媒体二维码等推广信息
- 保留与主题相关的图表、流程图、技术架构图等有价值的图片引用

原文：
---
{content}
---

请返回 JSON 格式，包含优化后的内容和主题标签：

{{
    "optimized_content": "优化后的完整文章内容（Markdown 格式）",
    "themes": ["主题1", "主题2", "主题3"]
}}

只返回 JSON 对象，无需其他文字。"""


class GEOOptimizer:
    """Applies GEO rules to optimize documents for AI search citation."""

    def __init__(
        self,
        rules: GEORules,
        client: ModelClient = None,
        prompt_template_name: Optional[str] = None,
        db_path: Optional[str] = None,
        template_type: str = "trust"
    ):
        self.rules = rules
        self.client = client
        self._explicit_template = prompt_template_name
        self._db_path = db_path
        self._template_type = template_type  # "trust" or "ranking"

    def _get_prompt(self, content: str, title: str, keyword: str = "", knowledge: str = "", lang: str = "en") -> tuple[str, str]:
        """Get system and user prompts, either from template or built-in."""
        template_name = self._explicit_template
        if not template_name:
            template_name = self._get_auto_template(lang)

        if template_name:
            db = Database.get_instance(self._db_path)
            registry = PromptRegistry(db)
            template = registry.get_template(template_name)
            if template:
                rendered = registry.render(
                    template,
                    title=title,
                    keyword=keyword,
                    Knowledge=knowledge
                )
                return "", rendered

        geo_rules_prompt = self.rules.get_optimization_prompt()
        user_prompt = GEO_OPTIMIZATION_PROMPT.format(
            geo_rules=geo_rules_prompt,
            content=content
        )
        system_prompt = """你是 GEO（生成式引擎优化）专家。
优化内容以提高被 AI 搜索引擎（Perplexity、ChatGPT、Claude）引用的可能性。
重点：权威性、新鲜度、直击要点、客观公平、可溯源、避免幻觉。
内容过滤：移除广告、关注引导、活动诱导、文末推广等信息。"""
        return system_prompt, user_prompt

    def _get_auto_template(self, lang: str) -> Optional[str]:
        """Get template name for language, falling back to Chinese."""
        mapping = LANG_TO_TEMPLATE.get(lang)
        if not mapping:
            return DEFAULT_TRUST_TEMPLATE if self._template_type == "trust" else DEFAULT_RANKING_TEMPLATE
        return mapping.get(self._template_type)

    def optimize(
        self,
        doc: MarkdownDocument,
        model_client: ModelClient,
        model: str,
        max_tokens: int = 8192,
        keyword: str = "",
        knowledge: str = "",
        lang: str = "en"
    ) -> MarkdownDocument:
        """Optimize document using GEO rules (themes extracted in same pass)."""
        if not model_client:
            if not self.client:
                raise ValueError("No model client provided")
            model_client = self.client

        template_name = self._explicit_template or self._get_auto_template(lang)
        system_prompt, user_prompt = self._get_prompt(doc.content, doc.title, keyword, knowledge, lang)

        messages = [
            {"role": "user", "content": user_prompt}
        ]

        result = model_client.complete(
            model=model,
            messages=messages,
            system=system_prompt if system_prompt else None,
            max_tokens=max_tokens
        )

        all_template_names = set()
        for m in LANG_TO_TEMPLATE.values():
            all_template_names.update(m.values())
        is_new_template = template_name and (
            template_name in [
                "GEO Marketing · Trust-Based Article Generation (English)",
                "GEO Ranking-Style Article Generation (English)",
                "GEO营销学·信任型正文生成",
                "GEO榜单型正文生成",
            ]
            or template_name in all_template_names
        )

        if is_new_template:
            optimized_content = result.strip()
            themes = []
        else:
            try:
                data = json.loads(result)
                optimized_content = data.get("optimized_content", result)
                themes = data.get("themes", [])
            except json.JSONDecodeError:
                logger.warning("Failed to parse optimization JSON, using raw content")
                optimized_content = result
                themes = []

        applied_rules = list(self.rules.dimensions.keys())

        frontmatter = {
            **doc.frontmatter,
            "geo_optimized": True,
            "geo_rules_applied": applied_rules
        }

        if themes:
            frontmatter["tags"] = themes

        if template_name:
            frontmatter["geo_template"] = template_name

        return MarkdownDocument(
            title=doc.title,
            content=optimized_content.strip(),
            frontmatter=frontmatter
        )