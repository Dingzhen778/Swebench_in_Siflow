#!/usr/bin/env python3
"""
Patch 生成脚本 - 本地直接运行 mini-swe-agent 生成 patch

架构（本地模式，不依赖平台）：
  直接在当前机器上运行 mini-swe-agent
  → agent 调用外部 API（OpenAI 兼容接口）
  → 生成 patch（git diff 格式）
  → 写入 patches/{method}/{instance_id}.diff
  → 轨迹写入 logs/{method}_patch/{instance_id}.traj.json

注意：本地运行需要 /testbed 目录不存在时，agent 会在宿主机执行命令。
      推荐在对应的 swebench-instance 容器内运行，或挂载了 testbed 的环境里运行。
      如果你有 SiFlow/SciTix 平台且想在容器里跑，参考 generate_patch_siflow.py（已保留备份）。

用法:
  单个实例:
    python patch_gen/generate_patch.py \\
        --instance django__django-13837 \\
        --model openai/Qwen/Qwen3-30B-A3B-mcore \\
        --api-base https://scitix-aries.scitix.ai/.../v1 \\
        --method qwen3_30b

  批量:
    python patch_gen/generate_patch.py \\
        --batch --filter "django__django" \\
        --model openai/Qwen/Qwen3-30B-A3B-mcore \\
        --api-base https://scitix-aries.scitix.ai/.../v1 \\
        --method qwen3_30b --workers 4
"""

from __future__ import annotations

import argparse
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

# mini-swe-agent src 路径（submodule）
MINI_SRC = PROJECT_ROOT / "mini-swe-agent" / "src"
if str(MINI_SRC) not in sys.path:
    sys.path.insert(0, str(MINI_SRC))

from dotenv import load_dotenv
load_dotenv(PROJECT_ROOT / ".env")

from datasets import load_dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("generate_patch")

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
DEFAULT_API_BASE = "https://scitix-aries.scitix.ai/siflow/aries/hisys/rhjiang/qwen3-30b-a3b-mcore/v1"

# mini-swe-agent prompt 模板（backticks 格式，不依赖 tool_call 协议）
SYSTEM_TEMPLATE = """You are a helpful assistant that can interact multiple times with a computer shell to solve programming tasks.
Your response must contain exactly ONE bash code block with ONE command (or commands connected with && or ||).

Include a THOUGHT section before your command where you explain your reasoning process.
Format your response as shown in <format_example>.

<format_example>
THOUGHT: Your reasoning and analysis here

```mswea_bash_command
your_command_here
```
</format_example>

Failure to follow these rules will cause your response to be rejected."""

INSTANCE_TEMPLATE = """<pr_description>
Consider the following PR description:
{task}
</pr_description>

<instructions>
You are a software engineer. Your task is to make changes to non-test files in /testbed to fix the issue described above.

## Rules
- MODIFY: source code files in /testbed only
- DO NOT MODIFY: tests, pyproject.toml, setup.cfg, setup.py, etc.
- Working dir is /testbed. cd is NOT persistent between commands.

## Workflow
1. Find and read relevant source files
2. Reproduce the issue with a small script
3. Fix the source code
4. Verify the fix

## Submission
Step 1 - Create patch (list ONLY changed source files, not test/helper scripts):
```mswea_bash_command
cd /testbed && git diff -- changed/file1.py changed/file2.py > /tmp/patch.txt
```

Step 2 - Verify patch is non-empty:
```mswea_bash_command
cat /tmp/patch.txt
```

Step 3 - Submit (EXACT command, run SEPARATELY from previous steps):
```mswea_bash_command
echo COMPLETE_TASK_AND_SUBMIT_FINAL_OUTPUT && cat /tmp/patch.txt
```
</instructions>"""


# ─────────────────────────────────────────────────────────────────────────────
# 单实例生成 patch（本地运行）
# ─────────────────────────────────────────────────────────────────────────────

def generate_patch_for_instance(
    instance: dict,
    *,
    model_name: str,
    api_base: str,
    api_key: str = "EMPTY",
    method: str = DEFAULT_METHOD,
    step_limit: int = 80,
    bash_timeout: int = 60,
    cost_limit: float = 0.0,
    overwrite: bool = False,
    # 以下参数为向后兼容占位（不实际使用）
    image_version: str = "1.0.0",
    task_timeout: int = 3600,
    wait: bool = True,
    config_specs: list | None = None,
    timeout: int | None = None,
) -> dict:
    """
    本地直接运行 mini-swe-agent 生成 patch。

    返回:
        {"instance_id", "success", "patch", "exit_status", "cost",
         "patch_file", "traj_file"}
    """
    instance_id = instance["instance_id"]

    patch_dir  = PROJECT_ROOT / "patches" / method
    patch_file = patch_dir / f"{instance_id}.diff"

    if patch_file.exists() and not overwrite:
        logger.info("[%s] patch 已存在，跳过", instance_id)
        return {
            "instance_id": instance_id,
            "success": True,
            "patch": patch_file.read_text(),
            "exit_status": "Cached",
            "cost": 0.0,
            "patch_file": str(patch_file),
            "traj_file": None,
        }

    # ── 设置 API 环境变量 ────────────────────────────────────────────────────
    os.environ["OPENAI_API_KEY"]      = api_key
    os.environ["OPENAI_API_BASE"]     = api_base
    os.environ["MSWEA_SILENT_STARTUP"] = "1"
    os.environ["MSWEA_COST_TRACKING"]  = "ignore_errors"

    # ── 导入 mini-swe-agent ──────────────────────────────────────────────────
    try:
        from minisweagent.agents.default import DefaultAgent
        from minisweagent.environments.local import LocalEnvironment
        from minisweagent.models.litellm_textbased_model import LitellmTextbasedModel
    except ImportError as e:
        logger.error("无法导入 mini-swe-agent: %s", e)
        logger.error("请确认已运行: git submodule update --init --recursive && pip install -e mini-swe-agent/")
        return {"instance_id": instance_id, "success": False, "patch": "",
                "exit_status": f"ImportError: {e}", "cost": 0.0,
                "patch_file": None, "traj_file": None}

    # ── 轨迹输出路径 ─────────────────────────────────────────────────────────
    traj_dir  = PROJECT_ROOT / "logs" / f"{method}_patch"
    traj_dir.mkdir(parents=True, exist_ok=True)
    traj_file = traj_dir / f"{instance_id}.traj.json"

    # ── 构建 agent ───────────────────────────────────────────────────────────
    model = LitellmTextbasedModel(
        model_name=model_name,
        model_kwargs={"temperature": 0.0, "drop_params": True},
        cost_tracking="ignore_errors",
    )

    effective_timeout = timeout if timeout is not None else bash_timeout
    env = LocalEnvironment(
        cwd="/testbed",
        timeout=effective_timeout,
        env={
            "PAGER": "cat", "MANPAGER": "cat", "LESS": "-R",
            "PIP_PROGRESS_BAR": "off", "TQDM_DISABLE": "1",
        },
    )

    agent = DefaultAgent(
        model, env,
        system_template=SYSTEM_TEMPLATE,
        instance_template=INSTANCE_TEMPLATE,
        step_limit=step_limit,
        cost_limit=cost_limit,
        output_path=traj_file,
    )

    logger.info("[%s] 开始运行 agent (model=%s, step_limit=%d)", instance_id, model_name, step_limit)
    t0 = time.time()

    try:
        info = agent.run(instance["problem_statement"])
    except Exception as e:
        logger.error("[%s] agent 运行异常: %s", instance_id, e)
        return {"instance_id": instance_id, "success": False, "patch": "",
                "exit_status": f"AgentError: {e}", "cost": 0.0,
                "patch_file": None, "traj_file": str(traj_file)}

    elapsed      = time.time() - t0
    exit_status  = info.get("exit_status", "Unknown")
    patch_content = info.get("submission", "") or ""
    cost          = getattr(agent, "cost", 0.0)

    logger.info("[%s] agent 完成 exit=%s cost=%.4f steps=%d time=%.0fs",
                instance_id, exit_status, cost, getattr(agent, "n_calls", 0), elapsed)

    if patch_content.strip():
        patch_dir.mkdir(parents=True, exist_ok=True)
        patch_file.write_text(patch_content)
        logger.info("[%s] ✅ patch 已保存 → %s", instance_id, patch_file)
        return {
            "instance_id": instance_id,
            "success": True,
            "patch": patch_content,
            "exit_status": exit_status,
            "cost": cost,
            "patch_file": str(patch_file),
            "traj_file": str(traj_file),
        }
    else:
        logger.warning("[%s] ❌ 未获得有效 patch (exit=%s)", instance_id, exit_status)
        return {
            "instance_id": instance_id,
            "success": False,
            "patch": "",
            "exit_status": exit_status,
            "cost": cost,
            "patch_file": None,
            "traj_file": str(traj_file),
        }


# ─────────────────────────────────────────────────────────────────────────────
# 批量
# ─────────────────────────────────────────────────────────────────────────────

def generate_patches_batch(
    instances: list[dict],
    *,
    model_name: str,
    api_base: str,
    api_key: str,
    method: str,
    step_limit: int,
    bash_timeout: int,
    cost_limit: float,
    workers: int,
    overwrite: bool,
    results_file: Path,
    **kwargs,
) -> list[dict]:
    all_results: list[dict] = []
    lock = threading.Lock()

    def _process(inst):
        result = generate_patch_for_instance(
            inst,
            model_name=model_name, api_base=api_base, api_key=api_key,
            method=method, step_limit=step_limit, bash_timeout=bash_timeout,
            cost_limit=cost_limit, overwrite=overwrite,
        )
        with lock:
            all_results.append(result)
            results_file.parent.mkdir(parents=True, exist_ok=True)
            results_file.write_text(json.dumps(all_results, indent=2, ensure_ascii=False))
        return result

    with concurrent.futures.ThreadPoolExecutor(max_workers=workers) as executor:
        futures = {executor.submit(_process, inst): inst["instance_id"] for inst in instances}
        done = 0
        for fut in concurrent.futures.as_completed(futures):
            iid = futures[fut]
            done += 1
            try:
                res = fut.result()
                icon = "✅" if res["success"] else "❌"
                logger.info("[%d/%d] %s %s  exit=%s  cost=%.4f",
                            done, len(instances), icon, iid,
                            res["exit_status"], res.get("cost", 0.0))
            except Exception as exc:
                logger.error("[%d/%d] ❌ %s: %s", done, len(instances), iid, exc)

    return all_results


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser():
    p = argparse.ArgumentParser(
        description="本地用 mini-swe-agent 生成 SWE-bench patch",
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
    rg.add_argument("--step-limit",   type=int,   default=80)
    rg.add_argument("--bash-timeout", type=int,   default=60,
                    help="bash 命令超时（秒）")
    rg.add_argument("--cost-limit",   type=float, default=0.0,
                    help="cost 上限（0 表示不限制，适用于本地/自建模型）")
    rg.add_argument("--workers", "-w", type=int, default=1)

    og = p.add_argument_group("输出")
    og.add_argument("--method",    default=DEFAULT_METHOD)
    og.add_argument("--overwrite", action="store_true")
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
        model_name=args.model, api_base=args.api_base, api_key=args.api_key,
        method=args.method, step_limit=args.step_limit,
        bash_timeout=args.bash_timeout, cost_limit=args.cost_limit,
        overwrite=args.overwrite,
    )

    if args.instance:
        if args.instance not in instance_map:
            logger.error("实例 '%s' 不在数据集中", args.instance)
            sys.exit(1)
        result = generate_patch_for_instance(instance_map[args.instance], **common)
        print("\n" + "=" * 60)
        print(f"实例:        {result['instance_id']}")
        print(f"成功:        {'✅' if result['success'] else '❌'}")
        print(f"exit_status: {result['exit_status']}")
        print(f"cost:        ${result.get('cost', 0):.4f}")
        if result.get("patch_file"):
            print(f"patch 文件:  {result['patch_file']}")
        if result.get("traj_file"):
            print(f"轨迹文件:    {result['traj_file']}")
        print("=" * 60)
        sys.exit(0 if result["success"] else 1)

    # 批量
    instances = all_instances
    if args.filter:
        instances = [i for i in instances if re.match(args.filter, i["instance_id"])]
    if args.slice:
        parts = [int(x) if x else None for x in args.slice.split(":")]
        instances = instances[slice(*parts)]
    logger.info("待处理 %d 个实例，并发=%d", len(instances), args.workers)

    results_file = Path(args.results_file) if args.results_file else (
        PROJECT_ROOT / "logs" / f"{args.method}_patch" / "generate_results.json"
    )
    results = generate_patches_batch(
        instances, workers=args.workers, results_file=results_file, **common
    )

    succeeded  = sum(1 for r in results if r["success"])
    total_cost = sum(r.get("cost", 0.0) for r in results)
    print(f"\n批量完成: {succeeded}/{len(results)} 成功  总 cost=${total_cost:.4f}  结果: {results_file}")


if __name__ == "__main__":
    main()
