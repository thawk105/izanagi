# -*- coding: utf-8 -*-
"""profiler_directive (段 8a の profiler → axis-proposer 結線) の単体テスト。

perf を実行しない機械部分のみ: perf report の汎用解析・信頼境界での落とし
(絶対規律 6)・恒真化しない導出 (突出が無ければ None)・位置以外を運ばない record 契約。

**恒真化の positive control を持つ**: `assert_position_only` は「キーが固定だから必ず通る」
だけの検査になりうるので、方向・値・骨格を足した record を**実際に拒否する**ことを
変異ケースで確かめる。棄却分岐 (`below_min_region_pct` / `margin_too_small` /
`no_mapped_region`) も、死んでいないことを個別に確かめる。
"""
from __future__ import annotations

import json
import os
import sys

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import profiler_directive as M  # noqa: E402


_REGIONS = ["cc/silo/transaction.cc", "cc/silo/silo.cc", "include/backoff.hh"]
_ROOT = "/build/ccbench"


def _report(event_blocks):
    """`perf report --stdio` 相当のテキストを組み立てる。"""
    out = []
    for event, rows in event_blocks:
        out.append(f"# Samples: 1K of event '{event}'")
        out.append("# Event count (approx.): 1000000")
        out.append("#")
        out.extend(rows)
        out.append("")
    return "\n".join(out)


def _write_report(tmp_path, text, name="perf-report.txt"):
    path = tmp_path / name
    path.write_text(text, encoding="utf-8")
    return path


def _write_provenance(tmp_path, edit_surface_map, name="n1-provenance.json"):
    path = tmp_path / name
    path.write_text(json.dumps({
        "projected_input": {"edit_surface_map": edit_surface_map},
    }), encoding="utf-8")
    return path


# ------------------------------------------------------------------ 解析

def test_parse_perf_rows_picks_only_the_requested_event():
    text = _report([
        ("cycles", ["    60.00%  /build/ccbench/cc/silo/transaction.cc:120"]),
        ("instructions", ["    99.00%  /build/ccbench/cc/silo/silo.cc:7"]),
    ])
    assert M.parse_perf_rows(text, event="cycles") == [
        ("/build/ccbench/cc/silo/transaction.cc:120", 60.0)
    ]
    assert M.parse_perf_rows(text, event="instructions") == [
        ("/build/ccbench/cc/silo/silo.cc:7", 99.0)
    ]


def test_parse_perf_rows_handles_symbol_form_with_spaces():
    """既定の --sort=symbol 形式では `[.] ` 以降を行末まで label にする。"""
    text = _report([("cycles", [
        "    65.44%  bench  bench  [.] Backoff::backoff",
        "    12.00%  bench  bench  [k] native_write_msr",
        "     3.00%  bench  bench  [.] std::vector<int, std::allocator<int> >::push_back",
    ])])
    assert M.parse_perf_rows(text) == [
        ("Backoff::backoff", 65.44),
        ("native_write_msr", 12.0),
        ("std::vector<int, std::allocator<int> >::push_back", 3.0),
    ]


def test_parse_perf_rows_returns_empty_for_absent_event():
    """該当 event が無ければ空 = 呼び手が「ヒントなし」に落とせる (fails-closed)。"""
    text = _report([("cycles", ["    60.00%  a.cc:1"])])
    assert M.parse_perf_rows(text, event="cache-misses") == []


# -------------------------------------------------- 信頼境界 (絶対規律 6)

@pytest.mark.parametrize("label", [
    "/build/ccbench/../outside/evil.cc:1",   # 親ディレクトリ参照
    "/etc/passwd:1",                          # source_root の外
    "cc/silo/not_in_the_map.cc:1",            # 地図に無い
    "[unknown]",                              # perf の解決失敗
    "??",
])
def test_mapper_drops_everything_outside_the_edit_surface(label):
    mapper = M.srcline_region_mapper(_ROOT, _REGIONS)
    assert mapper(label) is None


def test_mapper_accepts_both_absolute_and_relative_paths():
    mapper = M.srcline_region_mapper(_ROOT, _REGIONS)
    assert mapper("/build/ccbench/cc/silo/transaction.cc:120") == "cc/silo/transaction.cc"
    assert mapper("cc/silo/silo.cc:7") == "cc/silo/silo.cc"


def test_region_totals_accumulates_dropped_share():
    """捨てた割合を握り潰さず返す (何が見えていないかを記録に残すため)。"""
    rows = [("cc/silo/silo.cc:1", 30.0), ("/etc/passwd:1", 25.0), ("cc/silo/silo.cc:9", 5.0)]
    totals, dropped = M.region_totals(rows, M.srcline_region_mapper(_ROOT, _REGIONS))
    assert totals == {"cc/silo/silo.cc": 35.0}
    assert dropped == 25.0


# ------------------------------------------------ 導出 (恒真化しないこと)

def test_derive_picks_the_dominant_region():
    totals = {"cc/silo/transaction.cc": 42.0, "include/backoff.hh": 11.0}
    assert M.derive_directive(totals, _REGIONS) == ("cc/silo/transaction.cc", "dominant_region")


def test_derive_returns_none_when_nothing_stands_out():
    """僅差では None。この分岐が死ぬと「どんな入力にも directive が出る」恒真導出になる。"""
    totals = {"cc/silo/transaction.cc": 26.0, "cc/silo/silo.cc": 24.0}
    directive, reason = M.derive_directive(totals, _REGIONS)
    assert directive is None
    assert reason == "margin_too_small"


def test_derive_returns_none_below_the_floor():
    totals = {"cc/silo/transaction.cc": 4.0, "cc/silo/silo.cc": 1.0}
    directive, reason = M.derive_directive(totals, _REGIONS)
    assert directive is None
    assert reason == "below_min_region_pct"


def test_derive_returns_none_when_no_region_is_on_the_map():
    directive, reason = M.derive_directive({"vendor/other.cc": 99.0}, _REGIONS)
    assert directive is None
    assert reason == "no_mapped_region"


def test_derive_filters_unmapped_regions_even_when_they_dominate():
    """集約側を通り抜けた地図外領域も導出側で再度落とす (二重の fails-closed)。"""
    totals = {"vendor/other.cc": 90.0, "cc/silo/silo.cc": 10.0}
    assert M.derive_directive(totals, _REGIONS) == ("cc/silo/silo.cc", "dominant_region")


def test_derive_is_deterministic_under_exact_ties():
    """完全同値では順序に依らず margin 不足で棄却する (辞書順の揺れで採否が変わらない)。"""
    a = M.derive_directive({"cc/silo/silo.cc": 30.0, "cc/silo/transaction.cc": 30.0}, _REGIONS)
    b = M.derive_directive({"cc/silo/transaction.cc": 30.0, "cc/silo/silo.cc": 30.0}, _REGIONS)
    assert a == b == (None, "margin_too_small")


# ------------------------------------------------------ record の契約

def test_record_carries_position_and_provenance_only():
    record = M.build_directive_record(
        "cc/silo/silo.cc", "profiler_derived", reason="dominant_region",
        evidence=[{"label": "cc/silo/silo.cc:3", "pct": 40.0, "region": "cc/silo/silo.cc"}],
        totals={"cc/silo/silo.cc": 40.0}, dropped_pct=2.0,
    )
    M.assert_position_only(record)
    assert set(record) == M.DIRECTIVE_RECORD_KEYS
    assert record["provenance"]["source"] == "profiler_derived"


def test_human_declared_is_typed_apart_from_observation():
    """人間ヒントと観測由来は同じ record 型だが由来で分離できる (対照が取れる)。"""
    record = M.declare_directive("include/backoff.hh", _REGIONS)
    M.assert_position_only(record)
    assert record["provenance"]["source"] == "human_declared"
    assert record["provenance"]["reason"] == "human_declared"
    assert record["hole_region_directive"] == "include/backoff.hh"


def test_human_declared_rejects_regions_off_the_map():
    with pytest.raises(M.DirectiveDerivationError):
        M.declare_directive("cc/silo/nonexistent.cc", _REGIONS)


def test_record_with_no_directive_is_valid_as_a_control():
    """ヒントなし構成も正当な記録 — 対照アームとして残せる。"""
    record = M.build_directive_record(
        None, "profiler_derived", reason="margin_too_small", totals={"cc/silo/silo.cc": 26.0}
    )
    M.assert_position_only(record)
    assert record["hole_region_directive"] is None


@pytest.mark.parametrize("kwargs", [
    {"directive": None, "source": "profiler_derived", "reason": "dominant_region"},
    {"directive": "cc/silo/silo.cc", "source": "profiler_derived", "reason": "margin_too_small"},
    {"directive": "cc/silo/silo.cc", "source": "unknown_source", "reason": "dominant_region"},
    {"directive": "cc/silo/silo.cc", "source": "profiler_derived", "reason": "just_because"},
])
def test_record_rejects_inconsistent_combinations(kwargs):
    with pytest.raises(M.DirectiveDerivationError):
        M.build_directive_record(kwargs.pop("directive"), kwargs.pop("source"), **kwargs)


# ---------------------------- positive control: 位置以外を足すと必ず落ちる

@pytest.mark.parametrize("mutate", [
    pytest.param(lambda r: r.update({"backoff_us": 0}), id="値を record 直下に足す"),
    pytest.param(lambda r: r.update({"direction": "increase"}), id="方向を record 直下に足す"),
    pytest.param(lambda r: r["provenance"].update({"skeleton": "for(;;){}"}),
                 id="骨格を provenance に足す"),
    pytest.param(lambda r: r["provenance"].update({"recommend": "set BACK_OFF=0"}),
                 id="推奨文を provenance に足す"),
    pytest.param(lambda r: r["provenance"]["evidence"].append(
        {"label": "x", "pct": 1.0, "region": "cc/silo/silo.cc", "hint": "make it lock-free"}),
        id="指示を evidence の自由キーに埋める"),
])
def test_assert_position_only_rejects_smuggled_guidance(mutate):
    """`assert_position_only` が恒真でないことの positive control。

    方向・値・骨格・推奨文を運ぼうとした record は、どの経路でも拒否されなければならない。
    ここが緑のまま通ると、リーク制御が「謳うだけで発火しない保証」に退化する。
    """
    record = M.build_directive_record(
        "cc/silo/silo.cc", "profiler_derived", reason="dominant_region",
        evidence=[{"label": "cc/silo/silo.cc:3", "pct": 40.0, "region": "cc/silo/silo.cc"}],
    )
    M.assert_position_only(record)          # 変異前は通ることを先に確かめる
    mutate(record)
    with pytest.raises(M.DirectiveDerivationError):
        M.assert_position_only(record)


def test_assert_position_only_rejects_polluted_evidence_label():
    record = M.build_directive_record(
        "cc/silo/silo.cc", "profiler_derived", reason="dominant_region",
        evidence=[{"label": "cc/silo/silo.cc:3", "pct": 40.0, "region": "cc/silo/silo.cc"}],
    )
    record["provenance"]["evidence"][0]["label"] = "cc/silo/silo.cc:set_BACKOFF=0"

    with pytest.raises(M.DirectiveDerivationError, match="label"):
        M.assert_position_only(record)


def test_assert_position_only_rejects_evidence_for_another_region():
    record = M.build_directive_record(
        "cc/silo/silo.cc", "profiler_derived", reason="dominant_region",
        evidence=[{"label": "cc/silo/silo.cc:3", "pct": 40.0, "region": "cc/silo/silo.cc"}],
    )
    record["provenance"]["evidence"][0] = {
        "label": "include/backoff.hh:3",
        "pct": 40.0,
        "region": "include/backoff.hh",
    }

    with pytest.raises(M.DirectiveDerivationError, match="directive と不一致"):
        M.assert_position_only(record)


def test_assert_position_only_rejects_evidence_when_directive_is_none():
    record = M.build_directive_record(
        None, "profiler_derived", reason="margin_too_small",
        evidence=[{"label": "cc/silo/silo.cc:3", "pct": 40.0, "region": "cc/silo/silo.cc"}],
    )

    with pytest.raises(M.DirectiveDerivationError, match="None なら evidence は空"):
        M.assert_position_only(record)


def test_build_rejects_evidence_with_extra_keys_at_construction_time():
    """組立の時点でも自由キーを弾く (検査を呼び忘れても漏れない)。"""
    with pytest.raises(M.DirectiveDerivationError):
        M.build_directive_record(
            "cc/silo/silo.cc", "profiler_derived", reason="dominant_region",
            evidence=[{"label": "a", "pct": 1.0, "region": "cc/silo/silo.cc", "note": "使え"}],
        )


# ------------------------------------------------------------ 一気通貫

def test_end_to_end_from_a_perf_report():
    text = _report([("cycles", [
        "    38.00%  /build/ccbench/cc/silo/transaction.cc:120",
        "    12.00%  /build/ccbench/cc/silo/transaction.cc:311",
        "     9.00%  /build/ccbench/include/backoff.hh:40",
        "    20.00%  /usr/lib/libc.so:0",
    ])])
    record = M.derive_from_perf_report(text, _ROOT, _REGIONS)
    M.assert_position_only(record)
    assert record["hole_region_directive"] == "cc/silo/transaction.cc"
    assert record["provenance"]["region_totals_pct"] == {
        "cc/silo/transaction.cc": 50.0, "include/backoff.hh": 9.0,
    }
    assert record["provenance"]["dropped_pct"] == 20.0
    assert [e["label"] for e in record["provenance"]["evidence"]] == [
        "cc/silo/transaction.cc:120",
        "cc/silo/transaction.cc:311",
    ]


def test_evidence_drops_non_numeric_suffix_and_normalizes_valid_srcline():
    text = _report([("cycles", [
        "    38.00%  /build/ccbench/cc/silo/silo.cc:0007",
        "    12.00%  /build/ccbench/cc/silo/silo.cc:set_BACKOFF=0",
        "     9.00%  /build/ccbench/include/backoff.hh:40",
    ])])
    record = M.derive_from_perf_report(text, _ROOT, _REGIONS)

    assert record["hole_region_directive"] == "cc/silo/silo.cc"
    assert record["provenance"]["region_totals_pct"]["cc/silo/silo.cc"] == 50.0
    assert record["provenance"]["evidence"] == [
        {"label": "cc/silo/silo.cc:7", "pct": 38.0, "region": "cc/silo/silo.cc"},
    ]
    M.assert_position_only(record)


def test_end_to_end_falls_back_to_no_hint_when_flat():
    """平坦な断面では directive を出さず、その理由と観測を残す。"""
    text = _report([("cycles", [
        "    26.00%  /build/ccbench/cc/silo/transaction.cc:120",
        "    24.00%  /build/ccbench/cc/silo/silo.cc:5",
    ])])
    record = M.derive_from_perf_report(text, _ROOT, _REGIONS)
    assert record["hole_region_directive"] is None
    assert record["provenance"]["reason"] == "margin_too_small"
    assert record["provenance"]["evidence"] == []
    assert record["provenance"]["region_totals_pct"] == {
        "cc/silo/silo.cc": 24.0, "cc/silo/transaction.cc": 26.0,
    }


def test_derived_directive_is_accepted_by_the_role_policy_check():
    """供給側の出力が既存の機械検査 (codex_roles/policy.py) を通ることを確かめる。

    directive の受理条件は policy 側が正本 — 供給側で作った値がそこで弾かれたら結線が
    成立しない。地図外を宣言した場合に policy が弾くことも同時に確かめる。
    """
    from orchestrator.codex_roles import policy  # noqa: PLC0415

    surface = [{"region": r, "role": "mock", "opened": r == "include/backoff.hh"}
               for r in _REGIONS]
    payload = {
        "diagnostics": {},
        "stock_excerpts": [{"region": r, "source_rel": r, "excerpt": "// stock"}
                           for r in _REGIONS],
        "edit_surface_map": surface,
    }
    record = M.declare_directive("cc/silo/transaction.cc", _REGIONS)
    payload["hole_region_directive"] = record["hole_region_directive"]
    policy.validate_input_semantics("axis-proposer", payload)   # 例外が出なければ受理

    payload["hole_region_directive"] = "cc/silo/off_the_map.cc"
    with pytest.raises(policy.RolePolicyError):
        policy.validate_input_semantics("axis-proposer", payload)


# ---------------------------------------------------------------------- CLI

def test_cli_derive_emits_dominant_region_record(tmp_path, capsys):
    text = _report([("cycles", [
        "    45.00%  /build/ccbench/cc/silo/transaction.cc:120",
        "    12.00%  /build/ccbench/include/backoff.hh:40",
    ])])
    report = _write_report(tmp_path, text)
    rc = M.main([
        "derive", "--report", str(report), "--source-root", _ROOT,
        "--region", "cc/silo/transaction.cc",
        "--region", "include/backoff.hh",
    ])
    captured = capsys.readouterr()
    record = json.loads(captured.out)

    assert rc == 0
    assert captured.err == ""
    M.assert_position_only(record)
    assert record["hole_region_directive"] == "cc/silo/transaction.cc"
    assert record["provenance"]["reason"] == "dominant_region"


def test_cli_derive_emits_no_hint_control_when_flat(tmp_path, capsys):
    text = _report([("cycles", [
        "    26.00%  /build/ccbench/cc/silo/transaction.cc:120",
        "    24.00%  /build/ccbench/cc/silo/silo.cc:5",
    ])])
    report = _write_report(tmp_path, text)
    rc = M.main([
        "derive", "--report", str(report), "--source-root", _ROOT,
        "--region", "cc/silo/transaction.cc",
        "--region", "cc/silo/silo.cc",
    ])
    captured = capsys.readouterr()
    record = json.loads(captured.out)

    assert rc == 0
    assert captured.err == ""
    M.assert_position_only(record)
    assert record["hole_region_directive"] is None
    assert record["provenance"]["reason"] == "margin_too_small"


def test_cli_derive_reads_regions_from_n1_provenance_and_writes_output(tmp_path, capsys):
    provenance = _write_provenance(tmp_path, [
        {"opened": False, "region": "cc/silo/silo.cc", "role": "mock"},
        {"opened": True, "region": "include/backoff.hh", "role": "mock"},
    ])
    output = tmp_path / "directive.json"
    text = _report([("cycles", [
        "    41.00%  /scr/disappeared/ccbench/include/backoff.hh:40",
        "     9.00%  /scr/disappeared/ccbench/cc/silo/silo.cc:5",
    ])])
    report = _write_report(tmp_path, text)

    rc = M.main([
        "derive", "--report", str(report), "--source-root", "/scr/disappeared/ccbench",
        "--regions-from", str(provenance), "-o", str(output),
    ])
    captured = capsys.readouterr()
    record = json.loads(output.read_text(encoding="utf-8"))

    assert rc == 0
    assert captured.out == ""
    assert captured.err == ""
    M.assert_position_only(record)
    assert record["hole_region_directive"] == "include/backoff.hh"
    assert record["provenance"]["reason"] == "dominant_region"


def test_cli_declare_emits_human_declared_record(tmp_path, capsys):
    provenance = _write_provenance(tmp_path, [
        {"opened": False, "region": "cc/silo/silo.cc", "role": "mock"},
        {"opened": True, "region": "include/backoff.hh", "role": "mock"},
    ])
    rc = M.main([
        "declare", "--region", "include/backoff.hh",
        "--regions-from", str(provenance),
    ])
    captured = capsys.readouterr()
    record = json.loads(captured.out)

    assert rc == 0
    assert captured.err == ""
    M.assert_position_only(record)
    assert record["hole_region_directive"] == "include/backoff.hh"
    assert record["provenance"]["source"] == "human_declared"
    assert record["provenance"]["reason"] == "human_declared"


def test_cli_declare_rejects_region_outside_the_map(tmp_path, capsys):
    provenance = _write_provenance(tmp_path, [
        {"opened": False, "region": "cc/silo/silo.cc", "role": "mock"},
    ])
    rc = M.main([
        "declare", "--region", "cc/silo/not_in_the_map.cc",
        "--regions-from", str(provenance),
    ])
    captured = capsys.readouterr()

    assert rc == 2
    assert captured.out == ""
    assert "編集面の地図に無い領域" in captured.err


def test_cli_declare_rejects_freeform_region_list(capsys):
    with pytest.raises(SystemExit) as excinfo:
        M.main([
            "declare", "--region", "cc/silo/silo.cc",
            "--region-list", "cc/silo/silo.cc",
        ])
    captured = capsys.readouterr()

    assert excinfo.value.code == 2
    assert "--regions-from" in captured.err


def test_cli_regions_from_missing_n1_hierarchy_fails_closed(tmp_path, capsys):
    provenance = tmp_path / "bad-provenance.json"
    provenance.write_text(json.dumps({"projected_input": {}}), encoding="utf-8")
    report = _write_report(tmp_path, _report([("cycles", [
        "    60.00%  /build/ccbench/cc/silo/silo.cc:3",
    ])]))

    rc = M.main([
        "derive", "--report", str(report), "--source-root", _ROOT,
        "--regions-from", str(provenance),
    ])
    captured = capsys.readouterr()

    assert rc == 2
    assert captured.out == ""
    assert "projected_input.edit_surface_map が無い" in captured.err


def test_cli_rechecks_position_only_before_output(tmp_path, monkeypatch, capsys):
    def polluted_derive(*args, **kwargs):
        record = M.build_directive_record(
            "cc/silo/silo.cc", "profiler_derived", reason="dominant_region"
        )
        record["direction"] = "increase"
        return record

    monkeypatch.setattr(M, "derive_from_perf_report", polluted_derive)
    report = _write_report(tmp_path, _report([("cycles", [
        "    60.00%  /build/ccbench/cc/silo/silo.cc:3",
    ])]))
    rc = M.main([
        "derive",
        "--report", str(report),
        "--source-root", _ROOT,
        "--region", "cc/silo/silo.cc",
    ])
    captured = capsys.readouterr()

    assert rc == 2
    assert captured.out == ""
    assert "record のキーが契約と不一致" in captured.err


def test_cli_derive_rejects_missing_report_path(tmp_path, capsys):
    missing = tmp_path / "missing-perf-report.txt"
    rc = M.main([
        "derive", "--report", str(missing), "--source-root", _ROOT,
        "--region", "cc/silo/silo.cc",
    ])
    captured = capsys.readouterr()

    assert rc == 2
    assert captured.out == ""
    assert str(missing) in captured.err


@pytest.mark.parametrize("option", ["--min-region-pct", "--min-margin-pct"])
@pytest.mark.parametrize("value", ["nan", "-1", "101"])
def test_cli_derive_rejects_invalid_thresholds(tmp_path, capsys, option, value):
    report = _write_report(tmp_path, _report([("cycles", [
        "    60.00%  /build/ccbench/cc/silo/silo.cc:3",
    ])]))
    rc = M.main([
        "derive", "--report", str(report), "--source-root", _ROOT,
        "--region", "cc/silo/silo.cc", option, value,
    ])
    captured = capsys.readouterr()

    assert rc == 2
    assert captured.out == ""
    assert "有限な 0〜100" in captured.err


def test_cli_derive_rejects_empty_report(tmp_path, capsys):
    report = _write_report(tmp_path, "")
    rc = M.main([
        "derive", "--report", str(report), "--source-root", _ROOT,
        "--region", "cc/silo/silo.cc",
    ])
    captured = capsys.readouterr()

    assert rc == 2
    assert captured.out == ""
    assert "report ファイルが空" in captured.err


def test_cli_derive_rejects_report_without_requested_event(tmp_path, capsys):
    report = _write_report(tmp_path, _report([("cycles", [
        "    60.00%  /build/ccbench/cc/silo/silo.cc:3",
    ])]))
    rc = M.main([
        "derive", "--report", str(report), "--source-root", _ROOT,
        "--region", "cc/silo/silo.cc", "--event", "instructions",
    ])
    captured = capsys.readouterr()

    assert rc == 2
    assert captured.out == ""
    assert "report に該当 event の行が無い" in captured.err


def test_cli_derive_keeps_no_mapped_region_as_success(tmp_path, capsys):
    report = _write_report(tmp_path, _report([("cycles", [
        "    60.00%  /usr/lib/libc.so:3",
    ])]))
    rc = M.main([
        "derive", "--report", str(report), "--source-root", _ROOT,
        "--region", "cc/silo/silo.cc",
    ])
    captured = capsys.readouterr()
    record = json.loads(captured.out)

    assert rc == 0
    assert captured.err == ""
    assert record["hole_region_directive"] is None
    assert record["provenance"]["reason"] == "no_mapped_region"
    assert record["provenance"]["dropped_pct"] == 60.0


@pytest.mark.parametrize(
    ("edit_surface_map", "message"),
    [
        pytest.param([], "空であってはならない", id="empty-map"),
        pytest.param(
            [{"opened": False, "region": "cc/silo/silo.cc"}],
            "キー集合",
            id="wrong-keys",
        ),
        pytest.param(
            [{"opened": False, "region": "/cc/silo/silo.cc", "role": "mock"}],
            "安全な相対パス",
            id="absolute-region",
        ),
        pytest.param(
            [{"opened": False, "region": "cc/../silo/silo.cc", "role": "mock"}],
            "安全な相対パス",
            id="parent-region",
        ),
    ],
)
def test_cli_derive_rejects_invalid_provenance(
    tmp_path, capsys, edit_surface_map, message
):
    provenance = _write_provenance(tmp_path, edit_surface_map)
    report = _write_report(tmp_path, _report([("cycles", [
        "    60.00%  /build/ccbench/cc/silo/silo.cc:3",
    ])]))
    rc = M.main([
        "derive", "--report", str(report), "--source-root", _ROOT,
        "--regions-from", str(provenance),
    ])
    captured = capsys.readouterr()

    assert rc == 2
    assert captured.out == ""
    assert message in captured.err
