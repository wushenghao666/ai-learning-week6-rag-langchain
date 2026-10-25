"""Download pinned public model files into this repository, never into global cache."""
import argparse
import json
import sys
import urllib.request
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from src.embeddings import MODEL_ID, REVISION

def download(repo, revision, directory, files):
    directory.mkdir(parents=True, exist_ok=True)
    for name in files:
        target = directory / name
        if target.exists():
            continue
        print(f'Downloading {repo}/{name}', flush=True)
        url = f'https://huggingface.co/{repo}/resolve/{revision}/{name}'
        with urllib.request.urlopen(url, timeout=120) as response, target.with_suffix('.part').open('wb') as out:
            while block := response.read(1024*1024):
                out.write(block)
        target.with_suffix('.part').replace(target)
    (directory / 'download.json').write_text(json.dumps(dict(repo=repo, revision=revision)), encoding='utf-8')

if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--generation', action='store_true', help='Also download a small real local generator (~1 GB)')
    args = parser.parse_args()
    download(MODEL_ID, REVISION, ROOT / 'models/bge-small-zh-v1.5',
             ['config.json', 'tokenizer.json', 'tokenizer_config.json', 'special_tokens_map.json', 'vocab.txt', 'model.safetensors'])
    if args.generation:
        repo = 'Qwen/Qwen2.5-0.5B-Instruct'
        download(repo, '7ae557604adf67be50417f59c2c2f167def9a775', ROOT / 'models/Qwen2.5-0.5B-Instruct',
                 ['config.json', 'generation_config.json', 'tokenizer.json', 'tokenizer_config.json',
                  'vocab.json', 'merges.txt', 'model.safetensors'])
