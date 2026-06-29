import sys
import os

sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from cli import build_parser
from runners import run_stress_test, run_gradient_stress_test


def main():
    args = build_parser().parse_args()

    print("""
╔══════════════════════════════════════════════════════════════╗
║           LLMOps 多线程并发压力测试工具                         ║
╚══════════════════════════════════════════════════════════════╝
    """)

    if args.gradient:
        run_gradient_stress_test(args)
    else:
        args.concurrency = int(args.concurrency)
        run_stress_test(args)


if __name__ == "__main__":
    main()
