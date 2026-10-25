"""Shared application boundary for CLI, HTTP and evaluation."""
import time
from .generation import Generator, ModelError, messages_for
from .config import settings

def redact(value, key):
    if isinstance(value, str):
        return value.replace(key,'[REDACTED]') if key else value
    if isinstance(value, list):
        return [redact(x,key) for x in value]
    if isinstance(value, dict):
        return {k:redact(v,key) for k,v in value.items()
                if k.lower() not in {'authorization','api_key','reasoning_content','reasoning','chain_of_thought'}}
    return value

class RAGService:
    def __init__(self, retriever, generator=None):
        self.retriever = retriever
        self.generator = generator or Generator()

    def ask(self, question, method='hybrid', k=6, retrieve_only=False, on_event=None):
        start = time.perf_counter()
        trace = []
        key = settings()['key']
        def observe(stage, title, data):
            event=redact(dict(stage=stage,title=title,data=data,sequence=len(trace)+1,
                              elapsed_ms=round((time.perf_counter()-start)*1000,2)), key)
            trace.append(event)
            if on_event:
                on_event(event)
        observe('retrieval_started','开始检索本地资料',dict(method=method,k=k,query=question,
            indexed_chunks=len(self.retriever.chunks)))
        hits = self.retriever.search(question, method, k, on_event=observe)
        observe('retrieval_complete','已选出本次检索片段',{'hits':hits})
        context=messages_for(question,hits)
        observe('context','组织编号原文上下文',dict(sources=len(hits),
            chars=sum(len(h['text']) for h in hits),messages=context,
            generation_requested=not retrieve_only and bool(hits)))
        result = dict(question=question, method=method, k=k, hits=hits)
        if retrieve_only:
            result.update(status='retrieval_only', notice='只检索模式，未调用生成模型')
            observe('generation_skipped','已跳过生成模型',{'reason':'勾选了只检索，不发送模型 API 请求'})
        else:
            if not hits:
                observe('generation_skipped','没有匹配片段，跳过生成',{'reason':'缺少原文依据，直接返回资料不足'})
            try:
                result.update(self.generator.answer(question, hits, on_event=observe))
            except ModelError as exc:
                result.update(status='model_error', error=str(exc))
                observe('model_error','模型请求失败',{'error':str(exc)})
        observe('complete','本次处理结束',{'status':result['status']})
        result['trace']=trace
        result['elapsed_ms'] = round((time.perf_counter()-start)*1000, 2)
        return redact(result,key)
