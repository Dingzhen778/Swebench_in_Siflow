#!/usr/bin/env python3
"""
端到端脚本：先用 mini-swe-agent 本地生成 patch，再用 SiFlow 评测。

用法:
  单个实例:
    python patch_gen/run_and_eval.py --instance django__django-13670 --model openai/gpt-4o

  批量:
    python patch_gen/run_and_eval.py --batch --model openai/gpt-4o --workers 4

  指定方法名（patch 保存到 patches/{method}/，eval 日志写 logs/{method}_patch/）:
    python patch_gen/run_and_eval.py --instance django__django-13670 \\
        --model openai/gpt-4o --method my_model

  跳过生成、只 eval（patch 已在 patches/{method}/ 下）:
    python patch_gen/run_and_eval.py --instance django__django-13670 \\
        --model openai/gpt-4o --eval-only
"""

from __future__ import annotations

import argparse
import json
import logging
import re
import sys
import time
from pathlib import Path

# ── 项目路径 ──────────────────────────────────────────────────────────────────
SCRIPT_DIR   = Path(__file__).resolve().parent
PROJECT_ROOT = SCRIPT_DIR.parent
MINI_SRC     = PROJECT_ROOT / "mini-swe-agent" / "src"
if str(MINI_SRC) not in sys.path:
    sys.path.insert(0, str(MINI_SRC))
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "eval"))

from datasets import load_dataset

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
    datefmt="%H:%M:%S",
)
logger = logging.getLogger("run_and_eval")

DATASET_MAPPING = {
    "full":     "princeton-nlp/SWE-Bench",
    "verified": "princeton-nlp/SWE-Bench_Verified",
    "lite":     "princeton-nlp/SWE-Bench_Lite",
}
DEFAULT_SUBSET = "verified"
DEFAULT_SPLIT  = "test"
DEFAULT_METHOD = "mini_swe_agent"


# ─────────────────────────────────────────────────────────────────────────────
# 单实例端到端
# ─────────────────────────────────────────────────────────────────────────────

def run_and_eval_instance(
    instance: dict,
    *,
    model_name: str,
    method: str,
    config_specs: list[str] | None = None,  # 保留兼容性，暂不使用
    cost_limit: float,
    step_limit: int,
    bash_timeout: int,
    eval_timeout: int,
    overwrite: bool,
    eval_only: bool,
) -> dict:
    """
    1. 生成 patch（除非 --eval-only）
    2. 调用 eval 流水线
    返回合并的结果字典。
    """
    instance_id = instance["instance_id"]

    # ── Step 1: 生成 patch ────────────────────────────────────────────────────
    gen_result: dict = {"instance_id": instance_id, "success": False,
                        "patch": "", "exit_status": "Skipped", "cost": 0.0,
                        "patch_file": None, "traj_file": None}

    if not eval_only:
        from patch_gen.generate_patch import generate_patch_for_instance
        gen_result = generate_patch_for_instance(
            instance,
            model_name=model_name,
            method=method,
            cost_limit=cost_limit,
            step_limit=step_limit,
            bash_timeout=bash_timeout,
            overwrite=overwrite,
        )
        if not gen_result["success"]:
            logger.warning("[%s] patch 生成失败，跳过 eval", instance_id)
            return {**gen_result, "eval_result": None}
    else:
        # eval-only: 检查 patch 文件是否存在
        patch_file = PROJECT_ROOT / "patches" / method / f"{instance_id}.diff"
        if not patch_file.exists():
            logger.error("[%s] --eval-only 但 patch 文件不存在: %s", instance_id, patch_file)
            return {**gen_result, "eval_result": None}
        gen_result["patch_file"] = str(patch_file)
        gen_result["success"] = True

    # ── Step 2: Eval ──────────────────────────────────────────────────────────
    try:
        from run_gold_eval_fixed import run_gold_eval_for_instance
        eval_result = run_gold_eval_for_instance(
            instance_id=instance_id,
            image_version=None,
            timeout=eval_timeout,
            wait=True,
            patch_type="custom",
            method_name=method,
        )
    except Exception as e:
        logger.error("[%s] eval 失败: %s", instance_id, e, exc_info=True)
        eval_result = {"success": False, "error": str(e)}

    return {**gen_result, "eval_result": eval_result}


# ─────────────────────────────────────────────────────────────────────────────
# 批量
# ─────────────────────────────────────────────────────────────────────────────

def run_and_eval_batch(
    instances: list[dict],
    *,
    model_name: str,
    method: str,
    config_specs: list[str] | None = None,  # 保留兼容性
    cost_limit: float,
    step_limit: int,
    bash_timeout: int,
    eval_timeout: int,
    workers: int,
    overwrite: bool,
    eval_only: bool,
    results_file: Path,
) -> list[dict]:
    import concurrent.futures, threading

    all_results: list[dict] = []
    lock = threading.Lock()

    def _process(inst):
        result = run_and_eval_instance(
            inst,
            model_name=model_name,
            method=method,
            config_specs=config_specs,
            cost_limit=cost_limit,
            step_limit=step_limit,
            bash_timeout=bash_timeout,
            eval_timeout=eval_timeout,
            overwrite=overwrite,
            eval_only=eval_only,
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
                eval_res = res.get("eval_result") or {}
                resolved = eval_res.get("resolved") or eval_res.get("resolution_status", "")
                gen_ok = "✅" if res["success"] else "❌"
                logger.info("[%d/%d] %s %s | eval: %s | cost=$%.4f",
                            done, len(instances), gen_ok, iid,
                            resolved or eval_res.get("error", "N/A"),
                            res.get("cost", 0.0))
            except Exception as exc:
                logger.error("[%d/%d] ❌ %s exception: %s", done, len(instances), iid, exc)

    return all_results


# ─────────────────────────────────────────────────────────────────────────────
# CLI
# ─────────────────────────────────────────────────────────────────────────────

def _build_parser():
    p = argparse.ArgumentParser(
        description="mini-swe-agent 生成 patch + SiFlow 评测 一键运行",
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
    mg.add_argument("--model", "-m", required=True,
                    help="LiteLLM 模型名，如 openai/gpt-4o")
    mg.add_argument("--config", "-c", action="append", dest="config_specs",
                    default=None, metavar="SPEC")

    rg = p.add_argument_group("运行参数")
    rg.add_argument("--cost-limit",   type=float, default=3.0)
    rg.add_argument("--step-limit",   type=int,   default=250)
    rg.add_argument("--bash-timeout", type=int,   default=60,
                    help="bash 命令超时（秒，默认 60）")
    rg.add_argument("--eval-timeout", type=int,   default=1800,
                    help="eval 任务超时（秒，默认 1800）")
    rg.add_argument("--workers", "-w", type=int,  default=1)

    og = p.add_argument_group("输出")
    og.add_argument("--method",    default=DEFAULT_METHOD,
                    help=f"方法名 (默认: {DEFAULT_METHOD})")
    og.add_argument("--overwrite", action="store_true")
    og.add_argument("--eval-only", action="store_true",
                    help="跳过生成，直接 eval（需要 patches/{method}/ 下已有 patch）")
    og.add_argument("--results-file", metavar="PATH", default="")

    return p


def main():
    parser = _build_parser()
    args = parser.parse_args()

    dataset_path = DATASET_MAPPING[args.subset]
    logger.info("加载数据集 %s (split=%s) ...", dataset_path, args.split)
    all_instances = list(load_dataset(dataset_path, split=args.split))
    instance_map  = {i["instance_id"]: i for i in all_instances}

    kwargs = dict(
        model_name=args.model,
        method=args.method,
        config_specs=args.config_specs,
        cost_limit=args.cost_limit,
        step_limit=args.step_limit,
        bash_timeout=args.bash_timeout,
        eval_timeout=args.eval_timeout,
        overwrite=args.overwrite,
        eval_only=args.eval_only,
    )

    # ── 单实例 ────────────────────────────────────────────────────────────────
    if args.instance:
        iid = args.instance
        if iid not in instance_map:
            logger.error("实例 '%s' 不在数据集中", iid)
            sys.exit(1)
        result = run_and_eval_instance(instance_map[iid], **kwargs)
        print("\n" + "=" * 60)
        print(f"实例:        {result['instance_id']}")
        print(f"patch 生成:  {'✅' if result['success'] else '❌'} ({result['exit_status']})")
        print(f"cost:        ${result['cost']:.4f}")
        er = result.get("eval_result") or {}
        if er:
            print(f"eval 成功:   {'✅' if er.get('success') else '❌'}")
            if er.get("resolved"):
                print("eval 结果:   ✅ RESOLVED_FULL")
            elif er.get("resolution_status"):
                print(f"eval 结果:   {er['resolution_status']}")
        print("=" * 60)
        sys.exit(0 if (result["success"] and er.get("success")) else 1)

    # ── 批量 ──────────────────────────────────────────────────────────────────
    instances = all_instances
    if args.filter:
        instances = [i for i in instances if re.match(args.filter, i["instance_id"])]
    if args.slice:
        parts = [int(x) if x else None for x in args.slice.split(":")]
        instances = instances[slice(*parts)]
    logger.info("待处理 %d 个实例，并发 %d", len(instances), args.workers)

    results_file = Path(args.results_file) if args.results_file else (
        PROJECT_ROOT / "logs" / f"{args.method}_patch" / "run_and_eval_results.json"
    )

    t0 = time.time()
    results = run_and_eval_batch(instances, workers=args.workers,
                                 results_file=results_file, **kwargs)
    elapsed = time.time() - t0

    gen_ok  = sum(1 for r in results if r["success"])
    eval_ok = sum(1 for r in results
                  if (r.get("eval_result") or {}).get("success"))
    resolved = sum(1 for r in results
                   if (r.get("eval_result") or {}).get("resolved"))
    total_cost = sum(r.get("cost", 0.0) for r in results)

    print("\n" + "=" * 60)
    print(f"批量完成  耗时 {elapsed:.1f}s")
    print(f"  总实例:     {len(results)}")
    print(f"  patch 生成: {gen_ok} ✅")
    print(f"  eval 提交:  {eval_ok} ✅")
    print(f"  RESOLVED:   {resolved}")
    print(f"  总 cost:    ${total_cost:.4f}")
    print(f"  结果文件:   {results_file}")
    print("=" * 60)


if __name__ == "__main__":
    main()
