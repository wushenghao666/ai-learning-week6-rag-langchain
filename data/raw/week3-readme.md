# 第三周：一个可追踪的学习计划 Agent

本项目用 Python 标准库实现一个小型、可复现的 Agent。它接收一个学习目标，先把目标拆成步骤，再根据步骤选择工具执行，最后把过程和结果整理成一份报告。

项目刻意不依赖在线大模型 API，先把 Agent 的基本结构做清楚：目标、规划、工具调用、状态记忆和最终回答。后续周次可以把规则规划器替换为真实 LLM，再增加网页搜索、文件读取和更长期的记忆。

## 功能

- 把自然语言学习目标拆成 2–4 个可执行步骤。
- 根据步骤自动选择 `calculator`、`summarize`、`checklist` 三个本地工具。
- 保存任务目标、工具调用记录和结果，形成可检查的短期记忆。
- 以 JSON 或人类可读的 Markdown 风格输出执行轨迹。
- 全部使用 Python 标准库，方便离线运行和阅读源码。

## 快速开始

```powershell
cd "C:\Users\wushe\Documents\ChatGPT\week 3\ai-learning-week3-study-agent"
python -m src.agent "我想在本周学习 agent，并安排 6 小时复习时间"
python -m src.agent "比较 12 / 3 和 5 * 8，并整理成检查清单" --json
```

运行测试：

```powershell
python -m unittest discover -s tests -v
```

## 一次运行会发生什么

```text
用户目标
  ↓
Planner：识别主题、时长和动作
  ↓
Tool selection：选择 checklist / calculator / summarize
  ↓
Executor：调用工具并记录输入输出
  ↓
Memory：保存步骤、结果和状态
  ↓
Reporter：输出最终计划与执行轨迹
```

例如输入“我想在本周学习 agent，并安排 6 小时复习时间”，Agent 会生成概念学习、动手实现、复盘三个步骤，并把 `6 小时`识别为计划约束。输入中出现算式时，它会调用安全的本地计算器；出现“总结/整理”时，会调用摘要工具。

## 目录结构

```text
ai-learning-week3-study-agent/
├─ src/
│  ├─ __init__.py
│  ├─ agent.py       # Agent 循环、规划器与命令行入口
│  ├─ tools.py       # 三个可注册的本地工具
│  └─ memory.py      # 运行记忆与轨迹记录
├─ tests/test_agent.py
├─ examples/tasks.json
├─ blog/2026-10-03-study-agent.md
├─ requirements.txt
└─ README.md
```

## 设计边界

这周只实现一个单轮、单进程的本地 Agent。它没有联网、没有真实模型调用，也不会自动修改文件或执行任意 shell 命令。这样可以把注意力放在 Agent 与普通函数的区别：Agent 根据目标决定下一步行动，并把工具结果带回到后续流程中。

下一步可以逐步加入：真实 LLM 的结构化输出、工具参数校验、持久化向量记忆、网页搜索、人工确认和评测集。本项目暂时不把这些功能混在第一版里。
