#!/bin/bash
# 快速检查456个评测的进度

echo "检查456个Model Patch评测进度..."
echo "================================================================"

# 查询平台任务
/minconda3/envs/swebench/bin/python << 'PYEOF'
from siflow_utils import create_siflow_client

client = create_siflow_client()
tasks = client.tasks.list(count=600)

mp_tasks = [t for t in tasks if hasattr(t, 'name') and 
            t.name.startswith('eval-') and '-mp-' in t.name]

# 统计状态
status_counts = {}
for task in mp_tasks[:456]:
    status = getattr(task, 'status', 'unknown')
    status_counts[status] = status_counts.get(status, 0) + 1

print("\nModel Patch任务状态 (最近456个):")
for status, count in sorted(status_counts.items()):
    print(f"  {status}: {count}")

completed = status_counts.get('Succeeded', 0) + status_counts.get('Failed', 0)
total = sum(status_counts.values())
print(f"\n完成进度: {completed}/{total} ({completed/total*100:.1f}%)")

if completed >= 456:
    print("\n✅ 所有任务已完成！可以运行 analyze_456_results.py 分析结果")
elif completed >= 400:
    print(f"\n⏳ 接近完成，还剩 {456-completed} 个")
else:
    print(f"\n⏳ 评测进行中，还剩 {456-completed} 个")
PYEOF

echo ""
echo "================================================================"
