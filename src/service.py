"""Shared application boundary for CLI, HTTP and evaluation."""
import time
from .generation import Generator, ModelError

class RAGService:
    def __init__(self, retriever, generator=None):
        self.retriever = retriever
        self.generator = generator or Generator()

    def ask(self, question, method='hybrid', k=6, retrieve_only=False):
        start = time.perf_counter()
        hits = self.retriever.search(question, method, k)
        result = dict(question=question, method=method, k=k, hits=hits)
        if retrieve_only:
            result.update(status='retrieval_only', notice='只检索模式，未调用生成模型')
        else:
            try:
                result.update(self.generator.answer(question, hits))
            except ModelError as exc:
                result.update(status='model_error', error=str(exc))
        result['elapsed_ms'] = round((time.perf_counter()-start)*1000, 2)
        return result
