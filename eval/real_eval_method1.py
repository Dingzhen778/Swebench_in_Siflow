#!/usr/bin/env python3
"""
方案1真实评测: 消息队列 + Worker模式
使用真实的SiFlow API进行评测
"""
import asyncio
import time
from run_gold_eval_fixed import run_gold_eval_for_instance


async def worker(worker_id: int, queue: asyncio.Queue, results: list):
    """Worker进程：从队列拉取任务并执行"""
    while True:
        try:
            instance_id = await asyncio.wait_for(queue.get(), timeout=0.1)
        except asyncio.TimeoutError:
            break

        print(f"\n[Worker-{worker_id}] 开始处理: {instance_id}")
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

        print(f"[Worker-{worker_id}] 完成: {instance_id} ({elapsed:.1f}s)")

        results.append({
            "instance_id": instance_id,
            "success": result.get("success", False),
            "time": elapsed,
            "worker_id": worker_id,
            "result": result
        })

        queue.task_done()


async def queue_based_eval_method1(instances: list[str], num_workers: int = 1):
    """方案1: 消息队列 + Worker模式"""
    print(f"\n{'='*70}")
    print(f"方案1: 消息队列 + Worker模式（Workers={num_workers}）")
    print(f"{'='*70}\n")

    # 创建任务队列
    queue = asyncio.Queue()
    for instance_id in instances:
        await queue.put(instance_id)

    print(f"✅ 任务队列已创建: {len(instances)}个任务\n")

    # 启动Workers
    results = []
    workers = [
        asyncio.create_task(worker(i+1, queue, results))
        for i in range(num_workers)
    ]

    print(f"✅ 启动 {num_workers} 个Worker\n")

    # 等待所有任务完成
    start = time.time()
    await queue.join()
    await asyncio.gather(*workers)
    total_time = time.time() - start

    print(f"\n{'='*70}")
    print(f"方案1完成: {len(results)}个实例, 总耗时: {total_time:.1f}s")
    print(f"{'='*70}\n")

    return results, total_time


async def main():
    """主函数"""
    # 使用1个实例进行测试
    test_instances = [
        "django__django-11276",
    ]

    print("开始方案1真实评测实验...")
    results, total_time = await queue_based_eval_method1(test_instances, num_workers=1)

    # 统计结果
    success_count = sum(1 for r in results if r["success"])
    print(f"\n✅ 成功: {success_count}/{len(results)}")
    print(f"⏱️  总耗时: {total_time:.1f}s")

    return results


if __name__ == "__main__":
    asyncio.run(main())
