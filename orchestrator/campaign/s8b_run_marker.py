# -*- coding: utf-8 -*-
"""R6: 実走済みマーカーと原子的 one-shot 作成 (resume 拒否の強化)。

8b oracle の途中再開は §9 項 8 = 択 (a) で全拒否する (途中 crash は当該実験全体を
判定不能に倒す)。本モジュールはその機械的支柱を提供する。

- **実走済みマーカー:** `--output-root` 非依存の場所 (freeze 正本側、既定は freeze
  ファイルと同じディレクトリ = production では `output/s8b-freeze/` 配下) に、freeze の
  byte sha256 を identity として exclusive-create する。マーカーが存在すれば当該 freeze の
  再走を全拒否する。マーカーの場所は `--output-root` に依存しないため、resume 拒否を
  出力先の付け替えで迂回できない。
- **原子的作成:** `O_CREAT|O_EXCL` による作成のみを正とする。`exists` 確認後の通常書き込み
  (非原子) は並行起動で二重に通過しうるため使わない。
"""
from __future__ import annotations

import hashlib
import json
import os
from pathlib import Path
from typing import Mapping


class RunMarkerError(RuntimeError):
    """実走マーカーの identity・原子的獲得を検証できない場合の fail-closed 拒否。"""


_MARKER_SUBDIR = "run-markers"
_HEX = frozenset("0123456789abcdef")


def freeze_identity(freeze_path) -> str:
    """freeze の byte sha256 = マーカー identity。

    canonical JSON でなく生 byte の hash を使う (どの byte 列が発効中かを一意に固定し、
    整形差でも別 identity にならないよう内容そのものへ束縛する)。
    """
    path = Path(freeze_path)
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise RunMarkerError(
            f"freeze identity 用の byte を読めない: {path}: {exc}"
        ) from exc
    return digest.hexdigest()


def marker_path(marker_root, identity: str) -> Path:
    """identity から実走済みマーカーの path を導く。

    identity は sha256 hex に限定する (path 区切り等の混入で marker_root の外へ
    書き出す path traversal を防ぐ)。
    """
    if (not isinstance(identity, str) or len(identity) != 64
            or any(char not in _HEX for char in identity)):
        raise RunMarkerError("marker identity が sha256 hex でない")
    return Path(marker_root) / _MARKER_SUBDIR / f"{identity}.marker"


def marker_exists(marker_root, identity: str) -> bool:
    """当該 freeze の実走済みマーカーが存在するか。"""
    return marker_path(marker_root, identity).exists()


def exclusive_create(path, content: bytes) -> None:
    """`O_CREAT|O_EXCL` でファイルを原子的に作成し fsync する。既存なら拒否。

    ファイル本体・親ディレクトリエントリの双方を fsync し、作成直後の crash でも
    存在自体を耐久化する (D)。既存時は `RunMarkerError` に倒す (fail-closed)。
    """
    path = Path(path)
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        fd = os.open(path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o644)
    except FileExistsError as exc:
        raise RunMarkerError(f"既に存在し原子的獲得に失敗: {path}") from exc
    except OSError as exc:
        raise RunMarkerError(f"原子的作成に失敗: {path}: {exc}") from exc
    try:
        os.write(fd, content)
        os.fsync(fd)
    finally:
        os.close(fd)
    dir_fd = os.open(path.parent, os.O_RDONLY)
    try:
        os.fsync(dir_fd)
    finally:
        os.close(dir_fd)


def create_run_marker(marker_root, identity: str, payload: Mapping) -> Path:
    """実走済みマーカーを exclusive-create する。既存なら `RunMarkerError`。

    順序上の契約: 本マーカーは WAL `campaign-start` より前に生成する。生成直後の
    crash も択 (a) の下では「実走ゼロでも再走不可」であり救済経路を持たない。
    """
    path = marker_path(marker_root, identity)
    document = {"schema": "8b-run-marker/v1", "freeze_sha256": identity,
                **dict(payload)}
    content = json.dumps(
        document, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8") + b"\n"
    exclusive_create(path, content)
    return path
