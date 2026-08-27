# -*- coding: utf-8 -*-
"""plot_backoff._ci95 の 95% CI が t 分布規約 (FIGURE_CONVENTIONS.md §2) に従う回帰。

正本規約: 点推定 = 標本平均、CI 半幅 = 小 n では t_{0.975,n-1}·s/√n、n>=30 で
1.96·s/√n の正規近似。既知入力の期待値で t 分布使用 (1.96 固定でないこと) を固定する。
"""
from __future__ import annotations

import hashlib
import importlib.util
import json
import math
import os
import sys
import tempfile
from pathlib import Path
from types import SimpleNamespace

_HERE = os.path.dirname(os.path.abspath(__file__))
_ORCH = os.path.dirname(_HERE)
_REPO = os.path.dirname(_ORCH)
sys.path.insert(0, _HERE)

from skiputil import Skip, skip                                  # noqa: E402


def _load_plot_module(need_numpy=True):
    path = os.path.join(_REPO, "tools", "plotting", "plot_backoff.py")
    spec = importlib.util.spec_from_file_location("plot_backoff_ci_under_test", path)
    module = importlib.util.module_from_spec(spec)
    assert spec.loader is not None
    spec.loader.exec_module(module)   # module top-level は numpy 非依存 (遅延 import)。
    if need_numpy:
        # _ci95 は np のみ使う。matplotlib (作図専用) を要求せず np だけ注入する。
        try:
            import numpy as _np
        except ImportError as exc:
            skip(f"numpy 不在で _ci95 を検証できない: {exc}")
        module.np = _np
    return module


def test_t975_table_matches_known_critical_values():
    """内蔵 t 表が代表的自由度の t_{0.975,df} と一致し、n>=30 は 1.96 に落ちる。"""
    plot = _load_plot_module(need_numpy=False)   # 純粋な表引き、numpy 不要。
    assert plot._t975(1) == 12.706          # n=2
    assert plot._t975(4) == 2.776           # n=5 (実 campaign)
    assert plot._t975(28) == 2.048          # n=29 (t 表の下端)
    assert plot._t975(29) == 1.96           # n=30: 正規近似に切替
    assert plot._t975(100) == 1.96          # 大 n も 1.96


def test_ci95_small_n_uses_t_distribution():
    """n=5, reps=[1..5] → mean=3.0, 半幅 = t4·s/√n = 2.776·sqrt(0.5)。

    std(ddof=1) = sqrt(2.5), s/√n = sqrt(2.5)/sqrt(5) = sqrt(0.5)。旧実装 (1.96 固定)
    なら半幅 = 1.96·sqrt(0.5) ≈ 1.386 で、t4 期待値 ≈ 1.963 とは一致しない。
    """
    plot = _load_plot_module()
    center, half = plot._ci95([1.0, 2.0, 3.0, 4.0, 5.0])
    expected_half = 2.776 * math.sqrt(0.5)   # ≈ 1.96293
    assert abs(center - 3.0) < 1e-9, center
    assert abs(half - expected_half) < 1e-9, (half, expected_half)
    # 1.96 固定の旧挙動と明確に乖離していること (退行検知)。
    assert abs(half - 1.96 * math.sqrt(0.5)) > 0.5


def test_ci95_center_is_mean_not_median():
    """CI 半幅は平均 SE ベースなので中心も標本平均 (median との差で確認)。"""
    plot = _load_plot_module()
    # 歪んだ標本: median=2.0 だが mean=4.0。
    center, _ = plot._ci95([1.0, 2.0, 9.0])
    assert abs(center - 4.0) < 1e-9, center


def test_ci95_single_sample_ci_incalculable():
    """n<2 は分散を推定できず CI 計算不能 → 半幅は None (幅ゼロの誤差棒を描かない)。

    旧契約は半幅 0.0 を返し、図に幅ゼロの誤差棒が「95% CI」として描かれていた
    (分散未知なのに不確かさゼロと誤読させる)。None を返して描画側が誤差棒を抑止する。
    """
    plot = _load_plot_module()
    center, half = plot._ci95([123456.0])
    assert center == 123456.0
    assert half is None


def test_ci95_half_M_suppresses_errorbar_when_incalculable():
    """描画ヘルパ: n<2 は NaN (errorbar が誤差棒を描かない)、n>=2 は半幅/1e6。"""
    plot = _load_plot_module()
    assert math.isnan(plot._ci95_half_M([123456.0]))     # n=1 → 誤差棒抑止
    half_M = plot._ci95_half_M([1.0e6, 2.0e6, 3.0e6, 4.0e6, 5.0e6])
    expected_half_M = 2.776 * math.sqrt(0.5)             # n=5, 単位 1e6 tps
    assert not math.isnan(half_M)
    assert abs(half_M - expected_half_M) < 1e-9, (half_M, expected_half_M)


def test_ci95_large_n_uses_normal_approx():
    """n>=30 は 1.96·s/√n の正規近似 (t 表を引かない)。"""
    plot = _load_plot_module()
    reps = [float(i) for i in range(1, 31)]   # n=30
    np = plot.np
    a = np.asarray(reps, dtype=float)
    expected_half = 1.96 * a.std(ddof=1) / math.sqrt(30)
    _, half = plot._ci95(reps)
    assert abs(half - expected_half) < 1e-9, (half, expected_half)


class _RecordingAxis:
    def __init__(self):
        self.spans = []
        self.lines = []
        self.texts = []

    def axhspan(self, low, high, **kwargs):
        self.spans.append((low, high, kwargs))

    def axhline(self, center, **kwargs):
        self.lines.append((center, kwargs))

    def get_yaxis_transform(self):
        return "recording-transform"

    def text(self, x, y, label, **kwargs):
        self.texts.append((x, y, label, kwargs))


def test_each_baseline_draws_mean_line_and_t95_band():
    """no-backoff / stock-adaptive のどちらも同じ CI 帯契約を使う。"""
    plot = _load_plot_module()
    reps = [1.0e6, 2.0e6, 3.0e6, 4.0e6, 5.0e6]
    expected_half_M = 2.776 * math.sqrt(0.5)
    for baseline in plot.BASELINE_ORDER:
        axis = _RecordingAxis()
        record = plot._draw_baseline(axis, reps, plot.BASELINE_SPECS[baseline])
        assert record["value_tps"] == 3.0e6
        assert record["label"] == plot.BASELINE_SPECS[baseline]["label"]
        assert abs(record["ci95_half_tps"] - expected_half_M * 1e6) < 1e-6
        assert len(axis.lines) == 1
        assert len(axis.spans) == 1
        assert axis.texts[0][1:3] == (3.0, record["label"])
        low, high, _style = axis.spans[0]
        assert abs(low - (3.0 - expected_half_M)) < 1e-9
        assert abs(high - (3.0 + expected_half_M)) < 1e-9


def test_baseline_single_sample_draws_line_without_ci_band():
    """n<2 は平均線だけを描き、幅ゼロの 95% CI 帯は作らない。"""
    plot = _load_plot_module()
    axis = _RecordingAxis()
    record = plot._draw_baseline(
        axis, [123456.0], plot.BASELINE_SPECS["no-backoff"])
    assert record == {
        "label": "no backoff",
        "value_tps": 123456.0,
        "ci95_half_tps": None,
    }
    assert len(axis.lines) == 1
    assert axis.spans == []


def test_baseline_cli_keeps_legacy_call_and_accepts_no_backoff_only():
    plot = _load_plot_module(need_numpy=False)
    legacy = plot._parse_cli(["plot_backoff.py", "out", "campaign"])
    assert legacy == ("out", ["campaign"], ("no-backoff", "stock-adaptive"))
    selected = plot._parse_cli([
        "plot_backoff.py", "--baselines", "no-backoff", "out", "campaign",
    ])
    assert selected == ("out", ["campaign"], ("no-backoff",))


def test_baseline_cli_rejects_unknown_name():
    plot = _load_plot_module(need_numpy=False)
    try:
        plot._parse_cli([
            "plot_backoff.py", "--baselines", "no-backoff,mystery", "out", "campaign",
        ])
    except ValueError as exc:
        assert "mystery" in str(exc)
    else:
        raise AssertionError("unknown baseline was accepted")


def test_boolean_condition_spellings_and_numactl_arguments_are_meaning_preserving():
    plot = _load_plot_module(need_numpy=False)
    assert plot._condition_scalar("ycsb_rmw", "false") is False
    assert plot._condition_scalar("ycsb_rmw", "0") is False
    assert plot._condition_scalar("ycsb_rmw", "true") is True
    assert plot._condition_scalar("ycsb_rmw", "1") is True
    assert plot._numactl_arguments(
        "numactl --interleave=all /tmp/ycsb_silo.exe") == ["--interleave=all"]
    assert plot._numactl_arguments(
        "numactl --localalloc /tmp/ycsb_silo.exe") == ["--localalloc"]


def test_empty_tps_is_rejected_instead_of_becoming_nan():
    plot = _load_plot_module(need_numpy=False)
    try:
        plot._mean_tps([])
    except ValueError as exc:
        assert "must not be empty" in str(exc)
    else:
        raise AssertionError("empty tps repetitions were accepted")


def _figure_campaign(name, workload, scale):
    return {
        "campaign": name,
        "workload": workload,
        "pts": [
            (2, [2.0e6 * scale, 2.2e6 * scale]),
            (4, [2.4e6 * scale, 2.6e6 * scale]),
            (8, [2.1e6 * scale, 2.3e6 * scale]),
        ],
        "none": [1.8e6 * scale, 2.0e6 * scale],
        "adapt": [1.1e6 * scale, 1.3e6 * scale],
        "baseline_genomes": {
            "no-backoff": {"BACKOFF_FIXED": "-1", "BACK_OFF": "0"},
            "stock-adaptive": {"BACKOFF_FIXED": "-1", "BACK_OFF": "1"},
        },
        "abort_ipc": {2: (1.0, 1.1), 4: (2.0, 1.2), 8: (3.0, 1.3)},
        "threads": [48],
        "env": "linux-baremetal",
        "dir": f"output/campaigns/{name}",
        "wal": f"output/campaigns/{name}/runs/wal.jsonl",
        "wal_sha256": "w" * 64,
        "dat": f"output/campaigns/{name}/reports/{name}.dat",
        "dat_sha256": "d" * 64,
        "lock": f"output/campaigns/{name}/campaign.lock",
        "lock_sha256": "l" * 64,
        "conditions": {},
        "excluded_uncertified": [],
        "read_purpose": "HISTORICAL_RAW",
        "campaign_verifier_epoch": {
            "campaign_verifier_epoch": "E0",
            "state": "absent",
            "reason_code": "fixture",
            "identity_scope": [],
            "excluded_scope": [],
            "verifier_assessment_basis": (
                "recorded-at-original-verifier-epoch"
            ),
        },
    }


def test_actual_panel_artists_match_serialized_baseline_records():
    """各 panel の line y / text label と main が書く baselines[] を直接照合する。"""
    plot = _load_plot_module(need_numpy=False)
    campaigns = {
        "write": _figure_campaign("write", "write-heavy", 1.0),
        "balanced": _figure_campaign("balanced", "balanced", 1.3),
    }
    original_load_campaign = plot.load_campaign
    plot.load_campaign = campaigns.__getitem__
    try:
        with tempfile.TemporaryDirectory(prefix="backoff-artist-") as temp:
            out_prefix = str(Path(temp) / "figure")
            assert plot.main([
                "plot_backoff.py", out_prefix, "write", "balanced",
            ]) == 0
            provenance = json.loads(Path(
                out_prefix + ".provenance.json").read_text(encoding="utf-8"))
            figure = plot.plt.gcf()
            top_axes = figure.axes[:len(campaigns)]
            assert len(provenance["inputs"]) == len(top_axes)
            for axis, input_row in zip(top_axes, provenance["inputs"]):
                assert input_row["campaign_verifier_epoch"][
                    "verifier_assessment_basis"
                ] == "recorded-at-original-verifier-epoch"
                rows = input_row["baselines"]
                labels = {row["label"] for row in rows}
                baseline_texts = [text for text in axis.texts if text.get_text() in labels]
                assert len(baseline_texts) == len(rows)
                horizontal_y = []
                for line in axis.lines:
                    ydata = list(line.get_ydata())
                    if len(ydata) == 2 and math.isclose(float(ydata[0]), float(ydata[1])):
                        horizontal_y.append(float(ydata[0]))
                assert len(horizontal_y) == len(rows)
                for row in rows:
                    expected_y = row["value_tps"] / 1e6
                    matches = [text for text in baseline_texts
                               if text.get_text() == row["label"]]
                    assert len(matches) == 1
                    assert math.isclose(float(matches[0].get_position()[1]), expected_y)
                    assert sum(math.isclose(y, expected_y) for y in horizontal_y) == 1
    finally:
        plot.load_campaign = original_load_campaign
        if plot.plt is not None:
            plot.plt.close("all")


def test_figure_epoch_label_keeps_exact_recorded_epochs():
    plot = _load_plot_module(need_numpy=False)
    e1 = "E1:" + "a" * 64
    camps = [
        {"campaign_verifier_epoch": {"campaign_verifier_epoch": "E0"}},
        {"campaign_verifier_epoch": {"campaign_verifier_epoch": e1}},
    ]
    assert plot._figure_epoch_label(camps) == f"E0, {e1}"


def test_load_campaign_projects_historical_verifier_assessment_basis():
    plot = _load_plot_module(need_numpy=False)
    marker = "recorded-at-original-verifier-epoch"
    original = plot.require_admitted_campaign
    try:
        with tempfile.TemporaryDirectory(prefix="backoff-historical-marker-") as temp:
            campaign = Path(temp) / "campaign"
            wal_path = campaign / "runs" / "wal.jsonl"
            dat_path = campaign / "reports" / "fixture.dat"
            lock_path = campaign / "campaign.lock"
            wal_path.parent.mkdir(parents=True)
            dat_path.parent.mkdir(parents=True)
            wal_path.write_text("", encoding="utf-8")
            dat_path.write_text("# workload: fixture\n", encoding="utf-8")
            lock_path.write_text("{}\n", encoding="utf-8")
            view = SimpleNamespace(
                wal_file=str(wal_path),
                records=(),
                read_purpose=plot.CampaignReadPurpose.HISTORICAL_RAW,
                verifier_assessment_basis=marker,
                campaign_verifier_epoch=SimpleNamespace(
                    campaign_verifier_epoch="E0",
                    state="E0",
                    reason_code="v1-authority-absent",
                    identity_scope="fixture identity scope",
                    excluded_scope="fixture excluded scope",
                ),
            )

            def historical_only(cdir, *, purpose):
                assert Path(cdir) == campaign
                assert purpose is plot.CampaignReadPurpose.HISTORICAL_RAW
                return view

            plot.require_admitted_campaign = historical_only
            projected = plot.load_campaign(campaign)
    finally:
        plot.require_admitted_campaign = original

    assert projected["campaign_verifier_epoch"][
        "verifier_assessment_basis"
    ] == marker


def test_production_provenance_records_current_generator_source_sha():
    plot = _load_plot_module(need_numpy=False)
    campaign = _figure_campaign("fixture", "read-heavy", 1.0)
    original_load = plot.load_campaign
    original_make = plot.make_figure

    def load_fixture(_campaign_dir):
        return campaign

    def make_fixture(_campaigns, out_prefix):
        Path(f"{out_prefix}.png").write_bytes(b"fixture-png")
        Path(f"{out_prefix}.pdf").write_bytes(b"fixture-pdf")
        return ({
            "read-heavy": {
                "best_M": 1.0,
                "best_bf": 1,
                "none_M": 1.0,
                "adapt_M": 1.0,
                "n_reps": 1,
            },
        }, [[]])

    plot.load_campaign = load_fixture
    plot.make_figure = make_fixture
    try:
        with tempfile.TemporaryDirectory(prefix="backoff-current-generator-") as temp:
            prefix = str(Path(temp) / "figure")
            assert plot.main(["plot_backoff.py", prefix, "fixture"]) == 0
            provenance = json.loads(
                Path(f"{prefix}.provenance.json").read_text(encoding="utf-8")
            )
    finally:
        plot.load_campaign = original_load
        plot.make_figure = original_make

    generator_path = Path(plot.__file__).resolve()
    expected_sha256 = hashlib.sha256(generator_path.read_bytes()).hexdigest()
    assert provenance["generator_source"] == {
        "path": "tools/plotting/plot_backoff.py",
        "sha256": expected_sha256,
    }


# ---- 素の runner (pytest 無しでも) ----

def _run():
    fns = [v for k, v in sorted(globals().items())
           if k.startswith("test_") and callable(v)]
    passed = failed = skipped = 0
    for fn in fns:
        try:
            fn()
            print(f"PASS {fn.__name__}")
            passed += 1
        except Skip as e:
            print(f"SKIP {fn.__name__}: {e}")
            skipped += 1
        except AssertionError as e:
            print(f"FAIL {fn.__name__}: {e}")
            failed += 1
        except Exception as e:  # noqa: BLE001
            print(f"ERROR {fn.__name__}: {type(e).__name__}: {e}")
            failed += 1
    print(f"\n{passed} passed, {failed} failed, {skipped} skipped")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(_run())
