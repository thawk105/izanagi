# -*- coding: utf-8 -*-
"""Shared execution guard and versioned receipt binding for floor/oracle.

Legacy ``mode=none`` contracts retain the v1 machine-pin/receipt path unchanged.
For ``mode=required``, :func:`attest_and_build_receipt` is the only v2 issuer:
it probes and compares the hash-bound calibration profile before constructing a
receipt.  The consumer dispatches by receipt schema and independently recomputes
all recorded comparisons.  Environment-specific literals are forbidden here.
"""
from __future__ import annotations

import datetime as dt
import json
import math
import os
import re
import socket
import statistics
from pathlib import Path
from typing import Callable, Mapping, Optional

from ..calibrator import schema_v2 as _schema_v2
from ..calibrator import effective_clock_policy
from . import env_contract as _env_contract
from . import env_contract_activation as _env_contract_activation
from . import env_attestation as _env_attestation
from . import site_policy as _site_policy

RECEIPT_SCHEMA = "s8b-execution-receipt/v1"
RECEIPT_SCHEMA_V2 = "s8b-execution-receipt/v2"

_HEX64_RE = re.compile(r"[0-9a-f]{64}")
_SLUG_RE = re.compile(r"[a-z0-9][a-z0-9._-]*")


class ExecutionGuardError(RuntimeError):
    """machine-pin 不一致・attestation 取得不能などの fail-closed 拒否。"""


class CertifiedWriterAuthorizationError(ExecutionGuardError, ValueError):
    """Certified-writer authorization input is inconsistent or unregistered."""


def _contract_from_authorization(
        authorization: "_env_contract.AuthorizedContract",
) -> "_env_contract.ExecutionEnvironmentContract":
    """渡された authorized value の receipt だけから current 契約を解決する。"""
    if type(authorization) is not _env_contract.AuthorizedContract:
        raise TypeError(
            "authorization_contract は exact AuthorizedContract が必要"
        )
    if type(authorization.contract) is not _env_contract.ExecutionEnvironmentContract:
        raise CertifiedWriterAuthorizationError(
            "authorization receipt の contract 型が不正"
        )
    if (type(authorization.issued_pid) is not int
            or authorization.issued_pid != os.getpid()):
        raise CertifiedWriterAuthorizationError(
            "authorization receipt の発行 PID が current process と一致しない"
        )
    if authorization.process_seal is not _env_contract._AUTHORIZATION_PROCESS_SEAL:
        raise CertifiedWriterAuthorizationError(
            "authorization receipt の process seal が一致しない"
        )
    if _env_contract._AUTHORIZED_CONTRACTS.get(
            authorization.contract.env_tag) is not authorization:
        raise CertifiedWriterAuthorizationError(
            "authorization receipt が current process の cached issuer 発行物でない"
        )
    state = authorization._activation_state
    if type(state) is not _env_contract_activation.ActivationState:
        raise CertifiedWriterAuthorizationError(
            "authorization receipt の state 型が不正"
        )
    if (type(authorization.activation_serial) is not int
            or authorization.activation_serial != state.activation_serial
            or type(authorization.activation_state_sha256) is not str
            or authorization.activation_state_sha256 != state.activation_state_sha256):
        raise CertifiedWriterAuthorizationError(
            "authorization receipt の serial/state hash が state と一致しない"
        )
    env_tag = authorization.contract.env_tag
    matches = tuple(row for row in state.active_contracts if row.env_tag == env_tag)
    if len(matches) != 1:
        raise CertifiedWriterAuthorizationError(
            "activation receipt state から env_tag を一意に解決できない"
        )
    row = matches[0]
    try:
        entry = _env_contract.GENERATIONS[row.env_tag][row.generation - 1]
    except (KeyError, IndexError, TypeError) as exc:
        raise CertifiedWriterAuthorizationError(
            "activation receipt state が未登録 generation を指している"
        ) from exc
    if (entry.generation != row.generation
            or entry.contract.contract_sha256 != row.contract_sha256):
        raise CertifiedWriterAuthorizationError(
            "activation receipt state と generation registry が一致しない"
        )
    if authorization.contract is not entry.contract:
        raise CertifiedWriterAuthorizationError(
            "authorization contract が receipt state の current contract と一致しない"
        )
    return entry.contract


def require_certified_writer_authorization(
        authorization_contract: "_env_contract.AuthorizedContract", *,
        env_tag: str, clocks_per_us: int, numactl,
        env_contract: Optional[
            "_env_contract.ExecutionEnvironmentContract"
        ] = None,
) -> "_env_contract.ExecutionEnvironmentContract":
    """Require the registered runtime contract before a certified sink writes.

    ``env_contract`` remains the optional build-v2 selector.  Every certified
    evaluation, including the legacy-build path, must present the separate
    ``authorization_contract``.
    """
    if type(env_tag) is not str:
        raise TypeError("campaign env_tag は exact str でなければならない")
    if type(clocks_per_us) is not int:
        raise TypeError("campaign clocks_per_us は exact int でなければならない")
    registered = _contract_from_authorization(authorization_contract)
    if type(numactl) not in {list, tuple} or any(type(part) is not str for part in numactl):
        raise CertifiedWriterAuthorizationError(
            "campaign 実行値 numactl は str の list/tuple でなければならない"
        )
    if (env_tag != registered.env_tag
            or clocks_per_us != registered.clocks_per_us
            or tuple(numactl) != registered.numactl):
        raise CertifiedWriterAuthorizationError(
            "campaign execution values do not exactly match "
            "authorization_contract"
        )
    if (
        _site_policy.current_site() == _site_policy.PEGASUS_COMPUTE
    ):
        required_contracts = []
        for row in authorization_contract._activation_state.active_contracts:
            try:
                candidate = _env_contract.GENERATIONS[
                    row.env_tag
                ][row.generation - 1].contract
            except (KeyError, IndexError, TypeError) as exc:
                raise CertifiedWriterAuthorizationError(
                    "authorization receipt state の required contract を解決できない"
                ) from exc
            if candidate.contract_sha256 != row.contract_sha256:
                raise CertifiedWriterAuthorizationError(
                    "authorization receipt state の required contract hash が不一致"
                )
            if candidate.attestation_mode == "required":
                required_contracts.append(candidate)
        if len(required_contracts) != 1 or registered is not required_contracts[0]:
            raise CertifiedWriterAuthorizationError(
                "Pegasus compute では receipt state 内で一意な required "
                "authorization_contract だけを受理する"
            )
    if env_contract is not None:
        if type(env_contract) is not _env_contract.ExecutionEnvironmentContract:
            raise TypeError(
                "build selector env_contract は exact "
                "ExecutionEnvironmentContract でなければならない"
            )
        if env_contract != registered:
            raise CertifiedWriterAuthorizationError(
                "build selector env_contract が authorization_contract と一致しない"
            )
    return registered


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


def receipt_matches_contract(
    receipt: Mapping,
    *,
    env_tag: str,
    contract_sha256: str,
    attestation_mode: str,
    verified_calibration: Optional[_env_attestation.VerifiedCalibration] = None,
) -> bool:
    """Dispatch by ``receipt.schema`` and independently revalidate its binding.

    呼び手は v1 経路でも ``attestation_mode="none"`` を明示する。required
    contract は v1 receipt を受理せず、v2 receipt はさらに
    hash-bound expected profile so recorded comparisons can be recomputed.
    """
    if not isinstance(receipt, Mapping):
        return False
    schema = receipt.get("schema")
    if schema == RECEIPT_SCHEMA:
        if attestation_mode != "none":
            return False
        if receipt.get("env_tag") != env_tag:
            return False
        if receipt.get("contract_sha256") != contract_sha256:
            return False
        attestation = receipt.get("attestation")
        if not isinstance(attestation, Mapping):
            return False
        return set(attestation) == {"hostname", "boot_id", "cpuset", "captured_utc"}
    if schema != RECEIPT_SCHEMA_V2 or attestation_mode != "required":
        return False
    try:
        validate_receipt_v2(receipt)
    except ExecutionGuardError:
        return False
    if receipt.get("env_tag") != env_tag or receipt.get("contract_sha256") != contract_sha256:
        return False
    if not isinstance(verified_calibration, _env_attestation.VerifiedCalibration):
        return False
    if verified_calibration.schema_version != _schema_v2.SCHEMA_VERSION:
        return False
    if receipt.get("attestation_profile_sha256") != (
        verified_calibration.attestation_profile_sha256
    ):
        return False
    try:
        expected_values = _env_attestation.expected_comparison_values(
            verified_calibration.attestation_profile,
        )
    except _env_attestation.AttestationError:
        return False
    comparisons = receipt.get("comparisons")
    if type(comparisons) is not list or len(comparisons) != len(expected_values):
        return False
    seen = set()
    for comparison in comparisons:
        if not isinstance(comparison, Mapping):
            return False
        field = comparison.get("field")
        if field not in expected_values or field in seen:
            return False
        seen.add(field)
        if comparison.get("expected") != expected_values[field]:
            return False
        if not _independent_comparison_passes(
            field, comparison.get("expected"), comparison.get("observed"),
        ):
            return False
    return seen == set(expected_values)


def _independent_comparison_passes(field: str, expected: object, observed: object) -> bool:
    """Consumer-side recomputation, intentionally independent of issuer verdict code."""
    try:
        if field == "cpu.model_name_raw":
            return (
                _env_attestation.normalize_cpu_model_name(expected)  # type: ignore[arg-type]
                == _env_attestation.normalize_cpu_model_name(observed)  # type: ignore[arg-type]
            )
        if field in {"tsc.raw_samples_mhz", "tsc.median_mhz"}:
            if field == "tsc.raw_samples_mhz":
                expected_median = statistics.median(expected)  # type: ignore[arg-type]
                observed_median = statistics.median(observed)  # type: ignore[arg-type]
            else:
                expected_median = float(expected)  # type: ignore[arg-type]
                observed_median = float(observed)  # type: ignore[arg-type]
            return round(expected_median) == round(observed_median)
        if field == "effective_clock.samples_mhz":
            return effective_clock_comparison_passes(expected, observed)
        return expected == observed
    except (TypeError, ValueError, statistics.StatisticsError,
            _env_attestation.AttestationError):
        return False


def effective_clock_comparison_passes(expected: object, observed: object) -> bool:
    """Canonical pure predicate for effective-clock expected/observed values."""
    evaluation = _effective_clock_band_evaluation(
        expected,
        observed,
        collect_all_violations=False,
        catch_overflow=False,
        short_circuit_policy=True,
    )
    return bool(
        evaluation["input_valid"]
        and evaluation["policy_matches"]
        and evaluation["band_pass"]
    )


def _effective_clock_band_evaluation(
    expected: object,
    observed: object,
    *,
    collect_all_violations: bool = True,
    catch_overflow: bool = True,
    short_circuit_policy: bool = False,
) -> dict:
    """Evaluate shape, policy identity, and arbitrary-width band diagnostics.

    ``band_pass`` deliberately preserves the permissive historical mathematics:
    numeric strings and bool samples remain float-coercible, arbitrary tolerance
    widths remain evaluable, and expected/observed sample counts need not match.
    Diagnostics collect every violation; the legacy math caller requests first-
    violation short-circuiting and leaves ``OverflowError`` behavior unchanged.
    """
    evaluation = {
        "input_valid": False,
        "policy_matches": False,
        "band_pass": False,
        "median_mhz": None,
        "lower_mhz": None,
        "upper_mhz": None,
        "out_of_band_count": None,
        "violations": [],
        "evaluation_error": None,
    }
    try:
        if not isinstance(expected, Mapping):
            return evaluation
        expected_keys = expected.keys()
        if (len(expected_keys) != 2
                or "samples_mhz" not in expected_keys
                or "tolerance_pct" not in expected_keys):
            return evaluation
        if not isinstance(observed, Mapping):
            return evaluation
        observed_keys = observed.keys()
        if len(observed_keys) != 1 or "samples_mhz" not in observed_keys:
            return evaluation
        evaluation["input_valid"] = True
        tolerance = expected.get("tolerance_pct")
        evaluation["policy_matches"] = bool(
            type(tolerance) in (int, float)
            and tolerance
            == effective_clock_policy.EFFECTIVE_CLOCK_TOLERANCE_PCT
        )
        if short_circuit_policy and not evaluation["policy_matches"]:
            return evaluation
        expected_samples = expected.get("samples_mhz")
        observed_samples = observed.get("samples_mhz")
    except Exception as exc:
        evaluation["input_valid"] = False
        evaluation["evaluation_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        return evaluation

    try:
        if (type(expected_samples) is not list or type(observed_samples) is not list
                or not expected_samples or not observed_samples
                or type(tolerance) not in (int, float)):
            evaluation["input_valid"] = False
            return evaluation
        expected_median = float(statistics.median(expected_samples))
        allowed_delta = abs(expected_median) * float(tolerance) / 100.0
        lower = expected_median - allowed_delta
        upper = expected_median + allowed_delta
        evaluation.update({
            "median_mhz": expected_median if math.isfinite(expected_median) else None,
            "lower_mhz": lower if math.isfinite(lower) else None,
            "upper_mhz": upper if math.isfinite(upper) else None,
        })
        for sample_index, sample in enumerate(observed_samples):
            sample_mhz = float(sample)
            if lower <= sample_mhz <= upper:
                continue
            if sample_mhz < lower:
                direction = "below"
                outside_by = lower - sample_mhz
            elif sample_mhz > upper:
                direction = "above"
                outside_by = sample_mhz - upper
            else:
                direction = "indeterminate"
                outside_by = None
            deviation = sample_mhz - expected_median
            evaluation["violations"].append({
                "sample_index": sample_index,
                "sample_mhz": sample_mhz if math.isfinite(sample_mhz) else None,
                "direction": direction,
                "deviation_from_median_mhz": (
                    deviation if math.isfinite(deviation) else None
                ),
                "outside_by_mhz": (
                    outside_by
                    if outside_by is None or math.isfinite(outside_by)
                    else None
                ),
            })
            if not collect_all_violations:
                break
        evaluation["out_of_band_count"] = len(evaluation["violations"])
        evaluation["band_pass"] = not evaluation["violations"]
        return evaluation
    except OverflowError as exc:
        if not catch_overflow:
            raise
        evaluation["input_valid"] = False
        evaluation["band_pass"] = False
        evaluation["out_of_band_count"] = None
        evaluation["evaluation_error"] = {
            "type": type(exc).__name__,
            "message": str(exc),
        }
        return evaluation
    except (TypeError, ValueError, statistics.StatisticsError):
        evaluation["input_valid"] = False
        evaluation["band_pass"] = False
        evaluation["out_of_band_count"] = None
        evaluation["violations"] = []
        return evaluation


def effective_clock_comparison_diagnostics(
    expected: object, observed: object,
) -> dict:
    """Project structured clock-band diagnostics without granting admission."""
    return _effective_clock_band_evaluation(expected, observed)


def _effective_clock_band_math_passes(expected: object, observed: object) -> bool:
    """Arbitrary-width clock-band mathematics; never a public admission gate."""
    return bool(_effective_clock_band_evaluation(
        expected,
        observed,
        collect_all_violations=False,
        catch_overflow=False,
        short_circuit_policy=False,
    )["band_pass"])


def _json_value(value: object, *, field: str) -> None:
    """receipt 比較値が finite JSON value であることを再帰検査する。"""
    if value is None or type(value) in (str, bool, int):
        return
    if type(value) is float:
        if math.isfinite(value):
            return
        raise ExecutionGuardError(f"{field} に非有限 float がある")
    if type(value) is list:
        for index, item in enumerate(value):
            _json_value(item, field=f"{field}[{index}]")
        return
    if isinstance(value, Mapping):
        for key, item in value.items():
            if type(key) is not str:
                raise ExecutionGuardError(f"{field} に str でない key がある")
            _json_value(item, field=f"{field}.{key}")
        return
    raise ExecutionGuardError(f"{field} が JSON value でない: {type(value).__name__}")


def validate_receipt_v2(receipt: Mapping) -> None:
    """execution receipt v2 の exact shape と全比較 pass を fail-closed 検証する。

    v1 の ``build_receipt`` とは独立した reader 契約であり、v2 発行は必ず
    ``attest_and_build_receipt`` を通る。
    """
    if not isinstance(receipt, Mapping):
        raise ExecutionGuardError("execution receipt v2 が Mapping でない")
    expected_keys = {
        "schema", "env_tag", "contract_sha256", "attestation_profile_sha256",
        "captured_utc", "probe", "comparisons",
    }
    actual_keys = set(receipt)
    if actual_keys != expected_keys:
        raise ExecutionGuardError(
            "execution receipt v2 の key 集合が不一致 "
            f"(欠落={sorted(expected_keys - actual_keys)} "
            f"未知={sorted(actual_keys - expected_keys, key=repr)})"
        )
    if receipt["schema"] != RECEIPT_SCHEMA_V2:
        raise ExecutionGuardError(f"receipt.schema が {RECEIPT_SCHEMA_V2!r} でない")
    env_tag = receipt["env_tag"]
    if type(env_tag) is not str or _SLUG_RE.fullmatch(env_tag) is None:
        raise ExecutionGuardError("receipt.env_tag が canonical slug でない")
    for field in ("contract_sha256", "attestation_profile_sha256"):
        value = receipt[field]
        if type(value) is not str or _HEX64_RE.fullmatch(value) is None:
            raise ExecutionGuardError(f"receipt.{field} が 64 lower-hex でない")
    _validate_utc_iso(receipt["captured_utc"], field="receipt.captured_utc")
    probe = receipt["probe"]
    if not isinstance(probe, Mapping) or set(probe) != {"method", "version"}:
        raise ExecutionGuardError("receipt.probe が exact {method, version} でない")
    for field in ("method", "version"):
        if type(probe[field]) is not str or not probe[field]:
            raise ExecutionGuardError(f"receipt.probe.{field} が非空 str でない")
    comparisons = receipt["comparisons"]
    if type(comparisons) is not list or not comparisons:
        raise ExecutionGuardError("receipt.comparisons が空でない list でない")
    seen_fields = set()
    comparison_keys = {"field", "expected", "observed", "verdict"}
    for index, comparison in enumerate(comparisons):
        if not isinstance(comparison, Mapping) or set(comparison) != comparison_keys:
            raise ExecutionGuardError(
                f"receipt.comparisons[{index}] の key 集合が exact でない"
            )
        field = comparison["field"]
        if type(field) is not str or not field or field in seen_fields:
            raise ExecutionGuardError(
                f"receipt.comparisons[{index}].field が空または重複"
            )
        seen_fields.add(field)
        if field == "effective_clock.samples_mhz":
            expected_clock = comparison["expected"]
            observed_clock = comparison["observed"]
            if (not isinstance(expected_clock, Mapping)
                    or set(expected_clock) != {"samples_mhz", "tolerance_pct"}):
                raise ExecutionGuardError(
                    f"receipt.comparisons[{index}].expected clock key 集合が exact でない"
                )
            if (not isinstance(observed_clock, Mapping)
                    or set(observed_clock) != {"samples_mhz"}):
                raise ExecutionGuardError(
                    f"receipt.comparisons[{index}].observed clock key 集合が exact でない"
                )
        _json_value(comparison["expected"], field=f"comparisons[{index}].expected")
        _json_value(comparison["observed"], field=f"comparisons[{index}].observed")
        if comparison["verdict"] != "pass":
            raise ExecutionGuardError(
                f"receipt.comparisons[{index}].verdict が 'pass' でない"
            )


def attest_and_build_receipt(
    contract: "_env_contract.ExecutionEnvironmentContract",
    verified_calibration: _env_attestation.VerifiedCalibration,
    *,
    probe_fn: Callable[[], _schema_v2.ObservedAttestationProfile] = _env_attestation.probe,
    now_fn: Optional[Callable[[], object]] = None,
) -> dict:
    """Atomically attest a required contract and issue its receipt.

    ``mode=none`` delegates to the unchanged v1 builder.  Required mode has no
    receipt-producing path unless the hash-bound calibration profile and every
    production comparator verdict pass.
    """
    if not isinstance(contract, _env_contract.ExecutionEnvironmentContract):
        raise ExecutionGuardError("contract の型が不正")
    if contract.attestation_mode == "none":
        return build_receipt(contract, now_fn=now_fn)  # type: ignore[arg-type]
    if contract.attestation_mode != "required":
        raise ExecutionGuardError(
            f"未知の attestation_mode: {contract.attestation_mode!r}"
        )
    if not isinstance(verified_calibration, _env_attestation.VerifiedCalibration):
        raise ExecutionGuardError("verified_calibration の型が不正")
    if verified_calibration.schema_version != _schema_v2.SCHEMA_VERSION:
        raise ExecutionGuardError("required contract に calibration/v2 が束縛されていない")
    if verified_calibration.sha256 != contract.calibration_ref.sha256:
        raise ExecutionGuardError("verified calibration sha256 が contract ref と不一致")
    if verified_calibration.attestation_profile_sha256 is None:
        raise ExecutionGuardError("verified calibration に profile sha256 がない")
    if not callable(probe_fn):
        raise ExecutionGuardError("probe_fn が callable でない")
    comparison_now = now_fn or (lambda: dt.datetime.now(dt.timezone.utc))
    try:
        captured_value = comparison_now()
        captured_utc = _utc_iso_text(captured_value, field="receipt.captured_utc")
        observed = probe_fn()
        comparisons = _env_attestation.compare_profiles(
            verified_calibration.attestation_profile,
            observed,
            now_fn=lambda: captured_value,
        )
    except _env_attestation.AttestationError as exc:
        raise ExecutionGuardError(f"strict attestation probe failed: {exc}") from exc
    failures = [item for item in comparisons if item.get("verdict") != "pass"]
    if failures:
        raise ExecutionGuardError(
            "attestation comparisons failed: "
            + json.dumps(failures, sort_keys=True, separators=(",", ":"), ensure_ascii=True)
        )
    receipt = {
        "schema": RECEIPT_SCHEMA_V2,
        "env_tag": contract.env_tag,
        "contract_sha256": contract.contract_sha256,
        "attestation_profile_sha256": verified_calibration.attestation_profile_sha256,
        "captured_utc": captured_utc,
        "probe": {
            "method": _env_attestation.PROBE_METHOD,
            "version": _env_attestation.PROBE_VERSION,
        },
        "comparisons": comparisons,
    }
    validate_receipt_v2(receipt)
    return receipt


def _validate_utc_iso(value: object, *, field: str) -> None:
    if type(value) is not str or not value:
        raise ExecutionGuardError(f"{field} は非空の UTC ISO 文字列でなければならない")
    parse_text = value[:-1] + "+00:00" if value.endswith("Z") else value
    try:
        parsed = dt.datetime.fromisoformat(parse_text)
    except ValueError as exc:
        raise ExecutionGuardError(f"{field} は UTC ISO 形式でなければならない") from exc
    if parsed.tzinfo is None or parsed.utcoffset() != dt.timedelta(0):
        raise ExecutionGuardError(f"{field} は UTC ISO 形式でなければならない")


def _utc_iso_text(value: object, *, field: str) -> str:
    if isinstance(value, dt.datetime):
        text = value.isoformat()
    elif type(value) is str:
        text = value
    else:
        isoformat = getattr(value, "isoformat", None)
        if not callable(isoformat):
            raise ExecutionGuardError(f"{field} を now_fn の戻り値から生成できない")
        text = isoformat()
    _validate_utc_iso(text, field=field)
    return text
