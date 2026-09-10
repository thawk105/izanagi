"""Real temporary Git trees for the one-time layout; no evidence regeneration."""
import gzip
import json
from pathlib import Path
import re
import subprocess
import sys
from urllib.parse import unquote

import pytest

from tools import insights_date_layout as layout


def put(root, rel, data=b"research\n", mode=0o644):
    path = root / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    path.chmod(mode)
    return path


def seal(root):
    def git(*args):
        return subprocess.check_output(["git", *args], cwd=root)
    git("init", "-q")
    git("add", ".")
    git("-c", "user.name=Fixture", "-c", "user.email=fixture@example.invalid",
        "-c", "core.hooksPath=/dev/null", "commit", "-qm", "fixture")
    return git("rev-parse", "HEAD").decode().strip()


def test_moves_preserve_bytes_modes_and_retained_entries(tmp_path):
    old = layout.PREFIX + "2026-08-01_notes"
    packed = gzip.compress(b"archived evidence\n", mtime=0)
    put(tmp_path, old + "/report.md")
    put(tmp_path, old + "/verbatim/log.txt.gz", packed, 0o640)
    retained = layout.PREFIX + "2026-08-02_driver/run.sh"
    put(tmp_path, retained, b"#!/bin/sh\n", 0o755)
    base = seal(tmp_path)
    before = {str(p.relative_to(tmp_path)): (p.read_bytes(), p.stat().st_mode)
              for p in (tmp_path / layout.PREFIX).rglob("*") if p.is_file()}
    plan = layout.build_plan(tmp_path, base)
    assert plan["moves"] == {"2026-08-01_notes": "2026-08-01/notes"}
    assert (tmp_path / old).exists()  # Planning is read-only.
    layout.apply_plan(tmp_path, plan)
    for old_path, (data, mode) in before.items():
        current = tmp_path / layout.relocated(old_path, plan["moves"])
        assert current.read_bytes() == data
        assert current.stat().st_mode == mode
    layout.verify(tmp_path, plan["files"], plan["moves"])
    assert subprocess.check_output(["git", "diff", "--cached", "--name-only"], cwd=tmp_path) == b""


def test_destination_collision_preflights_before_any_move(tmp_path):
    put(tmp_path, layout.PREFIX + "2026-08-01_a/report.md")
    put(tmp_path, layout.PREFIX + "2026-08-02_b/report.md")
    base = seal(tmp_path)
    plan = layout.build_plan(tmp_path, base)
    # Empty directories are not inventory leaves: this isolates the destination
    # guard from the independent untracked-file guard (registered M2).
    target = tmp_path / layout.PREFIX / "2026-08-02/b"
    target.mkdir(parents=True)
    with pytest.raises(ValueError, match="destination collision"):
        layout.apply_plan(tmp_path, plan)
    assert target.is_dir() and not list(target.iterdir())
    assert (tmp_path / layout.PREFIX / "2026-08-01_a/report.md").read_bytes() == b"research\n"
    assert (tmp_path / layout.PREFIX / "2026-08-02_b/report.md").exists()


def test_new_consumer_invalidates_reviewed_plan_without_moving(tmp_path):
    source = put(tmp_path, layout.PREFIX + "2026-08-01_notes/report.md")
    consumer = put(tmp_path, "tools/consumer.py", b"# unrelated\n")
    base = seal(tmp_path)
    plan = layout.build_plan(tmp_path, base)
    consumer.write_bytes(b'path = "2026-08-01_notes"\n')
    with pytest.raises(ValueError, match="stale or edited"):
        layout.apply_plan(tmp_path, plan)
    assert source.read_bytes() == b"research\n"
    assert not (tmp_path / layout.PREFIX / "README.md").exists()


@pytest.mark.parametrize("change", ["bytes", "mode", "extra", "empty-dir", "symlink"])
def test_source_drift_rejected(tmp_path, change):
    path = put(tmp_path, layout.PREFIX + "2026-08-01_a/report.md")
    base = seal(tmp_path)
    if change == "bytes":
        path.write_bytes(b"dirty")
    elif change == "mode":
        path.chmod(0o755)
    elif change == "extra":
        put(tmp_path, layout.PREFIX + "2026-08-01_a/untracked")
    elif change == "empty-dir":
        (path.parent / "untracked-dir").mkdir()
    else:
        path.unlink()
        path.symlink_to("/dev/null")
    with pytest.raises(ValueError):
        layout.build_plan(tmp_path, base)


def test_pins_and_existing_links_are_retained_but_broken_links_are_not(tmp_path):
    names = ["code-pin", "split-pin", "manifest-pin", "image", "linked", "broken", "internal"]
    for name in names:
        put(tmp_path, layout.PREFIX + f"2026-08-01_{name}/report.md")
    put(tmp_path, "tools/consumer.py", b'a = "2026-08-01_code-pin"\nb = "2026-08-01_" + "split-pin"\n')
    put(tmp_path, "docs/manifest.json", b'{"path": "output/insights/2026-08-01_manifest-pin/report.md"}')
    put(tmp_path, "docs/index.md", b"[read](../output/insights/2026-08-01_linked/report.md)\n")
    put(tmp_path, layout.PREFIX + "picture.md", b"![plot](2026-08-01_image/report.md)\n")
    put(tmp_path, layout.PREFIX + "2026-08-01_broken/report.md", b"[absent](../../absent.md)\n")
    put(tmp_path, layout.PREFIX + "2026-08-01_internal/report.md", b"[local](child.md)\n")
    put(tmp_path, layout.PREFIX + "2026-08-01_internal/child.md")
    plan = layout.build_plan(tmp_path, seal(tmp_path))
    assert set(plan["moves"]) == {"2026-08-01_broken", "2026-08-01_internal"}


def test_raw_pages_cover_all_git_leaves_including_partial_page(tmp_path):
    expected = set()
    for group, count in (("mitigation", 1422), ("split-warning", 1424)):
        for number in range(count):
            rel = layout.PREFIX + layout.RAW_TOP + f"/{group}/raw/{number:04}.json"
            put(tmp_path, rel, b"{}\n")
            expected.add(rel)
    plan = layout.build_plan(tmp_path, seal(tmp_path))
    assert set(plan["files"]) == expected
    layout.apply_plan(tmp_path, plan)
    index_path = tmp_path / layout.PREFIX / "README.md"
    reachable = {layout.local_target(layout.PREFIX + "README.md", p)
                 for p in layout.link_targets(index_path.read_text())}
    pages = sorted((tmp_path / layout.GUIDE).glob("raw-*.md"))
    assert len(pages) == 6
    seen = []
    sizes = []
    for page in pages:
        rel = str(page.relative_to(tmp_path))
        assert rel in reachable
        links = list(layout.link_targets(page.read_text()))
        sizes.append(len(links))
        assert 0 < len(links) <= 500
        for link in links:
            target = layout.local_target(rel, unquote(link))
            assert (tmp_path / target).is_file()
            seen.append(target)
    assert sorted(sizes) == [422, 424, 500, 500, 500, 500]
    assert len(seen) == len(set(seen)) == 2846
    assert set(seen) == expected


def test_navigation_keeps_hold_details_in_plan_only(tmp_path):
    top = "2026-08-01_notes"
    put(tmp_path, layout.PREFIX + top + "/report.md")
    consumer = "tools/private_implementation_consumer.py"
    put(tmp_path, consumer, (f'path = "{top}"\n' * 100).encode())
    plan = layout.build_plan(tmp_path, seal(tmp_path))
    assert len(plan["holds"][top]) == 100
    assert all(consumer in reason for reason in plan["holds"][top])
    page = layout.navigation(plan)[layout.GUIDE + "/2026-08-01.md"]
    assert "保留: 固定参照を保持" in page
    assert consumer not in page
    assert len(page.splitlines()) == 3


def test_internal_split_pin_keeps_original_directory(tmp_path):
    top = "2026-08-01_notes"
    put(tmp_path, layout.PREFIX + top + "/manifest.json",
        b'{"date": "2026-08-01", "topic": "notes"}\n')
    plan = layout.build_plan(tmp_path, seal(tmp_path))
    assert not plan["moves"]
    assert any("machine/pin reference" in reason for reason in plan["holds"][top])


def test_cli_output_plan_apply_verify_roundtrip(tmp_path, monkeypatch, capsys):
    old = layout.PREFIX + "2026-08-01_notes/report.md"
    put(tmp_path, old)
    # Only the baseline identifier varies; all Git/filesystem operations are real.
    monkeypatch.setattr(layout, "BASE", seal(tmp_path))
    reports = [tmp_path / name for name in ("plan.json", "applied.json", "verified.json")]
    for index, report in enumerate(reports):
        operation = [] if index == 0 else ["--apply" if index == 1 else "--verify", str(reports[0])]
        monkeypatch.setattr(sys, "argv", ["insights_date_layout.py", "--repo", str(tmp_path),
                                         *operation, "--output", str(report)])
        assert layout.main() == 0
        plan = json.loads(report.read_text())
        assert json.loads(capsys.readouterr().out) == plan["summary"]
        assert plan == json.loads(reports[0].read_text())
        assert (tmp_path / old).exists() == (index == 0)
    assert (tmp_path / layout.PREFIX / "2026-08-01/notes/report.md").read_bytes() == b"research\n"


@pytest.mark.parametrize("operation", ["plan", "apply", "verify"])
@pytest.mark.parametrize("destination", ["existing", "input", "symlink"])
def test_cli_output_collision_refuses_before_mutation(tmp_path, monkeypatch, operation, destination):
    old = layout.PREFIX + "2026-08-01_notes/report.md"
    source = put(tmp_path, old)
    base = seal(tmp_path)
    monkeypatch.setattr(layout, "BASE", base)
    plan = layout.build_plan(tmp_path, base)
    reviewed = tmp_path / "plan.json"
    reviewed.write_text(json.dumps(plan))
    output = tmp_path / "existing.json"
    output.write_bytes(b"keep existing bytes\n")
    if destination == "input":
        output = reviewed
    elif destination == "symlink":
        output = tmp_path / "alias.json"
        output.symlink_to(reviewed)
    before = output.read_bytes()
    args = [] if operation == "plan" else ["--" + operation, str(reviewed)]
    monkeypatch.setattr(sys, "argv", ["insights_date_layout.py", "--repo", str(tmp_path),
                                     *args, "--output", str(output)])
    with pytest.raises(SystemExit) as exc:
        layout.main()
    assert exc.value.code == 1
    assert output.read_bytes() == before
    assert source.read_bytes() == b"research\n"
    assert not (tmp_path / layout.PREFIX / "2026-08-01").exists()


@pytest.mark.parametrize("operation", ["plan", "apply", "verify"])
def test_cli_output_cannot_write_into_evidence(tmp_path, monkeypatch, operation):
    source = put(tmp_path, layout.PREFIX + "2026-08-01_notes/report.md")
    base = seal(tmp_path)
    monkeypatch.setattr(layout, "BASE", base)
    reviewed = tmp_path / "plan.json"
    reviewed.write_text(json.dumps(layout.build_plan(tmp_path, base)))
    output = source.parent / "report.json"
    args = [] if operation == "plan" else ["--" + operation, str(reviewed)]
    monkeypatch.setattr(sys, "argv", ["insights_date_layout.py", "--repo", str(tmp_path),
                                     *args, "--output", str(output)])
    with pytest.raises(SystemExit) as exc:
        layout.main()
    assert exc.value.code == 1
    assert not output.exists()
    assert source.read_bytes() == b"research\n"


def test_cli_failed_apply_removes_only_new_output(tmp_path, monkeypatch):
    source = put(tmp_path, layout.PREFIX + "2026-08-01_notes/report.md")
    base = seal(tmp_path)
    monkeypatch.setattr(layout, "BASE", base)
    reviewed = tmp_path / "plan.json"
    reviewed.write_text(json.dumps(layout.build_plan(tmp_path, base)))
    before = reviewed.read_bytes()
    source.write_bytes(b"changed since review\n")
    output = tmp_path / "failed.json"
    monkeypatch.setattr(sys, "argv", ["insights_date_layout.py", "--repo", str(tmp_path),
                                     "--apply", str(reviewed), "--output", str(output)])
    with pytest.raises(SystemExit) as exc:
        layout.main()
    assert exc.value.code == 1
    assert not output.exists()
    assert reviewed.read_bytes() == before
    assert source.read_bytes() == b"changed since review\n"


@pytest.mark.parametrize("opening", ["[formula](<", "[formula]: <"])
def test_unclosed_angle_destination_does_not_consume_later_formula(opening):
    text = opening + "unfinished\n" + "mathematical prose " * 400 + " >\n[ok](child.md)"
    assert list(layout.link_targets(text)) == ["child.md"]


def test_impossible_link_candidates_do_not_abort_plan(tmp_path):
    top = "2026-08-01_notes"
    report = ("[formula](<unfinished\n" + "prose " * 1000 + " >\n"
              + "[long](<" + "prose " * 1000 + ">)\n"
              + "[bare](" + "x" * 5000 + ")\n"
              + "[bad-url](http://[invalid)\n[nul](bad%00name)\n"
              + "[ok](child.md)\n")
    put(tmp_path, layout.PREFIX + top + "/report.md", report.encode())
    put(tmp_path, layout.PREFIX + top + "/child.md")
    plan = layout.build_plan(tmp_path, seal(tmp_path))
    assert plan["moves"] == {top: "2026-08-01/notes"}
    layout.apply_plan(tmp_path, plan)
    assert (tmp_path / layout.PREFIX / "2026-08-01/notes/report.md").read_bytes() == report.encode()
    layout.verify(tmp_path, plan["files"], plan["moves"])


@pytest.mark.parametrize("markup", [
    '[read](<%s>)', '![image](%s)', '[ref]: <%s>', '<a href="%s">read</a>',
])
def test_valid_relative_links_keep_internal_move_and_hold_outgoing(tmp_path, markup):
    internal = "2026-08-01_internal"
    outgoing = "2026-08-01_outgoing"
    put(tmp_path, layout.PREFIX + internal + "/report.md", (markup % "child.md").encode())
    put(tmp_path, layout.PREFIX + internal + "/child.md")
    put(tmp_path, layout.PREFIX + outgoing + "/report.md",
        (markup % "../../../docs/target.md").encode())
    put(tmp_path, "docs/target.md")
    plan = layout.build_plan(tmp_path, seal(tmp_path))
    assert plan["moves"] == {internal: "2026-08-01/internal"}
    assert any("existing link would break" in reason for reason in plan["holds"][outgoing])
    layout.apply_plan(tmp_path, plan)
    source = layout.PREFIX + "2026-08-01/internal/report.md"
    target, = layout.link_targets((tmp_path / source).read_text())
    assert (tmp_path / layout.local_target(source, target)).is_file()
    layout.verify(tmp_path, plan["files"], plan["moves"])


@pytest.mark.parametrize("failure", ["read", "target-stat"])
def test_reference_permission_failure_still_aborts_plan(tmp_path, failure):
    put(tmp_path, layout.PREFIX + "2026-08-01_notes/report.md")
    consumer = put(tmp_path, "docs/index.md", b"[target](../private/target.txt)\n")
    base = seal(tmp_path)
    # Untracked, outside insights: reached only by the link existence guard.
    target = put(tmp_path, "private/target.txt")
    denied = consumer if failure == "read" else target.parent
    mode = denied.stat().st_mode
    denied.chmod(0)
    try:
        with pytest.raises(ValueError, match="reference scan failed") as exc:
            layout.build_plan(tmp_path, base)
        assert isinstance(exc.value.__cause__, PermissionError)
    finally:
        denied.chmod(mode)


def test_pin_names_matches_legacy_extraction():
    tops = ["2026-08-01_notes", "2026-08-01_notes.md",
            "2026-08-02_notes.json.gz", "2026-08-03_notes.md.extra",
            "2026-08-04_caf\u00e9", "2026-08-05_\u8cc7\u6599",
            "2026-08-06_.hidden", "2026-08-07_+notes",
            "2026-08-08_notes.+notes", "2026-08-09_a b",
            "2026-08-10_a.", "2026-08-11_a..b", "plain"]
    aliases = set(tops) | {m.group(2) for top in tops
                           if (m := layout.DATED.fullmatch(top))}
    legacy = re.compile(r"(?<![\w-])(?:" + "|".join(
        map(re.escape, sorted(aliases, key=len, reverse=True))) + r")(?![\w-])")
    matcher = layout.PinNames(aliases)
    # Exercise suffixes, Unicode word boundaries, combining marks, repeated
    # occurrences and overlapping names; compare order as well as the pin set.
    edges = ["", " ", "/", ".", "-", "_", "x", "\u00e9", "\u8cc7", "\u0301", "+"]
    texts = [left + name + right for name in sorted(aliases)
             for left in edges for right in edges]
    texts += ["notes.md.extra notes.md notes.json.gz notes notes",
              "notes.+notes +notes .hidden a..b a. a b",
              "notes.mdx notes.md-extra notes.json.gz.more",
              '"2026-08-01_" + "notes"', "no candidate here"]
    for text in texts:
        expected = [hit.group() for hit in legacy.finditer(text)]
        actual = list(matcher.find(text))
        assert actual == expected, ascii(text)
        assert set(actual) == set(expected), ascii(text)
    assert list(layout.PinNames({}).find("notes")) == []


@pytest.mark.parametrize("reference,pinned", [
    ('"2026-08-01_notes"', True),
    ('"2026-08-01_" + "notes"', True),
    ('"2026-08-01", "notes.md"', True),
    ('"2026-08-01", "notes.json.gz"', True),
    ('"2026-08-01", "notes-extra"', False),
    ('"2026-08-01", "xnotes"', False),
    ('"2026-08-01", "notes_"', False),
    ('"2026-08-01", "\u8cc7notes"', False),
    ('"2026-08-01", "notes\u00e9"', False),
    ('"2026-08-01", "notes\u0301"', True),
])
def test_pin_scan_literal_split_and_word_boundaries(tmp_path, reference, pinned):
    top = "2026-08-01_notes"
    put(tmp_path, layout.PREFIX + top + "/report.md")
    put(tmp_path, "tools/consumer.py", reference.encode())
    plan = layout.build_plan(tmp_path, seal(tmp_path))
    assert (top in plan["holds"]) == pinned
    assert plan["moves"] == ({} if pinned else {top: "2026-08-01/notes"})


@pytest.mark.parametrize("reference,pinned", [
    ('{"topic": "notes"}', False),
    ('{"date": "2026-08-01", "topic": "notes"}', True),
    ('{"date": "2026-08-01", "topic": "xnotes"}', False),
    ('{"path": "2026-08-01_notes"}', True),
])
def test_internal_split_scan_keeps_date_requirement(tmp_path, reference, pinned):
    top = "2026-08-01_notes"
    put(tmp_path, layout.PREFIX + top + "/manifest.json", reference.encode())
    plan = layout.build_plan(tmp_path, seal(tmp_path))
    assert (top in plan["holds"]) == pinned
    assert plan["moves"] == ({} if pinned else {top: "2026-08-01/notes"})


def test_pin_scan_ordinary_markdown_code_span_still_moves(tmp_path):
    top = "2026-08-01_notes"
    put(tmp_path, layout.PREFIX + top + "/report.md")
    put(tmp_path, "docs/history.md", (f"Previous report: `{layout.PREFIX}{top}`\n").encode())
    plan = layout.build_plan(tmp_path, seal(tmp_path))
    assert plan["moves"] == {top: "2026-08-01/notes"}


HISTORICAL_LOG_PATHS = (
    "output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measure/phase-20260904-223623-rep1.jsonl",
    "output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measure/phase-20260904-223914-rep2.jsonl",
)


@pytest.mark.parametrize("active", [
    None,
    "docs/active-manifest.json",
    "output/elsewhere/phase-20260904-223623-rep1.jsonl",
    "output/elsewhere/phase-20260904-223914-rep2.jsonl",
    "output/insights/2026-09-04_t2298-t2273-shard0-critical-path/measure/other.jsonl",
])
def test_historical_copytree_logs_only_exempt_exact_paths(tmp_path, active):
    top = "2026-08-01_notes"
    old = layout.PREFIX + top + "/report.md"
    put(tmp_path, old)
    payload = (json.dumps({"ev": "call", "name": "shutil.copytree",
                           "arg": f"<DirEntry '{top}'>", "dur": 0.1}) + "\n").encode()
    for rel in HISTORICAL_LOG_PATHS:
        put(tmp_path, rel, payload)
    if active:
        put(tmp_path, active, json.dumps({"path": old}).encode())
    base = seal(tmp_path)
    plan = layout.build_plan(tmp_path, base)
    assert plan["moves"] == ({} if active else {top: "2026-08-01/notes"})
    log_top = "2026-09-04_t2298-t2273-shard0-critical-path"
    assert "historical observation logs retained" in plan["holds"][log_top]
    assert set(HISTORICAL_LOG_PATHS) <= plan["files"].keys()
    if active:
        assert any(f"machine/pin reference: {active}:" in reason
                   for reason in plan["holds"][top])
    layout.apply_plan(tmp_path, plan)
    for rel in HISTORICAL_LOG_PATHS:
        assert (tmp_path / rel).read_bytes() == payload
        assert (tmp_path / rel).stat().st_mode & 0o777 == 0o644
    assert (tmp_path / layout.relocated(old, plan["moves"])).read_bytes() == b"research\n"
    layout.verify(tmp_path, plan["files"], plan["moves"])


@pytest.mark.parametrize("rel", HISTORICAL_LOG_PATHS)
@pytest.mark.parametrize("change", ["bytes", "mode", "missing"])
def test_historical_copytree_logs_remain_in_baseline_validation(tmp_path, rel, change):
    put(tmp_path, layout.PREFIX + "2026-08-01_notes/report.md")
    for log in HISTORICAL_LOG_PATHS:
        put(tmp_path, log, b'{"ev":"call","name":"shutil.copytree"}\n')
    base = seal(tmp_path)
    plan = layout.build_plan(tmp_path, base)
    path = tmp_path / rel
    if change == "bytes":
        path.write_bytes(b"changed historical log\n")
    elif change == "mode":
        path.chmod(0o755)
    else:
        path.unlink()
    with pytest.raises((ValueError, FileNotFoundError)):
        layout.apply_plan(tmp_path, plan)
    assert (tmp_path / layout.PREFIX / "2026-08-01_notes/report.md").exists()
    assert not (tmp_path / layout.PREFIX / "README.md").exists()
