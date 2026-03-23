#!/usr/bin/env python3
"""
快速测试：用 Qwen3-30B-A3B（hermes tool-call）对 django__django-11099 生成 patch
运行前确保 /testbed 下已有 django__django-11099 的代码（即在对应 instance 容器中）。
也可以在宿主机直接运行，会对宿主 shell 执行命令（LocalEnvironment）。

用法：
  python patch_gen/test_qwen3_run.py
"""

import os
import sys
from pathlib import Path

# ── 路径 ─────────────────────────────────────────────────────────────────────
PROJECT_ROOT = Path(__file__).resolve().parent.parent
MINI_SRC = PROJECT_ROOT / "mini-swe-agent" / "src"
if str(MINI_SRC) not in sys.path:
    sys.path.insert(0, str(MINI_SRC))

# ── 设置 API ──────────────────────────────────────────────────────────────────
os.environ.setdefault("OPENAI_API_KEY", "EMPTY")
os.environ["OPENAI_API_BASE"] = (
    "https://scitix-aries.scitix.ai/siflow/aries/hisys/rhjiang/qwen3-30b-a3b-mcore/v1"
)
# 关闭 litellm cost tracking 的错误（本地模型无 price 信息）
os.environ["MSWEA_COST_TRACKING"] = "ignore_errors"
os.environ["MSWEA_SILENT_STARTUP"] = "1"

# ── mini-swe-agent imports ────────────────────────────────────────────────────
from minisweagent.agents.default import DefaultAgent
from minisweagent.environments.local import LocalEnvironment
from minisweagent.models.litellm_textbased_model import LitellmTextbasedModel
from minisweagent.config import builtin_config_dir, get_config_from_spec
from minisweagent.utils.serialize import recursive_merge

# ── SWE-bench 数据集 ──────────────────────────────────────────────────────────
from datasets import load_dataset

INSTANCE_ID = "django__django-11099"
METHOD      = "qwen3_30b"
MODEL_NAME  = "openai/Qwen/Qwen3-30B-A3B-mcore"

def main():
    print(f"=== 加载实例 {INSTANCE_ID} ===")
    ds = load_dataset("princeton-nlp/SWE-Bench_Verified", split="test")
    instance = next(i for i in ds if i["instance_id"] == INSTANCE_ID)
    print(f"  repo:    {instance['repo']}")
    print(f"  problem: {instance['problem_statement'][:200]}...\n")

    # ── 配置 ──────────────────────────────────────────────────────────────────
    config_file = str(builtin_config_dir / "benchmarks" / "swebench.yaml")
    configs = [get_config_from_spec(config_file)]
    configs.append({
        "agent": {
            "cost_limit": 0.0,   # 0 = 不限制（本地模型 cost=0）
            "step_limit": 50,    # 测试先设小一点
        },
        "environment": {
            "cwd": "/testbed",
            "timeout": 60,
            "env": {
                "PAGER": "cat",
                "MANPAGER": "cat",
                "LESS": "-R",
                "PIP_PROGRESS_BAR": "off",
                "TQDM_DISABLE": "1",
            },
        },
    })
    config = recursive_merge(*configs)

    # ── 环境 ──────────────────────────────────────────────────────────────────
    env_cfg = config.get("environment", {})
    env = LocalEnvironment(
        cwd=env_cfg.get("cwd", "/testbed"),
        timeout=env_cfg.get("timeout", 60),
        env=env_cfg.get("env", {}),
    )

    # ── 使用 text-based 模型（backticks 格式，不依赖 tool_call 协议） ──────────
    # swebench_backticks.yaml 里的 system/instance/observation/format_error template
    backticks_config_file = str(builtin_config_dir / "benchmarks" / "swebench_backticks.yaml")
    backticks_cfg = get_config_from_spec(backticks_config_file)
    model = LitellmTextbasedModel(
        model_name=MODEL_NAME,
        model_kwargs={
            "temperature": 0.0,
            "drop_params": True,
        },
        cost_tracking="ignore_errors",
        observation_template=backticks_cfg.get("model", {}).get("observation_template", ""),
        format_error_template=backticks_cfg.get("model", {}).get("format_error_template", ""),
    )

    # ── 轨迹 & patch 输出路径 ─────────────────────────────────────────────────
    traj_dir  = PROJECT_ROOT / "logs" / f"{METHOD}_patch"
    traj_dir.mkdir(parents=True, exist_ok=True)
    traj_file = traj_dir / f"{INSTANCE_ID}.traj.json"

    patch_dir  = PROJECT_ROOT / "patches" / METHOD
    patch_dir.mkdir(parents=True, exist_ok=True)
    patch_file = patch_dir / f"{INSTANCE_ID}.diff"

    # ── 使用 backticks 配置里的 agent system/instance template ──────────────
    agent_kwargs = {
        "system_template": backticks_cfg.get("agent", {}).get("system_template", ""),
        "instance_template": backticks_cfg.get("agent", {}).get("instance_template", ""),
        "cost_limit": 0.0,
        "step_limit": 50,
        "output_path": traj_file,
    }
    agent = DefaultAgent(model, env, **agent_kwargs)

    print(f"=== 开始运行 Agent（model={MODEL_NAME}）===")
    info = agent.run(instance["problem_statement"])

    exit_status   = info.get("exit_status", "Unknown")
    patch_content = info.get("submission", "") or ""
    cost          = agent.cost

    print(f"\n=== 结果 ===")
    print(f"  exit_status : {exit_status}")
    print(f"  cost        : ${cost:.4f}")
    print(f"  steps       : {agent.n_calls}")
    print(f"  轨迹文件    : {traj_file}")

    if patch_content.strip():
        patch_file.write_text(patch_content)
        print(f"  ✅ patch 已保存 → {patch_file}")
        print(f"\n--- patch 内容 ---")
        print(patch_content[:2000])
        if len(patch_content) > 2000:
            print(f"  ...（共 {len(patch_content)} 字符）")
    else:
        print("  ❌ 未获得有效 patch")


if __name__ == "__main__":
    main()
