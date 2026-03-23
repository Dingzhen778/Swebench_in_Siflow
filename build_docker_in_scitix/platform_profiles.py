#!/usr/bin/env python3
"""Platform profiles for SWE-bench image build submitters."""

from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class PlatformProfile:
    name: str
    region: str
    cluster: str
    resource_pool: str
    instance_type: str


def get_platform_profile(name: str) -> PlatformProfile:
    key = (name or "aries").strip().lower()

    if key == "aries":
        return PlatformProfile(
            name="aries",
            region="ap-southeast",
            cluster="aries",
            resource_pool="ap-southeast-aries-hisys-ondemand-shared",
            instance_type="sci.g20-3",
        )

    if key == "cetus":
        return PlatformProfile(
            name="cetus",
            region="cn-shanghai",
            cluster="cetus",
            resource_pool="cn-shanghai-cetus-hisys-ondemand-shared",
            instance_type="sci.g20-3",
        )

    raise ValueError(f"Unsupported platform: {name}")
