#!/usr/bin/env python3
"""
批量构建validation instances的所有镜像 - 不等待版本

支持：
1. 构建Base镜像
2. 批量构建Environment镜像
3. 批量构建Instance镜像

特点：
- 不等待构建完成，一次性提交所有任务
- 返回镜像ID列表，可以在siflow平台上查看进度
"""

import sys
import json
import time
import logging
from pathlib import Path

# 禁用 httpx 详细日志
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("datasets").setLevel(logging.WARNING)

# 导入构建函数
from build_layer1_base import build_base_image
from build_layer2_env import build_env_image
from build_layer3_instance import build_instance_image


def build_base(image_version="2.0.0", force=False):
    """
    构建Base镜像 - 不等待
    """
    print(f"\n{'='*70}")
    print(f"构建 Layer 1: Base 镜像")
    print(f"{'='*70}\n")

    # 检查是否已存在
    if not force:
        from siflow_utils import create_siflow_client, image_exists, get_image_registry_url
        client = create_siflow_client()
        # 检查镜像是否存在（不管状态）
        if image_exists(client, "swebench-base", image_version):
            base_image_url = get_image_registry_url(client, "swebench-base", image_version)
            print(f"✅ Base镜像已存在{': ' + base_image_url if base_image_url else ''}")
            print(f"   使用 --force 强制重建\n")
            return {'success': True, 'status': 'already_exists', 'image_url': base_image_url}

    # 构建（不等待）
    result = build_base_image(
        image_name="swebench-base",
        image_version=image_version,
        wait=False  # 不等待
    )

    if result.get('success'):
        print(f"\n✅ Base镜像构建任务已提交")
        print(f"   镜像名称: swebench-base:{image_version}")
        print(f"   镜像ID: {result.get('image_id')}")
        print(f"   状态: {result.get('status', 'building')}")
        print(f"\n   💡 在siflow平台上查看构建进度")
    else:
        print(f"\n❌ Base镜像构建提交失败: {result.get('error')}")

    return result


def build_environments(image_version="2.0.0", base_image_version=None, force=False, delay=2, filter_repo=None, instances_file=None):
    """
    批量构建Environment镜像 - 不等待

    Args:
        delay: 每次提交之间的延迟（秒），避免API限流，默认2秒
        filter_repo: 只构建指定repo的镜像，格式如 "sphinx-doc/sphinx"
        instances_file: instances JSON文件路径，如果为None则从Dataset加载全部
    """
    print(f"\n{'='*70}")
    print(f"构建 Layer 2: Environment 镜像")
    print(f"{'='*70}\n")

    if filter_repo:
        print(f"🔍 只构建 repo: {filter_repo}\n")

    # 1. 读取instances
    if instances_file:
        # 从JSON文件读取（如validation_instances.json）
        instances_path = Path(instances_file)
        if not instances_path.exists():
            print(f"❌ 找不到 {instances_file}")
            return {'success': False, 'error': f'{instances_file} not found'}

        print(f"📥 从文件加载: {instances_file}")
        with open(instances_path) as f:
            instances = json.load(f)
    else:
        # 从Dataset加载全部instances
        print(f"📥 从Dataset加载全部instances...")
        from datasets import load_dataset
        ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
        instances = [{'instance_id': x['instance_id'], 'repo': x['repo'], 'version': x['version']} for x in ds]
        print(f"  ✓ 加载了 {len(instances)} 个instances")

    # 2. 按repo:version分组
    repo_versions = {}
    for inst in instances:
        repo = inst['repo']
        version = inst['version']

        # 过滤特定repo
        if filter_repo and repo != filter_repo:
            continue

        key = f"{repo}:{version}"
        if key not in repo_versions:
            repo_versions[key] = {
                'repo': repo,
                'version': version,
                'instance_ids': []
            }
        repo_versions[key]['instance_ids'].append(inst['instance_id'])

    print(f"📋 需要构建 {len(repo_versions)} 个不同的 Environment 镜像\n")

    # 3. 检查哪些需要构建
    from siflow_utils import create_siflow_client, image_exists, sanitize_image_name
    client = create_siflow_client()

    to_build = []
    for key, info in sorted(repo_versions.items()):
        repo = info['repo']
        version = info['version']
        instance_id = info['instance_ids'][0]  # 使用第一个instance来构建env

        repo_slug = repo.replace('/', '-')
        env_image_name = f"swebench-env-{repo_slug}-{version}"
        env_image_name = sanitize_image_name(env_image_name)

        if not force:
            # 检查镜像是否存在（不管状态）
            if image_exists(client, env_image_name, image_version):
                print(f"✅ 已存在: {env_image_name}:{image_version}")
                continue

        to_build.append({
            'repo': repo,
            'version': version,
            'instance_id': instance_id,
            'env_image_name': env_image_name
        })

    if not to_build:
        print(f"\n✅ 所有Environment镜像都已存在\n")
        return {'success': True, 'built': 0, 'skipped': len(repo_versions)}

    print(f"\n需要构建: {len(to_build)} 个")
    if not force:
        print(f"已存在: {len(repo_versions) - len(to_build)} 个\n")

    # 4. 批量提交构建任务（不等待）
    print(f"\n开始批量提交构建任务...\n")

    results = []
    for idx, build_info in enumerate(to_build, 1):
        instance_id = build_info['instance_id']
        repo = build_info['repo']
        version = build_info['version']
        env_image_name = build_info['env_image_name']

        print(f"[{idx}/{len(to_build)}] 提交: {env_image_name}:{image_version}")
        print(f"  Repo: {repo} (version {version})")
        print(f"  使用instance: {instance_id}")

        try:
            result = build_env_image(
                instance_id=instance_id,
                image_version=image_version,
                base_image_version=base_image_version or image_version,
                wait=False  # 不等待
            )

            results.append({
                'repo': repo,
                'version': version,
                'instance_id': instance_id,
                'image_name': env_image_name,
                'success': result.get('success'),
                'status': result.get('status'),
                'image_id': result.get('image_id'),
                'error': result.get('error')
            })

            if result.get('success'):
                print(f"  ✅ 已提交 (镜像ID: {result.get('image_id')})")
            else:
                print(f"  ❌ 提交失败: {result.get('error')}")

        except Exception as e:
            print(f"  ❌ 异常: {e}")
            results.append({
                'repo': repo,
                'version': version,
                'instance_id': instance_id,
                'image_name': env_image_name,
                'success': False,
                'error': str(e)
            })

        # 短暂延迟，避免API限流
        if idx < len(to_build) and delay > 0:
            time.sleep(delay)

        print()

    # 5. 统计
    success_count = sum(1 for r in results if r.get('success'))
    fail_count = len(results) - success_count

    print(f"{'='*70}")
    print(f"Environment 镜像构建任务提交完成")
    print(f"{'='*70}\n")
    print(f"总数: {len(results)}")
    print(f"✅ 已提交: {success_count}")
    print(f"❌ 失败: {fail_count}\n")

    if success_count > 0:
        print(f"💡 在siflow平台上查看构建进度")
        print(f"\n已提交的镜像ID列表:")
        for r in results:
            if r.get('success') and r.get('image_id'):
                print(f"  - {r['image_name']}: {r['image_id']}")
        print()

    return {
        'success': fail_count == 0,
        'submitted': success_count,
        'failed': fail_count,
        'details': results
    }


def build_instances(image_version="2.0.0", env_image_version="2.0.0", force=False, delay=2, filter_repo=None, instances_file=None, max_instances=None):
    """
    批量构建Instance镜像 - 不等待

    Args:
        image_version: Instance镜像版本
        env_image_version: Environment镜像版本（可以不同于instance版本）
        delay: 每次提交之间的延迟（秒），避免API限流，默认2秒
        filter_repo: 只构建指定repo的镜像，格式如 "sphinx-doc/sphinx"
        instances_file: instances JSON文件路径，如果为None则从Dataset加载全部
        max_instances: 最多构建多少个instance（用于分批构建），None表示全部
    """
    print(f"\n{'='*70}")
    print(f"构建 Layer 3: Instance 镜像")
    print(f"{'='*70}\n")

    if filter_repo:
        print(f"🔍 只构建 repo: {filter_repo}\n")

    # 1. 读取instances
    if instances_file:
        # 从JSON文件读取（如validation_instances.json）
        instances_path = Path(instances_file)
        if not instances_path.exists():
            print(f"❌ 找不到 {instances_file}")
            return {'success': False, 'error': f'{instances_file} not found'}

        print(f"📥 从文件加载: {instances_file}")
        with open(instances_path) as f:
            all_instances = json.load(f)
    else:
        # 从Dataset加载全部instances
        print(f"📥 从Dataset加载全部instances...")
        from datasets import load_dataset
        ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
        all_instances = [{'instance_id': x['instance_id'], 'repo': x['repo'], 'version': x['version']} for x in ds]
        print(f"  ✓ 加载了 {len(all_instances)} 个instances")

    # 过滤特定repo
    if filter_repo:
        instances = [inst for inst in all_instances if inst['repo'] == filter_repo]
    else:
        instances = all_instances

    print(f"📋 共 {len(instances)} 个 Instance\n")
    print(f"🔍 检查镜像存在情况...")

    # 2. 检查哪些需要构建
    from siflow_utils import create_siflow_client, image_exists, sanitize_image_name
    client = create_siflow_client()

    to_build = []
    already_exists = 0

    for inst in instances:
        instance_id = inst['instance_id']

        instance_image_name = f"swebench-instance-{instance_id}"
        instance_image_name = sanitize_image_name(instance_image_name)

        if not force:
            # 检查镜像是否存在（不管状态）
            if image_exists(client, instance_image_name, image_version):
                already_exists += 1
                continue

        to_build.append(inst)

    if not to_build:
        print(f"\n✅ 所有Instance镜像都已存在 (共 {already_exists} 个)\n")
        return {'success': True, 'built': 0, 'skipped': already_exists}

    # 应用 max_instances 限制
    total_to_build = len(to_build)
    if max_instances is not None and max_instances > 0:
        to_build = to_build[:max_instances]
        print(f"\n⚠️  限制构建数量: {max_instances}")
        print(f"需要构建: {len(to_build)} 个（总共 {total_to_build} 个待构建）")
    else:
        print(f"\n需要构建: {len(to_build)} 个")

    if not force and already_exists > 0:
        print(f"已存在: {already_exists} 个\n")

    # 3. 批量提交构建任务（不等待）
    print(f"\n开始批量提交构建任务...\n")

    results = []
    success_count = 0
    fail_count = 0

    for idx, inst in enumerate(to_build, 1):
        instance_id = inst['instance_id']
        repo = inst['repo']
        version = inst['version']

        instance_image_name = f"swebench-instance-{instance_id}"
        instance_image_name = sanitize_image_name(instance_image_name)

        # 简洁的进度输出
        print(f"[{idx}/{len(to_build)}] {instance_id} ({repo})...", end=' ', flush=True)

        try:
            result = build_instance_image(
                instance_id=instance_id,
                image_version=image_version,
                env_image_version=env_image_version,
                wait=False,  # 不等待
                verbose=False  # 禁用详细输出
            )

            results.append({
                'instance_id': instance_id,
                'repo': repo,
                'version': version,
                'image_name': instance_image_name,
                'success': result.get('success'),
                'status': result.get('status'),
                'image_id': result.get('image_id'),
                'error': result.get('error')
            })

            if result.get('success'):
                success_count += 1
                print(f"✅")
            else:
                fail_count += 1
                error_msg = result.get('error', 'Unknown error')
                # 只显示错误的前50个字符
                short_error = error_msg[:50] + '...' if len(error_msg) > 50 else error_msg
                print(f"❌ {short_error}")

        except Exception as e:
            fail_count += 1
            short_error = str(e)[:50]
            print(f"❌ {short_error}")
            results.append({
                'instance_id': instance_id,
                'repo': repo,
                'version': version,
                'image_name': instance_image_name,
                'success': False,
                'error': str(e)
            })

        # 短暂延迟，避免API限流
        if idx < len(to_build) and delay > 0:
            time.sleep(delay)

    # 4. 统计（使用已计算的值）

    print(f"{'='*70}")
    print(f"Instance 镜像构建任务提交完成")
    print(f"{'='*70}\n")
    print(f"总数: {len(results)}")
    print(f"✅ 已提交: {success_count}")
    print(f"❌ 失败: {fail_count}\n")

    if success_count > 0:
        print(f"💡 在siflow平台上查看构建进度")
        print(f"\n已提交的镜像ID列表:")
        for r in results:
            if r.get('success') and r.get('image_id'):
                print(f"  - {r['instance_id']}: {r['image_id']}")
        print()

    return {
        'success': fail_count == 0,
        'submitted': success_count,
        'failed': fail_count,
        'details': results
    }


def main():
    import argparse

    parser = argparse.ArgumentParser(description="批量构建镜像（不等待版本）")
    parser.add_argument("--layer", choices=['base', 'env', 'instance', 'all'], default='all',
                       help="构建哪一层 (default: all)")
    parser.add_argument("--version", default="2.0.0", help="镜像版本 (用于instance，默认2.0.0)")
    parser.add_argument("--env-version", dest="env_version", default=None,
                       help="Environment镜像版本（默认与--version相同）")
    parser.add_argument("--repo", default=None,
                       help="只构建指定repo，格式如 'sphinx-doc/sphinx'")
    parser.add_argument("--instances-file", dest="instances_file", default=None,
                       help="指定instances JSON文件（如validation_instances.json），不指定则从Dataset加载全部")
    parser.add_argument("--max-instances", dest="max_instances", type=int, default=None,
                       help="最多构建多少个instance（用于分批构建，如50），不指定则全部构建")
    parser.add_argument("--force", action="store_true", help="强制重建（即使已存在）")
    parser.add_argument("--delay", type=int, default=2,
                       help="每次提交之间的延迟（秒），避免API限流 (default: 2)")

    args = parser.parse_args()

    # 如果没有指定 env_version，使用 version
    if args.env_version is None:
        args.env_version = args.version

    print(f"\n{'='*70}")
    print(f"批量构建镜像 - 不等待模式")
    print(f"{'='*70}\n")
    print(f"层级: {args.layer}")
    print(f"Instance版本: {args.version}")
    print(f"Environment版本: {args.env_version}")
    if args.instances_file:
        print(f"Instances文件: {args.instances_file}")
    else:
        print(f"Instances来源: Dataset (全部)")
    if args.repo:
        print(f"过滤Repo: {args.repo}")
    if args.max_instances:
        print(f"构建数量限制: {args.max_instances} 个instance")
    print(f"强制重建: {args.force}")
    print(f"提交延迟: {args.delay}秒")
    print(f"\n💡 所有构建任务会立即提交，不等待完成")
    print(f"   请在siflow平台上查看构建进度\n")

    results = {}
    submitted_total = 0
    failed_total = 0

    # 构建Base
    if args.layer in ['base', 'all']:
        base_result = build_base(
            image_version=args.version,
            force=args.force
        )
        results['base'] = base_result

        if not base_result.get('success') and base_result.get('status') != 'already_exists':
            print(f"\n⚠️  Base镜像提交失败，继续构建其他层级")

        if base_result.get('status') == 'building':
            submitted_total += 1

    # 构建Environment
    if args.layer in ['env', 'all']:
        env_result = build_environments(
            image_version=args.env_version,
            base_image_version=args.version,
            force=args.force,
            delay=args.delay,
            filter_repo=args.repo,
            instances_file=args.instances_file
        )
        results['env'] = env_result
        submitted_total += env_result.get('submitted', 0)
        failed_total += env_result.get('failed', 0)

    # 构建Instance
    if args.layer in ['instance', 'all']:
        instance_result = build_instances(
            image_version=args.version,
            env_image_version=args.env_version,
            force=args.force,
            delay=args.delay,
            filter_repo=args.repo,
            instances_file=args.instances_file,
            max_instances=args.max_instances
        )
        results['instance'] = instance_result
        submitted_total += instance_result.get('submitted', 0)
        failed_total += instance_result.get('failed', 0)

    # 保存结果
    result_file = Path("./build_submit_results.json")
    with open(result_file, 'w') as f:
        json.dump(results, f, indent=2)

    print(f"\n💾 提交结果已保存到: {result_file}\n")

    # 最终统计
    print(f"{'='*70}")
    print(f"最终统计")
    print(f"{'='*70}\n")

    if 'base' in results:
        base = results['base']
        if base.get('status') == 'already_exists':
            print(f"Base镜像: ✅ 已存在")
        elif base.get('status') == 'building':
            print(f"Base镜像: 📤 已提交构建 (ID: {base.get('image_id')})")
        else:
            print(f"Base镜像: ❌ 提交失败")

    if 'env' in results:
        env = results['env']
        print(f"\nEnvironment镜像:")
        print(f"  已提交: {env.get('submitted', 0)}")
        print(f"  失败: {env.get('failed', 0)}")

    if 'instance' in results:
        inst = results['instance']
        print(f"\nInstance镜像:")
        print(f"  已提交: {inst.get('submitted', 0)}")
        print(f"  失败: {inst.get('failed', 0)}")

    print(f"\n总计:")
    print(f"  📤 已提交: {submitted_total}")
    print(f"  ❌ 失败: {failed_total}")

    print(f"\n{'='*70}")
    print(f"🚀 下一步")
    print(f"{'='*70}\n")
    print(f"1. 在siflow平台上查看构建进度")
    print(f"2. 等待所有镜像构建完成（可能需要1-3小时）")
    print(f"3. 运行以下命令检查镜像状态:")
    print(f"   python check_images_status.py")
    print(f"4. 所有镜像构建完成后，运行验证测试:")
    print(f"   ./quick_test.sh")
    print(f"   python batch_gold_eval_fixed.py --wait --max 5")
    print()

    # 返回状态码
    return 0 if failed_total == 0 else 1


if __name__ == "__main__":
    sys.exit(main())
