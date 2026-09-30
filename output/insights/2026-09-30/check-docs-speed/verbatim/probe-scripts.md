# probe scripts (逐語、Codex author)

repo 外の使い捨て probe の逐語写し。実行した版の置き場は `/work/SFC/tanab/tmp/check-docs-speed-2026-09-30/probe/`。
作成: probe 実装子 commit 09ef9a61ed7b2859dba24d31a2a23d2bb66ed4cd (branch worktree-dev-wave-check-docs-speed-probe)、equiv_real.py の故障注入だけ fix commit 665dd49245b4ac4aa999ee410827ca0d2a7e1011 で改訂 (r1 版は equiv_real-r1.py)。

## equiv_real.py

sha256: 070b24dfff9b87984d031595a620c39562ba41f09ccfb7871b9189e9a49f5e70

~~~~python
#!/usr/bin/env python3
"""Compare old/new check_docs on a clone and six injected corpus faults."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback


def absolute_file(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or not path.is_file():
        raise argparse.ArgumentTypeError(f"absolute existing file required: {value}")
    return path


def absolute_dir(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or not path.is_dir():
        raise argparse.ArgumentTypeError(f"absolute existing directory required: {value}")
    return path


def absolute_out(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("--out must be absolute")
    return path


def common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--src-repo", type=absolute_dir, required=True)
    parser.add_argument("--old-commit", required=True)
    parser.add_argument("--new-checker", type=absolute_file, required=True)
    parser.add_argument("--scratch", type=absolute_dir, required=True)
    parser.add_argument("--out", type=absolute_out, required=True)


def reserve_out(path: Path) -> None:
    with path.open("x", encoding="utf-8"):
        pass


def save_out(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def started() -> dict:
    return {"hostname": socket.gethostname(), "started_at": dt.datetime.now(dt.timezone.utc).isoformat(), "wall_seconds": None}


def git(*args: str, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], check=True, capture_output=capture)


def old_blob(src: Path, commit: str) -> bytes:
    return git("-C", str(src), "show", f"{commit}:tools/check_docs.py", capture=True).stdout


def clone(src: Path, commit: str, target: Path) -> None:
    git("clone", "--quiet", "--no-checkout", str(src), str(target))
    git("-C", str(target), "checkout", "--quiet", "--detach", commit)


def reset(tree: Path) -> None:
    git("-C", str(tree), "checkout", "--", ".")
    git("-C", str(tree), "clean", "-fdq")


def install(tree: Path, blob: bytes) -> None:
    target = tree / "tools/check_docs.py"
    fd, name = tempfile.mkstemp(prefix=".check_docs_probe_", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(blob)
        os.chmod(name, target.stat().st_mode & 0o777)
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def run_checker(tree: Path, args: list[str] | None = None) -> dict:
    stamp = started()
    start = time.perf_counter()
    proc = subprocess.run([sys.executable, "tools/check_docs.py", *(args or [])], cwd=tree, capture_output=True)
    stdout = proc.stdout
    return {
        "hostname": stamp["hostname"], "started_at": stamp["started_at"],
        "rc": proc.returncode,
        "stdout_hex": stdout.hex(), "stderr_hex": proc.stderr.hex(),
        "findings_hex": sorted({line.hex() for line in stdout.splitlines() if line.startswith(b"  - ")}),
        "wall_seconds": time.perf_counter() - start,
    }


def append_next_action(tree: Path, addition: bytes) -> None:
    path = tree / "docs/worklog.md"
    data = path.read_bytes()
    marker = b"### \xe6\xac\xa1\xe3\x81\xae\xe4\xb8\x80\xe6\x89\x8b"
    if marker not in data:
        raise ValueError("worklog has no next-action section")
    idx = data.rfind(marker)
    if b"\n## " in data[idx:]:
        raise ValueError("last next-action section is not in final entry")
    path.write_bytes(data.rstrip(b"\r\n") + b"\n" + addition + b"\n")


def archive_files(tree: Path) -> list[tuple[Path, list[re.Match[str]]]]:
    result = []
    mmdd = r"(?:0[1-9]|1[0-2])(?:0[1-9]|[12][0-9]|3[01])"
    number = r"[1-9][0-9]*"
    numbered_name = re.compile(
        rf"worklog-phase[0-9]+-{mmdd}-{number}(?:-(?:{mmdd}-)?{number})?\.md"
    )
    for path in sorted((tree / "docs/archive").glob("worklog-*.md")):
        if numbered_name.fullmatch(path.name) is None:
            continue
        text = path.read_text(encoding="utf-8")
        entries = list(re.finditer(r"^## (?P<date>\d{4}-\d{2}-\d{2}) \((?P<num>[1-9]\d*)\) — .*?$", text, re.M))
        if entries:
            result.append((path, entries))
    return result


def append_archive_next_action(path: Path, addition: str) -> None:
    text = path.read_text(encoding="utf-8")
    entries = list(re.finditer(r"^## \d{4}-\d{2}-\d{2} \([1-9]\d*\) — .*?$", text, re.M))
    for i, entry in enumerate(entries):
        entry_end = entries[i + 1].start() if i + 1 < len(entries) else len(text)
        body = text[entry.end():entry_end]
        section = re.search(r"^### 次の一手(?:[ \t][^\n]*)?$", body, re.M)
        if section is None:
            continue
        following = re.search(r"^#{2,3}[ \t]", body[section.end():], re.M)
        end = entry.end() + section.end() + following.start() if following else entry_end
        if re.search(r"^- \[T-[1-9][0-9]*\]", text[entry.end() + section.end():end], re.M) is None:
            continue
        path.write_text(text[:end].rstrip("\n") + "\n" + addition + "\n" + text[end:], encoding="utf-8")
        return
    raise ValueError(f"numbered archive has no ID entry next-action section: {path}")


def fault(tree: Path, index: int) -> str:
    if index == 0:
        return "unaltered"
    if index == 1:
        append_next_action(tree, b"- [T-9998] (999999)")
        return "dangling_carry"
    if index == 5:
        append_next_action(tree, b"<!--\n- [T-9996] (999997)\n-->\n```text\n- [T-9995] (999996)\n```\n- [T-9993] (999995)\nbefore <!-- inline --> after")
        return "visibility"
    if index == 6:
        append_next_action(tree, "- [T-9997] 変わらず (12 参照)".encode())
        return "malformed_carry"
    archives = archive_files(tree)
    if index == 2:
        if len(archives) < 2:
            raise ValueError("two numbered archives required")
        first = archives[0]
        other = next(((p, m) for p, m in archives[1:] if m[0].group("num") != first[1][0].group("num")), None)
        if other is None:
            raise ValueError("distinct archive entry numbers required")
        path, entries = other
        text = path.read_text(encoding="utf-8")
        match = entries[0]
        begin, end = match.span("num")
        path.write_text(text[:begin] + first[1][0].group("num") + text[end:], encoding="utf-8")
        return "duplicate_entry_number"
    if index == 3:
        if len(archives) < 2:
            raise ValueError("two numbered archives required")
        ordered = sorted(archives, key=lambda pair: (pair[1][0].group("date"), int(pair[1][0].group("num"))))
        left, right = ordered[0], ordered[1]
        path, entries = right
        text = path.read_text(encoding="utf-8")
        m = entries[0]
        replacement = left[1][-1].group("date") + " (" + left[1][-1].group("num") + ")"
        begin, end = m.start("date"), m.end("num") + 1
        path.write_text(text[:begin] + replacement + text[end:], encoding="utf-8")
        return "ambiguous_archive_order"
    if index == 4:
        candidates = sorted(archives, key=lambda pair: (pair[0].read_bytes().count(b"- [T-"), pair[0].stat().st_size), reverse=True)
        if len(candidates) < 2:
            raise ValueError("two numbered archives required")
        for (path, _), addition, ending in zip(candidates[:2], ("- [T-9998] (999999)", "- [T-9994] (999998)"), (b"\r\n", b"\r")):
            append_archive_next_action(path, addition)
            data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            path.write_bytes(data.replace(b"\n", ending))
        return "mixed_newlines"
    raise ValueError(index)


def execute(args: argparse.Namespace) -> dict:
    info = started()
    begin = time.perf_counter()
    old = old_blob(args.src_repo, args.old_commit)
    new = args.new_checker.read_bytes()
    results = []
    with tempfile.TemporaryDirectory(prefix="equiv_real_", dir=args.scratch) as place:
        tree = Path(place) / "tree"
        clone(args.src_repo, args.old_commit, tree)
        baseline = None
        for index in range(7):
            state_stamp = started()
            state_begin = time.perf_counter()
            reset(tree)
            label = fault(tree, index)
            install(tree, old)
            left = run_checker(tree)
            install(tree, new)
            right = run_checker(tree)
            if index == 0:
                baseline = left
            reached = None if index == 0 else (left["rc"], left["stdout_hex"]) != (baseline["rc"], baseline["stdout_hex"])
            results.append({"state": label, "hostname": state_stamp["hostname"],
                            "started_at": state_stamp["started_at"],
                            "wall_seconds": time.perf_counter() - state_begin,
                            "fault_reached": reached, "old": left, "new": right,
                            "bytes_equal": all(left[key] == right[key] for key in ("rc", "stdout_hex", "stderr_hex")),
                            "findings_equal": left["findings_hex"] == right["findings_hex"]})
    info["wall_seconds"] = time.perf_counter() - begin
    info.update({"states": results, "all_equal": all(row["bytes_equal"] for row in results)})
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    common(parser)
    args = parser.parse_args()
    try:
        reserve_out(args.out)
    except FileExistsError:
        print(f"output exists: {args.out}", file=sys.stderr)
        return 2
    try:
        result = execute(args)
        rc = 0 if result["all_equal"] else 1
    except Exception as exc:
        result = {**started(), "error": str(exc), "traceback": traceback.format_exc()}
        rc = 2
    result["exit_code"] = rc
    save_out(args.out, result)
    return rc


if __name__ == "__main__":
    sys.exit(main())
~~~~

## equiv_real-r1.py

sha256: 1830e949fbdce1c4a5d9bb60ac1c2c1113b08d70b3e00d419c01d0e0247d53bf

~~~~python
#!/usr/bin/env python3
"""Compare old/new check_docs on a clone and six injected corpus faults."""
from __future__ import annotations

import argparse
import datetime as dt
import json
import os
from pathlib import Path
import re
import shutil
import socket
import subprocess
import sys
import tempfile
import time
import traceback


def absolute_file(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or not path.is_file():
        raise argparse.ArgumentTypeError(f"absolute existing file required: {value}")
    return path


def absolute_dir(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute() or not path.is_dir():
        raise argparse.ArgumentTypeError(f"absolute existing directory required: {value}")
    return path


def absolute_out(value: str) -> Path:
    path = Path(value)
    if not path.is_absolute():
        raise argparse.ArgumentTypeError("--out must be absolute")
    return path


def common(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--src-repo", type=absolute_dir, required=True)
    parser.add_argument("--old-commit", required=True)
    parser.add_argument("--new-checker", type=absolute_file, required=True)
    parser.add_argument("--scratch", type=absolute_dir, required=True)
    parser.add_argument("--out", type=absolute_out, required=True)


def reserve_out(path: Path) -> None:
    with path.open("x", encoding="utf-8"):
        pass


def save_out(path: Path, data: dict) -> None:
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")


def started() -> dict:
    return {"hostname": socket.gethostname(), "started_at": dt.datetime.now(dt.timezone.utc).isoformat(), "wall_seconds": None}


def git(*args: str, capture: bool = False) -> subprocess.CompletedProcess:
    return subprocess.run(["git", *args], check=True, capture_output=capture)


def old_blob(src: Path, commit: str) -> bytes:
    return git("-C", str(src), "show", f"{commit}:tools/check_docs.py", capture=True).stdout


def clone(src: Path, commit: str, target: Path) -> None:
    git("clone", "--quiet", "--no-checkout", str(src), str(target))
    git("-C", str(target), "checkout", "--quiet", "--detach", commit)


def reset(tree: Path) -> None:
    git("-C", str(tree), "checkout", "--", ".")
    git("-C", str(tree), "clean", "-fdq")


def install(tree: Path, blob: bytes) -> None:
    target = tree / "tools/check_docs.py"
    fd, name = tempfile.mkstemp(prefix=".check_docs_probe_", dir=target.parent)
    try:
        with os.fdopen(fd, "wb") as stream:
            stream.write(blob)
        os.chmod(name, target.stat().st_mode & 0o777)
        os.replace(name, target)
    finally:
        if os.path.exists(name):
            os.unlink(name)


def run_checker(tree: Path, args: list[str] | None = None) -> dict:
    stamp = started()
    start = time.perf_counter()
    proc = subprocess.run([sys.executable, "tools/check_docs.py", *(args or [])], cwd=tree, capture_output=True)
    stdout = proc.stdout
    return {
        "hostname": stamp["hostname"], "started_at": stamp["started_at"],
        "rc": proc.returncode,
        "stdout_hex": stdout.hex(), "stderr_hex": proc.stderr.hex(),
        "findings_hex": sorted({line.hex() for line in stdout.splitlines() if line.startswith(b"  - ")}),
        "wall_seconds": time.perf_counter() - start,
    }


def append_next_action(tree: Path, addition: bytes) -> None:
    path = tree / "docs/worklog.md"
    data = path.read_bytes()
    marker = b"### \xe6\xac\xa1\xe3\x81\xae\xe4\xb8\x80\xe6\x89\x8b"
    if marker not in data:
        raise ValueError("worklog has no next-action section")
    idx = data.rfind(marker)
    if b"\n## " in data[idx:]:
        raise ValueError("last next-action section is not in final entry")
    path.write_bytes(data.rstrip(b"\r\n") + b"\n" + addition + b"\n")


def archive_files(tree: Path) -> list[tuple[Path, list[re.Match[str]]]]:
    result = []
    for path in sorted((tree / "docs/archive").glob("worklog-*.md")):
        text = path.read_text(encoding="utf-8")
        entries = list(re.finditer(r"^## (?P<date>\d{4}-\d{2}-\d{2}) \((?P<num>[1-9]\d*)\) — .*?$", text, re.M))
        if entries:
            result.append((path, entries))
    return result


def fault(tree: Path, index: int) -> str:
    if index == 0:
        return "unaltered"
    if index == 1:
        append_next_action(tree, b"- [T-9998] (999999)")
        return "dangling_carry"
    if index == 5:
        append_next_action(tree, b"<!--\n- [T-9996] hidden\n-->\n```text\n- [T-9995] hidden\n```")
        return "visibility"
    if index == 6:
        append_next_action(tree, "- [T-9997] 変わらず (12 参照)".encode())
        return "malformed_carry"
    archives = archive_files(tree)
    if index == 2:
        if len(archives) < 2:
            raise ValueError("two numbered archives required")
        first = archives[0]
        other = next(((p, m) for p, m in archives[1:] if m[0].group("num") != first[1][0].group("num")), None)
        if other is None:
            raise ValueError("distinct archive entry numbers required")
        path, entries = other
        text = path.read_text(encoding="utf-8")
        match = entries[0]
        begin, end = match.span("num")
        path.write_text(text[:begin] + first[1][0].group("num") + text[end:], encoding="utf-8")
        return "duplicate_entry_number"
    if index == 3:
        if len(archives) < 2:
            raise ValueError("two numbered archives required")
        ordered = sorted(archives, key=lambda pair: (pair[1][0].group("date"), int(pair[1][0].group("num"))))
        left, right = ordered[0], ordered[1]
        path, entries = right
        text = path.read_text(encoding="utf-8")
        m = entries[0]
        replacement = left[1][-1].group("date") + " (" + left[1][-1].group("num") + ")"
        begin, end = m.start("date"), m.end("num") + 1
        path.write_text(text[:begin] + replacement + text[end:], encoding="utf-8")
        return "ambiguous_archive_order"
    if index == 4:
        candidates = sorted(archives, key=lambda pair: (pair[0].read_bytes().count(b"- [T-"), pair[0].stat().st_size), reverse=True)
        if len(candidates) < 2:
            raise ValueError("two numbered archives required")
        for (path, _), ending in zip(candidates[:2], (b"\r\n", b"\r")):
            data = path.read_bytes().replace(b"\r\n", b"\n").replace(b"\r", b"\n")
            path.write_bytes(data.replace(b"\n", ending))
        return "mixed_newlines"
    raise ValueError(index)


def execute(args: argparse.Namespace) -> dict:
    info = started()
    begin = time.perf_counter()
    old = old_blob(args.src_repo, args.old_commit)
    new = args.new_checker.read_bytes()
    results = []
    with tempfile.TemporaryDirectory(prefix="equiv_real_", dir=args.scratch) as place:
        tree = Path(place) / "tree"
        clone(args.src_repo, args.old_commit, tree)
        baseline = None
        for index in range(7):
            state_stamp = started()
            state_begin = time.perf_counter()
            reset(tree)
            label = fault(tree, index)
            install(tree, old)
            left = run_checker(tree)
            install(tree, new)
            right = run_checker(tree)
            if index == 0:
                baseline = left
            reached = None if index == 0 else (left["rc"], left["stdout_hex"]) != (baseline["rc"], baseline["stdout_hex"])
            results.append({"state": label, "hostname": state_stamp["hostname"],
                            "started_at": state_stamp["started_at"],
                            "wall_seconds": time.perf_counter() - state_begin,
                            "fault_reached": reached, "old": left, "new": right,
                            "bytes_equal": all(left[key] == right[key] for key in ("rc", "stdout_hex", "stderr_hex")),
                            "findings_equal": left["findings_hex"] == right["findings_hex"]})
    info["wall_seconds"] = time.perf_counter() - begin
    info.update({"states": results, "all_equal": all(row["bytes_equal"] for row in results)})
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    common(parser)
    args = parser.parse_args()
    try:
        reserve_out(args.out)
    except FileExistsError:
        print(f"output exists: {args.out}", file=sys.stderr)
        return 2
    try:
        result = execute(args)
        rc = 0 if result["all_equal"] else 1
    except Exception as exc:
        result = {**started(), "error": str(exc), "traceback": traceback.format_exc()}
        rc = 2
    result["exit_code"] = rc
    save_out(args.out, result)
    return rc


if __name__ == "__main__":
    sys.exit(main())
~~~~

## equiv_fixtures.py

sha256: ad88ed18b5ccdae781121d57f8f45372d648925d5516ee4d871f562531c12c56

~~~~python
#!/usr/bin/env python3
"""Compare checker calls and pytest outcomes from old/new commit fixtures."""
from __future__ import annotations

import argparse
import json
import os
from pathlib import Path
import subprocess
import sys
import tempfile
import time
import traceback

from equiv_real import absolute_dir, clone, common, install, reserve_out, save_out, started


def test_file(value: str) -> str:
    path = Path(value)
    if path.is_absolute() or ".." in path.parts or path.suffix != ".py":
        raise argparse.ArgumentTypeError("--test-file must be a repo-relative Python file")
    return value


def run_pytest(tree: Path, test: str, selector: str | None, record: Path, probe_dir: Path) -> dict:
    env = os.environ.copy()
    env["PYTHONPATH"] = str(probe_dir)
    env["EQUIV_RECORD"] = str(record)
    env["EQUIV_TREE"] = str(tree)
    env.pop("PYTEST_ADDOPTS", None)
    argv = [sys.executable, "-m", "pytest", "-p", "no:xdist", "-p", "no:cacheprovider",
            "-p", "equiv_plugin", test, "-q"]
    if selector:
        argv.extend(["-k", selector])
    started_at = started()["started_at"]
    begin = time.perf_counter()
    proc = subprocess.run(argv, cwd=tree, env=env, capture_output=True)
    if not record.is_file():
        raise RuntimeError(f"pytest did not write record (rc={proc.returncode}): {proc.stderr[-3000:]!r}")
    data = json.loads(record.read_text(encoding="utf-8"))
    return {"command": argv, "started_at": started_at, "wall_seconds": time.perf_counter() - begin,
            "pytest_rc": proc.returncode, "pytest_stdout_tail": proc.stdout[-3000:].decode("utf-8", "replace"),
            "pytest_stderr_tail": proc.stderr[-3000:].decode("utf-8", "replace"), **data}


def compare(old: dict, new: dict) -> tuple[list[dict], int, int]:
    differences = []
    old_nodes, new_nodes = old["nodes"], new["nodes"]
    for node in sorted(set(old_nodes) | set(new_nodes)):
        if old_nodes.get(node) != new_nodes.get(node):
            differences.append({"nodeid": node, "field": "outcome", "old": old_nodes.get(node), "new": new_nodes.get(node)})
    def grouped(data):
        result = {}
        for call in data["calls"]:
            result.setdefault(call["nodeid"], []).append(call)
        return result
    old_calls, new_calls = grouped(old), grouped(new)
    for node in sorted(set(old_calls) | set(new_calls)):
        left, right = old_calls.get(node, []), new_calls.get(node, [])
        for index in range(max(len(left), len(right))):
            a = left[index] if index < len(left) else None
            b = right[index] if index < len(right) else None
            if a != b:
                differences.append({"nodeid": node, "field": "call", "index": index + 1, "old": a, "new": b})
    if old["pytest_rc"] != new["pytest_rc"]:
        differences.append({"field": "pytest_rc", "old": old["pytest_rc"], "new": new["pytest_rc"]})
    return differences, len(old["calls"]), len(old_calls)


def execute(args: argparse.Namespace) -> dict:
    info = started()
    begin = time.perf_counter()
    probe_dir = Path(__file__).resolve().parent
    with tempfile.TemporaryDirectory(prefix="equiv_fixtures_", dir=args.scratch) as place:
        root = Path(place)
        if args.smoke_tree:
            old_tree = new_tree = args.smoke_tree
        else:
            old_tree, new_tree = root / "old", root / "new"
            clone(args.src_repo, args.old_commit, old_tree)
            clone(args.src_repo, args.old_commit, new_tree)
            install(new_tree, args.new_checker.read_bytes())
        if not (old_tree / args.test_file).is_file() or not (new_tree / args.test_file).is_file():
            raise FileNotFoundError(args.test_file)
        old = run_pytest(old_tree, args.test_file, args.k, root / "old.json", probe_dir)
        new = run_pytest(new_tree, args.test_file, args.k, root / "new.json", probe_dir)
    differences, count, node_count = compare(old, new)
    info["wall_seconds"] = time.perf_counter() - begin
    info.update({"old": old, "new": new, "nodeid_sets_equal": set(old["nodes"]) == set(new["nodes"]),
                 "checker_call_count": count, "checker_node_count": node_count,
                 "differences_count": len(differences), "differences_first_20": differences[:20],
                 "all_equal": not differences and count > 0 and set(old["nodes"]) == set(new["nodes"])})
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    common(parser)
    parser.add_argument("--test-file", type=test_file, default="orchestrator/tests/test_check_docs.py")
    parser.add_argument("-k")
    parser.add_argument("--smoke-tree", type=absolute_dir, help=argparse.SUPPRESS)
    args = parser.parse_args()
    try:
        reserve_out(args.out)
    except FileExistsError:
        print(f"output exists: {args.out}", file=sys.stderr)
        return 2
    try:
        result = execute(args)
        rc = 2 if result["checker_call_count"] == 0 else (0 if result["all_equal"] else 1)
    except Exception as exc:
        result, rc = {**started(), "error": str(exc), "traceback": traceback.format_exc()}, 2
    result["exit_code"] = rc
    save_out(args.out, result)
    return rc


if __name__ == "__main__":
    sys.exit(main())
~~~~

## equiv_plugin.py

sha256: b89a496aa887af04da2fbaa0e99b647c04e46cc8f0b454824a14d7ba81148778

~~~~python
"""Pytest plugin recording check_docs subprocesses and collected node outcomes."""
from __future__ import annotations

import base64
import json
import os
from pathlib import Path
import re
import subprocess
import tempfile

import pytest

_ORIGINAL_RUN = subprocess.run
_ORIGINAL_POPEN = subprocess.Popen
_ACTIVE = None
_SUPPRESS_POPEN = False
_CALL_ORDER = {}
_NODES = {}
_CALLS = []


def _normalize_string(value: str) -> str:
    tree = os.environ.get("EQUIV_TREE", "")
    if tree:
        value = value.replace(tree, "<TREE>")
    tmp = re.escape(tempfile.gettempdir().rstrip("/"))
    value = re.sub(tmp + r"/izanagi_checkdocs_[^/\\\s:'\"<>]+", "<ROOT>", value)
    value = re.sub(tmp + r"/pytest-of-[^/\\\s:'\"<>]+/pytest-[^/\\\s:'\"<>]+(?:/[^/\\\s:'\"<>]+)?", "<ROOT>", value)
    return value


def _normalize(value):
    if value is None:
        return None
    if isinstance(value, bytes):
        normalized = _normalize_string(value.decode("latin1")).encode("latin1")
        return {"kind": "bytes", "base64": base64.b64encode(normalized).decode("ascii")}
    if isinstance(value, str):
        return {"kind": "text", "value": _normalize_string(value)}
    return {"kind": type(value).__name__, "value": repr(value)}


def _argv(args):
    if isinstance(args, (str, bytes, os.PathLike)):
        return [os.fsdecode(args)]
    return [os.fsdecode(arg) for arg in args]


def _is_checker(args):
    return any(arg.replace("\\", "/").endswith("tools/check_docs.py") for arg in _argv(args))


def _record(args, rc, stdout, stderr):
    if _ACTIVE is None:
        return
    order = _CALL_ORDER.get(_ACTIVE, 0) + 1
    _CALL_ORDER[_ACTIVE] = order
    _CALLS.append({"nodeid": _ACTIVE, "order": order,
                   "argv": [_normalize(arg) for arg in _argv(args)],
                   "rc": rc, "stdout": _normalize(stdout), "stderr": _normalize(stderr)})


def _run(*args, **kwargs):
    global _SUPPRESS_POPEN
    argv = args[0] if args else kwargs.get("args")
    previous = _SUPPRESS_POPEN
    _SUPPRESS_POPEN = True
    try:
        result = _ORIGINAL_RUN(*args, **kwargs)
    finally:
        _SUPPRESS_POPEN = previous
    if _is_checker(argv):
        _record(argv, result.returncode, result.stdout, result.stderr)
    return result


class _ObservedPopen:
    def __init__(self, process, argv):
        self._process = process
        self._argv = argv
        self._done = False

    def _finish(self, out=None, err=None):
        if not self._done and self._process.returncode is not None:
            _record(self._argv, self._process.returncode, out, err)
            self._done = True

    def communicate(self, *args, **kwargs):
        out, err = self._process.communicate(*args, **kwargs)
        self._finish(out, err)
        return out, err

    def wait(self, *args, **kwargs):
        rc = self._process.wait(*args, **kwargs)
        self._finish()
        return rc

    def __enter__(self):
        self._process.__enter__()
        return self

    def __exit__(self, *args):
        result = self._process.__exit__(*args)
        self._finish()
        return result

    def __getattr__(self, name):
        return getattr(self._process, name)


def _popen(*args, **kwargs):
    argv = args[0] if args else kwargs.get("args")
    process = _ORIGINAL_POPEN(*args, **kwargs)
    if _SUPPRESS_POPEN or not _is_checker(argv):
        return process
    return _ObservedPopen(process, argv)


def pytest_configure(config):
    subprocess.run = _run
    subprocess.Popen = _popen


def pytest_unconfigure(config):
    subprocess.run = _ORIGINAL_RUN
    subprocess.Popen = _ORIGINAL_POPEN


def pytest_collection_finish(session):
    for item in session.items:
        _NODES[item.nodeid] = "not_run"


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    global _ACTIVE
    previous = _ACTIVE
    _ACTIVE = item.nodeid
    try:
        yield
    finally:
        _ACTIVE = previous


def pytest_runtest_logreport(report):
    node = report.nodeid
    if report.failed:
        _NODES[node] = "failed" if report.when == "call" else "error"
    elif report.skipped and _NODES.get(node) not in ("failed", "error"):
        _NODES[node] = "skipped"
    elif report.passed and report.when == "call" and _NODES.get(node) not in ("failed", "error", "skipped"):
        _NODES[node] = "passed"


def pytest_sessionfinish(session, exitstatus):
    path = Path(os.environ["EQUIV_RECORD"])
    path.write_text(json.dumps({"nodes": _NODES, "calls": _CALLS, "pytest_rc": int(exitstatus)}, ensure_ascii=False, indent=2), encoding="utf-8")
~~~~

## bench_abab.py

sha256: ba22dffd419f615517d53ccdd902f2681d9b84e078cf32869f025eb7349af164

~~~~python
#!/usr/bin/env python3
"""Measure old/new checker wall time and child peak RSS in one ABAB job."""
from __future__ import annotations

import argparse
import hashlib
import os
from pathlib import Path
import statistics
import subprocess
import sys
import tempfile
import time
import traceback

from equiv_real import absolute_out, clone, common, install, old_blob, reserve_out, save_out, started


def positive(value: str) -> int:
    number = int(value)
    if number < 1:
        raise argparse.ArgumentTypeError("--rounds must be positive")
    return number


def measured_run(tree: Path) -> dict:
    stamp = started()
    begin = time.perf_counter()
    with tempfile.TemporaryFile() as out, tempfile.TemporaryFile() as err:
        proc = subprocess.Popen([sys.executable, "tools/check_docs.py"], cwd=tree, stdout=out, stderr=err)
        _, status, usage = os.wait4(proc.pid, 0)
        proc.returncode = os.waitstatus_to_exitcode(status)
        out.seek(0)
        stdout = out.read()
        err.seek(0)
        stderr = err.read()
    return {"started_at": stamp["started_at"], "wall_seconds": time.perf_counter() - begin,
            "peak_rss_kib": usage.ru_maxrss, "rc": proc.returncode,
            "stdout_sha256": hashlib.sha256(stdout).hexdigest(),
            "stderr_sha256": hashlib.sha256(stderr).hexdigest()}


def summary(runs: list[dict]) -> dict:
    walls = [row["wall_seconds"] for row in runs]
    rss = [row["peak_rss_kib"] for row in runs]
    return {"wall_median_seconds": statistics.median(walls), "wall_min_seconds": min(walls),
            "wall_max_seconds": max(walls), "rss_median_kib": statistics.median(rss),
            "rss_min_kib": min(rss), "rss_max_kib": max(rss)}


def execute(args: argparse.Namespace) -> dict:
    info = started()
    begin = time.perf_counter()
    old, new = old_blob(args.src_repo, args.old_commit), args.new_checker.read_bytes()
    runs = []
    with tempfile.TemporaryDirectory(prefix="bench_abab_", dir=args.scratch) as place:
        tree = Path(place) / "tree"
        clone(args.src_repo, args.old_commit, tree)
        for stage in ("warmup", "measure"):
            for round_index in range(1 if stage == "warmup" else args.rounds):
                for side, blob in (("old", old), ("new", new)):
                    install(tree, blob)
                    runs.append({"stage": stage, "round": round_index + 1, "side": side, **measured_run(tree)})
        profile = None
        if args.profile_new:
            if args.profile_new.exists():
                raise FileExistsError(args.profile_new)
            install(tree, new)
            profile_start = started()
            profile_begin = time.perf_counter()
            proc = subprocess.run([sys.executable, "-m", "cProfile", "-o", str(args.profile_new),
                                   "tools/check_docs.py"], cwd=tree, capture_output=True)
            profile = {"path": str(args.profile_new), "started_at": profile_start["started_at"],
                       "wall_seconds": time.perf_counter() - profile_begin, "rc": proc.returncode,
                       "stdout_sha256": hashlib.sha256(proc.stdout).hexdigest(),
                       "stderr_sha256": hashlib.sha256(proc.stderr).hexdigest()}
    measured = {side: [row for row in runs if row["stage"] == "measure" and row["side"] == side]
                for side in ("old", "new")}
    summaries = {side: summary(rows) for side, rows in measured.items()}
    side_stable = {side: len({(row["rc"], row["stdout_sha256"]) for row in runs if row["side"] == side}) == 1
                   for side in ("old", "new")}
    cross_equal = (measured["old"][0]["rc"], measured["old"][0]["stdout_sha256"]) == (measured["new"][0]["rc"], measured["new"][0]["stdout_sha256"])
    info["wall_seconds"] = time.perf_counter() - begin
    info.update({"runs": runs, "summary": summaries, "new_old_median_wall_ratio":
                 summaries["new"]["wall_median_seconds"] / summaries["old"]["wall_median_seconds"],
                 "side_stable": side_stable, "cross_equal": cross_equal, "profile_new": profile,
                 "all_equal": all(side_stable.values()) and cross_equal})
    return info


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    common(parser)
    parser.add_argument("--rounds", type=positive, default=5)
    parser.add_argument("--profile-new", type=absolute_out)
    args = parser.parse_args()
    try:
        reserve_out(args.out)
    except FileExistsError:
        print(f"output exists: {args.out}", file=sys.stderr)
        return 2
    try:
        result = execute(args)
        rc = 0 if result["all_equal"] and (result["profile_new"] is None or result["profile_new"]["rc"] == 0) else 1
    except Exception as exc:
        result, rc = {**started(), "error": str(exc), "traceback": traceback.format_exc()}, 2
    result["exit_code"] = rc
    save_out(args.out, result)
    return rc


if __name__ == "__main__":
    sys.exit(main())
~~~~

## README.md

sha256: 9dc9cd65f342d79106f8dcef0169acaa1e4cd3bafdf14b732a2122840b15cd08

~~~~markdown
# check_docs speed probe

These disposable scripts use Python's standard library and pytest. Run them through
`python3 tools/pegasus/dispatch_compute.py --task generic -- python3
<absolute-path>/<script> ...`. The generic task starts in the source checkout and
clears inherited environment variables. Every input and output path is therefore
an absolute CLI argument. `--scratch` must already exist; each driver creates and
removes its own temporary subdirectory there. The scripts make independent local
clones with `git clone --quiet --no-checkout` and detached checkout. They do not
initialize submodules or register worktrees. Checker replacement writes a separate
file and uses `os.replace` to avoid modifying hardlinked checkout data.

All drivers require `--src-repo ABS_DIR --old-commit SHA --new-checker ABS_FILE
--scratch ABS_DIR --out ABS_JSON`. Existing output JSON is refused with rc 2.
Results include hostname, UTC ISO start time and `perf_counter` wall durations.
Exit status is 0 for equality, 1 for inequality, 2 when execution is impossible.
Failures after output reservation are recorded as `error` and `traceback` in JSON.

* `equiv_real.py`: seven reset states (`unaltered`, `dangling_carry`,
  `duplicate_entry_number`, `ambiguous_archive_order`, `mixed_newlines`,
  `visibility`, `malformed_carry`). JSON `states[]` holds old/new rc, full stdout
  and stderr as hexadecimal bytes, finding set as hexadecimal lines, run wall,
  `bytes_equal`, `findings_equal`, and `fault_reached`. The latter compares the
  old rc and stdout with the unaltered baseline; `false` marks an injection that
  did not visibly reach the checker. It does not automatically make the old/new
  comparison fail.
* `equiv_fixtures.py`: optional `--test-file` (default
  `orchestrator/tests/test_check_docs.py`) and `-k EXPR`. It runs the same old
  commit test file in two independent clones, replacing only the new clone's
  checker. Its child pytest runs are serial (`-p no:xdist`) and do not use the
  cache provider. JSON includes both pytest records, node outcomes, every
  observed checker call, call and node counts, and the first 20 detailed
  differences. Zero checker calls returns rc 2. `--smoke-tree ABS_DIR` is an
  internal small smoke route that runs both sides on one existing tree without
  cloning or replacing its checker.
* `equiv_plugin.py`: loaded into child pytest by `-p equiv_plugin`. It records
  `subprocess.run` and `subprocess.Popen` calls whose argv has an element ending
  in `tools/check_docs.py`, including nodeid, order within node, argv, rc,
  stdout and stderr. It also records passed, failed, skipped and setup/teardown
  error outcomes. The fixture driver passes the plugin directory and record
  location in its *child* environment; it reads no inherited probe variables.
* `bench_abab.py`: optional `--rounds N` (default 5) and `--profile-new ABS_PROF`.
  JSON `runs[]` contains warmup and measured old/new pairs, wall seconds, child
  peak RSS in KiB (Linux `wait4`), rc, and stdout/stderr SHA256. `summary` has
  median, min and max wall/RSS for measured pairs; `new_old_median_wall_ratio`
  excludes warmup. `side_stable` verifies each side's rc/stdout across every run,
  and `cross_equal` verifies old/new rc/stdout. The optional cProfile run is last
  and excluded from the timing summary.

## Fixture normalization

Comparison preserves whether an argv/output value was `str` or `bytes`. Bytes
are normalized through Latin-1 (a reversible byte mapping) and stored as base64;
text is stored as text. The clone's exact absolute path is replaced with
`<TREE>` first. Paths rooted at the `_build_min_repo` temporary directory
`/tmp/izanagi_checkdocs_*` are replaced with `<ROOT>`. Paths rooted at pytest's
`/tmp/pytest-of-*/pytest-*` directories, optionally including the immediate
fixture directory, are also replaced with `<ROOT>`. `/tmp` means the child's
`tempfile.gettempdir()`. The same replacements apply to each argv element and
stdout/stderr. Node IDs and outcomes are compared literally. Replacement of
random roots intentionally loses their identity; the comparison targets checker
behavior, and every call remains in order under its node.

The direct `Popen` wrapper records output returned by `communicate()`. If a
caller reads a pipe manually and only invokes `wait()`, stdout/stderr are
recorded as null because Python does not expose the already consumed bytes.
~~~~
