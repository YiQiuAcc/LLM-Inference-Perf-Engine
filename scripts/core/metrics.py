import threading
import statistics
from typing import List, Dict


class StressMetrics:
    """压测指标收集器（线程安全）"""

    def __init__(self):
        self.lock = threading.Lock()
        self.success_count = 0
        self.failure_count = 0
        self.total_tokens = 0
        self.stream_ttft: List[float] = []
        self.nonstream_latency: List[float] = []
        self.response_times: List[float] = []
        self.status_codes: Dict[int, int] = {}
        self.errors: List[str] = []

    def record_success(
        self,
        latency: float,
        response_time: float,
        token_count: int,
        status_code: int,
        stream: bool = False,
    ):
        with self.lock:
            self.success_count += 1
            self.total_tokens += token_count
            if stream:
                self.stream_ttft.append(latency)
            else:
                self.nonstream_latency.append(latency)
            self.response_times.append(response_time)
            self.status_codes[status_code] = self.status_codes.get(status_code, 0) + 1

    def record_failure(self, error_msg: str):
        with self.lock:
            self.failure_count += 1
            self.errors.append(error_msg)

    def _percentile(self, values: List[float], p: float) -> float:
        if not values:
            return 0.0
        sorted_vals = sorted(values)
        idx = int(len(sorted_vals) * p)
        if idx >= len(sorted_vals):
            idx = len(sorted_vals) - 1
        return sorted_vals[idx]

    def get_summary(self) -> dict:
        with self.lock:
            total = self.success_count + self.failure_count
            avg_response = (
                statistics.mean(self.response_times) if self.response_times else 0.0
            )
            stream_avg = statistics.mean(self.stream_ttft) if self.stream_ttft else None
            stream_p95 = (
                self._percentile(self.stream_ttft, 0.95) if self.stream_ttft else None
            )
            nonstream_avg = (
                statistics.mean(self.nonstream_latency)
                if self.nonstream_latency
                else None
            )
            nonstream_p95 = (
                self._percentile(self.nonstream_latency, 0.95)
                if self.nonstream_latency
                else None
            )
            return {
                "total_requests": total,
                "success_count": self.success_count,
                "failure_count": self.failure_count,
                "success_rate": f"{(self.success_count / total * 100):.1f}%"
                if total > 0
                else "0.0%",
                "total_tokens": self.total_tokens,
                "avg_ttft_ms": f"{stream_avg * 1000:.1f}" if stream_avg else "N/A",
                "p95_ttft_ms": f"{stream_p95 * 1000:.1f}" if stream_p95 else "N/A",
                "avg_latency_ms": f"{nonstream_avg * 1000:.1f}"
                if nonstream_avg
                else "N/A",
                "p95_latency_ms": f"{nonstream_p95 * 1000:.1f}"
                if nonstream_p95
                else "N/A",
                "avg_response_time_s": f"{avg_response:.2f}",
                "status_codes": dict(sorted(self.status_codes.items())),
                "errors": self.errors[-10:] if self.errors else [],
            }

    def __str__(self) -> str:
        summary = self.get_summary()
        lines = [
            f"{'=' * 60}",
            "压测统计摘要 (Stress Test Summary)",
            f"{'=' * 60}",
            f"总请求数 (Total Requests): {summary['total_requests']}",
            f"成功 (Success): {summary['success_count']}  "
            f"失败 (Failure): {summary['failure_count']}  "
            f"成功率: {summary['success_rate']}",
            f"生成 Token 总数: {summary['total_tokens']}",
        ]
        if summary["avg_ttft_ms"] != "N/A":
            lines.append(
                f"Stream TTFT - 平均: {summary['avg_ttft_ms']} ms  "
                f"P95: {summary['p95_ttft_ms']} ms"
            )
        if summary["avg_latency_ms"] != "N/A":
            lines.append(
                f"Non-Stream Latency - 平均: {summary['avg_latency_ms']} ms  "
                f"P95: {summary['p95_latency_ms']} ms"
            )
        lines.append(f"平均响应时间 (Avg Response): {summary['avg_response_time_s']} s")
        lines.append(f"HTTP 状态码分布: {summary['status_codes']}")
        if summary["errors"]:
            lines.append("最近错误 (Recent Errors):")
            for err in summary["errors"]:
                lines.append(f"  - {err}")
        return "\n".join(lines)
