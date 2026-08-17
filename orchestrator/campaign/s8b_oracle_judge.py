# -*- coding: utf-8 -*-
"""8b oracle observations の I/O 非依存な三値判定。"""
from __future__ import annotations

import argparse
import json
import statistics
import sys
from collections import Counter
from collections.abc import Mapping, Sequence
from dataclasses import dataclass
from pathlib import Path
from typing import Optional

if __package__ in {None, ""}:  # pragma: no cover - direct CLI execution
    sys.path.insert(0, str(Path(__file__).resolve().parents[2]))
    __package__ = "orchestrator.campaign"

_ORCHESTRATOR = Path(__file__).resolve().parent.parent
ROOT = _ORCHESTRATOR.parent

from . import s8b_oracle_artifacts as _artifacts  # noqa: E402
from . import s8b_oracle_manifest, s8b_oracle_spec  # noqa: E402
from . import s8b_ratified_freeze  # noqa: E402
from orchestrator.calibrator import perf_preflight as _perf_preflight  # noqa: E402

INPUT_SCHEMA = _artifacts.OFFICIAL_OBSERVATIONS_SCHEMA
OUTPUT_SCHEMA = _artifacts.OFFICIAL_VERDICT_SCHEMA
_EXPECTED_CELL_KEYS = {"schedule_index", "holdout_id", "configuration_id"}
_MEASUREMENT_CONDITION_KEYS = {
    "campaign_id", "measurement_manifest_sha256", "perf_observation",
}
_SHA256_CHARS = frozenset("0123456789abcdef")
_DEGRADED_PLACEHOLDER_CMD = ("ccbench",)
_DEGRADED_PLACEHOLDER_INDICATORS = {
    "ipc": None,
    "llc_miss_rate": None,
}


@dataclass(frozen=True)
class ManifestScheduleProjection:
    """検証済み manifest schedule から一度だけ導出する immutable 射影。"""

    n_per_cell: int
    expected_cells: frozenset[tuple[int, str, str]]
    expected_campaign_ids: frozenset[str]

    def __post_init__(self) -> None:
        object.__setattr__(self, "expected_cells", frozenset(self.expected_cells))
        campaign_ids = frozenset(self.expected_campaign_ids)
        if not campaign_ids or not all(
                isinstance(value, str) and value for value in campaign_ids):
            raise ValueError(
                "expected_campaign_ids は空でない campaign ID 集合が必要"
            )
        object.__setattr__(
            self, "expected_campaign_ids", campaign_ids,
        )


def _verified_manifest_campaign_ids(document: Mapping) -> frozenset[str]:
    raw = document["campaign_ids"]
    if isinstance(raw, Mapping):
        values = raw.values()
    else:
        values = raw
    campaign_ids = {
        value.get("campaign_id") if isinstance(value, Mapping) else value
        for value in values
    }
    if not campaign_ids or not all(
            isinstance(value, str) and value for value in campaign_ids):
        raise ValueError("verified manifest campaign_ids の射影に失敗")
    return frozenset(campaign_ids)


def project_verified_manifest_schedule(
        verified_manifest: s8b_oracle_manifest.VerifiedManifest,
) -> ManifestScheduleProjection:
    """検証済み schedule の判定用最小射影を I/O なしで固定する。"""
    if type(verified_manifest) is not s8b_oracle_manifest.VerifiedManifest:
        raise TypeError("VerifiedManifest exact type が必要")
    schedule = verified_manifest.document["schedule"]
    return ManifestScheduleProjection(
        n_per_cell=schedule["n"],
        expected_cells=frozenset(
            (
                row["schedule_index"],
                row["holdout_id"],
                row["configuration_id"],
            )
            for row in schedule["rows"]
        ),
        expected_campaign_ids=_verified_manifest_campaign_ids(
            verified_manifest.document
        ),
    )


def _is_int(value: object) -> bool:
    return isinstance(value, int) and not isinstance(value, bool)


def _reason(code: str, message: str) -> dict:
    return {"code": code, "message": message}


def _unknown(reasons: Sequence[Mapping]) -> dict:
    ordered = sorted((dict(reason) for reason in reasons),
                     key=lambda reason: (str(reason.get("code")), str(reason.get("message"))))
    return {"status": "unknown", "median_of_medians": None,
            "trial_medians": [], "reasons": ordered}


def _measurement_conditions(
        observations: Mapping, expected_campaign_ids: frozenset[str],
) -> tuple[list[dict] | None, list[dict]]:
    """条件付き campaign 全被覆を検査し、集約前 claim gate を実行する。"""
    if "measurement_conditions" not in observations:
        return None, []
    raw = observations.get("measurement_conditions")
    reasons: list[dict] = []
    normalized: list[dict] = []
    if (not isinstance(raw, Sequence)
            or isinstance(raw, (str, bytes, bytearray)) or not raw):
        return [], [_reason(
            "measurement-conditions",
            "measurement_conditions が空でない array でない",
        )]
    campaign_ids: list[str] = []
    perf_present = 0
    degraded = 0
    for entry in raw:
        if not isinstance(entry, Mapping) or set(entry) != _MEASUREMENT_CONDITION_KEYS:
            reasons.append(_reason(
                "measurement-condition-schema",
                "measurement_conditions entry の exact key 集合が不一致",
            ))
            continue
        campaign_id = entry.get("campaign_id")
        if not isinstance(campaign_id, str) or not campaign_id:
            reasons.append(_reason(
                "measurement-condition-campaign-id",
                "measurement_conditions campaign_id が非空文字列でない",
            ))
            continue
        campaign_ids.append(campaign_id)
        sha256 = entry.get("measurement_manifest_sha256")
        observation = entry.get("perf_observation")
        if sha256 is None and observation is None:
            perf_present += 1
            normalized.append(dict(entry))
            continue
        if (not isinstance(sha256, str) or len(sha256) != 64
                or not set(sha256) <= _SHA256_CHARS or observation is None):
            reasons.append(_reason(
                "measurement-condition-pair",
                "measurement manifest hash と perf_observation の null 条件が不一致",
            ))
            continue
        try:
            allowed = _perf_preflight.perf_claim_allowed(
                observation,
                "throughput",
                run_cmd=_DEGRADED_PLACEHOLDER_CMD,
                leading_indicators=_DEGRADED_PLACEHOLDER_INDICATORS,
            )
            canonical = _perf_preflight.validate_perf_observation(
                observation,
                run_cmd=_DEGRADED_PLACEHOLDER_CMD,
                leading_indicators=_DEGRADED_PLACEHOLDER_INDICATORS,
            )
        except _perf_preflight.PerfPreflightError as exc:
            reasons.append(_reason(
                "measurement-condition-observation",
                f"measurement condition perf_observation が不正: {exc}",
            ))
            continue
        if not allowed:
            reasons.append(_reason(
                "measurement-condition-claim",
                "measurement condition は throughput claim を許可しない",
            ))
            continue
        if canonical["use_perf"] is not False:
            reasons.append(_reason(
                "measurement-condition-mode",
                "measurement manifest 付き condition が degraded でない",
            ))
            continue
        degraded += 1
        normalized.append({
            "campaign_id": campaign_id,
            "measurement_manifest_sha256": sha256,
            "perf_observation": canonical,
        })
    if len(campaign_ids) != len(set(campaign_ids)):
        reasons.append(_reason(
            "measurement-condition-duplicate",
            "measurement_conditions campaign_id が重複",
        ))
    if frozenset(campaign_ids) != expected_campaign_ids:
        reasons.append(_reason(
            "measurement-condition-campaigns",
            "measurement_conditions が検証済み manifest campaign_ids を完全被覆しない",
        ))
    if perf_present and degraded:
        reasons.append(_reason(
            "measurement-conditions-mixed",
            "perf 有り campaign と degraded campaign が混在",
        ))
    elif perf_present and not degraded:
        reasons.append(_reason(
            "measurement-conditions-redundant",
            "全 campaign が perf 有りなら measurement_conditions は不在でなければならない",
        ))
    return normalized, reasons


def _cell(
        rows: Sequence[Mapping], n: int, duplicate_indices: set[int],
        epoch_eligible_campaign_ids: frozenset[str],
) -> dict:
    reasons: list[dict] = []
    if len(rows) != n:
        reasons.append(_reason("trial-count", f"期待 n={n} に対して rows={len(rows)}"))
    if any(_is_int(row.get("schedule_index"))
           and row.get("schedule_index") in duplicate_indices for row in rows):
        reasons.append(_reason("duplicate-row", "schedule_index が observations 内で重複"))
    if any(
            row.get("campaign_id") not in epoch_eligible_campaign_ids
            for row in rows):
        reasons.append(_reason(
            "campaign-verifier-epoch",
            "campaign_verifier_epoch が certified E1 でない",
        ))
    for row in rows:
        if not _is_int(row.get("schedule_index")) or row["schedule_index"] < 0:
            reasons.append(_reason("schedule-index", "schedule_index が非負整数でない"))
        if not _is_int(row.get("attempt")) or row["attempt"] < 0:
            reasons.append(_reason("attempt", "attempt が非負整数でない"))
        if row.get("binding_ok") is not True:
            reasons.append(_reason("binding", "binding_ok が true でない"))
        if row.get("screen_outcome") != "not_enabled":
            reasons.append(_reason("screening", "screen_outcome が not_enabled でない"))
        if row.get("status") != "completed":
            reasons.append(_reason("row-status", f"status={row.get('status')!r}"))
        if not isinstance(row.get("block_id"), str) or not row.get("block_id"):
            reasons.append(_reason("block-id", "block_id が非空文字列でない"))
        if row.get("excluded_reason") is not None and not isinstance(
                row.get("excluded_reason"), str):
            reasons.append(_reason("excluded", "excluded_reason が null/文字列でない"))
        if row.get("reason") is not None and not isinstance(row.get("reason"), str):
            reasons.append(_reason("reason", "reason が null/文字列でない"))
        if (row.get("outcome") == "correctness-red"
                and row.get("excluded_reason") is not None):
            reasons.append(_reason("red-excluded", "correctness-red に excluded_reason がある"))
        if row.get("outcome") == "verify-inconclusive":
            reasons.append(_reason(
                "verify-inconclusive", "verify の pass/red が確定していない",
            ))
        if row.get("outcome") == "binary-mismatch":
            # C3-5: 計測 binary が期待 (floor 計測 bytes) と不一致で abort した trial。
            # この cell は計測の真正性が壊れているため disqualify でなく unknown に倒す
            # (verify-inconclusive と同じく、他 trial に red があっても cell を unknown に
            # 固定する: 誤った binary で走った cell の結論を採らない)。
            reasons.append(_reason(
                "binary-mismatch", "計測 binary が期待値と不一致で abort した",
            ))

    if reasons:
        return _unknown(reasons)

    definitive_red = any(
        row.get("outcome") == "correctness-red"
        and row.get("binding_ok") is True
        and "red" in (row.get("legacy_verify"), row.get("s2_verify"))
        for row in rows
    )
    if definitive_red:
        return {"status": "disqualified", "median_of_medians": None,
                "trial_medians": [], "reasons": []}

    trial_medians: list[float] = []
    for row in rows:
        if row.get("outcome") != "committed":
            reasons.append(_reason("outcome", f"eligible でない outcome={row.get('outcome')!r}"))
        if row.get("legacy_verify") != "pass" or row.get("s2_verify") != "pass":
            reasons.append(_reason("verify", "legacy/S2 の双方が pass でない"))
        if row.get("excluded_reason") is not None:
            reasons.append(_reason("excluded", "excluded_reason が null でない"))
        values = row.get("bench_values")
        if (not isinstance(values, Sequence)
                or isinstance(values, (str, bytes, bytearray)) or not values):
            reasons.append(_reason("bench-values", "bench_values が空または array でない"))
            continue
        projected = _artifacts.project_finite_float_sequence(values)
        if projected is None:
            reasons.append(_reason("non-finite", "bench_values に非有限値または非数値がある"))
            continue
        trial_medians.append(float(statistics.median(projected)))
    if reasons:
        return _unknown(reasons)
    return {
        "status": "eligible",
        "median_of_medians": float(statistics.median(trial_medians)),
        "trial_medians": sorted(trial_medians),
        "reasons": [],
    }


def judge_oracle(
    observations: _artifacts.OfficialObservations,
    *, schedule_projection: ManifestScheduleProjection,
    verified_manifest_sha256, approved_spec_sha256,
) -> _artifacts.OfficialVerdict:
    """holdout ごとの oracle verdict を返す純関数。

    集約は各 trial の bench rep 中央値を構成ごとにさらに中央値へ畳む
    median of medians とする。eligible な構成の median_of_medians の最大値との
    完全一致で tie を決める。これらの規則は docs/decisions.md の
    「8b oracle の比較規則を明示的に再凍結する」で明示的に再凍結済みである。
    floor は入力にも argmax の tie-break にも使わない。
    """
    if type(observations) is not _artifacts.OfficialObservations:
        raise _artifacts.OracleArtifactTypeError(
            "judge_oracle は OfficialObservations exact type のみ受理する")
    if type(schedule_projection) is not ManifestScheduleProjection:
        raise TypeError("schedule_projection は ManifestScheduleProjection exact type が必要")
    top_reasons: list[dict] = []
    if observations.get("schema_version") != INPUT_SCHEMA:
        top_reasons.append(_reason("schema-version", "observations schema_version が不一致"))
    if observations.get("manifest_kind") != "official":
        top_reasons.append(_reason(
            "manifest-kind", "manifest_kind が official でない",
        ))
    epoch_campaign_ids: frozenset[str] | None = None
    epoch_eligible_campaign_ids: frozenset[str] = frozenset()
    try:
        epoch_entries = _artifacts.validate_campaign_verifier_epochs(
            observations.get("campaign_verifier_epochs")
        )
    except _artifacts.OracleArtifactTypeError as exc:
        top_reasons.append(_reason(
            "campaign-verifier-epoch-evidence", str(exc),
        ))
    else:
        epoch_campaign_ids = frozenset(
            entry["campaign_id"] for entry in epoch_entries
        )
        epoch_eligible_campaign_ids = frozenset(
            entry["campaign_id"] for entry in epoch_entries
            if entry["state"] == "E1"
            and entry["certified_eligible"] is True
        )
        if epoch_campaign_ids != schedule_projection.expected_campaign_ids:
            top_reasons.append(_reason(
                "campaign-verifier-epoch-campaigns",
                "campaign_verifier_epochs が検証済み manifest campaign_ids と不一致",
            ))
        for entry in epoch_entries:
            if entry["state"] != "E1" or entry["certified_eligible"] is not True:
                rejection = entry["rejection"]
                top_reasons.append(_reason(
                    rejection["code"],
                    f"campaign_id={entry['campaign_id']!r}: "
                    f"{entry['reason_code']}: {rejection['message']}",
                ))
    manifest_sha = observations.get("manifest_sha256")
    if (not isinstance(verified_manifest_sha256, str)
            or len(verified_manifest_sha256) != 64
            or any(c not in "0123456789abcdef" for c in verified_manifest_sha256)
            or manifest_sha != verified_manifest_sha256):
        top_reasons.append(_reason(
            "manifest-sha256",
            "manifest_sha256 が検証済み manifest の実値と一致しない",
        ))
        manifest_sha = None
    spec_sha = observations.get("spec_sha256")
    if (not isinstance(approved_spec_sha256, str)
            or len(approved_spec_sha256) != 64
            or any(c not in "0123456789abcdef" for c in approved_spec_sha256)
            or spec_sha != approved_spec_sha256):
        top_reasons.append(_reason(
            "spec-sha256",
            "spec_sha256 が approved spec の実値と一致しない",
        ))
    observed_n = observations.get("n_per_cell")
    n = schedule_projection.n_per_cell
    if not _is_int(observed_n) or observed_n < 1:
        top_reasons.append(_reason("n-per-cell", "n_per_cell が 1 以上の整数でない"))
    elif observed_n != n:
        top_reasons.append(_reason(
            "n-per-cell-mismatch",
            "n_per_cell が検証済み manifest schedule と一致しない",
        ))
    raw_rows = observations.get("rows")
    if (not isinstance(raw_rows, Sequence)
            or isinstance(raw_rows, (str, bytes, bytearray))):
        top_reasons.append(_reason("rows", "rows が array でない"))
        rows: list[Mapping] = []
    else:
        rows = [row for row in raw_rows if isinstance(row, Mapping)]
        if len(rows) != len(raw_rows):
            top_reasons.append(_reason("row-type", "rows に object でない行がある"))
    if any(
            not isinstance(row.get("campaign_id"), str)
            or not row.get("campaign_id")
            or (
                epoch_campaign_ids is not None
                and row.get("campaign_id") not in epoch_campaign_ids
            )
            for row in rows):
        top_reasons.append(_reason(
            "campaign-id",
            "rows の campaign_id が epoch 証拠へ束縛された非空文字列でない",
        ))

    raw_expected = observations.get("expected_cells")
    observed_expected_cells: list[tuple[int, str, str]] = []
    if (not isinstance(raw_expected, Sequence)
            or isinstance(raw_expected, (str, bytes, bytearray)) or not raw_expected):
        top_reasons.append(_reason("expected-cells", "expected_cells が空でない array でない"))
    else:
        for entry in raw_expected:
            if not isinstance(entry, Mapping) or set(entry) != _EXPECTED_CELL_KEYS:
                top_reasons.append(_reason(
                    "expected-cell-schema", "expected_cells entry schema が不一致"))
                continue
            index = entry.get("schedule_index")
            holdout_id = entry.get("holdout_id")
            configuration_id = entry.get("configuration_id")
            if (not _is_int(index) or index < 0
                    or not isinstance(holdout_id, str) or not holdout_id
                    or not isinstance(configuration_id, str) or not configuration_id):
                top_reasons.append(_reason(
                    "expected-cell-identity", "expected_cells entry identity が不正"))
                continue
            observed_expected_cells.append((index, holdout_id, configuration_id))

    observed_expected_counter = Counter(observed_expected_cells)
    if any(count != 1 for count in observed_expected_counter.values()):
        top_reasons.append(_reason("expected-cell-duplicate", "expected_cells に重複がある"))
    expected_indices = Counter(index for index, _, _ in observed_expected_cells)
    if any(count != 1 for count in expected_indices.values()):
        top_reasons.append(_reason(
            "expected-schedule-index", "expected_cells の schedule_index が一意でない"))
    expected_cells = schedule_projection.expected_cells
    expected_counter = Counter(expected_cells)
    if observed_expected_counter != expected_counter:
        top_reasons.append(_reason(
            "expected-cells-mismatch",
            "expected_cells が検証済み manifest schedule と一致しない",
        ))
    expected_cell_counts = Counter(
        (holdout_id, configuration_id)
        for _, holdout_id, configuration_id in expected_cells
    )
    if any(count != n for count in expected_cell_counts.values()):
        top_reasons.append(_reason(
            "expected-trial-count",
            "manifest schedule の cell 件数が n_per_cell と不一致",
        ))

    holdout_ids = sorted({holdout_id for _, holdout_id, _ in expected_cells})
    configurations_by_holdout = {
        holdout_id: sorted({configuration_id for _, candidate, configuration_id
                            in expected_cells if candidate == holdout_id})
        for holdout_id in holdout_ids
    }
    configuration_sets = {tuple(value) for value in configurations_by_holdout.values()}
    if len(configuration_sets) > 1:
        top_reasons.append(_reason(
            "expected-product", "expected_cells の configuration 集合が holdout 間で不一致"))
    if any(not isinstance(row.get("holdout_id"), str) or not row.get("holdout_id")
           or not isinstance(row.get("configuration_id"), str)
           or not row.get("configuration_id") for row in rows):
        top_reasons.append(_reason("cell-identity", "holdout/configuration id が不正な行がある"))
    actual_cells = Counter(
        (row.get("schedule_index"), row.get("holdout_id"), row.get("configuration_id"))
        for row in rows
        if _is_int(row.get("schedule_index"))
        and isinstance(row.get("holdout_id"), str) and row.get("holdout_id")
        and isinstance(row.get("configuration_id"), str) and row.get("configuration_id")
    )
    if actual_cells != expected_counter:
        top_reasons.append(_reason(
            "expected-cell-mismatch", "rows が manifest 由来 expected_cells と完全一致しない"))
    counts = Counter(row.get("schedule_index") for row in rows
                     if _is_int(row.get("schedule_index")))
    duplicate_indices = {index for index, count in counts.items() if count > 1}

    measurement_conditions, measurement_reasons = _measurement_conditions(
        observations, schedule_projection.expected_campaign_ids,
    )
    top_reasons.extend(measurement_reasons)
    measurement_aggregation_allowed = not measurement_reasons

    holdouts: dict[str, dict] = {}
    for holdout_id in holdout_ids:
        configurations: dict[str, dict] = {}
        for configuration_id in configurations_by_holdout[holdout_id]:
            cell_rows = [row for row in rows
                         if row.get("holdout_id") == holdout_id
                         and row.get("configuration_id") == configuration_id]
            configurations[configuration_id] = (
                _cell(
                    cell_rows, n, duplicate_indices,
                    epoch_eligible_campaign_ids,
                )
                if measurement_aggregation_allowed
                else _unknown(measurement_reasons)
            )
        unknown = bool(top_reasons) or any(
            value["status"] == "unknown" for value in configurations.values())
        eligible = {key: value["median_of_medians"] for key, value in configurations.items()
                    if value["status"] == "eligible"}
        if unknown or not eligible:
            verdict = "indeterminate"
            winner = None
            tied: list[str] = []
        else:
            maximum = max(eligible.values())
            tied = sorted(key for key, value in eligible.items() if value == maximum)
            if len(tied) == 1:
                verdict = "unique-best"
                winner = tied[0]
                tied = []
            else:
                verdict = "tie"
                winner = None
        holdouts[holdout_id] = {
            "verdict": verdict,
            "winner_configuration_id": winner,
            "tied_configuration_ids": tied,
            "configurations": configurations,
            "reasons": sorted((dict(reason) for reason in top_reasons),
                              key=lambda reason: (reason["code"], reason["message"])),
        }
    overall = ("indeterminate" if top_reasons or not holdouts
               or any(value["verdict"] == "indeterminate" for value in holdouts.values())
               else "determinate")
    result = _artifacts.OfficialVerdict({
        "schema_version": OUTPUT_SCHEMA,
        "manifest_sha256": manifest_sha,
        "n_per_cell": n,
        "status": overall,
        "reasons": sorted((dict(reason) for reason in top_reasons),
                          key=lambda reason: (reason["code"], reason["message"])),
        "holdouts": holdouts,
    })
    if measurement_conditions is not None:
        result["measurement_conditions"] = measurement_conditions
    return result


def _write_create_only(path: Path, value: Mapping) -> None:
    with path.open("x", encoding="utf-8") as stream:
        json.dump(value, stream, ensure_ascii=False, indent=2, sort_keys=True, allow_nan=False)
        stream.write("\n")


def _parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)
    judge = sub.add_parser("judge", help="observations を oracle verdict にする")
    judge.add_argument("--input", type=Path, required=True)
    judge.add_argument("--manifest", type=Path, required=True)
    judge.add_argument("--out", type=Path, required=True)
    judge.add_argument("--repo-root", type=Path, default=ROOT)
    return parser


def main(argv: Optional[Sequence[str]] = None) -> int:
    args = _parser().parse_args(argv)
    try:
        manifest = _artifacts.load_official_manifest(args.manifest)
        if type(manifest) is not _artifacts.OfficialManifest:
            raise _artifacts.OracleArtifactTypeError(
                "judge は official manifest のみ検証できる"
            )
        root = Path(args.repo_root)
        ratified = s8b_ratified_freeze.load_ratified_freeze(root)
        reverified = s8b_ratified_freeze.reverify_published_freeze(ratified, root)
        approved = s8b_oracle_spec.load_approved_spec(root)
        verified = s8b_oracle_manifest.verify_manifest(
            args.manifest,
            root=root,
            freeze_document=reverified.ratified.document,
            freeze_sha256=reverified.ratified.sha256,
            approved_spec=approved,
        )
        observations = _artifacts.load_official_observations(args.input)
        _write_create_only(args.out, judge_oracle(
            observations,
            schedule_projection=project_verified_manifest_schedule(verified),
            verified_manifest_sha256=verified.sha256,
            approved_spec_sha256=approved.sha256,
        ))
    except (OSError, json.JSONDecodeError, _artifacts.OracleArtifactTypeError,
            s8b_ratified_freeze.RatifiedFreezeError,
            s8b_oracle_manifest.ManifestError,
            s8b_oracle_spec.ReviewedSpecError,
            TypeError, ValueError) as exc:
        print(f"error: {exc}", file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
