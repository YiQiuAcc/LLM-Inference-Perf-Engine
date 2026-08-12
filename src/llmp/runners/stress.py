import argparse
import threading
import time
from datetime import UTC, datetime
from llmp.core.client import OllamaStressClient, VLLMStressClient
from llmp.core.metrics import StressMetrics


def _make_client(args):
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


def run_stress_test(args) -> StressMetrics:
    metrics = StressMetrics()
    stop_event = threading.Event()

    print(f"\n[LLMOps 压测启动] {datetime.now(tz=UTC).strftime('%Y-%m-%d %H:%M:%S')}")
    print(f"目标地址: {args.base_url}")
    print(f"模型: {args.model}")
    print(f"后端: {args.backend}")
    print(f"并发用户数: {args.concurrency}")
    print(f"持续时间: {args.duration} 秒")
    print(f"流式模式: {'是' if args.stream else '否'}")
    print(f"{'=' * 60}\n")

    print("[预热] 发送测试请求...")
    try:
        warmup_cls = VLLMStressClient if args.backend == "vllm" else OllamaStressClient
        warmup_client = warmup_cls(args.base_url, args.model, "Hello", timeout=30)
        warmup_client.send_chat_request()
        print("[预热] 完成\n")
    except RuntimeError as e:
        print(f"[预热] 失败: {e}")
        print("[警告] 继续执行压测...\n")

    threads = []
    for i in range(args.concurrency):
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
    try:
        elapsed = 0
        while elapsed < args.duration:
            time.sleep(min(report_interval, args.duration - elapsed))
            elapsed = time.time() - start_time
            if elapsed >= args.duration:
                break
            summary = metrics.get_summary()
            req_per_sec = summary["success_count"] / elapsed if elapsed > 0 else 0
            print(
                f"[{elapsed:.0f}s] "
                f"请求: {summary['success_count']} 成功 / "
                f"{summary['failure_count']} 失败 | "
                f"吞吐: {req_per_sec:.1f} req/s | "
                f"Token: {summary['total_tokens']} | "
                f"状态码: {summary['status_codes']}"
            )
    except KeyboardInterrupt:
        print("\n[中断] 用户手动停止压测")
    finally:
        stop_event.set()

    for t in threads:
        t.join(timeout=5)

    elapsed = time.time() - start_time
    print(f"\n[LLMOps 压测结束] 历时 {elapsed:.1f}s\n")
    print(metrics)

    return metrics


def run_gradient_stress_test(args):
    concurrency_levels = [int(x) for x in args.concurrency.split(",")]
    per_stage_duration = args.duration

    print(f"\n{'=' * 60}")
    print("梯度压测模式")
    print(f"{'=' * 60}")
    print(f"并发梯度: {concurrency_levels}")
    print(f"每阶段持续时间: {per_stage_duration}s\n")

    all_results: list[dict] = []

    for i, cc in enumerate(concurrency_levels):
        print(f"\n{'#' * 60}")
        print(f"阶段 {i + 1}/{len(concurrency_levels)}: 并发用户数 = {cc}")
        print(f"{'#' * 60}")

        stage_args = argparse.Namespace(
            base_url=args.base_url,
            model=args.model,
            prompt=args.prompt,
            concurrency=cc,
            duration=per_stage_duration,
            timeout=args.timeout,
            stream=args.stream,
            backend=args.backend,
        )

        metrics = run_stress_test(stage_args)
        all_results.append({"concurrency": cc, "metrics": metrics.get_summary()})

        if i < len(concurrency_levels) - 1:
            print("\n[冷却] 等待 10 秒进入下一阶段...\n")
            time.sleep(10)

    print(f"\n{'=' * 80}")
    print("梯度压测结果对比")
    print(f"{'=' * 80}")
    header = (
        f"{'并发':>6} | {'成功率':>8} | {'吞吐(req/s)':>12} | "
        f"{'Avg TTFT(ms)':>14} | {'P95 TTFT(ms)':>14} | {'总Token':>8}"
    )
    print(header)
    print("-" * 80)
    for r in all_results:
        m = r["metrics"]
        req_per_sec = m["success_count"] / (per_stage_duration or 1)
        line = (
            f"{r['concurrency']:>6} | {m['success_rate']:>8} | "
            f"{req_per_sec:>12.1f} | {m['avg_ttft_ms']:>14} | "
            f"{m['p95_ttft_ms']:>14} | {m['total_tokens']:>8}"
        )
        print(line)
    print(f"{'=' * 80}\n")
