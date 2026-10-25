# 第四周：可持续运行的学习计划 Agent

本项目在第三周规则 Agent 的基础上，加入持久化会话、任务依赖、失败重试、进度更新和复盘评分。程序仍然使用 Python 标准库，运行时不需要在线大模型 API。

## 这周完成的功能

- 把学习目标规划成带编号的任务，并保存任务状态
- 支持任务之间的依赖关系，只有前置任务完成后才执行后续任务
- 把会话保存到 JSON 文件，下一次运行可以继续同一份计划
- 为工具调用提供有限次数的失败重试和错误记录
- 通过 `progress`、`run`、`review` 三个命令查看进度、执行可运行任务和生成复盘
- 使用确定性规则计算完成率、工具成功率和复盘建议

## 快速开始

```powershell
cd 'C:\Users\wushe\Documents\ChatGPT\week 4\ai-learning-week4-agent-session'
python -m src.agent init '本周学习 Agent，完成工具调用练习并整理笔记' --session outputs\session.json
python -m src.agent progress --session outputs\session.json
python -m src.agent run --session outputs\session.json
python -m src.agent review --session outputs\session.json
```

运行测试：

```powershell
python -m unittest discover -s tests -v
```

## 工作流

```text
目标
 ↓
Planner：生成任务、工具和依赖
 ↓
Session：从 JSON 恢复计划与历史事件
 ↓
Runner：检查依赖，执行可运行任务，失败时重试
 ↓
Progress：写回任务状态与工具结果
 ↓
Reviewer：计算完成率并生成下一步建议
```

## 目录结构

```text
ai-learning-week4-agent-session/
├─ src/
│  ├─ agent.py       # CLI、初始化、运行、进度与复盘
│  ├─ planner.py     # 目标拆解与任务依赖
│  ├─ memory.py      # Session、Task、Event 的 JSON 持久化
│  └─ tools.py       # 受控工具、重试与工具注册表
├─ tests/test_session_agent.py
├─ examples/sample_session.json
├─ outputs/          # 命令行生成的会话文件
├─ requirements.txt
└─ README.md
```

## 设计边界

项目只处理本地学习计划，不联网、不调用真实大模型、不执行任意 shell 命令。规划器使用规则保证运行结果稳定。后续可以替换规划器，加入人工确认和真实模型，同时保留会话格式、工具白名单和评测指标。

## 可选的大模型规划

项目现在支持通过 OpenAI Responses API 生成任务计划。默认规划器仍然是本地规则规划器；只有显式加入 `--llm` 才会尝试调用模型。

Windows PowerShell 示例：

```powershell
$env:OPENAI_API_KEY = '你的 API Key'
$env:OPENAI_MODEL = 'gpt-5-mini'
python -m src.agent init '本周学习 RAG，安排 6 小时并完成一个检索练习' --llm --session outputs\llm-session.json
```

模型只负责返回任务草案，程序会检查任务数量、工具白名单和依赖关系。没有设置 API Key、网络请求失败或返回格式不符合要求时，程序自动回退到规则规划。请求设置了 `store: false`，项目不会把响应状态交给服务端持久保存；本地会话文件仍会保存执行计划和工具结果。

模型连接代码位于 `src/llm.py`，使用 Python 标准库发送 HTTPS 请求，没有新增第三方依赖。
