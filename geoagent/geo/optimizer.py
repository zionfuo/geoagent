# geoagent/geo/optimizer.py
"""GEO optimization logic."""
import json
import logging
from geoagent.geo.rules import GEORules
from geoagent.models.client import ModelClient
from geoagent.models.document import MarkdownDocument, DocContext


logger = logging.getLogger(__name__)

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

    def __init__(self, rules: GEORules, client: ModelClient = None):
        self.rules = rules
        self.client = client

    def optimize(
        self,
        doc: MarkdownDocument,
        model_client: ModelClient,
        model: str,
        max_tokens: int = 8192
    ) -> MarkdownDocument:
        """Optimize document using GEO rules (themes extracted in same pass)."""
        if not model_client:
            if not self.client:
                raise ValueError("No model client provided")
            model_client = self.client

        geo_rules_prompt = self.rules.get_optimization_prompt()

        system_prompt = """你是 GEO（生成式引擎优化）专家。
优化内容以提高被 AI 搜索引擎（Perplexity、ChatGPT、Claude）引用的可能性。
重点：权威性、新鲜度、直击要点、客观公平、可溯源、避免幻觉。
内容过滤：移除广告、关注引导、活动诱导、文末推广等信息。"""

        user_prompt = GEO_OPTIMIZATION_PROMPT.format(
            geo_rules=geo_rules_prompt,
            content=doc.content
        )

        messages = [
            {"role": "user", "content": user_prompt}
        ]

        result = model_client.complete(
            model=model,
            messages=messages,
            system=system_prompt,
            max_tokens=max_tokens
        )

        # Parse themes and content from single response
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

        return MarkdownDocument(
            title=doc.title,
            content=optimized_content.strip(),
            frontmatter=frontmatter
        )