"""纯文本格式化工具(无 I/O 副作用)"""

from collections.abc import Mapping, Sequence


def format_status_codes(status_codes: Mapping[int, int]) -> str:
    """状态码分布 {200: 45, 500: 3} -> "200:45, 500:3"; 空 dict 返回 "无" """
    if not status_codes:
        return "无"
    return ", ".join(f"{code}:{count}" for code, count in status_codes.items())


def format_errors(errors: Sequence[str], limit: int = 3) -> str:
    """最近错误压缩为单行, 超过 limit 条时截断并追加 "..." """
    if not errors:
        return "无"
    text = "; ".join(errors[:limit])
    if len(errors) > limit:
        text += "; ..."
    return text
