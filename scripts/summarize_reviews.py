"""Recalculate quality metrics from inspectable per-question semantic reviews."""
import json
import statistics
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]

def summarize(review_path):
    review=json.loads(review_path.read_text(encoding='utf-8'))
    rows=[json.loads(line) for line in (ROOT/'reports'/f'{review["run"]}.jsonl').read_text(encoding='utf-8').splitlines()]
    questions=json.loads((ROOT/'evaluation/questions.json').read_text(encoding='utf-8'))
    expected={q['id'] for q in questions}
    items={i['id']:i for i in review['items']}
    assert len(rows)==len(expected)==len(items)==24
    assert {r['id'] for r in rows}==set(items)==expected
    citation_cases=[r for r in rows if r.get('validation_ok') and r.get('claims')]
    for row in citation_cases:
        assert type(items[row['id']]['citations_support']) is bool
    absent={q['id'] for q in questions if q['category']=='absent'}
    summary=dict(run=review['run'], total=len(rows), model_responses=sum('raw' in r for r in rows),
        validated=sum(r.get('validation_ok',False) for r in rows),
        answer_correct=sum(i['answer_correct'] for i in items.values()),
        citation_cases=len(citation_cases), citations_support=sum(items[r['id']]['citations_support'] for r in citation_cases),
        absent_correct=sum(items[q]['answer_correct'] for q in absent), absent_total=len(absent),
        joint_pass=sum(items[r['id']]['answer_correct'] and
                       (items[r['id']]['citations_support'] is True if r.get('claims') else r['status']=='insufficient')
                       for r in rows),
        total_tokens=sum((r.get('usage') or {}).get('total_tokens',0) for r in rows),
        median_elapsed_ms=statistics.median(r['elapsed_ms'] for r in rows))
    return summary, review

def main():
    results=[summarize(ROOT/'evaluation'/name) for name in ['review-baseline.json','review-final.json']]
    (ROOT/'reports/quality-summary.json').write_text(json.dumps([r[0] for r in results],ensure_ascii=False,indent=2),encoding='utf-8')
    lines=['# 逐题语义审阅', '', '审阅者：本次开发助手，未经过独立人工复核。通过只代表本次固定题和快照。', '',
           '回答按核心问题的完整性及事实正确性评价；引用按所选原文是否支持全部事实评价。无事实结论的拒答题，引用支持记为不适用。', '']
    for summary,review in results:
        lines += [f'## {review["run"]}', '', '| 题目 | 回答正确 | 引用支持 | 审阅说明 |', '| --- | --- | --- | --- |']
        for item in review['items']:
            cite='通过' if item['citations_support'] else '未通过' if item['citations_support'] is False else '不适用'
            lines.append(f'| {item["id"]} | {"通过" if item["answer_correct"] else "未通过"} | {cite} | {item["note"]} |')
        lines.append('')
    (ROOT/'reports/question-review.md').write_text('\n'.join(lines),encoding='utf-8')
    print(json.dumps([r[0] for r in results],ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
