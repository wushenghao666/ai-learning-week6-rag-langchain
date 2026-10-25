"""Offline delivery audit: quotes, snapshots, fixed-set coverage and secret exclusion."""
import json
import subprocess
from pathlib import Path
import sys
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.config import settings
from src.corpus import load_chunks
from src.generation import validate_answer

def main():
    chunks=load_chunks()
    ids={c['id'] for c in chunks}
    questions=json.loads((ROOT/'evaluation/questions.json').read_text(encoding='utf-8'))
    rows=[json.loads(s) for s in (ROOT/'reports/answers-final.jsonl').read_text(encoding='utf-8').splitlines()]
    assert len(rows)==24 and {r['id'] for r in rows}=={q['id'] for q in questions}
    citations=0
    for row in rows:
        for hit in row['hits']:
            assert hit['id'] in ids
            text=(ROOT/'data/raw'/hit['snapshot']).read_text(encoding='utf-8')
            assert text[hit['start']:hit['end']]==hit['text']
        answer=validate_answer(row['raw'],row['hits'])
        assert answer['citations']==row['citations']
        citations+=len(answer['citations'])
    blog=(ROOT/'blog/2026-10-25-personal-rag.md').read_text(encoding='utf-8')
    assert 'date: 2026-10-25' in blog and '10.25' in blog
    assert not any(x in blog for x in [chr(34),chr(0x201c),chr(0x201d),'不是','而是'])
    key=settings()['key']
    candidates=subprocess.check_output(['git','ls-files','--cached','--others','--exclude-standard','-z'],cwd=ROOT).split(b'\0')
    checked=0
    for encoded in candidates:
        if not encoded:
            continue
        path=ROOT/encoded.decode('utf-8')
        if path.is_file():
            assert not key or key.encode() not in path.read_bytes(), f'凭证出现在 {path.name}'
            checked+=1
    print(json.dumps(dict(ok=True,chunks=len(chunks),questions=len(rows),verified_citations=citations,
                          checked_repository_files=checked,blog_constraints=True),ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
