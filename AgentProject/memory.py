"""
测控领域毕业论文多Agent写作系统
框架：搜索者 → 论文撰写者 → 审查修改者

依赖：
    pip install langchain langchain-community langchain-core dashscope pandas scikit-learn requests
"""

import os
import shutil
import time
import requests
import pandas as pd
from typing import TypedDict, Annotated, List

from pure_eval.utils import safe_name
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from langchain_core.messages import HumanMessage, AIMessage, SystemMessage
from langchain_community.llms import Tongyi
from langchain_core.output_parsers import StrOutputParser

# ===================== 配置 =====================
#调用你自己的apikey
os.environ["DASHSCOPE_API_KEY"] = "sk-1bfc9786c2554b59817d0c5e435a89eb"

def make_llm(temperature=0.7):
    return Tongyi(
        model_name="qwen-turbo",
        streaming=False,
        temperature=temperature,
    )


# ===================== 工具层 =====================

class SearchResult(TypedDict):
    title: str
    url: str
    snippet: str


# --- 本地 RAG 文献检索，"知识库.txt"来源于利用selenium制作的知网爬虫---
def load_knowledge(file="知识库.txt") -> list:
    if not os.path.exists(file):
        print(f"⚠️ 未找到本地知识库 {file}，跳过。")
        return []
    with open(file, "r", encoding="utf-8") as f:
        lines = [l.strip() for l in f if l.strip()]
    docs = []
    for line in lines:
        if " -||- " in line:
            try:
                title, year, url = line.split(" -||- ")
                docs.append({"title": title, "year": year, "url": url,
                              "text": f"{title} {year}"})
            except Exception:
                continue
    return docs


_docs = load_knowledge()
_df = pd.DataFrame(_docs) if _docs else pd.DataFrame(columns=["title", "year", "url", "text"])
_vec = TfidfVectorizer() if not _df.empty else None
_emb = _vec.fit_transform(_df["text"]) if _vec is not None and not _df.empty else None


def local_literature_search(query: str, top_k: int = 5) -> str:
    """从本地知识库 TF-IDF 检索相关文献。"""
    if _vec is None or _emb is None:
        return "（本地文献库为空）"
    q_emb = _vec.transform([query])
    sim = cosine_similarity(q_emb, _emb)[0]
    top = sim.argsort()[-top_k:][::-1]
    results = []
    for i in top:
        row = _df.iloc[i]
        results.append(f"[{row['year']}] {row['title']}  {row.get('url', '')}")
    return "\n".join(results) if results else "（未命中相关文献）"


# --- 2. 调用DuckDuckGo Instant Answer API ---
def web_search(query: str, max_results: int = 5) -> str:
    """
    使用 DuckDuckGo Instant Answer API 进行网络搜索。
    无需 API Key，适合学术关键词查询。
    """
    try:
        url = "https://api.duckduckgo.com/"
        params = {
            "q": query,
            "format": "json",
            "no_html": 1,
            "skip_disambig": 1,
        }
        resp = requests.get(url, params=params, timeout=10)
        data = resp.json()

        results = []

        # Abstract（词条摘要）
        if data.get("AbstractText"):
            results.append(f"【摘要】{data['AbstractText']}\n来源：{data.get('AbstractURL', '')}")

        # RelatedTopics（相关主题）
        for item in data.get("RelatedTopics", [])[:max_results]:
            if isinstance(item, dict) and item.get("Text"):
                results.append(f"• {item['Text']}\n  {item.get('FirstURL', '')}")

        if not results:
            return f"（DuckDuckGo 未返回关于 '{query}' 的摘要，建议换用更具体的英文关键词）"

        return "\n\n".join(results)

    except requests.exceptions.ConnectionError:
        return "（网络不可达，请检查网络连接）"
    except Exception as e:
        return f"（网络搜索异常：{e}）"


# --- 3. 学术搜索（Semantic Scholar 开放 API） ---
def academic_search(query: str, limit: int = 5) -> str:
    """
    使用 Semantic Scholar 免费 API 搜索学术论文。
    返回论文标题、年份、摘要、DOI。
    """
    try:
        url = "https://api.semanticscholar.org/graph/v1/paper/search"
        params = {
            "query": query,
            "limit": limit,
            "fields": "title,year,abstract,externalIds,url",
        }
        headers = {"User-Agent": "MeasurementControlPaperAgent/1.0"}
        resp = requests.get(url, params=params, headers=headers, timeout=15)
        data = resp.json()

        papers = data.get("data", [])
        if not papers:
            return f"（Semantic Scholar 未找到关于 '{query}' 的论文）"

        lines = []
        for p in papers:
            year = p.get("year", "N/A")
            title = p.get("title", "无标题")
            abstract = (p.get("abstract") or "")[:120].replace("\n", " ")
            doi = p.get("externalIds", {}).get("DOI", "")
            link = f"DOI: {doi}" if doi else p.get("url", "")
            lines.append(f"[{year}] {title}\n  摘要：{abstract}…\n  {link}")

        return "\n\n".join(lines)

    except requests.exceptions.ConnectionError:
        return "（网络不可达，无法访问 Semantic Scholar）"
    except Exception as e:
        return f"（学术搜索异常：{e}）"


# ===================== Agent 定义 =====================

class PaperState:
    """流转于三个 Agent 之间的状态对象。"""

    def __init__(self, topic: str):
        self.topic: str = topic
        self.search_report: str = ""      # 搜索者产出
        self.draft_paper: str = ""        # 撰写者产出
        self.final_paper: str = ""        # 审查修改者产出
        self.review_notes: str = ""       # 审查意见
        self.iteration: int = 0
        self.max_iterations: int = 2      # 最多审查-修改轮次


# ── Agent 1：搜索者 ──────────────────────────────────────────────────────────

SEARCHER_SYSTEM = """
你是一名专业学术搜索助手，专注于测控工程领域。
给定论文题目/主题，你需要：
1. 分析题目，拆解为 3-5 个检索关键词组合（中英文均可）。
2. 整合本地文献库结果与网络搜索结果。
3. 输出结构化的"文献综述素材报告"，包含：
   - 研究背景与意义（3-5 句）
   - 国内外研究现状（分条列举，含年份/来源）
   - 关键技术点梳理（传感器、信号调理、AD采集、算法等）
   - 可引用文献列表（编号格式）

输出语言：中文学术风格。
"""

def run_searcher(state: PaperState) -> PaperState:
    """Agent 1：搜索者，收集文献与背景资料。"""
    print("\n" + "="*60)
    print("🔍 [Agent 1 / 搜索者] 正在检索相关资料…")
    print("="*60)

    topic = state.topic

    # Step 1：生成关键词
    llm = make_llm(temperature=0.3)
    kw_messages = [
        SystemMessage(content="你是测控领域专家，根据论文题目生成 5 个中英文检索关键词，每行一个，不加编号。"),
        HumanMessage(content=f"论文题目：{topic}"),
    ]
    keywords_raw = (llm | StrOutputParser()).invoke(kw_messages)
    keywords = [k.strip() for k in keywords_raw.strip().splitlines() if k.strip()][:5]
    print(f"  关键词：{keywords}")

    # Step 2：检索
    search_parts = []

    # 本地文献
    print("  → 本地文献库检索…")
    local_res = local_literature_search(topic)
    search_parts.append(f"【本地文献库】\n{local_res}")

    # 学术搜索（英文关键词优先）
    for kw in keywords[:3]:
        print(f"  → 学术搜索：{kw}")
        res = academic_search(kw, limit=3)
        search_parts.append(f"【学术搜索 / {kw}】\n{res}")
        time.sleep(0.5)  # 避免触发限流

    # 网络搜索（中文关键词）
    for kw in keywords[3:5]:
        print(f"  → 网络搜索：{kw}")
        res = web_search(kw)
        search_parts.append(f"【网络搜索 / {kw}】\n{res}")

    raw_data = "\n\n".join(search_parts)

    # Step 3：LLM 整理为文献综述素材报告
    print("  → 整理文献综述素材…")
    report_messages = [
        SystemMessage(content=SEARCHER_SYSTEM),
        HumanMessage(content=f"论文题目：{topic}\n\n以下是检索到的原始资料，请整理为文献综述素材报告：\n\n{raw_data}"),
    ]
    report = (make_llm(temperature=0.4) | StrOutputParser()).invoke(report_messages)
    state.search_report = report

    print("\n✅ 搜索者完成，文献综述素材已生成。")
    return state


# ── Agent 2：论文撰写者 ──────────────────────────────────────────────────────

WRITER_SYSTEM = (
    "你是专业的测控工程毕业论文撰写专家。\n"
    "根据提供的文献综述素材，严格按以下结构生成完整的毕业论文正文：\n\n"
    "摘要（中英文）\n"
    "关键词（5-8 个）\n"
    "1 引言\n"
    "  1.1 研究背景与意义\n"
    "  1.2 国内外研究现状\n"
    "  1.3 本文主要工作\n"
    "2 系统总体方案\n"
    "  2.1 系统需求分析\n"
    "  2.2 总体架构设计\n"
    "  2.3 技术路线\n"
    "3 硬件设计\n"
    "  3.1 传感器选型与接口\n"
    "  3.2 信号调理电路\n"
    "  3.3 A/D 采集模块\n"
    "  3.4 主控电路设计\n"
    "4 软件设计\n"
    "  4.1 系统软件架构\n"
    "  4.2 数据采集程序\n"
    "  4.3 滤波/控制算法实现\n"
    "  4.4 通信协议设计\n"
    "5 实验与分析\n"
    "  5.1 实验平台搭建\n"
    "  5.2 功能测试\n"
    "  5.3 性能指标测试\n"
    "  5.4 结果分析\n"
    "6 误差分析\n"
    "  6.1 误差来源分析\n"
    "  6.2 误差补偿方法\n"
    "7 结论\n"
    "  7.1 研究成果总结\n"
    "  7.2 不足与展望\n"
    "参考文献\n\n"
    "要求：\n"
    "- 内容充实，每章至少 400 字\n"
    "- 含关键公式（LaTeX 格式，例如传递函数 G(s) = K/(Ts+1)）\n"
    "- 含表格描述（如'表 3.1 传感器参数对比'）\n"
    "- 引言含[1][2][3]等参考文献标注\n"
    "- 语言规范、学术化"
)


def run_writer(state: PaperState) -> PaperState:
    """Agent 2：论文撰写者，生成完整论文草稿。"""
    print("\n" + "="*60)
    print("✍️  [Agent 2 / 论文撰写者] 正在撰写论文…")
    print("="*60)

    review_hint = ""
    if state.review_notes:
        review_hint = f"\n\n【本次修改需参考的审查意见】\n{state.review_notes}\n请针对性地修正上述问题。"

    # 直接构造消息列表，完全绕过 ChatPromptTemplate 的花括号解析
    user_content = (
        f"论文题目：{state.topic}\n"
        f"文献综述素材：\n{state.search_report[:3000]}\n"
        f"{review_hint}\n\n"
        "请按结构生成完整论文（摘要至参考文献），尽量详尽："
    )
    messages = [
        SystemMessage(content=WRITER_SYSTEM),
        HumanMessage(content=user_content),
    ]

    llm = make_llm(temperature=0.6)
    draft = (llm | StrOutputParser()).invoke(messages)
    state.draft_paper = draft
    state.iteration += 1

    print(f"\n✅ 撰写者完成（第 {state.iteration} 稿）。")
    return state


# ── Agent 3：审查修改者 ──────────────────────────────────────────────────────

REVIEWER_SYSTEM = """
你是严格的毕业论文评审专家（测控工程方向）。
你的任务：
1. 逐章评审论文草稿，给出具体问题清单（格式：问题编号 | 章节 | 问题描述 | 改进建议）。
2. 综合评分（满分 100 分），分项：
   - 结构完整性（20分）
   - 内容深度（30分）
   - 学术规范（20分）
   - 技术准确性（20分）
   - 语言表达（10分）
3. 最终给出"通过" / "需修改后通过" / "重大修改"三档结论。

若评分 ≥ 85 且无重大问题，输出"【APPROVED】"作为结论的最后一行。
否则输出具体修改意见，供撰写者在下一轮修改。
"""

def run_reviewer(state: PaperState) -> PaperState:
    """Agent 3：审查修改者，评审论文并决定是否通过。"""
    print("\n" + "="*60)
    print("🔎 [Agent 3 / 审查修改者] 正在评审论文…")
    print("="*60)

    # 直接构造消息列表，绕过模板解析
    user_content = (
        f"论文题目：{state.topic}\n\n"
        f"以下是第 {state.iteration} 稿论文，请逐章评审：\n\n"
        f"{state.draft_paper}"
    )
    messages = [
        SystemMessage(content=REVIEWER_SYSTEM),
        HumanMessage(content=user_content),
    ]

    llm = make_llm(temperature=0.3)
    review = (llm | StrOutputParser()).invoke(messages)
    state.review_notes = review

    approved = "【APPROVED】" in review
    print("\n📋 评审意见（摘要）：")
    print(review[:500] + ("…" if len(review) > 500 else ""))

    if approved:
        print("\n✅ 审查通过！论文达到毕业设计要求。")
        state.final_paper = state.draft_paper
    else:
        print(f"\n⚠️  需要修改（当前第 {state.iteration} 稿，最多 {state.max_iterations} 轮）。")

    return state, approved


# ===================== 多 Agent 流程编排 =====================

def run_pipeline(topic: str) -> str:
    """
    主流程：搜索者 → 撰写者 → 审查修改者（循环直至通过或达到最大轮次）
    返回最终论文文本。
    """
    state = PaperState(topic)

    # Step 1：搜索者
    state = run_searcher(state)

    # Step 2 + 3：撰写者 ↔ 审查修改者（迭代）
    approved = False
    while not approved and state.iteration < state.max_iterations:
        state = run_writer(state)
        state, approved = run_reviewer(state)

        if not approved and state.iteration >= state.max_iterations:
            print(f"\n⚠️  已达最大修改轮次（{state.max_iterations}），输出当前最佳稿件。")
            state.final_paper = state.draft_paper

    return state.final_paper, state.review_notes


# ===================== 主交互入口 =====================

def save_paper(topic: str, paper: str, review: str):
    """将论文和评审意见保存到本地文件。"""
    save_dir=os.path.join(os.getcwd(), "saves")
    safe_name=topic.strip()
    for ch in ["//", "?" , "<" , ">", "," ,"*"]:
        safe_name=safe_name.replace(ch, "_")
    safe_name=safe_name[:50]
    paper_file = os.path.join(save_dir,safe_name+"_论文.md")
    review_file = os.path.join(save_dir,safe_name+"_评审意见.txt")

    with open(paper_file, "w", encoding="utf-8") as f:
        f.write("#"+ topic + "\n\n" +paper)
    with open(review_file, "w", encoding="utf-8") as f:
        f.write(review)

    print(f"\n💾 论文已保存：{paper_file}")
    print(f"💾 评审意见已保存：{review_file}")


def chat():
    print("=" * 60)
    print("🎓 测控领域毕业论文多Agent写作系统")
    print("   架构：搜索者 → 论文撰写者 → 审查修改者")
    print("=" * 60)
    print("输入论文题目开始生成，输入 exit 退出。\n")

    while True:
        topic = input("📌 请输入论文题目：").strip()
        if topic.lower() == "exit":
            print("👋 退出系统。")
            break
        if not topic:
            continue

        start = time.time()
        try:
            final_paper, review_notes = run_pipeline(topic)
        except Exception as e:
            print(f"\n❌ 流程异常：{e}")
            import traceback; traceback.print_exc()
            continue

        elapsed = time.time() - start

        print("\n" + "=" * 60)
        print("📄 最终论文")
        print("=" * 60)
        print(final_paper)

        print(f"\n⏱  总耗时：{elapsed:.1f}s")

        save_choice = input("\n是否保存论文到本地文件？(y/n) ").strip().lower()
        if save_choice == "y":
            save_paper(topic, final_paper, review_notes)

        again = input("\n是否继续生成另一篇论文？(y/n) ").strip().lower()
        if again != "y":
            break


if __name__ == "__main__":
    chat()