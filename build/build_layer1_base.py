#!/usr/bin/env python3
"""
构建 Layer 1 (Base) 镜像 - SWE-bench Python Base

Layer 1 镜像包含:
- Ubuntu 基础系统
- 系统工具 (git, wget, build-essential等)
- Miniconda3
- 非 root 用户

参考: swebench/harness/dockerfiles/python.py -> _DOCKERFILE_BASE_PY
"""

import sys
from pathlib import Path

from siflow.types import ImageBuildConfigRequest, InstanceRequest
from siflow_config import (
    RESOURCE_POOL,
    INSTANCE_TYPE,
    IMAGE_CATEGORY_MAJOR
)
from siflow_utils import (
    create_siflow_client,
    wait_for_image_build,
    get_image_registry_url,
    sanitize_image_name
)


def build_base_image(image_name: str = "swebench-base",
                     image_version: str = "2.0.0",
                     wait: bool = True):
    """
    构建 Layer 1 (Base) 镜像

    Args:
        image_name: 镜像名称
        image_version: 镜像版本号
        wait: 是否等待构建完成

    Returns:
        包含镜像信息的字典
    """
    print(f"\n{'='*70}")
    print(f"构建 Layer 1 (Base) 镜像")
    print(f"{'='*70}\n")

    # 1. 清理镜像名称
    image_name = sanitize_image_name(image_name)
    print(f"📦 镜像名称: {image_name}:{image_version}")

    # 2. 初始化客户端
    print(f"\n📌 初始化 SiFlow 客户端...")
    client = create_siflow_client()
    print(f"✅ 客户端初始化成功\n")

    # 3. 检查镜像是否已存在
    existing_url = get_image_registry_url(client, image_name, image_version)
    if existing_url:
        print(f"⚠️  镜像已存在: {existing_url}")
        print(f"   如需重建，请先删除该镜像或使用不同版本号")
        return {
            "success": True,
            "image_name": image_name,
            "image_version": image_version,
            "image_url": existing_url,
            "status": "already_exists"
        }

    # 4. 生成 Dockerfile
    # 基于 swebench/harness/dockerfiles/python.py 中的 _DOCKERFILE_BASE_PY
    # 使用 ubuntu:22.04 和 miniconda 最新版本
    dockerfile_content = """FROM --platform=linux/x86_64 ubuntu:22.04

ARG DEBIAN_FRONTEND=noninteractive
ENV TZ=Etc/UTC

# 安装系统包
RUN apt update && apt install -y \\
    wget \\
    git \\
    build-essential \\
    libffi-dev \\
    libtiff-dev \\
    python3 \\
    python3-pip \\
    python-is-python3 \\
    jq \\
    curl \\
    locales \\
    locales-all \\
    tzdata && \\
    rm -rf /var/lib/apt/lists/*

# 下载并安装 Miniconda3
RUN wget 'https://repo.anaconda.com/miniconda/Miniconda3-py39_24.1.2-0-Linux-x86_64.sh' -O miniconda.sh && \\
    bash miniconda.sh -b -p /opt/miniconda3 && \\
    rm miniconda.sh

# 添加 conda 到 PATH
ENV PATH=/opt/miniconda3/bin:$PATH

# 初始化 conda 并配置 channels
RUN conda init --all && \\
    conda config --append channels conda-forge && \\
    conda clean -a -y

# 添加非 root 用户
RUN adduser --disabled-password --gecos 'dog' nonroot

# 设置工作目录
WORKDIR /testbed
"""

    print("\n📄 Dockerfile:")
    print("-" * 70)
    print(dockerfile_content)
    print("-" * 70)

    # 5. 构建配置
    print(f"\n📌 创建镜像构建任务...")
    print(f"   方法: baseDockerfile (✓ RUN 命令会执行)")

    try:
        # 使用 ubuntu:22.04 作为基础镜像
        image_build_config = ImageBuildConfigRequest(
            commit_id="v1",
            build_method="baseDockerfile",
            basic_image_type="official",
            basic_image_url="ubuntu:22.04",
            dockerfile_content=dockerfile_content,
            description=f"SWE-bench Base Image - Python with Miniconda3 (v{image_version})"
        )

        instances_config = [
            InstanceRequest(
                name=INSTANCE_TYPE,
                countPerPod=1
            )
        ]

        result = client.images.create(
            name=image_name,
            version=image_version,
            major_category=IMAGE_CATEGORY_MAJOR,
            minor_category="base",
            image_build_type="custom",
            image_build_region="cn-shanghai",
            image_build_cluster="hercules",
            image_build_config=image_build_config,
            resource_pool=RESOURCE_POOL,
            instances=instances_config
        )

        image_id = result.id if hasattr(result, 'id') else None
        print(f"✅ 镜像构建任务已创建")
        print(f"   镜像名称: {image_name}")
        print(f"   镜像版本: {image_version}")
        print(f"   镜像ID: {image_id}")

        # 6. 等待构建完成
        if wait:
            print()
            build_result = wait_for_image_build(
                client=client,
                image_name=image_name,
                image_id=image_id,
                timeout=1800  # 30分钟
            )

            if build_result.get("success"):
                print(f"\n🎉 Base 镜像构建成功！")
                print(f"   镜像 URL: {build_result.get('image_url')}")
                print(f"   构建时间: {build_result.get('build_time')}秒")

            return build_result
        else:
            return {
                "success": True,
                "image_name": image_name,
                "image_version": image_version,
                "image_id": image_id,
                "status": "building"
            }

    except Exception as e:
        print(f"\n❌ 镜像构建失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "image_name": image_name,
            "error": str(e)
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="构建 SWE-bench Base 镜像")
    parser.add_argument("--name", default="swebench-base", help="镜像名称")
    parser.add_argument("--version", default="2.0.0", help="镜像版本")
    parser.add_argument("--no-wait", action="store_true", help="不等待构建完成")

    args = parser.parse_args()

    result = build_base_image(
        image_name=args.name,
        image_version=args.version,
        wait=not args.no_wait
    )

    if result.get("success"):
        print(f"\n✅ 完成")
        sys.exit(0)
    else:
        print(f"\n❌ 失败")
        sys.exit(1)
