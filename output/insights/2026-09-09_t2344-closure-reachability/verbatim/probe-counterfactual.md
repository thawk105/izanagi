# 反実仮想の driver (実行済み if を 1 個ずつ否定する)

逐語。原本は repository の外 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability/run_counterfactual.py`) に置いた。
再現するときはこの内容を repository の外へ書き出して実行する。

```python
#!/usr/bin/env python3
"""Axis C: type-preserving counterfactual on unenrolled modules that really executed.

For every unenrolled module with functional execution in the baseline run we pick
``if`` statements whose line the baseline actually executed, negate exactly one of
them in memory, re-run the same production entry over the same inputs, and compare
the verdict vector.  A mutant only counts when the trace shows its line executed;
an unfired mutant is reported as CX, never as "no contribution".

The repository is never modified: the mutation lives in the child's AST only.

usage: run_counterfactual.py <repo> <commit> <entry> <baseline.json> <out.json>
       [--max-sites-per-module N]
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys
import time
from pathlib import Path

JOB = Path("/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability")
CHILD = JOB / "prod_trace_child.py"

REPO = Path(sys.argv[1]).resolve()
COMMIT = sys.argv[2]
ENTRY = sys.argv[3]
BASE = json.loads(Path(sys.argv[4]).read_text())
OUT = Path(sys.argv[5])
MAX_SITES = 6
if "--max-sites-per-module" in sys.argv:
    MAX_SITES = int(sys.argv[sys.argv.index("--max-sites-per-module") + 1])

head = json.loads((JOB / "artifacts" / "head_closure.json").read_text())
unenrolled = set(head["unenrolled"])


def verdict_vector(result: dict) -> dict:
    """The part of a run we call 'the acceptance decision'."""
    v = result.get("verdict", {})
    if "G_admitted" in v:
        return {
            "kind": "admission",
            "G": v["G_admitted"],
            "per_campaign": {k: val.split(":")[0] + "|" +
                             (val.split("reason=")[1].split()[0]
                              if "reason=" in val else "")
                             for k, val in v["denied"].items()},
        }
    return {"kind": "entry", "status": result.get("status"),
            "error": str(result.get("error"))[:200], "verdict": v}


BASE_VECTOR = verdict_vector(BASE)


def candidate_sites(rel: str, executed: list[int]) -> list[int]:
    src = (REPO / rel).read_text(encoding="utf-8")
    tree = ast.parse(src, filename=rel)
    exec_set = set(executed)
    sites = [n.lineno for n in ast.walk(tree)
             if isinstance(n, ast.If) and n.lineno in exec_set]
    # Unique lineno only; a duplicated lineno cannot be targeted unambiguously.
    seen = [ln for ln in sorted(set(sites)) if sites.count(ln) == 1]
    if len(seen) <= MAX_SITES:
        return seen
    step = len(seen) / MAX_SITES
    return [seen[int(i * step)] for i in range(MAX_SITES)]


def run_mutant(rel: str, line: int, out: Path) -> dict:
    started = time.time()
    proc = subprocess.run(
        [sys.executable, "-I", "-B", str(CHILD), str(REPO), COMMIT, ENTRY,
         str(out), rel, str(line)],
        cwd=str(JOB), capture_output=True, text=True, timeout=1800,
    )
    elapsed = round(time.time() - started, 1)
    if not out.is_file():
        return {"module": rel, "line": line, "class": "CX",
                "reason": f"child rc={proc.returncode}",
                "stderr": proc.stderr[-600:], "seconds": elapsed}
    res = json.loads(out.read_text())
    fired = res.get("mutation_line_executed", False)
    loaded = res.get("loaded", {}).get(rel, {})
    vec = verdict_vector(res)
    changed = vec != BASE_VECTOR
    if not loaded.get("mutated"):
        klass = "CX"
        reason = "mutant module not loaded"
    elif res["status"] == "entry-error":
        # The entry never reached its verdict, so a differing vector only shows
        # availability dependence, not a contribution to the acceptance decision.
        klass = "CD"
        reason = f"entry stopped: {str(res.get('error'))[:120]}"
    elif not fired:
        klass = "CX"
        reason = "mutation site never executed in mutant run"
    elif changed:
        klass = "C+"
        reason = "verdict vector changed"
    else:
        klass = "C0"
        reason = "verdict vector unchanged with the site executed"
    return {"module": rel, "line": line, "class": klass, "reason": reason,
            "fired": fired, "status": res["status"],
            "error": str(res.get("error"))[:200],
            "G_size": len(vec.get("G", [])) if vec["kind"] == "admission" else None,
            "changed": changed, "seconds": elapsed}


def main() -> int:
    targets = {rel: BASE["functional_line_numbers"][rel]
               for rel in sorted(BASE["functional_line_numbers"])
               if rel in unenrolled}
    mut_dir = JOB / "artifacts" / f"mutants-{ENTRY}"
    mut_dir.mkdir(parents=True, exist_ok=True)
    rows = []
    for rel, lines in targets.items():
        sites = candidate_sites(rel, lines)
        if not sites:
            rows.append({"module": rel, "line": None, "class": "C?",
                         "reason": "executed lines contain no uniquely addressable if"})
            continue
        for line in sites:
            out = mut_dir / f"{rel.replace('/', '_')}-{line}.json"
            row = run_mutant(rel, line, out)
            rows.append(row)
            print(f"{row['class']:3} {rel}:{line} {row['reason'][:70]}", flush=True)
    OUT.write_text(json.dumps({
        "entry": ENTRY, "commit": COMMIT,
        "baseline_vector": BASE_VECTOR,
        "max_sites_per_module": MAX_SITES,
        "rows": rows,
    }, indent=2, ensure_ascii=False))
    by = {}
    for r in rows:
        by[r["class"]] = by.get(r["class"], 0) + 1
    print("\nsummary:", json.dumps(by))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
