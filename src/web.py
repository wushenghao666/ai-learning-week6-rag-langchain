"""Loopback-only demonstration. No sessions, deployments or arbitrary file API."""
import argparse
import json
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from .config import ROOT, settings
from .embeddings import Embedder
from .retrieval import Retriever
from .service import RAGService

def handler_for(service):
    lock = threading.Lock()
    class Handler(BaseHTTPRequestHandler):
        def send_json(self, code, payload):
            body = json.dumps(payload, ensure_ascii=False).encode('utf-8')
            self.send_response(code)
            self.send_header('Content-Type', 'application/json; charset=utf-8')
            self.send_header('Content-Length', str(len(body)))
            self.send_header('Cache-Control', 'no-store')
            self.end_headers()
            self.wfile.write(body)

        def do_GET(self):
            if self.path == '/api/health':
                config = settings()
                self.send_json(200, dict(ok=True, generator=config['generator'],
                    model=config['model'] if config['generator']=='api' else 'Qwen2.5-0.5B-Instruct',
                    api_key_configured=bool(config['key']), chunks=len(service.retriever.chunks)))
            elif self.path == '/':
                body = (ROOT / 'web/index.html').read_bytes()
                self.send_response(200)
                self.send_header('Content-Type', 'text/html; charset=utf-8')
                self.send_header('Content-Length', str(len(body)))
                self.send_header('X-Content-Type-Options', 'nosniff')
                self.end_headers()
                self.wfile.write(body)
            else:
                self.send_json(404, {'error': '路径不存在'})

        def do_POST(self):
            if self.path != '/api/ask':
                self.send_json(404, {'error': '路径不存在'})
                return
            origin = self.headers.get('Origin')
            if origin and origin != f'http://{self.headers.get("Host")}':
                self.send_json(403, {'error': '仅接受同源请求'})
                return
            try:
                length = int(self.headers.get('Content-Length', '0'))
                if not 0 < length <= 16000:
                    raise ValueError('请求体长度应为 1 到 16000 字节')
                payload = json.loads(self.rfile.read(length))
                if not isinstance(payload, dict):
                    raise ValueError('请求体必须为对象')
                retrieve_only = payload.get('retrieve_only', True)
                if type(retrieve_only) is not bool:
                    raise ValueError('retrieve_only 必须为布尔值')
                with lock:
                    result = service.ask(payload.get('question'), payload.get('method', 'hybrid'),
                                         payload.get('k', 6), retrieve_only)
                self.send_json(502 if result['status'] in {'model_error','validation_error'} else 200, result)
            except (ValueError, TypeError) as exc:
                self.send_json(400, {'error': str(exc)})
            except Exception as exc:
                self.send_json(500, {'error': f'内部错误：{type(exc).__name__}'})
    return Handler

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument('--port', type=int, default=8006)
    args = parser.parse_args()
    service = RAGService(Retriever(embedder=Embedder()))
    server = ThreadingHTTPServer(('127.0.0.1', args.port), handler_for(service))
    print(f'Local RAG: http://127.0.0.1:{args.port}', flush=True)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()

if __name__ == '__main__':
    main()
