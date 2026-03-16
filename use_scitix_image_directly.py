#!/usr/bin/env python3
"""
直接使用 SciTix 镜像 URL 提交任务（无需查询镜像）
"""
import sys
from pathlib import Path

# 添加 vendor 目录到 Python 路径
sys.path.insert(0, str(Path(__file__).parent / '.vendor_siflow'))

from siflow_utils import create_siflow_client
from siflow.types import TaskVolume, TaskEnv, TaskUserSelectedInstance
from siflow_config import RESOURCE_POOL, VOLUME_MOUNT_DIR, VOLUME_ID


def submit_task_with_scitix_image():
    """
    使用 SciTix 镜像提交任务到 SiFlow 平台

    关键点：
    1. 使用 SiFlow 的 ACCESS_KEY（因为任务运行在 SiFlow 平台）
    2. 但指定 SciTix 的镜像 URL
    3. SiFlow 会从 SciTix registry 拉取镜像
    """

    print("\n" + "="*70)
    print("使用 SciTix 镜像提交任务到 SiFlow 平台")
    print("="*70 + "\n")

    # 创建 SiFlow 客户端（使用 SiFlow 的 ACCESS_KEY）
    client = create_siflow_client()
    print("✅ SiFlow 客户端创建成功")

    # SciTix 镜像的完整 URL
    # 格式: registry-{region}.scitix.ai/{namespace}/{image_name}:{tag}
    scitix_image_url = "registry-ap-southeast.scitix.ai/slimerl/slimev0.2.2"

    print(f"\n📦 镜像信息:")
    print(f"   镜像名称: slimerl/slimev0.2.2")
    print(f"   镜像URL: {scitix_image_url}")
    print(f"   来源: SciTix 平台")

    # 构建推理命令
    inference_cmd = """bash -c '
echo "=========================================="
echo "测试 SciTix sglang 镜像"
echo "=========================================="

# 检查 Python 和 sglang
python3 --version
pip3 list | grep -i sglang || echo "sglang not found"

# 检查 CUDA（如果有GPU）
nvidia-smi || echo "No GPU available"

# 简单的 Python 测试
python3 -c "
import sys
print(f\"Python: {sys.version}\")
try:
    import sglang
    print(f\"sglang imported successfully\")
except ImportError as e:
    print(f\"sglang import failed: {e}\")
"

echo "=========================================="
echo "测试完成"
echo "=========================================="
'"""

    print(f"\n📌 提交任务...")

    try:
        task_uuid = client.tasks.create(
            name_prefix="test-scitix-image",
            image="slimerl/slimev0.2.2",  # 镜像名称（简短形式）
            image_version="latest",        # 镜像版本（必需参数）
            image_url=scitix_image_url,   # 完整 registry URL
            image_type="custom",           # 自定义镜像
            type="pytorchjob",
            priority="medium",
            cmd=inference_cmd,
            workers=0,
            resource_pool=RESOURCE_POOL,
            instances=[
                TaskUserSelectedInstance(name="sci.c23-2", count_per_pod=1)
            ],
            task_env=[
                TaskEnv(name="TEST_VAR", value="scitix_image_test")
            ],
            volumes=[
                TaskVolume(mount_dir=VOLUME_MOUNT_DIR, volume_id=VOLUME_ID)
            ]
        )

        print(f"✅ 任务提交成功！")
        print(f"\n📋 任务信息:")
        print(f"   Task UUID: {task_uuid}")
        print(f"   镜像来源: SciTix (registry-ap-southeast.scitix.ai)")
        print(f"   运行平台: SiFlow (cn-shanghai/hercules)")

        print(f"\n💡 查看任务状态:")
        print(f"   python3 -c \"")
        print(f"import sys")
        print(f"sys.path.insert(0, '.vendor_siflow')")
        print(f"from siflow_utils import create_siflow_client")
        print(f"client = create_siflow_client()")
        print(f"status = client.tasks.get(uuid='{task_uuid}')")
        print(f"print(f'状态: {{status.status}}')\"")

        return task_uuid

    except Exception as e:
        print(f"\n❌ 任务提交失败: {e}")
        import traceback
        traceback.print_exc()
        return None


if __name__ == "__main__":
    print("\n" + "="*70)
    print("说明")
    print("="*70)
    print("""
这个脚本演示了如何在 SiFlow 平台上使用 SciTix 的镜像：

1. 认证: 使用 SiFlow 的 ACCESS_KEY（因为任务运行在 SiFlow）
2. 镜像: 指定 SciTix 的镜像 URL
3. 拉取: SiFlow 会自动从 SciTix registry 拉取镜像

关键点：
- 不需要 SciTix 的 ACCESS_KEY 来使用公开镜像
- 只需要知道完整的镜像 URL
- SiFlow 平台会处理跨平台的镜像拉取

镜像 URL 格式：
  registry-{region}.scitix.ai/{namespace}/{image_name}:{tag}

示例：
  registry-ap-southeast.scitix.ai/slimerl/slimev0.2.2
    """)

    result = submit_task_with_scitix_image()

    if result:
        print("\n✅ 成功！")
    else:
        print("\n❌ 失败")
