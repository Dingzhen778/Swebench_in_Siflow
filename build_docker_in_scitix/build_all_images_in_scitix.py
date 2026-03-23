#!/usr/bin/env python3
"""Submit SWE-bench image builds with explicit platform profile (aries/cetus)."""

from __future__ import annotations

import argparse
import json
import os
import sys
from pathlib import Path
from typing import Any

from dotenv import load_dotenv

ROOT = Path(__file__).resolve().parent.parent
BUILD_DIR = ROOT / "build"
VENDOR_DIR = ROOT / ".vendor_siflow"
LOCAL_DIR = Path(__file__).resolve().parent

sys.path.insert(0, str(VENDOR_DIR))
sys.path.insert(0, str(ROOT))
sys.path.insert(0, str(BUILD_DIR))
sys.path.insert(0, str(LOCAL_DIR))

from siflow import SiFlow  # type: ignore

import siflow_config
import siflow_utils
import build_layer1_base
import build_layer2_env
import build_layer3_instance
import build_all_images
from platform_profiles import get_platform_profile, PlatformProfile


def must_env(name: str) -> str:
    v = os.getenv(name, "").strip()
    if not v:
        raise RuntimeError(f"Missing required env var: {name}")
    return v


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


def create_client_patched(profile: PlatformProfile):
    return patch_client(create_client(profile), profile)


def patch_modules(profile: PlatformProfile) -> None:
    def _client_factory() -> SiFlow:
        return create_client_patched(profile)

    siflow_utils.create_siflow_client = _client_factory
    build_layer1_base.create_siflow_client = _client_factory
    build_layer2_env.create_siflow_client = _client_factory
    build_layer3_instance.create_siflow_client = _client_factory

    siflow_config.REGION = profile.region
    siflow_config.CLUSTER = profile.cluster
    siflow_config.RESOURCE_POOL = profile.resource_pool
    siflow_config.IMAGE_CATEGORY_MAJOR = "swebench"
    siflow_config.INSTANCE_TYPE = profile.instance_type

    build_layer1_base.RESOURCE_POOL = profile.resource_pool
    build_layer2_env.RESOURCE_POOL = profile.resource_pool
    build_layer3_instance.RESOURCE_POOL = profile.resource_pool

    build_layer1_base.INSTANCE_TYPE = profile.instance_type
    build_layer2_env.INSTANCE_TYPE = profile.instance_type
    build_layer3_instance.INSTANCE_TYPE = profile.instance_type

    build_layer1_base.IMAGE_CATEGORY_MAJOR = "swebench"
    build_layer2_env.IMAGE_CATEGORY_MAJOR = "swebench"
    build_layer3_instance.IMAGE_CATEGORY_MAJOR = "swebench"


def apply_env(profile: PlatformProfile) -> None:
    os.environ["SIFLOW_REGION"] = profile.region
    os.environ["SIFLOW_CLUSTER"] = profile.cluster
    os.environ["SIFLOW_RESOURCE_POOL"] = profile.resource_pool
    os.environ["SIFLOW_INSTANCE_TYPE"] = profile.instance_type


def main() -> int:
    parser = argparse.ArgumentParser(description="Build all SWE-bench images with explicit platform profile")
    parser.add_argument("--platform", choices=["aries", "cetus"], default="aries")
    parser.add_argument("--layer", choices=["base", "env", "instance", "all"], default="all")
    parser.add_argument("--version", default="1.0.0")
    parser.add_argument("--env-version", default=None)
    parser.add_argument("--repo", default=None)
    parser.add_argument("--instances-file", default=None)
    parser.add_argument("--max-instances", type=int, default=None)
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--delay", type=int, default=1)
    parser.add_argument("--result-file", default="build_submit_results_scitix.json")
    args = parser.parse_args()

    load_dotenv(ROOT / ".env")
    profile = get_platform_profile(args.platform)
    apply_env(profile)

    must_env("SIFLOW_ACCESS_KEY_ID")
    must_env("SIFLOW_ACCESS_KEY_SECRET")

    if args.env_version is None:
        args.env_version = args.version

    patch_modules(profile)

    print("=" * 70)
    print("SWE-bench Full Build Wrapper")
    print("=" * 70)
    print(
        f"platform={profile.name} region={profile.region} cluster={profile.cluster} "
        f"resource_pool={profile.resource_pool} instance_type={profile.instance_type}"
    )
    print(f"layer={args.layer}, version={args.version}, env_version={args.env_version}, delay={args.delay}")

    results: dict[str, Any] = {}
    submitted_total = 0
    failed_total = 0

    if args.layer in ["base", "all"]:
        r = build_all_images.build_base(image_version=args.version, force=args.force)
        results["base"] = r
        if r.get("status") == "building":
            submitted_total += 1

    if args.layer in ["env", "all"]:
        r = build_all_images.build_environments(
            image_version=args.env_version,
            base_image_version=args.version,
            force=args.force,
            delay=args.delay,
            filter_repo=args.repo,
            instances_file=args.instances_file,
        )
        results["env"] = r
        submitted_total += r.get("submitted", 0)
        failed_total += r.get("failed", 0)

    if args.layer in ["instance", "all"]:
        r = build_all_images.build_instances(
            image_version=args.version,
            env_image_version=args.env_version,
            force=args.force,
            delay=args.delay,
            filter_repo=args.repo,
            instances_file=args.instances_file,
            max_instances=args.max_instances,
        )
        results["instance"] = r
        submitted_total += r.get("submitted", 0)
        failed_total += r.get("failed", 0)

    out_file = ROOT / args.result_file
    out_file.write_text(json.dumps(results, indent=2, ensure_ascii=False) + "\n")
    print(f"\nResult saved to {out_file}")
    print(f"Submitted={submitted_total}, Failed={failed_total}")
    return 0 if failed_total == 0 else 1


if __name__ == "__main__":
    raise SystemExit(main())
