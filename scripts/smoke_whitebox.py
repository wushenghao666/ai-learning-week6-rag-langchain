"""Opt-in live HTTP check of incremental events and backend credential filtering."""
import argparse
import json
import sys
import time
import urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.config import settings

def main():
    parser=argparse.ArgumentParser()
    parser.add_argument('--real',action='store_true',help='Also call the configured real generation model once')
    parser.add_argument('--name',default='whitebox',help='Unique report prefix; never overwrite a run')
    args=parser.parse_args()
    cases=[dict(question='第五周为什么适配 Chat Completions？',method='keyword',k=4,retrieve_only=True)]
    if args.real:
        cases.append(dict(question='现有第五周项目是否已经实现用户登录？',method='hybrid',k=6,retrieve_only=False))
    summaries=[]
    output=ROOT/'reports'/f'{args.name}-live.jsonl'
    if output.exists():
        raise SystemExit('已存在实测记录，请另存后再运行，避免覆盖')
    with output.open('w',encoding='utf-8') as stream:
        for case in cases:
            req=urllib.request.Request('http://127.0.0.1:8006/api/ask/stream',
                data=json.dumps(case).encode(),headers={'Content-Type':'application/json'})
            begin=time.perf_counter()
            items=[]
            with urllib.request.urlopen(req,timeout=90) as response:
                for line in response:
                    if not line.strip():
                        continue
                    item=json.loads(line)
                    item['client_received_ms']=round((time.perf_counter()-begin)*1000,2)
                    items.append(item)
                    stream.write(json.dumps(dict(case=case,**item),ensure_ascii=False)+'\n')
                    stream.flush()
            assert items[-1]['type']=='result'
            result=items[-1]['result']
            stages=[i['event']['stage'] for i in items if i['type']=='event']
            serialized=json.dumps(items,ensure_ascii=False)
            key=settings()['key']
            assert not key or key not in serialized
            assert 'reasoning_content' not in serialized
            if case['retrieve_only']:
                assert result['status']=='retrieval_only'
                assert 'api_request' not in stages and 'api_response' not in stages
            else:
                assert 'api_request' in stages
                if result['status']=='model_error':
                    assert 'model_error' in stages and result.get('error')
                else:
                    assert stages.index('api_request')<stages.index('api_response')<stages.index('validation')
            summaries.append(dict(case=case,status=result['status'],stages=stages,
                first_event_ms=items[0]['client_received_ms'],final_result_ms=items[-1]['client_received_ms'],
                credentials_absent=True,provider_reasoning_absent=True,error=result.get('error'),
                answer_generated=result['status']=='answered'))
    (ROOT/'reports'/f'{args.name}-smoke.json').write_text(json.dumps(summaries,ensure_ascii=False,indent=2),encoding='utf-8')
    print(json.dumps(summaries,ensure_ascii=False,indent=2))

if __name__=='__main__':
    main()
