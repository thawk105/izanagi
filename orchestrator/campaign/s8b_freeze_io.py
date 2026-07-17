# -*- coding: utf-8 -*-
"""実行用 holdout freeze bytes の hash 検証付き読込の中立置場 (oracle/floor 共有)。

ratified 型・strict parse の追加 (duplicate key 拒否等) は F6/F7 裁定後の
``load_ratified_freeze`` の責務であり、本モジュールには追加しない。検証意味論
(verify_document) は所有しない。

stdlib のみに依存する leaf モジュール (campaign 内 import ゼロ)。oracle driver と
floor campaign が同一の loader を共有し、片方の import がもう片方を巻き込まないよう
にするための中立置場である。
"""
from __future__ import annotations

import hashlib
import json
from dataclasses import dataclass
from pathlib import Path
from typing import Optional


class FreezeIOError(RuntimeError):
    """実行用 holdout freeze bytes の読込・hash 検証・strict parse を満たせない拒否。"""


def _reject_json_constant(token: str):
    """strict parse: NaN / Infinity 等の非数値定数を拒否する。"""
    raise FreezeIOError(f"freeze JSON に非数値定数が含まれる: {token}")


@dataclass(frozen=True)
class VerifiedFreeze:
    """hash 検証済み freeze bytes の strict parse 結果と、その byte sha256。

    verify から use までを単一 object で束ね、consumer 間 (gate・driver・
    manifest verify・budget limits・perf 三軸) の再読込を除去する (A3-6)。
    """
    document: dict
    sha256: str


def load_verified_freeze(path, expected_hash: Optional[str] = None) -> VerifiedFreeze:
    """freeze bytes を一度だけ読み、hash 検証 + strict parse した単一 object を返す。

    全 consumer はこの戻り値の ``document`` / ``sha256`` だけを使い、freeze を
    再読込しない。よって gate 検証後・使用前に freeze byte を差し替えても差替え後
    の値は一切観測されない (verify-use 間 TOCTOU の遮断、A3-6)。``expected_hash``
    を与えた場合は byte sha256 との一致を要求し、不一致は拒否する (fail-closed)。
    """
    path = Path(path)
    try:
        raw = path.read_bytes()
    except OSError as exc:
        raise FreezeIOError(f"freeze bytes を読めない: {path}: {exc}") from exc
    sha256 = hashlib.sha256(raw).hexdigest()
    if expected_hash is not None and sha256 != expected_hash:
        raise FreezeIOError(
            f"freeze byte sha256 が expected_hash と不一致: {path}"
        )
    try:
        document = json.loads(raw.decode("utf-8"),
                              parse_constant=_reject_json_constant)
    except (UnicodeError, json.JSONDecodeError) as exc:
        raise FreezeIOError(
            f"freeze JSON を strict parse できない: {path}: {exc}"
        ) from exc
    if not isinstance(document, dict):
        raise FreezeIOError(f"freeze JSON top-level が object でない: {path}")
    return VerifiedFreeze(document=document, sha256=sha256)
