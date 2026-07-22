# -*- coding: utf-8 -*-
"""bench-first 導入後も backoff consumer が uncertified TPS を漏らさない回帰。"""
from __future__ import annotations

import importlib.util
import json
import os
import sys
from pathlib import Path

import pytest

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_ORCH)
sys.path.insert(0, _ORCH)

from campaign import wal                                      # noqa: E402
from campaign.backoff_repro import _bench_tps                 # noqa: E402
from campaign.layout import CampaignLayout                    # noqa: E402
from campaign.model import (STAGE_ABORT, STAGE_BENCH_DONE,    # noqa: E402
                            STAGE_BUILD_START, STAGE_COMMIT)


def _load_plot_module():
    path = os.path.join(_REPO, "tools", "plotting", "plot_backoff.py")
    spec = importlib.util.spec_from_file_location("plot_backoff_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)
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
    wal.log(layout, "v-certified", STAGE_COMMIT, "test", {"fitness_tps": 123456.0})
    dat = os.path.join(layout.reports_dir, "fixture.dat")
    with open(dat, "w", encoding="utf-8") as f:
        f.write("# workload: fixture\n# env: test\n# campaign: fixture-campaign\n")
        f.write("5 123456 1.0 1.5\n")
    return layout


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
    with open(out_prefix + ".provenance.json", encoding="utf-8") as f:
        prov = json.load(f)
    assert prov["inputs"][0]["excluded_uncertified_bench_done"] == \
        ["v-certified", "v-screen"]


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

    with pytest.raises(plot.campaign_wal.WalDuplicateKeyError, match="tps"):
        plot.load_campaign(layout.root)


def test_plot_backoff_rejects_blank_line_between_records(tmp_path):
    plot = _load_plot_module()
    layout = _fixture_layout(tmp_path)
    wal_path = Path(layout.wal_file)
    lines = wal_path.read_text(encoding="utf-8").splitlines(keepends=True)
    wal_path.write_text("".join([lines[0], "\n", *lines[1:]]), encoding="utf-8")

    with pytest.raises(plot.campaign_wal.WalLineError, match="must not be empty"):
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

    with pytest.raises(plot.campaign_wal.WalFramingError):
        plot.load_campaign(layout.root)
