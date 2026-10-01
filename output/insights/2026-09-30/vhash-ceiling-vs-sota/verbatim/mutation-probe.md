# 変異の期待 node を集める login 自走 probe の逐語 (mutation/probe.py、repo 外で実行)

sha256: 797f39607b19298e8c1ba43cdc806b1fad198608562a73b87783b09132f9a946、3176 bytes

```python
#!/usr/bin/env python3
"""変異の期待 node を集める login 自走 probe (repo 外、使い捨て)。

各変異を対象の木へ注入し、test file を `PYTHONPATH=. python3 <test>` で自走して FAIL / ERROR の node を集め、
注入前の bytes を書き戻して sha256 で復元を照合する。基準走 (変異なし) が全緑でなければ中止する。
引数: <木の絶対 path> <spec json> <出力 json>
"""
import hashlib, json, re, subprocess, sys
from pathlib import Path

TEST = "orchestrator/tests/test_vhash_ceiling_vs_sota.py"
PAT = re.compile(r"^(FAIL|ERROR): (\w+) \((?:[\w.]+\.)?(\w+)(?:\.\w+)?\)", re.M)


def run(tree: Path) -> tuple[int, list[str], str]:
    env = {"PATH": "/usr/bin:/bin", "PYTHONPATH": ".", "PYTHONDONTWRITEBYTECODE": "1", "HOME": str(Path.home())}
    p = subprocess.run([sys.executable, TEST], cwd=tree, env=env, capture_output=True, text=True, timeout=900)
    text = p.stdout + p.stderr
    nodes = sorted({f"{TEST}::{m.group(3)}::{m.group(2)}" for m in PAT.finditer(text)})
    return p.returncode, nodes, text[-3000:]


def main() -> int:
    tree, spec_path, out = Path(sys.argv[1]), Path(sys.argv[2]), Path(sys.argv[3])
    spec = json.loads(spec_path.read_text())
    rc, nodes, tail = run(tree)
    result = {"baseline": {"rc": rc, "nodes": nodes, "tail": tail}, "mutations": []}
    if rc != 0 or nodes:
        out.write_text(json.dumps(result, ensure_ascii=False, indent=1))
        print("baseline not green; abort", rc, nodes)
        return 2
    for m in spec["mutations"]:
        originals = {}
        try:
            for r in m["replacements"]:
                f = tree / r["file"]
                if r["file"] not in originals:
                    originals[r["file"]] = f.read_bytes()
                text = f.read_text()
                if text.count(r["old"]) != 1:
                    raise ValueError(f"old not unique in {r['file']}: {text.count(r['old'])}")
                f.write_text(text.replace(r["old"], r["new"], 1))
            rc, nodes, tail = run(tree)
            status = "KILLED" if nodes else "SURVIVED"
            entry = {"id": m["id"], "rc": rc, "observed_nodes": nodes, "status": status,
                     "expected_status": m["expected_status"], "expected_nodes": sorted(m["expected_nodes"]),
                     "exact_match": sorted(m["expected_nodes"]) == nodes}
            if not nodes and rc != 0:
                entry["tail"] = tail
        except Exception as exc:  # noqa: BLE001 - probe records and continues
            entry = {"id": m["id"], "error": repr(exc)}
        finally:
            for name, data in originals.items():
                (tree / name).write_bytes(data)
                if hashlib.sha256((tree / name).read_bytes()).hexdigest() != hashlib.sha256(data).hexdigest():
                    raise SystemExit(f"restore failed for {name}")
        result["mutations"].append(entry)
        print(entry["id"], entry.get("status"), entry.get("exact_match"), entry.get("error", ""), flush=True)
    out.write_text(json.dumps(result, ensure_ascii=False, indent=1))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
```
