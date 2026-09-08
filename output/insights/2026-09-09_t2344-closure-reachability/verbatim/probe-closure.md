# 閉包を数える probe (commit 固定・git blob 読み・AST import 解決)

逐語。原本は repository の外 (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2344-closure-reachability/probe_closure_v2.py`) に置いた。
再現するときはこの内容を repository の外へ書き出して実行する。

```python
#!/usr/bin/env python3
"""Commit-pinned re-derivation of the enforcement source closure discovery set.

Reads every blob through ``git`` at a fixed commit, so the same probe can be run
against today's main and against the commit that landed T-733 (positive control).

Discovery aid only (D368): the canonical closure remains the curated exact tuple.

usage: probe_closure_v2.py <repo> <commit> [--layer1-from-pre-t733]
"""
from __future__ import annotations

import ast
import json
import subprocess
import sys

TOP = "orchestrator"


class Tree:
    def __init__(self, repo: str, commit: str) -> None:
        self.repo = repo
        self.commit = commit
        out = subprocess.run(
            ["git", "ls-tree", "-r", "--name-only", commit],
            cwd=repo, capture_output=True, text=True, check=True,
        ).stdout
        self.files = set(out.splitlines())
        self._cache: dict[str, str] = {}

    def read(self, rel: str) -> str:
        if rel not in self._cache:
            self._cache[rel] = subprocess.run(
                ["git", "show", f"{self.commit}:{rel}"],
                cwd=self.repo, capture_output=True, text=True, check=True,
            ).stdout
        return self._cache[rel]

    def isfile(self, rel: str) -> bool:
        return rel in self.files


def enrolled_tuple(tree: Tree, name: str) -> list[str]:
    """Extract an ordered string tuple literal from campaign_lock.py at this commit."""
    src = tree.read("orchestrator/campaign/campaign_lock.py")
    module = ast.parse(src)
    for node in module.body:
        if isinstance(node, ast.Assign):
            for target in node.targets:
                if isinstance(target, ast.Name) and target.id == name:
                    value = node.value
                    if not isinstance(value, ast.Tuple):
                        raise SystemExit(f"{name} is not a tuple literal")
                    return [ast.literal_eval(elt) for elt in value.elts]
    raise SystemExit(f"{name} not found")


def package_of(rel: str) -> str:
    parts = rel[: -len(".py")].split("/")
    return ".".join(parts[:-1])


def rel_for_module(tree: Tree, name: str) -> str | None:
    if name.split(".")[0] != TOP:
        return None
    base = name.replace(".", "/")
    for candidate in (f"{base}.py", f"{base}/__init__.py"):
        if tree.isfile(candidate):
            return candidate
    return None


def package_inits(tree: Tree, rel: str) -> list[str]:
    """__init__.py files Python executes before importing ``rel``."""
    out = []
    parts = rel.split("/")
    for i in range(1, len(parts)):
        candidate = "/".join(parts[:i] + ["__init__.py"])
        if tree.isfile(candidate):
            out.append(candidate)
    return out


def imports_of(tree: Tree, rel: str) -> tuple[set[str], list[dict]]:
    node_tree = ast.parse(tree.read(rel), filename=rel)
    pkg = package_of(rel)
    resolved: set[str] = set()
    unresolved: list[dict] = []
    for node in ast.walk(node_tree):
        if isinstance(node, ast.Import):
            for alias in node.names:
                target = rel_for_module(tree, alias.name)
                if target is not None:
                    resolved.add(target)
                elif alias.name.split(".")[0] == TOP:
                    unresolved.append({"file": rel, "line": node.lineno,
                                       "ref": alias.name, "kind": "import"})
        elif isinstance(node, ast.ImportFrom):
            if node.level == 0:
                base = node.module or ""
                if base.split(".")[0] != TOP:
                    continue
                prefix = base
            else:
                pkg_parts = pkg.split(".") if pkg else []
                strip = node.level - 1
                if strip > len(pkg_parts):
                    unresolved.append({"file": rel, "line": node.lineno,
                                       "ref": f"level={node.level} module={node.module}",
                                       "kind": "relative-overflow"})
                    continue
                base_parts = pkg_parts[: len(pkg_parts) - strip] if strip else pkg_parts
                prefix = ".".join(base_parts + ([node.module] if node.module else []))
            if prefix.split(".")[0] != TOP:
                continue
            target = rel_for_module(tree, prefix)
            found_any = target is not None
            if target is not None:
                resolved.add(target)
            for alias in node.names:
                sub = rel_for_module(tree, f"{prefix}.{alias.name}")
                if sub is not None:
                    resolved.add(sub)
                    found_any = True
            if not found_any:
                unresolved.append({"file": rel, "line": node.lineno,
                                   "ref": prefix, "kind": "from"})
    return resolved, unresolved


def expand(tree: Tree, seeds: list[str], *, depth: int | None) -> dict:
    """Expand ``seeds`` by import edges (and package init of every member)."""
    seen: set[str] = set()
    edges: dict[str, list[str]] = {}
    unresolved_all: list[dict] = []
    frontier = list(seeds)
    level = 0
    while frontier and (depth is None or level < depth):
        nxt_frontier: list[str] = []
        for rel in frontier:
            if rel in seen or not tree.isfile(rel):
                continue
            seen.add(rel)
            targets, unresolved = imports_of(tree, rel)
            unresolved_all.extend(unresolved)
            inits = set(package_inits(tree, rel))
            for t in targets:
                inits.update(package_inits(tree, t))
            out = sorted(targets | inits)
            edges[rel] = out
            nxt_frontier.extend(t for t in out if t not in seen)
        frontier = nxt_frontier
        level += 1
    # Members reached on the last allowed level are part of the set even when we
    # stop expanding them.
    for rel in frontier:
        if tree.isfile(rel):
            seen.add(rel)
    return {"members": sorted(seen), "edges": edges, "unresolved": unresolved_all}


def main() -> int:
    repo, commit = sys.argv[1], sys.argv[2]
    mode = sys.argv[3] if len(sys.argv) > 3 else ""
    tree = Tree(repo, commit)
    now = enrolled_tuple(tree, "CONTRACT_LOADER_RELATIVE_PATHS")
    result: dict = {
        "repo": repo,
        "commit": subprocess.run(["git", "rev-parse", commit], cwd=repo,
                                 capture_output=True, text=True,
                                 check=True).stdout.strip(),
        "enrolled_count": len(now),
        "enrolled": now,
    }
    if mode in ("--layer1-from-pre-t733", "--layer1-from-enrolled"):
        if mode == "--layer1-from-enrolled":
            pre = now
        else:
            pre = enrolled_tuple(tree, "PRE_T733_CONTRACT_LOADER_RELATIVE_PATHS")
        one = expand(tree, pre, depth=1)
        explicit: set[str] = set()
        inits: set[str] = set()
        for rel in pre:
            targets, _ = imports_of(tree, rel)
            explicit |= targets
            inits.update(package_inits(tree, rel))
            for t in targets:
                inits.update(package_inits(tree, t))
        result.update({
            "pre_t733_count": len(pre),
            "new_explicit_import_targets": sorted(explicit - set(pre)),
            "new_package_inits": sorted(inits - set(pre) - explicit),
            "layer1_total": len(one["members"]),
            "layer1_members": one["members"],
            "layer1_minus_enrolled": sorted(set(one["members"]) - set(now)),
            "enrolled_minus_layer1": sorted(set(now) - set(one["members"])),
        })
    else:
        full = expand(tree, now, depth=None)
        one = expand(tree, now, depth=1)
        result.update({
            "discovered_count": len(full["members"]),
            "unenrolled_count": len(set(full["members"]) - set(now)),
            "layer1_count": len(one["members"]),
            "layer1_unenrolled": sorted(set(one["members"]) - set(now)),
            "discovered": full["members"],
            "unenrolled": sorted(set(full["members"]) - set(now)),
            "unresolved_references": full["unresolved"],
            "edges": full["edges"],
        })
    print(json.dumps(result, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
