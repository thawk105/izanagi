# -*- coding: utf-8 -*-
"""D12 の層3材料レポートを WAL と whiteboard から再生成する。

使い方: ``python3 orchestrator/campaign/layer3_report.py <campaign_dir> <out_json>``。
これは既存の構造化記録だけを完全射影する。loop campaign の whiteboard に加え、
``loop_state.json`` を持たない sweep campaign も whiteboard の provenance を明示して扱う。
入力由来の hash multiset と、構築済み
report 本体を再走査して得る multiset を独立に比較し、view の source_ref も一次配置を
参照することを検査する。未知 stage、重複、脱落、参照不能、読めない入力、schema
不適合はいずれも例外にし、部分レポートを出力しない。

``mechanism_hypotheses`` は未実装の予約区画であり、常に空である。WAL に必要な原料が
構造化され、schema_version を上げて契約を拡張するまで解除しない。
noise floor は within_run = 1 測定の品質、between_run = run 間比較の採否 floor として区別する（p2_2.py の A2 注記と同じ区別）。
abort variant も commit-event-absent のため rejects に載り、詳細理由は aborts view が保持する。
schema v1 で生成済みの実レポートは、generator sha を内包する記録済み artifact であり、
v2 への更新のために再生成しない。
``generated_from_head`` は provenance であり、決定論比較の対象外である（HEAD が動けば
変わる）。
"""
from __future__ import annotations

import argparse
import hashlib
import json
import os
import stat
import subprocess
import sys
import tempfile
from collections import Counter, defaultdict
from pathlib import Path
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple

import jsonschema


SCHEMA_VERSION = "layer3-material-report/v2"
GENERATOR_IDENTITY = "orchestrator.campaign.layer3_report"
STAGES = frozenset(("build_start", "build_done", "verify_done", "bench_done", "commit", "abort"))
_HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(_HERE.parent))

from campaign import wal  # noqa: E402


_SCHEMA_PATH = _HERE / "layer3_schema.json"
_DEFAULT_OUTPUT_ROOT = _HERE.parents[1] / "output"


class Layer3ReportError(RuntimeError):
    """材料レポートの完全性または再現性の入力契約違反。"""


def _canonical_bytes(value: Any) -> bytes:
    return json.dumps(value, sort_keys=True, ensure_ascii=False,
                      separators=(",", ":")).encode("utf-8")


def canonical_record_ref(kind: str, record: Mapping[str, Any]) -> str:
    """WAL/whiteboard record の内容ハッシュ付き source-ref を返す。"""
    if kind not in ("wal", "wb"):
        raise Layer3ReportError("source-ref kind が不正")
    return "%s:%s" % (kind, hashlib.sha256(_canonical_bytes(record)).hexdigest())


def _read_json(path: Path) -> Any:
    try:
        with path.open(encoding="utf-8") as stream:
            return json.load(stream)
    except (OSError, UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise Layer3ReportError("JSON を読めない: %s" % path) from exc


def _assert_unique_refs(kind: str, records: Sequence[Mapping[str, Any]], label: str) -> None:
    refs = [canonical_record_ref(kind, record) for record in records]
    if len(refs) != len(set(refs)):
        raise Layer3ReportError("%s に canonical hash の完全重複がある" % label)


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


def _artifact_refs(campaign_dir: Path) -> List[Dict[str, str]]:
    files = sorted(path for path in campaign_dir.rglob("*") if path.is_file())
    if not files:
        raise Layer3ReportError("campaign に artifact がない")
    return [{"path": str(path.relative_to(campaign_dir)), "sha256": _sha256_file(path)}
            for path in files]


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
    return refs


def _assert_bijection(records: Sequence[Mapping[str, Any]], whiteboard: Sequence[Mapping[str, Any]],
                      report: Mapping[str, Any]) -> None:
    """入力と本体一次配置を独立比較し、view の参照整合も fails-closed で強制する。"""
    expected = Counter(canonical_record_ref("wal", item) for item in records)
    expected.update(canonical_record_ref("wb", item) for item in whiteboard)
    actual = _report_primary_refs(report)
    if actual != expected:
        raise Layer3ReportError("source-ref multiset が入力 WAL/whiteboard と report 本体で一致しない")
    source_refs = Counter(report.get("source_refs", ()))
    if source_refs != actual:
        raise Layer3ReportError("source_refs 区画が report 本体走査結果と一致しない")
    primary_wal_refs = {ref for ref in actual if ref.startswith("wal:")}
    for section in ("runs", "verifications", "rejects", "aborts"):
        for row in report.get(section, ()):
            if not isinstance(row, Mapping) or row.get("source_ref") not in primary_wal_refs:
                raise Layer3ReportError("%s の source_ref が一次配置を参照しない" % section)


def _validate_schema(report: Mapping[str, Any]) -> None:
    schema = _read_json(_SCHEMA_PATH)
    try:
        jsonschema.Draft7Validator(schema).validate(report)
    except jsonschema.ValidationError as exc:
        raise Layer3ReportError("layer3 schema 検証に失敗") from exc


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


def _view_row(event: Mapping[str, Any]) -> Dict[str, Any]:
    return {**event["payload"], "variant": event["variant"],
            "source_ref": canonical_record_ref("wal", event)}


def _calibration_floors(calibration_dir: Path, records: Any, threads: Any,
                        workload: Any) -> Tuple[Dict[str, Dict[str, Any]],
                                                Dict[str, Dict[str, Any]]]:
    """floor を kind 別に分類・照合し、report 値と完全な検索詳細を返す。"""
    paths = sorted(calibration_dir.glob("*.json")) if calibration_dir.is_dir() else []
    block_for_kind = {"within_run": "noise_floor", "between_run": "between_run"}
    candidates: Dict[str, List[Tuple[Path, Dict[str, Any], Any, Any, Dict[str, Any]]]] = {
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
        kind = kinds[0]
        candidates[kind].append(
            (path, doc[block_for_kind[kind]], doc_records, doc["threads"], doc["workload"]))

    campaign_has_no_ycsb = not isinstance(workload, dict)
    report_floors: Dict[str, Dict[str, Any]] = {}
    search_details: Dict[str, Dict[str, Any]] = {}
    for kind in block_for_kind:
        candidate_rows = candidates[kind]
        mismatches = []
        matches = []
        for path, floor, doc_records, doc_threads, doc_workload in candidate_rows:
            if (not campaign_has_no_ycsb and doc_records == records
                    and doc_threads == threads and doc_workload == workload):
                matches.append((path, floor))
            else:
                mismatches.append({
                    "file": path.name,
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
            "criteria": {"records": records, "threads": threads,
                         "workload": workload if isinstance(workload, dict) else None},
            "mismatches": mismatches,
        }
        search_details[kind] = detail
        if matches:
            path, floor = matches[0]
            report_floors[kind] = {
                "value": floor,
                "provenance": "env-record",
                "source": {
                    "path": str(path.relative_to(calibration_dir.parents[2])),
                    "sha256": _sha256_file(path),
                },
                "search": None,
            }
        else:
            report_floors[kind] = {
                "value": None,
                "provenance": "no-matching-env-record",
                "source": None,
                "search": detail,
            }
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


def build_report(campaign_dir: Path, generated_from_head: Optional[str] = None, *,
                 output_root: Optional[Path] = None) -> Dict[str, Any]:
    """campaign を読み取り専用で完全射影し、出力前の report object を返す。"""
    campaign_dir, campaign_path = _resolve_campaign_dir(campaign_dir, output_root)
    output_root = Path(output_root) if output_root is not None else _DEFAULT_OUTPUT_ROOT
    if not campaign_dir.is_dir():
        raise Layer3ReportError("campaign directory が存在しない: %s" % campaign_dir)
    _reject_qualification_ancestry(campaign_dir, output_root.resolve().parent)
    lock = _read_json(campaign_dir / "campaign.lock")
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
    ordered = sorted(records, key=_event_key)
    events_by_variant = {row["variant"]: row["events"] for row in variant_rows}
    runs = [_view_row(event) for event in ordered if event["stage"] == "bench_done"]
    verifications = [_view_row(event) for event in ordered if event["stage"] == "verify_done"]
    aborts = [_view_row(event) for event in ordered if event["stage"] == "abort"]
    rejects = [{"variant": name, "reason": "commit-event-absent",
                "source_ref": canonical_record_ref("wal", events[-1])}
               for name, events in sorted(events_by_variant.items())
               if not any(event["stage"] == "commit" for event in events)]
    calibration_dir = output_root / "env" / next(iter(env_tags)) / "calibration"
    noise_floor, _ = _calibration_floors(
        calibration_dir, records_count, threads, lock["search_config"].get("ycsb"))
    report: Dict[str, Any] = {
        "schema_version": SCHEMA_VERSION,
        "meta": {
            "campaign_id": campaign_dir.name, "campaign_path": campaign_path.as_posix(),
            "ccbench_commit": lock["ccbench_commit"],
            "generated_from_head": generated_from_head if generated_from_head is not None else _git_head(campaign_dir),
            "generator": {"identity": GENERATOR_IDENTITY, "sha256": _sha256_file(Path(__file__))},
        },
        "workload": lock["search_config"], "variants": variant_rows, "runs": runs,
        "verifications": verifications, "rejects": rejects, "aborts": aborts,
        "noise_floor": noise_floor,
        "env_tags": sorted(env_tags),
        "whiteboard": sorted(whiteboard, key=lambda item: canonical_record_ref("wb", item)),
        "whiteboard_provenance": whiteboard_provenance,
        "artifact_refs": _artifact_refs(campaign_dir), "source_refs": [],
        "mechanism_hypotheses": [],
    }
    report["source_refs"] = sorted(_report_primary_refs(report).elements())
    _validate_schema(report)
    _assert_bijection(records, whiteboard, report)
    return report


def render(campaign_dir: Path, out_json: Path, generated_from_head: Optional[str] = None, *,
           output_root: Optional[Path] = None) -> Dict[str, Any]:
    """完全検査済み report を新規ファイルとして書く。既存出力は上書きしない。"""
    out_json = Path(out_json)
    if out_json.exists():
        raise Layer3ReportError("出力先が既に存在する: %s" % out_json)
    report = build_report(campaign_dir, generated_from_head=generated_from_head, output_root=output_root)
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
    return report


def main(argv: Optional[Sequence[str]] = None) -> int:
    parser = argparse.ArgumentParser(description="D12 層3材料レポート renderer")
    parser.add_argument("campaign_dir")
    parser.add_argument("out_json")
    parser.add_argument("--generated-from-head", metavar="HEX")
    args = parser.parse_args(argv)
    try:
        render(Path(args.campaign_dir), Path(args.out_json), args.generated_from_head)
    except Layer3ReportError as exc:
        parser.error(str(exc))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
