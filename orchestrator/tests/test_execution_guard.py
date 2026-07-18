# -*- coding: utf-8 -*-
"""共有 execution guard leaf (C3-10) の machine-pin / receipt / 照合契約テスト。

env_contract の唯一の登録 env (linux-baremetal) を実 lookup し、machine-pin の同値・
receipt の形・照合ヘルパ (存在と一致の両検査) を固定する。pytest 非依存の _run() 自走
harness を末尾に持つ (二重 runner 規律)。
"""
from __future__ import annotations

import os
import sys

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import env_contract as ec  # noqa: E402
from campaign import execution_guard as eg  # noqa: E402


_ENV = "linux-baremetal"


def _contract():
    return ec.lookup(_ENV)


def test_assert_machine_pin_accepts_matching_env_tag():
    eg.assert_machine_pin(_contract(), machine_env_tag=_ENV)  # 例外なし


def test_assert_machine_pin_rejects_foreign_env_tag():
    try:
        eg.assert_machine_pin(_contract(), machine_env_tag="foreign-machine")
    except eg.ExecutionGuardError as exc:
        assert "machine-pin" in str(exc)
    else:
        raise AssertionError("foreign machine env_tag が machine-pin で拒否されない")


def test_build_receipt_shape_and_contract_binding():
    contract = _contract()
    receipt = eg.build_receipt(contract, now_fn=lambda: _FixedNow())
    assert receipt["schema"] == eg.RECEIPT_SCHEMA
    assert receipt["env_tag"] == _ENV
    assert receipt["contract_sha256"] == contract.contract_sha256
    assert set(receipt["attestation"]) == {
        "hostname", "boot_id", "cpuset", "captured_utc",
    }
    assert receipt["attestation"]["captured_utc"] == "2026-07-18T00:00:00+00:00"


def test_receipt_matches_contract_accepts_consistent_receipt():
    contract = _contract()
    receipt = eg.build_receipt(contract)
    assert eg.receipt_matches_contract(
        receipt, env_tag=_ENV, contract_sha256=contract.contract_sha256,
    )


def test_receipt_matches_contract_rejects_mismatch_and_missing_attestation():
    contract = _contract()
    receipt = eg.build_receipt(contract)
    # contract_sha256 不一致。
    assert not eg.receipt_matches_contract(
        receipt, env_tag=_ENV, contract_sha256="1" * 64,
    )
    # env_tag 不一致。
    assert not eg.receipt_matches_contract(
        receipt, env_tag="other", contract_sha256=contract.contract_sha256,
    )
    # attestation 欠落は恒真受理でなく拒否。
    stripped = dict(receipt)
    stripped.pop("attestation")
    assert not eg.receipt_matches_contract(
        stripped, env_tag=_ENV, contract_sha256=contract.contract_sha256,
    )
    # attestation の key 集合が不完全なら拒否。
    bad_attest = dict(receipt)
    bad_attest["attestation"] = {"hostname": "h"}
    assert not eg.receipt_matches_contract(
        bad_attest, env_tag=_ENV, contract_sha256=contract.contract_sha256,
    )
    # 非 Mapping は拒否。
    assert not eg.receipt_matches_contract(
        None, env_tag=_ENV, contract_sha256=contract.contract_sha256,
    )


class _FixedNow:
    def isoformat(self):
        return "2026-07-18T00:00:00+00:00"


# ===== 二重 runner (pytest 非依存) =====

def _run():
    import traceback
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    npass = nfail = nerr = 0
    for fn in fns:
        try:
            fn()
            npass += 1
        except AssertionError as e:
            nfail += 1
            print(f"FAIL {fn.__name__}: {e}")
        except Exception:  # noqa: BLE001
            nerr += 1
            print(f"ERROR {fn.__name__}:")
            traceback.print_exc()
    print(f"\n{npass} passed, {nfail} failed, {nerr} errors (of {len(fns)})")
    return 0 if (nfail == 0 and nerr == 0) else 1


if __name__ == "__main__":
    sys.exit(_run())
