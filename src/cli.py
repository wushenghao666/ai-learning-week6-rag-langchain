import argparse
import json
import sys
from pathlib import Path
from .config import ROOT

def main():
    parser = argparse.ArgumentParser(description='第六周个人资料 RAG')
    sub = parser.add_subparsers(dest='command', required=True)
    imp = sub.add_parser('import')
    imp.add_argument('--source-root', type=Path, required=True)
    idx = sub.add_parser('index')
    idx.add_argument('--size', type=int, default=480)
    idx.add_argument('--overlap', type=int, default=80)
    idx.add_argument('--directory', type=Path, default=ROOT / 'data/index')
    ask = sub.add_parser('ask')
    ask.add_argument('question')
    ask.add_argument('--method', choices=['keyword', 'vector', 'hybrid'], default='hybrid')
    ask.add_argument('-k', type=int, default=6)
    ask.add_argument('--retrieve-only', action='store_true')
    args = parser.parse_args()
    try:
        if args.command == 'import':
            from .corpus import import_sources
            result = import_sources(args.source_root)
            print(f'导入 {len(result)} 份资料快照')
        elif args.command == 'index':
            from .embeddings import Embedder
            from .retrieval import build_index
            meta = build_index(Embedder(), args.directory, args.size, args.overlap)
            print(json.dumps({k: v for k, v in meta.items() if k != 'chunks'}, ensure_ascii=False, indent=2))
            print(f'建立 {len(meta["chunks"])} 个片段')
        else:
            from .retrieval import Retriever
            from .embeddings import Embedder
            from .service import RAGService
            retriever = Retriever(embedder=Embedder() if args.method != 'keyword' else None)
            result = RAGService(retriever).ask(args.question, args.method, args.k, args.retrieve_only)
            print(json.dumps(result, ensure_ascii=False, indent=2))
            if result['status'] in {'model_error', 'validation_error'}:
                return 2
    except (ValueError, OSError, RuntimeError) as exc:
        print(f'{type(exc).__name__}: {exc}', file=sys.stderr)
        return 2
    return 0

if __name__ == '__main__':
    sys.exit(main())
