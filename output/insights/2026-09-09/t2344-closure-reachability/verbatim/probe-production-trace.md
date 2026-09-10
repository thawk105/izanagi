# production 入口を trace する子 process (source-only loader・memory 上の 1 変異)

逐語。原本は repository の外 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability/prod_trace_child.py`) に置いた。
再現するときはこの内容を repository の外へ書き出して実行する。

```python
#!/usr/bin/env python3
"""Child process: run one production entry, optionally with one in-memory mutation.

Never writes to the repository.  Sources are read from disk, verified against the
pinned commit's blob, compiled in memory and executed by a custom loader, so an
existing ``__pycache__`` can never be the thing we observed.  The mutation (used
for the counterfactual axis) rewrites exactly one ``if`` test of exactly one
module in memory; the checkout stays byte-identical.

usage: prod_trace_child.py <repo> <commit> <entry> <out.json> [<module> <lineno>]
"""
from __future__ import annotations

import ast
import hashlib
import importlib.abc
import importlib.machinery
import importlib.util
import json
import subprocess
import sys
import traceback
from pathlib import Path

REPO = Path(sys.argv[1]).resolve()
COMMIT = sys.argv[2]
ENTRY = sys.argv[3]
OUT = Path(sys.argv[4])
MUT_MODULE = sys.argv[5] if len(sys.argv) > 6 else None
MUT_LINE = int(sys.argv[6]) if len(sys.argv) > 6 else None

TOP = "orchestrator"
LOADED: dict[str, dict] = {}
EXECUTED: dict[str, set[int]] = {}
MODULE_FRAMES: dict[str, set[int]] = {}
CLASSBODY_FRAMES: dict[str, set[int]] = {}
MUTATION_FIRED = {"value": False}

CO_OPTIMIZED = 0x0001
CO_NEWLOCALS = 0x0002


def frame_kind(code) -> str:
    """module body, class body, or a real callable.

    Class bodies run at import just like the module body, so counting them as
    "the module's behaviour ran" would inflate functional reachability.  CPython
    compiles functions with CO_OPTIMIZED (fast locals) and class bodies with
    CO_NEWLOCALS but not CO_OPTIMIZED; module code has neither.
    """
    flags = code.co_flags
    if flags & CO_OPTIMIZED:
        return "callable"
    if flags & CO_NEWLOCALS:
        return "classbody"
    return "module"


def blob_sha(rel: str) -> str | None:
    proc = subprocess.run(["git", "show", f"{COMMIT}:{rel}"], cwd=REPO,
                          capture_output=True)
    if proc.returncode != 0:
        return None
    return hashlib.sha256(proc.stdout).hexdigest()


class SourceLoader(importlib.abc.Loader):
    def __init__(self, fullname: str, path: Path, rel: str) -> None:
        self.fullname = fullname
        self.path = path
        self.rel = rel

    def create_module(self, spec):
        return None

    def exec_module(self, module):
        raw = self.path.read_bytes()
        disk = hashlib.sha256(raw).hexdigest()
        pinned = blob_sha(self.rel)
        record = {"rel": self.rel, "disk_sha256": disk, "pinned_sha256": pinned,
                  "matches_commit": disk == pinned, "exec_started": True,
                  "exec_completed": False, "mutated": False}
        LOADED[self.rel] = record
        text = raw.decode("utf-8")
        tree = ast.parse(text, filename=str(self.path))
        if MUT_MODULE is not None and self.rel == MUT_MODULE:
            hit = [n for n in ast.walk(tree)
                   if isinstance(n, ast.If) and n.lineno == MUT_LINE]
            if len(hit) != 1:
                raise RuntimeError(
                    f"mutation site not unique: {self.rel}:{MUT_LINE} ({len(hit)})")
            node = hit[0]
            node.test = ast.UnaryOp(op=ast.Not(), operand=node.test)
            ast.fix_missing_locations(tree)
            record["mutated"] = True
            MUTATION_FIRED["site"] = f"{self.rel}:{MUT_LINE}"
        code = compile(tree, str(self.path), "exec")
        exec(code, module.__dict__)
        record["exec_completed"] = True


class Finder(importlib.abc.MetaPathFinder):
    def find_spec(self, fullname, path=None, target=None):
        if fullname.split(".")[0] != TOP:
            return None
        base = fullname.replace(".", "/")
        for rel, is_pkg in ((f"{base}.py", False), (f"{base}/__init__.py", True)):
            candidate = REPO / rel
            if candidate.is_file():
                loader = SourceLoader(fullname, candidate, rel)
                spec = importlib.machinery.ModuleSpec(
                    fullname, loader, origin=str(candidate), is_package=is_pkg)
                spec.has_location = True
                if is_pkg:
                    spec.submodule_search_locations = [str(candidate.parent)]
                return spec
        if (REPO / base).is_dir():  # namespace package
            spec = importlib.machinery.ModuleSpec(fullname, None, is_package=True)
            spec.submodule_search_locations = [str(REPO / base)]
            return spec
        return None


def tracer(frame, event, arg):
    if event != "call":
        return None
    filename = frame.f_code.co_filename
    try:
        rel = str(Path(filename).resolve().relative_to(REPO))
    except (ValueError, OSError):
        return None
    return make_line_tracer(rel, frame_kind(frame.f_code))


def make_line_tracer(rel: str, kind: str):
    bucket = {"module": MODULE_FRAMES, "classbody": CLASSBODY_FRAMES,
              "callable": EXECUTED}[kind]

    def line_tracer(frame, event, arg):
        if event == "line":
            bucket.setdefault(rel, set()).add(frame.f_lineno)
            if MUT_MODULE is not None and rel == MUT_MODULE and frame.f_lineno == MUT_LINE:
                MUTATION_FIRED["value"] = True
        return line_tracer
    return line_tracer


EXTERNAL_ROOTS = (
    Path("/work/1/SFC/tanab/b10-backoff-grid-runs5"),
    Path("/work/1/SFC/tanab/izanagi-measurements"),
)


def _admit_over(paths) -> dict:
    from orchestrator.campaign import artifact_admission as A
    admitted, denied = [], {}
    for path in paths:
        try:
            view = A.require_admitted_campaign(
                path, purpose=A.CampaignReadPurpose.CERTIFIED_ACCEPTANCE)
            A.require_certified_commit_evidence(view)
            admitted.append(path.name)
        except BaseException as exc:  # noqa: BLE001 - the verdict is the datum
            denied[path.name] = f"{type(exc).__name__}: {exc}"[:300]
    return {"G_admitted": sorted(admitted), "denied": denied}


def entry_admission() -> dict:
    root = REPO / "output" / "campaigns"
    return _admit_over(sorted(p for p in root.iterdir() if p.is_dir()))


def entry_admission_ext() -> dict:
    """Same production API over the recorded external measurement roots."""
    paths = []
    for root in EXTERNAL_ROOTS:
        if root.is_dir():
            paths.extend(sorted(p for p in root.glob("**/campaigns/*") if p.is_dir()))
    return _admit_over(paths)


def entry_freeze() -> dict:
    from orchestrator.campaign import s8b_ratified_freeze as F
    from orchestrator.campaign import s8b_oracle_spec as S
    out: dict = {}
    ratified = F.load_ratified_freeze(REPO)
    out["ratified_sha256"] = ratified.sha256
    F.assert_g1_floor_selection_identity(ratified, REPO)
    reverified = F.reverify_published_freeze(ratified, REPO)
    out["reverified_sha256"] = reverified.ratified.sha256
    approved = S.load_approved_spec(REPO)
    out["approved_type"] = type(approved).__name__
    return out


ENTRIES = {"admission": entry_admission, "admission_ext": entry_admission_ext,
           "freeze": entry_freeze}


def main() -> int:
    if any(m.split(".")[0] == TOP for m in sys.modules):
        OUT.write_text(json.dumps({"status": "RX",
                                   "reason": "orchestrator preloaded"}))
        return 3
    sys.meta_path.insert(0, Finder())
    sys.path.insert(0, str(REPO))
    result: dict = {"entry": ENTRY, "commit": COMMIT,
                    "mutation": {"module": MUT_MODULE, "line": MUT_LINE}}
    sys.settrace(tracer)
    try:
        result["verdict"] = ENTRIES[ENTRY]()
        result["status"] = "ok"
    except BaseException as exc:  # noqa: BLE001
        result["status"] = "entry-error"
        result["error"] = f"{type(exc).__name__}: {exc}"[:500]
        result["traceback"] = traceback.format_exc()[-1500:]
    finally:
        sys.settrace(None)
    result["mutation_line_executed"] = MUTATION_FIRED["value"]
    result["loaded"] = LOADED
    result["functional_lines"] = {k: len(v) for k, v in sorted(EXECUTED.items())}
    result["module_body_lines"] = {k: len(v) for k, v in sorted(MODULE_FRAMES.items())}
    result["classbody_lines"] = {k: len(v) for k, v in sorted(CLASSBODY_FRAMES.items())}
    result["functional_line_numbers"] = {k: sorted(v) for k, v in sorted(EXECUTED.items())}
    result["source_mismatch"] = sorted(
        rel for rel, r in LOADED.items() if not r["matches_commit"])
    OUT.write_text(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
