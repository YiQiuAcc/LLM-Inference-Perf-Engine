import argparse
from configs.defaults import (
    DEFAULT_BASE_URL,
    DEFAULT_MODEL,
    DEFAULT_CONCURRENCY,
    DEFAULT_DURATION,
    DEFAULT_TIMEOUT,
    LONG_TEXT_PROMPT,
)


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="LLMOps 多线程并发压力测试脚本",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""示例:
  基础压测:  %(prog)s --concurrency 50 --duration 120
  梯度压测:  %(prog)s --concurrency 10,30,50,80,100 --duration 60 --gradient
  流式压测:  %(prog)s --concurrency 20 --stream --duration 60""",
    )
    parser.add_argument(
        "--base-url",
        type=str,
        default=DEFAULT_BASE_URL,
        help=f"推理网关地址(默认: {DEFAULT_BASE_URL})",
    )
    parser.add_argument(
        "--model",
        type=str,
        default=DEFAULT_MODEL,
        help=f"模型名称(默认: {DEFAULT_MODEL})",
    )
    parser.add_argument(
        "--prompt",
        type=str,
        default=LONG_TEXT_PROMPT,
        help="推理 prompt(默认: 长文本 prompt)",
    )
    parser.add_argument(
        "--concurrency",
        type=str,
        default=str(DEFAULT_CONCURRENCY),
        help=f"并发数；梯度模式用逗号分隔(默认: {DEFAULT_CONCURRENCY})",
    )
    parser.add_argument(
        "--duration",
        type=int,
        default=DEFAULT_DURATION,
        help=f"持续时间秒(默认: {DEFAULT_DURATION})",
    )
    parser.add_argument(
        "--timeout",
        type=int,
        default=DEFAULT_TIMEOUT,
        help=f"请求超时秒(默认: {DEFAULT_TIMEOUT})",
    )
    parser.add_argument(
        "--backend",
        type=str,
        default="ollama",
        choices=["ollama", "vllm"],
        help="推理引擎后端(默认: ollama, 可选: vllm)",
    )
    parser.add_argument("--stream", action="store_true", help="启用流式 SSE 模式")
    parser.add_argument("--gradient", action="store_true", help="启用梯度压测模式")
    return parser
