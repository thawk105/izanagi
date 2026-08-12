# -*- coding: utf-8 -*-
"""凍結チェーン同一性検証のユーザー裁定による一時保留。"""
from __future__ import annotations

import hashlib
import json
import os
import sys
import threading
from types import MappingProxyType
from typing import Iterable, Mapping


HELD: bool = True

HELD_CHECK_IDS = frozenset({
    "frozen-artifacts.manifest-bytes",
    "s1-known-axes.ccbench-submodule-head-pin",
    "s1-measurement.recorded-pin-current-pin",
    "s8b-floor.protocol-bytes-expected-pin",
    "s8b-floor.sealed-protocol-ccbench-pin-current-head",
    "s8b-holdout.design_source-implementation-bytes",
    "s8b-holdout.frozen-head-current-head",
    "s8b-holdout.generator-implementation-bytes",
    "s8b-holdout.known_axes_freeze-implementation-bytes",
    "s8b-oracle.known-axes-live-bytes",
    "s8b-oracle.known-axes-recorded-pin",
    "t080.historical-holdout-artifact-bytes",
    "t080.historical-known-axes-artifact-bytes",
    "t080.draft-known-axes-ccbench-current-pin",
    "t080.live-holdout-artifact-bytes",
    "t080.live-known-axes-artifact-bytes",
    "t080.live-known-axes-ccbench-current-pin",
    "t080.static-holdout-artifact-bytes",
    "t080.static-known-axes-artifact-bytes",
    "t080.static-known-axes-ccbench-current-pin",
    "t080.static-known-axes-recorded-pin",
})
HELD_CHECK_ID_COUNT = 21
HELD_CHECK_IDS_SHA256 = (
    "f60568ada1001c7b95239838300effa32431b5ee01536487f27a013fdac2e00d"
)
_actual_check_ids_sha256 = hashlib.sha256(
    "\n".join(sorted(HELD_CHECK_IDS)).encode("utf-8")
).hexdigest()
if (len(HELD_CHECK_IDS) != HELD_CHECK_ID_COUNT
        or _actual_check_ids_sha256 != HELD_CHECK_IDS_SHA256):
    raise RuntimeError("freeze verification hold の check_id 台帳が pin と不一致")

MARKER_PREFIX = "IZANAGI_FREEZE_HOLD"
_EMITTED_MARKERS: set[tuple[int, str]] = set()
_EMIT_LOCK = threading.Lock()

_RELEASE_CONDITION = "explicit-user-command-only"
REASON: Mapping[str, str] = MappingProxyType({
    "decision": "freeze-verification-hold",
    "ruling": "rulings-4th-batch-2026-08-12",
    "ruled_on": "2026-08-12",
    "authority": "user",
    "release": "ユーザーの明示命令のみ",
    "release_condition": _RELEASE_CONDITION,
})

if REASON.get("release_condition") != "explicit-user-command-only":
    raise RuntimeError("freeze verification hold の解除条件が不正")


def held_marker(check_id: str) -> dict[str, object]:
    """検査が成功したとは読めない、機械可読な保留 marker を返す。"""
    if not isinstance(check_id, str) or check_id not in HELD_CHECK_IDS:
        raise ValueError(f"freeze verification hold の未登録 check_id: {check_id!r}")
    marker = {
        "check_id": check_id,
        "status": "held",
        "reason": dict(REASON),
    }
    process_key = (os.getpid(), check_id)
    with _EMIT_LOCK:
        if process_key not in _EMITTED_MARKERS:
            payload = {
                "check_id": check_id,
                "decision": REASON["decision"],
                "ruling": REASON["ruling"],
                "release_condition": REASON["release_condition"],
            }
            sys.stderr.write(
                f"{MARKER_PREFIX} "
                f"{json.dumps(payload, ensure_ascii=False, sort_keys=True)}\n"
            )
            sys.stderr.flush()
            _EMITTED_MARKERS.add(process_key)
    return marker


class VerificationResult(dict):
    """artifact document の key を変えずに held marker を運ぶ dict 結果。"""

    def __init__(
        self, document: Mapping[str, object], *,
        held_checks: Iterable[Mapping[str, object]] = (),
    ) -> None:
        super().__init__(document)
        self.held_checks = tuple(dict(marker) for marker in held_checks)


def result_with_markers(
    document: Mapping[str, object],
    held_checks: Iterable[Mapping[str, object]],
) -> VerificationResult:
    return VerificationResult(document, held_checks=held_checks)
