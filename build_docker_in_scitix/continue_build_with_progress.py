#!/usr/bin/env python3
"""Continue SWE-bench image building on SciTix with progress tracking.

Rules:
- Build/check env first
- Then build instances in batches
- Total newly submitted instances in this run <= 24
- Write progress to build_docker_in_scitix/build_progress.md
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
WORK = Path(__file__).resolve().parent
BUILD_DIR = ROOT / "build"
VENDOR_DIR = ROOT / ".vendor_siflow"
PROGRESS_FILE = WORK / "build_progress.md"

sys.path.insert(0, str(VENDOR_DIR))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BUILD_DIR))

from siflow import SiFlow  # type: ignore

import siflow_config
import siflow_utils
import build_layer2_env
import build_layer3_instance
from siflow_utils import sanitize_image_name


def now() -> str:
    return datetime.now(timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def log(msg: str) -> None:
    line = f"[{now()}] {msg}"
    print(line)
    with open(PROGRESS_FILE, "a", encoding="utf-8") as f:
        f.write(line + "\n")


def must_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def create_client() -> SiFlow:
    return SiFlow(
        region="ap-southeast",
        cluster="aries",
        access_key_id=must_env("SIFLOW_ACCESS_KEY_ID"),
        access_key_secret=must_env("SIFLOW_ACCESS_KEY_SECRET"),
    )


def patch_client(client: SiFlow) -> SiFlow:
    orig_create = client.images.create

    def wrapped(*args: Any, **kwargs: Any):
        kwargs["image_build_region"] = "ap-southeast"
        kwargs["image_build_cluster"] = "aries"
        kwargs["major_category"] = "swebench"
        kwargs["resource_pool"] = os.getenv("SIFLOW_RESOURCE_POOL", kwargs.get("resource_pool", ""))
        return orig_create(*args, **kwargs)

    client.images.create = wrapped  # type: ignore[attr-defined]
    return client


def create_client_patched() -> SiFlow:
    return patch_client(create_client())


def patch_modules() -> None:
    siflow_utils.create_siflow_client = create_client_patched
    build_layer2_env.create_siflow_client = create_client_patched
    build_layer3_instance.create_siflow_client = create_client_patched

    siflow_config.REGION = "ap-southeast"
    siflow_config.CLUSTER = "aries"
    siflow_config.RESOURCE_POOL = os.getenv("SIFLOW_RESOURCE_POOL", "ap-southeast-aries-hisys-ondemand-shared")
    siflow_config.IMAGE_CATEGORY_MAJOR = "swebench"
    siflow_config.INSTANCE_TYPE = os.getenv("SIFLOW_INSTANCE_TYPE", "sci.g20-3")

    build_layer2_env.RESOURCE_POOL = siflow_config.RESOURCE_POOL
    build_layer3_instance.RESOURCE_POOL = siflow_config.RESOURCE_POOL
    build_layer2_env.INSTANCE_TYPE = siflow_config.INSTANCE_TYPE
    build_layer3_instance.INSTANCE_TYPE = siflow_config.INSTANCE_TYPE
    build_layer2_env.IMAGE_CATEGORY_MAJOR = "swebench"
    build_layer3_instance.IMAGE_CATEGORY_MAJOR = "swebench"


def pick_group_and_instances(preferred_repo: str | None, max_new: int) -> tuple[dict[str, Any], list[dict[str, str]]]:
    from datasets import load_dataset

    ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    rows = [{"instance_id": x["instance_id"], "repo": x["repo"], "version": x["version"]} for x in ds]
    if preferred_repo:
        rows = [r for r in rows if r["repo"] == preferred_repo]

    groups = Counter((r["repo"], r["version"]) for r in rows)
    (repo, version), total = groups.most_common(1)[0]
    group = [r for r in rows if r["repo"] == repo and r["version"] == version]

    client = create_client()
    images = getattr(client.images.list(keyword="swebench-instance", pageSize=1000), "rows", []) or []
    built_names = {
        getattr(x, "name", "")
        for x in images
        if getattr(x, "version", "") == "1.0.0"
    }

    remain = []
    for r in group:
        name = sanitize_image_name(f"swebench-instance-{r['instance_id']}")
        if name not in built_names:
            remain.append(r)

    selected = remain[:max_new]
    info = {
        "repo": repo,
        "version": version,
        "group_total": total,
        "already_built": total - len(remain),
        "remaining": len(remain),
        "selected_now": len(selected),
    }
    return info, selected


def ensure_env(instance_id: str, env_version: str, base_version: str) -> dict[str, Any]:
    return build_layer2_env.build_env_image(
        instance_id=instance_id,
        image_version=env_version,
        base_image_name="swebench-base",
        base_image_version=base_version,
        wait=False,
    )


def submit_instances(batch: list[dict[str, str]], image_version: str, env_version: str, delay: int) -> dict[str, Any]:
    ok = 0
    fail = 0
    details: list[dict[str, Any]] = []
    for i, item in enumerate(batch, 1):
        iid = item["instance_id"]
        log(f"submit instance {i}/{len(batch)}: {iid}")
        r = build_layer3_instance.build_instance_image(
            instance_id=iid,
            image_version=image_version,
            env_image_version=env_version,
            wait=False,
            verbose=False,
        )
        details.append({"instance_id": iid, **r})
        if r.get("success"):
            ok += 1
        else:
            fail += 1
        if i < len(batch) and delay > 0:
            time.sleep(delay)
    return {"submitted": ok, "failed": fail, "details": details}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("--image-version", default="1.0.0")
    parser.add_argument("--env-version", default="1.0.0")
    parser.add_argument("--max-new", type=int, default=24, help="upper bound of new instance submissions in this run")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--delay", type=int, default=1)
    parser.add_argument("--preferred-repo", default="django/django")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    os.environ["SIFLOW_REGION"] = "ap-southeast"
    os.environ["SIFLOW_CLUSTER"] = "aries"
    os.environ.setdefault("SIFLOW_RESOURCE_POOL", "ap-southeast-aries-hisys-ondemand-shared")
    os.environ.setdefault("SIFLOW_INSTANCE_TYPE", "sci.g20-3")

    must_env("SIFLOW_ACCESS_KEY_ID")
    must_env("SIFLOW_ACCESS_KEY_SECRET")

    patch_modules()

    log("=== continue build run start ===")
    log(f"config: image_version={args.image_version}, env_version={args.env_version}, max_new={args.max_new}, batch_size={args.batch_size}")

    info, selected = pick_group_and_instances(args.preferred_repo, min(args.max_new, 24))
    log(f"group: {json.dumps(info, ensure_ascii=False)}")

    if not selected:
        log("no remaining instances to build; stop")
        log("=== continue build run end ===")
        return 0

    env_res = ensure_env(selected[0]["instance_id"], args.env_version, args.image_version)
    log(f"env submit result: success={env_res.get('success')}, status={env_res.get('status')}, error={env_res.get('error')}")

    if not env_res.get("success"):
        log("env submit failed; stop")
        log("=== continue build run end ===")
        return 1

    total = 0
    all_details: list[dict[str, Any]] = []
    for start in range(0, len(selected), args.batch_size):
        sub = selected[start:start + args.batch_size]
        log(f"batch start: {start+1}-{start+len(sub)} / {len(selected)}")
        r = submit_instances(sub, args.image_version, args.env_version, args.delay)
        total += r["submitted"]
        all_details.extend(r["details"])
        log(f"batch done: submitted={r['submitted']}, failed={r['failed']}")

    out = {
        "ts": now(),
        "group": info,
        "max_new": args.max_new,
        "selected": len(selected),
        "submitted": total,
        "details": all_details,
    }
    out_file = WORK / "build_progress_last_run.json"
    out_file.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    log(f"run summary written: {out_file}")
    log("=== continue build run end ===")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
