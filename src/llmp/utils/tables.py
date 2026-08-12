"""rich 表格与面板构建器(只构建, 不打印)"""

from collections.abc import Mapping, Sequence
from typing import Any
from rich.console import RenderableType
from rich.panel import Panel
from rich.table import Table
from llmp.utils.formatting import format_errors, format_status_codes


def build_config_table(
    *,
    base_url: str,
    model: str,
    backend: str,
    concurrency: str,
    duration: int,
    stream: bool,
) -> Table:
    """启动配置两列表(配置项 | 值)"""
    table = Table(header_style="bold cyan")
    table.add_column("配置项", style="cyan")
    table.add_column("值")
    table.add_row("目标地址", base_url)
    table.add_row("模型", model)
    table.add_row("后端", backend)
    table.add_row("并发用户数", concurrency)
    table.add_row("持续时间", f"{duration} 秒")
    table.add_row("流式模式", "是" if stream else "否")
    return table


def build_results_table(summary: Mapping[str, Any]) -> Table:
    """压测结果两列表(指标 | 值), 直接消费 get_summary() 的格式化值"""
    table = Table(header_style="bold green")
    table.add_column("指标")
    table.add_column("值", justify="right")
    table.add_row("总请求数", str(summary["total_requests"]))
    table.add_row("成功", str(summary["success_count"]))
    table.add_row("失败", str(summary["failure_count"]))
    table.add_row("成功率", summary["success_rate"])
    table.add_row("生成 Token 总数", str(summary["total_tokens"]))
    if summary["avg_ttft_ms"] != "N/A":
        table.add_row("Stream TTFT 平均", f'{summary["avg_ttft_ms"]} ms')
        table.add_row("Stream TTFT P95", f'{summary["p95_ttft_ms"]} ms')
    if summary["avg_latency_ms"] != "N/A":
        table.add_row("Non-Stream Latency 平均", f'{summary["avg_latency_ms"]} ms')
        table.add_row("Non-Stream Latency P95", f'{summary["p95_latency_ms"]} ms')
    table.add_row("平均响应时间", f'{summary["avg_response_time_s"]} s')
    table.add_row("状态码分布", format_status_codes(summary["status_codes"]))
    if summary["errors"]:
        table.add_row("最近错误", format_errors(summary["errors"]))
    return table


def build_gradient_table(
    rows: Sequence[tuple[int, Mapping[str, Any]]], duration: int
) -> Table:
    """梯度对比六列表: 并发|成功率|吞吐(req/s)|Avg TTFT(ms)|P95 TTFT(ms)|总Token"""
    table = Table(header_style="bold magenta")
    table.add_column("并发", justify="right")
    table.add_column("成功率", justify="right")
    table.add_column("吞吐(req/s)", justify="right")
    table.add_column("Avg TTFT(ms)", justify="right")
    table.add_column("P95 TTFT(ms)", justify="right")
    table.add_column("总Token", justify="right")
    for concurrency, summary in rows:
        req_per_sec = summary["success_count"] / (duration or 1)
        table.add_row(
            str(concurrency),
            summary["success_rate"],
            f"{req_per_sec:.1f}",
            summary["avg_ttft_ms"],
            summary["p95_ttft_ms"],
            str(summary["total_tokens"]),
        )
    return table


def wrap_panel(
    title: str,
    content: RenderableType,
    border_style: str = "cyan",
    subtitle: str | None = None,
) -> Panel:
    """任意 renderable 包成带标题(可带副标题)的 Panel"""
    return Panel(
        content,
        title=title,
        border_style=border_style,
        subtitle=subtitle,
        padding=(1, 1),
        expand=False,
    )
