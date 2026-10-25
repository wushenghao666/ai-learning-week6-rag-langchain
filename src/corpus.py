"""Allowlisted Markdown snapshots and heading-aware, traceable chunks."""
import hashlib
import json
import re
from pathlib import Path
from .config import ROOT

SOURCES = [
    (1, '2026-09-20-fashion-mnist.md', 'ai-learning-week1-fashion-mnist'),
    (2, '2026-09-27-cnn-augmentation.md', 'ai-learning-week2-cnn-augmentation'),
    (3, '2026-10-03-study-agent.md', 'ai-learning-week3-study-agent'),
    (4, '2026-10-11-agent-session.md', 'ai-learning-week4-agent-session'),
    (5, '2026-10-18-agent-dashboard.md', 'ai-learning-week5-agent-dashboard'),
]

def digest(data):
    return hashlib.sha256(data).hexdigest()

def import_sources(base: Path):
    """Read exactly ten known files; never recursively scan projects or .env."""
    raw = ROOT / 'data/raw'
    raw.mkdir(parents=True, exist_ok=True)
    manifest = []
    for week, post, project in SOURCES:
        for kind, relative in [('blog', f'AI-learning/posts/{post}'),
                               ('readme', f'week {week}/{project}/README.md')]:
            path = base / relative
            content = path.read_text(encoding='utf-8-sig')
            if re.search(r'(?i)(?:sk-[a-z0-9_-]{16,}|Bearer\s+[a-z0-9_-]{20,})', content):
                raise ValueError(f'疑似密钥，停止导入：{relative}')
            name = f'week{week}-{kind}.md'
            (raw / name).write_text(content, encoding='utf-8')
            title = re.search(r'^title:\s*(.+)$', content, re.M)
            heading = re.search(r'^#\s+(.+)$', content, re.M)
            manifest.append(dict(id=f'w{week}-{kind}', week=week, kind=kind,
                source=relative, snapshot=name,
                title=title[1] if title else heading[1] if heading else name,
                sha256=digest(content.encode('utf-8'))))
    (raw / 'manifest.json').write_text(json.dumps(manifest, ensure_ascii=False, indent=2), encoding='utf-8')
    return manifest

def sections(text, title):
    lines = text.splitlines(keepends=True)
    offset = 0
    in_front = text.startswith('---\n') or text.startswith('---\r\n')
    fenced = False
    stack = []
    start = 0
    buffer = []
    for number, line in enumerate(lines):
        if in_front:
            offset += len(line)
            if number > 0 and line.strip() == '---':
                in_front = False
            start = offset
            continue
        if line.lstrip().startswith('```'):
            fenced = not fenced
        heading = re.match(r'^(#{1,6})\s+(.+?)\s*$', line) if not fenced else None
        if heading:
            if ''.join(buffer).strip():
                yield ' / '.join(x[1] for x in stack) or title, start, ''.join(buffer)
            level = len(heading[1])
            stack = [x for x in stack if x[0] < level] + [(level, heading[2])]
            buffer = []
            start = offset + len(line)
        else:
            buffer.append(line)
        offset += len(line)
    if ''.join(buffer).strip():
        yield ' / '.join(x[1] for x in stack) or title, start, ''.join(buffer)

def load_chunks(size=480, overlap=80):
    if size < 100 or not 0 <= overlap < size:
        raise ValueError('size 至少 100，overlap 必须在 [0, size) 内')
    raw = ROOT / 'data/raw'
    manifest = json.loads((raw / 'manifest.json').read_text(encoding='utf-8'))
    chunks = []
    for doc in manifest:
        path = raw / doc['snapshot']
        if path.resolve().parent != raw.resolve():
            raise ValueError('资料快照路径越界')
        text = path.read_text(encoding='utf-8')
        if digest(text.encode('utf-8')) != doc['sha256']:
            raise ValueError(f'资料摘要不符，请重新导入：{doc["id"]}')
        for section, offset, body in sections(text, doc['title']):
            pos = 0
            while pos < len(body):
                end = min(pos + size, len(body))
                if end < len(body):
                    # Prefer paragraph/sentence ends in the last third; overlap preserves context.
                    choices = [body.rfind(mark, pos + size * 2 // 3, end) for mark in ['\n\n', '。', '\n']]
                    boundary = max(choices)
                    if boundary >= 0:
                        end = boundary + 1
                fragment = body[pos:end]
                if fragment.strip():
                    chunks.append(dict(id=f'{doc["id"]}:{offset+pos}:{offset+end}',
                        doc_id=doc['id'], week=doc['week'], source=doc['source'],
                        snapshot=doc['snapshot'], title=doc['title'], section=section,
                        start=offset+pos, end=offset+end, text=fragment))
                if end == len(body):
                    break
                pos = max(pos + 1, end - overlap)
    return chunks

def corpus_hash(chunks):
    return digest(json.dumps(chunks, ensure_ascii=False, sort_keys=True).encode())
