from __future__ import annotations

import copy
import hashlib
import json
import subprocess
from pathlib import Path

import pytest

from orchestrator.campaign.s8b_descriptor import descriptor_for_holdout
from orchestrator.campaign.s8b_selector_freeze import (
    SELECTOR_BASIS_VERSION,
    SelectorFreezeError,
    _load_v1_freeze,
    binding_entry_for_choice,
    build_prediction_freeze,
    build_prediction_jobs,
    main,
    record_agent_attempt,
    selector_basis_preimage,
    selector_basis_sha256,
    verify_prediction_freeze,
    write_prediction_freeze,
)
from orchestrator.campaign.s8b_selector_input import (
    CHOICE_TO_BINDING,
    STATIC_DEFAULT_CHOICE_ID,
    build_selector_payload,
)


ROOT = Path(__file__).resolve().parents[2]
FREEZE_PATH = ROOT / "output/s8b-freeze/holdout_freeze.json"
ARMS = {"on", "off", "swapped"}


def _freeze() -> dict:
    return json.loads(FREEZE_PATH.read_text(encoding="utf-8"))


def _fixture_head(root: Path) -> str:
    """root を git repo 化して空 commit を作り、実在する HEAD SHA を返す。"""
    root.mkdir(parents=True, exist_ok=True)

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


def _raw(choice_id: str, rationale: str = "descriptor と機構の適合を比較した") -> str:
    return json.dumps(
        {
            "schema_version": "8b-selector-output/v1",
            "choice_id": choice_id,
            "rationale": rationale,
        },
        ensure_ascii=False,
        separators=(",", ":"),
    )


def _rows(
    freeze: dict, *, role_sha256: str | None = None, root: Path | None = None,
) -> list[dict]:
    choices = tuple(CHOICE_TO_BINDING)
    role_sha256 = role_sha256 or hashlib.sha256(b"role").hexdigest()
    rows = []
    agent_index = 0
    for job in build_prediction_jobs(freeze):
        if job["arm"] == "off":
            rows.append({
                **job,
                "status": "valid",
                "rationale": None,
                "raw_response_path": None,
                "raw_sha256": None,
                "parser_error_code": None,
                "agent_provenance": None,
            })
            continue
        raw = _raw(choices[agent_index])
        attempt = record_agent_attempt(job=job, raw_output=raw)
        raw_response_path = f"selector-runs/cell-{agent_index}.json"
        if root is not None:
            destination = root / raw_response_path
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_text(raw, encoding="utf-8")
        rows.append({
            **job,
            **attempt,
            "parser_error_code": attempt.get("parser_error_code"),
            "raw_response_path": raw_response_path,
            "agent_provenance": {
                "child_id": f"child-{agent_index}",
                "role_file_sha256": role_sha256,
                "model": "fixture-model",
                "started_at": f"2026-07-16T00:00:0{agent_index}Z",
                "finished_at": f"2026-07-16T00:01:0{agent_index}Z",
                "fresh_context": True,
                "declared_tools": [],
                "observed_tool_events": [],
            },
        })
        agent_index += 1
    return rows


def _sources(root: Path | None = None) -> dict:
    names = ("holdout_freeze", "builder", "role", "input_schema", "output_schema")
    if root is not None:
        originals = {
            "holdout_freeze": FREEZE_PATH,
            "builder": ROOT / "orchestrator/campaign/s8b_selector_input.py",
            "role": ROOT / ".claude/agents/selector-8b.md",
            "input_schema": ROOT / "orchestrator/campaign/s8b_selector_catalog.json",
            "output_schema": ROOT / "orchestrator/campaign/s8b_selector_output_schema.json",
        }
        records = {}
        for name in names:
            destination = root / "source" / name
            destination.parent.mkdir(parents=True, exist_ok=True)
            destination.write_bytes(originals[name].read_bytes())
            records[name] = {
                "path": f"source/{name}",
                "sha256": hashlib.sha256(destination.read_bytes()).hexdigest(),
            }
        return records
    return {
        name: {"path": f"source/{name}", "sha256": hashlib.sha256(name.encode()).hexdigest()}
        for name in names
    }


def _policy() -> dict:
    return {
        "attempts_per_agent_cell": 1,
        "retry": False,
        "reuse_equal_payload_output": False,
        "fresh_context": True,
        "declared_tools": [],
    }


def _make_missing(row: dict) -> None:
    row["status"] = "missing"
    for field in (
        "choice_id", "rationale", "raw_response_path", "raw_sha256",
        "parser_error_code", "agent_provenance",
    ):
        row[field] = None


def _document(
    freeze: dict,
    rows: list[dict] | None = None,
    *,
    root: Path | None = None,
    pre_oracle_head: str | None = None,
) -> dict:
    # 既定の "a"*40 は形式のみ有効な非実在 SHA。build は形式検査までなので通るが、
    # verify では commit 実在検証 (C2-R4) の負例になる。verify するテストは
    # _fixture_head() の実 commit を渡す。
    sources = _sources(root)
    return build_prediction_freeze(
        freeze=freeze,
        rows=(_rows(freeze, role_sha256=sources["role"]["sha256"], root=root)
              if rows is None else rows),
        generated_at="2026-07-16T00:00:00Z",
        pre_oracle_head=pre_oracle_head or "a" * 40,
        sources=sources,
        execution_policy=_policy(),
    )


def _rehash(document: dict) -> None:
    body = {key: value for key, value in document.items() if key != "body_sha256"}
    rendered = json.dumps(
        body, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    )
    document["body_sha256"] = hashlib.sha256(rendered.encode("utf-8")).hexdigest()


def test_build_prediction_jobs_has_six_complete_cells_and_static_off() -> None:
    freeze = _freeze()
    jobs = build_prediction_jobs(freeze)

    assert len(jobs) == 6
    cells = {(job["target_holdout"], job["arm"]) for job in jobs}
    assert cells == {(target, arm) for target in freeze["holdouts"] for arm in ARMS}
    off = [job for job in jobs if job["arm"] == "off"]
    assert len(off) == 2
    assert all(job["decision_method"] == "static_default" for job in off)
    assert all(job["choice_id"] == STATIC_DEFAULT_CHOICE_ID for job in off)
    assert all(job["descriptor_source_holdout"] is None for job in off)
    assert all(job["input_payload_sha256"] is None for job in off)


def test_swapped_uses_deranged_descriptor_without_payload_identity_fields() -> None:
    freeze = _freeze()
    jobs = build_prediction_jobs(freeze)

    for job in jobs:
        if job["arm"] == "off":
            continue
        expected_source = (
            job["target_holdout"]
            if job["arm"] == "on"
            else freeze["derangement"][job["target_holdout"]]
        )
        assert job["descriptor_source_holdout"] == expected_source
        payload = build_selector_payload(
            descriptor_for_holdout(freeze["holdouts"][expected_source])
        )
        assert "arm" not in payload
        assert "target_holdout" not in payload
        rendered = json.dumps(payload, ensure_ascii=False, sort_keys=True)
        assert all(target not in rendered for target in freeze["holdouts"])


def test_record_agent_attempt_valid_and_invalid_never_falls_back() -> None:
    job = next(job for job in build_prediction_jobs(_freeze()) if job["arm"] == "on")
    valid = record_agent_attempt(job=job, raw_output=_raw("c02"))
    invalid = record_agent_attempt(job=job, raw_output="not json")

    assert valid["status"] == "valid"
    assert valid["choice_id"] == "c02"
    assert valid["rationale"]
    assert invalid["status"] == "invalid"
    assert invalid["choice_id"] is None
    assert invalid["parser_error_code"]
    assert invalid["raw_sha256"]
    assert STATIC_DEFAULT_CHOICE_ID not in invalid.values()


def test_binding_resolution_is_target_local_and_unknown_choice_fails() -> None:
    freeze = _freeze()
    for target in freeze["holdouts"]:
        entry = binding_entry_for_choice(freeze, target, "c01")
        key = CHOICE_TO_BINDING["c01"]
        assert entry == freeze["holdouts"][target]["variant_binding"]["entries"][key]
        assert entry is not freeze["holdouts"][target]["variant_binding"]["entries"][key]
    with pytest.raises(SelectorFreezeError, match="unknown selector choice_id"):
        binding_entry_for_choice(freeze, next(iter(freeze["holdouts"])), "c99")


def test_build_prediction_freeze_requires_complete_unique_cells() -> None:
    freeze = _freeze()
    rows = _rows(freeze)
    document = _document(freeze, rows)
    assert len(document["rows"]) == 6

    with pytest.raises(SelectorFreezeError, match="ちょうど6行"):
        _document(freeze, rows[:-1])
    duplicate = copy.deepcopy(rows)
    duplicate[-1] = copy.deepcopy(duplicate[0])
    with pytest.raises(SelectorFreezeError, match="重複"):
        _document(freeze, duplicate)


def test_build_prediction_freeze_rejects_tagged_union_violations() -> None:
    freeze = _freeze()
    off_provenance = _rows(freeze)
    off = next(row for row in off_provenance if row["arm"] == "off")
    off["agent_provenance"] = {"child_id": "forbidden"}
    with pytest.raises(SelectorFreezeError, match="off row に agent provenance"):
        _document(freeze, off_provenance)

    agent_static = _rows(freeze)
    agent = next(row for row in agent_static if row["arm"] == "on")
    agent["decision_method"] = "static_default"
    with pytest.raises(SelectorFreezeError, match="固定 job と不一致"):
        _document(freeze, agent_static)


def test_missing_agent_row_with_null_provenance_builds_and_verifies(
    tmp_path: Path,
) -> None:
    freeze = _freeze()
    head = _fixture_head(tmp_path)
    sources = _sources(tmp_path)
    rows = _rows(
        freeze, role_sha256=sources["role"]["sha256"], root=tmp_path,
    )
    missing = next(row for row in rows if row["arm"] == "on")
    _make_missing(missing)

    document = build_prediction_freeze(
        freeze=freeze,
        rows=rows,
        generated_at="2026-07-16T00:00:00Z",
        pre_oracle_head=head,
        sources=sources,
        execution_policy=_policy(),
    )

    assert len(document["rows"]) == 6
    frozen_missing = next(
        row for row in document["rows"]
        if row["target_holdout"] == missing["target_holdout"]
        and row["arm"] == missing["arm"]
    )
    assert frozen_missing["status"] == "missing"
    assert all(frozen_missing[field] is None for field in (
        "choice_id", "rationale", "raw_response_path", "raw_sha256",
        "parser_error_code", "agent_provenance",
    ))
    verify_prediction_freeze(document, freeze=freeze, root=tmp_path)


def test_missing_agent_row_rejects_provenance_in_build_and_verify(
    tmp_path: Path,
) -> None:
    freeze = _freeze()
    sources = _sources(tmp_path)
    rows = _rows(
        freeze, role_sha256=sources["role"]["sha256"], root=tmp_path,
    )
    missing = next(row for row in rows if row["arm"] == "on")
    provenance = copy.deepcopy(missing["agent_provenance"])
    _make_missing(missing)
    missing["agent_provenance"] = provenance
    with pytest.raises(SelectorFreezeError, match="agent_provenance は null 固定"):
        build_prediction_freeze(
            freeze=freeze,
            rows=rows,
            generated_at="2026-07-16T00:00:00Z",
            pre_oracle_head=_fixture_head(tmp_path),
            sources=sources,
            execution_policy=_policy(),
        )

    good_rows = _rows(
        freeze, role_sha256=sources["role"]["sha256"], root=tmp_path,
    )
    good_missing = next(row for row in good_rows if row["arm"] == "on")
    _make_missing(good_missing)
    document = build_prediction_freeze(
        freeze=freeze,
        rows=good_rows,
        generated_at="2026-07-16T00:00:00Z",
        pre_oracle_head=_fixture_head(tmp_path),
        sources=sources,
        execution_policy=_policy(),
    )
    frozen_missing = next(
        row for row in document["rows"]
        if row["target_holdout"] == good_missing["target_holdout"]
        and row["arm"] == good_missing["arm"]
    )
    frozen_missing["agent_provenance"] = provenance
    _rehash(document)
    with pytest.raises(SelectorFreezeError, match="agent_provenance は null 固定"):
        verify_prediction_freeze(document, freeze=freeze, root=tmp_path)


@pytest.mark.parametrize(
    ("field", "value"),
    (
        ("choice_id", "c01"),
        ("rationale", "forbidden"),
        ("raw_response_path", "selector-runs/forbidden.json"),
        ("raw_sha256", "0" * 64),
        ("parser_error_code", "forbidden"),
    ),
)
def test_missing_agent_row_rejects_non_null_result_fields(
    field: str, value: str,
) -> None:
    freeze = _freeze()
    rows = _rows(freeze)
    missing = next(row for row in rows if row["arm"] == "on")
    _make_missing(missing)
    missing[field] = value

    with pytest.raises(SelectorFreezeError, match="missing"):
        _document(freeze, rows)


def test_swapped_expectations_are_derived_only_from_deranged_on_rows() -> None:
    freeze = _freeze()
    document = _document(freeze)
    on_choices = {
        row["target_holdout"]: row["choice_id"]
        for row in document["rows"] if row["arm"] == "on"
    }
    expectations = {
        item["target_holdout"]: item for item in document["swapped_follow_expectations"]
    }
    for target, source in freeze["derangement"].items():
        assert expectations[target]["source_on_holdout"] == source
        assert expectations[target]["expected_choice_id"] == on_choices[source]


def test_swapped_expectation_propagates_missing_on_choice_as_null() -> None:
    freeze = _freeze()
    rows = _rows(freeze)
    missing = next(row for row in rows if row["arm"] == "on")
    _make_missing(missing)

    document = _document(freeze, rows)
    target = next(
        target for target, source in freeze["derangement"].items()
        if source == missing["target_holdout"]
    )
    expectation = next(
        item for item in document["swapped_follow_expectations"]
        if item["target_holdout"] == target
    )
    assert expectation == {
        "target_holdout": target,
        "source_on_holdout": missing["target_holdout"],
        "expected_choice_id": None,
    }


def test_verify_detects_body_row_derangement_and_basis_tampering(tmp_path: Path) -> None:
    freeze = _freeze()
    head = _fixture_head(tmp_path)
    document = _document(freeze, root=tmp_path, pre_oracle_head=head)
    verify_prediction_freeze(document, freeze=freeze, root=tmp_path)

    body_tampered = copy.deepcopy(document)
    body_tampered["generated_at"] = "changed"
    with pytest.raises(SelectorFreezeError, match="body_sha256"):
        verify_prediction_freeze(body_tampered, freeze=freeze, root=tmp_path)

    row_tampered = copy.deepcopy(document)
    valid_agent = next(
        row for row in row_tampered["rows"]
        if row["arm"] == "on" and row["status"] == "valid"
    )
    valid_agent["choice_id"] = "c06"
    _rehash(row_tampered)
    with pytest.raises(SelectorFreezeError, match="binding_key"):
        verify_prediction_freeze(row_tampered, freeze=freeze, root=tmp_path)

    derangement_tampered = copy.deepcopy(document)
    first = next(iter(derangement_tampered["derangement"]))
    derangement_tampered["derangement"][first] = first
    _rehash(derangement_tampered)
    with pytest.raises(SelectorFreezeError, match="derangement"):
        verify_prediction_freeze(derangement_tampered, freeze=freeze, root=tmp_path)

    changed_freeze = copy.deepcopy(freeze)
    target = next(iter(changed_freeze["holdouts"]))
    key = next(iter(CHOICE_TO_BINDING.values()))
    changed_freeze["holdouts"][target]["variant_binding"]["entries"][key]["test_change"] = True
    with pytest.raises(SelectorFreezeError, match="selector_basis_sha256"):
        verify_prediction_freeze(document, freeze=changed_freeze, root=tmp_path)


def test_verify_binds_role_raw_and_exact_agent_provenance_to_files(tmp_path: Path) -> None:
    freeze = _freeze()

    role_root = tmp_path / "role-case"
    role_document = _document(
        freeze, root=role_root, pre_oracle_head=_fixture_head(role_root),
    )
    role_path = role_root / role_document["sources"]["role"]["path"]
    role_path.write_bytes(role_path.read_bytes() + b"x")
    with pytest.raises(SelectorFreezeError, match="sources.role.sha256"):
        verify_prediction_freeze(role_document, freeze=freeze, root=role_root)

    raw_root = tmp_path / "raw-case"
    raw_document = _document(
        freeze, root=raw_root, pre_oracle_head=_fixture_head(raw_root),
    )
    raw_row = next(row for row in raw_document["rows"] if row["arm"] == "on")
    raw_path = raw_root / raw_row["raw_response_path"]
    raw_path.write_bytes(raw_path.read_bytes() + b"x")
    with pytest.raises(SelectorFreezeError, match="raw_response.sha256"):
        verify_prediction_freeze(raw_document, freeze=freeze, root=raw_root)

    provenance_root = tmp_path / "provenance-case"
    provenance_document = _document(
        freeze, root=provenance_root, pre_oracle_head=_fixture_head(provenance_root),
    )
    provenance_row = next(
        row for row in provenance_document["rows"] if row["arm"] == "on"
    )
    provenance_row["agent_provenance"].pop("model")
    _rehash(provenance_document)
    with pytest.raises(SelectorFreezeError, match="agent_provenance schema"):
        verify_prediction_freeze(
            provenance_document, freeze=freeze, root=provenance_root,
        )


def test_verify_reparses_raw_and_rejects_forged_valid_agent_rows(tmp_path: Path) -> None:
    """C2-R2 positive control: 非 JSON raw + status=valid/choice_id=c01 の偽装を拒否する。"""
    freeze = _freeze()
    head = _fixture_head(tmp_path)
    sources = _sources(tmp_path)
    poison = "import os\n\ndef pwn():\n    return 'not selector json'\n"
    poison_path = tmp_path / "selector-runs" / "poison.py"
    poison_path.parent.mkdir(parents=True, exist_ok=True)
    poison_path.write_text(poison, encoding="utf-8")
    poison_sha = hashlib.sha256(poison.encode("utf-8")).hexdigest()

    rows = []
    agent_index = 0
    for job in build_prediction_jobs(freeze):
        if job["arm"] == "off":
            rows.append({
                **job,
                "status": "valid",
                "rationale": None,
                "raw_response_path": None,
                "raw_sha256": None,
                "parser_error_code": None,
                "agent_provenance": None,
            })
            continue
        rows.append({
            **job,
            "status": "valid",
            "choice_id": "c01",
            "rationale": "forged rationale",
            "raw_response_path": "selector-runs/poison.py",
            "raw_sha256": poison_sha,
            "parser_error_code": None,
            "agent_provenance": {
                "child_id": f"forged-{agent_index}",
                "role_file_sha256": sources["role"]["sha256"],
                "model": "fixture-model",
                "started_at": "2026-07-16T00:00:00Z",
                "finished_at": "2026-07-16T00:01:00Z",
                "fresh_context": True,
                "declared_tools": [],
                "observed_tool_events": [],
            },
        })
        agent_index += 1

    # build は raw を再 parse しない (C2 実証どおり通る) が、verify は落とす。
    document = build_prediction_freeze(
        freeze=freeze,
        rows=rows,
        generated_at="2026-07-16T00:00:00Z",
        pre_oracle_head=head,
        sources=sources,
        execution_policy=_policy(),
    )
    with pytest.raises(SelectorFreezeError, match="再 parse"):
        verify_prediction_freeze(document, freeze=freeze, root=tmp_path)


def test_verify_reparse_detects_choice_swap_and_off_row_agent_fields(
    tmp_path: Path,
) -> None:
    freeze = _freeze()
    head = _fixture_head(tmp_path)
    document = _document(freeze, root=tmp_path, pre_oracle_head=head)
    verify_prediction_freeze(document, freeze=freeze, root=tmp_path)

    # raw は c01 の正規出力のまま、記録だけ c02 (binding は整合済み) へ差し替える。
    swapped_choice = copy.deepcopy(document)
    row = next(r for r in swapped_choice["rows"] if r["arm"] == "on")
    assert row["choice_id"] == "c01"
    row["choice_id"] = "c02"
    row["binding_key"] = CHOICE_TO_BINDING["c02"]
    entry = binding_entry_for_choice(freeze, row["target_holdout"], "c02")
    rendered = json.dumps(
        entry, ensure_ascii=False, sort_keys=True, separators=(",", ":"), allow_nan=False,
    )
    row["binding_entry_sha256"] = hashlib.sha256(rendered.encode("utf-8")).hexdigest()
    _rehash(swapped_choice)
    with pytest.raises(SelectorFreezeError, match="再 parse"):
        verify_prediction_freeze(swapped_choice, freeze=freeze, root=tmp_path)

    # static off セルへの agent 系フィールド注入も verify 経路で落ちる。
    off_forged = copy.deepcopy(document)
    off_row = next(r for r in off_forged["rows"] if r["arm"] == "off")
    off_row["rationale"] = "forged"
    _rehash(off_forged)
    with pytest.raises(SelectorFreezeError, match="off row に agent"):
        verify_prediction_freeze(off_forged, freeze=freeze, root=tmp_path)


def test_verify_requires_commit_pin_resolvable_in_root_repo(tmp_path: Path) -> None:
    """C2-R4: 形式のみ有効な 40 桁 hex は commit 実在検証で拒否する。"""
    freeze = _freeze()
    head = _fixture_head(tmp_path)
    good = _document(freeze, root=tmp_path, pre_oracle_head=head)
    verify_prediction_freeze(good, freeze=freeze, root=tmp_path)

    forged = _document(freeze, root=tmp_path, pre_oracle_head="a" * 40)
    with pytest.raises(SelectorFreezeError, match="pre_oracle_head"):
        verify_prediction_freeze(forged, freeze=freeze, root=tmp_path)


def test_selector_basis_preimage_is_versioned_and_backward_compatible() -> None:
    """test_selector_basis_ignores_floor_budget_but_binds_variant_entries を統合 (固定 baseline 検査を含む上位集合)。"""
    freeze = _freeze()
    baseline = selector_basis_sha256(freeze)
    preimage = selector_basis_preimage(freeze)

    # 拡張点が機械可読: version tag が preimage に含まれ、hash はそれに束縛される。
    assert preimage["version"] == SELECTOR_BASIS_VERSION == "selector_basis/v1"
    rendered = json.dumps(
        preimage, ensure_ascii=False, sort_keys=True, separators=(",", ":"),
        allow_nan=False,
    )
    assert selector_basis_sha256(freeze) == hashlib.sha256(
        rendered.encode("utf-8")
    ).hexdigest()

    # 後方互換: 含める/除く field 集合は不変 (floor/budget 除外・binding 束縛)。
    floor_budget_changed = copy.deepcopy(freeze)
    floor_budget_changed["floor"] = {"future": 1}
    floor_budget_changed["budget"] = {"future": 2}
    assert selector_basis_sha256(floor_budget_changed) == selector_basis_sha256(freeze)
    assert selector_basis_sha256(floor_budget_changed) == baseline
    assert "floor" not in preimage and "budget" not in preimage

    binding_changed = copy.deepcopy(freeze)
    target = next(iter(binding_changed["holdouts"]))
    key = next(iter(CHOICE_TO_BINDING.values()))
    binding_changed["holdouts"][target]["variant_binding"]["entries"][key]["future"] = 1
    assert selector_basis_sha256(binding_changed) != selector_basis_sha256(freeze)
    assert selector_basis_sha256(binding_changed) != baseline


def test_write_prediction_freeze_is_atomic_exclusive_create(tmp_path: Path) -> None:
    document = _document(_freeze())
    destination = tmp_path / "nested" / "prediction.json"
    write_prediction_freeze(destination, document)
    assert json.loads(destination.read_text(encoding="utf-8")) == document

    with pytest.raises(SelectorFreezeError, match="既に存在"):
        write_prediction_freeze(destination, document)
    assert json.loads(destination.read_text(encoding="utf-8")) == document


def test_cli_plan_accepts_v1_trust_root_freeze(capsys) -> None:
    """C2-7 残余: CLI が v1 trust root freeze を読むと plan が成功する (正例)。"""
    if not FREEZE_PATH.is_file():
        pytest.skip("v1 freeze 不在")
    rc = main(["plan", "--freeze", str(FREEZE_PATH)])
    assert rc == 0
    out = capsys.readouterr().out
    assert "input_payload_sha256" in out  # job 計画が出力された


def test_cli_rejects_non_v1_freeze(tmp_path, capsys) -> None:
    """C2-7 残余: v1 bytes と異なる freeze を CLI が読むと fail-closed で拒否する (負例)。"""
    forged = tmp_path / "forged_freeze.json"
    # 実 v1 と異なる bytes (何であれ v1 sha に一致しない)。
    forged.write_text(json.dumps({"holdouts": {}}), encoding="utf-8")
    rc = main(["plan", "--freeze", str(forged)])
    assert rc == 1
    err = capsys.readouterr().err
    assert "v1 trust root と不一致" in err


def test_load_v1_freeze_reads_once_binding_verify_and_use(monkeypatch) -> None:
    """A3-6 回帰: v1 pin は照合した bytes と parse/使用する bytes を同一にする。

    read_bytes を 2 回呼ぶ設計では、1 回目 (照合) の後・2 回目 (使用) の前に別内容へ
    差し替えると pin を通過しつつ差替え後 freeze から job を組めてしまう (verify-use
    TOCTOU)。read-once を call-count == 1 で機械的に固定し、二読み再導入を殺す。
    既存の正例/負例テストは差替え窓を突けないため本回帰が必要。"""
    if not FREEZE_PATH.is_file():
        pytest.skip("v1 freeze 不在")
    v1_bytes = FREEZE_PATH.read_bytes()
    forged = b'{"holdouts": {}}'  # v1 と別内容 (2 回目に読めば job が変わる)
    calls = {"n": 0}

    def fake_read_bytes(self):
        calls["n"] += 1
        return v1_bytes if calls["n"] == 1 else forged

    monkeypatch.setattr(Path, "read_bytes", fake_read_bytes)
    document = _load_v1_freeze(FREEZE_PATH)
    assert calls["n"] == 1  # 一度しか読まない = 照合 bytes と使用 bytes が同一
    assert document == json.loads(v1_bytes.decode("utf-8"))
