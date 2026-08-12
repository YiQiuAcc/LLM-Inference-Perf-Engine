import threading
import time
from dataclasses import dataclass, replace
from datetime import UTC, datetime
from rich.progress import Progress, SpinnerColumn, TextColumn, TimeElapsedColumn
from llmp.core.client import OllamaStressClient, VLLMStressClient
from llmp.core.metrics import StressMetrics
from llmp.utils.console import get_console
from llmp.utils.formatting import format_status_codes
from llmp.utils.tables import (
    build_config_table,
    build_gradient_table,
    build_results_table,
    wrap_panel,
)


@dataclass
class StressArgs:
    """压测配置参数, 由 cli.py 构造"""

    base_url: str
    model: str
    prompt: str
    concurrency: str  # 梯度模式为逗号分隔串, 否则单个数字串
    duration: int
    timeout: int
    backend: str  # "ollama" | "vllm"
    stream: bool
    gradient: bool = False


def _make_client(args: StressArgs):
    cls = VLLMStressClient if args.backend == "vllm" else OllamaStressClient
    return cls(args.base_url, args.model, args.prompt, timeout=args.timeout)


def worker_thread(
    client,
    metrics: StressMetrics,
    stop_event: threading.Event,
    use_stream: bool = False,
):
    while not stop_event.is_set():
        try:
            if use_stream:
                latency, response_time, token_count, status_code = (
                    client.send_stream_request()
                )
            else:
                latency, response_time, token_count, status_code = (
                    client.send_chat_request()
                )
            metrics.record_success(
                latency, response_time, token_count, status_code, stream=use_stream
            )
        except RuntimeError as e:
            metrics.record_failure(str(e))


def _status_line(summary: dict, elapsed: float, duration: int) -> str:
    """运行中单行动态状态文本(Progress description)"""
    req_per_sec = summary["success_count"] / elapsed if elapsed > 0 else 0.0
    return (
        f"[bold]{elapsed:.0f}s/{duration}s[/] "
        f"成功 [green]{summary['success_count']}[/] "
        f"失败 [red]{summary['failure_count']}[/] "
        f"吞吐 {req_per_sec:.1f} req/s "
        f"Token {summary['total_tokens']} "
        f"状态码 {format_status_codes(summary['status_codes'])}"
    )


def run_stress_test(args: StressArgs) -> StressMetrics:
    console = get_console()
    metrics = StressMetrics()
    stop_event = threading.Event()

    console.print(
        wrap_panel(
            f"启动配置 · {datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M:%S')}",
            build_config_table(
                base_url=args.base_url,
                model=args.model,
                backend=args.backend,
                concurrency=args.concurrency,
                duration=args.duration,
                stream=args.stream,
            ),
        )
    )

    console.print("[预热] 发送测试请求...")
    try:
        warmup_cls = VLLMStressClient if args.backend == "vllm" else OllamaStressClient
        warmup_client = warmup_cls(args.base_url, args.model, "Hello", timeout=30)
        with console.status("[bold yellow]预热请求进行中…[/]"):
            warmup_client.send_chat_request()
        console.print("[green]预热完成[/]")
    except RuntimeError as e:
        console.print(f"[red]预热失败: {e}[/]")
        console.print("[yellow]继续执行压测…[/]")

    threads = []
    for i in range(int(args.concurrency.split(",")[0])):
        client = _make_client(args)
        t = threading.Thread(
            target=worker_thread,
            args=(client, metrics, stop_event, args.stream),
            daemon=True,
            name=f"Worker-{i}",
        )
        t.start()
        threads.append(t)

    start_time = time.time()
    report_interval = max(args.duration // 10, 5)
    interrupted = False
    try:
        with Progress(
            SpinnerColumn(),
            TimeElapsedColumn(),
            TextColumn("{task.description}"),
            console=console,
            transient=True,
        ) as progress:
            task_id = progress.add_task("", total=None)
            elapsed = 0
            while elapsed < args.duration:
                time.sleep(min(report_interval, args.duration - elapsed))
                elapsed = time.time() - start_time
                if elapsed >= args.duration:
                    break
                progress.update(
                    task_id,
                    description=_status_line(
                        metrics.get_summary(), elapsed, args.duration
                    ),
                )
    except KeyboardInterrupt:
        interrupted = True
        console.print("[yellow]收到中断信号, 正在停止压测…[/]")
    finally:
        stop_event.set()
        for t in threads:
            t.join(timeout=5)

    elapsed = time.time() - start_time
    title = "压测结果(已中断)" if interrupted else "压测结果"
    console.print(
        wrap_panel(
            f"[bold green]{title}[/]",
            build_results_table(metrics.get_summary()),
            border_style="green",
            subtitle=f"历时 {elapsed:.1f}s",
        )
    )

    if interrupted:
        raise KeyboardInterrupt
    return metrics


def run_gradient_stress_test(args: StressArgs):
    console = get_console()
    concurrency_levels = [int(x) for x in args.concurrency.split(",")]
    per_stage_duration = args.duration

    all_results: list[tuple[int, dict]] = []

    for i, cc in enumerate(concurrency_levels):
        console.print(
            f"[bold cyan]阶段 {i + 1}/{len(concurrency_levels)}: 并发用户数 = {cc}[/]"
        )
        stage_args = replace(args, concurrency=str(cc))
        metrics = run_stress_test(stage_args)
        all_results.append((cc, metrics.get_summary()))

        if i < len(concurrency_levels) - 1:
            with console.status("[bold yellow]冷却 10 秒进入下一阶段…[/]"):
                time.sleep(10)
            console.print()

    console.print(
        wrap_panel(
            "[bold magenta]梯度压测结果对比[/]",
            build_gradient_table(all_results, per_stage_duration),
            border_style="magenta",
        )
    )
