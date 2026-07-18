# -*- coding: utf-8 -*-
"""8b holdout freeze の検索、束縛、改竄検出の限定テスト。"""
from __future__ import annotations

import copy
import json
import os
import shutil
import subprocess
import sys
from pathlib import Path

import pytest


_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, _ORCH)

from campaign import s8b_holdout_freeze as M  # noqa: E402


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
