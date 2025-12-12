#!/bin/bash
# 检查第二批评测的进度

echo "==============================================="
echo "第二批Model Patch评测进度"
echo "==============================================="
echo ""

# 检查进程
if ps aux | grep batch_model_eval_50 | grep batch2 | grep -v grep > /dev/null; then
    echo "✅ 评测进程正在运行"
    echo "   PID: $(cat model_eval_batch2.pid 2>/dev/null || echo 'N/A')"
else
    echo "⚠️  评测进程未运行（可能已完成）"
fi

echo ""
echo "📊 当前状态:"
echo "───────────────────────────────────────────────"

# 检查进度文件
if [ -f "model_patch_50_progress.txt" ]; then
    cat model_patch_50_progress.txt
else
    echo "进度文件不存在"
fi

echo ""
echo "📁 输出文件:"
echo "───────────────────────────────────────────────"

# 检查结果文件
if [ -f "model_patch_50_results.json" ]; then
    echo "✅ 结果文件已生成"
    
    # 统计
    /minconda3/envs/swebench/bin/python << 'PYEOF'
import json
try:
    with open("model_patch_50_results.json", 'r') as f:
        data = json.load(f)
    summary = data.get('summary', {})
    print(f"   完成: {summary.get('total', 0)}/50")
    print(f"   RESOLVED_FULL: {summary.get('RESOLVED_FULL', 0)}")
    print(f"   Resolve率: {summary.get('resolve_rate', '0%')}")
except:
    print("   无法读取结果")
PYEOF
else
    echo "⏳ 结果文件尚未生成"
fi

echo ""
echo "📝 查看实时日志:"
echo "   tail -f model_eval_batch2.log"
echo ""
echo "==============================================="






