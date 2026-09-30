# 直交表の生成器 (repo 外で実行、逐語)

- 置き場 (repo 外、永続を保証しない): `/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/design/make_design.py`
- sha256: `faefb0e85195926d63b875ab00da57e152ad9d03d3f972d7ed557993cbe7f156`
- 実行: `python3 make_design.py > design.json`。stderr は `S=72 O1=27 O2=27 dup=0`。出力 `design.json` の sha256: `13bc8761fd3b396b6462064e6b49a3c16a701933c08f280aefcff6a38e69016c`
- 経緯: 初版 (sha256 `e8ddb3e5…`) は層 S の長い tx が 2 水準 (48 点) だった。段 4 裁定 R1 で 3 水準に広げ、層 S の行だけを直した。層 O (O1・O2) の 54 点は初版の出力と一致することを照合した。
- 計測で使う条件表の正本は driver `orchestrator/campaign/vhash_cicada_vlife.py` の W 条件であり、driver の test が本生成器と同じ点であることを検査する。

```python
#!/usr/bin/env python3
"""Pre-registration helper (repo 外): layer S grid and two L27 (3^9, strength 2) blocks."""
import itertools, json, sys
from collections import Counter

FACTORS = [
    ("skew", [0.6, 0.9, 0.99]),
    ("rr", [5, 50, 95]),
    ("records", [10000, 100000, 1000000]),
    ("ops", [10, 100, 1000]),
    ("long", ["none", "batchU", "batchR"]),
    ("ro", [0, 50, 95]),
    ("val", [4, 100, 1000]),
    ("threads", [12, 24, 48]),
    ("gc", [10, 1000, 100000]),
]
# columns over GF(3)^3 rows (a,b,c): a, b, c, a+b, a+2b, a+c, a+2c, b+c, b+2c
COLS = [(1,0,0),(0,1,0),(0,0,1),(1,1,0),(1,2,0),(1,0,1),(1,0,2),(0,1,1),(0,1,2)]

def l27():
    rows = []
    for a, b, c in itertools.product(range(3), repeat=3):
        rows.append([(x*a + y*b + z*c) % 3 for x, y, z in COLS])
    return rows

def check_strength2(rows):
    for i, j in itertools.combinations(range(9), 2):
        cnt = Counter((r[i], r[j]) for r in rows)
        if len(cnt) != 9 or set(cnt.values()) != {3}:
            raise SystemExit(f"not strength 2: cols {i},{j}")

def block(rows, perm, shift):
    pts = []
    for r in rows:
        p = {}
        for f, (name, levels) in enumerate(FACTORS):
            p[name] = levels[(r[perm[f]] + shift[f]) % 3]
        pts.append(p)
    return pts

rows = l27()
check_strength2(rows)
o1 = block(rows, list(range(9)), [0]*9)
# block 2: rotate factor->column assignment by 4 and shift levels, fixed before results
o2 = block(rows, [(f + 4) % 9 for f in range(9)], [1, 2, 1, 2, 1, 2, 1, 2, 1])
for pts in (o1, o2):
    for name, levels in FACTORS:
        c = Counter(p[name] for p in pts)
        assert all(c[l] == 9 for l in levels), (name, c)
dups = [p for p in o2 if p in o1]
center = dict(records=1000000, ops=10, ro=0, val=4, threads=48, gc=100)
layer_s = [dict(skew=s, rr=rr, long=l, **center)
           for s in (0.5, 0.6, 0.7, 0.8, 0.9, 0.95, 0.97, 0.99)
           for rr in (5, 50, 95) for l in ("none", "batchU", "batchR")]
out = {"layer_s": layer_s, "layer_o1": o1, "layer_o2": o2, "o1_o2_duplicates": len(dups)}
json.dump(out, sys.stdout, indent=1)
print(file=sys.stderr)
print(f"S={len(layer_s)} O1={len(o1)} O2={len(o2)} dup={len(dups)}", file=sys.stderr)
```
