#!/usr/bin/env python3
"""
在 SiFlow 平台上使用 SciTix 的 slimerl 镜像进行推理
"""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / '.vendor_siflow'))

from siflow_utils import create_siflow_client
from siflow.types import TaskVolume, TaskUserSelectedInstance
from siflow_config import RESOURCE_POOL, VOLUME_MOUNT_DIR, VOLUME_ID


def submit_inference_task_with_slimerl():
    """
    使用 SciTix 的 slimerl 镜像提交推理任务到 SiFlow 平台
    """
    print("\n" + "="*70)
    print("使用 SciTix slimerl 镜像提交推理任务")
    print("="*70 + "\n")

    # 创建 SiFlow 客户端（使用 SiFlow 的 ACCESS_KEY）
    client = create_siflow_client()
    print("✅ SiFlow 客户端创建成功")

    # SciTix slimerl 镜像的完整 URL
    slimerl_image_url = "registry-us-east.scitix.ai/hisys/slimerl:slimev0.2.2-8e52a0ab61d4dfbb0c392fb2b13b85f93400d3edefdf5f0c71edfb6f02fa0202"

    print(f"\n📦 镜像信息:")
    print(f"   名称: slimerl")
    print(f"   版本: slimev0.2.2")
    print(f"   URL: {slimerl_image_url}")
    print(f"   来源: SciTix 平台 (us-east)")

    # 构建推理命令
    inference_cmd = """bash -c '
set -e

echo "=========================================="
echo "SciTix slimerl 镜像测试"
echo "=========================================="

# 检查环境
echo "Python 版本:"
python3 --version

echo ""
echo "检查 sglang:"
pip3 list | grep -i sglang || echo "sglang not installed"

echo ""
echo "检查 GPU:"
nvidia-smi || echo "No GPU available"

echo ""
echo "Python 包列表:"
pip3 list | head -20

echo "=========================================="
echo "测试完成"
echo "=========================================="
'"""

    print(f"\n📌 提交任务...")

    try:
        # 注意：TaskEnv 使用 env_key 和 env_value，不是 name 和 value
        from siflow.types import TaskEnv

        task_uuid = client.tasks.create(
            name_prefix="slimerl-test",
            image="slimerl",                # 镜像名称
            image_version="slimev0.2.2",    # 镜像版本
            image_url=slimerl_image_url,    # 完整 registry URL
            image_type="custom",
            type="pytorchjob",
            priority="medium",
            cmd=inference_cmd,
            workers=0,
            resource_pool=RESOURCE_POOL,
            instances=[
                TaskUserSelectedInstance(name="sci.c23-2", count_per_pod=1)
            ],
            task_env=[
                TaskEnv(env_key="TEST_MODE", env_value="scitix_image", hide=False)
            ],
            volumes=[
                TaskVolume(mount_dir=VOLUME_MOUNT_DIR, volume_id=VOLUME_ID)
            ]
        )

        print(f"✅ 任务提交成功！")
        print(f"\n📋 任务信息:")
        print(f"   Task UUID: {task_uuid}")
        print(f"   镜像来源: SciTix (registry-us-east.scitix.ai)")
        print(f"   运行平台: SiFlow (cn-shanghai/hercules)")

        print(f"\n💡 查看任务状态:")
        print(f"   python3 -c \"")
        print(f"import sys; sys.path.insert(0, '.vendor_siflow')")
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
这个脚本演示了跨平台镜像使用：

1. 认证: 使用 SiFlow 的 ACCESS_KEY
2. 镜像: 使用 SciTix 的 slimerl 镜像
3. 执行: 任务在 SiFlow 平台运行

关键点：
- SiFlow 会自动从 SciTix registry 拉取镜像
- 不需要 SciTix 的 ACCESS_KEY 来使用公开镜像
- 只需要提供完整的镜像 URL

镜像 URL:
  registry-us-east.scitix.ai/hisys/slimerl:slimev0.2.2-8e52a0ab...
    """)

    result = submit_inference_task_with_slimerl()

    if result:
        print("\n✅ 成功！")
    else:
        print("\n❌ 失败")
