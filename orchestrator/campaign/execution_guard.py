# -*- coding: utf-8 -*-
"""共有 execution guard / receipt (C3-10 最小) — floor / oracle 両 driver 共通の実行機束縛。

責務 (本 wave の最小形):
- ``env_contract.lookup`` で解決した契約に対し、実行機の env_tag と一致するかの暫定
  machine-pin を検査する (``assert_machine_pin``)。floor の ``p2_2.ENV_TAG`` 直比較を
  この共有経路に置換し、拒否意味論を同値に保つ (guard が machine env_tag との一致を検査)。
- 契約の ``contract_sha256`` と実行機 attestation ({hostname, boot_id, cpuset,
  captured_utc}) を構造化 capture した receipt を返す (``build_receipt``)。両 driver は
  この receipt を記録 (oracle=WAL の campaign-start / floor=journal の campaign-start)。
- report / verifier 側は receipt の存在と env_tag / contract_sha256 を manifest と照合する。

この leaf は **何も強制する宣言 field を持たない** (γ-3 と同じ規律): G12 の完全強制
(walltime 予約 / allowlist / allocation・process 同一性 attestation) は Pegasus 登録段
(runbook §7) の責務であり、本 guard は「registry 契約の値集合 + 実行機の素朴な attestation」
だけを capture する。契約 lookup 自体は呼び手が行い (呼び手ごとの例外型・message を保つ)、
guard には解決済み契約を渡す — こうすることで既存の lookup 失敗経路 (floor の "env 契約"
message 等) を guard が握り潰さない。

env 固有 literal はこのモジュールに持たない (machine env_tag は呼び手が渡す)。
"""
from __future__ import annotations

import datetime as dt
import socket
from pathlib import Path
from typing import Callable, Mapping, Optional

from campaign import env_contract as _env_contract

RECEIPT_SCHEMA = "s8b-execution-receipt/v1"


class ExecutionGuardError(RuntimeError):
    """machine-pin 不一致・attestation 取得不能などの fail-closed 拒否。"""


def _boot_id() -> Optional[str]:
    """/proc/sys/kernel/random/boot_id (取得不能なら None)。"""
    try:
        text = Path("/proc/sys/kernel/random/boot_id").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    return text.strip() or None


def _cpuset() -> Optional[str]:
    """/proc/self/cpuset (存在すれば。無ければ None)。"""
    try:
        text = Path("/proc/self/cpuset").read_text(encoding="utf-8")
    except (OSError, UnicodeError):
        return None
    return text.strip() or None


def assert_machine_pin(contract: "_env_contract.ExecutionEnvironmentContract",
                       *, machine_env_tag: str) -> None:
    """契約の env_tag が実行機の env_tag と一致することを要求する (暫定 machine-pin)。

    不一致は ExecutionGuardError (「この機で走らせてよい env でない」)。呼び手が
    自分の例外型 (FloorCampaignError / OracleDriverError) へ翻訳する。"""
    if contract.env_tag != machine_env_tag:
        raise ExecutionGuardError(
            f"env_tag machine-pin 不一致: contract.env_tag={contract.env_tag} "
            f"!= machine env_tag={machine_env_tag} (この機で走らせてよい env でない)"
        )


def build_receipt(contract: "_env_contract.ExecutionEnvironmentContract",
                  *, now_fn: Optional[Callable[[], dt.datetime]] = None) -> dict:
    """解決済み契約から execution receipt を組む (contract_sha256 + 実行機 attestation)。

    receipt = {schema, env_tag, contract_sha256, attestation:{hostname, boot_id,
    cpuset, captured_utc}}。G12 完全強制 (walltime 予約等) はここに含めない — Pegasus
    登録段のまま (runbook §7)。"""
    now_fn = now_fn or (lambda: dt.datetime.now(dt.timezone.utc))
    return {
        "schema": RECEIPT_SCHEMA,
        "env_tag": contract.env_tag,
        "contract_sha256": contract.contract_sha256,
        "attestation": {
            "hostname": socket.gethostname(),
            "boot_id": _boot_id(),
            "cpuset": _cpuset(),
            "captured_utc": now_fn().isoformat(),
        },
    }


def receipt_matches_contract(receipt: Mapping, *, env_tag: str,
                             contract_sha256: str) -> bool:
    """receipt の env_tag / contract_sha256 が期待値 (manifest 由来) と一致するか。

    report 側の照合ヘルパ。attestation の存在も要求する (恒真な受理を避ける)。"""
    if not isinstance(receipt, Mapping):
        return False
    if receipt.get("schema") != RECEIPT_SCHEMA:
        return False
    if receipt.get("env_tag") != env_tag:
        return False
    if receipt.get("contract_sha256") != contract_sha256:
        return False
    attestation = receipt.get("attestation")
    if not isinstance(attestation, Mapping):
        return False
    if set(attestation) != {"hostname", "boot_id", "cpuset", "captured_utc"}:
        return False
    return True
