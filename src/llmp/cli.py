"""llmp 统一命令行入口(typer + rich)"""

from pathlib import Path
from typing import Annotated, Literal
import typer
from llmp.runners import run_gradient_stress_test, run_stress_test
from llmp.runners.stress import StressArgs
from llmp.utils.console import get_console

# 压测默认参数
DEFAULT_BASE_URL = "http://localhost:11434"
DEFAULT_MODEL = "deepseek-r1:7b"
DEFAULT_CONCURRENCY = "50"
DEFAULT_DURATION = 120
DEFAULT_TIMEOUT = 600

LONG_TEXT_PROMPT = (
    "请详细解释人工智能大语言模型的工作原理"
    "包括 Transformer 架构、注意力机制和训练过程。"
)

BANNER = """
╔══════════════════════════════════════════════════════════════╗
║           LLMOps 多线程并发压力测试工具                         ║
╚══════════════════════════════════════════════════════════════╝
"""

app = typer.Typer(
    name="llmp",
    help="LLM-Inference-Perf-Engine: 私有化大模型推理网关与流式性能工程系统",
    rich_markup_mode="rich",
    no_args_is_help=True,
    add_completion=False,
    context_settings={"help_option_names": ["-h", "--help"]},
)


@app.command()
def stress(
    base_url: Annotated[
        str, typer.Option("--base-url", help=f"推理网关地址(默认: {DEFAULT_BASE_URL})")
    ] = DEFAULT_BASE_URL,
    model: Annotated[
        str, typer.Option("--model", help=f"模型名称(默认: {DEFAULT_MODEL})")
    ] = DEFAULT_MODEL,
    prompt: Annotated[
        str, typer.Option("--prompt", help="推理 prompt(默认: 长文本 prompt)")
    ] = LONG_TEXT_PROMPT,
    concurrency: Annotated[
        str,
        typer.Option(
            "--concurrency", help=f"并发数；梯度模式用逗号分隔(默认: {DEFAULT_CONCURRENCY})"
        ),
    ] = DEFAULT_CONCURRENCY,
    duration: Annotated[
        int, typer.Option("--duration", help=f"持续时间秒(默认: {DEFAULT_DURATION})")
    ] = DEFAULT_DURATION,
    timeout: Annotated[
        int, typer.Option("--timeout", help=f"请求超时秒(默认: {DEFAULT_TIMEOUT})")
    ] = DEFAULT_TIMEOUT,
    backend: Annotated[
        Literal["ollama", "vllm"],
        typer.Option("--backend", help="推理引擎后端(默认: ollama, 可选: vllm)"),
    ] = "ollama",
    stream: Annotated[
        bool, typer.Option("--stream", help="启用流式 SSE 模式")
    ] = False,
    gradient: Annotated[
        bool, typer.Option("--gradient", help="启用梯度压测模式")
    ] = False,
) -> None:
    """多线程并发压力测试

    示例:
      基础压测:  llmp stress --concurrency 50 --duration 120
      梯度压测:  llmp stress --concurrency 10,30,50,80,100 --duration 60 --gradient
      流式压测:  llmp stress --concurrency 20 --stream --duration 60
    """
    args = StressArgs(
        base_url=base_url,
        model=model,
        prompt=prompt,
        concurrency=concurrency,
        duration=duration,
        timeout=timeout,
        backend=backend,
        stream=stream,
        gradient=gradient,
    )
    try:
        if gradient:
            run_gradient_stress_test(args)
        else:
            run_stress_test(args)
    except KeyboardInterrupt:
        get_console().print("[yellow]压测被用户中断[/]")
        raise typer.Exit(130) from None


@app.command()
def review(
    path: Annotated[Path | None, typer.Option("--path", help="目标项目路径")] = None,
) -> None:
    """本地代码库流式 Review(业务负载, 待实现)"""
    get_console().print(
        f"[yellow][llmp] review 子命令尚未实现[/] --path={path or '<未指定>'}"
    )
    raise typer.Exit(1)


def main() -> None:
    get_console().print(BANNER, highlight=False)
    app()


if __name__ == "__main__":
    main()
