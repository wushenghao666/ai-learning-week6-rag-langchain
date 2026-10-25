"""Backend-only configuration. No credentials in returned metadata."""
import os
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]

def load_env():
    path = ROOT / '.env'
    if path.exists():
        for line in path.read_text(encoding='utf-8-sig').splitlines():
            if line.strip() and not line.lstrip().startswith('#'):
                key, sep, value = line.partition('=')
                if sep and key.strip() in {'OPENAI_BASE_URL', 'OPENAI_MODEL', 'OPENAI_API_KEY',
                    'RAG_TIMEOUT', 'RAG_EMBED_PATH', 'RAG_GENERATOR', 'RAG_LOCAL_MODEL',
                    'RAG_MAX_TOKENS', 'RAG_THINKING'}:
                    os.environ.setdefault(key.strip(), value.strip().strip('\"\''))

def settings():
    load_env()
    return dict(base=os.getenv('OPENAI_BASE_URL', 'https://llmapi.paratera.com/v1').rstrip('/'),
                model=os.getenv('OPENAI_MODEL', 'GLM-4.5-Flash'),
                key=os.getenv('OPENAI_API_KEY', ''), timeout=float(os.getenv('RAG_TIMEOUT', '60')),
                embed=str(ROOT / os.getenv('RAG_EMBED_PATH', 'models/bge-small-zh-v1.5')),
                generator=os.getenv('RAG_GENERATOR', 'api'),
                max_tokens=int(os.getenv('RAG_MAX_TOKENS', '2400')),
                thinking=os.getenv('RAG_THINKING', 'default'),
                local=str(ROOT / os.getenv('RAG_LOCAL_MODEL', 'models/Qwen2.5-0.5B-Instruct')))
