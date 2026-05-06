# geoagent/translator/translator.py
"""Translation logic for multi-language support."""
from geoagent.models.client import ModelClient
from geoagent.models.document import MarkdownDocument, DocContext


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

TRANSLATION_PROMPT = """You are a professional translator. Translate the following document into {target_lang} ({target_display}).

Preserve:
- Markdown formatting
- Technical terms (only translate if there's a standard translation)
- The tone and style of the original

Original document:
---
{content}
---

Translation:"""


class Translator:
    """Handles translation of documents to target languages."""

    def __init__(self, client: ModelClient, default_model: str, max_tokens: int = 8192):
        self.client = client
        self.default_model = default_model
        self.max_tokens = max_tokens

    def get_language_display(self, code: str) -> str:
        return LANGUAGE_DISPLAY.get(code, code)

    def translate(self, doc: MarkdownDocument, target_lang: str, context: DocContext = None) -> MarkdownDocument:
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