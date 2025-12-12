#!/usr/bin/env python3
"""
构建 Layer 3 (Instance) 镜像 - SWE-bench Instance

Layer 3 镜像包含:
- FROM environment 镜像
- 克隆的 GitHub 仓库代码
- Checkout 到 base_commit
- 项目安装 (editable mode)

参考: swebench/harness/dockerfiles/python.py -> _DOCKERFILE_INSTANCE_PY
     swebench/harness/test_spec/python.py -> make_repo_script_list_py
"""

import sys
import logging
from pathlib import Path
from datasets import load_dataset

# 禁用详细日志
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("datasets").setLevel(logging.WARNING)

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

from swebench.harness.constants import (
    MAP_REPO_VERSION_TO_SPECS,
    MAP_REPO_TO_INSTALL,
    REPO_BASE_COMMIT_BRANCH,
)


def build_instance_image(instance_id: str,
                         image_version: str = "2.0.0",
                         env_image_name: str = None,
                         env_image_version: str = "2.0.0",
                         wait: bool = True,
                         verbose: bool = True):
    """
    构建 Layer 3 (Instance) 镜像

    Args:
        instance_id: 实例 ID (例如: django__django-10097)
        image_version: Instance 镜像版本号
        env_image_name: Environment 镜像名称 (如果为None则自动推断)
        env_image_version: Environment 镜像版本
        wait: 是否等待构建完成
        verbose: 是否输出详细信息

    Returns:
        包含镜像信息的字典
    """
    if verbose:
        print(f"\n{'='*70}")
        print(f"构建 Layer 3 (Instance) 镜像: {instance_id}")
        print(f"{'='*70}\n")
        print("📥 正在从 Dataset 加载实例信息...")

    # 1. 从 Dataset 获取实例信息
    ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    instance = [x for x in ds if x['instance_id'] == instance_id][0]

    repo = instance['repo']
    version = instance['version']
    base_commit = instance['base_commit']
    environment_setup_commit = instance.get('environment_setup_commit', '')

    if verbose:
        print(f"  ✓ Repo: {repo}")
        print(f"  ✓ Version: {version}")
        print(f"  ✓ Base Commit: {base_commit}")
        if environment_setup_commit:
            print(f"  ✓ Environment Setup Commit: {environment_setup_commit}")

    # 2. 获取项目 specs
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
    install_cmd = specs.get('install', 'python -m pip install -e .')
    pre_install = specs.get('pre_install', [])

    # 应用已知问题的补丁（如果需要）
    from fix_build_issues import should_apply_fix, get_install_cmd_fix, get_pre_install_fix, get_env_vars
    env_vars = {}
    if should_apply_fix(instance_id):
        install_cmd = get_install_cmd_fix(instance_id, install_cmd)
        pre_install = get_pre_install_fix(instance_id, pre_install)
        env_vars = get_env_vars(instance_id)

    if verbose:
        print(f"  ✓ install: {install_cmd}")
        print(f"  ✓ pre_install: {len(pre_install)} commands")
        if env_vars:
            print(f"  ✓ env_vars: {list(env_vars.keys())}")

    # 3. 初始化客户端
    if verbose:
        print(f"\n📌 初始化 SiFlow 客户端...")
    client = create_siflow_client()
    if verbose:
        print(f"✅ 客户端初始化成功\n")

    # 4. 获取 env 镜像的 registry URL
    if env_image_name is None:
        # 自动推断 env 镜像名称
        repo_slug = repo.replace('/', '-')
        env_image_name = f"swebench-env-{repo_slug}-{version}"
        env_image_name = sanitize_image_name(env_image_name)

    if verbose:
        print(f"🔍 正在查询 environment 镜像: {env_image_name}:{env_image_version}")
    env_image_url = get_image_registry_url(client, env_image_name, env_image_version)
    if not env_image_url:
        print("  ❌ 无法找到 environment 镜像!")
        if verbose:
            print("  提示: 请先运行 build_layer2_env.py")
        return {
            "success": False,
            "error": "Environment image not found"
        }

    if verbose:
        print(f"  ✓ Environment镜像: {env_image_url}")

    # 5. 生成 instance 镜像名称
    instance_image_name = f"swebench-instance-{instance_id}"
    instance_image_name = sanitize_image_name(instance_image_name)

    if verbose:
        print(f"\n🏗️  镜像名称: {instance_image_name}:{image_version}")

    # 6. 检查镜像是否已存在
    existing_url = get_image_registry_url(client, instance_image_name, image_version)
    if existing_url:
        if verbose:
            print(f"⚠️  镜像已存在: {existing_url}")
        return {
            "success": True,
            "image_name": instance_image_name,
            "image_version": image_version,
            "image_url": existing_url,
            "status": "already_exists"
        }

    # 7. 生成 setup_repo.sh 脚本
    if verbose:
        print(f"\n📝 生成 setup_repo.sh 脚本...")

    env_name = "testbed"
    repo_directory = f"/{env_name}"

    # 获取 branch (如果有) - 按2.1.0逻辑，使用--single-branch
    branch = REPO_BASE_COMMIT_BRANCH.get(repo, {}).get(base_commit, "")
    clone_options = f"--branch {branch} --single-branch" if branch else ""

    setup_commands = [
        "#!/bin/bash",
        "set -euxo pipefail",
        "",
        "# 克隆仓库",
        f"git clone -o origin {clone_options} https://github.com/{repo} {repo_directory}",
        f"chmod -R 777 {repo_directory}",
        f"cd {repo_directory}",
        f"git reset --hard {base_commit}",
        "",
    ]

    # 删除远程和未来的 tags (在install之前，按2.1.0逻辑)
    setup_commands.extend([
        "# 删除远程和未来的 tags",
        "git remote remove origin",
        f"TARGET_TIMESTAMP=$(git show -s --format=%ci {base_commit})",
        """git tag -l | while read tag; do
    TAG_COMMIT=$(git rev-list -n 1 "$tag")
    TAG_TIME=$(git show -s --format=%ci "$TAG_COMMIT")
    if [[ "$TAG_TIME" > "$TARGET_TIMESTAMP" ]]; then
        git tag -d "$tag"
    fi
done""",
        "git reflog expire --expire=now --all",
        "git gc --prune=now --aggressive",
        "",
        "# 验证未来的 commits 不可见",
        """AFTER_TIMESTAMP=$(date -d "$TARGET_TIMESTAMP + 1 second" '+%Y-%m-%d %H:%M:%S')""",
        """COMMIT_COUNT=$(git log --oneline --all --since="$AFTER_TIMESTAMP" | wc -l)""",
        """[ "$COMMIT_COUNT" -eq 0 ] || exit 1""",
        "",
    ])

    # 激活环境并安装项目 (按2.1.0逻辑，在base_commit上直接安装)
    setup_commands.extend([
        "# 激活环境并安装项目",
        "source /opt/miniconda3/bin/activate",
        f"conda activate {env_name}",
        """echo "Current environment: $CONDA_DEFAULT_ENV" """,
        "",
    ])

    # 添加 repo-specific install command (如果有)
    if repo in MAP_REPO_TO_INSTALL:
        setup_commands.append("# Repo-specific install command")
        setup_commands.append(MAP_REPO_TO_INSTALL[repo])
        setup_commands.append("")

    # 添加 pre_install (如果有)
    if pre_install:
        setup_commands.append("# Pre-install commands")
        for cmd in pre_install:
            setup_commands.append(cmd)
        setup_commands.append("")

    # 添加 install 命令
    setup_commands.append("# Install project")
    setup_commands.append(install_cmd)
    setup_commands.append("")

    # 清理 Python 缓存
    setup_commands.extend([
        "# 清理 Python 缓存",
        "find . -type d -name '__pycache__' -exec rm -rf {} + 2>/dev/null || true",
        "find . -type f -name '*.pyc' -delete 2>/dev/null || true",
        "find . -type f -name '*.pyo' -delete 2>/dev/null || true",
        "",
        "# 创建空 commit 用于 diff",
        "git config --global user.email setup@swebench.config",
        "git config --global user.name SWE-bench",
        "git commit --allow-empty -am SWE-bench",
    ])

    setup_repo_script = '\n'.join(setup_commands) + '\n'

    if verbose:
        print(f"  ✓ 脚本生成完成 ({len(setup_commands)} 行)")

    # 8. 生成 Dockerfile
    # 构建ENV语句
    env_statements = ""
    if env_vars:
        env_lines = [f"ENV {key}={value}" for key, value in env_vars.items()]
        env_statements = "\n".join(env_lines) + "\n\n"

    dockerfile_content = f"""FROM {env_image_url}

{env_statements}# 创建 setup_repo.sh 脚本
RUN cat <<'SETUP_REPO_EOF' > /root/setup_repo.sh
{setup_repo_script}SETUP_REPO_EOF

RUN chmod +x /root/setup_repo.sh
RUN /bin/bash /root/setup_repo.sh

WORKDIR /testbed/
"""

    if verbose:
        print("\n📄 Dockerfile:")
        print("-" * 70)
        print(dockerfile_content[:500])
        print("...")
        print("-" * 70)

        print("\n📄 setup_repo.sh (前15行):")
        print("-" * 70)
        script_lines = setup_repo_script.split('\n')
        print('\n'.join(script_lines[:15]))
        if len(script_lines) > 15:
            print(f"... ({len(script_lines)} 行总计)")
        print("-" * 70)

    # 9. 构建配置
    if verbose:
        print(f"\n📌 创建镜像构建任务...")

    try:
        image_build_config = ImageBuildConfigRequest(
            commit_id="v1",
            build_method="baseDockerfile",
            basic_image_type="custom",
            basic_image_url=env_image_url,
            dockerfile_content=dockerfile_content,
            description=f"Instance for {instance_id}",
        )

        instances_config = [
            InstanceRequest(
                name=INSTANCE_TYPE,
                countPerPod=1
            )
        ]

        # minor_category: instance 镜像按 instance_id 分类
        minor_category = instance_id.split('__')[0] if '__' in instance_id else instance_id

        result = client.images.create(
            name=instance_image_name,
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
        if verbose:
            print(f"✅ 镜像构建任务已创建")
            print(f"   镜像名称: {instance_image_name}")
            print(f"   镜像版本: {image_version}")
            print(f"   镜像ID: {image_id}")

        # 10. 等待构建完成
        if wait:
            if verbose:
                print()
            build_result = wait_for_image_build(
                client=client,
                image_name=instance_image_name,
                image_id=image_id,
                timeout=3600  # 60分钟
            )

            if build_result.get("success"):
                if verbose:
                    print(f"\n🎉 Instance 镜像构建成功！")
                    print(f"   镜像 URL: {build_result.get('image_url')}")
                    print(f"   构建时间: {build_result.get('build_time')}秒")

            return build_result
        else:
            return {
                "success": True,
                "image_name": instance_image_name,
                "image_version": image_version,
                "image_id": image_id,
                "status": "building"
            }

    except Exception as e:
        print(f"❌ 镜像构建失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e)
        }


if __name__ == "__main__":
    import argparse

    parser = argparse.ArgumentParser(description="构建 SWE-bench Instance 镜像")
    parser.add_argument("instance_id", help="实例 ID (例如: django__django-10097)")
    parser.add_argument("--version", default="2.0.0", help="镜像版本")
    parser.add_argument("--env-name", default=None, help="Environment 镜像名称")
    parser.add_argument("--env-version", default="2.0.0", help="Environment 镜像版本")
    parser.add_argument("--no-wait", action="store_true", help="不等待构建完成")

    args = parser.parse_args()

    result = build_instance_image(
        instance_id=args.instance_id,
        image_version=args.version,
        env_image_name=args.env_name,
        env_image_version=args.env_version,
        wait=not args.no_wait
    )

    if result.get("success"):
        print(f"\n✅ 完成")
        sys.exit(0)
    else:
        print(f"\n❌ 失败")
        sys.exit(1)
