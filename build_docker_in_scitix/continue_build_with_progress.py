#!/usr/bin/env python3
"""Continue SWE-bench image build with progress tracking and env-ready gating.

Rules:
- Explicit platform profile: aries/cetus
- Ensure env image exists and is READY before instance submissions
- Instance submissions in this run <= 24
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
sys.path.insert(0, str(WORK))

from siflow import SiFlow  # type: ignore

import siflow_config
import siflow_utils
import build_layer2_env
import build_layer3_instance
from siflow_utils import sanitize_image_name, get_image_registry_url
from platform_profiles import get_platform_profile, PlatformProfile


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


def apply_env(profile: PlatformProfile) -> None:
    os.environ["SIFLOW_REGION"] = profile.region
    os.environ["SIFLOW_CLUSTER"] = profile.cluster
    os.environ["SIFLOW_RESOURCE_POOL"] = profile.resource_pool
    os.environ["SIFLOW_INSTANCE_TYPE"] = profile.instance_type


def create_client(profile: PlatformProfile) -> SiFlow:
    return SiFlow(
        region=profile.region,
        cluster=profile.cluster,
        access_key_id=must_env("SIFLOW_ACCESS_KEY_ID"),
        access_key_secret=must_env("SIFLOW_ACCESS_KEY_SECRET"),
    )


def patch_client(client: SiFlow, profile: PlatformProfile) -> SiFlow:
    orig_create = client.images.create

    def wrapped(*args: Any, **kwargs: Any):
        kwargs["image_build_region"] = profile.region
        kwargs["image_build_cluster"] = profile.cluster
        kwargs["major_category"] = "swebench"
        kwargs["resource_pool"] = profile.resource_pool
        return orig_create(*args, **kwargs)

    client.images.create = wrapped  # type: ignore[attr-defined]
    return client


def create_client_patched(profile: PlatformProfile) -> SiFlow:
    return patch_client(create_client(profile), profile)


def patch_modules(profile: PlatformProfile) -> None:
    def _client_factory() -> SiFlow:
        return create_client_patched(profile)

    siflow_utils.create_siflow_client = _client_factory
    build_layer2_env.create_siflow_client = _client_factory
    build_layer3_instance.create_siflow_client = _client_factory

    siflow_config.REGION = profile.region
    siflow_config.CLUSTER = profile.cluster
    siflow_config.RESOURCE_POOL = profile.resource_pool
    siflow_config.IMAGE_CATEGORY_MAJOR = "swebench"
    siflow_config.INSTANCE_TYPE = profile.instance_type

    build_layer2_env.RESOURCE_POOL = profile.resource_pool
    build_layer3_instance.RESOURCE_POOL = profile.resource_pool
    build_layer2_env.INSTANCE_TYPE = profile.instance_type
    build_layer3_instance.INSTANCE_TYPE = profile.instance_type
    build_layer2_env.IMAGE_CATEGORY_MAJOR = "swebench"
    build_layer3_instance.IMAGE_CATEGORY_MAJOR = "swebench"


def env_image_name(repo: str, version: str) -> str:
    return sanitize_image_name(f"swebench-env-{repo.replace('/', '-')}-{version}")


def get_env_state(client: SiFlow, name: str, version: str) -> dict[str, Any]:
    rows = getattr(client.images.list(keyword=name, pageSize=100), "rows", []) or []
    for r in rows:
        if getattr(r, "name", "") == name and getattr(r, "version", "") == version:
            return {
                "id": getattr(r, "id", None),
                "status": str(getattr(r, "status", None)),
                "step_status": str(getattr(r, "step_status", None)),
                "registry_url": get_image_registry_url(client, name, version),
            }
    return {"id": None, "status": "missing", "step_status": None, "registry_url": None}


def wait_env_ready(client: SiFlow, name: str, version: str, timeout_sec: int, poll_sec: int) -> bool:
    start = time.time()
    while time.time() - start < timeout_sec:
        st = get_env_state(client, name, version)
        if st.get("registry_url"):
            log(f"env ready: {name}:{version} id={st.get('id')}")
            return True
        log(
            f"env pending: {name}:{version} id={st.get('id')} "
            f"status={st.get('status')} step={st.get('step_status')}"
        )
        time.sleep(max(1, poll_sec))
    return False


def pick_group_and_instances(profile: PlatformProfile, image_version: str, preferred_repo: str | None, max_new: int) -> tuple[dict[str, Any], list[dict[str, str]]]:
    from datasets import load_dataset

    ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    rows = [{"instance_id": x["instance_id"], "repo": x["repo"], "version": x["version"]} for x in ds]
    if preferred_repo:
        rows = [r for r in rows if r["repo"] == preferred_repo]

    groups = Counter((r["repo"], r["version"]) for r in rows)
    (repo, version), total = groups.most_common(1)[0]
    group = [r for r in rows if r["repo"] == repo and r["version"] == version]

    client = create_client(profile)
    images = getattr(client.images.list(keyword="swebench-instance", pageSize=2000), "rows", []) or []
    built_names = {
        getattr(x, "name", "")
        for x in images
        if getattr(x, "version", "") == image_version and bool(get_image_registry_url(client, getattr(x, "name", ""), image_version))
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


def ensure_env(instance_id: str, env_version: str, base_version: str, commit_id: str = "v1") -> dict[str, Any]:
    return build_layer2_env.build_env_image(
        instance_id=instance_id,
        image_version=env_version,
        base_image_name="swebench-base",
        base_image_version=base_version,
        wait=False,
        commit_id=commit_id,
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
    parser.add_argument("--platform", choices=["aries", "cetus"], default="aries")
    parser.add_argument("--image-version", default="1.0.0")
    parser.add_argument("--env-version", default="1.0.0")
    parser.add_argument("--max-new", type=int, default=24, help="upper bound of new instance submissions in this run")
    parser.add_argument("--batch-size", type=int, default=8)
    parser.add_argument("--delay", type=int, default=1)
    parser.add_argument("--preferred-repo", default="django/django")
    parser.add_argument("--env-ready-timeout", type=int, default=3600)
    parser.add_argument("--env-ready-poll", type=int, default=30)
    parser.add_argument("--retry-env-submit", type=int, default=1, help="resubmit env if timeout reached")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    profile = get_platform_profile(args.platform)
    apply_env(profile)

    must_env("SIFLOW_ACCESS_KEY_ID")
    must_env("SIFLOW_ACCESS_KEY_SECRET")

    patch_modules(profile)

    log("=== continue build run start ===")
    log(
        "config: "
        f"platform={profile.name}, region={profile.region}, cluster={profile.cluster}, "
        f"resource_pool={profile.resource_pool}, image_version={args.image_version}, env_version={args.env_version}, "
        f"max_new={args.max_new}, batch_size={args.batch_size}"
    )

    info, selected = pick_group_and_instances(profile, args.image_version, args.preferred_repo, min(args.max_new, 24))
    log(f"group: {json.dumps(info, ensure_ascii=False)}")

    if not selected:
        log("no remaining instances to build; stop")
        log("=== continue build run end ===")
        return 0

    target_repo = selected[0]["repo"]
    target_ver = selected[0]["version"]
    env_name = env_image_name(target_repo, target_ver)

    env_res = ensure_env(selected[0]["instance_id"], args.env_version, args.image_version, commit_id="v1")
    log(f"env submit result: success={env_res.get('success')}, status={env_res.get('status')}, error={env_res.get('error')}")

    client = create_client(profile)
    ready = wait_env_ready(client, env_name, args.env_version, args.env_ready_timeout, args.env_ready_poll)

    retry = 0
    while (not ready) and retry < max(0, args.retry_env_submit):
        retry += 1
        commit_id = f"retry-{int(time.time())}"
        log(f"env not ready after timeout, resubmit env retry={retry} commit_id={commit_id}")
        retry_res = ensure_env(selected[0]["instance_id"], args.env_version, args.image_version, commit_id=commit_id)
        log(
            f"env retry submit result: success={retry_res.get('success')}, "
            f"status={retry_res.get('status')}, error={retry_res.get('error')}"
        )
        ready = wait_env_ready(client, env_name, args.env_version, args.env_ready_timeout, args.env_ready_poll)

    if not ready:
        log("env still not ready, stop before instance submissions")
        log("=== continue build run end ===")
        return 1

    total = 0
    total_fail = 0
    all_details: list[dict[str, Any]] = []
    for start in range(0, len(selected), args.batch_size):
        sub = selected[start:start + args.batch_size]
        log(f"batch start: {start+1}-{start+len(sub)} / {len(selected)}")
        r = submit_instances(sub, args.image_version, args.env_version, args.delay)
        total += r["submitted"]
        total_fail += r["failed"]
        all_details.extend(r["details"])
        log(f"batch done: submitted={r['submitted']}, failed={r['failed']}")

    out = {
        "ts": now(),
        "platform": {
            "name": profile.name,
            "region": profile.region,
            "cluster": profile.cluster,
            "resource_pool": profile.resource_pool,
        },
        "group": info,
        "max_new": args.max_new,
        "selected": len(selected),
        "submitted": total,
        "failed": total_fail,
        "details": all_details,
    }
    out_file = WORK / "build_progress_last_run.json"
    out_file.write_text(json.dumps(out, indent=2, ensure_ascii=False) + "\n")
    log(f"run summary written: {out_file}")
    log("=== continue build run end ===")
    return 0 if total_fail == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
