# -*- coding: utf-8 -*-
"""Low-level constants for identifying the exact P3 B-4 protocol."""
from __future__ import annotations


B4_PROTOCOL_KEY = "b4_protocol"
B4_PROTOCOL_VALUE = "p3-b4-reflux-ablation/v1"


def driver_kind_from_identity(
    *, search_tag: object, trial: object, axis: object,
) -> str | None:
    """Decode the fixed B-4 driver selector from cfg or lock identity fields."""
    return {
        ("s4-autonomous", "p3-s4-loop", "silo-backoff-magnitude"): "base",
        ("s5-sort-autonomous", "p3-s5-sort-loop", "silo-writeset-sort"): "sort",
        (
            "s8a-trigger-autonomous",
            "p3-s8a-trigger-loop",
            "silo-backoff-trigger-gating",
        ): "trigger",
    }.get((search_tag, trial, axis))
