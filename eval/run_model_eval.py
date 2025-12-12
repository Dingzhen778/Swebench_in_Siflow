#!/usr/bin/env python3
"""
通用Patch评估脚本 - 支持不同方法生成的patch

用法: python run_model_eval.py <instance_id> [--method METHOD_NAME]
"""

import sys
import argparse
from pathlib import Path

# 导入run_gold_eval的核心函数
from run_gold_eval_fixed import (
    get_image_version_for_instance,
    run_gold_eval_for_instance
)
from method_config import get_method_config, DEFAULT_METHOD, list_methods


def find_patch_file(instance_id: str, method_config: dict) -> Path:
    """
    查找patch文件
    
    Args:
        instance_id: 实例ID
        method_config: 方法配置
        
    Returns:
        patch文件路径，如果不存在则返回None
    """
    # 优先从patches/{method_name}/目录查找
    patch_dir = Path(f"patches/{method_config['name']}")
    
    for ext in method_config['file_extensions']:
        candidate = patch_dir / f"{instance_id}{ext}"
        if candidate.exists():
            return candidate
    
    # 向后兼容：检查旧路径
    old_model_dir = Path("/volume/ai-infra/rhjiang/SWE-bench-cc/predictions/model")
    for ext in method_config['file_extensions']:
        candidate = old_model_dir / f"{instance_id}{ext}"
        if candidate.exists():
            return candidate
    
    return None


def run_patch_eval(instance_id: str, method_name: str = None):
    """
    运行指定方法的patch评估
    
    Args:
        instance_id: 实例ID
        method_name: 方法名称（如果为None，使用默认方法）
    """
    # 确定方法名称
    if method_name is None:
        method_name = DEFAULT_METHOD
    
    # 获取方法配置
    method_config = get_method_config(method_name)
    if not method_config:
        print(f"❌ 错误: 未找到方法配置 '{method_name}'")
        print(f"   可用方法: {', '.join(list_methods())}")
        return {"success": False, "error": f"Unknown method: {method_name}"}
    
    display_name = method_config.get('display_name', method_name)
    
    print("=" * 70)
    print(f"{display_name} Patch 评估: {instance_id}")
    print("=" * 70)
    print()
    
    # 查找patch文件
    print(f"📥 查找 {display_name} patch文件...")
    patch_file = find_patch_file(instance_id, method_config)
    
    if not patch_file:
        print(f"  ❌ 未找到patch文件")
        print(f"     查找路径: patches/{method_config['name']}/")
        print(f"     支持的扩展名: {method_config['file_extensions']}")
        return {"success": False, "error": "Patch file not found"}
    
    print(f"  ✓ 找到patch文件: {patch_file.name}")
    print(f"  ✓ 格式类型: {method_config['format_type']}")
    
    # 调用评估（复用gold_eval的基础设施）
    print()
    result = run_gold_eval_for_instance(
        instance_id=instance_id,
        image_version=None,  # 自动选择版本
        timeout=1800,
        wait=True,
        patch_type="custom",  # 非gold
        method_name=method_name  # 传递方法名
    )
    
    # 显示结果
    print()
    print("=" * 70)
    if result.get('success'):
        print("✅ 评估任务提交成功")
        if result.get('task_uuid'):
            print(f"   Task UUID: {result.get('task_uuid')}")
        if result.get('resolved'):
            print(f"   ✅ RESOLVED_FULL")
        elif result.get('resolution_status'):
            print(f"   状态: {result.get('resolution_status')}")
        print()
        log_dir = method_config['log_dir']
        print(f"检查结果:")
        print(f"   tail -100 {log_dir}/{instance_id}_test_output.txt")
    else:
        print(f"❌ 评估失败: {result.get('error')}")
    print("=" * 70)
    
    return result


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description="运行patch评估",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=f"""
示例:
  python run_model_eval.py django__django-13670
  python run_model_eval.py django__django-13670 --method agentless
  python run_model_eval.py django__django-13670 --method claude

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
    
    args = parser.parse_args()
    
    result = run_patch_eval(args.instance_id, args.method)
    
    sys.exit(0 if result.get('success') else 1)


if __name__ == '__main__':
    main()
