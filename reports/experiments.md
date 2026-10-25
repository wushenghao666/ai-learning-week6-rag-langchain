# 运行记录与可复查边界

日期：2026-10-25，本地执行。运行时间按各 JSONL 的 UTC 时间戳记录，博客日期为 10.25。

- `platform-probe-no-key.json`：实际无认证请求，三个接口均 HTTP 401。
- `platform-probe.json`：配置用户授权的后端密钥后重新探测；GLM-4-Flash 生成成功；BGE 平台模型名 HTTP 400；GLM-Embedding-3 返回 2048 维向量。保留账户返回的模型 ID 列表，无凭证。
- `retrieval-initial.jsonl`：24 题 × 两种检索 × k=2/4/6，共 144 条真实结果。资料、切分、向量、问题和 BM25 参数固定，只改变检索方式和 k。
- `retrieval-with-hybrid.jsonl`：加入 RRF 和重叠去重后的 216 条检索记录；前两种检索结果与初轮一致，新增组合检索 72 条。组合方法各取关键词与向量前 12 名，按 1/(60+rank) 相加，重叠超过短片段一半时去重。
- `answers-local-initial.jsonl`：无密钥期间的小型真实本地 Qwen2.5-0.5B-Instruct 探索，完成 2 题后因获得平台密钥主动中断，不是完整评估。无模拟答案。首题状态值不合法，次题同样未通过结构校验。
- `answers-api-vector4.jsonl`：GLM-4-Flash、vector k=4、temperature=0、max_tokens=1400、timeout=60，共 24 题。旧提示见 `prompt-baseline.txt`。消息包含文件、章节、完整检索文本，尚未显式增加 week 字段；模型手工复制 quote。
- `answers-api-hybrid6.jsonl`：GLM-4-Flash、hybrid k=6、max_tokens=1400，共 24 题，增加显式 week 以及周次和示例归因约束，模型仍手工复制 quote。配置及当时源码摘要见同名前缀 config JSON。
- `candidate-glm45.json`：GLM-4.5-Flash 的单题试用，回答接口适配问题成功；保持原始结果，不据此推断总体效果。
- `answers-glm45-pilot.jsonl`：GLM-4.5-Flash、hybrid k=6、max_tokens=2400、thinking=disabled，完成 8 题后因发现系统性引文抄写问题主动中断，不计为完整评估。
- `answers-final.jsonl`：最终固定 24 题；GLM-4.5-Flash、hybrid k=6、temperature=0、max_tokens=2400、thinking=disabled、timeout=60。使用编号原文单元，程序按 source/span 取回原文。模型返回的 model 标识另存为 served_model，未独立验证供应商实际底层权重。

最终改进同时涉及检索、上下文格式、生成模型和输出协议，不能把回答质量差异归因于其中单独一项。只有 k 对比是控制其他条件的检索参数实验。

严格依据命中按 `evaluation/questions.json` 中预先指定的 doc 和 any 文本锚点计算，跨周题要求所有组命中。该分数会漏掉其他文件中的等价依据。例如第四周回顾也能证明第三周的内存行为。题目和锚点未因结果而修改，逐题语义审阅对这类情况另作说明。

答案语义及引用支持由本次开发助手逐题审阅，未经过独立人工复核，不能当作外部权威基准。所有题都参与开发和回归，没有独立留出的测试集。结果仅适用于这批快照、问题、提示和当次接口响应，模型输出及外部平台可发生变化。

首次自动测试在受限沙箱中出现 8 项环境错误，涉及回环网络及临时目录权限；在正常本地权限下全部通过。后续增加组合检索、网络错误和编号引用测试，最终完整日志见 `tests.txt`。没有把环境错误计成模型回答失败，也没有把测试通过当作模型回答正确。
