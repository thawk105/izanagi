"""T1–T8: real snapshot, independent styles/hashes, fail-closed publication."""
from __future__ import annotations

import hashlib
import importlib.util
import json
import os
from pathlib import Path
import shutil
import stat
import subprocess
import sys

os.environ["MPLBACKEND"] = "Agg"
import pytest
from matplotlib.colors import to_rgba

REPO = Path(__file__).resolve().parents[2]
SCRIPT = REPO / "tools/plotting/plot_arc_status.py"
STATES = REPO / "tools/plotting/arc_status_story_2026-09-19.json"
spec = importlib.util.spec_from_file_location("arc_status_under_test", SCRIPT)
PLOT = importlib.util.module_from_spec(spec)
spec.loader.exec_module(PLOT)

# Independent specification, not derived from the generator table.
EXPECTED_STYLES = {
    "obtained": ("#DCEAF5", "o", "#444444"),
    "uncertified": ("#FCE8CF", "D", "none"),
    "awaiting-ruling": ("#EBDFF2", "^", "none"),
    "not-obtained": ("#EEEEEE", "x", "none"),
}


def _raw():
    return json.loads(STATES.read_bytes())


def _expected(raw):
    result = []
    for group in raw["acts"] + raw["evidence_groups"]:
        act = "progress" in group
        if act:
            result.append({"id": group["id"], "state": None,
                           "label": f"{group['id']}: {group['label']} {group['progress'].replace('-', ' ')}"})
        for item in group["items"]:
            result.append({"id": item["id"], "state": item["state"],
                           "label": f"{'' if act else item['id'] + ' '}{item['label']} {item['sublabel']}"})
    return result


@pytest.fixture(scope="module")
def production():
    data = PLOT.load_states(REPO)
    fig, layout = PLOT.make_figure(data)
    try:
        yield data, fig, layout
    finally:
        PLOT.plt.close(fig)


def _styles_and_provenance(data, layout, raw):
    prov = PLOT.build_provenance(data, layout, [], ["style-probe"])
    assert prov["drawn_items"] == _expected(raw)
    inputs = {item["id"]: item for group in raw["acts"] + raw["evidence_groups"] for item in group["items"]}
    for drawn in layout["items"]:
        if drawn["id"] not in inputs:
            continue
        state = inputs[drawn["id"]]["state"]
        mark = drawn["marker"]
        if state is None:
            assert mark.get_marker() == "None"
            assert len(mark.get_xdata()) == 2
        else:
            color, shape, fill = EXPECTED_STYLES[state]
            assert mark.get_marker() == shape
            assert to_rgba(mark.get_markerfacecolor()) == to_rgba(fill)
            if drawn["patch"] is not None:
                assert drawn["patch"].get_facecolor() == to_rgba(color)
    return prov


def test_t1_real_states_render_at_production_size(production):
    _, fig, layout = production
    PLOT.check_figure_layout(fig, layout)
    assert tuple(fig.get_size_inches()) == (16, 11.5)
    assert fig.dpi == 200 and fig.axes == []
    assert len(layout["siblings"]["acts"]) == 3
    assert len(layout["siblings"]["A"]) == 5
    assert len(layout["siblings"]["B"]) == 11
    actual = [" ".join(" ".join(t.get_text() for t in row["texts"]).split()) for row in layout["items"]]
    assert actual == [row["label"] for row in _expected(_raw())]
    assert len(layout["items"]) == 27


def test_t2_independent_styles_and_changed_state(production, tmp_path):
    data, _, layout = production
    _styles_and_provenance(data, layout, _raw())
    path = tmp_path / STATES.name
    shutil.copyfile(STATES, path)
    raw = json.loads(path.read_bytes())
    raw["evidence_groups"][0]["items"][0]["state"] = "obtained"
    path.write_text(json.dumps(raw), encoding="utf-8")
    changed = PLOT.load_states(REPO, path)
    fig, artists = PLOT.make_figure(changed)
    try:
        # Actual full-size artists measured with Agg; style checks need no
        # additional whole-canvas rasterization.
        prov = _styles_and_provenance(changed, artists, raw)
        assert next(row for row in prov["drawn_items"] if row["id"] == "A-1")["state"] == "obtained"
    finally:
        PLOT.plt.close(fig)


BAD_CASES = [
    ("bogus-state", "invalid state"), ("null-evidence", "invalid state"),
    ("duplicate-id", "duplicate id"), ("unknown-item-key", "key set"),
    ("missing-item-key", "key set"), ("unknown-top-key", "key set"),
    ("unknown-act-key", "key set"), ("unknown-group-key", "key set"),
    ("unknown-definition-key", "key set"), ("invalid-anchor", "invalid anchor"),
    ("absent-anchor", "exactly one line"), ("nonunique-anchor", "exactly one line"),
    ("story-path", "story_path mismatch"), ("percent", "quantity"),
    ("group-percent", "quantity"),
    ("throughput", "quantity"), ("latency", "quantity"), ("assignment", "quantity"),
    ("duplicate-key", "duplicate key"), ("nan", "non-finite"),
    ("infinity", "non-finite"), ("negative-infinity", "non-finite"),
]


@pytest.mark.parametrize("case,reason", BAD_CASES, ids=[x[0] for x in BAD_CASES])
def test_t3_invalid_json_without_drawing(tmp_path, case, reason):
    path = tmp_path / STATES.name
    shutil.copyfile(STATES, path)
    raw = json.loads(path.read_bytes())
    item = raw["evidence_groups"][0]["items"][0]
    root = REPO
    if case == "bogus-state":
        item["state"] = "bogus"
    elif case == "null-evidence":
        item["state"] = None
    elif case == "duplicate-id":
        item["id"] = "A-2"
    elif case == "missing-item-key":
        del item["label"]
    elif case.startswith("unknown-"):
        target = {"unknown-item-key": item, "unknown-top-key": raw,
                  "unknown-act-key": raw["acts"][0], "unknown-group-key": raw["evidence_groups"][0],
                  "unknown-definition-key": raw["state_definitions"]}[case]
        target["extra"] = "Additional definition." if case == "unknown-definition-key" else 1
    elif case == "invalid-anchor":
        item["source_anchor"] = "§8:L1-L2"
    elif case == "absent-anchor":
        item["source_anchor"] = "§8 A-99"
    elif case == "nonunique-anchor":
        root = tmp_path
        story_path = root / raw["story_path"]
        story_path.parent.mkdir(parents=True)
        source = (REPO / raw["story_path"]).read_text()
        story_path.write_text(source.replace(
            "## 9. ", "- **A-1 (duplicate anchor fixture)**\n\n## 9. ", 1))
    elif case == "story-path":
        raw["story_path"] = "docs/paper-story/2026-09-20.md"
    elif case == "group-percent":
        raw["evidence_groups"][0]["label"] = "38%"
    elif case in ("percent", "throughput", "latency", "assignment"):
        item["label"] = {"percent": "38%", "throughput": "10 tps", "latency": "2 µs", "assignment": "A=0.58"}[case]
    text = json.dumps(raw)
    if case == "duplicate-key":
        text = text.replace('"label":', '"label": "duplicate", "label":', 1)
    elif case in ("nan", "infinity", "negative-infinity"):
        text = text.replace('"state": "uncertified"', '"state": '+{
            "nan": "NaN", "infinity": "Infinity", "negative-infinity": "-Infinity"}[case], 1)
    path.write_text(text, encoding="utf-8")
    with pytest.raises(PLOT.FigureDataError, match=reason):
        PLOT.load_states(root, path)


def test_t4_free_text_contract():
    allowed = {"A-1", "S-1a", "P2-4", "D2114", "fig8", "T-1998"}
    PLOT.check_display_text("A-1 / S-1a; P2-4, D2114 fig8 T-1998", allowed)
    for value in ("38%", "10 tps", "2 µs", "A=0.58", "three runs", "applied twice",
                  "３８％", "١٢", "A-1suffix", "fig8.5", "a dozen runs", "2 μs", "ten seconds"):
        with pytest.raises(PLOT.FigureDataError):
            PLOT.check_display_text(value, allowed)


def _overlap(layout):
    row = next(row for row in layout["items"] if row["id"] == "A-1")
    # Both Texts stay in the same cell, away from the marker.
    row["texts"][2].set_position(row["texts"][1].get_position())


@pytest.fixture
def overlap_figure():
    data = PLOT.load_states(REPO)
    fig, layout = PLOT.make_figure(data)
    _overlap(layout)
    try:
        yield data, fig, layout
    finally:
        PLOT.plt.close(fig)


@pytest.fixture
def escape_figure():
    data = PLOT.load_states(REPO)
    fig, layout = PLOT.make_figure(data)
    layout["items"][-1]["texts"][-1].set_position((1.2, 1.2))
    try:
        yield data, fig, layout
    finally:
        PLOT.plt.close(fig)


@pytest.mark.parametrize("fixture,reason", [("overlap_figure", "text overlap"), ("escape_figure", "text escape")], ids=["overlap", "escape"])
def test_t5_layout_rejects_overlap_and_escape(request, fixture, reason):
    _, fig, layout = request.getfixturevalue(fixture)
    with pytest.raises(PLOT.FigureLayoutError, match=reason):
        PLOT.check_figure_layout(fig, layout)


def test_t6_publisher_rejects_collision_without_files(overlap_figure, tmp_path):
    data, fig, layout = overlap_figure
    with pytest.raises(PLOT.FigureLayoutError, match="text overlap"):
        PLOT._publish_outputs(fig, layout, tmp_path / "new" / "fig3b_collision", data, ["probe"])
    assert list(tmp_path.iterdir()) == []


def _cli(prefix):
    return subprocess.run([sys.executable, str(SCRIPT), "--repo-root", str(REPO), str(prefix)],
                          capture_output=True, text=True, env={**os.environ, "MPLBACKEND": "Agg"})


def test_t7_cli_outputs_and_independent_hashes(tmp_path):
    prefix = tmp_path / "fig3b_test"
    result = _cli(prefix)
    assert result.returncode == 0, result.stderr
    paths = [Path(str(prefix)+suffix) for suffix in (".png", ".pdf", ".provenance.json")]
    assert set(tmp_path.iterdir()) == set(paths)
    assert all(stat.S_IMODE(path.stat().st_mode) == 0o644 for path in paths)
    assert paths[0].read_bytes().startswith(b"\x89PNG\r\n\x1a\n")
    assert paths[1].read_bytes().startswith(b"%PDF-")
    prov = json.loads(paths[2].read_bytes())
    assert set(prov) == {"schema", "generated_utc", "story_version", "story_path", "figure_created",
                         "inputs", "generator", "outputs", "drawn_items", "state_definitions", "caption", "argv", "versions"}
    assert prov["schema"] == "izanagi-arc-status-figure-provenance/v1"
    assert prov["story_version"] == "2026-09-19" and prov["figure_created"] == "2026-09-20"
    assert [row["kind"] for row in prov["inputs"]] == ["states", "story"]
    for row in prov["inputs"] + [prov["generator"]] + prov["outputs"]:
        assert row["sha256"] == hashlib.sha256((REPO / row["path"]).read_bytes()).hexdigest()
    assert prov["drawn_items"] == _expected(_raw())
    assert prov["state_definitions"] == _raw()["state_definitions"]
    assert prov["caption"].startswith("Figure 3b. Status of the paper-story arc read from the frozen 2026-09-19 story:")
    for clause in ("B-1 remains not met", "A-6 records reject", "A-3 is a settled reporting rule",
                   "A-4 is adopted by ruling but inactive pending human action",
                   "later identity fixes do not strengthen them retrospectively.",
                   "No measurement values are drawn and no judgments are recomputed."):
        assert clause in prov["caption"]
    assert prov["argv"] == ["python3", "tools/plotting/plot_arc_status.py", "--repo-root", str(REPO), str(prefix)]
    assert set(prov["versions"]) == {"matplotlib", "numpy"} and all(prov["versions"].values())
    before = [p.read_bytes() for p in paths]
    repeated = _cli(prefix)
    assert repeated.returncode == 2 and "output already exists" in repeated.stderr
    assert before == [p.read_bytes() for p in paths]


def test_t8_cli_rejects_invalid_prefix(tmp_path):
    result = _cli(tmp_path / "foo_x")
    assert result.returncode == 2
    assert "[error] FigureDataError: output prefix" in result.stderr
    assert list(tmp_path.iterdir()) == []
