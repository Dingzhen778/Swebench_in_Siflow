#!/usr/bin/env python3
"""
构建 Layer 2 (Environment) 镜像 - SWE-bench Environment

Layer 2 镜像包含:
- FROM base 镜像
- Conda 环境 (testbed) + 指定 Python 版本
- 项目依赖 (从 requirements.txt 或 environment.yml)

参考: swebench/harness/dockerfiles/python.py -> _DOCKERFILE_ENV_PY
     swebench/harness/test_spec/python.py -> make_env_script_list_py
"""

import sys
import json
from pathlib import Path
from datasets import load_dataset

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
from repo_version_to_python import get_python_version

# 导入swebench的函数
from swebench.harness.constants import MAP_REPO_VERSION_TO_SPECS
from swebench.harness.test_spec.python import (
    get_environment_yml,
    get_requirements,
)

# 针对特定 repo/version 的额外依赖补丁
# 用于修复 SWE-bench 官方 specs 中缺失的依赖
EXTRA_PIP_PACKAGES = {
    'sphinx-doc/sphinx': {
        '3.5': ['roman'],  # sphinx 3.5 需要 roman 包来转换罗马数字
        '4.3': ['roman'],  # sphinx 4.3 也需要 roman 包
    },
    # 未来可以添加更多 repo 的补丁
}


def build_env_image(instance_id: str,
                    image_version: str = "2.0.0",
                    base_image_name: str = "swebench-base",
                    base_image_version: str = "2.0.0",
                    wait: bool = True):
    """
    构建 Layer 2 (Environment) 镜像

    Args:
        instance_id: 实例 ID (例如: django__django-10097)
        image_version: 环境镜像版本号
        base_image_name: Base 镜像名称
        base_image_version: Base 镜像版本
        wait: 是否等待构建完成

    Returns:
        包含镜像信息的字典
    """
    print(f"\n{'='*70}")
    print(f"构建 Layer 2 (Environment) 镜像: {instance_id}")
    print(f"{'='*70}\n")

    # 1. 从 Dataset 获取实例信息
    print("📥 正在从 Dataset 加载实例信息...")
    ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    instance = [x for x in ds if x['instance_id'] == instance_id][0]

    repo = instance['repo']
    version = instance['version']

    print(f"  ✓ Repo: {repo}")
    print(f"  ✓ Version: {version}")

    # 2. 获取正确的 Python 版本
    python_version = get_python_version(repo, version)
    print(f"  ✓ Python版本: {python_version}")

    # 3. 获取项目 specs
    if repo not in MAP_REPO_VERSION_TO_SPECS:
        print(f"  ❌ 未找到 repo {repo} 的配置")
        return {
            "success": False,
            "error": f"Repo {repo} not in MAP_REPO_VERSION_TO_SPECS"
        }

    if version not in MAP_REPO_VERSION_TO_SPECS[repo]:
        print(f"  ❌ 未找到 repo {repo} version {version} 的配置")
        return {
            "success": False,
            "error": f"Version {version} not found for {repo}"
        }

    specs = MAP_REPO_VERSION_TO_SPECS[repo][version]
    packages = specs.get('packages', '')
    pip_packages = specs.get('pip_packages', []).copy()  # 创建副本，避免修改原始 specs

    # 添加额外的 pip packages（如果有定义的话）
    if repo in EXTRA_PIP_PACKAGES and version in EXTRA_PIP_PACKAGES[repo]:
        extra_packages = EXTRA_PIP_PACKAGES[repo][version]
        pip_packages.extend(extra_packages)
        print(f"  ℹ️  添加额外依赖: {extra_packages}")

    print(f"  ✓ packages: {packages}")
    print(f"  ✓ pip_packages: {pip_packages}")

    # 4. 初始化客户端
    print(f"\n📌 初始化 SiFlow 客户端...")
    client = create_siflow_client()
    print(f"✅ 客户端初始化成功\n")

    # 5. 获取 base 镜像的 registry URL
    print(f"🔍 正在查询 base 镜像: {base_image_name}:{base_image_version}")
    base_image_url = get_image_registry_url(client, base_image_name, base_image_version)
    if not base_image_url:
        print("  ❌ 无法找到 base 镜像!")
        print("  提示: 请先运行 build_layer1_base.py")
        return {
            "success": False,
            "error": "Base image not found"
        }

    print(f"  ✓ Base镜像: {base_image_url}")

    # 6. 生成 env 镜像名称
    # 格式: swebench-env-<repo>-<version>
    repo_slug = repo.replace('/', '-')
    env_image_name = f"swebench-env-{repo_slug}-{version}"
    env_image_name = sanitize_image_name(env_image_name)

    print(f"\n🏗️  镜像名称: {env_image_name}:{image_version}")

    # 7. 检查镜像是否已存在
    existing_url = get_image_registry_url(client, env_image_name, image_version)
    if existing_url:
        print(f"⚠️  镜像已存在: {existing_url}")
        return {
            "success": True,
            "image_name": env_image_name,
            "image_version": image_version,
            "image_url": existing_url,
            "status": "already_exists"
        }

    # 8. 生成 setup_env.sh 脚本
    # 基于 swebench/harness/test_spec/python.py -> make_env_script_list_py
    print(f"\n📝 生成 setup_env.sh 脚本...")

    HEREDOC_DELIMITER = "EOF_59812759871"
    env_name = "testbed"

    setup_commands = [
        "#!/bin/bash",
        "set -euxo pipefail",
        "source /opt/miniconda3/bin/activate",
    ]

    # 根据 packages 类型生成不同的安装命令
    if packages == "requirements.txt":
        # 使用 requirements.txt
        print(f"  ✓ 使用 requirements.txt")
        setup_commands.append(f"conda create -n {env_name} python={python_version} -y")

        # 获取 requirements
        try:
            reqs = get_requirements(instance)
            path_to_reqs = "$HOME/requirements.txt"
            setup_commands.append(
                f"cat <<'{HEREDOC_DELIMITER}' > {path_to_reqs}\n{reqs}\n{HEREDOC_DELIMITER}"
            )
            setup_commands.append(f"conda activate {env_name} && python -m pip install -r {path_to_reqs}")
            setup_commands.append(f"rm {path_to_reqs}")
        except Exception as e:
            print(f"  ⚠️  获取 requirements 失败: {e}, 使用空环境")
            pass

    elif packages == "environment.yml":
        # 使用 environment.yml
        print(f"  ✓ 使用 environment.yml")
        try:
            reqs = get_environment_yml(instance, env_name)

            # 关键修复：在environment.yml的dependencies列表中注入Python版本
            # 这样conda env create会直接使用正确的Python版本，避免先安装3.13再降级
            import re
            lines = reqs.split('\n')
            modified_lines = []
            dependencies_found = False
            python_injected = False

            for i, line in enumerate(lines):
                modified_lines.append(line)
                # 找到dependencies:行后，在下一个有效依赖前注入python版本
                if line.strip().startswith('dependencies:'):
                    dependencies_found = True
                elif dependencies_found and not python_injected:
                    # 检查是否已经有python版本定义
                    if 'python' in line.lower() and '=' in line:
                        python_injected = True  # 已有python定义，不注入
                    # 找到第一个依赖项（以-开头），在它之前注入python
                    elif line.strip().startswith('-'):
                        # 获取缩进
                        indent = len(line) - len(line.lstrip())
                        # 在当前行之前插入python版本
                        modified_lines.insert(-1, ' ' * indent + f'- python={python_version}')
                        python_injected = True

            # 如果没有找到dependencies或没有注入成功，在文件末尾添加
            if dependencies_found and not python_injected:
                modified_lines.append(f'  - python={python_version}')

            reqs = '\n'.join(modified_lines)

            path_to_reqs = "environment.yml"
            setup_commands.append(
                f"cat <<'{HEREDOC_DELIMITER}' > {path_to_reqs}\n{reqs}\n{HEREDOC_DELIMITER}"
            )

            if specs.get("no_use_env"):
                # conda create 方式
                setup_commands.append(f"conda create -c conda-forge -n {env_name} python={python_version} -y")
                setup_commands.append(f"conda env update -f {path_to_reqs}")
            else:
                # conda env create 方式 - 现在environment.yml中已经包含正确的Python版本
                setup_commands.append(f"conda env create --file {path_to_reqs}")
                # 不再需要后续的conda install python，因为已经在yml中指定了

            setup_commands.append(f"rm {path_to_reqs}")
        except Exception as e:
            print(f"  ⚠️  获取 environment.yml 失败: {e}, 使用空环境")
            setup_commands.append(f"conda create -n {env_name} python={python_version} -y")

    else:
        # 直接创建环境 + 安装包
        print(f"  ✓ 直接创建环境")
        setup_commands.append(f"conda create -n {env_name} python={python_version} {packages} -y")

    setup_commands.append(f"conda activate {env_name}")

    # 安装额外的 pip packages
    if pip_packages:
        pip_packages_str = ' '.join(pip_packages)
        setup_commands.append(f"python -m pip install {pip_packages_str}")

    # 清理
    setup_commands.append("conda clean -a -y")

    setup_env_script = '\n'.join(setup_commands) + '\n'

    print(f"  ✓ 脚本生成完成 ({len(setup_commands)} 行)")

    # 9. 生成 Dockerfile
    # 基于 swebench/harness/dockerfiles/python.py -> _DOCKERFILE_ENV_PY
    dockerfile_content = f"""FROM {base_image_url}

COPY ./setup_env.sh /root/
RUN sed -i -e 's/\\r$//' /root/setup_env.sh
RUN chmod +x /root/setup_env.sh
RUN /bin/bash -c "source ~/.bashrc && /root/setup_env.sh"

WORKDIR /testbed/

# 自动激活 testbed 环境
RUN echo "source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed" > /root/.bashrc
"""

    print("\n📄 Dockerfile:")
    print("-" * 70)
    print(dockerfile_content)
    print("-" * 70)

    print("\n📄 setup_env.sh (前10行):")
    print("-" * 70)
    script_lines = setup_env_script.split('\n')
    print('\n'.join(script_lines[:10]))
    if len(script_lines) > 10:
        print(f"... ({len(script_lines)} 行总计)")
    print("-" * 70)

    # 10. 构建配置
    print(f"\n📌 创建镜像构建任务...")

    try:
        # 将 setup_env.sh 作为额外文件
        # 注意：siflow 可能不支持多文件，我们需要把脚本内容嵌入到 Dockerfile 中
        # 使用 RUN echo 或 RUN cat <<EOF 的方式

        # 重新生成 Dockerfile，将脚本内容嵌入
        dockerfile_with_script = f"""FROM {base_image_url}

# 创建 setup_env.sh 脚本
RUN cat <<'SETUP_ENV_EOF' > /root/setup_env.sh
{setup_env_script}SETUP_ENV_EOF

RUN chmod +x /root/setup_env.sh
RUN /bin/bash -c "source ~/.bashrc && /root/setup_env.sh"

WORKDIR /testbed/

# 自动激活 testbed 环境
RUN echo "source /opt/miniconda3/etc/profile.d/conda.sh && conda activate testbed" > /root/.bashrc
"""

        image_build_config = ImageBuildConfigRequest(
            commit_id="v1",
            build_method="baseDockerfile",
            basic_image_type="custom",
            basic_image_url=base_image_url,
            dockerfile_content=dockerfile_with_script,
            description=f"Environment for {repo} {version} (Python {python_version})"
        )

        instances_config = [
            InstanceRequest(
                name=INSTANCE_TYPE,
                countPerPod=1
            )
        ]

        minor_category = repo.split('/')[0] if '/' in repo else "common"

        result = client.images.create(
            name=env_image_name,
            version=image_version,
            major_category=IMAGE_CATEGORY_MAJOR,
            minor_category=minor_category,
            image_build_type="custom",
            image_build_region="cn-shanghai",
            image_build_cluster="hercules",
            image_build_config=image_build_config,
            resource_pool=RESOURCE_POOL,
            instances=instances_config
        )

        image_id = result.id if hasattr(result, 'id') else None
        print(f"✅ 镜像构建任务已创建")
        print(f"   镜像名称: {env_image_name}")
        print(f"   镜像版本: {image_version}")
        print(f"   镜像ID: {image_id}")

        # 11. 等待构建完成
        if wait:
            print()
            build_result = wait_for_image_build(
                client=client,
                image_name=env_image_name,
                image_id=image_id,
                timeout=3600  # 60分钟
            )

            if build_result.get("success"):
                print(f"\n🎉 Environment 镜像构建成功！")
                print(f"   镜像 URL: {build_result.get('image_url')}")
                print(f"   构建时间: {build_result.get('build_time')}秒")

            return build_result
        else:
            return {
                "success": True,
                "image_name": env_image_name,
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
            "image_name": env_image_name,
            "error": str(e)
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="构建 SWE-bench Environment 镜像")
    parser.add_argument("instance_id", help="实例 ID (例如: django__django-10097)")
    parser.add_argument("--version", default="2.0.0", help="镜像版本")
    parser.add_argument("--base-name", default="swebench-base", help="Base 镜像名称")
    parser.add_argument("--base-version", default="2.0.0", help="Base 镜像版本")
    parser.add_argument("--no-wait", action="store_true", help="不等待构建完成")

    args = parser.parse_args()

    result = build_env_image(
        instance_id=args.instance_id,
        image_version=args.version,
        base_image_name=args.base_name,
        base_image_version=args.base_version,
        wait=not args.no_wait
    )

    if result.get("success"):
        print(f"\n✅ 完成")
        sys.exit(0)
    else:
        print(f"\n❌ 失败")
        sys.exit(1)
