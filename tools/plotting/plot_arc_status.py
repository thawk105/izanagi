#!/usr/bin/env python3
"""Render recorded paper-story statuses without recomputing judgments."""
from __future__ import annotations

import argparse
import datetime
import hashlib
import itertools
import json
import os
from pathlib import Path
import re
import sys
import tempfile
import unicodedata

import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.font_manager import FontProperties
from matplotlib.lines import Line2D
from matplotlib.patches import Rectangle
from matplotlib.text import Text
from matplotlib.transforms import Bbox
import numpy as np

GENERATOR = Path(__file__).resolve()
GENERATOR_PATH = "tools/plotting/plot_arc_status.py"
REPO_ROOT = GENERATOR.parents[2]
DEFAULT_STATES = "tools/plotting/arc_status_story_2026-09-19.json"
STYLES = {
    "obtained": ("#DCEAF5", "o", "obtained"),
    "uncertified": ("#FCE8CF", "D", "uncertified"),
    "awaiting-ruling": ("#EBDFF2", "^", "awaiting ruling / human action"),
    "not-obtained": ("#EEEEEE", "x", "not obtained"),
}


class FigureDataError(ValueError):
    """Input violates the recorded-status schema."""


class FigureLayoutError(FigureDataError):
    """Rendered artists cannot be published safely."""


def _require(condition, message):
    if not condition:
        raise FigureDataError(message)


def _keys(value, expected):
    _require(type(value) is dict and set(value) == set(expected.split()), "key set mismatch")


def _string(value):
    _require(type(value) is str and bool(value.strip()), "nonempty string required")
    return value


def _pairs(pairs):
    result = {}
    for key, value in pairs:
        _require(key not in result, f"duplicate key: {key}")
        result[key] = value
    return result


def _constant(value):
    raise FigureDataError(f"non-finite JSON constant: {value}")


def check_display_text(value, declared_ids):
    """A small lexical contract, not a natural-language quantity classifier."""
    value = unicodedata.normalize("NFKC", _string(value))
    words = ("tps μs us ms ns sec seconds percent zero one two three four five six "
             "seven eight nine ten eleven twelve twenty thirty hundred thousand million "
             "dozen once twice thrice").split()
    _require(not re.search(r"[=%]|\b(?:" + "|".join(words) + r")\b", value, re.I),
             "quantity in free text")
    for token in re.split(r"[\s;,/]+", value):
        _require(not any(c.isdigit() for c in token) or token in declared_ids,
                 f"undeclared numeric token: {token}")


def _anchor(anchor, sections):
    _string(anchor)
    match = re.fullmatch(r"§8 ([A-Za-z]+[0-9]*-?[0-9]+[a-z]?)", anchor)
    if match:
        section, pattern = 8, r"^- \*\*" + re.escape(match[1]) + r"[ .(]"
    else:
        match = re.fullmatch(r"§0 (item|act) ([1-9][0-9]*)", anchor)
        _require(match is not None, f"invalid anchor: {anchor}")
        section = 0
        pattern = (r"^" + match[2] + r"\. \*\*" if match[1] == "item" else
                   r"^- \*\*第 " + match[2] + r" 幕")
    _require(len(re.findall(pattern, sections[section], re.M)) == 1,
             f"anchor must match exactly one line: {anchor}")


def load_states(repo_root=REPO_ROOT, states=DEFAULT_STATES):
    """Read each input once; retain the exact bytes used for provenance."""
    try:
        root = Path(repo_root).resolve()
        path = (root / states).resolve()
        raw = path.read_bytes()
        data = json.loads(raw, object_pairs_hook=_pairs, parse_constant=_constant)
        _keys(data, "schema story_version story_path figure_created reference_ids state_definitions acts evidence_groups")
        _require(data["schema"] == "izanagi-arc-status/v1", "schema mismatch")
        for key in ("story_version", "figure_created"):
            value = _string(data[key])
            pattern = r"\d{4}-\d{2}-\d{2}[a-z]?" if key == "story_version" else r"\d{4}-\d{2}-\d{2}"
            _require(re.fullmatch(pattern, value) is not None, "ISO date required")
            datetime.date.fromisoformat(value[:10] if key == "story_version" else value)
        _require(data["story_path"] == f"docs/paper-story/{data['story_version']}.md", "story_path mismatch")
        story = (root / data["story_path"]).read_bytes()
        source = story.decode("utf-8")
        sections = {}
        for n in (0, 8):
            match = re.search(rf"^## {n}\. .*?\n(.*?)(?=^## {n+1}\. )", source, re.M | re.S)
            _require(match is not None, f"missing section {n}")
            sections[n] = match[1]
        _keys(data["state_definitions"], " ".join(STYLES))
        refs = data["reference_ids"]
        _require(type(refs) is list and all(type(x) is str and re.fullmatch(
            r"[A-Za-z]+[0-9]*-?[0-9]+[a-z]?", x) for x in refs), "reference_ids format")
        _require(len(refs) == len(set(refs)), "duplicate reference_ids")
        acts, groups = data["acts"], data["evidence_groups"]
        _require(type(acts) is list and len(acts) == 3, "three acts required")
        _require(type(groups) is list and len(groups) == 2, "two groups required")
        ids, free, evidence_ids = set(), list(data["state_definitions"].values()), set()
        for index, container in enumerate(acts + groups):
            is_act = index < 3
            _keys(container, "id label progress source_anchor items" if is_act else "id label items")
            expected_id = f"Act {index + 1}" if is_act else ("A", "B")[index - 3]
            _require(container["id"] == expected_id, "act/group id or order mismatch")
            _string(container["label"])
            if is_act:
                _require(container["progress"] in ("complete", "in-progress"), "invalid progress")
                _anchor(container["source_anchor"], sections)
            free.append(container["label"])
            items = container["items"]
            _require(type(items) is list and bool(items), "nonempty items required")
            if not is_act:
                _require(len(items) == (5 if index == 3 else 11), "evidence group size mismatch")
            for item in items:
                _keys(item, "id label state sublabel source_anchor")
                ident = _string(item["id"])
                _require(ident not in ids, f"duplicate id: {ident}")
                ids.add(ident)
                state = item["state"]
                _require((is_act and state is None) or (type(state) is str and state in STYLES),
                         f"invalid state: {state}")
                if not is_act:
                    evidence_ids.add(ident)
                _anchor(item["source_anchor"], sections)
                free.extend((item["label"], item["sublabel"]))
        for value in free:
            check_display_text(value, evidence_ids | set(refs))
        return {"states": data, "repo_root": root, "input_bytes": [
            ("states", os.path.relpath(path, root), raw), ("story", data["story_path"], story)]}
    except FigureDataError:
        raise
    except (OSError, ValueError, TypeError, KeyError, IndexError) as exc:
        raise FigureDataError(f"malformed states: {exc}") from exc


def _figure_number(prefix):
    match = re.match(r"^fig([0-9]+[a-z]*)_", Path(prefix).name)
    _require(match is not None, "output prefix basename must start with fig<N><letters>_")
    return match[1] if match else Path(prefix).name


def _normalized(parts):
    return " ".join(" ".join(parts).split())


def make_figure(data):
    """Create artists in figure coordinates; no axes or automatic shrinking."""
    fig = plt.figure(figsize=(16, 11.5), dpi=200)
    layout = {"regions": {}, "owners": {}, "siblings": {}, "items": [], "markers": []}
    renderer = fig.canvas.get_renderer()
    px, py = fig.dpi / 72 / fig.bbox.width, fig.dpi / 72 / fig.bbox.height

    def style(state):
        return STYLES[state][:2]

    def region(key, bounds, parent, color=None):
        box = Bbox.from_bounds(*bounds)
        layout["regions"][key] = box
        layout["siblings"].setdefault(parent, []).append(key)
        if color is None:
            return None
        patch = Rectangle(bounds[:2], *bounds[2:], transform=fig.transFigure,
                          facecolor=color, edgecolor="#888888", linewidth=.6)
        fig.add_artist(patch)
        return patch

    def text(owner, x, y, value, size, width=None, bold=False):
        prop = FontProperties(family="DejaVu Sans", size=size, weight="bold" if bold else "normal")
        if width is not None:
            lines, line = [], ""
            for word in value.split():
                candidate = (line + " " + word).strip()
                if line and renderer.get_text_width_height_descent(candidate, prop, False)[0] > width * fig.bbox.width:
                    lines.append(line)
                    line = word
                else:
                    line = candidate
            value = "\n".join(lines + [line])
        artist = fig.text(x, y, value, va="top", fontproperties=prop, linespacing=1.15)
        layout["owners"][artist] = owner
        return artist

    def marker(owner, state, x, y):
        if state is None:
            artist = Line2D([x - 3 * px, x + 3 * px], [y, y], transform=fig.transFigure,
                            color="#666666", linewidth=.8, marker="None")
        else:
            _, shape = style(state)
            artist = Line2D([x], [y], transform=fig.transFigure, linestyle="none", marker=shape,
                            markersize=6, color="#444444",
                            markerfacecolor="#444444" if shape == "o" else "none")
        fig.add_artist(artist)
        layout["markers"].append((artist, owner, state is None))
        return artist

    def record(item, artists, patch=None, mark=None):
        layout["items"].append({"id": item["id"], "state": item.get("state"),
                                "texts": artists, "patch": patch, "marker": mark})

    region("title", (.03, .95, .94, .04), "headings")
    text("title", .03, .97, "Paper-story arc: recorded status", 16, bold=True)
    for i, act in enumerate(data["states"]["acts"]):
        x, y, w, h = .03 + .32 * i, .66, .30, .26
        owner = act["id"]
        region(owner, (x, y, w, h), "acts", "#FAFAFA")
        heading = text(owner, x + 8*px, y+h-8*py, act["id"] + ": " + act["label"], 13, w-16*px, True)
        progress = text(owner, x+8*px, y+h-28*py, act["progress"].replace("-", " "), 10)
        record(act, [heading, progress])
        cursor = y+h-47*py
        for item in act["items"]:
            owner_row = item["id"]
            left = x+22*px
            label = text(owner_row, left, cursor, item["label"], 10, w-30*px)
            height = label.get_window_extent(renderer).height / fig.bbox.height
            sub = text(owner_row, left, cursor-height-2*py, item["sublabel"], 10, w-30*px)
            bottom = sub.get_window_extent(renderer).y0 / fig.bbox.height - 3*py
            region(owner_row, (x+4*px, bottom, w-8*px, cursor-bottom+2*py), owner)
            mark = marker(owner_row, item["state"], x+11*px, cursor-5*py)
            record(item, [label, sub], mark=mark)
            cursor = bottom-3*py
    for gi, group in enumerate(data["states"]["evidence_groups"]):
        heading_y = .63 if gi == 0 else .46
        region("heading-"+group["id"], (.03, heading_y-.022, .94, .025), "headings")
        text("heading-"+group["id"], .03, heading_y, group["label"], 11, bold=True)
        cols, height, top = (5, .12, .605) if gi == 0 else (6, .11, .435)
        width = (.94 - (cols-1)*.01)/cols
        for i, item in enumerate(group["items"]):
            x, y = .03+(i % cols)*(width+.01), top-(i//cols)*(height+.01)-height
            owner = item["id"]
            color, _ = style(item["state"])
            patch = region(owner, (x, y, width, height), group["id"], color)
            left, cursor = x+22*px, y+height-7*py
            artists = []
            for field, size in (("id", 10), ("label", 9), ("sublabel", 8.5)):
                artist = text(owner, left, cursor, item[field], size, width-30*px, field == "id")
                artists.append(artist)
                cursor -= artist.get_window_extent(renderer).height / fig.bbox.height + 3*py
            record(item, artists, patch, marker(owner, item["state"], x+11*px, y+height-12*py))
    for i, (state, definition) in enumerate(data["states"]["state_definitions"].items()):
        x, y, w, h = .03+(i % 2)*.48, .135-(i//2)*.05, .46, .045
        owner = "legend-" + state
        region(owner, (x, y, w, h), "legend", style(state)[0])
        marker(owner, state, x+11*px, y+h-10*py)
        text(owner, x+22*px, y+h-4*py, STYLES[state][2], 9, bold=True)
        text(owner, x+22*px, y+h-17*py, definition, 8.5, w-30*px)
    footnotes = [
        f"Evidence states: paper-story {data['states']['story_version']} section 8; act summaries: section 0. No values drawn.",
        "Obtained does not imply a supported claim. A-3 is a settled rule, not new evidence.",
        "Successor to fig3; the original remains frozen. Statuses are recorded, not evaluated, here.",
    ]
    region("footnotes", (.03, .025, .94, .043), "footnotes")
    for i, value in enumerate(footnotes):
        text("footnotes", .03, .067-i*.015, value, 8)
    return fig, layout


def _intersection(left, right):
    return max(0, min(left.x1, right.x1)-max(left.x0, right.x0)) * max(0, min(left.y1, right.y1)-max(left.y0, right.y0))


def _contains(outer, inner):
    return inner.x0 >= outer.x0-1 and inner.y0 >= outer.y0-1 and inner.x1 <= outer.x1+1 and inner.y1 <= outer.y1+1


def check_figure_layout(fig, layout):
    fig.canvas.draw()
    renderer = fig.canvas.get_renderer()
    regions = {key: box.transformed(fig.transFigure) for key, box in layout["regions"].items()}

    def positive(box):
        if not np.isfinite(box.extents).all() or box.width <= 0 or box.height <= 0:
            raise FigureLayoutError("nonpositive or nonfinite bbox")

    boxes = []
    for artist in fig.findobj(Text):
        if not artist.get_visible() or not artist.get_text().strip():
            continue
        box = artist.get_window_extent(renderer)
        positive(box)
        owner = layout["owners"].get(artist)
        if owner not in regions:
            raise FigureLayoutError("unregistered text")
        if not _contains(fig.bbox, box) or not _contains(regions[owner], box):
            raise FigureLayoutError(f"text escape: {artist.get_text()!r}")
        boxes.append((artist, box))
    for (left, box), (right, other) in itertools.combinations(boxes, 2):
        if _intersection(box, other) > 1:
            raise FigureLayoutError(f"text overlap: {left.get_text()!r} / {right.get_text()!r}")
    for parent, keys in layout["siblings"].items():
        for key in keys:
            positive(regions[key])
            if not _contains(regions.get(parent, fig.bbox), regions[key]):
                raise FigureLayoutError(f"region escape: {key}")
        for left, right in itertools.combinations(keys, 2):
            if _intersection(regions[left], regions[right]) > 1:
                raise FigureLayoutError(f"sibling overlap: {left} / {right}")
    for artist, owner, neutral in layout["markers"]:
        box = artist.get_window_extent(renderer)
        if not neutral:
            positive(box)
        elif not np.isfinite(box.extents).all() or box.width <= 0:
            raise FigureLayoutError("invalid neutral line")
        box = box.padded(fig.dpi/72)
        if not _contains(regions[owner], box):
            raise FigureLayoutError("marker escape")
        if any(_intersection(box, other) > 1 for _, other in boxes):
            raise FigureLayoutError("marker/text overlap")


def _drawn_items(data, layout):
    actual = [{"id": row["id"], "state": row["state"],
               "label": _normalized([t.get_text() for t in row["texts"] if t.get_visible()])}
              for row in layout["items"]]
    expected = []
    for group in data["states"]["acts"] + data["states"]["evidence_groups"]:
        if "progress" in group:
            expected.append(dict(id=group["id"], state=None, label=_normalized([
                group["id"]+":", group["label"], group["progress"].replace("-", " ")])))
        for item in group["items"]:
            ident = "" if "progress" in group else item["id"]
            expected.append(dict(id=item["id"], state=item["state"], label=_normalized([
                ident, item["label"], item["sublabel"]])))
    _require(actual == expected, "drawn_items disagree with states")
    return actual


def _caption(data, number):
    story_version = data["states"]["story_version"]
    template = CAPTION if story_version == "2026-09-19" else GENERIC_CAPTION
    return template.format(number=number, story_version=story_version)


def build_provenance(data, layout, outputs, argv, *, hash_paths=None, figure_number="3b"):
    hashes = outputs if hash_paths is None else hash_paths
    return {
        "schema": "izanagi-arc-status-figure-provenance/v1",
        "generated_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
        **{key: data["states"][key] for key in ("story_version", "story_path", "figure_created", "state_definitions")},
        "inputs": [{"kind": kind, "path": path, "sha256": hashlib.sha256(raw).hexdigest()}
                   for kind, path, raw in data["input_bytes"]],
        "generator": {"path": GENERATOR_PATH, "sha256": hashlib.sha256(GENERATOR.read_bytes()).hexdigest()},
        "outputs": [{"path": os.path.relpath(path, data["repo_root"]),
                     "sha256": hashlib.sha256(Path(source).read_bytes()).hexdigest()}
                    for path, source in zip(outputs, hashes)],
        "drawn_items": _drawn_items(data, layout), "caption": _caption(data, figure_number),
        "argv": list(argv), "versions": {"matplotlib": matplotlib.__version__, "numpy": np.__version__},
    }


def _destinations(prefix):
    paths = [Path(f"{prefix}{suffix}") for suffix in (".png", ".pdf", ".provenance.json")]
    _require(not any(os.path.lexists(p) for p in paths), "output already exists")
    return paths


def _publish_outputs(fig, layout, prefix, data, argv):
    prefix = Path(prefix)
    number = _figure_number(prefix)
    destinations = _destinations(prefix)
    check_figure_layout(fig, layout)
    _drawn_items(data, layout)
    prefix.parent.mkdir(parents=True, exist_ok=True)
    temporary, published = [], []
    try:
        for suffix in (".png", ".pdf", ".provenance.json"):
            fd, name = tempfile.mkstemp(prefix=f".{prefix.name}.", suffix=suffix, dir=prefix.parent)
            os.close(fd)
            temporary.append(Path(name))
        for path, fmt in zip(temporary[:2], ("png", "pdf")):
            fig.savefig(path, format=fmt, dpi=200)
        provenance = build_provenance(data, layout, destinations[:2], argv,
                                      hash_paths=temporary[:2], figure_number=number)
        temporary[2].write_text(json.dumps(provenance, indent=2, allow_nan=False)+"\n", encoding="utf-8")
        for source, destination in zip(temporary, destinations):
            source.chmod(0o644)
            # Atomic no-clobber publication, including a concurrent creator.
            os.link(source, destination)
            published.append(destination)
        return destinations
    except BaseException:
        for path in published:
            path.unlink(missing_ok=True)
        raise
    finally:
        for path in temporary:
            path.unlink(missing_ok=True)


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--repo-root", type=Path, default=REPO_ROOT)
    parser.add_argument("--states", type=Path, default=Path(DEFAULT_STATES))
    parser.add_argument("out_prefix", type=Path)
    args = parser.parse_args(argv)
    figure = None
    try:
        _figure_number(args.out_prefix)
        _destinations(args.out_prefix)
        data = load_states(args.repo_root, args.states)
        figure, layout = make_figure(data)
        recorded_argv = ["python3", GENERATOR_PATH, *(sys.argv[1:] if argv is None else map(str, argv))]
        _publish_outputs(figure, layout, args.out_prefix.resolve(), data, recorded_argv)
    except Exception as exc:
        print(f"[error] {type(exc).__name__}: {exc}", file=sys.stderr)
        return 2
    finally:
        if figure is not None:
            plt.close(figure)
    print(f"wrote {args.out_prefix}.png / .pdf / .provenance.json")
    return 0


# Caption is a fixed structural template, outside the free-text quantity contract.
CAPTION = 'Figure {number}. Status of the paper-story arc read from the frozen {story_version} story: act summaries from section 0 and evidence-item states from section 8. Colors and marker shapes distinguish obtained, uncertified, awaiting ruling / human action, and not obtained. Obtained records that a judgment or completion exists, not that a claim is supported: B-1 remains not met and A-6 records reject. A-3 is a settled reporting rule, not new empirical evidence. A-1 remains descriptive and non-certifying; A-4 is adopted by ruling but inactive pending human action. B-7, B-9, and B-10 are neither promoted nor closed by this figure. This figure summarizes recorded statuses; it does not evaluate correctness, certify performance, or authorize further work. A-2 and A-6 retain the judgments made under the identity layer used at the time; later identity fixes do not strengthen them retrospectively. No measurement values are drawn and no judgments are recomputed. Successor to fig3; the original remains frozen.'

# Generic caption is a fixed structural template, independent of item states.
GENERIC_CAPTION = "Figure {number}. Status of the paper-story arc read from the frozen {story_version} story: act summaries from section 0 and evidence-item states from section 8. Colors and marker shapes distinguish obtained, uncertified, awaiting ruling / human action, and not obtained. Obtained records that a judgment or completion exists, not that a claim is supported; each item's sublabel carries the recorded judgment words and limitations. This figure summarizes recorded statuses; it does not evaluate correctness, certify performance, or authorize further work. Recorded judgments keep the identity layer used at the time; later identity fixes do not strengthen them retrospectively. No measurement values are drawn and no judgments are recomputed. Successor to fig3; the original remains frozen."

if __name__ == "__main__":
    raise SystemExit(main())
