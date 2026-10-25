"""BM25 Chinese bigram baseline versus exact cosine dense retrieval."""
import collections
import json
import math
import re
import time
from pathlib import Path
import numpy as np
from .config import ROOT
from .corpus import load_chunks, corpus_hash

def tokens(text):
    text = text.lower()
    result = re.findall(r'[a-z0-9_]+', text)
    for run in re.findall(r'[\u4e00-\u9fff]+', text):
        result += [run[i:i+2] for i in range(len(run)-1)] if len(run)>1 else [run]
    return result

def indexed_text(chunk):
    return f'第{chunk["week"]}周 {chunk["title"]}\n{chunk["section"]}\n{chunk["text"]}'

def build_index(embedder, directory=None, size=480, overlap=80):
    directory = Path(directory or ROOT / 'data/index')
    chunks = load_chunks(size, overlap)
    vectors = embedder.encode([indexed_text(c) for c in chunks])
    directory.mkdir(parents=True, exist_ok=True)
    meta = dict(size=size, overlap=overlap, corpus_hash=corpus_hash(chunks),
                embedding=embedder.signature, chunks=chunks, dimension=int(vectors.shape[1]))
    np.save(directory / 'vectors.npy', vectors, allow_pickle=False)
    (directory / 'index.json').write_text(json.dumps(meta, ensure_ascii=False, indent=2), encoding='utf-8')
    return meta

class Retriever:
    def __init__(self, directory=None, embedder=None):
        directory = Path(directory or ROOT / 'data/index')
        self.meta = json.loads((directory / 'index.json').read_text(encoding='utf-8'))
        self.chunks = self.meta['chunks']
        if corpus_hash(load_chunks(self.meta['size'], self.meta['overlap'])) != self.meta['corpus_hash']:
            raise ValueError('索引与原始资料不一致，请重建索引')
        self.embedder = embedder
        if embedder and embedder.signature != self.meta['embedding']:
            raise ValueError('向量模型已变化，请重建索引')
        self.vectors = np.load(directory / 'vectors.npy', allow_pickle=False)
        if self.vectors.shape != (len(self.chunks), self.meta['dimension']) or not np.isfinite(self.vectors).all():
            raise ValueError('索引向量损坏，请重建')
        self.bags = [collections.Counter(tokens(indexed_text(c))) for c in self.chunks]
        self.df = collections.Counter(t for bag in self.bags for t in bag)
        self.avgdl = sum(map(lambda b: sum(b.values()), self.bags)) / len(self.bags)

    def search(self, question, method='vector', k=4, on_event=None):
        if not isinstance(question, str) or not question.strip():
            raise ValueError('问题不能为空')
        if len(question) > 2000:
            raise ValueError('问题最多 2000 字符')
        if method not in {'keyword', 'vector', 'hybrid'} or type(k) is not int or not 1 <= k <= 12:
            raise ValueError('method 为 keyword/vector/hybrid，k 为 1 到 12')
        if method == 'hybrid':
            # Reciprocal rank fusion uses ranks, never mixes incompatible score scales.
            sparse = self.search(question, 'keyword', 12, on_event)
            dense = self.search(question, 'vector', 12, on_event)
            fused = {}
            by_id = {}
            for group in [sparse, dense]:
                for hit in group:
                    fused[hit['id']] = fused.get(hit['id'], 0) + 1/(60+hit['rank'])
                    by_id[hit['id']] = hit
            candidates = sorted(fused, key=lambda x:(-fused[x], x))
            selected = []
            removed = []
            for cid in candidates:
                hit = by_id[cid]
                # Overlapping windows should not consume multiple context slots.
                if any(hit['doc_id']==old['doc_id'] and
                       max(0,min(hit['end'],old['end'])-max(hit['start'],old['start'])) /
                       min(hit['end']-hit['start'],old['end']-old['start']) > 0.5 for old in selected):
                    removed.append(cid)
                    continue
                selected.append(dict(hit, rank=len(selected)+1, score=round(fused[cid],6)))
                if len(selected)==k:
                    break
            if on_event:
                on_event('fusion', '合并两路排名并去重', dict(rrf_constant=60,
                    candidate_count=len(candidates), removed_overlaps=removed,
                    ranking=[dict(id=cid, score=round(fused[cid],6),
                        keyword_rank=next((h['rank'] for h in sparse if h['id']==cid),None),
                        vector_rank=next((h['rank'] for h in dense if h['id']==cid),None)) for cid in candidates],
                    selected=[h['id'] for h in selected]))
            return selected
        if method == 'vector':
            if self.embedder is None:
                raise ValueError('向量模型尚未加载')
            begin = time.perf_counter()
            if on_event:
                on_event('embedding_started', '正在把问题编码为本地向量', {'model':'BAAI/bge-small-zh-v1.5'})
            vector = self.embedder.encode([question], query=True)[0]
            scores = self.vectors @ vector
            if on_event:
                on_event('embedding', '问题向量与余弦计算完成', dict(dimension=len(vector),
                    norm=round(float(np.linalg.norm(vector)),6), compared_chunks=len(self.chunks),
                    elapsed_ms=round((time.perf_counter()-begin)*1000,2)))
        else:
            scores = []
            for bag in self.bags:
                score = 0
                for token in set(tokens(question)):
                    freq = bag[token]
                    idf = math.log(1 + (len(self.bags)-self.df[token]+0.5)/(self.df[token]+0.5))
                    score += idf * freq * 2.5 / (freq + 1.5*(0.25+0.75*sum(bag.values())/self.avgdl))
                scores.append(score)
        order = sorted(range(len(scores)), key=lambda i: (-float(scores[i]), self.chunks[i]['id']))
        hits = [dict(self.chunks[i], rank=n+1, score=round(float(scores[i]), 6))
                for n, i in enumerate(order[:k]) if float(scores[i]) > 0]
        if on_event:
            on_event('ranking', '关键词排名完成' if method=='keyword' else '向量排名完成',
                dict(method=method, query_terms=sorted(set(tokens(question))) if method=='keyword' else None,
                     score_meaning='BM25 相关分数' if method=='keyword' else '余弦相似度；不代表答案正确概率',
                     ranking=[{key:h[key] for key in ['id','rank','score','title','section']} for h in hits]))
        return hits
