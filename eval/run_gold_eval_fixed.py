#!/usr/bin/env python3
"""
运行gold patch评测 - 修复版本

严格遵循SWE-bench的评估逻辑:
1. 应用 gold/model patch 到源代码
2. 重新安装仓库 (python -m pip install -e .)
3. 重置测试文件到 base_commit
4. 应用 test patch
5. 运行测试
6. 解析结果
"""

import sys
import json
import time
from pathlib import Path
from datasets import load_dataset

# 添加父目录到路径，以便导入siflow_utils等模块
sys.path.insert(0, str(Path(__file__).parent.parent))

from siflow.types import TaskVolume, TaskEnv, TaskUserSelectedInstance
from siflow_utils import create_siflow_client, get_image_registry_url
from siflow_config import RESOURCE_POOL, INSTANCE_TYPE, PROJECT_ROOT, VOLUME_MOUNT_DIR, VOLUME_ID
from swebench.harness.constants import MAP_REPO_VERSION_TO_SPECS, FAIL_TO_PASS, PASS_TO_PASS, START_TEST_OUTPUT, END_TEST_OUTPUT
from swebench.harness.test_spec.python import get_test_directives, get_modified_files
from swebench.harness.test_spec.test_spec import TestSpec, make_test_spec
from swebench.harness.grading import get_eval_tests_report, get_resolution_status
from swebench.harness.log_parsers import MAP_REPO_TO_PARSER
from build.fix_build_issues import should_apply_fix
from method_config import get_method_config, DEFAULT_METHOD


def get_image_version_for_instance(instance_id: str) -> str:
    """
    获取instance应该使用的镜像版本

    如果instance需要应用修复补丁，使用2.1.0版本（已修复）
    否则使用2.0.0版本（原始）

    注意：正在迁移到统一2.0.0版本，迁移完成前保持双版本
    """
    if should_apply_fix(instance_id):
        return "2.1.0"  # 修复后的镜像（临时）
    return "2.0.0"  # 原始镜像


def generate_eval_script_fixed(instance, specs, patch_file_path, test_patch_file_path, method_config=None):
    """
    生成评估脚本 - 严格遵循SWE-bench逻辑

    Args:
        instance: dataset instance
        specs: 配置规范
        patch_file_path: patch文件路径 (.diff)
        test_patch_file_path: test patch文件路径
        method_config: 方法配置

    关键顺序:
    1. 应用patch到源代码
    2. 重新安装仓库
    3. 重置测试文件到 base_commit
    4. 应用 test patch
    5. 运行测试
    """
    instance_id = instance['instance_id']
    repo = instance['repo']
    base_commit = instance['base_commit']
    test_patch = instance['test_patch']

    env_name = "testbed"
    repo_directory = f"/{env_name}"

    # 获取测试指令
    test_directives = get_test_directives(instance)
    test_command = specs.get('test_cmd', 'pytest')
    test_targets = ' '.join(test_directives) if test_directives else ''

    # 获取test patch修改的测试文件
    test_files = get_modified_files(test_patch)

    # 确定日志目录
    if method_config:
        log_dir = method_config['log_dir']
    else:
        # 向后兼容：默认使用eval_outputs
        log_dir = "eval_outputs"
    
    # 输出文件路径（使用配置的项目根目录，在脚本中使用变量）
    test_output_file = f'"{PROJECT_ROOT}/{log_dir}/{instance_id}_test_output.txt"'

    # 生成脚本 - 严格按照SWE-bench的顺序
    # 使用单引号包裹整个bash命令，避免双引号嵌套问题
    script_lines = [
        "bash -c '",
        'set -uxo pipefail &&',
        '',
        'echo "========================================" &&',
        'echo "Step 0: Setup" &&',
        'echo "========================================" &&',
        'source /opt/miniconda3/bin/activate &&',
        f'conda activate {env_name} &&',
        f'mkdir -p "{PROJECT_ROOT}/{log_dir}" &&',  # 直接使用绝对路径创建日志目录
        f'cd {repo_directory} &&',
        '',
    ]

    # 使用diff格式patch
    actual_patch = f'"{patch_file_path}"'

    script_lines.extend([
        'echo "" &&',
        'echo "========================================" &&',
        'echo "Step 1: Apply Model Patch" &&',
        'echo "========================================" &&',
        f'if [ -f {actual_patch} ]; then',
        f'    git apply --verbose {actual_patch} || patch --batch --fuzz=5 -p1 -i {actual_patch} || exit 1',
        '    echo "Model patch applied successfully"',
        'else',
        f'    echo "ERROR: Patch file not found: {actual_patch}"',
        '    exit 1',
        'fi &&',
        '',
        'echo "" &&',
        'echo "========================================" &&',
        'echo "Step 2: Record git info" &&',
        'echo "========================================" &&',
        f'git config --global --add safe.directory {repo_directory} &&',
        f'cd {repo_directory} &&',
        'git status &&',
        'git show &&',
        f'git -c core.fileMode=false diff {base_commit} &&',
        '',
        'echo "" &&',
        'echo "========================================" &&',
        'echo "Step 3: Reinstall repository" &&',
        'echo "========================================" &&',
        'source /opt/miniconda3/bin/activate &&',
        f'conda activate {env_name} &&',
    ])

    # 清理 Python 缓存（防止 .pyc 文件过时）
    script_lines.extend([
        'echo "Cleaning Python cache..." &&',
        f'find {repo_directory} -type d -name __pycache__ -exec rm -rf {{}} + 2>/dev/null || true &&',
        f'find {repo_directory} -type f -name "*.pyc" -delete 2>/dev/null || true &&',
    ])

    # 添加安装命令
    install_cmd = specs.get('install', 'python -m pip install -e .')
    script_lines.extend([
        f'{install_cmd} &&',
        'echo "Cleaning Python cache again after install..." &&',
        f'find {repo_directory} -type d -name __pycache__ -exec rm -rf {{}} + 2>/dev/null || true &&',
        f'find {repo_directory} -type f -name "*.pyc" -delete 2>/dev/null || true &&',
        '',
        'echo "" &&',
        'echo "========================================" &&',
        'echo "Step 4: Reset test files to base commit" &&',
        'echo "========================================" &&',
    ])

    # 重置测试文件
    if test_files:
        script_lines.append(f'git checkout {base_commit} {" ".join(test_files)} &&')
        script_lines.append(f'echo "Test files reset: {len(test_files)} files" &&')
    else:
        script_lines.append('echo "No test file modifications detected" &&')

    # 使用绝对路径（类似成功命令的方式）
    test_patch_script_path = f'"{test_patch_file_path}"'
    
    script_lines.extend([
        '',
        'echo "" &&',
        'echo "========================================" &&',
        'echo "Step 5: Apply Test Patch" &&',
        'echo "========================================" &&',
        # 使用文件路径apply test patch (SWE-bench标准做法)
        f'if [ -f {test_patch_script_path} ]; then',
        f'    git apply -v {test_patch_script_path} || patch --batch --fuzz=5 -p1 -i {test_patch_script_path} || exit 1',
        '    echo "Test patch applied successfully"',
        'else',
        f'    echo "ERROR: Test patch file not found: {test_patch_script_path}"',
        '    exit 1',
        'fi &&',
        '',
        'echo "" &&',
        'echo "========================================" &&',
        'echo "Step 6: Run tests" &&',
        'echo "========================================" &&',
    ])

    # 标记测试输出开始 (与SWE-bench一致)
    # 先输出START标记到文件，然后运行测试追加到同一文件，最后追加END标记
    script_lines.extend([
        f'echo "{START_TEST_OUTPUT}" > {test_output_file}.tmp &&',
        '(',
        f'    export PYTHONPATH={repo_directory}:${{PYTHONPATH:-}} &&',
        f'    echo "PYTHONPATH=$PYTHONPATH" &&',
        f'    {test_command} {test_targets}',
        f') >> {test_output_file}.tmp 2>&1 ; TEST_EXIT_CODE=$? &&',
        f'echo "{END_TEST_OUTPUT}" >> {test_output_file}.tmp &&',
        f'echo "SWEBENCH_TEST_EXIT_CODE=$TEST_EXIT_CODE" >> {test_output_file}.tmp &&',
        f'cat {test_output_file}.tmp | tee {test_output_file} &&',
        f'rm -f {test_output_file}.tmp &&',
        '',
        'echo "" &&',
        'echo "========================================" &&',
        'echo "Step 7: Restore test files" &&',
        'echo "========================================" &&',
    ])

    # 恢复测试文件 (与SWE-bench一致)
    if test_files:
        script_lines.append(f'git checkout {base_commit} {" ".join(test_files)} &&')

    script_lines.extend([
        '',
        'echo "" &&',
        'echo "========================================" &&',
        'echo "Testing completed" &&',
        'echo "========================================" &&',
        'echo "Exit code: $TEST_EXIT_CODE" &&',
        'exit $TEST_EXIT_CODE',
        "'"
    ])

    return '\n'.join(script_lines)


def run_gold_eval_for_instance(instance_id, image_version=None, timeout=1800, wait=True, patch_type="gold", task_name_suffix="", method_name=None):
    """
    为单个instance运行patch评测 - 使用修复后的评估逻辑

    Args:
        instance_id: 实例ID
        image_version: 镜像版本（None时自动选择：有修复用2.1.0，否则用2.0.0）
        timeout: 超时时间（秒）
        wait: 是否等待任务完成
        patch_type: patch类型 ("gold" 或 "model") - 向后兼容参数
        task_name_suffix: 任务名称后缀
        method_name: 方法名称（优先使用，如果为None则从patch_type推断）
    """
    # 确定方法名称
    if method_name is None:
        if patch_type == "gold":
            method_name = "gold"
        else:
            method_name = DEFAULT_METHOD  # 默认使用agentless
    
    # 获取方法配置
    method_config = get_method_config(method_name)
    if not method_config:
        print(f"  ⚠️  警告: 未找到方法配置 '{method_name}'，使用默认配置")
        method_config = get_method_config(DEFAULT_METHOD)
    
    display_name = method_config.get('display_name', method_name)
    print(f"\n{'='*70}")
    print(f"运行 {display_name} 评测: {instance_id}")
    print(f"{'='*70}\n")

    # 1. 从 Dataset 获取实例信息
    print("📥 正在从 Dataset 加载实例信息...")
    ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    instance = [x for x in ds if x['instance_id'] == instance_id][0]

    repo = instance['repo']
    version = instance['version']

    print(f"  ✓ Repo: {repo}")
    print(f"  ✓ Version: {version}")

    # 2. 获取specs
    if repo not in MAP_REPO_VERSION_TO_SPECS or version not in MAP_REPO_VERSION_TO_SPECS[repo]:
        print(f"  ❌ 未找到配置")
        return {"success": False, "error": "Config not found"}

    specs = MAP_REPO_VERSION_TO_SPECS[repo][version]

    # 3. 自动选择镜像版本（如果未指定）
    if image_version is None:
        image_version = get_image_version_for_instance(instance_id)
        if image_version == "2.1.0":
            print(f"  ℹ️  使用修复后的镜像版本: 2.1.0")

    # 4. 读取patch
    print(f"\n📄 读取 {display_name} patch...")
    if method_name == "gold":
        # Gold patch从dataset的'patch'字段读取
        gold_patch = instance['patch']
        print(f"  ✓ Patch 大小: {len(gold_patch)} 字节")

        # Gold patch需要从dataset写入文件（使用配置的项目根目录）
        patch_dir = Path(PROJECT_ROOT) / "patches/gold"
        patch_dir.mkdir(parents=True, exist_ok=True)

        patch_file = patch_dir / f"{instance_id}.diff"
        patch_file.write_text(gold_patch)
        patch_file_path = str(patch_file)
        print(f"  ✓ Patch已写入: {patch_file_path}")
    else:
        # 从patches/{method_name}/目录读取（使用配置的项目根目录）
        patch_dir = Path(PROJECT_ROOT) / f"patches/{method_config['name']}"
        patch_file_path = None
        gold_patch = None
        
        # 按优先级检查文件扩展名
        for ext in method_config['file_extensions']:
            candidate = patch_dir / f"{instance_id}{ext}"
            if candidate.exists():
                patch_file_path = str(candidate)
                print(f"  ✓ 找到patch文件: {candidate.name}")
                break
        
        if not patch_file_path:
            print(f"  ❌ 找不到 {display_name} patch文件")
            print(f"     查找路径: {patch_dir}/")
            print(f"     支持的扩展名: {method_config['file_extensions']}")
            return {"success": False, "error": f"Patch file not found for method {method_name}"}

    # 写入test patch文件（使用配置的项目根目录）
    test_patch = instance['test_patch']
    test_patch_dir = Path(PROJECT_ROOT) / "patches/test"
    test_patch_dir.mkdir(parents=True, exist_ok=True)
    test_patch_file = test_patch_dir / f"{instance_id}.diff"
    test_patch_file.write_text(test_patch)
    test_patch_file_path = str(test_patch_file)
    print(f"  ✓ Test patch已写入: {test_patch_file_path}")

    # 6. 初始化客户端
    print(f"\n📌 初始化 SiFlow 客户端...")
    client = create_siflow_client()

    # 7. 获取 instance 镜像
    from siflow_utils import sanitize_image_name
    instance_image_name = f"swebench-instance-{instance_id}"
    instance_image_name = sanitize_image_name(instance_image_name)

    print(f"🔍 正在查询 instance 镜像: {instance_image_name}:{image_version}")
    instance_image_url = get_image_registry_url(client, instance_image_name, image_version)
    if not instance_image_url:
        print(f"  ❌ 找不到 instance 镜像")
        return {"success": False, "error": "Instance image not found"}

    print(f"  ✓ Instance 镜像: {instance_image_url}")

    # 8. 生成评估脚本 (使用修复后的版本，传递patch文件路径和方法配置)
    print(f"\n📝 生成评估脚本 (修复版本)...")
    eval_script = generate_eval_script_fixed(instance, specs, patch_file_path, test_patch_file_path, method_config)

    script_lines = eval_script.split('\n')
    print(f"  ✓ 脚本生成完成 ({len(script_lines)} 行)")
    print(f"\n  关键步骤:")
    print(f"    1. 应用 Gold Patch 到源代码")
    print(f"    2. 重新安装仓库")
    print(f"    3. 重置测试文件")
    print(f"    4. 应用 Test Patch")
    print(f"    5. 运行测试")

    # 7. 获取需要的环境变量（用于修复）
    from build.fix_build_issues import get_env_vars
    env_vars = get_env_vars(instance_id)

    # 7. 创建评测任务
    print(f"\n🚀 创建 SiFlow 评测任务...")

    # 构建任务名称：SiFlow限制35字符
    # 格式: eval-{short_id}-{method}
    # 例如: eval-django-11066-agentless
    short_id = instance_id.split('__')[-1] if '__' in instance_id else instance_id
    prefix_code = method_config['task_prefix']

    # 计算可用长度: 35 - 5(eval-) - len(prefix_code) - 1(dash)
    max_id_len = 35 - 5 - len(prefix_code) - 1
    if len(short_id) > max_id_len:
        short_id = short_id[:max_id_len]

    if task_name_suffix:
        task_name_prefix = f"sieval-{short_id}-{prefix_code}-{task_name_suffix}"
    else:
        task_name_prefix = f"sieval-{short_id}-{prefix_code}"

    # 最终检查并截断
    if len(task_name_prefix) > 35:
        task_name_prefix = task_name_prefix[:35]

    print(f"  ✓ 任务名称前缀: {task_name_prefix} (method: {method_name})")

    # 构建task_env列表
    task_env_list = [
        TaskEnv(env_key="INSTANCE_ID", env_value=instance_id, hide=False),
        TaskEnv(env_key="PATCH_TYPE", env_value=patch_type, hide=False),  # 向后兼容
        TaskEnv(env_key="METHOD_NAME", env_value=method_name, hide=False),
        TaskEnv(env_key="EVAL_VERSION", env_value="fixed", hide=False),
    ]

    # 添加修复所需的环境变量
    if env_vars:
        for key, value in env_vars.items():
            task_env_list.append(TaskEnv(env_key=key, env_value=value, hide=False))
        print(f"  ✓ 添加修复环境变量: {list(env_vars.keys())}")

    try:
        task_uuid = client.tasks.create(
            name_prefix=task_name_prefix,
            image=instance_image_name,
            image_version=image_version,
            image_url=instance_image_url,
            image_type="custom",
            type="pytorchjob",
            priority="medium",
            cmd=eval_script,
            workers=0,
            resource_pool=RESOURCE_POOL,
            instances=[
                TaskUserSelectedInstance(name=INSTANCE_TYPE, count_per_pod=1)
            ],
            task_env=task_env_list,
            volumes=[
                TaskVolume(mount_dir=VOLUME_MOUNT_DIR, volume_id=VOLUME_ID)
            ]
        )

        print(f"  ✅ 任务创建成功")
        print(f"     Task UUID: {task_uuid}")

    except Exception as e:
        print(f"\n  ❌ 任务创建失败: {e}")
        import traceback
        traceback.print_exc()
        return {
            "success": False,
            "error": str(e),
            "instance_id": instance_id
        }

    # 8. 如果不等待，直接返回
    if not wait:
        return {
            "success": True,
            "task_uuid": task_uuid,
            "instance_id": instance_id,
            "status": "submitted"
        }

    # 9. 等待任务完成
    print(f"\n⏳ 等待任务执行完成...")
    print()

    start_time = time.time()
    last_status = None
    check_interval = 30

    while time.time() - start_time < timeout:
        try:
            task = client.tasks.get(uuid=task_uuid)

            if task.status != last_status:
                elapsed = int(time.time() - start_time)
                elapsed_min = elapsed // 60
                elapsed_sec = elapsed % 60
                print(f"   [{elapsed_min:02d}:{elapsed_sec:02d}] 状态: {task.status}")
                last_status = task.status

            # 检查是否完成
            if task.status == "Succeeded":
                print()
                print(f"✅ 任务执行成功！")

                # 读取保存的测试输出
                log_dir = method_config['log_dir']
                output_dir = Path(f"./{log_dir}")
                test_output_file = output_dir / f"{instance_id}_test_output.txt"

                # 等待文件写入（最多10秒）
                import time as time_module
                for _ in range(10):
                    if test_output_file.exists():
                        break
                    time_module.sleep(1)

                try:
                    print(f"\n📋 读取测试结果...")

                    if test_output_file.exists():
                        test_output = test_output_file.read_text()
                        print(f"  ✓ 测试输出已读取: {test_output_file}")

                        # 检查是否有测试输出标记
                        if START_TEST_OUTPUT not in test_output or END_TEST_OUTPUT not in test_output:
                            print(f"  ⚠️  警告: 测试输出中缺少标记")
                        else:
                            print(f"  ✓ 找到测试输出标记")

                        # 从测试输出中提取exit_code
                        exit_code = -1
                        if "SWEBENCH_TEST_EXIT_CODE=" in test_output:
                            try:
                                for line in test_output.split('\n'):
                                    if 'SWEBENCH_TEST_EXIT_CODE=' in line:
                                        exit_code = int(line.split('=')[1].strip())
                                        break
                            except (ValueError, IndexError):
                                exit_code = -1

                        # 使用log parser解析测试结果
                        repo = instance['repo']
                        log_parser = MAP_REPO_TO_PARSER[repo]
                        status_map = log_parser(test_output, instance)

                        print(f"  ✓ 解析到 {len(status_map)} 个测试结果")

                        # 获取FAIL_TO_PASS和PASS_TO_PASS测试列表
                        import json
                        fail_to_pass_str = instance.get('FAIL_TO_PASS', '[]')
                        pass_to_pass_str = instance.get('PASS_TO_PASS', '[]')

                        fail_to_pass = json.loads(fail_to_pass_str) if isinstance(fail_to_pass_str, str) else fail_to_pass_str
                        pass_to_pass = json.loads(pass_to_pass_str) if isinstance(pass_to_pass_str, str) else pass_to_pass_str

                        gold_results = {
                            FAIL_TO_PASS: fail_to_pass,
                            PASS_TO_PASS: pass_to_pass
                        }

                        # 生成测试报告
                        report = get_eval_tests_report(status_map, gold_results)
                        resolution_status = get_resolution_status(report)

                        # 判断是否resolved
                        resolved = (resolution_status == "RESOLVED_FULL")

                        # 打印详细的测试结果
                        print(f"\n  📊 测试结果统计:")
                        print(f"  {'='*60}")

                        # FAIL_TO_PASS
                        f2p_pass = len(report[FAIL_TO_PASS]['success'])
                        f2p_total = len(fail_to_pass)
                        print(f"\n  🎯 FAIL_TO_PASS: {f2p_pass}/{f2p_total} passed")

                        if f2p_pass > 0:
                            print(f"     ✅ 成功:")
                            for test in report[FAIL_TO_PASS]['success'][:3]:
                                print(f"        • {test}")
                            if f2p_pass > 3:
                                print(f"        ... 及其他 {f2p_pass - 3} 个")

                        if report[FAIL_TO_PASS]['failure']:
                            print(f"     ❌ 失败:")
                            for test in report[FAIL_TO_PASS]['failure'][:3]:
                                print(f"        • {test}")
                            if len(report[FAIL_TO_PASS]['failure']) > 3:
                                print(f"        ... 及其他 {len(report[FAIL_TO_PASS]['failure']) - 3} 个")

                        # PASS_TO_PASS
                        p2p_pass = len(report[PASS_TO_PASS]['success'])
                        p2p_total = len(pass_to_pass)
                        print(f"\n  🛡️  PASS_TO_PASS: {p2p_pass}/{p2p_total} passed")

                        if report[PASS_TO_PASS]['failure']:
                            print(f"     ⚠️  回归:")
                            for test in report[PASS_TO_PASS]['failure'][:3]:
                                print(f"        • {test}")
                            if len(report[PASS_TO_PASS]['failure']) > 3:
                                print(f"        ... 及其他 {len(report[PASS_TO_PASS]['failure']) - 3} 个")

                        print(f"\n  {'='*60}")
                        print(f"  最终状态: {resolution_status}")
                        print(f"  退出码: {exit_code}")

                        if resolved:
                            print(f"  ✅ RESOLVED_FULL - Gold Patch 完全解决问题")
                        else:
                            print(f"  ❌ {resolution_status} - Gold Patch 未完全解决问题")
                    else:
                        print(f"  ⚠️  未找到测试输出文件: {test_output_file}")
                        resolved = False

                except Exception as e:
                    print(f"  ⚠️  读取结果失败: {e}")
                    import traceback
                    traceback.print_exc()
                    resolved = False

                return {
                    "success": True,
                    "instance_id": instance_id,
                    "task_uuid": task_uuid,
                    "resolved": resolved,
                    "resolution_status": resolution_status if 'resolution_status' in locals() else "UNKNOWN",
                    "exit_code": exit_code if 'exit_code' in locals() else -1,
                    "report": report if 'report' in locals() else None,
                    "execution_time": int(time.time() - start_time),
                    "test_output_file": str(test_output_file) if test_output_file.exists() else None
                }

            elif task.status in ["Failed", "Error"]:
                print()
                print(f"⚠️  任务状态: {task.status}，但仍尝试分析日志文件...")
                
                # 即使任务失败，也尝试读取日志文件分析resolve状态
                log_dir = method_config['log_dir']
                output_dir = Path(f"./{log_dir}")
                test_output_file = output_dir / f"{instance_id}_test_output.txt"
                
                if test_output_file.exists():
                    print(f"  ✓ 找到日志文件，开始分析...")
                    try:
                        test_output = test_output_file.read_text()
                        
                        # 检查是否有测试输出标记
                        if START_TEST_OUTPUT not in test_output or END_TEST_OUTPUT not in test_output:
                            print(f"  ⚠️  警告: 测试输出中缺少标记")
                        else:
                            print(f"  ✓ 找到测试输出标记")
                        
                        # 从测试输出中提取exit_code
                        exit_code = -1
                        if "SWEBENCH_TEST_EXIT_CODE=" in test_output:
                            try:
                                for line in test_output.split('\n'):
                                    if 'SWEBENCH_TEST_EXIT_CODE=' in line:
                                        exit_code = int(line.split('=')[1].strip())
                                        break
                            except (ValueError, IndexError):
                                exit_code = -1
                        
                        # 使用log parser解析测试结果
                        repo = instance['repo']
                        log_parser = MAP_REPO_TO_PARSER[repo]
                        status_map = log_parser(test_output, instance)
                        
                        print(f"  ✓ 解析到 {len(status_map)} 个测试结果")
                        
                        # 获取FAIL_TO_PASS和PASS_TO_PASS测试列表
                        import json
                        fail_to_pass_str = instance.get('FAIL_TO_PASS', '[]')
                        pass_to_pass_str = instance.get('PASS_TO_PASS', '[]')
                        
                        fail_to_pass = json.loads(fail_to_pass_str) if isinstance(fail_to_pass_str, str) else fail_to_pass_str
                        pass_to_pass = json.loads(pass_to_pass_str) if isinstance(pass_to_pass_str, str) else pass_to_pass_str
                        
                        gold_results = {
                            FAIL_TO_PASS: fail_to_pass,
                            PASS_TO_PASS: pass_to_pass
                        }
                        
                        # 生成测试报告
                        report = get_eval_tests_report(status_map, gold_results)
                        resolution_status = get_resolution_status(report)
                        
                        # 判断是否resolved
                        resolved = (resolution_status == "RESOLVED_FULL")
                        
                        # 打印详细的测试结果
                        print(f"\n  📊 测试结果统计:")
                        print(f"  {'='*60}")
                        
                        # FAIL_TO_PASS
                        f2p_pass = len(report[FAIL_TO_PASS]['success'])
                        f2p_total = len(fail_to_pass)
                        print(f"\n  🎯 FAIL_TO_PASS: {f2p_pass}/{f2p_total} passed")
                        
                        if f2p_pass > 0:
                            print(f"     ✅ 成功:")
                            for test in report[FAIL_TO_PASS]['success'][:3]:
                                print(f"        • {test}")
                            if f2p_pass > 3:
                                print(f"        ... 及其他 {f2p_pass - 3} 个")
                        
                        if report[FAIL_TO_PASS]['failure']:
                            print(f"     ❌ 失败:")
                            for test in report[FAIL_TO_PASS]['failure'][:3]:
                                print(f"        • {test}")
                            if len(report[FAIL_TO_PASS]['failure']) > 3:
                                print(f"        ... 及其他 {len(report[FAIL_TO_PASS]['failure']) - 3} 个")
                        
                        # PASS_TO_PASS
                        p2p_pass = len(report[PASS_TO_PASS]['success'])
                        p2p_total = len(pass_to_pass)
                        print(f"\n  🛡️  PASS_TO_PASS: {p2p_pass}/{p2p_total} passed")
                        
                        if report[PASS_TO_PASS]['failure']:
                            print(f"     ⚠️  回归:")
                            for test in report[PASS_TO_PASS]['failure'][:3]:
                                print(f"        • {test}")
                            if len(report[PASS_TO_PASS]['failure']) > 3:
                                print(f"        ... 及其他 {len(report[PASS_TO_PASS]['failure']) - 3} 个")
                        
                        print(f"\n  {'='*60}")
                        print(f"  最终状态: {resolution_status}")
                        print(f"  退出码: {exit_code}")
                        
                        if resolved:
                            print(f"  ✅ RESOLVED_FULL - 完全解决问题！")
                        else:
                            print(f"  ❌ {resolution_status} - 未完全解决问题")
                        
                        return {
                            "success": True,  # 即使任务失败，但日志分析成功
                            "instance_id": instance_id,
                            "task_uuid": task_uuid,
                            "resolved": resolved,
                            "resolution_status": resolution_status,
                            "exit_code": exit_code,
                            "report": report,
                            "execution_time": int(time.time() - start_time),
                            "test_output_file": str(test_output_file),
                            "task_status": task.status  # 记录原始任务状态
                        }
                    except Exception as e:
                        print(f"  ⚠️  分析日志失败: {e}")
                        import traceback
                        traceback.print_exc()
                
                # 如果没有日志文件或分析失败，返回失败
                return {
                    "success": False,
                    "instance_id": instance_id,
                    "task_uuid": task_uuid,
                    "status": "failed",
                    "error": "Task failed and no valid log file found"
                }

        except Exception as e:
            print(f"   ⚠️  查询失败: {e}")

        time.sleep(check_interval)

    # 超时
    print()
    print(f"❌ 任务执行超时 (>{timeout}秒)")
    return {
        "success": False,
        "instance_id": instance_id,
        "task_uuid": task_uuid,
        "status": "timeout"
    }


def main():
    """主函数"""
    import argparse

    parser = argparse.ArgumentParser(description="运行 gold patch 评测 (修复版本)")
    parser.add_argument("instance_id", help="Instance ID")
    parser.add_argument("--version", default="2.0.0", help="镜像版本")
    parser.add_argument("--timeout", type=int, default=1800, help="超时时间（秒）")
    parser.add_argument("--wait", action="store_true", help="等待任务完成")

    args = parser.parse_args()

    result = run_gold_eval_for_instance(
        instance_id=args.instance_id,
        image_version=args.version,
        timeout=args.timeout,
        wait=args.wait
    )

    print("\n" + "="*70)
    if result.get("success"):
        if result.get("resolved"):
            print(f"🎉 评测成功 - RESOLVED_FULL")
        elif result.get("status") == "submitted":
            print("✅ 任务已提交")
            print(f"Task UUID: {result.get('task_uuid')}")
        else:
            print(f"⚠️  评测完成 - {result.get('resolution_status', 'UNKNOWN')}")
        if result.get("test_output_file"):
            print(f"测试输出: {result.get('test_output_file')}")
        return 0 if result.get("resolved") else 1
    else:
        print("❌ 评测失败")
        print(f"错误: {result.get('error', 'Unknown')}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
