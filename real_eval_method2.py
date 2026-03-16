#!/usr/bin/env python3
"""
方案2真实评测: 批量处理（来一批处理一批）
使用真实的SiFlow API进行评测
"""
import asyncio
import time
from eval.run_gold_eval_fixed import run_gold_eval_for_instance


async def run_single_instance(instance_id: str) -> dict:
    """运行单个实例的评测"""
    print(f"\n{'='*60}")
    print(f"开始评测: {instance_id}")
    print(f"{'='*60}")

    start = time.time()

    # 调用真实的评测函数（同步函数，在executor中运行）
    loop = asyncio.get_event_loop()
    result = await loop.run_in_executor(
        None,
        run_gold_eval_for_instance,
        instance_id,
        "2.0.0",  # image_version
        1800,     # timeout
        True,     # wait
        "gold",   # patch_type
        "",       # task_name_suffix
        "gold"    # method_name
    )

    elapsed = time.time() - start

    print(f"\n{'='*60}")
    print(f"完成: {instance_id} ({elapsed:.1f}s)")
    print(f"结果: {result.get('success', False)}")
    print(f"{'='*60}\n")

    return {
        "instance_id": instance_id,
        "success": result.get("success", False),
        "time": elapsed,
        "result": result
    }


async def batch_eval_method2(instances: list[str], max_concurrent: int = 1):
    """方案2: 批量处理，控制并发数"""
    print(f"\n{'='*70}")
    print(f"方案2: 批量处理（并发={max_concurrent}）")
    print(f"{'='*70}\n")

    semaphore = asyncio.Semaphore(max_concurrent)

    async def run_with_limit(instance_id):
        async with semaphore:
            return await run_single_instance(instance_id)

    start = time.time()
    results = await asyncio.gather(*[run_with_limit(i) for i in instances])
    total_time = time.time() - start

    print(f"\n{'='*70}")
    print(f"方案2完成: {len(results)}个实例, 总耗时: {total_time:.1f}s")
    print(f"{'='*70}\n")

    return results, total_time


async def main():
    """主函数"""
    # 使用1个实例进行测试
    test_instances = [
        "django__django-11276",
    ]

    print("开始方案2真实评测实验...")
    results, total_time = await batch_eval_method2(test_instances, max_concurrent=1)

    # 统计结果
    success_count = sum(1 for r in results if r["success"])
    print(f"\n✅ 成功: {success_count}/{len(results)}")
    print(f"⏱️  总耗时: {total_time:.1f}s")

    return results


if __name__ == "__main__":
    asyncio.run(main())
