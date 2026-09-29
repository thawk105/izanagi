#!/usr/bin/env python3
"""Closed, fail-closed classification and test selection for scoped acceptance."""

from __future__ import annotations

import argparse
import ast
import hashlib
import json
import re
import subprocess
from pathlib import Path

RULES_VERSION = "scoped-acceptance-rules/v1"
MAX_BLOB = 2 * 1024 * 1024
GATES = [["python3", "tools/check_docs.py"],
         ["python3", "tools/spool_fold.py", "--dry-run"]]
FIXED_FILES = (
    "test_check_docs.py", "test_spool_fold.py", "test_check_ai_provenance.py",
    "test_real_repo_serialization.py", "test_acceptance_schedule_order.py",
    "test_official_perf_closure.py", "test_p3_exploration_namespace.py",
    "test_p3_b4_wiring_probe.py",
)
FIXED_NODES = ("test_campaign.py::test_certified_writer_authorization_caller_inventory_is_closed",)
GENERIC = {"docs", "output", "insights", "spool", "worklog", "decisions",
           "failures", "archive", "README.md", "index.md"}
DATE = re.compile(r"\d{4}-\d{2}-\d{2}\Z")
SHA = re.compile(rb"[0-9a-f]{40}(?:[0-9a-f]{24})?\Z")


def _git(repo: Path, *args: str) -> bytes:
    result = subprocess.run(["git", "-C", str(repo), *args], capture_output=True)
    if result.returncode:
        raise ValueError(f"git {args[0]} failed: {result.stderr[:200]!r}")
    return result.stdout


def _digest(value: object) -> str:
    return hashlib.sha256(json.dumps(value, sort_keys=True, ensure_ascii=False,
                                     separators=(",", ":")).encode("utf-8")).hexdigest()


def _tree(repo: Path, revision: str) -> dict[str, tuple[str, str, str]]:
    records = _git(repo, "ls-tree", "-r", "-z", "--full-tree", revision).split(b"\0")
    tree = {}
    for record in records:
        if not record:
            continue
        try:
            header, path = record.split(b"\t", 1)
            mode, kind, oid = (part.decode("ascii") for part in header.split(b" "))
            name = path.decode("utf-8", "strict")
            if not SHA.fullmatch(oid.encode()) or name in tree:
                raise ValueError("bad tree entry")
        except (UnicodeError, ValueError) as exc:
            raise ValueError("bad tree entry") from exc
        tree[name] = mode, kind, oid
    return tree


def changed_entries(repo: Path, tested_main: str, tested_tip: str) -> list[dict]:
    raw = _git(repo, "diff-tree", "-r", "-z", "--raw", "--no-renames",
               "--no-ext-diff", "--no-textconv", tested_main, tested_tip)
    records = raw.split(b"\0")
    entries = []
    i = 0
    while i < len(records) and records[i]:
        try:
            fields = records[i][1:].split(b" ")
            if not records[i].startswith(b":") or len(fields) != 5:
                raise ValueError("bad raw metadata")
            old_mode, new_mode, old_oid, new_oid, status = fields
            if not all(SHA.fullmatch(x) for x in (old_oid, new_oid)):
                raise ValueError("bad object id")
            path_bytes = records[i + 1]
            path = path_bytes.decode("utf-8", "strict")
            entries.append({"status": status.decode("ascii"),
                            "old_mode": old_mode.decode("ascii"),
                            "mode": new_mode.decode("ascii"),
                            "old_blob": old_oid.decode("ascii"),
                            "blob": new_oid.decode("ascii"), "path": path})
            i += 2
        except (IndexError, UnicodeError, ValueError) as exc:
            raise ValueError("bad raw diff") from exc
    if i != len(records) - 1 or not entries:
        raise ValueError("empty or malformed raw diff")
    return entries


def _allowed_path(path: str, status: str) -> bool:
    if (path.startswith(("docs/dev-wave/", "docs/archive/", "docs/handoff/"))
            or path in {"docs/worklog.md", "docs/decisions.md", "docs/failures.md",
                        "docs/skill-self-improvement.md", "docs/ai-provenance.md"}
            or any(term in path.rsplit("/", 1)[-1].lower()
                   for term in ("preregistration", "erratum", "freeze"))):
        return False
    parts = path.split("/")
    if len(parts) == 4 and parts[:2] == ["docs", "spool"]:
        return (status == "A" and parts[2] in {"worklog", "decisions", "failures"}
                and parts[3].endswith(".md") and parts[3] != "README.md")
    if path.startswith("docs/spool/"):
        return False
    if path.startswith("output/insights/") and len(parts) >= 3:
        return path.rsplit(".", 1)[-1] in {"md", "txt", "csv", "tsv", "json", "jsonl"}
    return path.startswith("docs/") and len(parts) >= 2 and path.endswith(".md")


def _keys(path: str) -> set[bytes]:
    parts = path.split("/")
    keys = {path}
    if parts[-1] not in {"README.md", "index.md"} and not DATE.fullmatch(parts[-1]):
        keys.add(parts[-1])
    if path.startswith("docs/spool/"):
        return {key.encode("utf-8") for key in keys}
    minimum_depth = 4 if path.startswith("output/insights/") else 2
    for depth in range(minimum_depth, len(parts)):
        keys.add("/".join(parts[:depth]))
        name = parts[depth - 1]
        if name not in GENERIC and not DATE.fullmatch(name):
            keys.add(name)
    return {key.encode("utf-8") for key in keys}


def _references(data: bytes, keys: set[bytes]) -> bool:
    return any(key in data for key in keys)


def _blob(repo: Path, oid: str) -> bytes:
    return _git(repo, "cat-file", "blob", oid)


def _blobs(repo: Path, oids: list[str]) -> dict[str, bytes]:
    unique = list(dict.fromkeys(oids))
    if not unique:
        return {}
    result = subprocess.run(
        ["git", "-C", str(repo), "cat-file", "--batch"],
        input=("\n".join(unique) + "\n").encode("ascii"), capture_output=True,
    )
    if result.returncode:
        raise ValueError("git cat-file --batch failed")
    output = result.stdout
    cursor = 0
    blobs = {}
    for oid in unique:
        end = output.find(b"\n", cursor)
        if end < 0:
            raise ValueError("truncated batch header")
        fields = output[cursor:end].split(b" ")
        if len(fields) != 3 or fields[0] != oid.encode() or fields[1] != b"blob":
            raise ValueError("unexpected batch object")
        size = int(fields[2])
        cursor = end + 1
        if size < 0 or cursor + size >= len(output) or output[cursor + size] != 10:
            raise ValueError("truncated batch body")
        blobs[oid] = output[cursor:cursor + size]
        cursor += size + 1
    if cursor != len(output):
        raise ValueError("extra batch output")
    return blobs


def classify(repo: Path, tested_main: str, tested_tip: str) -> dict:
    try:
        entries = changed_entries(repo, tested_main, tested_tip)
        tree = _tree(repo, tested_tip)
    except ValueError as exc:
        return {"rules_version": RULES_VERSION, "eligible": False,
                "reasons": [str(exc)], "entries": [], "entries_digest": _digest([])}
    reasons = []
    candidates = [(candidate, oid) for candidate, (_, kind, oid) in tree.items()
                  if kind == "blob" and not candidate.startswith(("docs/", "output/", "external/", "orchestrator/tests/"))
                  and not candidate.endswith(".md")
                  and not (candidate.rsplit("/", 1)[-1].startswith("test_") and candidate.endswith(".py"))
                  and candidate not in {"tools/check_docs.py", "tools/spool_fold.py"}]
    try:
        production_blobs = _blobs(repo, [oid for _, oid in candidates])
    except ValueError as exc:
        return {"rules_version": RULES_VERSION, "eligible": False,
                "reasons": [str(exc)], "entries": [], "entries_digest": _digest([])}
    for entry in entries:
        path = entry["path"]
        parts = path.split("/")
        if (not path or any(x in {"", ".", ".."} for x in parts)
                or any(x.startswith("-") for x in parts) or "\\" in path
                or any(ord(ch) < 32 or ord(ch) == 127 for ch in path)):
            reasons.append(f"unsafe-path:{path}")
            continue
        if (entry["status"] not in {"A", "M"} or entry["mode"] != "100644"
                or (entry["status"] == "M" and entry["old_mode"] != "100644")):
            reasons.append(f"metadata:{path}")
            continue
        if not _allowed_path(path, entry["status"]):
            reasons.append(f"path:{path}")
            continue
        if tree.get(path) != (entry["mode"], "blob", entry["blob"]):
            reasons.append(f"object-type:{path}")
            continue
        try:
            size = len(_blob(repo, entry["blob"]))
        except ValueError:
            reasons.append(f"unreadable-blob:{path}")
            continue
        if size > MAX_BLOB:
            reasons.append(f"size:{path}")
            continue
        keys = _keys(path)
        for candidate, oid in candidates:
            body = production_blobs[oid]
            if _references(body, keys):
                reasons.append(f"production-reference:{path}:{candidate}")
                break
    canonical_entries = [
        {key: entry[key] for key in ("status", "mode", "blob", "path")}
        for entry in entries
    ]
    return {"rules_version": RULES_VERSION, "eligible": not reasons,
            "reasons": sorted(set(reasons)), "entries": canonical_entries,
            "entries_digest": _digest(canonical_entries)}


def _inventory(source: bytes) -> list[str]:
    module = ast.parse(source.decode("utf-8"))
    for node in module.body:
        if (isinstance(node, ast.Assign) and len(node.targets) == 1
                and isinstance(node.targets[0], ast.Name)
                and node.targets[0].id == "_REAL_REPO_NODE_INVENTORY"
                and isinstance(node.value, ast.Call)
                and isinstance(node.value.func, ast.Name)
                and node.value.func.id == "frozenset" and len(node.value.args) == 1):
            value = ast.literal_eval(node.value.args[0])
            if not isinstance(value, set) or not value or len(value) != len(node.value.args[0].elts) or not all(isinstance(x, str) and x for x in value):
                raise ValueError("invalid inventory")
            return sorted(value)
    raise ValueError("missing inventory")


def select_tests(repo: Path, tested_tip: str, classification: dict) -> dict:
    tree = _tree(repo, tested_tip)
    tests = {path: oid for path, (_, kind, oid) in tree.items()
             if kind == "blob" and path.endswith(".py")
             and path.rsplit("/", 1)[-1].startswith("test_")}
    missing = [name for name in FIXED_FILES if "orchestrator/tests/" + name not in tests]
    test_blobs = _blobs(repo, list(tests.values()))
    missing += [node for node in FIXED_NODES if "orchestrator/tests/" + node.split("::")[0] not in tests]
    conftest = tree.get("orchestrator/tests/conftest.py")
    try:
        if conftest is None or conftest[1] != "blob":
            raise ValueError("missing conftest")
        inventory = _inventory(_blob(repo, conftest[2]))
        if any("orchestrator/tests/" + node.split("::")[0] not in tests for node in inventory):
            raise ValueError("inventory file missing")
    except (ValueError, UnicodeError, SyntaxError) as exc:
        inventory = []
        missing.append(str(exc))
    nodes = sorted(set(inventory) | set(FIXED_NODES))
    files = {"orchestrator/tests/" + name for name in FIXED_FILES}
    keys = set().union(*(_keys(entry["path"]) for entry in classification["entries"]))
    insight = any(entry["path"].startswith("output/insights/") for entry in classification["entries"])
    for path, oid in tests.items():
        body = test_blobs[oid]
        if _references(body, keys) or insight and (b'"insights"' in body or b"'insights'" in body):
            files.add(path)
    files = sorted(files)
    return {"nodes": nodes, "files": files, "selection_digest": _digest({"nodes": nodes, "files": files}),
            "direct_gates": GATES, "eligible": not missing, "reasons": sorted(missing)}


def plan(repo: Path, tested_main: str, tested_tip: str) -> dict:
    classification = classify(repo, tested_main, tested_tip)
    try:
        selection = select_tests(repo, tested_tip, classification)
    except (ValueError, OSError) as exc:
        selection = {"nodes": [], "files": [], "selection_digest": _digest({"nodes": [], "files": []}),
                     "direct_gates": GATES, "eligible": False, "reasons": [str(exc)]}
    classification["eligible"] = classification["eligible"] and selection["eligible"]
    classification["reasons"] = sorted(set(classification["reasons"] + selection["reasons"]))
    return {"classification": classification, "selection": selection}


def main() -> int:
    parser = argparse.ArgumentParser()
    parser.add_argument("command", choices=["plan"])
    parser.add_argument("--repo", type=Path, required=True)
    parser.add_argument("--tested-main", required=True)
    parser.add_argument("--tested-tip", required=True)
    args = parser.parse_args()
    print(json.dumps(plan(args.repo.resolve(), args.tested_main, args.tested_tip),
                     sort_keys=True, ensure_ascii=False, separators=(",", ":")))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
