# -*- coding: utf-8 -*-
"""段 8b R3 trusted prediction runner の at-most-once・journal 契約テスト。

受入ベクトル V7 (`output/insights/2026-07-16_s8b-freeze-v2-design-material.md` 付録 2):
同一セル二重 claim 拒否 + claim 後 crash 模擬から再起動して当該セル missing 恒久確定
(journal に invocation record が 1 件も増えない) を中核に据える。
"""
from __future__ import annotations

import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from orchestrator.campaign.s8b_prediction_runner import (
    PRODUCTION_PROVIDER,
    PredictionJournal,
    PredictionRunnerError,
    ProviderResponse,
    build_rows_from_journal,
    drive_journal,
    materialize_predictions,
    resolve_journal,
)
from orchestrator.campaign.s8b_selector_freeze import verify_prediction_freeze

ROOT = Path(__file__).resolve().parents[2]
FREEZE_PATH = ROOT / "output/s8b-freeze/holdout_freeze.json"

# jobs 列挙順 (build_prediction_jobs): sorted target × (on, off, swapped)
FIRST_AGENT_CELL = ("rr20", "on")
AGENT_CELLS = {("rr20", "on"), ("rr20", "swapped"), ("rr80", "on"), ("rr80", "swapped")}
OFF_CELLS = {("rr20", "off"), ("rr80", "off")}


def _freeze() -> dict:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def _valid_raw(choice_id: str = "c01", rationale: str = "descriptor と機構を比較した") -> str:
    return json.dumps(
        {
            "schema_version": "8b-selector-output/v1",
            "choice_id": choice_id,
            "rationale": rationale,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _provenance(role_sha256: str, tag: str) -> dict:
    return {
        "child_id": f"child-{tag}",
        "role_file_sha256": role_sha256,
        "model": "fixture-model",
        "started_at": "2026-07-16T00:00:00Z",
        "finished_at": "2026-07-16T00:01:00Z",
        "fresh_context": True,
        "declared_tools": [],
        "observed_tool_events": [],
    }


class _RecordingProvider:
    """呼び出しセルを記録し、指定セルで crash を起こせる注入 provider。"""

    def __init__(self, *, role_sha256: str = "0" * 64, crash_on=None):
        self.role_sha256 = role_sha256
        self.crash_on = set(crash_on or ())
        self.called: list[tuple[str, str]] = []

    def __call__(self, *, target_holdout, arm, payload) -> ProviderResponse:
        cell = (target_holdout, arm)
        self.called.append(cell)
        if cell in self.crash_on:
            raise RuntimeError(f"simulated crash mid-invocation: {cell}")
        return ProviderResponse(
            raw_response=_valid_raw(),
            provenance=_provenance(self.role_sha256, f"{target_holdout}-{arm}"),
        )


def _invocation_count(journal: PredictionJournal, cell=None) -> int:
    records = journal.read_records()
    return sum(
        1
        for rec in records
        if rec.get("record_type") == "invocation"
        and (cell is None or (rec["target_holdout"], rec["arm"]) == cell)
    )


# --------------------------------------------------------------------------- V7

def test_v7_double_claim_is_protocol_violation(tmp_path) -> None:
    """同一セルへの二度目の claim record は protocol violation として拒否される。"""
    journal = PredictionJournal(tmp_path / "journal.jsonl")
    claim = {
        "record_type": "claim",
        "target_holdout": "rr20",
        "arm": "on",
        "decision_method": "selector_agent",
        "input_payload_sha256": "a" * 64,
        "payload_path": "artifacts/payload_rr20_on.json",
        "claimed_at": "2026-07-16T00:00:00Z",
    }
    journal.append(claim)
    journal.append(dict(claim))  # 同一セルの二度目の claim

    with pytest.raises(PredictionRunnerError, match="二重 claim"):
        resolve_journal(journal.read_records())


def test_v7_claim_then_crash_stays_missing_without_recall(tmp_path) -> None:
    """claim 後 crash → 再起動で当該セルは missing 恒久確定、再呼出も invocation 追記もない。"""
    freeze = _freeze()
    journal = PredictionJournal(tmp_path / "journal.jsonl")
    root = tmp_path
    artifact_root = tmp_path / "artifacts"

    # 第 1 走: 最初の agent セルの invocation 中に crash させる。
    crashing = _RecordingProvider(crash_on={FIRST_AGENT_CELL})
    with pytest.raises(RuntimeError, match="simulated crash"):
        drive_journal(
            freeze=freeze, journal=journal, artifact_root=artifact_root,
            root=root, provider=crashing,
        )

    # crash 後: claim は durable、invocation は 1 件も書かれていない。
    statuses = resolve_journal(journal.read_records())
    assert statuses[FIRST_AGENT_CELL].kind == "claimed_missing"
    assert _invocation_count(journal, FIRST_AGENT_CELL) == 0
    invocations_before = _invocation_count(journal)

    # 再起動: 成功する provider を注入して drive をやり直す。
    resumed = _RecordingProvider()
    statuses = drive_journal(
        freeze=freeze, journal=journal, artifact_root=artifact_root,
        root=root, provider=resumed,
    )

    # 恒久 missing: 当該セルは再呼出されず invocation は依然 0 件。
    assert FIRST_AGENT_CELL not in resumed.called
    assert statuses[FIRST_AGENT_CELL].kind == "claimed_missing"
    assert _invocation_count(journal, FIRST_AGENT_CELL) == 0

    # 他の未着手 agent セルだけは再起動時に前進する (missing の巻き添えにしない)。
    assert set(resumed.called) == AGENT_CELLS - {FIRST_AGENT_CELL}
    invocations_after = _invocation_count(journal)
    assert invocations_after - invocations_before == len(AGENT_CELLS) - 1

    # missing セルが残る間は freeze を組めない (fail-closed)。
    with pytest.raises(PredictionRunnerError, match="missing"):
        build_rows_from_journal(freeze, journal)


# ------------------------------------------------------------- provider 未配線

def test_production_provider_refuses_before_claiming(tmp_path) -> None:
    """production 未配線 provider は claim を書く前に拒否し journal を汚染しない。"""
    freeze = _freeze()
    journal = PredictionJournal(tmp_path / "journal.jsonl")

    with pytest.raises(PredictionRunnerError, match="未解禁"):
        drive_journal(
            freeze=freeze, journal=journal, artifact_root=tmp_path / "artifacts",
            root=tmp_path, provider=PRODUCTION_PROVIDER,
        )

    # off arm の static terminal は書かれ得るが、agent セルの claim は 1 件もない。
    records = journal.read_records()
    assert not any(rec["record_type"] == "claim" for rec in records)


def test_unwired_provider_call_raises() -> None:
    """未配線 provider を直接呼んでも fail-closed で拒否する。"""
    with pytest.raises(PredictionRunnerError, match="未配線"):
        PRODUCTION_PROVIDER(target_holdout="rr20", arm="on", payload={})


# ------------------------------------------------------------- protocol 違反

def test_invocation_without_claim_is_protocol_violation(tmp_path) -> None:
    journal = PredictionJournal(tmp_path / "journal.jsonl")
    journal.append({
        "record_type": "invocation",
        "target_holdout": "rr20",
        "arm": "on",
        "status": "valid",
        "choice_id": "c01",
        "rationale": "x",
        "parser_error_code": None,
        "raw_response_path": "artifacts/raw_rr20_on.txt",
        "raw_sha256": "b" * 64,
        "receipt": {},
    })
    with pytest.raises(PredictionRunnerError, match="claim なき invocation"):
        resolve_journal(journal.read_records())


def test_static_terminal_on_agent_arm_is_rejected(tmp_path) -> None:
    journal = PredictionJournal(tmp_path / "journal.jsonl")
    journal.append({
        "record_type": "static_terminal",
        "target_holdout": "rr20",
        "arm": "on",
        "decision_method": "static_default",
        "choice_id": "c06",
    })
    with pytest.raises(PredictionRunnerError, match="off arm 専用"):
        resolve_journal(journal.read_records())


def test_unknown_record_type_is_rejected(tmp_path) -> None:
    journal_path = tmp_path / "journal.jsonl"
    journal_path.write_text(
        json.dumps({"record_type": "bogus", "target_holdout": "rr20", "arm": "on"}) + "\n",
        encoding="utf-8",
    )
    with pytest.raises(PredictionRunnerError, match="record_type"):
        resolve_journal(PredictionJournal(journal_path).read_records())


# ------------------------------------------------------------- 正常駆動

def test_off_arms_are_static_terminal_without_invocation(tmp_path) -> None:
    """off arm 2 セルは invocation を持たない static terminal として区別される。"""
    freeze = _freeze()
    journal = PredictionJournal(tmp_path / "journal.jsonl")
    statuses = drive_journal(
        freeze=freeze, journal=journal, artifact_root=tmp_path / "artifacts",
        root=tmp_path, provider=_RecordingProvider(),
    )
    for cell in OFF_CELLS:
        assert statuses[cell].kind == "static"
        assert statuses[cell].invocation is None
    # off セルに invocation record は存在しない。
    for cell in OFF_CELLS:
        assert _invocation_count(journal, cell) == 0


def test_invalid_raw_recorded_as_invalid_without_fallback(tmp_path) -> None:
    """strict parser を通らない応答は invalid として記録し既定構成へ fallback しない。"""
    freeze = _freeze()
    journal = PredictionJournal(tmp_path / "journal.jsonl")

    class _BadProvider(_RecordingProvider):
        def __call__(self, *, target_holdout, arm, payload):
            self.called.append((target_holdout, arm))
            return ProviderResponse(
                raw_response="```json\n{}\n```",  # markdown fence → parser 拒否
                provenance=_provenance(self.role_sha256, f"{target_holdout}-{arm}"),
            )

    statuses = drive_journal(
        freeze=freeze, journal=journal, artifact_root=tmp_path / "artifacts",
        root=tmp_path, provider=_BadProvider(),
    )
    for cell in AGENT_CELLS:
        invocation = statuses[cell].invocation
        assert invocation is not None
        assert invocation["status"] == "invalid"
        assert invocation["choice_id"] is None  # fallback しない
        assert invocation["parser_error_code"] == "markdown_fence"


# --------------------------------------------------- freeze/journal payload 束縛

def _diverged_freeze(freeze: dict) -> dict:
    """holdout ID・derangement を保ったまま descriptor だけ変えた freeze を作る。

    threads を変えると各 holdout の descriptor projection (scale.threads) が変わり、
    build_prediction_jobs が算出する input_payload_sha256 が原 freeze と一致しなくなる。
    """
    diverged = json.loads(json.dumps(freeze))
    for entry in diverged["holdouts"].values():
        entry["threads"] = int(entry["threads"]) * 2
    return diverged


def test_build_rows_rejects_journal_bound_to_other_freeze(tmp_path) -> None:
    """freeze A で駆動した journal を別 descriptor の freeze B で materialize すると拒否。

    claim が束縛した canonical payload sha を job と照合しなければ、agent が実際に見た
    payload と異なる descriptor を消費したと誤って certified される (provenance 汚染)。
    """
    freeze_a = _freeze()
    journal = PredictionJournal(tmp_path / "journal.jsonl")
    drive_journal(
        freeze=freeze_a, journal=journal, artifact_root=tmp_path / "artifacts",
        root=tmp_path, provider=_RecordingProvider(),
    )
    # 原 freeze では全 agent セルが解決し build_rows は通る (回帰防止)。
    rows = build_rows_from_journal(freeze_a, journal)
    assert len(rows) == len(AGENT_CELLS) + len(OFF_CELLS)

    # 同一 holdout ID・derangement のまま descriptor だけ変えた freeze で付け替えを試みる。
    freeze_b = _diverged_freeze(freeze_a)
    # job sha が実際に分岐していること (テストの前提) を確認する。
    from orchestrator.campaign.s8b_selector_freeze import build_prediction_jobs
    sha_a = {(j["target_holdout"], j["arm"]): j["input_payload_sha256"]
             for j in build_prediction_jobs(freeze_a) if j["arm"] in ("on", "swapped")}
    sha_b = {(j["target_holdout"], j["arm"]): j["input_payload_sha256"]
             for j in build_prediction_jobs(freeze_b) if j["arm"] in ("on", "swapped")}
    assert all(sha_a[c] != sha_b[c] for c in sha_a)

    with pytest.raises(PredictionRunnerError, match="freeze/journal 束縛違反"):
        build_rows_from_journal(freeze_b, journal)


# ------------------------------------------------------------- materialize 統合

def _fixture_head(root: Path) -> str:
    def _git(*args: str) -> str:
        return subprocess.run(
            ["git", *args], cwd=root, check=True, text=True,
            stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        ).stdout.strip()

    _git("init", "-q")
    _git(
        "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false",
        "commit", "--allow-empty", "-q", "-m", "fixture",
    )
    return _git("rev-parse", "HEAD")


def _sources(root: Path) -> dict:
    originals = {
        "holdout_freeze": FREEZE_PATH,
        "builder": ROOT / "orchestrator/campaign/s8b_selector_input.py",
        "role": ROOT / ".claude/agents/selector-8b.md",
        "input_schema": ROOT / "orchestrator/campaign/s8b_selector_catalog.json",
        "output_schema": ROOT / "orchestrator/campaign/s8b_selector_output_schema.json",
    }
    records = {}
    for name, original in originals.items():
        destination = root / "source" / name
        destination.parent.mkdir(parents=True, exist_ok=True)
        destination.write_bytes(original.read_bytes())
        records[name] = {
            "path": f"source/{name}",
            "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
        }
    return records


def _policy() -> dict:
    return {
        "attempts_per_agent_cell": 1,
        "retry": False,
        "reuse_equal_payload_output": False,
        "fresh_context": True,
        "declared_tools": [],
    }


def test_materialize_seals_predictions_and_verifies(tmp_path) -> None:
    """全セル解決 → selector_predictions.json を exclusive-create で封印し verify を通す。"""
    freeze = _freeze()
    root = tmp_path
    head = _fixture_head(root)
    sources = _sources(root)
    journal = PredictionJournal(root / "journal.jsonl")

    drive_journal(
        freeze=freeze, journal=journal, artifact_root=root / "artifacts",
        root=root, provider=_RecordingProvider(role_sha256=sources["role"]["sha256"]),
    )

    predictions_path = root / "output/s8b-freeze/selector_predictions.json"
    document = materialize_predictions(
        freeze=freeze,
        journal=journal,
        predictions_path=predictions_path,
        generated_at="2026-07-16T00:00:00Z",
        pre_oracle_head=head,
        sources=sources,
        execution_policy=_policy(),
    )
    # selector_basis が束縛されている (既存 API 経由)。
    assert document["selector_basis_sha256"]
    verify_prediction_freeze(document, freeze=freeze, root=root)

    # exclusive-create: 二度目の封印は拒否される。
    with pytest.raises(Exception):
        materialize_predictions(
            freeze=freeze,
            journal=journal,
            predictions_path=predictions_path,
            generated_at="2026-07-16T00:00:00Z",
            pre_oracle_head=head,
            sources=sources,
            execution_policy=_policy(),
        )
