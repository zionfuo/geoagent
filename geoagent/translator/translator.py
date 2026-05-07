# geoagent/translator/translator.py
"""Translation logic for multi-language support."""
from geoagent.models.client import ModelClient
from geoagent.models.document import MarkdownDocument


LANGUAGE_DISPLAY = {
    "en": "English",
    "zh-TW": "Traditional Chinese (Taiwan)",
    "zh-HK": "Traditional Chinese (Hong Kong)",
    "ja": "Japanese",
    "ko": "Korean",
    "ar": "Arabic",
    "fr": "French",
    "de": "German",
    "es": "Spanish",
}

TRANSLATION_PROMPT = """你是一位专业翻译。请将以下文档翻译成{target_lang}（{target_display}）。

翻译规则：
1. 保留 Markdown 格式
2. 保留技术术语（除非有标准翻译）
3. 保持原文的语气和风格

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

翻译结果："""


class Translator:
    """Handles translation of documents to target languages."""

    def __init__(self, client: ModelClient, default_model: str, max_tokens: int = 8192):
        self.client = client
        self.default_model = default_model
        self.max_tokens = max_tokens

    def get_language_display(self, code: str) -> str:
        return LANGUAGE_DISPLAY.get(code, code)

    def translate(self, doc: MarkdownDocument, target_lang: str) -> MarkdownDocument:
        """Translate document to target language."""
        target_display = self.get_language_display(target_lang)

        system_prompt = "You are a professional translator. Preserve markdown formatting and technical terms."
        user_prompt = TRANSLATION_PROMPT.format(
            target_lang=target_lang,
            target_display=target_display,
            content=doc.content
        )

        messages = [
            {"role": "user", "content": user_prompt}
        ]

        translated_content = self.client.complete(
            model=self.default_model,
            messages=messages,
            system=system_prompt,
            max_tokens=self.max_tokens
        )

        return MarkdownDocument(
            title=doc.title,
            content=translated_content.strip(),
            frontmatter={
                **doc.frontmatter,
                "lang": target_lang,
                "translated_from": doc.frontmatter.get("lang", "zh")
            }
        )