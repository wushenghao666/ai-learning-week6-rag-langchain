const q = document.querySelector('#q');
const result = document.querySelector('#result');
const examples = document.querySelector('#examples');

function show(data) {
  const hits = (data.hits || []).map(h => `<article class="hit"><b>${h.citation} ${h.source} · ${h.section}</b><p>${h.text}</p></article>`).join('');
  result.innerHTML = `<h2>结果</h2><p><b>状态：</b>${data.status || 'error'} ${data.notice || data.error || ''}</p>${data.answer ? `<div class="answer">${data.answer.replaceAll('\n','<br>')}</div>` : ''}<h3>检索片段</h3>${hits || '<p>没有相关资料。</p>'}`;
}

async function ask() {
  result.innerHTML = '<h2>结果</h2><p>正在读取资料……</p>';
  try {
    const response = await fetch((window.RAG_API_BASE || '') + '/api/ask', {method:'POST', headers:{'Content-Type':'application/json'}, body: JSON.stringify({question:q.value, k:Number(document.querySelector('#k').value), retrieve_only:document.querySelector('#only').checked})});
    show(await response.json());
  } catch (error) { result.innerHTML = `<h2>结果</h2><p>请求失败：${error}</p>`; }
}

document.querySelector('#ask').addEventListener('click', ask);
fetch('/examples.json').then(r => r.json()).then(items => { examples.innerHTML = items.map(item => `<button class="example">${item.question}</button><small>${item.expected}</small>`).join(''); document.querySelectorAll('.example').forEach((button, i) => button.addEventListener('click', () => { q.value = items[i].question; })); });

