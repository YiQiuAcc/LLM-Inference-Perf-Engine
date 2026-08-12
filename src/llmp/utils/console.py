"""统一 rich Console 封装"""

from rich.console import Console

_console: Console | None = None


def get_console() -> Console:
    """全局共享 Console 单例(soft_wrap 防长行截断, highlight=False 防误高亮)"""
    global _console
    if _console is None:
        _console = Console(soft_wrap=True, highlight=False)
    return _console


def print_info(message: str) -> None:
    get_console().print(message)


def print_warning(message: str) -> None:
    get_console().print(f"[yellow]{message}[/]")


def print_error(message: str) -> None:
    get_console().print(f"[red]{message}[/]")
