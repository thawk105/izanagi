"""受入テスト選択の runner / pytest 間共有契約。

この module は契約値を定義するだけで、import 時に環境変数やファイルを変更しない。
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from os import PathLike
from pathlib import Path
from typing import Iterable


RUNNER_EXCLUSION_ENV = "IZANAGI_TEST_RUNNER_EXCLUSIONS_V1"
SELECTION_RECEIPT_PREFIX = "IZANAGI_TEST_SELECTION_V1 "
_CANONICAL_EXCLUSION_SET_VERSION = "dev-wave-cleanup-occupancy-churn-v1"
EXCLUSION_SET_VERSION = _CANONICAL_EXCLUSION_SET_VERSION

_REPO_ROOT = Path(__file__).resolve().parents[1]


def normalize_path(path: str | PathLike[str]) -> Path:
    """契約で使う path 正規化を一箇所に固定する。"""

    return Path(path).resolve(strict=False)


@dataclass(frozen=True)
class Exclusion:
    """受入全走から除外できる一つの契約 entry。"""

    path: str | PathLike[str]
    reason: str
    release_condition: str
    ruling: str
    set_version: str = EXCLUSION_SET_VERSION


_CANONICAL_CLEANUP_TEST_PATH = normalize_path(
    _REPO_ROOT / "orchestrator" / "tests" / "test_dev_wave_cleanup.py"
)
_CANONICAL_EXCLUSION_REASON = (
    "消滅pid型occupancy issueを3 scan連続観測しcleanup testsがrc22になる"
)
_CANONICAL_EXCLUSION_RULING = (
    "2026-08-24 user direct known-red registration"
)
_CANONICAL_EXCLUSION_RELEASE_CONDITION = (
    "dev-wave-cleanup-occupancy-churn taskがlandし、明示file走が全緑"
)

SANCTIONED_CLEANUP_TEST_PATH = _CANONICAL_CLEANUP_TEST_PATH
_CANONICAL_EXCLUSION = Exclusion(
    path=_CANONICAL_CLEANUP_TEST_PATH,
    reason=_CANONICAL_EXCLUSION_REASON,
    release_condition=_CANONICAL_EXCLUSION_RELEASE_CONDITION,
    ruling=_CANONICAL_EXCLUSION_RULING,
    set_version=_CANONICAL_EXCLUSION_SET_VERSION,
)
SANCTIONED_EXCLUSIONS: tuple[Exclusion, ...] = ()


def _entry_payload(entry: Exclusion) -> dict[str, str]:
    if type(entry) is not Exclusion:
        raise TypeError("selection contract entries must be Exclusion values")
    if not all(
        isinstance(value, str) and value.strip()
        for value in (
            entry.reason,
            entry.release_condition,
            entry.ruling,
            entry.set_version,
        )
    ):
        raise ValueError("selection contract metadata must be non-empty strings")
    return {
        "path": str(normalize_path(entry.path)),
        "reason": entry.reason,
        "release_condition": entry.release_condition,
        "ruling": entry.ruling,
        "set_version": entry.set_version,
    }


def payload_entries(entries: Iterable[Exclusion]) -> list[dict[str, str]]:
    """payload の構造を canonical な dict 列として返す。"""

    return [_entry_payload(entry) for entry in entries]


def serialize_payload(entries: Iterable[Exclusion]) -> str:
    """runner env の payload に使う canonical serializer。"""

    return json.dumps(
        payload_entries(entries),
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def serialize_selection_receipt(entries: Iterable[Exclusion]) -> str:
    """既存 receipt 形式の単一 entry payload を canonical に serialize する。"""

    payload = payload_entries(entries)
    if len(payload) != 1:
        raise ValueError("selection receipt requires exactly one exclusion entry")
    return json.dumps(
        payload[0],
        ensure_ascii=False,
        separators=(",", ":"),
        sort_keys=True,
    )


def selection_receipt_line(entries: Iterable[Exclusion]) -> str:
    return SELECTION_RECEIPT_PREFIX + serialize_selection_receipt(entries)


def exclusion_tokens(entries: Iterable[Exclusion]) -> tuple[str, ...]:
    """契約 entry 列に対応する runner-owned pytest narrowing token。"""

    return tuple(f"--ignore={normalize_path(entry.path)}" for entry in entries)


def sanctioned_target_is_regular_file() -> bool:
    path = _CANONICAL_CLEANUP_TEST_PATH
    return path.is_file() and not path.is_symlink()


def canonicalize_sanctioned_exclusion_set(
    entries: Iterable[Exclusion],
) -> tuple[Exclusion, ...] | None:
    """裁定済み集合を entry まで immutable な private canonical 値へ写す。"""

    try:
        actual = tuple(entries)
    except TypeError:
        return None
    if not actual:
        return ()
    if len(actual) != 1 or type(actual[0]) is not Exclusion:
        return None
    entry = actual[0]
    try:
        # PathLike はここで一度だけ評価する。以後は caller entry を再利用せず、
        # private canonical Exclusion だけを serializer / token consumer へ渡す。
        raw_path = Path(entry.path)
        path_matches = normalize_path(raw_path) == _CANONICAL_CLEANUP_TEST_PATH
        actual_target_is_regular = raw_path.is_file() and not raw_path.is_symlink()
    except (OSError, TypeError, ValueError):
        return None
    matches = bool(
        path_matches
        and actual_target_is_regular
        and sanctioned_target_is_regular_file()
        and entry.reason == _CANONICAL_EXCLUSION_REASON
        and entry.release_condition == _CANONICAL_EXCLUSION_RELEASE_CONDITION
        and entry.ruling == _CANONICAL_EXCLUSION_RULING
        and entry.set_version == _CANONICAL_EXCLUSION_SET_VERSION
    )
    if not matches:
        return None
    if entry is _CANONICAL_EXCLUSION:
        return actual
    return (_CANONICAL_EXCLUSION,)


def is_sanctioned_exclusion_set(entries: Iterable[Exclusion]) -> bool:
    """空集合または private canonical exactly-one だけを許可する。"""

    return canonicalize_sanctioned_exclusion_set(entries) is not None
