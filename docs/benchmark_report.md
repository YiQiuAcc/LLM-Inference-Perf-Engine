# 压测性能报告 / 容量规划分析

> 本文档用于沉淀全链路压测实验数据与容量规划结论（对应 ROADMAP 阶段六）。
> 实验完成后，将测试数据与系统参数优化项记录于此，形成《私有化大模型性能工程白皮书》。

## 实验 1：长文本挑战（KV Cache 容量与碎片化）

- **负载：** `llm-perf review --path <target_project>`（长文本上下文 8K-32K Tokens）
- **对比对象：** Ollama vs vLLM（PagedAttention）
- **观察点：** KV Cache 分配比例、显存碎片化引发的崩溃/排队（Prometheus + DCGM 指标）

## 实验 2：并发极限发现（TTFT 拐点）

- **负载：** `llm-perf stress --concurrency 10,30,50,80,100 --gradient`
- **观察点：** 并发上升时 TTFT 由平缓走向陡峭的拐点（Knee Point），确定最大合理并发承载量
- **记录项：** 梯度并发结果对比表（并发 / 成功率 / 吞吐 / Avg TTFT / P95 TTFT / 总 Token）

## 实验记录

| 日期 | 硬件 | 引擎/模型 | 实验 | 结论 |
|------|------|-----------|------|------|
|      |      |           |      |      |
