# -*- coding: utf-8 -*-
"""Pegasus の site 判定と既定並列度を集約する stdlib-only leaf。"""
from __future__ import annotations

import os
import re
import shutil
import socket


OTHER = "OTHER"
PEGASUS_LOGIN = "PEGASUS_LOGIN"
PEGASUS_COMPUTE = "PEGASUS_COMPUTE"
PEGASUS_SUSPECT = "PEGASUS_SUSPECT"

LOGIN_FALLBACK_RE = re.compile(r"^pegasus0[1-9]$")
_COMPUTE_RE = re.compile(r"^bnode[0-9]+$")
NQSV_MARKER_DIR = "/opt/nec/nqsv"


def _first_label(hostname: str | None) -> str | None:
    if not isinstance(hostname, str):
        return None
    normalized = hostname.lower().rstrip(".")
    if not normalized:
        return None
    return normalized.split(".", 1)[0]


def classify_site(hostname: str | None, environ, has_nqsv: bool) -> str:
    """明示入力だけから site を分類する純関数。

    ``environ`` は caller API の一部だが、現裁定では ``PBS_JOBID`` を含む環境値は
    分類条件にしない。計算ノードの権威は ``bnode`` hostname と affinity である。
    """
    del environ
    label = _first_label(hostname)
    if label is None:
        return PEGASUS_SUSPECT if has_nqsv else OTHER
    if _COMPUTE_RE.fullmatch(label):
        return PEGASUS_COMPUTE
    if LOGIN_FALLBACK_RE.fullmatch(label):
        return PEGASUS_LOGIN if has_nqsv else OTHER
    if label.startswith("pegasus"):
        return PEGASUS_SUSPECT if has_nqsv else OTHER
    return OTHER


def _has_nqsv(marker_path=None) -> bool:
    """PATH 上の実行体または機体固有 directory から NQSV を検出する。"""
    try:
        qsub = shutil.which("qsub")
        qstat = shutil.which("qstat")
    except OSError:
        qsub = qstat = None
    if qsub is not None and qstat is not None:
        return True

    marker = NQSV_MARKER_DIR if marker_path is None else marker_path
    try:
        return os.path.isdir(marker)
    except Exception:  # marker 観測不能は NQSV 証拠なしへ倒す
        return False


def current_site() -> str:
    """実 hostname と PATH / directory の NQSV 証拠から現在の site を解決する。"""
    try:
        hostname = socket.gethostname()
    except Exception:  # hostname 解決不能は証拠の有無に応じて安全側へ分類する
        hostname = None
    return classify_site(hostname, os.environ, _has_nqsv())


def is_pegasus_login(site: str) -> bool:
    return site == PEGASUS_LOGIN


def is_pegasus_compute(site: str) -> bool:
    return site == PEGASUS_COMPUTE


def refuses_heavy_work(site: str) -> bool:
    """重い処理を拒否すべき site なら True。"""
    return site in {PEGASUS_LOGIN, PEGASUS_SUSPECT}


def available_cpus() -> int:
    """cgroup / affinity を尊重して、この process が使える CPU 数を返す。"""
    process_cpu_count = getattr(os, "process_cpu_count", None)
    if process_cpu_count is not None:
        try:
            count = process_cpu_count()
        except OSError:
            count = None
        if count is not None and count > 0:
            return count

    try:
        affinity_count = len(os.sched_getaffinity(0))
    except (AttributeError, OSError):
        affinity_count = 0
    if affinity_count > 0:
        return affinity_count

    count = os.cpu_count()
    return count if count is not None and count > 0 else 1


def default_test_jobs(site: str, *, cap: int = 32) -> int:
    """test の既定並列度。compute だけ affinity 全数、それ以外は cap 付き。"""
    cpus = available_cpus()
    if is_pegasus_compute(site):
        return cpus
    return min(cpus, cap)


def default_build_jobs(site: str) -> int:
    """build の既定並列度。compute 以外の既存値 16 は変更しない。"""
    if is_pegasus_compute(site):
        return available_cpus()
    return 16


def heavy_work_refusal(
    site: str,
    what: str,
    *,
    queue_hint: tuple[bool, str] | None = None,
) -> str:
    """重い処理の拒否理由と、計算ノードを使う準拠経路を日本語で返す。

    この leaf 自身はキューを観測しない。最上位 caller が既に観測した
    ``dispatch_possible()`` の結果を ``queue_hint`` に渡した場合だけ、
    利用不可の診断を追記する。
    """
    if site == PEGASUS_LOGIN:
        reason = "Pegasus ログインノードでは重い処理を実行できません"
    elif site == PEGASUS_SUSPECT:
        reason = "Pegasus 環境の疑いがあり、安全に実行場所を確定できません"
    else:
        reason = "この site では重い処理を実行できません"
    message = (
        f"{what} を拒否します: {reason}。"
        "qsub または qlogin を使い、Pegasus 計算ノードで実行してください。"
    )
    if queue_hint is None:
        return message
    possible, queue_reason = queue_hint
    if possible:
        return message
    return (
        message + f" 計算ノードが必要ですが、{queue_reason}"
        " この状態では投入しても実行されません。"
        "したがって性能測定は現時点では実施できません。"
    )
