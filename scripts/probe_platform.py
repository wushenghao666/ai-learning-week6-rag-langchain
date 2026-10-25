"""Independently probe chat and embeddings; model listing alone proves neither."""
import json
import sys
from datetime import datetime, timezone
from pathlib import Path
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.generation import request_json, ModelError
from src.config import settings

def main():
    config = settings()
    report = {'time_utc': datetime.now(timezone.utc).isoformat(), 'base': config['base'],
              'key_configured': bool(config['key']), 'checks': []}
    for path, payload in [('/models', None), ('/chat/completions',
        {'model': config['model'], 'messages': [{'role':'user', 'content':'只回复 好'}], 'max_tokens':8}),
        ('/embeddings', {'model': 'BAAI/bge-small-zh-v1.5', 'input':['测试文本']}),
        ('/embeddings', {'model': 'GLM-Embedding-3', 'input':['测试文本']})]:
        entry = {'path': path, 'requested_model': payload.get('model') if payload else None}
        try:
            response = request_json(path, payload, config)
            if path == '/models':
                entry.update(ok=True, models=[x.get('id') for x in response.get('data', [])])
            elif path == '/chat/completions':
                text = response['choices'][0]['message']['content']
                entry.update(ok=bool(text), text=text)
            else:
                vector = response['data'][0]['embedding']
                entry.update(ok=bool(vector), dimension=len(vector))
        except (ModelError, KeyError, IndexError, TypeError) as exc:
            entry.update(ok=False, error=str(exc))
        report['checks'].append(entry)
    report['interpretation'] = '失败或缺少认证无法证明平台不支持该能力；当前账户能力需有效密钥分别确认。'
    target = ROOT / 'reports/platform-probe.json'
    target.parent.mkdir(exist_ok=True)
    target.write_text(json.dumps(report, ensure_ascii=False, indent=2), encoding='utf-8')
    print(json.dumps(report, ensure_ascii=False, indent=2))

if __name__ == '__main__':
    main()
