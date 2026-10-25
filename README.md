# 第六周：个人学习资料问答

把前五周的博客和项目 README 导入本地，完成资料 → 切分 → BGE 向量 → 检索 → 真实模型回答 → 引用校验。关键词 BM25 和向量余弦检索使用同一套资料和固定评估题。

第六周交付本地单次问答与评估。第七周继续完善 Web 应用、会话和公网部署。本仓库没有部署工作流，也没有远程发布。

## 当前机器直接运行

项目位置为 `C:\Users\wushe\Documents\ChatGPT\week 6`。已安装独立 `.venv`、下载本地模型并建立索引。

```powershell
.\.venv\Scripts\python.exe -m src.web
# 或 .\run.ps1
```

打开 http://127.0.0.1:8006/ 。默认只检索，取消只检索后使用后端 `.env` 中配置的真实模型。页面展示回答、文件、章节、逐字引文及实际检索片段；请求和引用校验失败会显示错误。服务只监听回环地址。

```powershell
.\.venv\Scripts\python.exe -m src.cli ask '第四周怎样实现会话恢复？' --method vector -k 4
.\.venv\Scripts\python.exe -m src.cli ask '第五周为什么适配 Chat Completions？' --method keyword --retrieve-only
```

CLI 输出 JSON，调用或校验失败退出码为 2。没有密钥仍能运行两种检索，不会生成模拟回答。

## 新环境安装

建议 Python 3.12+、4 GB 以上可用内存，首次安装需联网。CPU 运行，主依赖见 `requirements.txt`，本次完整环境见 `requirements-lock.txt`。BGE 权重约 95 MB；可选小生成模型约 1 GB。模型文件不提交 Git。

```powershell
python -m venv --without-pip .venv
python -m pip --python .\.venv\Scripts\python.exe install numpy==2.2.6 transformers==4.57.1
python -m pip --python .\.venv\Scripts\python.exe install torch==2.9.0 --index-url https://download.pytorch.org/whl/cpu
.\.venv\Scripts\python.exe scripts\download_models.py
.\.venv\Scripts\python.exe -m src.cli index
```

也可以运行 `scripts/setup.ps1 -Python <实际Python路径>`。这里使用父解释器的 pip 为独立环境安装依赖，避免当前捆绑运行时 ensurepip 的限制。Windows 商店别名不可运行时，需要指定真实解释器。现有快照足以独立建立索引，无需前五周仓库。

## 配置与平台能力

复制 `.env.example` 到 `.env`，填写生成模型地址、名称和密钥。也可设置同名后端环境变量，环境变量优先，修改后重启服务。前端不接触密钥，健康接口只返回是否配置。

本次分别实测了 `/models`、`/chat/completions`、`/embeddings`，记录在 [platform-probe.json](reports/platform-probe.json)。生成使用并行科技 `GLM-4-Flash`；向量使用本地 `BAAI/bge-small-zh-v1.5`，便于无密钥重建与检索。平台可用的生成能力和向量能力分别确认，不能从支持 Chat Completions 推断支持某个向量模型。

```powershell
.\.venv\Scripts\python.exe scripts\probe_platform.py
```

可选真实本地生成：先运行 `scripts/download_models.py --generation`，再设置 `RAG_GENERATOR=local`。该路径使用 Qwen2.5-0.5B-Instruct，属于真实模型，体积小且结构化引用能力有限。失败样例保存在 `reports/answers-local-initial.jsonl`；它只完成了中断前的两个探索样例，不能视为完整评估。

## 资料导入与索引重建

`data/raw/` 保存十份原始 Markdown 快照及清单；`data/index/` 保存可重新生成的片段元数据和向量。原始资料中存在旧说明也会原样保留。八周计划用于理解学习进度，未纳入当前问答范围。

导入器只读取 `src/corpus.py` 中列明的五篇博客和五份 README，不递归扫描目录，排除 `.env`、密钥、Git 文件、会话和输出文件。清单记录原始相对路径、标题、周次、类型与 SHA-256。每个片段保留章节路径、原文起止字符和稳定编号。

```powershell
.\.venv\Scripts\python.exe -m src.cli import --source-root 'C:\Users\wushe\Documents\ChatGPT'
.\.venv\Scripts\python.exe -m src.cli index --size 480 --overlap 80
```

相同命令覆盖本地快照或索引。导入后需要重建，服务需重启。资料摘要或向量模型变化时拒绝使用旧索引，避免混用向量空间。

## 实际参数

| 环节 | 参数 |
| --- | --- |
| 切分 | 先按 Markdown 章节，代码围栏内的井号不作标题；最多 480 字符、重叠 80；窗口后段优先换段/句末 |
| 片段数量 | 当前快照生成 112 段 |
| 向量 | BAAI/bge-small-zh-v1.5，固定 revision，CLS 池化、L2 归一化，512 维 |
| 编码 | 标题、周次、章节和原文一同编码，最长 512 token，CPU、批次 16、4 线程；问题加模型推荐的中文检索指令 |
| 索引 | NumPy 矩阵精确余弦检索，无独立向量数据库 |
| 关键词 | 中文连续双字词及英文/数字词，BM25 k1=1.5、b=0.75 |
| 检索 | 可选 k=2/4/6，后端允许 1–12，不设未经校准的语义分数拒答阈值 |
| 生成 | GLM-4-Flash，temperature=0，max_tokens=1400，超时 60 秒，无隐藏重试 |

完整实验和质量边界见 [实际评估报告](reports/evaluation.md)。固定证据锚点评分衡量指定依据的位置，不能替代逐题语义检查。

## 引用、拒答和资料边界

模型返回事实结论、引用编号、连续原文及独立建议。程序检查编号是否对应本次检索、引文是否逐字存在、事实是否带引用。失败保留原始输出并标记 `validation_error`，不会把它当作正常回答。

资料不足时使用 `insufficient`，页面明确显示不足。零检索片段时直接返回不足，不调用模型。向量相似度较高依然可能缺少答案，非空检索后的拒答依赖模型判断，固定无答案题用于检查这条边界。引文匹配仅证明来源存在，无法自动证明结论被支持，报告另行审阅。

资料放在用户消息的 `untrusted_evidence` 中。系统提示约束回答，程序没有提供 shell、文件修改或其他模型工具权限。建议单独展示；资料中的命令不会执行。网页使用 `textContent` 显示资料和模型输出。

## 测试与评估复现

```powershell
.\.venv\Scripts\python.exe -m unittest discover -s tests -v
.\.venv\Scripts\python.exe scripts\evaluate.py --name my-retrieval
.\.venv\Scripts\python.exe scripts\evaluate.py --answers --generator api --name my-answers
```

真实回答评估调用外部接口，产生模型用量。每次使用新名称，已有结果拒绝覆盖。24 题位于 `evaluation/questions.json`，逐题含类别、预期证据和质量标准。3 道无答案题不计入检索依据命中率分母；回答质量另按 24 题评价。每题的实际片段、分数、输出、错误及耗时即时写入 JSONL，接口收到文本、结构引用校验和语义正确分别统计。

自动测试使用合成向量隔离网络，覆盖资料范围、原文位置、索引失效、空输入、无匹配、引用错位、伪造引文、模型失败、缺少依据、密钥错误脱敏、HTTP 同源和路径边界。真实模型与真实向量结果由评估脚本验证。

## 模块与第七周接口

```text
src/corpus.py       白名单导入、章节与片段
src/embeddings.py   本地向量模型
src/retrieval.py    两种检索和索引
src/generation.py   模型请求、提示和引用校验
src/service.py      统一单次问答入口
src/cli.py          命令行
src/web.py          本地 HTTP 适配
web/index.html     简单页面
evaluation/        固定问题和审阅记录
reports/           实际结果、失败样例和报告
blog/              第六周博客副本
```

下一周可围绕 `RAGService.ask()` 增加交互、会话、持久化和部署，保留检索结果与引用结构。当前没有登录、会话历史、流式输出和公网服务。
