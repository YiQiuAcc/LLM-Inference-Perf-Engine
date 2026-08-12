"""llm-perf 统一命令行入口"""

import argparse
from llmp.runners import run_gradient_stress_test, run_stress_test

# 压测默认参数
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "deepseek-r1:7b"
DEFAULT_CONCURRENCY = 50
DEFAULT_DURATION = 120
DEFAULT_TIMEOUT = 600

LONG_TEXT_PROMPT = (
    "请详细解释人工智能大语言模型的工作原理"
    "包括 Transformer 架构、注意力机制和训练过程。"
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        prog="llm-perf",
        description="LLM-Inference-Perf-Engine: 私有化大模型推理网关与流式性能工程系统",
    )
    sub = parser.add_subparsers(dest="command", required=True)

    stress = sub.add_parser(
        "stress",
        help="多线程并发压力测试",
        description="LLMOps 多线程并发压力测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  基础压测:  llm-perf stress --concurrency 50 --duration 120
  梯度压测:  llm-perf stress --concurrency 10,30,50,80,100 --duration 60 --gradient
  流式压测:  llm-perf stress --concurrency 20 --stream --duration 60""",
    )
    stress.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_BASE_URL,
        help=f"推理网关地址(默认: {DEFAULT_BASE_URL})",
    )
    stress.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"模型名称(默认: {DEFAULT_MODEL})",
    )
    stress.add_argument(
        "--prompt",
        type=str,
        default=LONG_TEXT_PROMPT,
        help="推理 prompt(默认: 长文本 prompt)",
    )
    stress.add_argument(
        "--concurrency",
        type=str,
        default=str(DEFAULT_CONCURRENCY),
        help=f"并发数；梯度模式用逗号分隔(默认: {DEFAULT_CONCURRENCY})",
    )
    stress.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help=f"持续时间秒(默认: {DEFAULT_DURATION})",
    )
    stress.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"请求超时秒(默认: {DEFAULT_TIMEOUT})",
    )
    stress.add_argument(
        "--backend",
        type=str,
        default="ollama",
        choices=["ollama", "vllm"],
        help="推理引擎后端(默认: ollama, 可选: vllm)",
    )
    stress.add_argument("--stream", action="store_true", help="启用流式 SSE 模式")
    stress.add_argument("--gradient", action="store_true", help="启用梯度压测模式")
    stress.set_defaults(func=_run_stress)

    review = sub.add_parser(
        "review",
        help="本地代码库流式 Review（业务负载，待实现）",
        description="扫描本地源码库并拼接长文本上下文，为推理集群构建真实业务负载",
    )
    review.add_argument("--path", type=str, help="目标项目路径")
    review.set_defaults(func=_run_review)

    return parser


def _run_stress(args):
    if args.gradient:
        run_gradient_stress_test(args)
    else:
        args.concurrency = int(args.concurrency)
        run_stress_test(args)


def _run_review(_):
    print("[llm-perf] review 子命令尚未实现（业务负载层位于 src/llmp/loadgen/）")
    raise SystemExit(1)


def main():
    args = build_parser().parse_args()

    print("""
╔══════════════════════════════════════════════════════════════╗
║           LLMOps 多线程并发压力测试工具                         ║
╚══════════════════════════════════════════════════════════════╝
    """)

    args.func(args)


if __name__ == "__main__":
    main()
