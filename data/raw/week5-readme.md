# 第五周：Agent 可视化任务控制台

在第四周的 Planner、Session、工具白名单和依赖执行器上增加 Web 界面。支持学习、作品集项目规划、面试准备和笔记整理。模型负责规划任务，本地工具输出摘要、清单、时间预算和复盘提醒；完成率统计工具执行进度。

## 公网地址

- 前端：https://wushenghao666.github.io/ai-learning-week5-agent-dashboard/
- 后端：https://ai-learning-week5-agent-dashboard.onrender.com
- 仓库：https://github.com/wushenghao666/ai-learning-week5-agent-dashboard

2026-10-13 前端与 Render 免费后端已上线并连接。后端已配置并行科技 Chat Completions 接口及 GLM-4-Flash，线上真实模型规划、四个工具执行及刷新恢复测试通过。

后端尚未配置时，Pages 自动使用浏览器本地模拟模型，并显示明确警告。模拟会话保存到当前浏览器的 localStorage，刷新后可以恢复。这里只保存演示会话和随机会话编号，不保存 API Key。

## 本地运行

真实模型统一生成摘要、清单、时间预算、复盘四个任务。模型输出校验失败时反馈具体错误并重新请求，最多 3 次；临时网络错误也会有限重试，认证失败直接提示。页面保留每次输出、失败原因和请求次数。用户明确给出的总小时数必须一致；未提供小时数时忽略模型推测时长并记录处理过程，工具显示每天 1 小时的建议。重试可能增加等待时间与模型用量。

```powershell
python -m src.web
```

打开 http://127.0.0.1:8000 。本地 Python 后端通过 JSON 文件保存状态。每个浏览器发送随机会话编号，后端将各份会话分开保存，文件不会提交到 GitHub。服务端通过锁串行执行写操作，防止同时点击时重复写入。

```powershell
python -m unittest discover -s tests -v
node tests/test_demo.cjs
```

11 项 Python 测试覆盖持久化、依赖、复盘、模拟警告恢复、会话隔离、空目标、非法编号、路径遍历和失败阻塞。Node 测试执行四类示例、刷新恢复、清空和失败依赖。Pages 工作流在发布前运行这些检查，发布后检查首页与四个静态资源的 HTTP 200。

## 三种运行状态

| 状态 | 条件 | 提示与结果 |
| --- | --- | --- |
| 浏览器模拟 | Pages 未配置后端地址 | 警告后端尚未连接，输出规则生成的预期结果 |
| 服务端模拟 | 开启模型选项，后端没有 OPENAI_API_KEY | 警告 Key 未配置，使用本地规则生成任务 |
| 真实模型规划 | 后端有 OPENAI_API_KEY，开启模型选项 | 请求 Responses API，校验工具和依赖后保存计划 |

关闭模型选项时使用规则规划。配置了 Key 后发生网络或模型错误会显示失败，不会把错误包装成真实模型成功。

## 免费托管方案：Pages + Render Free

GitHub Pages 发布 web/，Render Free 运行 Python 后端。免费托管额度不包含 OpenAI 模型费用。

1. 登录 https://dashboard.render.com/ ，创建 Web Service。
2. 使用公开仓库地址 https://github.com/wushenghao666/ai-learning-week5-agent-dashboard 。
3. Runtime 选择 Python 3，Build Command 为 pip install -r requirements.txt 。
4. Start Command 为 python -m src.web --host 0.0.0.0 --port $PORT 。
5. Instance Type 明确选择 Free。也可以使用仓库 render.yaml 创建 Blueprint。
6. 设置 AGENT_ALLOWED_ORIGIN 为 https://wushenghao666.github.io ，不包含仓库路径。
7. 如果需要真实模型，在 Render 环境变量中自行设置 OPENAI_API_KEY，可设置 OPENAI_MODEL。Key 无需发到聊天，不应提交到代码。
8. 后端成功部署后，访问 /api/health 检查 model_configured。
9. 在 GitHub 仓库 Settings → Secrets and variables → Actions → Variables 增加 AGENT_API_BASE，填写完整 HTTPS 后端地址，不带末尾斜杠。
10. 在 Actions 手动运行 Deploy web to GitHub Pages，前端将改为使用该后端。

Render 免费服务闲置 15 分钟后休眠，下次访问可能需要约一分钟唤醒；文件在重启、休眠或重新部署后会丢失。该版本用于学习演示，长期会话需要外部持久化存储。浏览器必须能访问 Render，Pages 不会代替浏览器转发请求。

模型调用默认限制为每个进程滚动 24 小时最多 20 次，可通过 AGENT_DAILY_MODEL_LIMIT 调整。计数会在进程重启后清空，不能用作硬性费用上限。正式公开提供长期服务前需要账户认证与持久化额度统计。

## 示例预期结果

- RAG，6 小时：学习清单，3 天，每天约 2 小时。
- 作品集网站，8 小时：内容整理、页面原型、布局检查清单，4 天，每天约 2 小时。
- 面试准备，4 小时：知识复习、题目练习、薄弱项复盘，2 天，每天约 2 小时。
- 读书笔记：摘录、主题归纳、复盘清单，未提供时长时建议每天 1 小时。

模拟模式四次执行依次达到 25%、50%、75%、100%。真实模型可以返回 2 到 5 个任务，数量和文字随响应变化。规划工具会生成材料，实际网页制作与面试练习需要使用者继续完成。
## 过程透明化

页面新增运行阶段条、模型与规划记录、任务依赖图和工具输入输出详情。

- 规划记录保存目标输入、公开规划指令、模型返回的任务草案、校验结果；真实模型返回用量时显示 Token 统计。
- 无 Key 的模拟规划也保存草案，并明确标记模拟来源。
- 工具时间线保存参数、结果或错误、尝试次数和服务端测得的执行耗时。
- 依赖图根据 depends_on 连线，已完成、可执行、等待和失败任务显示不同颜色。
- 网络请求期间显示当前操作，请求完成后显示保存的记录；本版采用完整响应展示，未实现逐 Token 推送。
- 刷新页面恢复完整记录。旧会话缺少规划记录时显示提示，重新创建后可以查看。

测试已扩展为 14 项 Python 测试；新增规划输出记录、失败校验记录、耗时恢复、密钥与内部推理排除检查。
# 并行科技接口配置

后端支持 OpenAI Responses 和兼容 Chat Completions 两种接口。在 Render Environment 中配置：

```text
OPENAI_API_STYLE=chat_completions
OPENAI_BASE_URL=https://llmapi.paratera.com/v1
OPENAI_MODEL=GLM-4-Flash
OPENAI_API_KEY=填写你自己的密钥
```

模型 ID 应从当前账户模型列表确认；上述模型仅为配置示例。保留环境变量名称 OPENAI_API_KEY 以兼容已有部署，该变量也可存放并行科技密钥。密钥仅在后端使用，不写入 GitHub Pages。默认接口仍为 OpenAI Responses。兼容接口保留原始文本输出、用量和工具执行记录。
