"""Real-issuer caller tests using tmp campaigns and synthetic scheduled inputs.

The 201-row fixture tests only issue/serialization, not the ability to assemble
a nonempty batch from actual campaigns or to obtain a production publication.
"""

from functools import wraps
import hashlib
import json
from pathlib import Path

import pytest

from orchestrator.campaign import p3_b4_analysis_ledgers as ledgers
from orchestrator.campaign import p3_b4_prerun_caller as caller
from p3_b4_proposal_binding_support import preregistered_publication_root


def _campaign(parent, name, trial, results):
    root = parent / name
    root.mkdir()
    axis = {
        "p3-s4-loop": "silo-backoff-magnitude",
        "p3-s5-sort-loop": "silo-writeset-sort",
        "p3-s8a-trigger-loop": "silo-backoff-trigger-gating",
    }[trial]
    (root / "campaign.lock").write_text(json.dumps({
        "trial": trial,
        "search_config": {"axis": axis, "records": 100000, "reflux": "on",
                          "scale": "silo", "threads": 4},
        "ccbench_commit": "fixture-commit", "search_tag": "fixture",
        "spec_content": "synthetic campaign",
    }), encoding="utf-8")
    (root / "loop_state.json").write_text(json.dumps({
        "iteration": len(results), "start_wall": 1.0, "reverse_recommendations": 0,
        "whiteboard": [
            {"iteration": index + 1, "direction": "decrease", "magnitude": "small",
             "result": result, "delta_pct": None}
            for index, result in enumerate(results)
        ],
    }), encoding="utf-8")
    return root


@pytest.fixture
def observed_issuer(tmp_path, monkeypatch):
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    monkeypatch.chdir(elsewhere)
    real_issue = caller.issuer.issue_b4_prerun_publication
    calls = []

    @wraps(real_issue)
    def observed(**kwargs):
        calls.append(kwargs)
        return real_issue(**kwargs)

    monkeypatch.setattr(caller.issuer, "issue_b4_prerun_publication", observed)
    with preregistered_publication_root(tmp_path / "repository") as root:
        yield root, calls


def _read_payload(capsys):
    captured = capsys.readouterr()
    assert captured.err == ""
    assert len(captured.out.splitlines()) == 1
    payload = json.loads(captured.out)
    assert captured.out == json.dumps(payload, sort_keys=True) + "\n"
    return payload


def _assert_empty_rejection(payload, root, calls):
    assert payload["reason"] == "design_not_feasible"
    assert payload["detail"] == "fewer than 201 eligible scheduled attempts"
    assert payload["candidate_count"] == 0
    assert calls == [{"scheduled_inputs": (), "planned_result_artifacts": (),
                      "publication_root": str(root)}]
    assert not root.exists()


def test_success_only_campaigns_reach_issuer_once_with_empty_batch_and_no_root(
    tmp_path, capsys, observed_issuer,
):
    root, calls = observed_issuer
    specs = [("p3-s4-loop", "base", 4), ("p3-s5-sort-loop", "sort", 1),
             ("p3-s8a-trigger-loop", "trigger", 2)]
    campaigns = [
        _campaign(tmp_path, f"unrelated-{index}", trial, ["success"] * count)
        for index, (trial, _, count) in enumerate(specs)
    ]
    assert caller.main(["--campaign-root", *map(str, campaigns)]) == 2
    payload = _read_payload(capsys)
    _assert_empty_rejection(payload, root, calls)
    assert payload["campaigns"] == [
        {"campaign_root": str(campaign), "driver": driver,
         "whiteboard_rows": count, "rejected_rows": 0}
        for campaign, (_, driver, count) in zip(campaigns, specs)
    ]


def test_mixed_campaigns_report_all_missing_sources_and_never_call_issuer(
    tmp_path, capsys, observed_issuer,
):
    root, calls = observed_issuer
    first = _campaign(tmp_path, "first", "p3-s4-loop", ["success"])
    second = _campaign(tmp_path, "second", "p3-s5-sort-loop", ["success", "rejected"])
    assert caller.main(["--campaign-root", str(first), str(second)]) == 2
    payload = _read_payload(capsys)
    assert payload["reason"] == "scheduled_input_sources_missing"
    assert payload["candidate_count"] == 1
    missing = payload["missing"]
    fields = {item["field"] for item in missing}
    assert fields == {
        "attempt_id", "block_id", "digest_red_classes", "workload",
        "calibrated_workload_member", "initial_proposal_sha256", "bootstrap_member",
        "reference_tps", "reference_snapshot_hash", "reference_receipt_hash",
        "reference_is_unique", "arm_digest_received",
    }
    assert "bootstrap_member" in fields
    assert "calibrated_workload_member" in fields
    assert "reference_is_unique" in fields
    assert "arm_digest_received" in fields
    assert len(missing) == 12
    for item in missing:
        assert item["campaign_root"] == str(second)
        assert item["whiteboard_index"] == 1
        assert item["iteration"] == 2
        assert item["artifact_path"] is None
        assert item["artifact_key"] is None
        assert item["explanation"]
    assert calls == []
    assert not root.exists()


def test_minimal_rejected_row_is_a_candidate(tmp_path, capsys, observed_issuer):
    root, calls = observed_issuer
    campaign = _campaign(tmp_path, "minimal", "p3-s4-loop", [])
    (campaign / "loop_state.json").write_text(
        '{"whiteboard": [{"iteration": 1, "result": "rejected"}]}', encoding="utf-8",
    )
    assert caller.main(["--campaign-root", str(campaign)]) == 2
    payload = _read_payload(capsys)
    assert payload["reason"] == "scheduled_input_sources_missing"
    assert payload["candidate_count"] == 1
    assert len(payload["missing"]) == 12
    assert calls == []
    assert not root.exists()


def test_fail_row_is_not_a_candidate(tmp_path, capsys, observed_issuer):
    root, calls = observed_issuer
    campaign = _campaign(tmp_path, "failed", "p3-s4-loop", ["fail", "success"])
    assert caller.main(["--campaign-root", str(campaign)]) == 2
    _assert_empty_rejection(_read_payload(capsys), root, calls)


def test_publication_root_is_not_an_argument(tmp_path, observed_issuer):
    root, calls = observed_issuer
    campaign = _campaign(tmp_path, "override", "p3-s4-loop", [])
    with pytest.raises(SystemExit) as caught:
        caller.main(["--campaign-root", str(campaign), "--publication-root", str(root)])
    assert caught.value.code == 2
    assert calls == []
    assert not root.exists()


def test_issue_half_serializes_real_receipt_for_a_complete_batch(observed_issuer):
    """Synthetic inputs test issue/serialization only, not real campaign assembly."""
    root, calls = observed_issuer

    def digest(label):
        return hashlib.sha256(label.encode("ascii")).hexdigest()

    batch = tuple(
        ledgers.B4ScheduledAttemptInput(
            schema_version=ledgers.B4_SCHEDULED_ATTEMPT_SCHEMA_VERSION,
            attempt_id=f"attempt-{index:04d}", registry_ordinal=index,
            block_id=f"block-{index:04d}", driver="base",
            reason=ledgers.B4ScheduledAttemptReason.SCHEDULED,
            whiteboard_result=ledgers.B4WhiteboardResult.REJECTED,
            digest_red_classes=(ledgers.B4DigestRedClass.VERIFY_RED,),
            workload="calibrated-workload", calibrated_workload_member=True,
            initial_proposal_sha256=digest(f"proposal-{index}"), bootstrap_member=True,
            reference_tps=(10_000 + index, 1),
            reference_snapshot_hash=digest(f"snapshot-{index}"),
            reference_receipt_hash=digest(f"receipt-{index}"),
            reference_is_unique=True, arm_digest_received=False,
        ) for index in range(201)
    )
    payload, rc = caller.issue(batch)
    assert rc == 0
    assert set(payload) == {"issued"}
    issued = payload["issued"]
    assert set(issued) == {"receipt_path", "receipt_sha256",
                           "issuer_commitment_sha256", "manifest_row_count"}
    assert issued["manifest_row_count"] == 201
    assert issued["receipt_path"] == str(root / "prerun-issuer-receipt.json")
    assert issued["receipt_sha256"] == hashlib.sha256(
        Path(issued["receipt_path"]).read_bytes()
    ).hexdigest()
    planned = caller.planned_result_artifacts_for(batch, root)
    assert [(item.attempt_id, item.artifact_path) for item in planned] == [
        (attempt.attempt_id, str(root / "results" / f"{attempt.attempt_id}.json"))
        for attempt in batch
    ]
    loaded = caller.issuer.load_b4_prerun_publication(str(root))
    assert set(loaded.planned_result_artifacts) == set(planned)
    assert issued["issuer_commitment_sha256"] == loaded.issuer_commitment_sha256
    assert calls == [{"scheduled_inputs": batch, "planned_result_artifacts": planned,
                      "publication_root": str(root)}]
    assert not (root / "results").exists()


@pytest.mark.parametrize("broken", ["checkpoint_absent", "lock_absent", "json",
                                       "whiteboard", "trial", "row",
                                       "result_absent", "deep_json"])
def test_unreadable_campaign_never_calls_issuer(
    tmp_path, capsys, observed_issuer, broken,
):
    root, calls = observed_issuer
    campaign = _campaign(tmp_path, "broken", "p3-s4-loop", ["success"])
    checkpoint = campaign / "loop_state.json"
    lock = campaign / "campaign.lock"
    if broken == "checkpoint_absent":
        checkpoint.unlink()
    elif broken == "lock_absent":
        lock.unlink()
    elif broken == "json":
        lock.write_text("{", encoding="utf-8")
    elif broken == "whiteboard":
        checkpoint.write_text('{"whiteboard": {}}', encoding="utf-8")
    elif broken == "trial":
        lock.write_text('{"trial": "unknown"}', encoding="utf-8")
    elif broken == "result_absent":
        checkpoint.write_text('{"whiteboard": [{"iteration": 1}]}', encoding="utf-8")
    elif broken == "deep_json":
        deep_json = "[" * 100000 + "]" * 100000
        with pytest.raises(RecursionError):
            json.loads(deep_json)
        lock.write_text(deep_json, encoding="utf-8")
    else:
        checkpoint.write_text('{"whiteboard": [null]}', encoding="utf-8")
    assert caller.main(["--campaign-root", str(campaign)]) == 2
    payload = _read_payload(capsys)
    assert payload["reason"] == "campaign_input_unreadable"
    assert payload["campaign_root"] == str(campaign)
    assert payload["detail"]
    assert calls == []
    assert not root.exists()


def test_all_candidates_have_all_missing_fields(tmp_path, capsys, observed_issuer):
    _, calls = observed_issuer
    campaigns = [
        _campaign(tmp_path, "one", "p3-s4-loop", ["rejected", "success", "rejected"]),
        _campaign(tmp_path, "two", "p3-s8a-trigger-loop", ["rejected"]),
    ]
    assert caller.main(["--campaign-root", *map(str, campaigns)]) == 2
    payload = _read_payload(capsys)
    assert payload["candidate_count"] == 3
    assert len(payload["missing"]) == 36
    assert [(item["campaign_root"], item["whiteboard_index"], item["iteration"])
            for item in payload["missing"][::12]] == [
        (str(campaigns[0]), 0, 1), (str(campaigns[0]), 2, 3), (str(campaigns[1]), 0, 1),
    ]
    assert calls == []
