# -*- coding: utf-8 -*-
"""D12 の層3材料レポートを WAL と whiteboard から再生成する。

使い方: ``python3 orchestrator/campaign/layer3_report.py <campaign_dir> <out_json>``。
これは既存の構造化記録だけを完全射影する。loop campaign の whiteboard に加え、
``loop_state.json`` を持たない sweep campaign も whiteboard の provenance を明示して扱う。
入力由来の hash multiset と、構築済み
report 本体を再走査して得る multiset を独立に比較し、view の source_ref も一次配置を
参照することを検査する。未知 stage、重複、脱落、参照不能、読めない入力、schema
不適合はいずれも例外にし、部分レポートを出力しない。

``agent_outputs`` は役割出力の全文を保持し、``mechanism_hypotheses`` は critic の
帰属記録を逐語で射影する。機序仮説は LLM の帰属記録であり、機序の実証ではない。
noise floor は within_run = 1 測定の品質、between_run = run 間比較の採否 floor として区別する（p2_2.py の A2 注記と同じ区別）。
abort variant も commit-event-absent のため rejects に載り、詳細理由は aborts view が保持する。
schema v1/v2 で生成済みの実レポートは、generator sha を内包する記録済み artifact
であり、v3 への更新のために再生成しない。schema reader は v2 を引き続き受理するが、
新規生成は admission decision receipt を必須にした v3 だけを発行する。
新規 v3 は常に ``acceptance_receipt`` と ``certifying_input`` を持つ。通常の
``build_report`` / ``render`` では前者が null、後者が false であり、受入前の材料
report にすぎないことを機械可読に示す。既存 v3 reader では両 field の欠落を
非認証入力として受理する。
``generated_from_head`` は provenance であり、決定論比較の対象外である（HEAD が動けば
変わる）。
D1537 の ``SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS`` は consumer-local な
exact identity 集合であり、T-419 U-1/U-2 で登録簿から外れたときに削除する。
契約 ref がこの集合に完全一致する campaign では within-run 候補をすべて空にする。
これは samples/tolerance を読んで自己整合性述語を再検査するものではない。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import stat
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import jsonschema
from pathlib import Path, PurePosixPath

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

SCHEMA_VERSION = "layer3-material-report/v3"
LEGACY_SCHEMA_VERSION = "layer3-material-report/v2"
GENERATOR_IDENTITY = "orchestrator.campaign.layer3_report"
STAGES = frozenset(("build_start", "build_done", "verify_done", "bench_done", "commit", "abort"))
_HERE = Path(__file__).resolve().parent

from ..calibrator import perf_preflight as _perf_preflight  # noqa: E402
from . import (  # noqa: E402
    agent_outputs as _agent_outputs,
    campaign_lock,
    env_contract,
    p3_s4_loop,
    s8c_acceptance_receipt,
    trigger_gate_binding,
    wal,
)
from .artifact_admission import (  # noqa: E402
    ArtifactAdmissionError,
    CampaignReadPurpose,
    CampaignVerifierEpoch,
    require_admitted_campaign,
    require_certified_commit_evidence,
)
from .genome import protocol_from_floor_genome  # noqa: E402
from .layout import CampaignLayout  # noqa: E402
from .model import WalRecord  # noqa: E402


_SCHEMA_PATH = _HERE / "layer3_schema.json"
_DEFAULT_OUTPUT_ROOT = _HERE.parents[1] / "output"
SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS: frozenset[tuple[str, str]] = frozenset({
    (
        "output/env/pegasus/calibration/registered/"
        "calibration-753f535a8d024727.json",
        "753f535a8d02472781bb51b8f56cc383112a791ff2a1e80963039e83bcce5a49",
    ),
})


class Layer3ReportError(RuntimeError):
    """材料レポートの完全性または再現性の入力契約違反。"""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def canonical_record_ref(kind: str, record: Mapping[str, Any]) -> str:
    """WAL/whiteboard/agent-output record の内容ハッシュ付き source-ref を返す。"""
    if kind not in ("wal", "wb", "ao"):
        raise Layer3ReportError("source-ref kind が不正")
    if kind == "ao":
        try:
            return "ao:" + _agent_outputs.canonical_sha256(record)
        except _agent_outputs.AgentOutputError as exc:
            raise Layer3ReportError("agent output canonical JSON が不正") from exc
    return "%s:%s" % (kind, hashlib.sha256(_canonical_bytes(record)).hexdigest())


def _read_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Layer3ReportError("JSON を読めない: %s" % path) from exc


def _read_campaign_lock(
    path: Path, *, purpose: CampaignReadPurpose,
) -> campaign_lock.DecodedCampaignLock | campaign_lock.DecodedHistoricalCampaignLock:
    """v1/v2 lock を検証し、report 投影用の inner identity を返せる形にする。

    HISTORICAL_RAW は歴史 decoder、それ以外の有効な purpose は通常 decoder を使う。
    """
    if type(purpose) is not CampaignReadPurpose:
        raise TypeError(
            "purpose は exact CampaignReadPurpose.CERTIFIED_ACCEPTANCE "
            "または HISTORICAL_RAW が必要"
        )
    try:
        text = path.read_text(encoding="utf-8")
        if purpose is CampaignReadPurpose.HISTORICAL_RAW:
            return campaign_lock.decode_historical_campaign_lock(text)
        return campaign_lock.decode_campaign_lock(text)
    except (OSError, UnicodeDecodeError) as exc:
        raise Layer3ReportError("campaign.lock を読めない: %s" % path) from exc
    except campaign_lock.CampaignLockCodecError as exc:
        raise Layer3ReportError("campaign.lock schema が不正") from exc


def _assert_unique_refs(kind: str, records: Sequence[Mapping[str, Any]], label: str) -> None:
    refs = [canonical_record_ref(kind, record) for record in records]
    if len(refs) != len(set(refs)):
        raise Layer3ReportError("%s に canonical hash の完全重複がある" % label)


def _read_agent_outputs(path: Path) -> Tuple[Optional[List[Dict[str, Any]]], Optional[str]]:
    """None denotes absence; reject append races across the shared reader."""
    try:
        mode = path.lstat().st_mode
    except FileNotFoundError:
        return None, None
    except OSError as exc:
        raise Layer3ReportError("agent outputs を読めない") from exc
    if not stat.S_ISREG(mode):
        raise Layer3ReportError("agent outputs が通常ファイルでない")
    try:
        before = _sha256_file(path)
        envelopes = _agent_outputs.read_agent_outputs(path)
        after = _sha256_file(path)
    except (_agent_outputs.AgentOutputError, OSError) as exc:
        raise Layer3ReportError("agent outputs を読めない: %s" % exc) from exc
    if before != after:
        raise Layer3ReportError("agent outputs bytes changed during read")
    return envelopes, before


def _mechanism_view(records: Sequence[Mapping[str, Any]],
                    envelopes: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    wal_refs = {canonical_record_ref("wal", record) for record in records}
    variants = {record["variant"] for record in records if record["stage"] == "commit"}
    result = []
    for env in envelopes:
        try:
            _agent_outputs.validate_envelope(env)
        except _agent_outputs.AgentOutputError as exc:
            raise Layer3ReportError("agent output envelope が不正") from exc
        if env["variant"] is not None and env["variant"] not in variants:
            raise Layer3ReportError("agent output variant に WAL commit がない")
        payload = env["payload"]
        if any(ref not in wal_refs for ref in payload["refs"]):
            raise Layer3ReportError("agent output refs が一次 WAL を参照しない")
        if env["stage"] != "critic_attributed":
            continue
        output = payload["output"]
        raw = output["raw_markdown"]
        headings = list(re.finditer(r"^## ([^\r\n]+)\r?$", raw, re.MULTILINE))
        for name in ("attribution", "recommend", "avoid", "uncertainty"):
            matches = [i for i, heading in enumerate(headings) if heading[1] == name]
            if len(matches) != 1:
                raise Layer3ReportError("critic heading が欠落または重複: " + name)
            index = matches[0]
            end = headings[index + 1].start() if index + 1 < len(headings) else len(raw)
            if raw[headings[index].end():end].strip() != output[name]:
                raise Layer3ReportError("critic raw_markdown と節が一致しない: " + name)
        result.append({
            "variant": env["variant"], "attribution": output["attribution"],
            "source_ref": canonical_record_ref("ao", env),
            "refs": payload["refs"], "digest_sha256": payload["digest_sha256"],
        })
    return sorted(result, key=lambda row: row["source_ref"])


def _read_wal(path: Path) -> List[Dict[str, Any]]:
    if not path.is_file():
        raise Layer3ReportError("WAL が存在しない: %s" % path)
    records: List[Dict[str, Any]] = []
    try:
        for lineno, line, _is_last in wal.iter_lines(path):
            try:
                parsed = wal.parse_line(line)
            except (json.JSONDecodeError, wal.WalLineError) as exc:
                raise Layer3ReportError(
                    "WAL record が不正: line %d: %s: %s"
                    % (lineno, type(exc).__name__, exc)
                ) from exc
            record = {
                "variant": parsed.variant, "stage": parsed.stage,
                "env_tag": parsed.env_tag, "ts": parsed.ts,
                "payload": parsed.payload,
            }
            if record["stage"] == trigger_gate_binding.WAL_RECORD_STAGE:
                continue
            if record["stage"] not in STAGES:
                raise Layer3ReportError("未知の WAL stage: %r" % record["stage"])
            records.append(record)
    except wal.WalFramingError as exc:
        raise Layer3ReportError(
            "WAL framing が不正: %s: %s" % (path, exc)
        ) from exc
    except (OSError, UnicodeDecodeError) as exc:
        raise Layer3ReportError("WAL を読めない: %s" % path) from exc
    if not records:
        raise Layer3ReportError("WAL が空である")
    _assert_unique_refs("wal", records, "WAL")
    return records


def _sha256_file(path: Path) -> str:
    digest = hashlib.sha256()
    try:
        with path.open("rb") as stream:
            for chunk in iter(lambda: stream.read(1024 * 1024), b""):
                digest.update(chunk)
    except OSError as exc:
        raise Layer3ReportError("artifact を読めない: %s" % path) from exc
    return digest.hexdigest()


def _event_key(record: Mapping[str, Any]) -> tuple:
    return (record["ts"], canonical_record_ref("wal", record))


def _git_head(campaign_dir: Path) -> str:
    try:
        head = subprocess.check_output(
            ["git", "-C", str(campaign_dir), "rev-parse", "HEAD"], text=True,
            stderr=subprocess.DEVNULL).strip()
    except (OSError, subprocess.CalledProcessError) as exc:
        raise Layer3ReportError("git HEAD を取得できない") from exc
    if len(head) != 40 or any(char not in "0123456789abcdef" for char in head):
        raise Layer3ReportError("git HEAD が40桁hexでない")
    return head


def _resolve_generated_from_head(
    campaign_dir: Path,
    decoded_lock: campaign_lock.DecodedCampaignLock | campaign_lock.DecodedHistoricalCampaignLock,
    generated_from_head: Optional[str],
) -> str:
    if generated_from_head is not None:
        return generated_from_head
    try:
        return _git_head(campaign_dir)
    except Layer3ReportError:
        if campaign_dir.is_relative_to(_DEFAULT_OUTPUT_ROOT.parent):
            raise
        if decoded_lock.authority is not None:
            return decoded_lock.authority.contract_loader_commit
        raise


def _artifact_refs(
        campaign_dir: Path, *,
        knowledge_receipt_sha256: Optional[str] = None,
) -> List[Dict[str, str]]:
    files = sorted(path for path in campaign_dir.rglob("*") if path.is_file())
    if not files:
        raise Layer3ReportError("campaign に artifact がない")
    refs = [
        {
            "path": str(path.relative_to(campaign_dir)),
            "sha256": _sha256_file(path),
        }
        for path in files
    ]
    if knowledge_receipt_sha256 is not None and not any(
            ref == {
                "path": wal.KNOWLEDGE_RECEIPT_FILENAME,
                "sha256": knowledge_receipt_sha256,
            }
            for ref in refs):
        raise Layer3ReportError(
            "knowledge receipt bytes changed after provenance validation"
        )
    return refs


def _report_primary_refs(report: Mapping[str, Any]) -> Counter:
    """完成した report 本体の一次配置だけから source-ref multiset を再計算する。"""
    refs: Counter = Counter()
    for row in report.get("variants", ()):
        if not isinstance(row, Mapping):
            raise Layer3ReportError("variants 行が object でない")
        for event in row.get("events", ()):
            if not isinstance(event, Mapping):
                raise Layer3ReportError("variants.events が object でない")
            refs[canonical_record_ref("wal", event)] += 1
    for item in report.get("whiteboard", ()):
        if not isinstance(item, Mapping):
            raise Layer3ReportError("whiteboard 行が object でない")
        refs[canonical_record_ref("wb", item)] += 1
    for env in report.get("agent_outputs", ()):
        refs[canonical_record_ref("ao", env)] += 1
    return refs


def _assert_bijection(records: Sequence[Mapping[str, Any]], whiteboard: Sequence[Mapping[str, Any]],
                      report: Mapping[str, Any], *,
                      agent_outputs: Optional[Sequence[Mapping[str, Any]]] = None) -> None:
    """入力と本体一次配置を独立比較し、view の参照整合も fails-closed で強制する。"""
    expected = Counter(canonical_record_ref("wal", item) for item in records)
    expected.update(canonical_record_ref("wb", item) for item in whiteboard)
    expected.update(canonical_record_ref("ao", env) for env in (agent_outputs or ()))
    actual = _report_primary_refs(report)
    if actual != expected:
        raise Layer3ReportError("source-ref multiset が入力 WAL/whiteboard/AO と report 本体で一致しない")
    source_refs = Counter(report.get("source_refs", ()))
    if source_refs != actual:
        raise Layer3ReportError("source_refs 区画が report 本体走査結果と一致しない")
    if report.get("mechanism_hypotheses", []) != _mechanism_view(records, agent_outputs or ()):
        raise Layer3ReportError("mechanism_hypotheses が独立再射影と一致しない")
    provenance = "absent" if agent_outputs is None else "agent_outputs"
    if report.get("mechanism_hypotheses_provenance", "absent") != provenance:
        raise Layer3ReportError("mechanism_hypotheses_provenance が入力と一致しない")
    primary_wal_refs = {ref for ref in actual if ref.startswith("wal:")}
    for section in ("runs", "verifications", "rejects", "aborts"):
        for row in report.get(section, ()):
            if not isinstance(row, Mapping) or row.get("source_ref") not in primary_wal_refs:
                raise Layer3ReportError("%s の source_ref が一次配置を参照しない" % section)


def _validate_certifying_prerequisites(report: Mapping[str, Any]) -> None:
    certifying_input = report.get("certifying_input", False)
    acceptance_receipt = report.get("acceptance_receipt")
    if (certifying_input is True) != (acceptance_receipt is not None):
        raise Layer3ReportError(
            "certifying_input=true と acceptance_receipt 非 null は同値必須"
        )
    admission_decision = report.get("admission_decision")
    if certifying_input is True and (
        not isinstance(admission_decision, Mapping)
        or admission_decision.get("admission_status") != "admitted"
    ):
        raise Layer3ReportError(
            "certifying_input=true には admission_status=admitted が必須"
        )


def _validate_schema(report: Mapping[str, Any]) -> None:
    campaign_verifier_epoch = report.get("campaign_verifier_epoch")
    if (
        report.get("certifying_input") is True
        and isinstance(campaign_verifier_epoch, Mapping)
        and "verifier_assessment_basis" in campaign_verifier_epoch
    ):
        _validate_certifying_prerequisites(report)
    schema = _read_json(_SCHEMA_PATH)
    if report.get("schema_version") == LEGACY_SCHEMA_VERSION:
        # A v2 artifact is immutable historical evidence.  Derive its reader
        # schema from v3 by removing only the forward admission receipt.
        schema = json.loads(json.dumps(schema))
        schema["properties"]["schema_version"] = {"const": LEGACY_SCHEMA_VERSION}
        schema["required"].remove("admission_decision")
        schema["properties"].pop("admission_decision")
        schema["properties"].pop("knowledge_provenance")
    try:
        jsonschema.Draft7Validator(schema).validate(report)
    except jsonschema.ValidationError as exc:
        raise Layer3ReportError("layer3 schema 検証に失敗") from exc
    for run in report.get("runs", ()):
        observation = run.get("perf_observation")
        if observation is None:
            continue
        try:
            _perf_preflight.validate_perf_observation(
                observation,
                run_cmd=run.get("run_cmd"),
                leading_indicators=run.get("leading_indicators"),
            )
        except _perf_preflight.PerfPreflightError as exc:
            raise Layer3ReportError(
                "layer3 perf observation 共有検証に失敗"
            ) from exc
    _validate_certifying_prerequisites(report)


def _epoch_projection(
        epoch: CampaignVerifierEpoch, *,
        verifier_assessment_basis: str | None = None,
) -> Dict[str, str]:
    projection = {
        "campaign_verifier_epoch": epoch.campaign_verifier_epoch,
        "state": epoch.state,
        "reason_code": epoch.reason_code,
        "identity_scope": epoch.identity_scope,
        "excluded_scope": epoch.excluded_scope,
    }
    if verifier_assessment_basis is not None:
        projection["verifier_assessment_basis"] = verifier_assessment_basis
    return projection


def _variant_rows(records: Sequence[Mapping[str, Any]]) -> List[Dict[str, Any]]:
    variants: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for record in sorted(records, key=_event_key):
        variants[record["variant"]].append(dict(record))
    rows = []
    for name in sorted(variants):
        events = variants[name]
        starts = [event for event in events if event["stage"] == "build_start"]
        genomes = sorted({event["payload"].get("genome") for event in starts
                          if isinstance(event["payload"].get("genome"), str)})
        tokens = sorted({event["payload"].get("src_token") for event in starts
                         if isinstance(event["payload"].get("src_token"), str)})
        rows.append({"variant": name, "genome": genomes, "src_token": tokens, "events": events})
    return rows


def _campaign_protocol(records: Sequence[Mapping[str, Any]]) -> Optional[str]:
    """WAL build_start の canonical genome が示す一意な protocol を返す。"""
    starts = [record for record in records if record.get("stage") == "build_start"]
    if not starts:
        return None
    protocols = set()
    for record in starts:
        payload = record.get("payload")
        if not isinstance(payload, Mapping):
            return None
        try:
            protocols.add(protocol_from_floor_genome(payload.get("genome")))
        except ValueError:
            return None
    if len(protocols) != 1:
        return None
    return next(iter(protocols))


def _contract_calibration_pin(
    decoded_lock: campaign_lock.DecodedCampaignLock | campaign_lock.DecodedHistoricalCampaignLock,
    env_tag: str,
) -> Tuple[Optional[env_contract.CalibrationRef], Optional[Dict[str, Any]]]:
    """Resolve a v2 lock pin, or record why it does not apply to this WAL env."""
    if decoded_lock.authority is None:
        return None, None
    try:
        entry = env_contract.resolve_by_contract_sha256(
            decoded_lock.authority.environment_contract_sha256,
        )
    except env_contract.EnvContractError as exc:
        raise Layer3ReportError(
            "campaign lock の environment contract を解決できない"
        ) from exc
    if entry.contract.env_tag != env_tag:
        return None, {
            "status": "authority-env-tag-mismatch",
            "authority_env_tag": entry.contract.env_tag,
            "campaign_env_tag": env_tag,
        }
    contract_pin = entry.contract.calibration_ref
    return contract_pin, {
        "status": "candidate",
        "path": contract_pin.path,
        "sha256": contract_pin.sha256,
    }


def _validated_pin_path(
    calibration_dir: Path,
    contract_pin: env_contract.CalibrationRef,
) -> Optional[Path]:
    """Map a contract pin's calibration suffix into the active output root."""
    logical_calibration_dir = Path(calibration_dir)
    resolved_calibration_dir = calibration_dir.resolve()
    relative_pin = PurePosixPath(contract_pin.path)
    if relative_pin.is_absolute():
        raise Layer3ReportError("contract calibration pin が repo 相対 path でない")
    if ".." in relative_pin.parts:
        raise Layer3ReportError("contract calibration pin に .. 成分がある")
    if (logical_calibration_dir.name != "calibration"
            or logical_calibration_dir.parent.parent.name != "env"):
        raise Layer3ReportError(
            "calibration directory から当該 env_tag を解決できない"
        )
    env_tag = logical_calibration_dir.parent.name
    expected_prefix = ("output", "env", env_tag, "calibration")
    if (len(relative_pin.parts) < len(expected_prefix)
            or relative_pin.parts[:len(expected_prefix)] != expected_prefix):
        raise Layer3ReportError(
            "contract calibration pin が当該 env の calibration directory 外にある"
        )
    suffix = relative_pin.parts[len(expected_prefix):]
    if not suffix:
        raise Layer3ReportError("contract calibration pin が通常 file でない")
    unresolved_pin = logical_calibration_dir.joinpath(*suffix)
    try:
        pin_path = unresolved_pin.resolve(strict=False)
    except (OSError, RuntimeError) as exc:
        raise Layer3ReportError(
            "contract calibration pin を解決できない: %s" % unresolved_pin
        ) from exc
    try:
        pin_path.relative_to(resolved_calibration_dir)
    except ValueError as exc:
        raise Layer3ReportError(
            "contract calibration pin が当該 env の calibration directory 外にある"
        ) from exc
    try:
        unresolved_pin.stat()
    except FileNotFoundError:
        if unresolved_pin.is_symlink():
            raise Layer3ReportError("contract calibration pin が通常 file でない")
        return None
    except OSError as exc:
        raise Layer3ReportError(
            "contract calibration pin を検査できない: %s" % unresolved_pin
        ) from exc
    try:
        pin_path = unresolved_pin.resolve(strict=True)
    except (OSError, RuntimeError) as exc:
        raise Layer3ReportError(
            "contract calibration pin を解決できない: %s" % unresolved_pin
        ) from exc
    try:
        pin_path.relative_to(resolved_calibration_dir)
    except ValueError as exc:
        raise Layer3ReportError(
            "contract calibration pin が当該 env の calibration directory 外にある"
        ) from exc
    if not pin_path.is_file():
        raise Layer3ReportError("contract calibration pin が通常 file でない")
    actual_sha256 = _sha256_file(pin_path)
    if actual_sha256 != contract_pin.sha256:
        raise Layer3ReportError(
            "contract calibration pin の SHA-256 が不一致: "
            f"expected={contract_pin.sha256} actual={actual_sha256}"
        )
    return pin_path


def _floor_protocol_and_basis(
    doc: Mapping[str, Any], kind: str, path: Path,
) -> Tuple[str, str]:
    if "genome" in doc:
        try:
            protocol = protocol_from_floor_genome(doc["genome"])
        except ValueError as exc:
            raise Layer3ReportError(
                "floor calibration の genome が canonical でない: %s" % path
            ) from exc
        basis = (
            "receipt-derived-build-argv"
            if "acquisition_receipt" in doc
            else "canonical-floor-genome"
        )
        return protocol, basis
    if kind == "within_run":
        return "silo", "genome-absent-legacy-record"
    raise Layer3ReportError(
        "between-run floor calibration に canonical genome がない: %s" % path
    )


def _view_row(event: Mapping[str, Any]) -> Dict[str, Any]:
    payload = {
        key: value for key, value in event["payload"].items()
        if key not in {
            "build_attempt_id", "build_admission_receipt_sha256",
        }
    }
    return {**payload, "variant": event["variant"],
            "source_ref": canonical_record_ref("wal", event)}


def _calibration_floors(calibration_dir: Path, records: Any, threads: Any,
                        workload: Any, *, protocol: Optional[str],
                        contract_pin: Optional[env_contract.CalibrationRef] = None,
                        contract_pin_search: Optional[Mapping[str, Any]] = None,
                        ) -> Tuple[Dict[str, Dict[str, Any]],
                                   Dict[str, Dict[str, Any]]]:
    """floor を kind 別に分類・照合し、report 値と完全な検索詳細を返す。"""
    direct_paths = (
        sorted(path.resolve() for path in calibration_dir.glob("*.json"))
        if calibration_dir.is_dir() else []
    )
    path_sources = {path: True for path in direct_paths}
    pin_search = (
        dict(contract_pin_search) if contract_pin_search is not None else None
    )
    if contract_pin is not None:
        pin_path = _validated_pin_path(calibration_dir, contract_pin)
        if pin_search is None:
            pin_search = {
                "status": "candidate",
                "path": contract_pin.path,
                "sha256": contract_pin.sha256,
            }
        if pin_path is None:
            pin_search["status"] = "pin-file-missing"
        else:
            pin_search["status"] = "validated"
            path_sources[pin_path] = path_sources.get(pin_path, False)
    exclude_within_run = (
        contract_pin is not None
        and (contract_pin.path, contract_pin.sha256)
        in SELF_INCONSISTENT_WITHIN_RUN_CALIBRATIONS
    )
    paths = sorted(path_sources)
    block_for_kind = {"within_run": "noise_floor", "between_run": "between_run"}
    candidates: Dict[str, List[Tuple[
        Path, Dict[str, Any], Any, Any, Dict[str, Any], str, str,
    ]]] = {
        kind: [] for kind in block_for_kind
    }
    skipped_no_floor_block = []
    for path in paths:
        doc = _read_json(path)
        if not isinstance(doc, dict):
            raise Layer3ReportError("calibration record が object でない: %s" % path)

        kinds = [kind for kind, block in block_for_kind.items()
                 if isinstance(doc.get(block), dict)]
        if len(kinds) > 1:
            raise Layer3ReportError("calibration record が複数 kind の floor block を持つ: %s" % path)
        if not kinds:
            skipped_no_floor_block.append(path.name)
            continue
        kind = kinds[0]
        if kind == "between_run" and not path_sources[path]:
            continue

        if "records" in doc:
            doc_records = doc["records"]
        else:
            saturation = doc.get("saturation")
            if not isinstance(saturation, dict) or "records" not in saturation:
                raise Layer3ReportError("floor calibration に records がない: %s" % path)
            doc_records = saturation["records"]
        if "threads" not in doc:
            raise Layer3ReportError("floor calibration に threads がない: %s" % path)
        if "workload" not in doc or not isinstance(doc["workload"], dict):
            raise Layer3ReportError("floor calibration に workload dict がない: %s" % path)
        doc_protocol, protocol_match_basis = _floor_protocol_and_basis(
            doc, kind, path,
        )
        if kind == "within_run" and exclude_within_run:
            continue
        candidates[kind].append(
            (path, doc[block_for_kind[kind]], doc_records, doc["threads"],
             doc["workload"], doc_protocol, protocol_match_basis))

    campaign_has_no_ycsb = not isinstance(workload, dict)
    report_floors: Dict[str, Dict[str, Any]] = {}
    search_details: Dict[str, Dict[str, Any]] = {}
    for kind in block_for_kind:
        candidate_rows = candidates[kind]
        mismatches = []
        matches = []
        for (path, floor, doc_records, doc_threads, doc_workload,
             doc_protocol, protocol_match_basis) in candidate_rows:
            if (protocol is not None and not campaign_has_no_ycsb
                    and doc_protocol == protocol and doc_records == records
                    and doc_threads == threads and doc_workload == workload):
                matches.append((path, floor, protocol_match_basis))
            else:
                mismatches.append({
                    "file": path.name,
                    "protocol": doc_protocol,
                    "protocol_match_basis": protocol_match_basis,
                    "records": doc_records,
                    "threads": doc_threads,
                    "workload": doc_workload,
                })
        if len(matches) > 1:
            raise Layer3ReportError("一致する %s calibration floor が複数ある" % kind)

        detail = {
            "scanned_files": len(paths),
            "candidate_files": [row[0].name for row in candidate_rows],
            "skipped_no_floor_block": list(skipped_no_floor_block),
            "campaign_has_no_ycsb": campaign_has_no_ycsb,
            "campaign_protocol_resolution": (
                "unique-canonical-build-start-genome" if protocol is not None
                else "campaign-protocol-missing-invalid-or-multiple"
            ),
            "criteria": {"protocol": protocol, "records": records, "threads": threads,
                         "workload": workload if isinstance(workload, dict) else None},
            "mismatches": mismatches,
        }
        if pin_search is not None:
            detail_pin = dict(pin_search)
            if kind == "within_run" and exclude_within_run:
                detail_pin["within_run_exclusion"] = (
                    "self-inconsistent-calibration"
                )
            detail["contract_pin"] = detail_pin
        search_details[kind] = detail
        if matches:
            path, floor, protocol_match_basis = matches[0]
            report_floors[kind] = {
                "value": floor,
                "provenance": "env-record",
                "protocol": protocol,
                "source": {
                    "path": str(path.relative_to(calibration_dir.parents[2])),
                    "sha256": _sha256_file(path),
                },
                "search": None,
            }
            report_floors[kind]["protocol_match_basis"] = protocol_match_basis
        else:
            report_floors[kind] = {
                "value": None,
                "provenance": "no-matching-env-record",
                "source": None,
                "search": detail,
            }
            if protocol is not None:
                report_floors[kind]["protocol"] = protocol
    return report_floors, search_details


def _resolve_campaign_dir(campaign_dir: Path, output_root: Optional[Path]) -> Tuple[Path, Path]:
    root = Path(output_root) if output_root is not None else _DEFAULT_OUTPUT_ROOT
    repo_root = root.resolve().parent
    resolved = Path(campaign_dir).resolve()
    try:
        relative = resolved.relative_to(repo_root)
    except ValueError as exc:
        raise Layer3ReportError("campaign directory が repo 外にある: %s" % resolved) from exc
    return resolved, relative


def _contains_qualification_lineage(value: Any) -> bool:
    """Recognize explicit T-126 provenance, independent of campaign shape."""
    if isinstance(value, Mapping):
        if value.get("qualification_lineage") == "t126-only":
            return True
        schema = value.get("schema_version")
        if isinstance(schema, str) and schema.startswith("t126-qualification-"):
            return True
        return any(_contains_qualification_lineage(item) for item in value.values())
    if isinstance(value, list):
        return any(_contains_qualification_lineage(item) for item in value)
    return False


def _reject_qualification_ancestry(campaign_dir: Path, repo_root: Path) -> None:
    current = campaign_dir
    while True:
        marker = current / "qualification-marker.json"
        if marker.exists() or marker.is_symlink():
            raise Layer3ReportError(
                "qualification provenance は formal Layer3 入力として受理しない")
        if current == repo_root:
            break
        try:
            current.relative_to(repo_root)
        except ValueError:
            break
        if current.parent == current:
            break
        current = current.parent


def _qualification_ancestry_bound(campaign_dir: Path, output_root: Path) -> Path:
    """Return the boundary used when walking for qualification provenance.

    A campaign inside the real repository must be checked all the way to the
    repository root, even when a narrower output root was supplied.  Truly
    external campaigns retain the existing output-root-derived boundary.
    """
    real_repo_root = _DEFAULT_OUTPUT_ROOT.parent
    try:
        campaign_dir.relative_to(real_repo_root)
    except ValueError:
        resolved_output_root = output_root.resolve()
        if (
            resolved_output_root == campaign_dir
            or campaign_dir in resolved_output_root.parents
        ):
            raise Layer3ReportError(
                "output_root が campaign 配下にあり qualification-ancestry の境界として使えない"
            )
        return resolved_output_root.parent
    return real_repo_root


def build_report(campaign_dir: Path, generated_from_head: Optional[str] = None, *,
                 output_root: Optional[Path] = None) -> Dict[str, Any]:
    """campaign を読み取り専用で完全射影し、出力前の report object を返す。"""
    campaign_dir, campaign_path = _resolve_campaign_dir(campaign_dir, output_root)
    output_root = Path(output_root) if output_root is not None else _DEFAULT_OUTPUT_ROOT
    if not campaign_dir.is_dir():
        raise Layer3ReportError("campaign directory が存在しない: %s" % campaign_dir)
    try:
        admitted_campaign = require_admitted_campaign(
            campaign_dir,
            purpose=CampaignReadPurpose.HISTORICAL_RAW,
        )
    except ArtifactAdmissionError as exc:
        if str(exc) == "post-policy campaign WAL has a truncated tail":
            # Keep Layer 3's established framing diagnosis while the shared
            # admission gate remains fail-closed for the same malformed bytes.
            _read_wal(campaign_dir / "runs" / "wal.jsonl")
        raise Layer3ReportError(f"campaign admission 検証に失敗: {exc}") from exc
    except wal.WalFramingError as exc:
        raise Layer3ReportError(
            "WAL framing が不正: %s: %s"
            % (campaign_dir / "runs" / "wal.jsonl", exc)
        ) from exc
    except (json.JSONDecodeError, wal.WalLineError) as exc:
        raise Layer3ReportError(
            "WAL record が不正: %s: %s" % (type(exc).__name__, exc)
        ) from exc
    _reject_qualification_ancestry(
        campaign_dir, _qualification_ancestry_bound(campaign_dir, output_root),
    )
    decoded_lock = _read_campaign_lock(
        campaign_dir / "campaign.lock", purpose=CampaignReadPurpose.HISTORICAL_RAW,
    )
    lock = decoded_lock.identity
    ao_path = Path(CampaignLayout(root=str(campaign_dir)).agent_outputs_file)
    agent_outputs, ao_sha256 = _read_agent_outputs(ao_path)
    state_path = campaign_dir / "loop_state.json"
    try:
        state_mode = state_path.stat().st_mode
    except FileNotFoundError:
        if state_path.is_symlink():
            raise Layer3ReportError("loop_state.json が読めない: %s" % state_path)
        whiteboard = []
        whiteboard_provenance = "absent"
    except OSError as exc:
        raise Layer3ReportError("loop_state.json が読めない: %s" % state_path) from exc
    else:
        if not stat.S_ISREG(state_mode):
            raise Layer3ReportError("loop_state.json が通常ファイルでない: %s" % state_path)
        state = _read_json(state_path)
        if not isinstance(state, dict):
            raise Layer3ReportError("loop_state.json が object でない")
        whiteboard = state.get("whiteboard")
        if not isinstance(whiteboard, list) or not all(isinstance(item, dict) for item in whiteboard):
            raise Layer3ReportError("loop_state.whiteboard が object の list でない")
        whiteboard_provenance = "loop_state"
    for index, entry in enumerate(whiteboard):
        try:
            p3_s4_loop.assert_whiteboard_value_domains(entry, index)
        except (ValueError, KeyError) as exc:
            raise Layer3ReportError(
                f"whiteboard entry[{index}] の値域検査に失敗: {exc}"
            ) from exc
    if not isinstance(lock, dict):
        raise Layer3ReportError("campaign.lock が object でない")
    if _contains_qualification_lineage(lock):
        raise Layer3ReportError(
            "qualification lineage は formal Layer3 入力として受理しない")
    required_lock = {"ccbench_commit", "search_config", "search_tag", "spec_content", "trial"}
    if set(lock) != required_lock or not isinstance(lock["search_config"], dict):
        raise Layer3ReportError("campaign.lock のキーが不正")
    _assert_unique_refs("wb", whiteboard, "whiteboard")
    records = _read_wal(campaign_dir / "runs" / "wal.jsonl")
    if (
        _sha256_file(campaign_dir / "campaign.lock")
        != admitted_campaign.decision.campaign_lock_sha256
        or _sha256_file(campaign_dir / "runs" / "wal.jsonl")
        != admitted_campaign.decision.wal_sha256
    ):
        raise Layer3ReportError("campaign bytes changed after admission validation")
    try:
        checked_knowledge_provenance = (
            wal.knowledge_provenance_and_receipt_sha256_for_material_report(
                CampaignLayout(root=str(campaign_dir)),
                [
                    WalRecord(
                        variant=record["variant"],
                        stage=record["stage"],
                        env_tag=record["env_tag"],
                        ts=record["ts"],
                        payload=record["payload"],
                    )
                    for record in records
                ],
                campaign_lock=decoded_lock.identity,
            )
        )
    except wal.AttemptTopologyError as exc:
        raise Layer3ReportError(
            "knowledge provenance 検証に失敗"
        ) from exc
    if checked_knowledge_provenance is None:
        knowledge_provenance = None
        knowledge_receipt_sha256 = None
    else:
        knowledge_provenance, knowledge_receipt_sha256 = (
            checked_knowledge_provenance
        )
    if _contains_qualification_lineage(records):
        raise Layer3ReportError(
            "qualification lineage は formal Layer3 入力として受理しない")
    env_tags = {record["env_tag"] for record in records}
    if len(env_tags) != 1:
        raise Layer3ReportError("campaign WAL の env_tag が一意でない")
    records_count = lock["search_config"].get("records")
    threads = lock["search_config"].get("threads")
    if isinstance(records_count, bool) or isinstance(threads, bool) or not isinstance(records_count, int) or not isinstance(threads, int):
        raise Layer3ReportError("campaign search_config の records/threads が整数でない")
    variant_rows = _variant_rows(records)
    protocol = _campaign_protocol(records)
    ordered = sorted(records, key=_event_key)
    events_by_variant = {row["variant"]: row["events"] for row in variant_rows}
    runs = [_view_row(event) for event in ordered if event["stage"] == "bench_done"]
    verifications = [_view_row(event) for event in ordered if event["stage"] == "verify_done"]
    aborts = [_view_row(event) for event in ordered if event["stage"] == "abort"]
    rejects = [{"variant": name, "reason": "commit-event-absent",
                "source_ref": canonical_record_ref("wal", events[-1])}
               for name, events in sorted(events_by_variant.items())
               if not any(event["stage"] == "commit" for event in events)]
    env_tag = next(iter(env_tags))
    calibration_dir = output_root / "env" / env_tag / "calibration"
    contract_pin, contract_pin_search = _contract_calibration_pin(
        decoded_lock, env_tag,
    )
    noise_floor, _ = _calibration_floors(
        calibration_dir, records_count, threads, lock["search_config"].get("ycsb"),
        protocol=protocol, contract_pin=contract_pin,
        contract_pin_search=contract_pin_search,
    )
    report: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "campaign_id": campaign_dir.name, "campaign_path": campaign_path.as_posix(),
            "ccbench_commit": lock["ccbench_commit"],
            "generated_from_head": _resolve_generated_from_head(
                campaign_dir, decoded_lock, generated_from_head,
            ),
            "generator": {"identity": GENERATOR_IDENTITY, "sha256": _sha256_file(Path(__file__))},
        },
        "workload": lock["search_config"],
        "policy_hint": lock["search_config"].get("policy_hint"),
        "knowledge_provenance": knowledge_provenance,
        "variants": variant_rows, "runs": runs,
        "verifications": verifications, "rejects": rejects, "aborts": aborts,
        "noise_floor": noise_floor,
        "env_tags": sorted(env_tags),
        "whiteboard": sorted(whiteboard, key=lambda item: canonical_record_ref("wb", item)),
        "whiteboard_provenance": whiteboard_provenance,
        "artifact_refs": _artifact_refs(
            campaign_dir,
            knowledge_receipt_sha256=knowledge_receipt_sha256,
        ),
        "source_refs": [],
        "admission_decision": admitted_campaign.decision.as_receipt(),
        "campaign_verifier_epoch": _epoch_projection(
            admitted_campaign.campaign_verifier_epoch,
            verifier_assessment_basis=(
                admitted_campaign.verifier_assessment_basis
            ),
        ),
        "current_verifier_conformance": (
            admitted_campaign.current_verifier_conformance
        ),
        "acceptance_receipt": None,
        "certifying_input": False,
        "agent_outputs": sorted(agent_outputs or (), key=lambda env: canonical_record_ref("ao", env)),
        "mechanism_hypotheses": _mechanism_view(records, agent_outputs or ()),
        "mechanism_hypotheses_provenance": "absent" if agent_outputs is None else "agent_outputs",
    }
    artifact_ao = [ref["sha256"] for ref in report["artifact_refs"]
                   if ref["path"] == ao_path.relative_to(campaign_dir).as_posix()]
    if artifact_ao != ([] if ao_sha256 is None else [ao_sha256]):
        raise Layer3ReportError("agent outputs bytes changed before artifact_refs")
    report["source_refs"] = sorted(_report_primary_refs(report).elements())
    _validate_schema(report)
    _assert_bijection(records, whiteboard, report, agent_outputs=agent_outputs)
    return report


def build_accepted_report(
    campaign_dir: Path,
    *,
    acceptance_receipt: s8c_acceptance_receipt.VerifiedAcceptanceReceipt,
    generated_from_head: Optional[str] = None,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """Build a receipt-bound Layer 3 report for a future certified consumer.

    No certified-selection consumer exists in this checkout.  This function is
    therefore a fail-closed future entrypoint, not evidence that such a
    consumer has been wired.  It accepts neither a return code nor stdout.
    """
    try:
        verified = s8c_acceptance_receipt.require_current_verified_receipt(
            acceptance_receipt
        )
    except s8c_acceptance_receipt.AcceptanceReceiptError as exc:
        raise Layer3ReportError(f"acceptance receipt 検証に失敗: {exc}") from exc
    if verified.certifying is not True:
        raise Layer3ReportError("acceptance receipt が certifying=true でない")

    resolved_campaign, _campaign_path = _resolve_campaign_dir(
        campaign_dir, output_root,
    )
    matching = [
        trial for trial in verified.trials
        if trial.campaign_id == resolved_campaign.name
    ]
    if len(matching) != 1:
        raise Layer3ReportError(
            "acceptance receipt の campaign_id が対象 campaign と一意に一致しない"
        )
    lock = _read_campaign_lock(
        resolved_campaign / "campaign.lock",
        purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
    ).identity
    lock_trial = lock.get("trial")
    receipt_trial_id = matching[0].trial_id
    if not isinstance(lock_trial, str) or not (
        lock_trial == receipt_trial_id
        or lock_trial.startswith(receipt_trial_id + "-")
    ):
        raise Layer3ReportError(
            "acceptance receipt の trial_id が対象 campaign と一致しない"
        )

    if generated_from_head is None:
        # Keep the certifying path's accepted inputs identical to its pre-wave set.
        generated_from_head = _git_head(resolved_campaign)
    report = build_report(
        resolved_campaign,
        generated_from_head=generated_from_head,
        output_root=output_root,
    )
    admission_decision = report.get("admission_decision")
    if (
        not isinstance(admission_decision, Mapping)
        or admission_decision.get("admission_status") != "admitted"
    ):
        raise Layer3ReportError(
            "certifying Layer3 report には admission_status=admitted が必須"
        )
    try:
        certified_campaign = require_certified_commit_evidence(
            require_admitted_campaign(
                resolved_campaign,
                purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
            )
        )
    except (ArtifactAdmissionError, TypeError) as exc:
        raise Layer3ReportError(
            f"certifying campaign admission 検証に失敗: {exc}"
        ) from exc
    if admission_decision != certified_campaign.decision.as_receipt():
        raise Layer3ReportError(
            "campaign admission decision が historical 構築後に変化した"
        )
    epoch = _epoch_projection(certified_campaign.campaign_verifier_epoch)
    if epoch["state"] != "E1":
        raise Layer3ReportError(
            "新規 certifying Layer3 report には E1 epoch が必須"
        )
    report.pop("current_verifier_conformance")
    report.update({
        "acceptance_receipt": {
            "path": verified.relative_path,
            "sha256": verified.sha256,
        },
        "certifying_input": True,
        "campaign_verifier_epoch": epoch,
    })
    _validate_schema(report)
    return report


def _write_report_atomic(out_json: Path, report: Dict[str, Any]) -> None:
    """report を既存出力を上書きせず atomic に新規作成する。"""
    out_json = Path(out_json)
    encoded = _canonical_bytes(report) + b"\n"
    if not out_json.parent.is_dir():
        raise Layer3ReportError("出力先 parent directory が存在しない: %s" % out_json.parent)
    fd, temporary = tempfile.mkstemp(prefix=".layer3-", dir=str(out_json.parent))
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(encoded)
            stream.flush()
            os.fsync(stream.fileno())
        try:
            os.link(temporary, out_json)
        except FileExistsError as exc:
            raise Layer3ReportError("出力先が既に存在する: %s" % out_json) from exc
    finally:
        try:
            os.unlink(temporary)
        except FileNotFoundError:
            pass


def render(campaign_dir: Path, out_json: Path, generated_from_head: Optional[str] = None, *,
           output_root: Optional[Path] = None) -> Dict[str, Any]:
    """完全検査済み report を新規ファイルとして書く。既存出力は上書きしない。"""
    out_json = Path(out_json)
    if out_json.exists():
        raise Layer3ReportError("出力先が既に存在する: %s" % out_json)
    report = build_report(
        campaign_dir,
        generated_from_head=generated_from_head,
        output_root=output_root,
    )
    _write_report_atomic(out_json, report)
    return report


def render_accepted(
    campaign_dir: Path,
    out_json: Path,
    *,
    acceptance_receipt: s8c_acceptance_receipt.VerifiedAcceptanceReceipt,
    generated_from_head: Optional[str] = None,
    output_root: Optional[Path] = None,
) -> Dict[str, Any]:
    """検証済み receipt-bound report を新規ファイルとして書く。

    caller は non-certifying 出力と異なる path を渡すこと。本関数は path の意味を検証しない。
    既存出力は上書きしない。
    """
    out_json = Path(out_json)
    if out_json.exists():
        raise Layer3ReportError("出力先が既に存在する: %s" % out_json)
    report = build_accepted_report(
        campaign_dir,
        acceptance_receipt=acceptance_receipt,
        generated_from_head=generated_from_head,
        output_root=output_root,
    )
    _write_report_atomic(out_json, report)
    return report


def _non_empty_path(value: str) -> Path:
    if not value:
        raise argparse.ArgumentTypeError("--output-root を空文字列にはできない")
    return Path(value)


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="D12 層3材料レポート renderer")
    parser.add_argument("campaign_dir")
    parser.add_argument("out_json")
    parser.add_argument("--generated-from-head", metavar="HEX")
    parser.add_argument(
        "--output-root", type=_non_empty_path, default=None, metavar="PATH",
    )
    args = parser.parse_args(argv)
    try:
        render(
            Path(args.campaign_dir),
            Path(args.out_json),
            args.generated_from_head,
            output_root=args.output_root,
        )
    except Layer3ReportError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
