import argparse
import json
import sys

from .simple_rag import ask, build_index, import_sources


def main():
    parser = argparse.ArgumentParser(description="最小个人资料 RAG")
    sub = parser.add_subparsers(dest="command", required=True)
    sub.add_parser("import", help="检查资料快照")
    sub.add_parser("index", help="建立简单关键词索引")
    ask_parser = sub.add_parser("ask", help="提问")
    ask_parser.add_argument("question")
    ask_parser.add_argument("-k", type=int, default=4)
    ask_parser.add_argument("--answer", action="store_true", help="调用生成模型")
    args = parser.parse_args()
    try:
        if args.command == "import":
            print(f"资料快照：{import_sources()} 份")
        elif args.command == "index":
            print(f"索引片段：{len(build_index())} 个")
        else:
            print(json.dumps(ask(args.question, args.k, not args.answer), ensure_ascii=False, indent=2))
    except (ValueError, OSError, RuntimeError) as exc:
        print(f"{type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
