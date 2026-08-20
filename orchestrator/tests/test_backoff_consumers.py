# -*- coding: utf-8 -*-
"""bench-first 導入後も backoff consumer が uncertified TPS を漏らさない回帰。"""
from __future__ import annotations

import importlib.util
import json
import math
import os
import sys
from pathlib import Path
from types import SimpleNamespace

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_ORCH)
sys.path.insert(0, os.path.dirname(_ORCH))

from orchestrator.campaign import backoff_sweep_report, wal                # noqa: E402
from orchestrator.campaign.artifact_admission import CampaignReadPurpose   # noqa: E402
from orchestrator.campaign.backoff_repro import _bench_tps                 # noqa: E402
from orchestrator.campaign.layout import CampaignLayout                    # noqa: E402
from orchestrator.campaign.model import (STAGE_ABORT, STAGE_BENCH_DONE,    # noqa: E402
                            STAGE_BUILD_START)
from orchestrator.tests import commit_receipt_support as receipt_support  # noqa: E402


def _load_plot_module():
    path = os.path.join(_REPO, "tools", "plotting", "plot_backoff.py")
    spec = importlib.util.spec_from_file_location("plot_backoff_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)

    def historical_fixture_view(campaign, *, purpose):
        assert purpose is CampaignReadPurpose.HISTORICAL_RAW
        layout = CampaignLayout(str(campaign))
        records, _truncated = wal.read_records_checked(layout)
        epoch = SimpleNamespace(
            campaign_verifier_epoch="E0",
            state="E0",
            reason_code="v1-authority-absent",
            identity_scope="fixture enforcement closure",
            excluded_scope="fixture verifier exclusion",
        )
        return SimpleNamespace(
            wal_file=layout.wal_file,
            records=tuple(records),
            read_purpose=CampaignReadPurpose.HISTORICAL_RAW,
            campaign_verifier_epoch=epoch,
        )

    # These parser fixtures intentionally contain no campaign.lock.  Keep their
    # WAL-malformation focus while separately asserting the production caller's
    # exact historical purpose at this seam.
    module.require_admitted_campaign = historical_fixture_view
    return module


def _fixture_layout(tmp_path):
    layout = CampaignLayout(str(tmp_path / "campaign")).ensure()
    screen_genome = "silo|BACK_OFF=1,BACKOFF_FIXED=10"
    certified_genome = "silo|BACK_OFF=1,BACKOFF_FIXED=5"
    wal.log(layout, "v-screen", STAGE_BUILD_START, "test", {"genome": screen_genome})
    wal.log(layout, "v-screen", STAGE_BENCH_DONE, "test",
            {"median_tps": 999999.0, "tps": [999999.0], "screening": True})
    wal.log(layout, "v-screen", STAGE_ABORT, "test",
            {"reason": "screen-slower-than-floor", "screen": {"median_tps": 999999.0}})
    wal.log(layout, "v-certified", STAGE_BUILD_START, "test",
            {"genome": certified_genome})
    wal.log(layout, "v-certified", STAGE_BENCH_DONE, "test",
            {"median_tps": 123456.0, "tps": [123456.0, 123457.0]})
    receipt_support.log_receipted_commit(
        layout, "v-certified", "test", {"fitness_tps": 123456.0},
        lock_identity_sha256="0" * 64,
    )
    dat = os.path.join(layout.reports_dir, "fixture.dat")
    with open(dat, "w", encoding="utf-8") as f:
        f.write("# workload: fixture\n# env: test\n# campaign: fixture-campaign\n")
        f.write("5 123456 1.0 1.5\n")
    return layout


def test_backoff_report_declares_certified_purpose_and_epoch(
        tmp_path, monkeypatch):
    layout = CampaignLayout(str(tmp_path / "certified-campaign")).ensure()
    epoch = SimpleNamespace(
        campaign_verifier_epoch="E1:" + "a" * 64,
        identity_scope="fixture enforcement closure",
        excluded_scope="fixture verifier exclusion",
    )
    view = SimpleNamespace(
        layout=layout,
        read_purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
        campaign_verifier_epoch=epoch,
    )
    observed = {}

    def discover(_slug, _tag, *, purpose):
        observed["purpose"] = purpose
        return object()

    monkeypatch.setattr(
        backoff_sweep_report, "config_for",
        lambda _tag, _workload: SimpleNamespace(spec_slug="fixture", search_tag="sweep"),
    )
    monkeypatch.setattr(backoff_sweep_report, "discover_campaign_dir", discover)
    monkeypatch.setattr(
        backoff_sweep_report, "require_certified_campaign_view", lambda _value: view,
    )
    monkeypatch.setattr(backoff_sweep_report, "load_workload", lambda _view: [
        SimpleNamespace(flags={"BACK_OFF": 0}, li={"throughput_tps": 100.0}),
        SimpleNamespace(
            flags={"BACK_OFF": 1, "BACKOFF_FIXED": -1},
            li={"throughput_tps": 110.0},
        ),
        SimpleNamespace(
            flags={"BACK_OFF": 1, "BACKOFF_FIXED": 5},
            li={"throughput_tps": 120.0, "abort_rate": 0.1, "ipc": 1.2},
        ),
    ])

    def make_plot(dat, _spec, stem):
        observed["provenance"] = dat.provenance
        return {"png": stem + ".png", "dat": stem + ".dat", "plt": stem + ".plt"}

    monkeypatch.setattr(backoff_sweep_report, "make_plot", make_plot)
    result = backoff_sweep_report.report_workload("fixture", {})
    assert observed["purpose"] is CampaignReadPurpose.CERTIFIED_ACCEPTANCE
    assert observed["provenance"]["read_purpose"] == "CERTIFIED_ACCEPTANCE"
    assert observed["provenance"]["campaign_verifier_epoch"] == "E1:" + "a" * 64
    assert result["best_amt"] == 5
    report = Path(result["report"]).read_text(encoding="utf-8")
    assert "受理目的**: `CERTIFIED_ACCEPTANCE`" in report
    assert "campaign_verifier_epoch**: `E1:" in report


def _report_view(tmp_path):
    layout = CampaignLayout(str(tmp_path / "certified-campaign")).ensure()
    epoch = SimpleNamespace(
        campaign_verifier_epoch="E2",
        identity_scope="fixture enforcement closure",
        excluded_scope="fixture verifier exclusion",
    )
    return SimpleNamespace(
        layout=layout,
        read_purpose=CampaignReadPurpose.CERTIFIED_ACCEPTANCE,
        campaign_verifier_epoch=epoch,
    )


def _patch_report_inputs(monkeypatch, view, genomes):
    monkeypatch.setattr(
        backoff_sweep_report, "config_for",
        lambda _tag, _workload: SimpleNamespace(spec_slug="fixture", search_tag="sweep"),
    )
    monkeypatch.setattr(
        backoff_sweep_report, "discover_campaign_dir",
        lambda _slug, _tag, *, purpose: object(),
    )
    monkeypatch.setattr(
        backoff_sweep_report, "require_certified_campaign_view", lambda _value: view,
    )
    monkeypatch.setattr(backoff_sweep_report, "load_workload", lambda _view: genomes)


def _capture_report_plot(monkeypatch, observed):
    def make_plot(dat, _spec, stem):
        observed["rows"] = dat.rows
        observed["render"] = dat.render()
        return {"png": stem + ".png", "dat": stem + ".dat", "plt": stem + ".plt"}

    monkeypatch.setattr(backoff_sweep_report, "make_plot", make_plot)


def test_backoff_report_formats_ipc_for_dat_markdown_and_reading(tmp_path, monkeypatch):
    view = _report_view(tmp_path)
    genomes = [
        SimpleNamespace(flags={"BACK_OFF": 0}, li={"throughput_tps": 100.0}),
        SimpleNamespace(flags={"BACK_OFF": 1, "BACKOFF_FIXED": -1},
                        li={"throughput_tps": 110.0}),
        SimpleNamespace(
            flags={"BACK_OFF": 1, "BACKOFF_FIXED": 5},
            li={"throughput_tps": 120.0, "abort_rate": 0.1, "ipc": None},
        ),
        SimpleNamespace(
            flags={"BACK_OFF": 1, "BACKOFF_FIXED": 10},
            li={"throughput_tps": 130.0, "abort_rate": 0.2, "ipc": 0.0},
        ),
        SimpleNamespace(
            flags={"BACK_OFF": 1, "BACKOFF_FIXED": 20},
            li={"throughput_tps": 140.0, "abort_rate": 0.3, "ipc": 1.2},
        ),
    ]
    _patch_report_inputs(monkeypatch, view, genomes)
    observed = {}
    _capture_report_plot(monkeypatch, observed)

    result = backoff_sweep_report.report_workload("fixture", {})

    rows = observed["rows"]
    assert math.isnan(rows[0][3])
    assert rows[1][3] == 0.0
    assert rows[2][3] == 1.2
    rendered = observed["render"]
    assert "\tnan\n" in rendered
    assert "—" not in rendered

    report = Path(result["report"]).read_text(encoding="utf-8")
    assert "| 5 | 120 | 10.0% | — | +20.0% |" in report
    assert "| 10 | 130 | 20.0% | 0.00 | +30.0% |" in report
    assert "| 20 | 140 | 30.0% | 1.20 | +40.0% |" in report
    assert ("IPC が実測できた点に限り、backoff を増やすと abort は下がるが "
            "ipc が落ちる trade-off が量の関数として見える。") in report


def test_backoff_report_describes_all_measured_ipc(tmp_path, monkeypatch):
    view = _report_view(tmp_path)
    genomes = [
        SimpleNamespace(flags={"BACK_OFF": 0}, li={"throughput_tps": 100.0}),
        SimpleNamespace(flags={"BACK_OFF": 1, "BACKOFF_FIXED": -1},
                        li={"throughput_tps": 110.0}),
        SimpleNamespace(
            flags={"BACK_OFF": 1, "BACKOFF_FIXED": 5},
            li={"throughput_tps": 120.0, "abort_rate": 0.1, "ipc": 0.0},
        ),
        SimpleNamespace(
            flags={"BACK_OFF": 1, "BACKOFF_FIXED": 10},
            li={"throughput_tps": 130.0, "abort_rate": 0.2, "ipc": 1.2},
        ),
    ]
    _patch_report_inputs(monkeypatch, view, genomes)
    observed = {}
    _capture_report_plot(monkeypatch, observed)

    result = backoff_sweep_report.report_workload("fixture", {})

    report = Path(result["report"]).read_text(encoding="utf-8")
    assert ("abort% と ipc の列で「backoff を増やすと abort は下がるが ipc が落ちる」"
            "trade-off が量の関数として見える。") in report
    assert "IPC が実測できた点に限り" not in report


def test_backoff_report_describes_all_static_ipc_as_unmeasured(tmp_path, monkeypatch):
    view = _report_view(tmp_path)
    genomes = [
        SimpleNamespace(flags={"BACK_OFF": 0}, li={"throughput_tps": 100.0}),
        SimpleNamespace(flags={"BACK_OFF": 1, "BACKOFF_FIXED": -1},
                        li={"throughput_tps": 110.0}),
        SimpleNamespace(
            flags={"BACK_OFF": 1, "BACKOFF_FIXED": 5},
            li={"throughput_tps": 120.0, "abort_rate": 0.1, "ipc": None},
        ),
        SimpleNamespace(
            flags={"BACK_OFF": 1, "BACKOFF_FIXED": 10},
            li={"throughput_tps": 130.0, "abort_rate": 0.2, "ipc": None},
        ),
    ]
    assert all("ipc" in genome.li and genome.li["ipc"] is None
               for genome in genomes[2:])
    _patch_report_inputs(monkeypatch, view, genomes)
    observed = {}
    _capture_report_plot(monkeypatch, observed)

    result = backoff_sweep_report.report_workload("fixture", {})

    assert all(math.isnan(row[3]) for row in observed["rows"])
    assert observed["render"].count("\tnan\n") == 2
    report = Path(result["report"]).read_text(encoding="utf-8")
    assert "| 5 | 120 | 10.0% | — | +20.0% |" in report
    assert "| 10 | 130 | 20.0% | — | +30.0% |" in report
    assert "IPC が実測できた点に限り" in report


def test_backoff_report_treats_missing_ipc_key_as_unmeasured(tmp_path, monkeypatch):
    view = _report_view(tmp_path)
    explicit_none = SimpleNamespace(
        flags={"BACK_OFF": 1, "BACKOFF_FIXED": 5},
        li={"throughput_tps": 120.0, "abort_rate": 0.1, "ipc": None},
    )
    missing_key = SimpleNamespace(
        flags={"BACK_OFF": 1, "BACKOFF_FIXED": 10},
        li={"throughput_tps": 130.0, "abort_rate": 0.2},
    )
    genomes = [
        SimpleNamespace(flags={"BACK_OFF": 0}, li={"throughput_tps": 100.0}),
        SimpleNamespace(flags={"BACK_OFF": 1, "BACKOFF_FIXED": -1},
                        li={"throughput_tps": 110.0}),
        explicit_none,
        missing_key,
    ]
    assert "ipc" in explicit_none.li and explicit_none.li["ipc"] is None
    assert "ipc" not in missing_key.li
    assert missing_key.li.get("ipc") is None
    _patch_report_inputs(monkeypatch, view, genomes)
    observed = {}
    _capture_report_plot(monkeypatch, observed)

    result = backoff_sweep_report.report_workload("fixture", {})

    assert all(math.isnan(row[3]) for row in observed["rows"])
    report = Path(result["report"]).read_text(encoding="utf-8")
    assert report.count("| — |") == 2
    assert "IPC が実測できた点に限り" in report


def test_plot_backoff_loads_nan_ipc_as_missing(tmp_path):
    plot = _load_plot_module()
    layout = _fixture_layout(tmp_path)
    dat = backoff_sweep_report.DatFile(
        title="fixture",
        columns=["backoff_us", "throughput_tps", "abort_pct", "ipc"],
        rows=[[5, 123456, 1.0, backoff_sweep_report._format_ipc(None, dat=True)]],
    )
    rendered = dat.render()
    assert "\tnan\n" in rendered
    assert "—" not in rendered
    Path(layout.reports_dir, "fixture.dat").write_text(
        rendered, encoding="utf-8",
    )

    campaign = plot.load_campaign(layout.root)

    assert campaign["abort_ipc"][5][0] == 1.0
    assert math.isnan(campaign["abort_ipc"][5][1])


def test_backoff_repro_bench_tps_requires_commit(tmp_path):
    layout = _fixture_layout(tmp_path)
    assert _bench_tps(layout, "v-screen") is None
    assert _bench_tps(layout, "v-certified") == 123456.0
    # 既存COMMIT後に再評価benchだけが残っても、後発の未認証値へ更新しない。
    wal.log(layout, "v-certified", STAGE_BENCH_DONE, "test",
            {"median_tps": 999999.0, "tps": [999999.0], "screening": True})
    wal.log(layout, "v-certified", STAGE_ABORT, "test",
            {"reason": "screen-slower-than-floor"})
    assert _bench_tps(layout, "v-certified") == 123456.0


def test_plot_backoff_excludes_and_reports_uncertified_bench_done(tmp_path, capsys):
    plot = _load_plot_module()
    layout = _fixture_layout(tmp_path)
    wal.log(layout, "v-certified", STAGE_BENCH_DONE, "test",
            {"median_tps": 999999.0, "tps": [999999.0], "screening": True})
    wal.log(layout, "v-certified", STAGE_ABORT, "test",
            {"reason": "screen-slower-than-floor"})
    campaign = plot.load_campaign(layout.root)
    assert campaign["pts"] == [(5, [123456.0, 123457.0])]
    assert campaign["excluded_uncertified"] == ["v-certified", "v-screen"]
    assert campaign["read_purpose"] == "HISTORICAL_RAW"
    assert campaign["campaign_verifier_epoch"]["campaign_verifier_epoch"] == "E0"
    assert "999999" not in repr(campaign["pts"])

    out_prefix = str(tmp_path / "plot")
    original_make_figure = plot.make_figure
    plot.make_figure = lambda camps, out: {
        "fixture": {"best_M": 0.12, "best_bf": 5, "none_M": 0.10,
                    "adapt_M": 0.11, "n_reps": 2}}
    try:
        assert plot.main(["plot_backoff.py", out_prefix, layout.root]) == 0
    finally:
        plot.make_figure = original_make_figure
    stdout = capsys.readouterr().out
    assert "excluded 2 uncertified BENCH_DONE (後続COMMITなし): v-certified, v-screen" in stdout
    assert "historical best 0.12M @ 5\u00b5s (epoch=E0;" in stdout
    with open(out_prefix + ".provenance.json", encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["inputs"][0]["excluded_uncertified_bench_done"] == \
        ["v-certified", "v-screen"]
    assert prov["inputs"][0]["read_purpose"] == "HISTORICAL_RAW"
    assert prov["inputs"][0]["campaign_verifier_epoch"][
        "campaign_verifier_epoch"
    ] == "E0"
    assert prov["facts"]["fixture"]["campaign_verifier_epoch"] == "E0"


def test_plot_backoff_rejects_duplicate_tps_before_it_reaches_plot_data(tmp_path):
    plot = _load_plot_module()
    layout = _fixture_layout(tmp_path)
    wal_path = Path(layout.wal_file)
    lines = wal_path.read_text(encoding="utf-8").splitlines(keepends=True)
    for index, line in enumerate(lines):
        record = json.loads(line)
        if record["variant"] == "v-certified" and record["stage"] == STAGE_BENCH_DONE:
            lines[index] = (
                '{"variant":"v-certified","stage":"bench_done","env_tag":"test",'
                '"ts":1,"payload":{"median_tps":123456,'
                '"tps":[123456],"tps":[999999]}}\n'
            )
            break
    else:
        raise AssertionError("fixture に certified BENCH_DONE がない")
    wal_path.write_bytes("".join(lines).encode("utf-8"))

    with pytest.raises(wal.WalDuplicateKeyError, match="tps"):
        plot.load_campaign(layout.root)


def test_plot_backoff_rejects_blank_line_between_records(tmp_path):
    plot = _load_plot_module()
    layout = _fixture_layout(tmp_path)
    wal_path = Path(layout.wal_file)
    lines = wal_path.read_text(encoding="utf-8").splitlines(keepends=True)
    wal_path.write_text("".join([lines[0], "\n", *lines[1:]]), encoding="utf-8")

    with pytest.raises(wal.WalLineError, match="must not be empty"):
        plot.load_campaign(layout.root)


@pytest.mark.parametrize("tail_kind", ["complete-json", "multibyte-partial"])
def test_plot_backoff_rejects_unframed_tail_without_returning_partial_data(
        tmp_path, tail_kind):
    plot = _load_plot_module()
    layout = _fixture_layout(tmp_path)
    wal_path = Path(layout.wal_file)
    if tail_kind == "complete-json":
        tail = json.dumps({
            "variant": "late", "stage": STAGE_BUILD_START,
            "env_tag": "test", "ts": 1,
            "payload": {"genome": "silo|BACK_OFF=1,BACKOFF_FIXED=999"},
        }, separators=(",", ":")).encode("utf-8")
    else:
        tail = b'{"variant":"late-\xe3\x81'
    with wal_path.open("ab") as stream:
        stream.write(tail)

    with pytest.raises(wal.WalFramingError):
        plot.load_campaign(layout.root)
