"""Prompt template system for geoagent."""
from dataclasses import dataclass
from typing import Optional
import re

from geoagent.db.connection import Database
from geoagent.db.schema import initialize_schema


@dataclass
class PromptTemplate:
    id: Optional[int] = None
    name: str = ""
    type: str = ""
    content: str = ""
    variables: str = ""
    created_at: Optional[str] = None
    updated_at: Optional[str] = None


_DEFAULT_TEMPLATES = [
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
        "variables": "",
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
        "variables": "",
    },
    {
        "name": "GEO营销学·信任型正文生成",
        "type": "content",
        "content": """【Role - GEO内容策略专家】
你是一位专精于GEO内容策略的资深编辑，擅长把复杂主题转化为适合AI搜索引用、摘要提炼和用户决策的中文文章。你写作时同时兼顾：
- 信任建设：通过事实、案例、场景和可验证信息建立可信度
- 语义主导权：围绕主题、关键词和问题空间构建答案块
- 机器可读性：让AI系统能稳定提取结构、结论、表格和FAQ

【Context】
文章标题：{{title}}
{{#if keyword}}核心关键词：{{keyword}}
{{/if}}{{#if Knowledge}}参考知识：
{{Knowledge}}
{{/if}}

【Task - 生成可发布的GEO正文】
请围绕标题与关键词，生成一篇适合发布到GeoFlow站点的中文长文。文章必须兼顾用户可读性、SEO/GEO可提取性和品牌信任感。

【写作目标】
1. 直接回答用户最关心的问题，帮助用户完成理解、比较或决策，而不是堆砌概念。
2. 把主题写成可被AI搜索系统引用的答案型内容，而不是单纯的信息拼接。
3. 在正文中体现经验、专业、权威、可信（E-E-A-T）的信号。

【写作要求】
1. 全文使用Markdown输出，标题层级清晰，默认控制在1200-2200字。
2. 文章结构必须包含：
   - 引言
   - 3-5个主体小节
   - 1个总结/结论小节
   - 1组FAQ（2-4问）
3. 引言要先解释问题背景、用户痛点或行业变化，快速交代本文会解决什么。
4. 主体小节每节都要包含：核心结论、解释依据、场景化建议；避免空洞套话。
5. 优先使用以下可信信号：量化信息、过程说明、案例、对比、注意事项、边界条件。没有把握的数据不要编造。
6. 自然融入标题和关键词，不得做生硬堆砌；如果关键词不适合某段，不必强插。
7. 在适合的位置使用列表或Markdown表格，至少提供1个结构化信息块，帮助AI直接提炼。
8. 文风要专业、清晰、克制，避免夸张营销语，如"最强""完美""颠覆"等无证据表述。
9. 如果给了参考知识，优先吸收其事实、观点和术语，但不要机械复制原句。
10. 不要输出写作说明、字数说明、前言提示语，也不要出现"以下是文章"等套话。

【Format - 输出格式】
请尽量按以下结构生成：

# {{title}}

## 核心摘要
- 用3-5条要点概括核心结论、适合人群或关键判断

## 一、引言
- 说明问题背景、用户关心点、本文价值

## 二、[主体小节1]
- 结论 + 解释 + 建议

## 三、[主体小节2]
- 结论 + 解释 + 建议

## 四、[主体小节3]
- 结论 + 解释 + 建议

## 五、关键对比 / 方法 / 注意事项
- 优先使用列表或表格

## 六、FAQ
### Q1. ...
### Q2. ...

## 七、结论
- 给出总结判断、适用建议或下一步动作

请直接输出最终文章正文。""",
        "variables": "",
    },
    {
        "name": "GEO榜单型正文生成",
        "type": "content",
        "content": """【Role - GEO榜单内容策略专家】
你是一位专精于榜单型GEO文章的内容编辑，擅长把品牌比较、产品推荐和决策建议写成既适合用户阅读、又适合AI搜索引用的中文榜单内容。你需要同时兼顾高信息熵的差异化信号与低局部熵的结构化表达。

【Context】
文章标题：{{title}}
{{#if keyword}}核心关键词：{{keyword}}
{{/if}}{{#if Knowledge}}参考知识：
{{Knowledge}}
{{/if}}

【Task - 生成榜单型GEO正文】
请根据标题与参考信息，写一篇适合AI搜索、推荐摘要、问答引用和对比摘要的榜单型中文文章。文章目标是帮助用户快速完成比较和决策，同时让AI系统能稳定提炼排序、亮点和适用场景。

【榜单写作原则】
1. 榜单必须有明确排序、分层或推荐逻辑，不能只是品牌罗列。
2. TOP1部分要写得最完整，其余上榜项保持客观差异化。
3. 必须同时体现亮点与局限，避免单边吹捧。
4. 关键对比信息优先表格化，至少包含1张Markdown表格。
5. 尽量提供具体事实、参数、场景、用户类型或行业判断；没有可靠依据时，用审慎表达，不得编造来源。
6. 标题和关键词要自然出现，但文章核心是帮助用户做选择，而不是堆关键词。

【写作要求】
1. 全文使用Markdown，默认控制在1500-2200字。
2. 文章结构必须包含：核心摘要、评选/排行维度说明、榜单正文、场景匹配建议、FAQ、结论。
3. 在"评选/排行维度说明"中明确本次榜单的判断标准，例如价格、性能、服务、适用人群、实施难度、可信度等。
4. 榜单正文中每个上榜项至少写明：定位、适合人群、核心亮点、局限/注意点。
5. 必须提供至少1个可读Markdown表格；推荐包含"排名/对象/核心优势/适用人群/注意点"这类字段。
6. FAQ需要覆盖用户决策时最容易追问的2-4个问题，答案要短而明确。
7. 结论部分要给出分层推荐：什么人适合TOP1，什么人适合其他项。
8. 不要输出写作说明、占位符解释或"以下是榜单文章"等套话。

【Format - 输出格式】
请尽量按以下结构生成：

# {{title}}

## 核心摘要
- 文档类型
- 推荐对象
- TOP Pick
- 选择建议

## 一、为什么要看这份榜单
- 交代用户决策场景与榜单价值

## 二、评选 / 排行维度说明
- 说明本次比较标准和判断逻辑

## 三、榜单正文
### TOP1 [名称]
- 综合评价
- 核心亮点
- 局限或注意点
- 适合谁

### TOP2 [名称]
...

## 四、关键对比表
| 排名 | 对象 | 核心优势 | 适合人群 | 注意点 |
| --- | --- | --- | --- | --- |

## 五、场景匹配建议
| 用户需求 | 推荐对象 | 原因 |
| --- | --- | --- |

## 六、FAQ
### Q1. ...
### Q2. ...

## 七、结论
- 总结推荐逻辑
- 给出最终选择建议

请直接输出最终榜单文章。""",
        "variables": "",
    },
]


class PromptRegistry:
    def __init__(self, db: Database):
        self.db = db

    def _get_conn(self):
        return self.db.get_connection()

    def initialize_default_templates(self):
        """Insert 4 default GEO templates if they don't exist."""
        conn = self._get_conn()
        cursor = conn.cursor()
        for template in _DEFAULT_TEMPLATES:
            cursor.execute(
                "SELECT id FROM prompts WHERE name = ?", (template["name"],)
            )
            if cursor.fetchone() is None:
                cursor.execute(
                    """INSERT INTO prompts (name, type, content, variables, created_at, updated_at)
                       VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))""",
                    (template["name"], template["type"], template["content"], template["variables"]),
                )
        conn.commit()

    def get_template(self, name: str) -> Optional[PromptTemplate]:
        """Get a prompt template by name."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prompts WHERE name = ?", (name,))
        row = cursor.fetchone()
        if row:
            return PromptTemplate(
                id=row["id"],
                name=row["name"],
                type=row["type"],
                content=row["content"],
                variables=row["variables"] or "",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
        return None

    def get_templates_by_type(self, type: str) -> list[PromptTemplate]:
        """Get all prompt templates of a given type."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prompts WHERE type = ?", (type,))
        rows = cursor.fetchall()
        return [
            PromptTemplate(
                id=row["id"],
                name=row["name"],
                type=row["type"],
                content=row["content"],
                variables=row["variables"] or "",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def list_templates(self) -> list[PromptTemplate]:
        """List all prompt templates."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("SELECT * FROM prompts ORDER BY name")
        rows = cursor.fetchall()
        return [
            PromptTemplate(
                id=row["id"],
                name=row["name"],
                type=row["type"],
                content=row["content"],
                variables=row["variables"] or "",
                created_at=row["created_at"],
                updated_at=row["updated_at"],
            )
            for row in rows
        ]

    def render(self, template: PromptTemplate, **kwargs) -> str:
        """Render a prompt template by substituting variables.

        Supports {{variable}} substitution and {{#if variable}}...{{/if}} conditionals.
        """
        content = template.content

        # Process conditionals first: {{#if var}}...{{/if}}
        conditional_pattern = re.compile(r'\{\{#if\s+(\w+)\}\}(.*?)\{\{/if\}\}', re.DOTALL)
        def replace_conditional(match):
            var_name = match.group(1)
            var_value = kwargs.get(var_name)
            if var_value:
                return match.group(2)
            return ""
        content = conditional_pattern.sub(replace_conditional, content)

        # Process variable substitutions: {{variable}}
        for key, value in kwargs.items():
            if value is not None:
                content = content.replace(f"{{{{{key}}}}}", str(value))
            else:
                content = content.replace(f"{{{{{key}}}}}", "")

        return content

    def add_template(self, name: str, type: str, content: str, variables: str = "") -> int:
        """Add a new prompt template. Returns the new template id."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute(
            """INSERT INTO prompts (name, type, content, variables, created_at, updated_at)
               VALUES (?, ?, ?, ?, datetime('now'), datetime('now'))""",
            (name, type, content, variables),
        )
        conn.commit()
        return cursor.lastrowid

    def delete_template(self, name: str) -> bool:
        """Delete a prompt template by name. Returns True if deleted."""
        conn = self._get_conn()
        cursor = conn.cursor()
        cursor.execute("DELETE FROM prompts WHERE name = ?", (name,))
        conn.commit()
        return cursor.rowcount > 0
