#!/usr/bin/env python3
"""Build SWE-bench images on SciTix ap-southeast/aries.

- Logic location: build_docker_in_scitix/
- Target: class/category=swebench, version=1.0.0
- Scope: build base + env + 20~30 instance images (default 25)
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from collections import Counter
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT / "build"
VENDOR_DIR = ROOT / ".vendor_siflow"

sys.path.insert(0, str(VENDOR_DIR))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BUILD_DIR))

from siflow import SiFlow  # type: ignore

import siflow_config
import siflow_utils
import build_layer1_base
import build_layer2_env
import build_layer3_instance


def _must_getenv(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


def _normalize_pool() -> str:
    pool = os.getenv("SIFLOW_RESOURCE_POOL", "").strip()
    if not pool or "ap-southeast-aries" not in pool:
        pool = "ap-southeast-aries-hisys-ondemand-shared"
        os.environ["SIFLOW_RESOURCE_POOL"] = pool
    return pool


def _create_scitix_client() -> SiFlow:
    return SiFlow(
        region=os.getenv("SIFLOW_REGION", "ap-southeast"),
        cluster=os.getenv("SIFLOW_CLUSTER", "aries"),
        access_key_id=_must_getenv("SIFLOW_ACCESS_KEY_ID"),
        access_key_secret=_must_getenv("SIFLOW_ACCESS_KEY_SECRET"),
    )


def _patch_client(client: SiFlow) -> SiFlow:
    orig_create = client.images.create

    def _wrapped_create(*args: Any, **kwargs: Any):
        kwargs["image_build_region"] = "ap-southeast"
        kwargs["image_build_cluster"] = "aries"
        kwargs["major_category"] = "swebench"
        kwargs["resource_pool"] = os.getenv("SIFLOW_RESOURCE_POOL", kwargs.get("resource_pool", ""))

        if kwargs.get("name") == "swebench-base":
            ibc = kwargs.get("image_build_config")
            if ibc is not None and hasattr(ibc, "description"):
                ver = kwargs.get("version", "1.0.0")
                ibc.description = f"SWE-bench Base Image - Python with Miniconda3 (v{ver})"

        return orig_create(*args, **kwargs)

    client.images.create = _wrapped_create  # type: ignore[attr-defined]
    return client


def _create_scitix_client_patched() -> SiFlow:
    return _patch_client(_create_scitix_client())


def _patch_build_modules() -> None:
    siflow_utils.create_siflow_client = _create_scitix_client_patched
    build_layer1_base.create_siflow_client = _create_scitix_client_patched
    build_layer2_env.create_siflow_client = _create_scitix_client_patched
    build_layer3_instance.create_siflow_client = _create_scitix_client_patched

    siflow_config.REGION = "ap-southeast"
    siflow_config.CLUSTER = "aries"
    siflow_config.RESOURCE_POOL = os.getenv("SIFLOW_RESOURCE_POOL", siflow_config.RESOURCE_POOL)
    siflow_config.IMAGE_CATEGORY_MAJOR = "swebench"

    inst = os.getenv("SIFLOW_INSTANCE_TYPE", "sci.g20-3")
    siflow_config.INSTANCE_TYPE = inst

    build_layer1_base.RESOURCE_POOL = siflow_config.RESOURCE_POOL
    build_layer2_env.RESOURCE_POOL = siflow_config.RESOURCE_POOL
    build_layer3_instance.RESOURCE_POOL = siflow_config.RESOURCE_POOL
    build_layer1_base.INSTANCE_TYPE = inst
    build_layer2_env.INSTANCE_TYPE = inst
    build_layer3_instance.INSTANCE_TYPE = inst
    build_layer1_base.IMAGE_CATEGORY_MAJOR = "swebench"
    build_layer2_env.IMAGE_CATEGORY_MAJOR = "swebench"
    build_layer3_instance.IMAGE_CATEGORY_MAJOR = "swebench"


def _pick_instance_batch(n: int, out_file: Path, preferred_repo: str | None = None) -> dict[str, Any]:
    from datasets import load_dataset

    ds = load_dataset("princeton-nlp/SWE-bench_Verified", split="test")
    rows = [{"instance_id": x["instance_id"], "repo": x["repo"], "version": x["version"]} for x in ds]

    if preferred_repo:
        rows = [r for r in rows if r["repo"] == preferred_repo]
        if not rows:
            raise RuntimeError(f"preferred_repo not found in dataset: {preferred_repo}")

    groups = Counter((r["repo"], r["version"]) for r in rows)
    (repo, version), count = groups.most_common(1)[0]
    selected = [r for r in rows if r["repo"] == repo and r["version"] == version][:n]

    if len(selected) < n:
        raise RuntimeError(f"Not enough instances for {repo}:{version}, need {n}, got {len(selected)}")

    out_file.write_text(json.dumps(selected, indent=2, ensure_ascii=False) + "\n")
    return {"repo": repo, "version": version, "available": count, "selected": len(selected), "file": str(out_file)}


def _build_env_for_group(instance_id: str, env_version: str, base_version: str) -> dict[str, Any]:
    return build_layer2_env.build_env_image(
        instance_id=instance_id,
        image_version=env_version,
        base_image_name="swebench-base",
        base_image_version=base_version,
        wait=False,
    )


def _build_instances(batch: list[dict[str, str]], image_version: str, env_version: str, delay: int) -> dict[str, Any]:
    results: list[dict[str, Any]] = []
    for idx, inst in enumerate(batch, 1):
        iid = inst["instance_id"]
        repo = inst["repo"]
        print(f"[{idx}/{len(batch)}] {iid} ({repo})...", end=" ", flush=True)
        r = build_layer3_instance.build_instance_image(
            instance_id=iid,
            image_version=image_version,
            env_image_version=env_version,
            wait=False,
            verbose=False,
        )
        ok = bool(r.get("success"))
        if ok:
            print(f"✅ id={r.get('image_id')}")
        else:
            print(f"❌ {r.get('error')}")
        results.append({"instance_id": iid, "repo": repo, **r})
        if idx < len(batch) and delay > 0:
            time.sleep(delay)

    submitted = sum(1 for x in results if x.get("success"))
    failed = len(results) - submitted
    return {"submitted": submitted, "failed": failed, "details": results}


def main() -> int:
    parser = argparse.ArgumentParser(description="Build SWE-bench images on SciTix aries")
    parser.add_argument("--image-version", default="1.0.0")
    parser.add_argument("--env-version", default="1.0.0")
    parser.add_argument("--n-instances", type=int, default=25)
    parser.add_argument("--delay", type=int, default=1)
    parser.add_argument("--preferred-repo", default="django/django")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    os.environ["SIFLOW_REGION"] = "ap-southeast"
    os.environ["SIFLOW_CLUSTER"] = "aries"
    _normalize_pool()
    os.environ.setdefault("SIFLOW_INSTANCE_TYPE", "sci.g20-3")

    _ = _must_getenv("SIFLOW_ACCESS_KEY_ID")
    _ = _must_getenv("SIFLOW_ACCESS_KEY_SECRET")

    _patch_build_modules()

    work_dir = Path(__file__).resolve().parent
    instances_file = work_dir / f"instances_{args.n_instances}_selected.json"
    batch_info = _pick_instance_batch(args.n_instances, instances_file, args.preferred_repo)
    batch: list[dict[str, str]] = json.loads(instances_file.read_text())

    print("[batch]", batch_info)
    print("[cfg] region/cluster=ap-southeast/aries")
    print("[cfg] resource_pool=", os.getenv("SIFLOW_RESOURCE_POOL"))
    print("[cfg] instance_type=", os.getenv("SIFLOW_INSTANCE_TYPE"))

    base_result = build_layer1_base.build_base_image(
        image_name="swebench-base",
        image_version=args.image_version,
        wait=False,
    )

    env_result = _build_env_for_group(
        instance_id=batch[0]["instance_id"],
        env_version=args.env_version,
        base_version=args.image_version,
    )

    instance_result = {"submitted": 0, "failed": args.n_instances, "details": []}
    if env_result.get("success"):
        instance_result = _build_instances(batch, args.image_version, args.env_version, args.delay)
    else:
        print("[halt] env image submit failed; skip instance submit")

    report = {
        "base": base_result,
        "env": env_result,
        "instance": instance_result,
        "batch": batch_info,
        "region": "ap-southeast",
        "cluster": "aries",
        "resource_pool": os.getenv("SIFLOW_RESOURCE_POOL"),
    }

    report_file = work_dir / "build_submit_results_scitix.json"
    report_file.write_text(json.dumps(report, indent=2, ensure_ascii=False) + "\n")
    print("[done] report:", report_file)

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
