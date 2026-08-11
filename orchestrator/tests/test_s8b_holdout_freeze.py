# -*- coding: utf-8 -*-
"""8b holdout freeze の検索、束縛、改竄検出の限定テスト。"""
from __future__ import annotations

import copy
import hashlib
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import s8b_holdout_freeze as M  # noqa: E402
from orchestrator.campaign import t080_freeze_migration as T080  # noqa: E402
import s8b_v2_freeze_fixture as V2FIX  # noqa: E402
import t080_fixture_roots as FIXTURE_ROOTS  # noqa: E402


_V2_CANONICAL_PROBE_DOCUMENT = {
    "z_scientific": 1e2,
    "m_label": "測定",
    "a_budget": {"as_int": 100, "as_float": 100.0},
}
_V2_WRITER_RAW_LITERAL = (
    b'{"a_budget":{"as_float":100.0,"as_int":100},'
    b'"m_label":"\xe6\xb8\xac\xe5\xae\x9a","z_scientific":100.0}\n'
)
_V2_WRITER_SHA256_LITERAL = (
    "da5d41c6a6146af354a91ebcc640e4e2785155a2e7c1911e3a54e97ce61e790f"
)


def _axis_value(holdout_name: str, axis: str) -> str:
    keys = {"rratio": M.RRATIO_KEY, "skew": M.SKEW_KEY, "rmw": M.RMW_KEY}
    return M.HOLDOUTS[holdout_name]["ycsb"][keys[axis]]


def _three_axis_text(ratio: str, encoding: int = 0, *, omit: str | None = None) -> str:
    values = {
        "rratio": ratio,
        "skew": _axis_value("rr80", "skew"),
        "rmw": _axis_value("rr80", "rmw"),
    }
    parts = []
    for axis, value in values.items():
        if axis != omit:
            parts.append(M.concrete_axis_encodings(axis, value)[encoding])
    return "\n".join(parts) + "\n"


def _write(path: Path, text: str) -> str:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding="utf-8")
    return path.as_posix()


def _positive_text(encoding: int = 0) -> str:
    return _three_axis_text(M._POSITIVE_RATIO, encoding)


def _positive_fixture_report() -> dict:
    """外部固定 fixture だけを明示注入し、repo 全体は検索しない。"""
    return M.search_repository(
        FIXTURE_ROOTS.REPO_ROOT,
        files=[FIXTURE_ROOTS.POSITIVE_CONTROL_PATH],
    )


def test_t080_positive_control_fixture_raw_bytes_match_test_pin():
    payload = FIXTURE_ROOTS.POSITIVE_CONTROL_FILE.read_bytes()

    assert hashlib.sha256(payload).hexdigest() == FIXTURE_ROOTS.POSITIVE_CONTROL_SHA256


def test_t080_positive_control_test_pins_match_production_literals():
    # raw bytes の hash node を独立させたうえで、別値源の三 literal を相互固定する。
    assert FIXTURE_ROOTS.POSITIVE_CONTROL_SHA256 == T080.POSITIVE_CONTROL_SHA256
    assert FIXTURE_ROOTS.POSITIVE_CONTROL_PATH == T080.POSITIVE_CONTROL_PATH
    assert FIXTURE_ROOTS.POSITIVE_CONTROL_ROOT_KEY == T080.POSITIVE_CONTROL_ROOT_KEY


def test_t080_positive_control_kills_predicate_only_rr51_mutant(monkeypatch):
    baseline = _positive_fixture_report()["positive_control"]
    assert baseline["hit_count"] == 1
    assert baseline["hit_paths"] == [FIXTURE_ROOTS.POSITIVE_CONTROL_PATH]

    original_expressions = M._expressions

    def rr51_positive_expressions(rratio: str, skew: str, rmw: str) -> dict:
        expressions = original_expressions(rratio, skew, rmw)
        if rratio == M._POSITIVE_RATIO:
            expressions["rratio"] = M.RRATIO_TEMPLATE.replace("<v>", "5" + "1")
        return expressions

    with monkeypatch.context() as mutant:
        mutant.setattr(M, "_expressions", rr51_positive_expressions)
        mutated = _positive_fixture_report()["positive_control"]

    assert mutated["hit_count"] == 0
    assert mutated["hit_paths"] == []
    assert mutated["expressions"]["rratio"] != baseline["expressions"]["rratio"]
    assert mutated["expressions"]["skew"] == baseline["expressions"]["skew"]
    assert mutated["expressions"]["rmw"] == baseline["expressions"]["rmw"]

    reverted = _positive_fixture_report()["positive_control"]
    assert reverted["hit_count"] == 1
    assert reverted["hit_paths"] == [FIXTURE_ROOTS.POSITIVE_CONTROL_PATH]
    assert reverted["expressions"] == baseline["expressions"]


def _known_axes() -> dict:
    entries = {}
    for workload in M.KNOWN_READ_RATIOS:
        entries[workload] = {}
        for index, name in enumerate(M.VARIANT_NAMES):
            entries[workload][name] = {
                "identity": workload + "-" + name,
                "payload": {
                    "index": index,
                    "reference_fitness_tps": 100 + index,
                    "nested": [{"reference_points": {"x": index}}],
                },
                "remeasure_reference": {"value": index},
                "sources": [{"path": workload + "/source"}],
            }
    return {"entries": entries}


def _synthetic_freeze_root(tmp_path: Path) -> tuple[Path, list[str], str]:
    root = tmp_path / "repo"
    _write(root / M.DESIGN_REL, "design fixture\n")
    known_path = root / M.KNOWN_AXES_REL
    known_path.parent.mkdir(parents=True, exist_ok=True)
    known_path.write_text(json.dumps(_known_axes()), encoding="utf-8")
    generator_path = root / M.SCRIPT_REL
    generator_path.parent.mkdir(parents=True, exist_ok=True)
    shutil.copyfile(Path(M.__file__), generator_path)
    ccbench = root / "external/ccbench"
    ccbench.mkdir(parents=True)
    _git(ccbench, "init", "-q")
    _git(
        ccbench, "-c", "user.name=fixture", "-c",
        "user.email=fixture@example.invalid", "-c", "commit.gpgsign=false",
        "commit", "--allow-empty", "-qm", "ccbench fixture",
    )
    rel = "fixtures/positive.txt"
    _write(root / rel, _positive_text())
    return root, [rel], "a" * 40


def test_file_level_conjunction_requires_all_three_axes(tmp_path):
    ratio = _axis_value("rr80", "rratio")
    full = tmp_path / "full.txt"
    partial = tmp_path / "partial.txt"
    _write(full, _three_axis_text(ratio))
    _write(partial, _three_axis_text(ratio, omit="rmw"))

    report = M.search_repository(tmp_path, [full, partial])
    result = report["holdouts"]["rr80"]
    assert result["conjunction_hits"] == ["full.txt"]
    assert result["per_axis_counts"] == {"rratio": 2, "skew": 2, "rmw": 1}


def test_all_three_canonical_encodings_are_detected(tmp_path):
    ratio = _axis_value("rr80", "rratio")
    files = []
    for encoding in range(3):
        path = tmp_path / ("encoding-" + str(encoding) + ".txt")
        _write(path, _three_axis_text(ratio, encoding))
        files.append(path)

    hits = M.search_repository(tmp_path, files)["holdouts"]["rr80"]["conjunction_hits"]
    assert hits == ["encoding-0.txt", "encoding-1.txt", "encoding-2.txt"]


def test_binary_and_non_utf8_files_are_skipped(tmp_path):
    binary = tmp_path / "binary.dat"
    binary.write_bytes(b"\0" + _three_axis_text(_axis_value("rr80", "rratio")).encode())
    non_utf8 = tmp_path / "non-utf8.dat"
    non_utf8.write_bytes(b"\xff\xfe")
    text = tmp_path / "text.txt"
    _write(text, "irrelevant\n")

    report = M.search_repository(tmp_path, [binary, non_utf8, text])
    assert report["search"]["file_count"] == 3
    assert report["search"]["skipped_binary_count"] == 2
    assert report["holdouts"]["rr80"]["conjunction_hits"] == []


def test_zero_positive_control_fails_closed(tmp_path):
    path = tmp_path / "irrelevant.txt"
    _write(path, "irrelevant\n")
    report = M.search_repository(tmp_path, [path])
    with pytest.raises(M.FreezeError, match="陽性対照が 0 件"):
        M._assert_search_pass(report)


def test_holdout_hit_rejects_generate_and_search_reports_path(
    tmp_path, monkeypatch, capsys,
):
    positive = tmp_path / "positive.txt"
    holdout = tmp_path / "holdout.txt"
    _write(positive, _positive_text())
    _write(holdout, _three_axis_text(_axis_value("rr20", "rratio")))
    files = [positive, holdout]
    report = M.search_repository(tmp_path, files)

    with pytest.raises(M.FreezeError, match="rr20: holdout hit"):
        M.generate(
            confirmed_by="reviewer",
            confirmed_at="date",
            output_path=tmp_path / "freeze.json",
            root=tmp_path,
            files=files,
            frozen_at_head="b" * 40,
        )

    monkeypatch.setattr(M, "search_repository", lambda: report)
    assert M.main(["search"]) == 1
    captured = capsys.readouterr()
    assert "holdout.txt" in captured.out
    assert "fails-closed" in captured.err


def test_binding_anchors_and_recursively_strips_measurements():
    known_axes = _known_axes()
    high = M.build_variant_binding(int(_axis_value("rr80", "rratio")), known_axes)
    low = M.build_variant_binding(int(_axis_value("rr20", "rratio")), known_axes)

    assert high["anchor_workload"] == "read-heavy"
    assert low["anchor_workload"] == "write-heavy"
    assert high["distances"] == {"read-heavy": 15, "balanced": 30, "write-heavy": 75}
    assert low["distances"] == {"read-heavy": 75, "balanced": 30, "write-heavy": 15}
    assert high["stripped_keys"] == sorted(M.STRIP_KEYS)
    serialized = json.dumps(high["entries"], sort_keys=True)
    assert all(key not in serialized for key in M.STRIP_KEYS)
    assert high["entries"]["stock_common"]["sources"]
    assert known_axes["entries"]["read-heavy"]["stock_common"]["remeasure_reference"]

    with pytest.raises(M.FreezeError, match="tie"):
        M.select_anchor(50, {"left": 40, "right": 60})


def test_generate_refuses_overwrite_and_requires_confirmation(tmp_path):
    existing = tmp_path / "freeze.json"
    existing.write_text("{}", encoding="utf-8")
    with pytest.raises(M.FreezeError, match="既に存在"):
        M.generate(
            confirmed_by="reviewer", confirmed_at="date", output_path=existing,
        )

    root, files, head = _synthetic_freeze_root(tmp_path)
    with pytest.raises(M.FreezeError, match="confirmed-by"):
        M.generate(
            confirmed_by="", confirmed_at="date",
            output_path=tmp_path / "missing-confirmation.json",
            root=root, files=files, frozen_at_head=head,
        )
    with pytest.raises(SystemExit):
        M.main(["generate", "--confirmed-at", "date"])


def test_verify_rejects_source_hash_and_binding_tamper(tmp_path):
    root, files, head = _synthetic_freeze_root(tmp_path)
    freeze = tmp_path / "freeze.json"
    doc = M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=freeze,
        root=root, files=files, frozen_at_head=head,
    )
    M.verify(freeze, root=root, files=files, current_head=head)

    hash_tamper = copy.deepcopy(doc)
    hash_tamper["design_source"]["sha256"] = "0" * 64
    hash_path = tmp_path / "hash-tamper.json"
    hash_path.write_text(json.dumps(hash_tamper), encoding="utf-8")
    with pytest.raises(M.FreezeError, match="design_source sha256 不一致"):
        M.verify(hash_path, root=root, files=files, current_head=head)

    binding_tamper = copy.deepcopy(doc)
    binding_tamper["holdouts"]["rr80"]["variant_binding"]["entries"][
        "stock_common"
    ]["identity"] = "tampered"
    binding_path = tmp_path / "binding-tamper.json"
    binding_path.write_text(json.dumps(binding_tamper), encoding="utf-8")
    with pytest.raises(M.FreezeError, match="variant_binding 不一致"):
        M.verify(binding_path, root=root, files=files, current_head=head)


def test_verify_tolerates_per_axis_drift_and_rejects_snapshot_tamper(tmp_path):
    root, files, head = _synthetic_freeze_root(tmp_path)
    freeze = tmp_path / "freeze.json"
    doc = M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=freeze,
        root=root, files=files, frozen_at_head=head,
    )

    # 生成後に単一軸 (skew+rmw) だけ一致する無関係ファイルが増えても、conjunction に
    # 至らない限り verify は通る (per_axis_counts の経時ドリフト耐性)。
    drift_rel = _write(
        root / "fixtures/drift.txt",
        _three_axis_text(_axis_value("rr80", "rratio"), omit="rratio"),
    )
    drifted = files + ["fixtures/drift.txt"]
    M.verify(freeze, root=root, files=drifted, current_head=head)

    # スナップショット改竄: 記録済み per_axis_counts を書き換えると hash 再計算で落ちる。
    tampered = copy.deepcopy(doc)
    tampered["holdouts"]["rr80"]["unknownness_check"]["per_axis_counts"]["rratio"] += 1
    tampered_path = tmp_path / "snapshot-tamper.json"
    tampered_path.write_text(json.dumps(tampered), encoding="utf-8")
    with pytest.raises(M.FreezeError, match="zero_hit_output_sha256"):
        M.verify(tampered_path, root=root, files=drifted, current_head=head)

    # 実走後 (holdout 条件が repo に記録され既知化) は現時点有効性で落ちる。
    _write(root / "fixtures/post-run.txt",
           _three_axis_text(_axis_value("rr80", "rratio")))
    with pytest.raises(M.FreezeError, match="holdout hit"):
        M.verify(freeze, root=root, files=drifted + ["fixtures/post-run.txt"],
                 current_head=head)


def _git(root: Path, *args: str) -> str:
    return subprocess.run(
        ["git", *args], cwd=root, check=True, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    ).stdout.strip()


def _commit_all(root: Path) -> str:
    """root を git repo 化し全ファイルを 1 commit にして実在 HEAD SHA を返す。"""
    _git(root, "init", "-q")
    _git(root, "add", "-A")
    _git(
        root, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-q", "-m", "gen1",
    )
    return _git(root, "rev-parse", "HEAD")


def _empty_search_repo(tmp_path: Path) -> Path:
    """root と ccbench の tmp git repo を作り、実列挙経路を使えるようにする。"""
    root = tmp_path / "repo"
    root.mkdir()
    _git(root, "init", "-q")
    ccbench = root / "external/ccbench"
    ccbench.mkdir(parents=True)
    _git(ccbench, "init", "-q")
    return root


def _report_bytes(report: dict) -> bytes:
    return json.dumps(
        report, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
    ).encode("utf-8")


def test_exact_exemption_matching_bytes_is_not_scanned_but_is_enumerated(tmp_path):
    root = _empty_search_repo(tmp_path)
    rel = "output/s8b-freeze/active.json"
    positive_rel = "fixtures/positive.txt"
    path = root / rel
    _write(path, _three_axis_text(_axis_value("rr80", "rratio")))
    _write(root / positive_rel, _positive_text())

    report = M.search_repository(root, exempt_exact={rel: M._sha256(path)})

    assert M.enumerate_repository_files(root) == (positive_rel, rel)
    assert report["search"]["file_count"] == 2
    assert report["search"]["excluded_paths"] == []
    assert report["holdouts"]["rr80"]["conjunction_hits"] == []
    M._assert_search_pass(report)


def test_exact_exemption_hash_mismatch_is_scanned_and_hits(tmp_path):
    root = _empty_search_repo(tmp_path)
    rel = "output/s8b-freeze/active.json"
    _write(root / rel, _three_axis_text(_axis_value("rr80", "rratio")))

    report = M.search_repository(root, exempt_exact={rel: "0" * 64})

    assert report["holdouts"]["rr80"]["conjunction_hits"] == [rel]


def test_exact_exemption_unknown_non_hit_file_is_still_scanned(tmp_path):
    root = _empty_search_repo(tmp_path)
    rel = "output/s8b-freeze/unknown.json"
    ratio = _axis_value("rr80", "rratio")
    _write(root / rel, M.concrete_axis_encodings("rratio", ratio)[0] + "\n")
    _write(root / "fixtures/positive.txt", _positive_text())

    report = M.search_repository(root, exempt_exact={})

    assert report["holdouts"]["rr80"]["per_axis_counts"] == {
        "rratio": 1, "skew": 1, "rmw": 1,
    }
    assert report["holdouts"]["rr80"]["conjunction_hits"] == []
    M._assert_search_pass(report)


def test_exact_exemption_unknown_hit_file_is_detected(tmp_path):
    root = _empty_search_repo(tmp_path)
    rel = "output/s8b-freeze/unknown.json"
    # concrete 三軸 encoding は helper 内で実行時結合し、test source へ同居させない。
    _write(root / rel, _three_axis_text(_axis_value("rr20", "rratio")))

    report = M.search_repository(root, exempt_exact={})

    assert report["holdouts"]["rr20"]["conjunction_hits"] == [rel]


@pytest.mark.parametrize("exempt_exact", [None, {}])
def test_similar_freeze_prefix_is_always_scanned(tmp_path, exempt_exact):
    root = _empty_search_repo(tmp_path)
    rel = "output/s8b-freeze-evil/hit.json"
    _write(root / rel, _three_axis_text(_axis_value("rr80", "rratio")))

    report = M.search_repository(root, exempt_exact=exempt_exact)

    assert report["holdouts"]["rr80"]["conjunction_hits"] == [rel]


def test_exempt_none_preserves_v1_prefix_report_bytes(tmp_path):
    root = _empty_search_repo(tmp_path)
    included = "fixtures/positive.txt"
    excluded = "output/s8b-freeze/hidden.json"
    _write(root / included, _positive_text())
    _write(root / excluded, _three_axis_text(_axis_value("rr80", "rratio")))

    legacy_report = M.search_repository(root, files=[included])
    default_report = M.search_repository(root, exempt_exact=None)

    assert _report_bytes(default_report) == _report_bytes(legacy_report)
    assert default_report["search"]["excluded_paths"] == list(M.EXCLUDED_PATHS)
    assert default_report["holdouts"]["rr80"]["conjunction_hits"] == []


def test_verify_rejects_active_generation_worktree_drift(tmp_path):
    # v1 単一 filename freeze は唯一の発効中 (active) 世代。生成後に設計本文を worktree で
    # 改変すると、frozen_at_head 時点の blob が recorded sha256 と一致していても、verify は
    # worktree 完全一致を要求して拒否する (active 世代のドリフト検知)。blob 救済は世代別
    # 不変 filename + 承認束縛を伴う v2 の旧世代専用であり、唯一の active 世代へ適用すると
    # 設計本文の worktree 改変が骨抜きになる (fail-open) ため、ここでは通してはいけない。
    root, files, _ = _synthetic_freeze_root(tmp_path)
    head1 = _commit_all(root)
    freeze = tmp_path / "freeze.json"
    doc = M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=freeze,
        root=root, files=files, frozen_at_head=head1,
    )
    M.verify(freeze, root=root, files=files)

    # 設計本文を worktree で改変 + 再 commit。frozen_at_head=head1 の blob は不変で
    # recorded と一致し (blob 救済なら通ってしまう) が、worktree の現物は record と食い違う。
    (root / M.DESIGN_REL).write_text("design fixture drifted body\n", encoding="utf-8")
    _git(
        root, "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "commit.gpgsign=false", "commit", "-aqm", "gen2",
    )
    assert M._sha256(root / M.DESIGN_REL) != doc["design_source"]["sha256"]
    with pytest.raises(M.FreezeError, match="design_source sha256 不一致"):
        M.verify(freeze, root=root, files=files)


def test_verify_rejects_unratified_generation_documents(tmp_path):
    root, files, head = _synthetic_freeze_root(tmp_path)
    freeze = tmp_path / "freeze.json"
    doc = M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=freeze,
        root=root, files=files, frozen_at_head=head,
    )
    M.verify(freeze, root=root, files=files, current_head=head)

    # 世代 schema field をどれか 1 つでも持つ document は一律 invalid (承認束縛未裁定)。
    for field in sorted(M.GENERATION_SCHEMA_FIELDS):
        generation = copy.deepcopy(doc)
        generation[field] = "x" if field != "supersedes_sha256" else "a" * 64
        gen_path = tmp_path / f"generation-{field}.json"
        gen_path.write_text(json.dumps(generation), encoding="utf-8")
        with pytest.raises(M.FreezeError, match="未承認世代 document は発効しない"):
            M.verify(gen_path, root=root, files=files, current_head=head)


def _active_t080_resolution(*, holdout_sha256: str = T080.HOLDOUT_RAW_SHA256):
    receipt = {
        "artifacts": {
            "holdout": {"raw_sha256": holdout_sha256},
        },
    }
    return T080.ReceiptResolution(
        "active-valid", (), {"migration_id": "T-080"}, "a" * 40,
        receipt=receipt,
    )


def _t080_artifact_root(tmp_path: Path) -> tuple[Path, Path, Path]:
    root = tmp_path / "repo"
    holdout = root / M.FREEZE_REL
    known = root / T080.KNOWN_AXES_REL
    holdout.parent.mkdir(parents=True)
    known.parent.mkdir(parents=True)
    shutil.copyfile(M.FREEZE_PATH, holdout)
    shutil.copyfile(M.ROOT / T080.KNOWN_AXES_REL, known)
    return root, holdout, known


def test_verify_cli_accepts_active_t080_receipt_exact_match(capsys):
    assert M.main(["verify"]) == 0
    captured = capsys.readouterr()
    assert f"verified: {M.FREEZE_PATH}" in captured.out
    assert captured.err == ""


def test_verify_direct_cli_accepts_active_t080_receipt_exact_match():
    completed = subprocess.run(
        ["python3", M.SCRIPT_REL, "verify"], cwd=M.ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE,
    )

    assert completed.returncode == 0, completed.stderr
    assert f"verified: {M.FREEZE_PATH}" in completed.stdout
    assert completed.stderr == ""


def test_verify_cli_active_receipt_hash_mismatch_is_immediate_red(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    path = root / M.FREEZE_REL
    path.parent.mkdir(parents=True)
    path.write_bytes(b"{}\n")
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: _active_t080_resolution())
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: pytest.fail("hash mismatch で adapter を呼んだ"),
    )
    monkeypatch.setattr(
        M, "verify", lambda *_args, **_kwargs: pytest.fail("legacy fallback へ戻った"),
    )

    with pytest.raises(M.FreezeError, match="capture bytes の sha256 が不一致"):
        M.verify_cli_with_t080_receipt(path, root=root)


def test_verify_cli_same_bytes_at_noncanonical_path_are_rejected(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    alternate = root / "alternate" / "holdout_freeze.json"
    known = root / T080.KNOWN_AXES_REL
    alternate.parent.mkdir(parents=True)
    known.parent.mkdir(parents=True)
    alternate.write_bytes(M.FREEZE_PATH.read_bytes())
    shutil.copyfile(M.ROOT / T080.KNOWN_AXES_REL, known)
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: _active_t080_resolution())
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: T080.AdapterResult((), {"migration_id": "T-080"}),
    )
    monkeypatch.setattr(
        M, "verify", lambda *_args, **_kwargs: pytest.fail("legacy fallback へ戻った"),
    )

    with pytest.raises(M.FreezeError, match="canonical active path でない"):
        M.verify_cli_with_t080_receipt(alternate, root=root)


@pytest.mark.parametrize(
    ("state", "refusals"),
    [
        ("invalid", ("migration-receipt-verify:receipt.invalid",)),
        ("issued-but-missing", ("migration-receipt-verify:receipt.issued_but_missing",)),
    ],
    ids=["invalid", "issued-but-missing"],
)
def test_verify_cli_issued_receipt_failure_never_delegates_to_legacy_verify(
        tmp_path, monkeypatch, state, refusals):
    root, files, _ = _synthetic_freeze_root(tmp_path)
    head = _commit_all(root)
    path = root / M.FREEZE_REL
    M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=path,
        root=root, files=files, frozen_at_head=head,
    )
    M.verify(path, root=root, current_head=head)
    resolution = T080.ReceiptResolution(state, refusals, None, head)
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: resolution)

    with pytest.raises(M.FreezeError, match=f"receipt が有効でない: {state}"):
        M.verify_cli_with_t080_receipt(path, root=root)


def test_verify_cli_known_axes_fire_condition_mismatch_is_red(
        tmp_path, monkeypatch):
    root, path, _known = _t080_artifact_root(tmp_path)
    document = json.loads(path.read_text(encoding="utf-8"))
    document["known_axes_freeze"]["sha256"] = "0" * 64
    raw = json.dumps(document, ensure_ascii=False, sort_keys=True).encode("utf-8")
    path.write_bytes(raw)
    monkeypatch.setattr(
        T080, "verify_receipt",
        lambda **_kwargs: _active_t080_resolution(
            holdout_sha256=hashlib.sha256(raw).hexdigest(),
        ),
    )
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: T080.AdapterResult((), {"migration_id": "T-080"}),
    )

    with pytest.raises(M.FreezeError, match="known_axes 発火条件が一致しない"):
        M.verify_cli_with_t080_receipt(path, root=root)


def test_verify_cli_rejects_bytes_changed_while_receipt_is_verified(
        tmp_path, monkeypatch):
    root = tmp_path / "repo"
    path = root / M.FREEZE_REL
    path.parent.mkdir(parents=True)
    original = M.FREEZE_PATH.read_bytes()
    path.write_bytes(original)

    def swap_after_capture(**_kwargs):
        path.write_bytes(original + b" ")
        return _active_t080_resolution()

    monkeypatch.setattr(T080, "verify_receipt", swap_after_capture)
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: pytest.fail("TOCTOU mismatch で adapter を呼んだ"),
    )
    monkeypatch.setattr(
        M, "verify", lambda *_args, **_kwargs: pytest.fail("legacy fallback へ戻った"),
    )

    with pytest.raises(M.FreezeError, match="検証前後で freeze bytes が変化"):
        M.verify_cli_with_t080_receipt(path, root=root)


@pytest.mark.parametrize(
    ("changed_artifact", "message"),
    [
        ("holdout", "adapter 検証中に freeze bytes が変化"),
        ("known", "adapter 検証中に known_axes bytes が変化"),
    ],
    ids=["holdout", "known-axes"],
)
def test_verify_cli_rejects_artifact_changed_while_adapter_runs(
        tmp_path, monkeypatch, changed_artifact, message):
    root, path, known = _t080_artifact_root(tmp_path)
    target = path if changed_artifact == "holdout" else known
    original = target.read_bytes()
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: _active_t080_resolution())

    def swap_in_adapter(**_kwargs):
        target.write_bytes(original + b" ")
        return T080.AdapterResult((), {"migration_id": "T-080"})

    monkeypatch.setattr(T080, "static_gate_adapter", swap_in_adapter)

    with pytest.raises(M.FreezeError, match=message):
        M.verify_cli_with_t080_receipt(path, root=root)


def test_verify_cli_never_issued_delegates_to_legacy_verify_and_keeps_drift_red(
        tmp_path, monkeypatch):
    root, files, _ = _synthetic_freeze_root(tmp_path)
    head = _commit_all(root)
    path = root / M.FREEZE_REL
    M.generate(
        confirmed_by="reviewer", confirmed_at="date", output_path=path,
        root=root, files=files, frozen_at_head=head,
    )
    M.verify(path, root=root, current_head=head)
    (root / M.DESIGN_REL).write_text("unreceived drift\n", encoding="utf-8")
    never_issued = T080.ReceiptResolution("never-issued", (), None, head)
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: never_issued)
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: pytest.fail("never-issued で adapter を呼んだ"),
    )

    with pytest.raises(M.FreezeError, match="design_source sha256 不一致"):
        M.verify_cli_with_t080_receipt(path, root=root)


def test_read_regular_nofollow_rejects_symlink(tmp_path):
    target = tmp_path / "target"
    target.write_bytes(b"freeze\n")
    link = tmp_path / "canonical"
    link.symlink_to(target)

    with pytest.raises(M.FreezeError, match="nofollow|regular file"):
        M._read_regular_nofollow(link)


def test_read_regular_nofollow_rejects_fifo_without_blocking(tmp_path):
    fifo = tmp_path / "canonical"
    os.mkfifo(fifo)
    script = """
import sys
from pathlib import Path
from orchestrator.campaign import s8b_holdout_freeze as module
try:
    module._read_regular_nofollow(Path(sys.argv[1]))
except module.FreezeError:
    raise SystemExit(0)
raise SystemExit(1)
"""

    completed = subprocess.run(
        [sys.executable, "-c", script, str(fifo)], cwd=M.ROOT, text=True,
        stdout=subprocess.PIPE, stderr=subprocess.PIPE, timeout=3,
    )

    assert completed.returncode == 0, completed.stderr


def test_verify_cli_does_not_mask_unexpected_receipt_exception(tmp_path, monkeypatch):
    root = tmp_path / "repo"
    monkeypatch.setattr(
        T080, "verify_receipt",
        lambda **_kwargs: (_ for _ in ()).throw(ValueError("internal receipt bug")),
    )

    with pytest.raises(ValueError, match="internal receipt bug"):
        M.verify_cli_with_t080_receipt(root / M.FREEZE_REL, root=root)


def test_verify_cli_does_not_mask_unexpected_adapter_exception(tmp_path, monkeypatch):
    root, path, _known = _t080_artifact_root(tmp_path)
    monkeypatch.setattr(T080, "verify_receipt", lambda **_kwargs: _active_t080_resolution())
    monkeypatch.setattr(
        T080, "static_gate_adapter",
        lambda **_kwargs: (_ for _ in ()).throw(TypeError("internal adapter bug")),
    )

    with pytest.raises(TypeError, match="internal adapter bug"):
        M.verify_cli_with_t080_receipt(path, root=root)


def test_source_guard_has_no_static_concrete_axis_encoding():
    module_source = Path(M.__file__).read_text(encoding="utf-8")
    test_source = Path(__file__).read_text(encoding="utf-8")
    sources = (module_source, test_source)
    values = {
        "rratio": {
            _axis_value("rr80", "rratio"),
            _axis_value("rr20", "rratio"),
            M._POSITIVE_RATIO,
        },
        "skew": {_axis_value("rr80", "skew")},
        "rmw": {_axis_value("rr80", "rmw")},
    }
    for axis, axis_values in values.items():
        for value in axis_values:
            for encoding in M.concrete_axis_encodings(axis, value):
                assert all(encoding not in source for source in sources)


def test_v2_candidate_fails_closed_before_reading_inputs_when_budget_unratified(
        tmp_path, monkeypatch):
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", None)

    with pytest.raises(M.FreezeError, match="^budget-approval-not-ratified$"):
        M.build_v2_g1_candidate(
            floor_result_path="missing-result.json",
            budget_path="missing-budget.json",
            root=tmp_path,
        )
    assert M.main([
        "generate-v2-candidate",
        "--floor-result", "missing-result.json",
        "--budget", "missing-budget.json",
    ]) == 1


def test_v1_apis_import_and_execute_when_v2_dependencies_fail_to_import(
        tmp_path):
    root, files, _fixture_head = _synthetic_freeze_root(tmp_path)
    _git(root, "init", "-q")
    _git(root, "config", "user.name", "fixture")
    _git(root, "config", "user.email", "fixture@example.invalid")
    _git(root, "add", "-A")
    _git(root, "commit", "-qm", "v1 import boundary fixture")
    head = _git(root, "rev-parse", "HEAD")
    output = root / M.FREEZE_REL
    script = r'''
import importlib.abc
import pathlib
import sys

blocked = {
    "orchestrator.campaign.env_contract",
    "orchestrator.campaign.s8b_floor_contract",
    "orchestrator.campaign.s8b_floor_stats",
    "orchestrator.campaign.s8b_launch_cert",
}

class BlockV2Dependencies(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname in blocked:
            raise ImportError(f"blocked v2 dependency: {fullname}")
        return None

sys.meta_path.insert(0, BlockV2Dependencies())
from orchestrator.campaign import s8b_holdout_freeze as module

root = pathlib.Path(sys.argv[1])
source = sys.argv[2]
head = sys.argv[3]
output = pathlib.Path(sys.argv[4])
report = module.search_repository(root, files=[source])
assert report["positive_control"]["hit_count"] == 1
generated = module.generate(
    confirmed_by="reviewer",
    confirmed_at="2026-08-11T00:00:00Z",
    output_path=output,
    root=root,
    files=[source],
    frozen_at_head=head,
)
assert module.verify(
    output, root=root, files=[source], current_head=head,
) == generated
assert module.verify_cli_with_t080_receipt(output, root=root) == generated
assert blocked.isdisjoint(sys.modules)
'''
    completed = subprocess.run(
        [sys.executable, "-c", script, str(root), files[0], head, str(output)],
        cwd=Path(M.ROOT), text=True, stdout=subprocess.PIPE,
        stderr=subprocess.PIPE, check=False,
    )
    assert completed.returncode == 0, completed.stderr


def test_v2_candidate_build_and_generate_synthetic_g1(tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )

    document = M.build_v2_g1_candidate(
        floor_result_path=fixture["result_rel"],
        budget_path=fixture["budget_rel"],
        root=root,
    )

    assert frozenset(document) == M.V2_TOP_LEVEL_KEYS
    assert document["schema_version"] == M.V2_SCHEMA_VERSION
    assert document["generation_number"] == 1
    assert document["supersedes_sha256"] == T080.HOLDOUT_RAW_SHA256
    assert document["frozen_at_head"] == fixture["head"]
    assert document["generator"]["path"] == M.SCRIPT_REL
    assert document["known_axes_freeze"] == json.loads(
        (root / M.FREEZE_REL).read_bytes(),
    )["known_axes_freeze"]
    v1 = json.loads((root / M.FREEZE_REL).read_bytes())
    changed_v1_fields = {
        "schema_version", "frozen_at_head", "design_source", "generator", "floor",
        "budget", "refreeze_note",
    }
    assert all(
        document[field] == v1[field]
        for field in M.TOP_LEVEL_KEYS - changed_v1_fields
    )
    assert document["budget"] == fixture["budget"]
    assert document["floor"]["by_holdout"]
    closure = {
        entry["canonical_path"]: entry["sha256"]
        for entry in document["measurement_closure"]
    }
    assert set(fixture["closure_paths"]) <= set(closure)
    assert all(
        closure[rel] == hashlib.sha256((root / rel).read_bytes()).hexdigest()
        for rel in fixture["closure_paths"]
    )

    generated = M.generate_v2_g1_candidate(
        floor_result_path=fixture["result_rel"],
        budget_path=fixture["budget_rel"],
        root=root,
    )
    output = root / M.V2_CANDIDATE_REL
    assert output.read_bytes() == V2FIX.canonical_bytes(generated)
    assert generated == document
    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M.generate_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


def test_v2_candidate_budget_approval_compares_canonical_numeric_bytes(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    changed = copy.deepcopy(fixture["budget"])
    changed["total_bench_s"] = float(changed["total_bench_s"])
    (root / fixture["budget_rel"]).write_bytes(V2FIX.canonical_bytes(changed))

    with pytest.raises(
            M.FreezeError, match="budget-approval-budget-canonical-mismatch"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


@pytest.mark.parametrize("field", ["total_bench_s", "per_holdout_bench_s"])
def test_v2_candidate_rejects_negative_zero_budget_field(
        tmp_path, monkeypatch, field):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    changed = copy.deepcopy(fixture["budget"])
    if field == "total_bench_s":
        changed[field] = -0.0
        reason = r"budget\.total_bench_s が有限非負数でない"
    else:
        holdout_id = sorted(changed[field])[0]
        changed[field][holdout_id] = -0.0
        reason = rf"budget\.per_holdout_bench_s\.{holdout_id} が有限非負数でない"
    (root / fixture["budget_rel"]).write_bytes(V2FIX.canonical_bytes(changed))

    with pytest.raises(M.FreezeError, match=reason):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


def test_v2_candidate_none_pin_rejects_valid_inputs_without_output(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(M, "BUDGET_APPROVAL_SHA256", None)

    with pytest.raises(M.FreezeError, match="^budget-approval-not-ratified$"):
        M.generate_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )
    assert not (root / M.V2_CANDIDATE_REL).exists()


def test_v2_candidate_rejects_floor_not_eligible_for_refreeze(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    result_path = root / fixture["result_rel"]
    result = json.loads(result_path.read_bytes())
    result["eligible_for_refreeze"] = False
    result_path.write_bytes(V2FIX.canonical_bytes(result))

    with pytest.raises(M.FreezeError, match="eligible_for_refreeze が true でない"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


def test_v2_candidate_rejects_closure_hit_absent_from_captured_head(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    untracked = root / "untracked-holdout.txt"
    untracked.write_bytes(V2FIX._holdout_hit_text(M, "rr80"))

    with pytest.raises(M.FreezeError, match="captured HEAD の blob として存在しない"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


def test_v2_candidate_rejects_dirty_closure_without_pinned_diagnostic(
        tmp_path, monkeypatch):
    fixture = V2FIX.candidate_repository(tmp_path, M)
    root = fixture["root"]
    monkeypatch.setattr(
        M, "BUDGET_APPROVAL_SHA256", fixture["approval_sha256"],
    )
    rel = fixture["closure_paths"][0]
    changed = (root / rel).read_bytes() + b"worktree-drift\n"
    (root / rel).write_bytes(changed)

    with pytest.raises(
            M.FreezeError,
            match=r"measurement_closure path が captured HEAD と worktree で不一致"):
        M.build_v2_g1_candidate(
            floor_result_path=fixture["result_rel"],
            budget_path=fixture["budget_rel"],
            root=root,
        )


@pytest.mark.parametrize(
    "output",
    [
        "output/s8b-freeze/holdout_freeze.v2.g1.json",
        "../outside.json",
        "/tmp/outside.json",
        "output//s8b-freeze-candidates/holdout_freeze.v2.g1.json",
        "output/s8b-freeze-candidates/../holdout_freeze.v2.g1.json",
    ],
)
def test_v2_candidate_output_gate_rejects_every_nonfixed_raw_path(tmp_path, output):
    root = tmp_path / "repo"
    root.mkdir()

    with pytest.raises(M.FreezeError):
        M._write_v2_candidate_create_only(root, output, b"{}")
    assert not (tmp_path / "outside.json").exists()


def test_v2_candidate_writer_creates_fixed_root_and_preserves_literal_bytes(tmp_path):
    root = tmp_path / "repo"
    root.mkdir()

    assert M._canonical_bytes(_V2_CANONICAL_PROBE_DOCUMENT) == (
        _V2_WRITER_RAW_LITERAL[:-1]
    )
    assert hashlib.sha256(_V2_WRITER_RAW_LITERAL).hexdigest() == (
        _V2_WRITER_SHA256_LITERAL
    )
    assert _V2_WRITER_RAW_LITERAL.endswith(b"\n")
    M._write_v2_candidate_create_only(
        root, M.V2_CANDIDATE_REL, _V2_WRITER_RAW_LITERAL,
    )

    output = root / M.V2_CANDIDATE_REL
    assert output.read_bytes() == _V2_WRITER_RAW_LITERAL
    assert hashlib.sha256(output.read_bytes()).hexdigest() == (
        _V2_WRITER_SHA256_LITERAL
    )


def test_v2_candidate_output_gate_rejects_symlink_parent(tmp_path):
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "output").mkdir()
    (root / "output" / "s8b-freeze-candidates").symlink_to(outside)

    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M._write_v2_candidate_create_only(
            root, M.V2_CANDIDATE_REL, _V2_WRITER_RAW_LITERAL,
        )
    assert list(outside.iterdir()) == []


def test_v2_candidate_output_gate_rejects_existing_leaf_without_overwrite(
        tmp_path):
    root = tmp_path / "repo"
    leaf = root / M.V2_CANDIDATE_REL
    leaf.parent.mkdir(parents=True)
    leaf.write_bytes(b"existing")

    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M._write_v2_candidate_create_only(
            root, M.V2_CANDIDATE_REL, b"replacement",
        )
    assert leaf.read_bytes() == b"existing"


def test_v2_candidate_output_gate_rejects_symlink_parent_and_existing_leaf(tmp_path):
    root = tmp_path / "repo"
    outside = tmp_path / "outside"
    root.mkdir()
    outside.mkdir()
    (root / "output").mkdir()
    (root / "output" / "s8b-freeze-candidates").symlink_to(outside)

    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M._write_v2_candidate_create_only(root, M.V2_CANDIDATE_REL, b"{}")
    assert list(outside.iterdir()) == []

    (root / "output" / "s8b-freeze-candidates").unlink()
    parent = root / "output" / "s8b-freeze-candidates"
    parent.mkdir()
    leaf = root / M.V2_CANDIDATE_REL
    leaf.write_bytes(b"existing")
    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M._write_v2_candidate_create_only(root, M.V2_CANDIDATE_REL, b"replacement")
    assert leaf.read_bytes() == b"existing"

    leaf.unlink()
    outside_leaf = outside / "existing"
    outside_leaf.write_bytes(b"outside")
    leaf.symlink_to(outside_leaf)
    with pytest.raises(M.FreezeError, match="安全に新規作成できない"):
        M._write_v2_candidate_create_only(root, M.V2_CANDIDATE_REL, b"replacement")
    assert outside_leaf.read_bytes() == b"outside"


def test_v2_candidate_cli_surface_has_no_approval_or_root_arguments():
    parser = M._parser()
    accepted = parser.parse_args([
        "generate-v2-candidate",
        "--floor-result", "result.json",
        "--budget", "budget.json",
    ])
    assert accepted.output == M.V2_CANDIDATE_REL
    for forbidden in ("--approver", "--approved-at", "--budget-approval", "--root"):
        with pytest.raises(SystemExit) as caught:
            parser.parse_args([
                "generate-v2-candidate",
                "--floor-result", "result.json",
                "--budget", "budget.json",
                forbidden, "value",
            ])
        assert caught.value.code == 2
