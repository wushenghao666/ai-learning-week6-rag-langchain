"""Real local BGE embeddings: CLS pooling, L2 normalization, CPU."""
import numpy as np
from .config import settings

REVISION = '7999e1d3359715c523056ef9478215996d62a620'
MODEL_ID = 'BAAI/bge-small-zh-v1.5'
INSTRUCTION = '为这个句子生成表示以用于检索相关文章：'

class Embedder:
    def __init__(self):
        import torch
        from transformers import AutoModel, AutoTokenizer
        self.torch = torch
        torch.set_num_threads(4)
        path = settings()['embed']
        self.tokenizer = AutoTokenizer.from_pretrained(path, local_files_only=True)
        self.model = AutoModel.from_pretrained(path, local_files_only=True).eval()

    def encode(self, texts, query=False):
        vectors = []
        for begin in range(0, len(texts), 16):
            batch = texts[begin:begin+16]
            if query:
                batch = [INSTRUCTION + x for x in batch]
            inputs = self.tokenizer(batch, padding=True, truncation=True, max_length=512, return_tensors='pt')
            with self.torch.inference_mode():
                result = self.model(**inputs).last_hidden_state[:, 0]
                result = self.torch.nn.functional.normalize(result, p=2, dim=1)
            vectors.append(result.cpu().numpy())
        return np.concatenate(vectors)

    @property
    def signature(self):
        from pathlib import Path
        from .corpus import digest
        path = Path(settings()['embed'])
        # Pin the actual model and tokenizer files, so replacing a local model invalidates the index.
        return {'model': MODEL_ID, 'revision': REVISION, 'pooling': 'CLS/L2', 'max_tokens': 512,
                'files': {name: digest((path / name).read_bytes()) for name in
                          ['model.safetensors', 'config.json', 'tokenizer.json']}}
