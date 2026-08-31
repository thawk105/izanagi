# -*- coding: utf-8 -*-
"""mutation local attempt marker の admission 契約を検査する。"""
from __future__ import annotations

import hashlib
import inspect
import json
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[2]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from orchestrator.campaign import mutation_attempt_marker as MAM
from orchestrator.campaign import site_policy
from tools.pegasus import dispatch_compute as DC


def _require_marker() -> dict[str, object]:
    return MAM.require_local_attempt_marker(
        normalize_request_id=DC._normalize_request_id,
        is_regular_pbs_jobid=DC._is_regular_pbs_jobid,
    )


@pytest.fixture
def valid_marker(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> tuple[dict[str, str], Path, Path]:
    dispatch_root = tmp_path / "repo" / "output" / "pegasus-dispatch"
    submission = dispatch_root / "submission"
    submission.mkdir(parents=True)
    request = submission / "request.json"
    request.write_bytes(b'{"task":"mutation"}\n')
    compute_marker = submission / MAM.COMPUTE_MARKER_NAME
    compute_marker.write_text(
        json.dumps(
            {
                "schema_version": "pegasus-compute-visible/v1",
                "pbs_jobid": "0:424242.nqsv",
                "hostname": "bnode114.example",
            }
        )
        + "\n",
        encoding="utf-8",
    )
    binding = MAM.build_binding(
        dispatch_root=dispatch_root,
        submission_dir=submission,
        pbs_jobid="0:424242.nqsv",
        hostname="bnode114.example",
        request_sha256=hashlib.sha256(request.read_bytes()).hexdigest(),
        is_regular_pbs_jobid=DC._is_regular_pbs_jobid,
    )
    monkeypatch.setenv(MAM.MARKER_ENV, MAM.encode_binding(binding))
    monkeypatch.setattr(site_policy.socket, "gethostname", lambda: "bnode114")
    return binding, request, compute_marker


def test_m10_valid_binding_passes_real_site_classifier_and_returns_verified_object(
    valid_marker: tuple[dict[str, str], Path, Path],
) -> None:
    binding, _request, _compute_marker = valid_marker

    observed = _require_marker()

    assert observed == binding
    assert set(observed) == {
        "schema_version",
        "dispatch_root",
        "submission_dir",
        "pbs_jobid",
        "hostname",
        "request_sha256",
    }
    assert site_policy.classify_site("bnode114", {}, False) == site_policy.PEGASUS_COMPUTE


def test_m1_non_compute_hostname_is_rejected_by_real_site_classifier(
    valid_marker: tuple[dict[str, str], Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding, _request, compute_marker = valid_marker
    forged = {**binding, "hostname": "developer-host"}
    monkeypatch.setenv(MAM.MARKER_ENV, MAM.encode_binding(forged))
    document = json.loads(compute_marker.read_text(encoding="utf-8"))
    document["hostname"] = "developer-host"
    compute_marker.write_text(json.dumps(document) + "\n", encoding="utf-8")
    monkeypatch.setattr(site_policy.socket, "gethostname", lambda: "developer-host")
    monkeypatch.setattr(site_policy, "_has_nqsv", lambda: False)
    assert site_policy.classify_site("developer-host", {}, False) == site_policy.OTHER

    with pytest.raises(MAM.MutationAttemptMarkerError, match="compute site"):
        _require_marker()


def test_binding_schema_version_mismatch_is_rejected(
    valid_marker: tuple[dict[str, str], Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding, _request, _compute_marker = valid_marker
    forged = {**binding, "schema_version": "forged/v1"}
    monkeypatch.setenv(MAM.MARKER_ENV, MAM.encode_binding(forged))

    with pytest.raises(MAM.MutationAttemptMarkerError, match="marker schema"):
        _require_marker()


def test_compute_marker_schema_version_mismatch_is_rejected(
    valid_marker: tuple[dict[str, str], Path, Path],
) -> None:
    _binding, _request, compute_marker = valid_marker
    document = json.loads(compute_marker.read_text(encoding="utf-8"))
    document["schema_version"] = "forged/v1"
    compute_marker.write_text(json.dumps(document) + "\n", encoding="utf-8")

    with pytest.raises(MAM.MutationAttemptMarkerError, match="compute-visible.json schema"):
        _require_marker()


def test_binding_and_compute_marker_hostname_mismatch_is_rejected(
    valid_marker: tuple[dict[str, str], Path, Path],
) -> None:
    _binding, _request, compute_marker = valid_marker
    document = json.loads(compute_marker.read_text(encoding="utf-8"))
    document["hostname"] = "bnode999.example"
    compute_marker.write_text(json.dumps(document) + "\n", encoding="utf-8")

    with pytest.raises(MAM.MutationAttemptMarkerError, match="compute-visible.json と不一致"):
        _require_marker()


def test_m2_missing_marker_is_rejected_on_compute(
    valid_marker: tuple[dict[str, str], Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.delenv(MAM.MARKER_ENV)

    with pytest.raises(MAM.MutationAttemptMarkerError, match="marker がありません"):
        _require_marker()


def test_m3_pbs_job_id_mismatch_is_rejected(
    valid_marker: tuple[dict[str, str], Path, Path],
) -> None:
    _binding, _request, compute_marker = valid_marker
    document = json.loads(compute_marker.read_text(encoding="utf-8"))
    document["pbs_jobid"] = "0:777777.nqsv"
    compute_marker.write_text(json.dumps(document) + "\n", encoding="utf-8")

    with pytest.raises(MAM.MutationAttemptMarkerError, match="PBS job ID.*不一致"):
        _require_marker()


def test_m4_current_hostname_mismatch_is_rejected(
    valid_marker: tuple[dict[str, str], Path, Path],
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    monkeypatch.setattr(site_policy.socket, "gethostname", lambda: "bnode999")

    with pytest.raises(MAM.MutationAttemptMarkerError, match="現在の compute node"):
        _require_marker()


def test_m5_request_sha_mismatch_is_rejected(
    valid_marker: tuple[dict[str, str], Path, Path],
) -> None:
    _binding, request, _compute_marker = valid_marker
    request.write_bytes(b'{"task":"mutation","changed":true}\n')

    with pytest.raises(MAM.MutationAttemptMarkerError, match="SHA-256.*不一致"):
        _require_marker()


def test_m6_submission_outside_dispatch_root_is_rejected(
    valid_marker: tuple[dict[str, str], Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding, request, compute_marker = valid_marker
    outside = tmp_path / "outside-submission"
    outside.mkdir()
    (outside / "request.json").write_bytes(request.read_bytes())
    (outside / MAM.COMPUTE_MARKER_NAME).write_bytes(compute_marker.read_bytes())
    forged = {**binding, "submission_dir": str(outside.resolve())}
    monkeypatch.setenv(MAM.MARKER_ENV, MAM.encode_binding(forged))

    with pytest.raises(MAM.MutationAttemptMarkerError, match="dispatch root の外"):
        _require_marker()


def test_m6_submission_symlink_alias_is_not_canonical(
    valid_marker: tuple[dict[str, str], Path, Path],
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    binding, _request, _compute_marker = valid_marker
    alias = tmp_path / "submission-alias"
    alias.symlink_to(binding["submission_dir"], target_is_directory=True)
    forged = {**binding, "submission_dir": str(alias)}
    monkeypatch.setenv(MAM.MARKER_ENV, MAM.encode_binding(forged))

    with pytest.raises(MAM.MutationAttemptMarkerError, match="canonical path"):
        _require_marker()


@pytest.mark.parametrize("leaf", ["request.json", MAM.COMPUTE_MARKER_NAME])
def test_m7_evidence_symlink_is_rejected(
    valid_marker: tuple[dict[str, str], Path, Path],
    leaf: str,
) -> None:
    binding, _request, _compute_marker = valid_marker
    path = Path(binding["submission_dir"]) / leaf
    target = path.with_name(f"{path.name}.target")
    path.rename(target)
    path.symlink_to(target)

    with pytest.raises(MAM.MutationAttemptMarkerError, match="安全に開けません"):
        _require_marker()


@pytest.mark.parametrize("change", ["extra", "missing"])
def test_m8_binding_requires_exact_keys(
    valid_marker: tuple[dict[str, str], Path, Path],
    monkeypatch: pytest.MonkeyPatch,
    change: str,
) -> None:
    binding, _request, _compute_marker = valid_marker
    forged = dict(binding)
    if change == "extra":
        forged["extra"] = "forged"
    else:
        del forged["hostname"]
    monkeypatch.setenv(MAM.MARKER_ENV, MAM.encode_binding(forged))

    with pytest.raises(MAM.MutationAttemptMarkerError, match="field 集合"):
        _require_marker()


@pytest.mark.parametrize("change", ["extra", "missing"])
def test_m8_compute_marker_requires_exact_keys(
    valid_marker: tuple[dict[str, str], Path, Path],
    change: str,
) -> None:
    _binding, _request, compute_marker = valid_marker
    document = json.loads(compute_marker.read_text(encoding="utf-8"))
    if change == "extra":
        document["extra"] = "forged"
    else:
        del document["hostname"]
    compute_marker.write_text(json.dumps(document) + "\n", encoding="utf-8")

    with pytest.raises(MAM.MutationAttemptMarkerError, match="field 集合"):
        _require_marker()


@pytest.mark.parametrize(
    "jobid",
    ["0:424242.nqsv", "424242.nqsv", "424242.server-name", "unknown", "bad"],
)
def test_pbs_job_id_predicate_is_shared_with_dispatcher_authority(jobid: str) -> None:
    assert DC._is_regular_pbs_jobid(jobid) is (jobid not in {"unknown", "bad"})


def test_marker_leaf_has_no_second_pbs_job_id_regex() -> None:
    source = inspect.getsource(MAM)
    assert "_PBS_JOBID_RE" not in source
    assert "A-Za-z0-9_-" not in source


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__]))
