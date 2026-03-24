#!/usr/bin/env python3
"""
端到端：在 SciTix/aries swebench-instance 容器里
  1. 运行 mini-swe-agent 生成 patch
  2. 直接 apply patch + 运行测试（同一容器）
  3. Task exit_code = 0 → 测试通过 (RESOLVED)

特点：
  - patch 通过 base64 打印到 stdout（PATCH_BEGIN_B64 / PATCH_END_B64）
  - mini-swe-agent src 走 /volume/ai-infra/... 挂载路径
  - 生成 + 评测合并为一个 SiFlow Task

用法:
  单个实例 (等待结果):
    python patch_gen/run_generate_and_eval.py \\
        --instance django__django-13837

  两个实例同时提交 (不等待):
    python patch_gen/run_generate_and_eval.py \\
        --batch --filter "django__django-1383[0-9]" \\
        --workers 2 --no-wait

  自定义模型/API:
    python patch_gen/run_generate_and_eval.py \\
        --instance django__django-13837 \\
        --model openai/Qwen/Qwen3-30B-A3B-mcore \\
        --api-base https://scitix-aries.scitix.ai/.../v1 \\
        --method qwen3_30b
"""

from __future__ import annotations

import argparse
import base64
import concurrent.futures
import json
import logging
import os
import re
import sys
import threading
import time
from pathlib import Path

# ── 路径 ──────────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent

sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "eval"))
sys.path.insert(0, str(PROJECT_ROOT / "build"))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

# 强制 aries 平台
os.environ.setdefault("SIFLOW_REGION",        "ap-southeast")
os.environ.setdefault("SIFLOW_CLUSTER",       "aries")
os.environ.setdefault("SIFLOW_RESOURCE_POOL", "ap-southeast-aries-hisys-ondemand-shared")

from siflow.types import TaskEnv, TaskUserSelectedInstance
from siflow_utils import create_siflow_client, get_image_registry_url, sanitize_image_name
from build.fix_build_issues import get_env_vars
from datasets import load_dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_gen_eval")

# ── 常量 ──────────────────────────────────────────────────────────────────────
DATASET_MAPPING = {
    "full":     "princeton-nlp/SWE-Bench",
    "verified": "princeton-nlp/SWE-Bench_Verified",
    "lite":     "princeton-nlp/SWE-Bench_Lite",
}
DEFAULT_SUBSET   = "verified"
DEFAULT_SPLIT    = "test"
DEFAULT_METHOD   = "qwen3_30b"
DEFAULT_MODEL    = "openai/Qwen/Qwen3-30B-A3B-mcore"
DEFAULT_API_BASE = (
    "https://scitix-aries.scitix.ai/siflow/aries/hisys/rhjiang/qwen3-30b-a3b-mcore/v1"
)

ARIES_RESOURCE_POOL = "ap-southeast-aries-hisys-ondemand-shared"
ARIES_INSTANCE_TYPE = "sci.c23-2"
IMAGE_VERSION       = "1.0.0"

# mini-swe-agent 在容器内通过 volume 可访问的路径
MINI_SWE_SRC = "/volume/ai-infra/rhjiang/Swebench_in_Siflow/mini-swe-agent/src"

# SWE-bench 测试输出标记
START_TEST_OUTPUT = ">>>>> Start Test Output"
END_TEST_OUTPUT   = ">>>>> End Test Output"


# ─────────────────────────────────────────────────────────────────────────────
# 获取 swebench 测试规格（在本机用 swebench_scitix 环境）
# ─────────────────────────────────────────────────────────────────────────────

def _get_test_specs(instance: dict) -> tuple[str, str, list[str], list[str]]:
    """返回 (test_cmd, install_cmd, test_directives, test_files)"""
    swebench_site = (
        "/minconda3/envs/swebench_scitix/lib/python3.10/site-packages"
    )
    if swebench_site not in sys.path:
        sys.path.insert(0, swebench_site)
    try:
        from swebench.harness.constants import MAP_REPO_VERSION_TO_SPECS
        from swebench.harness.test_spec.python import (
            get_test_directives,
            get_modified_files,
        )
        specs = (
            MAP_REPO_VERSION_TO_SPECS
            .get(instance["repo"], {})
            .get(instance["version"], {})
        )
        return (
            specs.get(
                "test_cmd",
                "./tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1",
            ),
            specs.get("install", "python -m pip install -e ."),
            get_test_directives(instance),
            get_modified_files(instance["test_patch"]),
        )
    except Exception as e:
        logger.warning("无法获取 swebench specs，用默认值: %s", e)
        return (
            "./tests/runtests.py --verbosity 2 --settings=test_sqlite --parallel 1",
            "python -m pip install -e .",
            [],
            [],
        )


# ─────────────────────────────────────────────────────────────────────────────
# 构建容器内运行的 bash 脚本
# ─────────────────────────────────────────────────────────────────────────────

def _build_cmd(
    instance: dict,
    model_name: str,
    api_base: str,
    api_key: str,
    step_limit: int,
    bash_timeout: int,
) -> str:
    """
    生成在 swebench-instance 容器内运行的完整 bash 脚本。
    所有动态内容（problem_statement、prompt 模板、Python 代码等）
    全部 base64 编码后嵌入，彻底避免引号/heredoc 冲突。
    """
    test_cmd, install_cmd, test_dirs, test_files = _get_test_specs(instance)
    test_targets = " ".join(test_dirs)
    reset_cmd    = (
        "git checkout $BASE_COMMIT " + " ".join(test_files)
        if test_files else "true"
    )
    restore_cmd  = reset_cmd

    # ── 在容器内执行的 Python runner ─────────────────────────────────────────
    # 注意：这段代码本身是普通字符串，不是 f-string，
    # 所以 {model_name} 这类占位符要在下面单独替换。
    runner_template = r"""
import base64, os, sys

os.environ["OPENAI_API_KEY"]       = API_KEY_PLACEHOLDER
os.environ["OPENAI_API_BASE"]      = API_BASE_PLACEHOLDER
os.environ["MSWEA_SILENT_STARTUP"] = "1"
os.environ["MSWEA_COST_TRACKING"]  = "ignore_errors"

mini_src = base64.b64decode("MINI_SRC_B64_PLACEHOLDER").decode()
if mini_src not in sys.path:
    sys.path.insert(0, mini_src)

from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.local import LocalEnvironment
from minisweagent.models.litellm_textbased_model import LitellmTextbasedModel

SYSTEM_TEMPLATE = base64.b64decode("SYSTEM_B64_PLACEHOLDER").decode()
INSTANCE_TEMPLATE = base64.b64decode("INSTANCE_B64_PLACEHOLDER").decode()
task = base64.b64decode("PS_B64_PLACEHOLDER").decode()

model = LitellmTextbasedModel(
    model_name=MODEL_NAME_PLACEHOLDER,
    model_kwargs={"temperature": 0.0, "drop_params": True},
    cost_tracking="ignore_errors",
)
env = LocalEnvironment(
    cwd="/testbed",
    timeout=BASH_TIMEOUT_PLACEHOLDER,
    env={"PAGER": "cat", "MANPAGER": "cat", "LESS": "-R",
         "PIP_PROGRESS_BAR": "off", "TQDM_DISABLE": "1"},
)
agent = DefaultAgent(
    model, env,
    system_template=SYSTEM_TEMPLATE,
    instance_template=INSTANCE_TEMPLATE,
    step_limit=STEP_LIMIT_PLACEHOLDER,
    cost_limit=0.0,
)

info   = agent.run(task)
status = info.get("exit_status", "Unknown")
patch  = info.get("submission", "") or ""

print(f"[gen] exit_status={status}", flush=True)
print(f"[gen] patch_len={len(patch)}",  flush=True)

if patch.strip():
    open("/tmp/model.patch", "w").write(patch)
    encoded = base64.b64encode(patch.encode()).decode()
    print("PATCH_BEGIN_B64", flush=True)
    print(encoded,           flush=True)
    print("PATCH_END_B64",   flush=True)
    sys.exit(0)
else:
    print("[gen] ERROR: empty patch", flush=True)
    sys.exit(1)
"""

    system_template = (
        "You are a helpful assistant that can interact multiple times with a "
        "computer shell to solve programming tasks.\n"
        "Your response must contain exactly ONE bash code block with ONE command "
        "(or commands connected with && or ||).\n\n"
        "Include a THOUGHT section before your command where you explain your "
        "reasoning process.\n"
        "Format your response as shown in <format_example>.\n\n"
        "<format_example>\n"
        "THOUGHT: Your reasoning and analysis here\n\n"
        "```mswea_bash_command\n"
        "your_command_here\n"
        "```\n"
        "</format_example>\n\n"
        "Failure to follow these rules will cause your response to be rejected."
    )

    instance_template = (
        "<pr_description>\n"
        "Consider the following PR description:\n"
        "{{task}}\n"
        "</pr_description>\n\n"
        "<instructions>\n"
        "You are a software engineer. Your task is to make changes to non-test "
        "files in /testbed to fix the issue described above.\n\n"
        "## Rules\n"
        "- MODIFY: source code files in /testbed only\n"
        "- DO NOT MODIFY: tests, pyproject.toml, setup.cfg, setup.py, etc.\n"
        "- Working dir is /testbed. cd is NOT persistent between commands.\n\n"
        "## Workflow\n"
        "1. Find and read relevant source files\n"
        "2. Reproduce the issue with a small script\n"
        "3. Fix the source code\n"
        "4. Verify the fix\n\n"
        "## Submission\n"
        "Step 1 - Create patch (list ONLY changed source files):\n"
        "```mswea_bash_command\n"
        "cd /testbed && git diff -- path/to/changed_file.py > /tmp/patch.txt\n"
        "```\n\n"
        "Step 2 - Verify patch is non-empty:\n"
        "```mswea_bash_command\n"
        "cat /tmp/patch.txt\n"
        "```\n\n"
        "Step 3 - Submit (EXACT command, run SEPARATELY):\n"
        "```mswea_bash_command\n"
        "echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat /tmp/patch.txt\n"
        "```\n"
        "</instructions>"
    )

    # 替换所有占位符
    runner_py = (
        runner_template
        .replace("API_KEY_PLACEHOLDER",          json.dumps(api_key))
        .replace("API_BASE_PLACEHOLDER",         json.dumps(api_base))
        .replace("MINI_SRC_B64_PLACEHOLDER",
                 base64.b64encode(MINI_SWE_SRC.encode()).decode())
        .replace("SYSTEM_B64_PLACEHOLDER",
                 base64.b64encode(system_template.encode()).decode())
        .replace("INSTANCE_B64_PLACEHOLDER",
                 base64.b64encode(instance_template.encode()).decode())
        .replace("PS_B64_PLACEHOLDER",
                 base64.b64encode(instance["problem_statement"].encode()).decode())
        .replace("MODEL_NAME_PLACEHOLDER",       json.dumps(model_name))
        .replace("BASH_TIMEOUT_PLACEHOLDER",     str(bash_timeout))
        .replace("STEP_LIMIT_PLACEHOLDER",       str(step_limit))
    )

    runner_b64      = base64.b64encode(runner_py.encode()).decode()
    test_patch_b64  = base64.b64encode(instance["test_patch"].encode()).decode()

    # ── 完整 bash 脚本（在容器里执行）───────────────────────────────────────
    # 注意：使用 heredoc (<<"PY") 而不是 python3 -c "..."，避免单引号嵌套问题。
    # 外层是 bash -lc '...'（单引号），内层 Python 用 <<"PY" heredoc 传入，互不干扰。
    cmd = (
        "bash -lc '\n"
        "set -euo pipefail\n"
        "source /opt/miniconda3/bin/activate\n"
        "conda activate testbed\n"
        "cd /testbed\n\n"
        "echo \"=== [Step 1] Generate patch with mini-swe-agent ===\"\n"
        'python3 - <<"PY"\n'
        "import base64, sys\n"
        "src = base64.b64decode(\"" + runner_b64 + "\").decode()\n"
        "exec(compile(src, \"<runner>\", \"exec\"))\n"
        "PY\n\n"
        "echo \"=== [Step 2] Write test patch ===\"\n"
        'python3 - <<"PY"\n'
        "import base64, pathlib\n"
        "pathlib.Path(\"/tmp/test.patch\").write_bytes(base64.b64decode(\"" + test_patch_b64 + "\"))\n"
        "PY\n\n"
        "echo \"=== [Step 3] Apply model patch ===\"\n"
        "BASE_COMMIT=$(git rev-parse HEAD)\n"
        "git apply --verbose /tmp/model.patch "
        "|| patch --batch --fuzz=5 -p1 -i /tmp/model.patch\n\n"
        "echo \"=== [Step 4] Reinstall ===\"\n"
        + install_cmd + "\n\n"
        "echo \"=== [Step 5] Reset test files & apply test patch ===\"\n"
        + reset_cmd + "\n"
        "git apply -v /tmp/test.patch "
        "|| patch --batch --fuzz=5 -p1 -i /tmp/test.patch\n\n"
        "echo \"=== [Step 6] Run tests ===\"\n"
        "export PYTHONPATH=/testbed:${PYTHONPATH:-}\n"
        "echo \"" + START_TEST_OUTPUT + "\"\n"
        + test_cmd + " " + test_targets + "\n"
        "TEST_EXIT=$?\n"
        "echo \"" + END_TEST_OUTPUT + "\"\n"
        "echo \"SWEBENCH_TEST_EXIT_CODE=$TEST_EXIT\"\n\n"
        + restore_cmd + "\n"
        "exit $TEST_EXIT\n"
        "'"
    )

    return cmd


# ─────────────────────────────────────────────────────────────────────────────
# 提交单个实例
# ─────────────────────────────────────────────────────────────────────────────

def submit_instance(
    instance: dict,
    *,
    model_name: str,
    api_base: str,
    api_key: str = "EMPTY",
    method: str = DEFAULT_METHOD,
    image_version: str = IMAGE_VERSION,
    step_limit: int = 80,
    bash_timeout: int = 60,
    task_timeout: int = 3600,
    wait: bool = True,
) -> dict:
    instance_id = instance["instance_id"]
    client      = create_siflow_client()

    image_name = sanitize_image_name(f"swebench-instance-{instance_id}")
    image_url  = get_image_registry_url(client, image_name, image_version)
    if not image_url:
        logger.error("[%s] 找不到镜像 %s:%s", instance_id, image_name, image_version)
        return {
            "instance_id": instance_id, "success": False,
            "task_uuid": None, "exit_status": "ImageNotFound",
        }

    logger.info("[%s] 镜像 OK: %s", instance_id, image_url)

    cmd = _build_cmd(
        instance=instance,
        model_name=model_name,
        api_base=api_base,
        api_key=api_key,
        step_limit=step_limit,
        bash_timeout=bash_timeout,
    )

    # Task 名称 ≤35 字符
    short_id    = instance_id.split("__")[-1] if "__" in instance_id else instance_id
    method_code = re.sub(r"[^a-z0-9]", "", method.lower())[:4]
    task_prefix = ("sge-" + short_id + "-" + method_code)[:35]

    task_env = [
        TaskEnv(env_key="INSTANCE_ID", env_value=instance_id, hide=False),
        TaskEnv(env_key="GEN_METHOD",  env_value=method,       hide=False),
        TaskEnv(env_key="GEN_MODEL",   env_value=model_name,   hide=False),
    ]
    for k, v in (get_env_vars(instance_id) or {}).items():
        task_env.append(TaskEnv(env_key=k, env_value=v, hide=False))

    try:
        task_uuid = client.tasks.create(
            name_prefix=task_prefix,
            image=image_name,
            image_version=image_version,
            image_url=image_url,
            image_type="custom",
            type="pytorchjob",
            priority="medium",
            cmd=cmd,
            workers=0,
            resource_pool=ARIES_RESOURCE_POOL,
            instances=[TaskUserSelectedInstance(
                name=ARIES_INSTANCE_TYPE, count_per_pod=1
            )],
            task_env=task_env,
        )
    except Exception as e:
        logger.error("[%s] Task 提交失败: %s", instance_id, e)
        return {
            "instance_id": instance_id, "success": False,
            "task_uuid": None, "exit_status": str(e),
        }

    logger.info("[%s] ✅ Task 已提交: %s", instance_id, task_uuid)

    if not wait:
        return {
            "instance_id": instance_id, "success": True,
            "task_uuid": task_uuid, "exit_status": "Submitted",
        }

    # ── 等待完成 ──────────────────────────────────────────────────────────────
    t0, last_status = time.time(), None
    while time.time() - t0 < task_timeout:
        try:
            task = client.tasks.get(uuid=task_uuid)
        except Exception as e:
            logger.warning("[%s] 查询失败: %s", instance_id, e)
            time.sleep(30)
            continue

        if task.status != last_status:
            elapsed = int(time.time() - t0)
            logger.info(
                "[%s] [%02d:%02d] %s",
                instance_id, elapsed // 60, elapsed % 60, task.status,
            )
            last_status = task.status

        if task.status == "Succeeded":
            logger.info("[%s] ✅ RESOLVED (task exit=0)", instance_id)
            logger.info(
                "[%s] 📋 提取 patch: 查看 task %s 日志，"
                "找 PATCH_BEGIN_B64..PATCH_END_B64 段",
                instance_id, task_uuid,
            )
            return {
                "instance_id": instance_id, "success": True,
                "task_uuid": task_uuid, "exit_status": "Succeeded",
                "resolved": True,
            }

        if task.status in ("Failed", "Error", "Stopped"):
            logger.warning("[%s] ❌ %s", instance_id, task.status)
            return {
                "instance_id": instance_id, "success": False,
                "task_uuid": task_uuid, "exit_status": task.status,
                "resolved": False,
            }

        time.sleep(30)

    return {
        "instance_id": instance_id, "success": False,
        "task_uuid": task_uuid, "exit_status": "Timeout", "resolved": False,
    }


# ─────────────────────────────────────────────────────────────────────────────
# 批量提交
# ─────────────────────────────────────────────────────────────────────────────

def submit_batch(
    instances: list[dict],
    *,
    model_name: str,
    api_base: str,
    api_key: str,
    method: str,
    image_version: str,
    step_limit: int,
    bash_timeout: int,
    task_timeout: int,
    workers: int,
    wait: bool,
    results_file: Path,
) -> list[dict]:
    all_results: list[dict] = []
    lock = threading.Lock()

    def _process(inst):
        result = submit_instance(
            inst,
            model_name=model_name, api_base=api_base, api_key=api_key,
            method=method, image_version=image_version,
            step_limit=step_limit, bash_timeout=bash_timeout,
            task_timeout=task_timeout, wait=wait,
        )
        with lock:
            all_results.append(result)
            results_file.parent.mkdir(parents=True, exist_ok=True)
            results_file.write_text(
                json.dumps(all_results, indent=2, ensure_ascii=False)
            )
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {
            executor.submit(_process, inst): inst["instance_id"]
            for inst in instances
        }
        done = 0
        for fut in concurrent.futures.as_completed(futures):
            iid = futures[fut]
            done += 1
            try:
                res = fut.result()
                icon = (
                    "✅" if res.get("resolved")
                    else ("🔄" if res["exit_status"] == "Submitted" else "❌")
                )
                logger.info(
                    "[%d/%d] %s %s  status=%s  uuid=%s",
                    done, len(instances), icon, iid,
                    res["exit_status"], res.get("task_uuid", "N/A"),
                )
            except Exception as exc:
                logger.error("[%d/%d] ❌ %s: %s", done, len(instances), iid, exc)

    return all_results


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser() -> argparse.ArgumentParser:
    p = argparse.ArgumentParser(
        description="SciTix aries 上一键 生成+评测 SWE-bench patch（单 Task）",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    dg = p.add_argument_group("数据选择")
    me = dg.add_mutually_exclusive_group(required=True)
    me.add_argument("--instance", "-i", metavar="ID")
    me.add_argument("--batch", action="store_true")
    dg.add_argument("--subset", default=DEFAULT_SUBSET, choices=list(DATASET_MAPPING))
    dg.add_argument("--split",  default=DEFAULT_SPLIT)
    dg.add_argument("--filter", metavar="REGEX", default="")
    dg.add_argument("--slice",  metavar="START:END", default="")

    mg = p.add_argument_group("模型")
    mg.add_argument("--model",    "-m", default=DEFAULT_MODEL)
    mg.add_argument("--api-base",       default=DEFAULT_API_BASE)
    mg.add_argument("--api-key",        default="EMPTY")

    rg = p.add_argument_group("运行参数")
    rg.add_argument("--image-version", default=IMAGE_VERSION)
    rg.add_argument("--step-limit",    type=int, default=80)
    rg.add_argument("--bash-timeout",  type=int, default=60,
                    help="容器内每条 bash 命令的超时（秒）")
    rg.add_argument("--task-timeout",  type=int, default=3600,
                    help="等待 Task 完成的最长时间（秒）")
    rg.add_argument("--workers", "-w", type=int, default=1)
    rg.add_argument("--no-wait",       action="store_true",
                    help="只提交 Task，不等待结果（批量时推荐）")

    og = p.add_argument_group("输出")
    og.add_argument("--method",       default=DEFAULT_METHOD)
    og.add_argument("--results-file", metavar="PATH", default="")
    return p


def main():
    parser = _build_parser()
    args   = parser.parse_args()

    dataset_path = DATASET_MAPPING[args.subset]
    logger.info("加载数据集 %s ...", dataset_path)
    all_instances = list(load_dataset(dataset_path, split=args.split))
    instance_map  = {i["instance_id"]: i for i in all_instances}

    common = dict(
        model_name    = args.model,
        api_base      = args.api_base,
        api_key       = args.api_key,
        method        = args.method,
        image_version = args.image_version,
        step_limit    = args.step_limit,
        bash_timeout  = args.bash_timeout,
        task_timeout  = args.task_timeout,
        wait          = not args.no_wait,
    )

    if args.instance:
        if args.instance not in instance_map:
            logger.error("实例 '%s' 不在数据集中", args.instance)
            sys.exit(1)
        result = submit_instance(instance_map[args.instance], **common)
        print("\n" + "=" * 60)
        print(f"实例:        {result['instance_id']}")
        print(f"Task UUID:   {result.get('task_uuid', 'N/A')}")
        print(f"exit_status: {result['exit_status']}")
        if result.get("resolved") is not None:
            print(f"RESOLVED:    {'✅ YES' if result['resolved'] else '❌ NO'}")
        print("=" * 60)
        sys.exit(0 if result.get("success") else 1)

    # ── 批量 ──────────────────────────────────────────────────────────────────
    instances = all_instances
    if args.filter:
        instances = [i for i in instances if re.search(args.filter, i["instance_id"])]
    if args.slice:
        parts     = [int(x) if x else None for x in args.slice.split(":")]
        instances = instances[slice(*parts)]

    logger.info(
        "待处理 %d 个实例，并发=%d，wait=%s",
        len(instances), args.workers, not args.no_wait,
    )

    results_file = (
        Path(args.results_file) if args.results_file
        else PROJECT_ROOT / "logs" / f"{args.method}_patch" / "gen_eval_results.json"
    )
    results = submit_batch(instances, workers=args.workers,
                           results_file=results_file, **common)

    resolved  = sum(1 for r in results if r.get("resolved"))
    submitted = sum(1 for r in results if r["exit_status"] == "Submitted")
    failed    = sum(1 for r in results if not r.get("success")
                    and r["exit_status"] not in ("Submitted",))
    print(f"\n批量完成: {len(results)} 个实例")
    print(f"  ✅ RESOLVED:  {resolved}")
    print(f"  🔄 Submitted: {submitted}  (--no-wait，结果待查)")
    print(f"  ❌ Failed:    {failed}")
    print(f"  结果文件:     {results_file}")


if __name__ == "__main__":
    main()
