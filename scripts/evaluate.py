"""Fixed gold evidence tests; raw outputs are appended before any aggregate score."""
import argparse
import json
import os
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.embeddings import Embedder
from src.retrieval import Retriever
from src.service import RAGService
from src.generation import SYSTEM
from src.config import settings
from src.corpus import digest

def evidence_scores(question, hits):
    groups = question['requirements']
    if not groups:
        return {'evidence_found': None, 'group_recall': None, 'first_relevant_rank': None}
    matched = [any(h['doc_id']==g['doc'] and any(a in h['text'] for a in g['any']) for h in hits) for g in groups]
    ranks = [i+1 for i,h in enumerate(hits) if any(h['doc_id']==g['doc'] and any(a in h['text'] for a in g['any']) for g in groups)]
    return dict(evidence_found=all(matched), group_recall=sum(matched)/len(groups),
                first_relevant_rank=min(ranks) if ranks else None, matched_groups=matched)

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--answers', action='store_true')
    parser.add_argument('--generator', choices=['api','local'])
    parser.add_argument('--name', default='baseline')
    parser.add_argument('--k', type=int, default=4)
    parser.add_argument('--method', choices=['keyword','vector','hybrid'], default='vector')
    parser.add_argument('--include-hybrid', action='store_true')
    args = parser.parse_args()
    if args.generator:
        os.environ['RAG_GENERATOR'] = args.generator
    questions = json.loads((ROOT / 'evaluation/questions.json').read_text(encoding='utf-8'))
    retriever = Retriever(embedder=Embedder())
    service = RAGService(retriever)
    reports = ROOT / 'reports'
    reports.mkdir(exist_ok=True)
    output = reports / f'{args.name}.jsonl'
    if output.exists():
        raise SystemExit('结果文件已存在；用新的 --name 保留旧实验')
    config = settings()
    metadata = dict(questions_sha256=digest((ROOT/'evaluation/questions.json').read_bytes()),
                    corpus_hash=retriever.meta['corpus_hash'], embedding=retriever.meta['embedding'],
                    model=config['model'], generator=config['generator'], system=SYSTEM,
                    temperature=0, max_tokens=config['max_tokens'], thinking=config['thinking'], timeout=config['timeout'],
                    source_files={name:digest((ROOT/'src'/name).read_bytes()) for name in
                                  ['retrieval.py','generation.py','corpus.py','embeddings.py']})
    (reports/f'{args.name}-config.json').write_text(json.dumps(metadata,ensure_ascii=False,indent=2),encoding='utf-8')
    runs = [(args.method, args.k)] if args.answers else [(method,k) for method in ['keyword','vector'] for k in [2,4,6]]
    if args.include_hybrid and not args.answers:
        runs += [('hybrid',k) for k in [2,4,6]]
    with output.open('w', encoding='utf-8') as stream:
        for method,k in runs:
            for q in questions:
                result = service.ask(q['question'], method, k, retrieve_only=not args.answers)
                row = dict(id=q['id'], category=q['category'], rubric=q['rubric'],
                           time_utc=datetime.now(timezone.utc).isoformat(), **result,
                           **evidence_scores(q, result['hits']))
                stream.write(json.dumps(row, ensure_ascii=False)+'\n')
                stream.flush()
                print(f'{method} k={k} {q["id"]} {result["status"]} evidence={row["evidence_found"]}', flush=True)
    summary = []
    rows = [json.loads(line) for line in output.read_text(encoding='utf-8').splitlines()]
    for method,k in runs:
        subset = [r for r in rows if r['method']==method and r['k']==k]
        answerable = [r for r in subset if r['evidence_found'] is not None]
        summary.append(dict(method=method, k=k, count=len(subset), answerable=len(answerable),
            evidence_all=sum(r['evidence_found'] for r in answerable),
            group_recall=sum(r['group_recall'] for r in answerable)/len(answerable),
            mrr=sum(1/r['first_relevant_rank'] if r['first_relevant_rank'] else 0 for r in answerable)/len(answerable),
            model_responses=sum('raw' in r for r in subset) if args.answers else None,
            validated=sum(r.get('validation_ok',False) for r in subset) if args.answers else None,
            model_errors=sum(r['status']=='model_error' for r in subset)))
    (reports / f'{args.name}-summary.json').write_text(json.dumps(summary,ensure_ascii=False,indent=2), encoding='utf-8')
    print(json.dumps(summary,ensure_ascii=False,indent=2))

if __name__ == '__main__':
    main()
