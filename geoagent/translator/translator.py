# geoagent/translator/translator.py
"""Translation logic for multi-language support."""
from geoagent.models.client import ModelClient
from geoagent.models.document import MarkdownDocument


LANGUAGE_DISPLAY = {
    "en": "English",
    "zh-CN": "Simplified Chinese",
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

TRANSLATION_PROMPT_ZH_TW = """你是一位專業繁體中文（臺灣）翻譯專家。請將以下簡體中文文章翻譯為正體中文（臺灣使用習慣）。

【臺灣用語對照表 - 必須遵循】
| 簡體中文 | 臺灣正體 |
|---------|----------|
| 数据中心 | 資料中心 |
| 云计算 | 雲端運算 |
| 边缘计算 | 邊緣運算 |
| 数字化/数字化 | 數位化 |
| 超大规模 | 超大規模 |
| 高性能计算 | 高效能計算 |
| 主机托管 | 主機代管 |
| 技术趋势 | 技術趨勢 |
| 发展趋势 | 發展趨勢 |
| 市场展望 | 市場展望 |
| 自动化 | 自動化 |
| 可持续发展 | 可持續發展 |
| 安全升级 | 安全升級 |
| 良性竞争 | 良性競爭 |
| 数字化转型 | 數位轉型 |
| 网络安全 | 網路安全 |
| 智慧城市 | 智慧城市 |
| 人工智能 | 人工智慧 |
| 区块链 | 區塊鏈 |
| 大数据 | 大數據 |
| 物联网 | 物聯網 |
| 智能制造 | 智慧製造 |
| 预测 | 預測 |
| 布局 | 佈局 |
| 变革 | 變革 |
| 转型 | 轉型 |
| 生态 | 生態 |
| 赋能 | 賦能 |
| 协同 | 協同 |
| 驱动 | 驅動 |
| 构建 | 構築 |
| 推进 | 推進 |
| 基础设施 | 基礎設施 |
| 产业链 | 產業鏈 |
| 供应链 | 供應鏈 |
| 架构 | 架構 |
| 平台 | 平臺 |
| 运营 | 營運 |
| 运维 | 維運 |
| 部署 | 部署 |
| 集成 | 整合 |
| 监控 | 監控 |
| 优化 | 優化 |
| 效率 | 效率 |
| 可靠性 | 可靠性 |
| 可用性 | 可用性 |
| 弹性 | 彈性 |
| 扩展性 | 擴展性 |
| 安全性 | 安全性 |
| 隐私 | 隱私 |
| 风险 | 風險 |
| 合规 | 法規遵循 |
| 治理 | 治理 |
| 管理 | 管理 |
| 分析 | 分析 |
| 处理 | 處理 |
| 存储 | 儲存 |
| 传输 | 傳輸 |
| 计算 | 計算 |
| 网络 | 網路 |
| 服务器 | 伺服器 |
| 芯片 | 晶片 |
| 处理器 | 處理器 |
| 内存 | 記憶體 |
| 存储 | 儲存 |
| 负载 | 負載 |
| 性能 | 效能 |
| 成本 | 成本 |
| 收益 | 收益 |
| 增长 | 成長 |
| 增长 | 增長 |
| 规模 | 規模 |
| 市场 | 市場 |
| 行业 | 產業 |
| 企业 | 企業 |
| 客户 | 客戶 |
| 用户 | 用戶 |
| 消费者 | 消費者 |
| 产品 | 產品 |
| 服务 | 服務 |
| 方案 | 方案 |
| 平台 | 平臺 |
| 解决方案 | 解決方案 |
| 案例 | 案例 |
| 最佳实践 | 最佳實踐 |
| 方法论 | 方法論 |
| 策略 | 策略 |
| 路线图 | 路線圖 |
| 规划 | 規劃 |
| 目标 | 目標 |
| 关键 | 關鍵 |
| 核心 | 核心 |
| 基础 | 基礎 |
| 能力 | 能力 |
| 价值 | 價值 |
| 创新 | 創新 |
| 技术创新 | 技術創新 |
| 商业创新 | 商業創新 |
| 模式 | 模式 |
| 业态 | 業態 |
| 场景 | 場景 |
| 应用 | 應用 |
| 案例 | 案例 |

【翻譯規則】
1. 保留 Markdown 格式結構
2. 所有標題使用臺灣正體中文
3. 術語嚴格按照對照表轉換
4. 保持原文語氣和專業風格
5. 數字、英文、符號保持不變
6. 簡體中文成語/詞組轉為正體（如"宏观"→「宏觀」、「其他」→「其他」）

【內容過濾規則】
- 移除廣告圖片描述（如「立即購買」、「限時優惠」、「掃碼購物」等推廣內容）
- 移除關注/訂閱號引導（如「長按掃碼關注」、「掃碼訂閱」等）
- 移除活動誘導內容（如「立即參加」、「掃碼參與」、「報名從速」等）
- 移除與文章主題無關的裝飾性圖片和元素
- 移除文末的微信公眾號、社群媒體二維碼等推廣資訊
- 保留與主題相關的圖表、流程圖、技術架構圖等有價值的圖片引用

原文：
---
{content}
---

翻譯結果："""


# Title term mapping for TW conversion
TITLE_TERM_MAP = {
    '数据中心': '資料中心',
    '云计算': '雲端運算',
    '边缘计算': '邊緣運算',
    '数字化': '數位化',
    '超大规模': '超大規模',
    '高性能计算': '高效能計算',
    '主机托管': '主機代管',
    '网络安全': '網路安全',
    '人工智能': '人工智慧',
    '区块链': '區塊鏈',
    '大数据': '大數據',
    '物联网': '物聯網',
    '智能制造': '智慧製造',
    '配电室': '配電室',
    '受伤': '受傷',
    '爆炸': '爆炸',
    '急救': '急救',
    '发生': '發生',
    '发展': '發展',
    '趋势': '趨勢',
    '技术': '技術',
    '市场': '市場',
    '自动化': '自動化',
    '可持续': '可持續',
    '安全': '安全',
    '创新': '創新',
    '运营': '營運',
    '运维': '維運',
    '优化': '優化',
    '监控': '監控',
    '故障': '故障',
    '维护': '維護',
    '检测': '檢測',
    '管理': '管理',
    '系统': '系統',
    '设备': '設備',
    '方案': '方案',
    '建设': '建設',
    '投资': '投資',
    '项目': '項目',
    '企业': '企業',
    '行业': '產業',
    '服务': '服務',
    '平台': '平臺',
    '网络': '網路',
    '计算': '計算',
    '存储': '儲存',
    '处理': '處理',
    '分析': '分析',
}


def convert_title_to_tw(title: str) -> str:
    """Convert a title to Traditional Chinese (Taiwan) style."""
    result = title
    # Sort by length descending to avoid partial replacements
    for cn, tw in sorted(TITLE_TERM_MAP.items(), key=lambda x: -len(x[0])):
        result = result.replace(cn, tw)
    return result


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

        # Use specialized TW translation prompt for zh-TW
        if target_lang == "zh-TW":
            user_prompt = TRANSLATION_PROMPT_ZH_TW.format(content=doc.content)
            system_prompt = "你是一位專業的繁體中文翻譯專家，擅長臺灣用語習慣。請嚴格按照術語對照表翻譯，保持專業技術文章風格。"
            translated_title = convert_title_to_tw(doc.title)
        else:
            user_prompt = TRANSLATION_PROMPT.format(
                target_lang=target_lang,
                target_display=target_display,
                content=doc.content
            )
            translated_title = doc.title

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
            title=translated_title,
            content=translated_content.strip(),
            frontmatter={
                **doc.frontmatter,
                "lang": target_lang,
                "translated_from": doc.frontmatter.get("lang", "zh")
            }
        )