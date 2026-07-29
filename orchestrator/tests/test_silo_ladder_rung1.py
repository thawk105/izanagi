# -*- coding: utf-8 -*-
"""Silo ladder rung 1 の patch/ledger 静的契約と事前登録変異。"""
from __future__ import annotations

import hashlib
import inspect
import json
from pathlib import Path
import shutil
import subprocess
import sys
import tempfile
import traceback


HERE = Path(__file__).resolve().parent
ROOT = HERE.parent.parent
FIXTURES = HERE / "fixtures" / "silo_ladder_rung1"
PATCH = ROOT / "patches" / "silo_ladder_rung1.patch"
LEDGER = ROOT / "patches" / "ledger.json"

sys.path.insert(0, str(ROOT))
from orchestrator.campaign import silo_ladder_rung1_contract as contract  # noqa: E402


def _read(path: Path) -> str:
    return path.read_text(encoding="utf-8")


def _stock_sources() -> dict[str, str]:
    return {
        path: _read(FIXTURES / "stock" / path)
        for path in contract.SOURCE_FILES
    }


def _reason_codes(failures) -> list[str]:
    return [failure.reason_code for failure in failures]


def _assert_only_fixture_reason(name: str, reason: str) -> None:
    failures = contract.validate_patch(
        _read(FIXTURES / name),
        _stock_sources(),
    )
    assert _reason_codes(failures) == [reason], failures


def test_p_plus_1_real_patch_and_ledger_pass_every_contract():
    """P+1: 実 patch + 実 ledger + pin fixture は全八契約が緑。"""
    failures = contract.validate(
        _read(PATCH),
        _stock_sources(),
        _read(LEDGER),
    )
    assert failures == ()


def test_n1_thread_local_kills_only_non_thread_local():
    _assert_only_fixture_reason(
        "n1_thread_local.patch",
        contract.NON_THREAD_LOCAL,
    )


def test_n2a_guard_early_close_kills_only_guard_lifetime():
    _assert_only_fixture_reason(
        "n2a_guard_early_close.patch",
        contract.GUARD_LIFETIME,
    )


def test_n2b_second_cas_kills_only_single_cas_no_bypass():
    _assert_only_fixture_reason(
        "n2b_second_cas.patch",
        contract.SINGLE_CAS_NO_BYPASS,
    )


def test_n_fixtures_are_exact_single_mutations_of_real_patch():
    """N1/N2a/N2b は実 patch から対象 predicate だけを変異した bytes。"""
    patch = _read(PATCH)
    expected = {
        "n1_thread_local.patch": patch.replace(
            "+std::mutex gate_mutex;",
            "+thread_local std::mutex gate_mutex;",
            1,
        ),
        "n2a_guard_early_close.patch": patch.replace(
            (
                "+          acquired = compareExchange("
                "(*itr).rcdptr_->tidword_.obj_,\n"
                "+                                     expected.obj_, desired.obj_);\n"
                "+        }\n"
            ),
            (
                "+        }\n"
                "+        acquired = compareExchange("
                "(*itr).rcdptr_->tidword_.obj_,\n"
                "+                                   expected.obj_, desired.obj_);\n"
            ),
            1,
        ),
        "n2b_second_cas.patch": patch.replace(
            "@@ -169,8 +184,20 @@",
            "@@ -169,8 +184,22 @@",
            1,
        ).replace(
            "+        }\n+        if (acquired) {",
            (
                "+        }\n"
                "+        acquired = compareExchange("
                "(*itr).rcdptr_->tidword_.obj_,\n"
                "+                                   expected.obj_, desired.obj_);\n"
                "+        if (acquired) {"
            ),
            1,
        ),
    }
    for name, expected_bytes in expected.items():
        assert _read(FIXTURES / name) == expected_bytes


def test_identity_rejects_legacy_single_declaration_and_missing_definition():
    patch = _read(PATCH)
    identity_block = (
        '+extern "C" {\n'
        '+__attribute__((used, visibility("default")))\n'
        "+volatile unsigned char "
        "izanagi_silo_ladder_rung1_identity = 1;\n"
        "+}\n"
    )
    cases = (
        patch.replace(
            identity_block,
            (
                '+extern "C" __attribute__((used, visibility("default")))\n'
                "+volatile unsigned char "
                "izanagi_silo_ladder_rung1_identity = 1;\n"
            ),
            1,
        ),
        patch.replace(identity_block, "", 1),
    )
    for mutated in cases:
        failures = contract.validate_patch(mutated, _stock_sources())
        assert _reason_codes(failures) == [contract.IDENTITY_SYMBOL_REASON], failures


def test_remaining_patch_checks_have_non_vacuous_single_reason_controls():
    """N1/N2 群外の patch predicate も、対応する一変異だけで発火する。"""
    patch = _read(PATCH)
    cases = (
        (
            patch.replace(
                (
                    "#if IZANAGI_SILO_LADDER_RUNG1 && "
                    "IZANAGI_SILO_LADDER_RUNG1_REPORT"
                ),
                "#if IZANAGI_SILO_LADDER_RUNG1",
                1,
            ),
            contract.MACRO_DISCIPLINE,
        ),
        (
            patch.replace(
                "                            desired.obj_)) {",
                "                            desired.obj_)) { ",
                1,
            ),
            contract.STOCK_VERBATIM,
        ),
        (
            patch.replace(
                "izanagi_silo_ladder_rung1_identity = 1;",
                "izanagi_silo_ladder_rung1_identity = 2;",
                1,
            ),
            contract.IDENTITY_SYMBOL_REASON,
        ),
        (
            patch + (
                "diff --git a/cc/silo/undeclared.cc "
                "b/cc/silo/undeclared.cc\n"
            ),
            contract.DECLARED_FILES_ONLY,
        ),
    )
    for mutated, expected in cases:
        failures = contract.validate_patch(mutated, _stock_sources())
        assert _reason_codes(failures) == [expected], failures


def test_ledger_closed_schema_and_hash_binding_have_teeth():
    patch = _read(PATCH)
    base = json.loads(_read(LEDGER))
    unknown_documents = []
    for location in (
        (),
        ("entries", 0),
        ("entries", 0, "symbols", 0),
        ("entries", 0, "projection_policy"),
    ):
        ledger = json.loads(json.dumps(base))
        target = ledger
        for component in location:
            target = target[component]
        target["unknown_key"] = "must-fail"
        unknown_documents.append(ledger)
    for ledger in unknown_documents:
        unknown = contract.validate_ledger(
            patch,
            json.dumps(ledger, ensure_ascii=False),
        )
        assert unknown is not None
        assert unknown.reason_code == contract.LEDGER_CONSISTENCY

    drift = contract.validate_ledger(patch + "\n", _read(LEDGER))
    assert drift is not None
    assert drift.reason_code == contract.LEDGER_CONSISTENCY
    assert "patch_sha256 mismatch" in drift.detail

    duplicated = json.loads(json.dumps(base))
    duplicated["entries"].append(
        json.loads(json.dumps(duplicated["entries"][0]))
    )
    duplicate_failure = contract.validate_ledger(
        patch,
        json.dumps(duplicated, ensure_ascii=False),
    )
    assert duplicate_failure is not None
    assert "entry ids are not unique" in duplicate_failure.detail
    assert "entry macros are not unique" in duplicate_failure.detail
    assert "symbol names are not unique" in duplicate_failure.detail


def test_patch_applies_to_hermetic_pinned_source_fixture(tmp_path: Path):
    """共有 submodule を読まず、pin bytes の一時 repo だけで apply --check する。"""
    expected_fixture_hashes = {
        "cc/silo/transaction.cc": (
            "89a552b251950f46568856e9c229d1b370e84eda710c0bdc23a7a5cc6e1b85fa"
        ),
        "cc/silo/ycsb_silo.cc": (
            "2fcbf7233b04d92f5fa079ff504016d7ff0793ae9658b00e8aea30a5ff859bc9"
        ),
    }
    for relative, expected_hash in expected_fixture_hashes.items():
        source = FIXTURES / "stock" / relative
        assert hashlib.sha256(source.read_bytes()).hexdigest() == expected_hash
        destination = tmp_path / relative
        destination.parent.mkdir(parents=True, exist_ok=True)
        shutil.copyfile(source, destination)

    initialized = subprocess.run(
        ["git", "init", "-q"],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert initialized.returncode == 0, initialized.stderr
    checked = subprocess.run(
        ["git", "apply", "--check", str(PATCH)],
        cwd=tmp_path,
        check=False,
        capture_output=True,
        text=True,
    )
    assert checked.returncode == 0, checked.stderr


def _run() -> int:
    functions = [
        value
        for name, value in sorted(globals().items())
        if name.startswith("test_") and callable(value)
    ]
    passed = failed = errors = 0
    for function in functions:
        try:
            if "tmp_path" in inspect.signature(function).parameters:
                with tempfile.TemporaryDirectory(
                    prefix="izanagi-silo-rung1-test-"
                ) as temp:
                    function(Path(temp))
            else:
                function()
            passed += 1
        except AssertionError as exc:
            failed += 1
            print(f"FAIL {function.__name__}: {exc}")
        except Exception:
            errors += 1
            print(f"ERROR {function.__name__}:")
            traceback.print_exc()
    print(
        f"\n{passed} passed, {failed} failed, {errors} errors "
        f"(of {len(functions)})"
    )
    return 0 if failed == 0 and errors == 0 else 1


if __name__ == "__main__":
    sys.exit(_run())
