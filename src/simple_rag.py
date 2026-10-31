"""A deliberately small local RAG example.

The project keeps the learning goal visible: load Markdown, split it, rank a few
matching passages, then optionally call an OpenAI-compatible chat API.
"""
from __future__ import annotations

import json
import os
import re
import urllib.error
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "raw"
INDEX = ROOT / "data" / "index" / "simple-index.json"


def load_env():
    path = ROOT / ".env"
    if path.exists():
        for line in path.read_text(encoding="utf-8-sig").splitlines():
            key, sep, value = line.partition("=")
            if sep and key.strip() and not key.lstrip().startswith("#"):
                os.environ.setdefault(key.strip(), value.strip().strip("\"'"))


def words(text: str) -> set[str]:
    text = text.lower()
    result = set(re.findall(r"[a-z0-9_]+", text))
    for run in re.findall(r"[\u4e00-\u9fff]+", text):
        result.update(run[i:i + 2] for i in range(max(1, len(run) - 1)))
    return result


def split_markdown(text: str, source: str, size: int = 700) -> list[dict]:
    heading = "资料"
    chunks = []
    buffer: list[str] = []

    def flush():
        body = "".join(buffer).strip()
        if not body:
            return
        for start in range(0, len(body), size):
            part = body[start:start + size].strip()
            if part:
                chunks.append({"source": source, "section": heading, "text": part})

    for line in text.splitlines(keepends=True):
        match = re.match(r"^#{1,6}\s+(.+?)\s*$", line)
        if match:
            flush()
            buffer.clear()
            heading = match.group(1)
        elif line.strip() != "---":
            buffer.append(line)
    flush()
    return chunks


def import_sources() -> int:
    """Validate that the checked-in snapshot is available."""
    RAW.mkdir(parents=True, exist_ok=True)
    files = sorted(RAW.glob("week*-*.md"))
    if not files:
        raise RuntimeError("data/raw 中没有资料快照")
    return len(files)


def build_index() -> list[dict]:
    import_sources()
    chunks = []
    for path in sorted(RAW.glob("week*-*.md")):
        chunks.extend(split_markdown(path.read_text(encoding="utf-8"), path.name))
    INDEX.parent.mkdir(parents=True, exist_ok=True)
    INDEX.write_text(json.dumps(chunks, ensure_ascii=False, indent=2), encoding="utf-8")
    return chunks


def load_index() -> list[dict]:
    if not INDEX.exists():
        return build_index()
    return json.loads(INDEX.read_text(encoding="utf-8"))


def retrieve(question: str, k: int = 4) -> list[dict]:
    question = (question or "").strip()
    if not question:
        raise ValueError("问题不能为空")
    if len(question) > 1000:
        raise ValueError("问题最多 1000 个字符")
    q = words(question)
    scored = []
    for chunk in load_index():
        overlap = q & words(chunk["text"] + " " + chunk["section"])
        score = len(overlap)
        if score:
            scored.append((score, chunk))
    scored.sort(key=lambda item: (-item[0], item[1]["source"], item[1]["section"]))
    result = []
    for rank, (score, chunk) in enumerate(scored[:max(1, min(k, 8))], 1):
        result.append({**chunk, "rank": rank, "score": score, "citation": f"[{rank}]"})
    return result


def prompt(question: str, hits: list[dict]) -> str:
    context = "\n\n".join(
        f"[{h['rank']}] 文件：{h['source']}；章节：{h['section']}\n{h['text']}"
        for h in hits
    )
    return (
        "你是个人学习资料助手。只依据给定资料回答。资料不足时直接说资料中没有依据。"
        "把资料事实和你的建议分开，并在结论后写引用编号。\n\n"
        f"问题：{question}\n\n资料：\n{context}"
    )


def answer(question: str, hits: list[dict]) -> dict:
    load_env()
    key = os.getenv("OPENAI_API_KEY", "")
    if not key:
        return {"status": "retrieval_only", "notice": "未配置 OPENAI_API_KEY，仅返回检索结果"}
    base = os.getenv("OPENAI_BASE_URL", "https://llmapi.paratera.com/v1").rstrip("/")
    model = os.getenv("OPENAI_MODEL", "GLM-4.5-Flash")
    body = json.dumps({"model": model, "temperature": 0, "messages": [
        {"role": "user", "content": prompt(question, hits)}
    ]}, ensure_ascii=False).encode("utf-8")
    request = urllib.request.Request(base + "/chat/completions", data=body, method="POST",
        headers={"Content-Type": "application/json", "Authorization": "Bearer " + key})
    try:
        with urllib.request.urlopen(request, timeout=45) as response:
            payload = json.loads(response.read().decode("utf-8"))
        content = payload["choices"][0]["message"]["content"]
        return {"status": "answered", "answer": content, "model": model}
    except (urllib.error.HTTPError, urllib.error.URLError, KeyError, json.JSONDecodeError) as exc:
        return {"status": "model_error", "error": f"{type(exc).__name__}: {exc}"}


def ask(question: str, k: int = 4, retrieve_only: bool = True) -> dict:
    hits = retrieve(question, k)
    result = {"question": question, "k": k, "hits": hits}
    if not hits:
        result.update(status="insufficient", notice="没有检索到相关资料")
    elif retrieve_only:
        result.update(status="retrieval_only", notice="只检索模式，未调用生成模型")
    else:
        result.update(answer(question, hits))
    return result
