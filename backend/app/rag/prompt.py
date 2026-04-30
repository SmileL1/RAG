"""Prompt 模板集中管理。"""
from __future__ import annotations

RAG_SYSTEM_PROMPT = """你是一个严谨的文档问答助手。你必须遵守以下规则：

1. 只根据【参考资料】中的内容回答问题。
2. 如果资料不足以回答，明确说"根据已有资料无法回答"，不要编造。
3. 回答时用简体中文。
4. 在答案中用 [1] [2] 等标记引用的资料编号，便于用户溯源。
5. 答案结构清晰：先给结论，再给依据。
"""


RAG_USER_PROMPT_TEMPLATE = """【参考资料】
{context}

【用户问题】
{question}

请基于上述资料回答。"""


HYDE_PROMPT_TEMPLATE = """你是一个文档检索助手。用户有一个问题，请你假设性地写一段可能回答这个问题的文档内容（200 字左右，风格像正式文档）。不要说"可能"、"也许"，就像从真实文档里摘的一样。

用户问题：{question}

请直接输出假设的文档段落："""


def format_context(chunks: list) -> str:
    """把检索到的 chunks 格式化为 Prompt 中的 context 段。"""
    lines = []
    for i, c in enumerate(chunks, start=1):
        meta = getattr(c, "metadata", {}) or {}
        filename = meta.get("filename", "未知文件")
        page = meta.get("page")
        loc = f"《{filename}》" + (f"第 {page} 页" if page else "")
        text = getattr(c, "text", "") or getattr(c, "content", "")
        lines.append(f"[{i}] (来自 {loc})\n{text}")
    return "\n\n".join(lines)
