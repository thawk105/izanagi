"""Synthetic tree checks for the closed scoped acceptance rules."""

import importlib.util
import subprocess
from pathlib import Path

import pytest


SOURCE = Path(__file__).resolve().parents[2] / "tools/scoped_acceptance.py"
SPEC = importlib.util.spec_from_file_location("scoped_acceptance_under_test", SOURCE)
SCOPED = importlib.util.module_from_spec(SPEC)
SPEC.loader.exec_module(SCOPED)


def git(repo, *args):
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    assert result.returncode == 0, result.stderr
    return result.stdout.decode().strip()


def put(repo, name, content):
    path = repo / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(content if isinstance(content, bytes) else content.encode())


@pytest.fixture
def tree(tmp_path):
    repo = tmp_path / "tree"
    repo.mkdir()
    git(repo, "init", "-q")
    git(repo, "config", "user.name", "Test")
    git(repo, "config", "user.email", "test@example.invalid")
    put(repo, "orchestrator/tests/conftest.py",
        '_REAL_REPO_NODE_INVENTORY = frozenset({"test_real_repo_serialization.py::test_real"})\n')
    for name in SCOPED.FIXED_FILES:
        put(repo, "orchestrator/tests/" + name, "def test_present(): pass\n")
    put(repo, "orchestrator/tests/test_campaign.py",
        "def test_certified_writer_authorization_caller_inventory_is_closed(): pass\n")
    put(repo, "tools/check_docs.py", "pass\n")
    put(repo, "tools/spool_fold.py", "pass\n")
    put(repo, "tools/x.py", "pass\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "base")
    return repo, git(repo, "rev-parse", "HEAD")


def result(tree, changes, *, delete=()):
    repo, base = tree
    for name, body in changes.items():
        put(repo, name, body)
    for name in delete:
        (repo / name).unlink()
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "change")
    return SCOPED.plan(repo, base, git(repo, "rev-parse", "HEAD"))


@pytest.mark.parametrize("path,body", [
    ("docs/spool/worklog/entry.md", "# log\n"),
    ("output/insights/2026-09-29/result.jsonl", '{}\n'),
    ("docs/notes/story.md", "# story\n"),
])
def test_allowed_tree_changes(tree, path, body):
    got = result(tree, {path: body})
    assert got["classification"]["eligible"] is True
    assert got["selection"]["nodes"]
    assert got["selection"]["direct_gates"] == SCOPED.GATES


@pytest.mark.parametrize("path", ["docs/notes/story.md", "output/insights/old.md"])
def test_existing_knowledge_file_change_allowed(tree, path):
    repo, _ = tree
    put(repo, path, "# first\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "first")
    main = git(repo, "rev-parse", "HEAD")
    put(repo, path, "# second\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "second")
    got = SCOPED.plan(repo, main, git(repo, "rev-parse", "HEAD"))
    assert got["classification"]["eligible"] is True
    entry, = got["classification"]["entries"]
    assert set(entry) == {"status", "mode", "blob", "path"}
    assert (entry["status"], entry["mode"], entry["path"]) == ("M", "100644", path)


@pytest.mark.parametrize("path", [
    "docs/dev-wave/protocol.md", "docs/worklog.md", "docs/archive/old.md",
    "docs/my-preregistration.md", "docs/ai-provenance.md",
    "docs/spool/README.md", "tools/new.py",
])
def test_closed_path_exclusions(tree, path):
    assert result(tree, {path: "text"})["classification"]["eligible"] is False


@pytest.mark.parametrize("literal", [
    '"docs/notes/story.md"', '"docs/notes"', '"story.md"', '"notes"',
])
def test_production_literal_reference_rejects(tree, literal):
    repo, _ = tree
    put(repo, "tools/x.py", "PATH = " + literal + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "reader")
    main = git(repo, "rev-parse", "HEAD")
    put(repo, "docs/notes/story.md", "# story\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "doc")
    got = SCOPED.plan(repo, main, git(repo, "rev-parse", "HEAD"))
    assert any(reason.startswith("production-reference:") for reason in got["classification"]["reasons"])


def test_selection_literals_and_digest(tree):
    repo, _ = tree
    put(repo, "orchestrator/tests/test_consumer.py",
        'PATH = "docs/notes"\nOTHER = "story.md"\nINSIGHT = "insights"\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "consumer")
    main = git(repo, "rev-parse", "HEAD")
    put(repo, "docs/notes/story.md", "# story\n")
    put(repo, "output/insights/2026-09-29/findings.md", "# findings\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "docs")
    tip = git(repo, "rev-parse", "HEAD")
    first = SCOPED.plan(repo, main, tip)
    assert "orchestrator/tests/test_consumer.py" in first["selection"]["files"]
    assert first == SCOPED.plan(repo, main, tip)


@pytest.mark.parametrize("literal", ['"docs/notes"', '"story.md"', '"notes"'])
def test_each_selection_key_selects_consumer(tree, literal):
    repo, _ = tree
    put(repo, "orchestrator/tests/test_consumer.py", "PATH = " + literal + "\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "consumer")
    main = git(repo, "rev-parse", "HEAD")
    put(repo, "docs/notes/story.md", "# story\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "doc")
    got = SCOPED.plan(repo, main, git(repo, "rev-parse", "HEAD"))
    assert "orchestrator/tests/test_consumer.py" in got["selection"]["files"]


def test_insights_literal_selects_test(tree):
    repo, _ = tree
    put(repo, "orchestrator/tests/test_consumer.py", 'KIND = "insights"\n')
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "consumer")
    main = git(repo, "rev-parse", "HEAD")
    put(repo, "output/insights/report.md", "# report\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "insight")
    got = SCOPED.plan(repo, main, git(repo, "rev-parse", "HEAD"))
    assert "orchestrator/tests/test_consumer.py" in got["selection"]["files"]


def test_missing_fixed_file_fails_closed(tree):
    got = result(tree, {"docs/story.md": "# story\n"},
                 delete=("orchestrator/tests/test_spool_fold.py",))
    assert got["classification"]["eligible"] is False
    assert "test_spool_fold.py" in got["classification"]["reasons"]


def test_raw_metadata_rejects(tree):
    repo, base = tree
    put(repo, "docs/story.md", "# story\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "add")
    added = git(repo, "rev-parse", "HEAD")
    (repo / "docs/story.md").chmod(0o755)
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "mode")
    assert SCOPED.plan(repo, added, git(repo, "rev-parse", "HEAD"))["classification"]["eligible"] is False
    (repo / "docs/story.md").unlink()
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "delete")
    assert SCOPED.plan(repo, added, git(repo, "rev-parse", "HEAD"))["classification"]["eligible"] is False
    assert SCOPED.plan(repo, base, added)["classification"]["eligible"] is True


def test_rename_is_delete_plus_add_and_rejected(tree):
    repo, _ = tree
    put(repo, "docs/story.md", "# story\n")
    git(repo, "add", "-A")
    git(repo, "commit", "-qm", "add")
    main = git(repo, "rev-parse", "HEAD")
    git(repo, "mv", "docs/story.md", "docs/renamed.md")
    git(repo, "commit", "-qm", "rename")
    got = SCOPED.plan(repo, main, git(repo, "rev-parse", "HEAD"))
    assert got["classification"]["eligible"] is False
    assert any(reason.startswith("metadata:") for reason in got["classification"]["reasons"])


def test_oversize_blob_rejects(tree):
    got = result(tree, {"docs/story.md": b"x" * (SCOPED.MAX_BLOB + 1)})
    assert any(x.startswith("size:") for x in got["classification"]["reasons"])


def test_symlink_and_gitlink_reject(tree):
    repo, base = tree
    target = repo / "docs/link.md"
    target.parent.mkdir(exist_ok=True)
    target.symlink_to("story.md")
    git(repo, "add", "-A", "docs/link.md")
    git(repo, "commit", "-qm", "symlink")
    assert SCOPED.plan(repo, base, git(repo, "rev-parse", "HEAD"))["classification"]["eligible"] is False
    target.unlink()
    git(repo, "update-index", "--add", "--cacheinfo", f"160000,{base},docs/link.md")
    git(repo, "commit", "-qm", "gitlink")
    assert SCOPED.plan(repo, base, git(repo, "rev-parse", "HEAD"))["classification"]["eligible"] is False


def test_non_utf8_path_fails_closed(tree):
    repo, base = tree
    name = b"docs/bad-\xff.md"
    import os
    (repo / "docs").mkdir()
    with open(os.path.join(os.fsencode(repo), name), "wb") as stream:
        stream.write(b"# bad\n")
    git(repo, "add", "-A", "docs")
    git(repo, "commit", "-qm", "non utf8")
    assert SCOPED.plan(repo, base, git(repo, "rev-parse", "HEAD"))["classification"]["eligible"] is False


def test_inventory_literal_is_selected(tree):
    got = result(tree, {"docs/story.md": "# story\n"})
    assert "test_real_repo_serialization.py::test_real" in got["selection"]["nodes"]
    assert SCOPED.FIXED_NODES[0] in got["selection"]["nodes"]


def test_duplicate_inventory_fails_closed(tree):
    repo, _ = tree
    put(repo, "orchestrator/tests/conftest.py",
        '_REAL_REPO_NODE_INVENTORY = frozenset({"test_real_repo_serialization.py::test_real", "test_real_repo_serialization.py::test_real"})\n')
    got = result(tree, {"docs/story.md": "# story\n"})
    assert got["classification"]["eligible"] is False
