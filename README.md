# LLM-Inference-Perf-Engine: 私有化大模型推理网关与流式性能工程系统

本项目是一个面向大语言模型（LLM）私有化部署、高负载长文本业务支撑及全栈性能工程的闭学系统。系统构建了企业级的私有化大模型推理运维基础设施，并针对长文本流式推理中高昂的 **KV Cache 显存占用**、**首字延迟（TTFT）** 及 **网关吞吐瓶颈**，实现了从上层业务负载构建、流量网关控制、高性能基准测试到全链路白盒化监控的完整闭环。

---

## 系统核心架构

### 1. 业务负载层：本地代码库分析与自动化 Review 引擎 (`src/llmp/loadgen`，规划中)

- **真实长文本高负载场景构建**：计划开发 `loadgen` 模块，通过扫描本地 Python/C# 项目源码并进行拓扑组装，拼接成大规模的上下文 Prompt（单次请求可达 8K-32K Tokens），为底层推理集群提供真实、持续的长文本高负载业务流。
- **动态上下文调度**：支持代码文件的按需加载与 Token 预估，为评估后端推理引擎在长文本状态下的系统容量与显存表现提供关键的业务支撑。

### 2. 性能测试工程：自研流式多线程基准测试框架 (`src/llmp/runners`)

- **流式语义协议解析**：攻克传统 Web 压测工具（如 AB、WRK）无法解析大模型打字机流式响应（Server-Sent Events, SSE）的痛点，基于 Python 独立编写了高性能并发测试引擎 `stress.py`。
- **高精度多维指标捕获**：除传统的成功率与 QPS 外，自研脚本能够精准拆解 SSE 数据包，捕获并计算**首字延迟（TTFT）**、**间字延迟（ITI）**、**每秒生成 Token 数（Tokens/s）** 以及**输入/输出 Token 吞吐比**。
- **自动化梯度并发与系统冷却**：支持配置自动化梯度压力曲线（如 1->5->10 线程），并在测试阶段之间引入系统冷却期，以确保基准测试数据的客观性与可复现性。

### 3. 流量网关层：Nginx 流式代理与传输优化

- **消除流式传输截断与卡顿**：针对大模型流式响应的特征，对 Nginx 进行了定制化反向代理调优，通过关闭代理缓冲区（`proxy_buffering off`）等手段，确保推理 Token 能够毫无延迟地以“打字机式”送达客户端。
- **网络传输层网络优化**：通过配置 `tcp_nodelay on` 禁用 Nagle 算法，与应用层流式代理协同，最大化降低流式 Token 的端到端传输时延。

### 4. 观测与基础设施层：云原生容器化编排与白盒监控

- **一键编排技术栈**：利用 Docker Compose 统一调度模型推理后端（Ollama/vLLM）、Nginx 网关以及监控组件，解决异构硬件依赖与服务启动时序问题。
- **全链路白盒监控**：整合 Prometheus 与 NVIDIA DCGM Exporter，在长文本并发压测期间，秒级监控 GPU 显存利用率、动态 KV Cache 分配、流式请求排队状态等核心可观测性指标。

---

## 系统技术栈

- **开发语言与框架：** Python 3.12 (Threading, Stream API, AST/Token Parser)
- **容器与基础设施：** Docker / Docker Compose / GPU Pass-through (NVIDIA Container Toolkit)
- **AI 推理引擎：** Ollama / vLLM (支持 PagedAttention 显存优化后端)
- **流量路由与网关：** Nginx (Custom Reverse Proxy)
- **可观测性监控：** Prometheus / Grafana / NVIDIA DCGM Exporter / Alertmanager

---

## 📂 项目文件结构说明

根据系统的物理布局，核心文件组织如下：

```text
├── config/                  # 基础设施配置文件（运维与网络）
│   ├── alertmanager/        # 告警通道与策略配置
│   ├── nginx/               # Nginx 反向代理与流式代理调优配置
│   └── prometheus/          # Prometheus 指标抓取规则与数据周期配置
├── docs/                    # 工程白皮书与报告
│   ├── ROADMAP.md           # 演进路线图
│   └── benchmark_report.md  # 压测性能报告/容量规划分析
├── src/                     # 核心 Python 源码 (src layout)
│   └── llmp/                # 统一包名 llmp
│       ├── cli.py           # 统一命令行入口 (llmp)
│       ├── core/            # 通信底层（client.py）与指标收集模型（metrics.py）
│       ├── loadgen/         # 业务负载层：本地代码库分析与自动化 Review 引擎
│       └── runners/         # 压测与基准测试执行引擎（stress.py 主逻辑）
├── docker-compose.yml       # 全栈组件一键容器化编排配置
└── pyproject.toml / uv.lock # 现代 Python 项目依赖与包管理 (uv)
```

# LLM-Inference-Perf-Engine: 私有化大模型推理网关与流式性能工程系统

本项目是一个面向大语言模型（LLM）私有化部署，基于高负载长文本业务的推理底座编排与全链路白盒化性能调优实践。

项目构建了完整的 LLMOps 基础设施，并在此之上开发了一款面向本地源码库的高负载长文本分析应用（`llmc`）。针对长文本流式推理中高昂的 **KV Cache 显存占用**、**首字延迟（TTFT）** 及 **网关吞吐瓶颈**，系统通过引入自研多线程梯度压测框架进行量化分析，并利用 Prometheus/Grafana 实现了硬件与引擎指标的白盒化监控与性能调优。

---

## 项目核心架构

### 1. 业务应用层：本地代码库分析与自动化 Review 引擎 (`src/llmp/loadgen`，规划中)

- **真实高负载场景构建**：计划开发 `loadgen` 模块，通过扫描本地 Python/C# 项目源码并进行拓扑组装，拼接成大规模的上下文 Prompt（单次请求可达 8k-32k Tokens），为底层推理集群提供真实、持续的长文本高负载业务流。
- **动态上下文调度**：支持代码文件的按需加载与 Token 预估，为评估后端推理引擎在长文本状态下的系统容量提供业务支撑。

### 2. 性能测试工程：自研流式多线程压测框架 (`src/llmp/runners`)

- **攻克传统网络压测痛点**：传统压测工具（如 AB、WRK）无法解析大模型打字机流式响应（Server-Sent Events, SSE）。本项目基于 Python 独立编写了高性能并发测试引擎 `stress.py`。
- **高精度多维指标捕获**：除传统的成功率与 QPS 外，自研脚本能够精准拆解 SSE 数据包，捕获并计算**首字延迟（TTFT）**、**间字延迟（ITI）**、**每秒生成 Token 数（Tokens/s）** 以及**输入/输出 Token 吞吐比**。
- **自动化梯度并发与系统冷却**：支持配置自动化梯度压力曲线（如 1->5->10 线程），并在测试阶段之间引入系统冷却期，以确保基准测试数据的客观性与可复现性。

### 3. 流量网关层：Nginx 流式代理与传输优化

- **消除流式传输截断与卡顿**：针对大模型流式响应的特征，对 Nginx 进行了定制化反向代理调优，通过关闭代理缓冲区（`proxy_buffering off`）等手段，确保推理 Token 能够毫无延迟地以“打字机式”送达客户端。

### 4. 观测与基础设施层：云原生容器化编排与白盒监控

- **一键编排技术栈**：利用 Docker Compose 统一调度模型推理后端（Ollama/vLLM）、Nginx 网关以及监控组件，解决异构硬件依赖与服务启动时序问题。
- **全链路白盒监控**：整合 Prometheus 与 NVIDIA DCGM Exporter，在长文本并发压测期间，秒级监控 GPU 显存利用率、动态 KV Cache 分配、流式请求排队状态等核心可观测性指标。

---

## 🛠️ 项目技术栈

- **开发语言与框架：** Python 3.12 (Threading, Stream API, AST/Token Parser)
- **容器与基础设施：** Docker / Docker Compose / GPU Pass-through (NVIDIA Container Toolkit)
- **AI 推理引擎：** Ollama / vLLM (支持 PagedAttention 显存优化后端)
- **流量路由与网关：** Nginx (Custom Reverse Proxy)
- **可观测性监控：** Prometheus / Grafana / NVIDIA DCGM Exporter / Alertmanager

---

## 📂 项目文件结构说明

根据项目的物理布局（参考 `image_afe23d.png`），核心文件组织如下：

```text
├── config/                  # 基础设施配置文件（运维与网络）
│   ├── alertmanager/        # 告警通道配置
│   ├── nginx/               # Nginx 反向代理与流式调优配置
│   └── prometheus/          # Prometheus 指标抓取规则
├── docs/                    # 工程白皮书与报告
│   ├── ROADMAP.md           # 演进路线图
│   └── benchmark_report.md  # 压测性能报告/容量规划分析
├── src/                     # 核心 Python 源码 (src layout)
│   └── llmp/                # 统一包名 llmp
│       ├── cli.py           # 统一命令行入口 (llmp)
│       ├── core/            # 通信底层（client.py）与指标收集模型（metrics.py）
│       ├── loadgen/         # 业务负载层：本地代码库分析与自动化 Review 引擎
│       └── runners/         # 压测执行引擎（stress.py 主逻辑）
├── docker-compose.yml       # 全栈组件一键容器化编排配置
└── pyproject.toml / uv.lock # 现代 Python 项目依赖管理 (uv)
```

---

## 快速开始与使用指南

### 1. 基础设施启动

确保本地已安装 `NVIDIA Container Toolkit`，在系统根目录下执行以下命令完成全栈编排服务的拉起：

```bash
docker compose up -d
```

### 2. 依赖环境安装（基于 uv）

项目采用现代包管理工具 `uv`，执行以下命令快速初始化虚拟环境并同步全量依赖：

```bash
uv sync
```

### 3. CLI 控制台统一调度

系统提供统一入口 `llmp` 进行各项子功能的调度：

- **执行代码库流式 Review（业务负载测试，待实现）：**

```bash
llmp review --path ./target_project
```

- **执行流式基准压力测试：**

```bash
llmp stress --concurrency 1,5,10 --duration 60
```
