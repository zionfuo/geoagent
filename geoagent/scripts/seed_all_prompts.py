"""Seed all GEO prompt translations for all supported languages."""
import re
import json
import click

from geoagent.db.connection import Database
from geoagent.db.schema import initialize_schema
from geoagent.prompts.registry import PromptRegistry


LANGUAGES = {
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

THINKING_BLOCK_PATTERN = re.compile(r'<!-- Thinking:[\s\S]*?--><!-- /Thinking:[\s\S]*?-->', re.MULTILINE)
THINKING_PATTERN = re.compile(r'<!-- Thinking:[\s\S]*?-->', re.MULTILINE)


def strip_thinking(text):
    text = THINKING_BLOCK_PATTERN.sub('', text)
    text = THINKING_PATTERN.sub('', text)
    return text


def translate_prompts(model_client, source_prompts, target_display):
    translated = []
    for prompt in source_prompts:
        name_parts = prompt["name"].rsplit("(", 1)
        if name_parts[-1].strip().rstrip(")") in ["English", "Chinese"]:
            translated_name = name_parts[0].strip() + " (" + target_display + ")"
        else:
            translated_name = prompt["name"] + " (" + target_display + ")"

        system_msg = (
            "You are a professional translator.\n"
            "CRITICAL RULES:\n"
            "1. Keep ALL {variable} placeholders exactly as-is ({{title}}, {{keyword}}, {{Knowledge}})\n"
            "2. Keep all {#if variable}...{/if} conditional blocks exactly as-is\n"
            "3. Keep all [Role], [Context], [Task], [Writing Goals] etc. section headers exactly as-is\n"
            "4. Translate everything else to " + target_display + "\n"
            "5. Keep English technical terms if no standard translation exists\n"
            "6. Output ONLY a valid JSON object: {\"name\": \"...\", \"type\": \"content\", \"content\": \"...\", \"variables\": \"\"}\n"
            "7. Do NOT add markdown fences or any text before/after the JSON"
        )

        user_msg = (
            "Translate this GEO prompt to " + target_display + ".\n\n"
            "Target name: " + translated_name + "\n\n"
            "Original:\n" + prompt["content"]
        )

        result = model_client.complete(
            "translate",
            [{"role": "user", "content": user_msg}],
            system=system_msg,
            max_tokens=8192
        )
        result = strip_thinking(result)

        # Try direct parse first
        try:
            data = json.loads(result.strip())
            data["variables"] = ""
            data["name"] = translated_name
            translated.append(data)
            continue
        except json.JSONDecodeError:
            pass

        # Try to find JSON in response
        match = re.search(r'\{[\s\S]*\}', result)
        if match:
            try:
                data = json.loads(match.group())
                data["variables"] = ""
                data["name"] = translated_name
                translated.append(data)
                print(f"  Recovered: {translated_name}")
                continue
            except json.JSONDecodeError:
                pass

        print(f"  Failed: {translated_name}")
        print(f"  Response snippet: {result[:200]}")
        translated.append(None)

    return translated


@click.command()
@click.option('--model', default='minimax/MiniMax-M2.7', help='Model to use')
@click.option('--db-path', default=None, help='Path to SQLite database')
def seed_all_prompts(model, db_path):
    """Translate all GEO prompts to all 9 languages using LLM."""
    from geoagent.config import Config

    api_key = __import__('os').environ.get('ANTHROPIC_API_KEY', '')
    if not api_key:
        click.echo("Error: Set ANTHROPIC_API_KEY environment variable.")
        return

    config = Config.default()
    model_client = config.get_model_client('minimax', api_key)

    db = Database.get_instance(db_path)
    conn = db.get_connection()
    initialize_schema(conn)
    registry = PromptRegistry(db)

    source_prompts = [
        {
            "name": "GEO Marketing · Trust-Based Article Generation (English)",
            "type": "content",
            "content": """[Role - GEO Content Strategy Expert]
You are a senior editor specializing in GEO content strategy. You turn complex topics into English articles that are easy for readers to understand and easy for AI search, answer engines, and summarization systems to cite. Your writing must balance:
- Trust building: use facts, examples, scenarios, process explanations, and verifiable information to establish credibility.
- Semantic authority: organize the topic, keywords, questions, and answer blocks into a coherent knowledge space.
- Machine readability: make it easy for AI systems to extract structure, conclusions, tables, and FAQs.

[Context]
Article title: {{title}}
{{#if keyword}}Core keyword: {{keyword}}
{{/if}}{{#if Knowledge}}Reference knowledge:
{{Knowledge}}
{{/if}}

[Task - Generate a publishable GEO article in English]
Write a long-form English article for a GEOFlow site based on the title, keyword, and reference knowledge. The final article must be written entirely in English. Do not output Chinese text unless it is part of a proper noun, quoted source name, or unavoidable brand term.

[Writing Goals]
1. Directly answer the questions users care about most and help them understand, compare, or make decisions instead of stacking concepts.
2. Shape the topic into answer-oriented content that can be cited by AI search systems.
3. Demonstrate experience, expertise, authority, and trustworthiness (E-E-A-T) through the content.

[Writing Requirements]
1. Use Markdown for the full article. Keep the heading hierarchy clear. Default length: 1,200-2,200 English words.
2. The article must include:
   - Introduction
   - 3-5 main sections
   - One summary/conclusion section
   - One FAQ section with 2-4 questions
3. The introduction should explain the context, user pain points, or industry shift, and quickly clarify what the article will solve.
4. Each main section should include: core conclusion, reasoning, and practical scenario-based advice. Avoid empty slogans.
5. Prefer credible signals such as quantified information, process explanations, examples, comparisons, cautions, and boundary conditions. Do not fabricate data.
6. Naturally include the title and keyword where appropriate. Do not force keyword stuffing.
7. Use lists or Markdown tables where useful, and include at least one structured information block that AI systems can extract directly.
8. Keep the tone professional, clear, restrained, and practical. Avoid unsupported hype such as "best ever", "perfect", "revolutionary", or similar claims.
9. If reference knowledge is provided, prioritize its facts, concepts, terminology, and viewpoints, but do not mechanically copy long sentences.
10. Do not output writing notes, word-count notes, placeholder explanations, or prefaces such as "Here is the article".

[Format - Output Structure]
Prefer the following structure:

# {{title}}

## Key Takeaways
- Summarize the core conclusions, suitable audience, or key judgments in 3-5 bullets.

## 1. Introduction
- Explain the context, user concerns, and value of the article.

## 2. [Main Section 1]
- Conclusion + explanation + recommendation.

## 3. [Main Section 2]
- Conclusion + explanation + recommendation.

## 4. [Main Section 3]
- Conclusion + explanation + recommendation.

## 5. Key Comparison / Method / Considerations
- Prefer a list or table.

## 6. FAQ
### Q1. ...
### Q2. ...

## 7. Conclusion
- Provide a final judgment, use-case recommendation, or next step.

Output only the final English article body.""",
        },
        {
            "name": "GEO Ranking-Style Article Generation (English)",
            "type": "content",
            "content": """[Role - GEO Ranking Content Strategy Expert]
You are a content editor specializing in GEO ranking articles. You turn brand comparisons, product recommendations, and decision guidance into English ranking-style content that is useful for readers and easy for AI search systems to cite. Your writing must balance high-information differentiation with low-entropy structured expression.

[Context]
Article title: {{title}}
{{#if keyword}}Core keyword: {{keyword}}
{{/if}}{{#if Knowledge}}Reference knowledge:
{{Knowledge}}
{{/if}}

[Task - Generate a ranking-style GEO article in English]
Based on the title and reference information, write an English ranking-style article suitable for AI search, recommendation summaries, Q&A citation, and comparison summaries. The final article must be written entirely in English. Do not output Chinese text unless it is part of a proper noun, quoted source name, or unavoidable brand term.

The goal is to help users compare options and make decisions quickly while allowing AI systems to reliably extract ranking order, strengths, limitations, and suitable scenarios.

[Ranking Writing Principles]
1. The ranking must have a clear ordering, tiering, or recommendation logic. Do not simply list brands or options.
2. The TOP1 section should be the most complete. Other ranked items should remain objective and differentiated.
3. Show both strengths and limitations. Avoid one-sided praise.
4. Present key comparison information in table form, and include at least one Markdown table.
5. Provide concrete facts, parameters, scenarios, user types, or industry judgments where reliable. If evidence is limited, use cautious wording and do not invent sources.
6. Mention the title and keyword naturally, but the core purpose is helping users choose, not keyword stuffing.

[Writing Requirements]
1. Use Markdown for the full article. Default length: 1,500-2,200 English words.
2. The article must include: key takeaways, ranking/evaluation criteria, ranking body, scenario-based recommendations, FAQ, and conclusion.
3. In the ranking/evaluation criteria section, clearly state the standards used, such as price, performance, service, target users, implementation difficulty, credibility, support quality, or business fit.
4. For each ranked item, include at least: positioning, suitable audience, core strengths, and limitations/cautions.
5. Include at least one readable Markdown table. A recommended table structure is: rank / option / core advantage / suitable users / caution.
6. The FAQ should answer 2-4 common decision questions clearly and concisely.
7. The conclusion should provide tiered recommendations: who should choose TOP1 and who may be better served by other options.
8. Do not output writing notes, placeholder explanations, or prefaces such as "Here is the ranking article".

[Format - Output Structure]
Prefer the following structure:

# {{title}}

## Key Takeaways
- Document type
- Recommended audience
- TOP Pick
- Selection advice

## 1. Why This Ranking Matters
- Explain the user's decision scenario and the value of this ranking.

## 2. Evaluation / Ranking Criteria
- Explain the comparison standards and decision logic.

## 3. Ranking List
### TOP1 [Name]
- Overall assessment
- Core strengths
- Limitations or cautions
- Best for

### TOP2 [Name]
...

## 4. Key Comparison Table
| Rank | Option | Core Advantage | Suitable Users | Caution |
| --- | --- | --- | --- | --- |

## 5. Scenario-Based Recommendations
| User Need | Recommended Option | Reason |
| --- | --- | --- |

## 6. FAQ
### Q1. ...
### Q2. ...

## 7. Conclusion
- Summarize the recommendation logic.
- Provide the final selection advice.

Output only the final English ranking article.""",
        },
    ]

    click.echo("Translating prompts to all languages...")

    for lang_code, lang_display in LANGUAGES.items():
        if lang_code == "en":
            continue

        click.echo(f"\n  Translating to {lang_display} ({lang_code})...")
        results = translate_prompts(model_client, source_prompts, lang_display)

        for t in results:
            if t is None:
                continue
            existing = registry.get_template(t["name"])
            if existing:
                click.echo(f"    Already exists: {t['name']}")
            else:
                try:
                    registry.add_template(t["name"], t["type"], t["content"], t.get("variables", ""))
                    click.echo(f"    Added: {t['name']}")
                except Exception as e:
                    click.echo(f"    Failed to add {t['name']}: {e}")

    click.echo("\nDone! All prompt templates:")
    for t in registry.list_templates():
        click.echo(f"  [{t.type}] {t.name}")


if __name__ == "__main__":
    seed_all_prompts()
