#!/usr/bin/env python3
"""
Model Patch评估脚本 - 支持Agentless SEARCH/REPLACE格式

用法: python run_model_eval.py <instance_id>
"""

import sys
from pathlib import Path
from datasets import load_dataset

# 导入run_gold_eval的核心函数
from run_gold_eval_fixed import (
    get_image_version_for_instance,
    run_gold_eval_for_instance
)


def detect_patch_format(instance_id):
    """检测model patch格式"""
    model_dir = Path('/volume/ai-infra/rhjiang/SWE-bench-cc/predictions/model')
    
    # 优先检查agentless格式
    agentless_file = model_dir / f"{instance_id}.agentless_raw"
    diff_file = model_dir / f"{instance_id}.diff"
    
    if agentless_file.exists():
        return "agentless", agentless_file
    elif diff_file.exists():
        return "model", diff_file
    else:
        return None, None


def convert_agentless_to_diff(instance_id, agentless_file):
    """
    将Agentless SEARCH/REPLACE转换为git diff
    
    这个函数会被Docker容器内的脚本调用
    这里只是标记，实际转换在容器内进行
    """
    # 实际的转换会在容器内通过apply_agentless.py完成
    # 这里只需要确保.agentless_raw文件存在
    print(f"  📝 Agentless格式将在容器内转换为diff")
    return True


def run_model_patch_eval(instance_id):
    """运行model patch评估"""
    
    print("=" * 70)
    print(f"Model Patch 评估: {instance_id}")
    print("=" * 70)
    print()
    
    # 1. 检测patch格式
    print("📥 检测patch格式...")
    format_type, patch_file = detect_patch_format(instance_id)
    
    if not format_type:
        print(f"  ❌ 未找到patch文件 (.diff 或 .agentless_raw)")
        return {"success": False, "error": "Patch file not found"}
    
    if format_type == "agentless":
        print(f"  ✓ 检测到 Agentless SEARCH/REPLACE 格式")
        print(f"  ✓ 文件: {patch_file.name}")
        # Agentless格式需要特殊处理，但我们仍然使用patch_type="model"
        # 因为run_gold_eval_fixed会自动检测.agentless_raw文件
        patch_type = "model"
    else:
        print(f"  ✓ 检测到标准 git diff 格式")
        print(f"  ✓ 文件: {patch_file.name}")
        patch_type = "model"
    
    # 2. 调用评估（复用gold_eval的基础设施）
    print()
    result = run_gold_eval_for_instance(
        instance_id=instance_id,
        image_version=None,  # 自动选择版本
        timeout=1800,
        wait=True,
        patch_type=patch_type
    )
    
    # 3. 显示结果
    print()
    print("=" * 70)
    if result.get('success'):
        print("✅ 评估任务提交成功")
        print(f"   Task UUID: {result.get('task_uuid')}")
        print()
        print("检查结果:")
        print(f"   tail -100 eval_outputs/{instance_id}_test_output.txt")
    else:
        print(f"❌ 评估失败: {result.get('error')}")
    print("=" * 70)
    
    return result


if __name__ == '__main__':
    if len(sys.argv) < 2:
        print("用法: python run_model_eval.py <instance_id>")
        print()
        print("示例:")
        print("  python run_model_eval.py astropy__astropy-14539")
        sys.exit(1)
    
    instance_id = sys.argv[1]
    result = run_model_patch_eval(instance_id)
    
    sys.exit(0 if result.get('success') else 1)
