#!/usr/bin/env python3
"""
统一的评测入口脚本
支持不同方法的patch评测

用法:
  python run_eval.py <instance_id> --method <method_name>
  
示例:
  python run_eval.py django__django-13670 --method agentless
  python run_eval.py django__django-13670 --method claude
  python run_eval.py django__django-13670 --method gold
"""

import argparse
import sys
from pathlib import Path

# 添加当前目录到路径，以便导入模块
sys.path.insert(0, str(Path(__file__).parent))

from method_config import METHOD_CONFIGS, DEFAULT_METHOD, list_methods
from run_gold_eval_fixed import run_gold_eval_for_instance
from run_model_eval import run_patch_eval


def main():
    parser = argparse.ArgumentParser(
        description="SWE-bench Patch评测统一入口",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
示例:
  # 评测agentless方法（默认）
  python run_eval.py django__django-13670 --method agentless
  
  # 评测claude方法
  python run_eval.py django__django-13670 --method claude
  
  # 评测gold patch
  python run_eval.py django__django-13670 --method gold

可用方法: {', '.join(list_methods())}
        """
    )
    parser.add_argument("instance_id", help="Instance ID")
    parser.add_argument(
        "--method",
        default=DEFAULT_METHOD,
        choices=list_methods(),
        help=f"Patch生成方法 (默认: {DEFAULT_METHOD})"
    )
    parser.add_argument("--version", help="镜像版本（可选）")
    parser.add_argument("--timeout", type=int, default=1800, help="超时时间（秒）")
    parser.add_argument("--wait", action="store_true", default=True, help="等待任务完成")
    parser.add_argument("--no-wait", dest="wait", action="store_false", help="不等待任务完成")
    
    args = parser.parse_args()
    
    # 根据方法类型选择不同的处理逻辑
    if args.method == "gold":
        # Gold patch使用专门的函数
        result = run_gold_eval_for_instance(
            instance_id=args.instance_id,
            image_version=args.version,
            timeout=args.timeout,
            wait=args.wait,
            method_name="gold"
        )
    else:
        # 其他方法使用通用函数
        result = run_patch_eval(
            instance_id=args.instance_id,
            method_name=args.method
        )
    
    # 返回退出码
    if result.get("success"):
        if result.get("resolved"):
            return 0
        elif result.get("status") == "submitted":
            return 0
        else:
            return 1
    else:
        return 1


if __name__ == "__main__":
    sys.exit(main())

