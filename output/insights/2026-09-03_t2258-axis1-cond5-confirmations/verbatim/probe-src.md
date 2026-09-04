# 親が使った probe の逐語ソース

repo 外 (job tmp) に置いた使い捨て probe である。凍結 bundle と repo 内の catalog を
読むだけで書き込みはしない。出力は `verbatim/measure-*.md` に対応する。

## premise.py — 実測 1 — leaf ごとの rows / distinct / 申告総数 / 重複内訳と、attempt 間の集合差

```python
import gzip, json, re, sys
from collections import Counter, defaultdict
from pathlib import Path

B = Path("/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle")
RAW = B / "raw"
pat = re.compile(r"^(?P<leaf>.+)_p(?P<page>\d+)\.a(?P<att>\d+)\.body\.gz$")

runs = defaultdict(dict)  # (leaf, att) -> {page: path}
for p in sorted(RAW.iterdir()):
    m = pat.match(p.name)
    if not m:
        print("UNMATCHED", p.name); continue
    runs[(m.group("leaf"), int(m.group("att")))][int(m.group("page"))] = p

print(f"runs: {len(runs)}")
summary = {}
for key in sorted(runs):
    pages = runs[key]
    ords = sorted(pages)
    assert ords == list(range(len(ords))), (key, ords)
    ids = []
    counts = []
    per_page = []
    for o in ords:
        d = json.loads(gzip.open(pages[o]).read())
        counts.append(d["meta"]["count"])
        pids = [r["id"] for r in d["results"]]
        per_page.append(pids)
        ids.extend(pids)
    c = Counter(ids)
    dup_occ = sum(v - 1 for v in c.values() if v > 1)
    # page-boundary duplicate: same id in adjacent pages
    boundary = 0
    for i in range(len(per_page) - 1):
        boundary += len(set(per_page[i]) & set(per_page[i + 1]))
    within = sum(1 for pids in per_page for k, v in Counter(pids).items() if v > 1 for _ in range(v - 1))
    nonadjacent = dup_occ - boundary - within
    summary[key] = dict(pages=len(ords), rows=len(ids), distinct=len(c),
                        declared=sorted(set(counts)), dup_occ=dup_occ,
                        boundary=boundary, within=within, nonadjacent=nonadjacent,
                        idset=set(c))
    print(f"{key[0]} a{key[1]:02d}: pages={len(ords)} rows={len(ids)} distinct={len(c)} "
          f"declared={sorted(set(counts))} dup_occ={dup_occ} boundary_pairs={boundary} "
          f"within_page={within} nonadjacent={nonadjacent} distinct-declared={len(c)-counts[0]}")

print()
print("=== cross-attempt comparison ===")
leaves = defaultdict(list)
for (leaf, att) in summary:
    leaves[leaf].append(att)
for leaf, atts in sorted(leaves.items()):
    if len(atts) < 2:
        continue
    a, b = sorted(atts)[:2]
    sa, sb = summary[(leaf, a)]["idset"], summary[(leaf, b)]["idset"]
    only_a, only_b = sa - sb, sb - sa
    print(f"{leaf}: |a{a:02d}|={len(sa)} |a{b:02d}|={len(sb)} inter={len(sa&sb)} "
          f"only_a{a:02d}={len(only_a)} only_a{b:02d}={len(only_b)} "
          f"declared_a{a:02d}={summary[(leaf,a)]['declared']} declared_a{b:02d}={summary[(leaf,b)]['declared']}")
    for x in sorted(only_a)[:10]:
        print(f"    only in a{a:02d}: {x}")
    for x in sorted(only_b)[:10]:
        print(f"    only in a{b:02d}: {x}")
```

## mech.py — 実測 2 — 頁ごとの first / last / next_cursor、境界重複の位置、差分 ID の素性

```python
import base64, gzip, json, re
from collections import Counter, defaultdict
from pathlib import Path

B = Path("/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle")
RAW = B / "raw"
pat = re.compile(r"^(?P<leaf>.+)_p(?P<page>\d+)\.a(?P<att>\d+)\.body\.gz$")
runs = defaultdict(dict)
for p in sorted(RAW.iterdir()):
    m = pat.match(p.name)
    runs[(m.group("leaf"), int(m.group("att")))][int(m.group("page"))] = p

def load(key):
    pages = runs[key]
    out = []
    for o in sorted(pages):
        out.append(json.loads(gzip.open(pages[o]).read()))
    return out

def key_of(r):
    return (r.get("relevance_score"), r.get("publication_date"), r["id"])

for key in [("AX1-20260902-E1-Q1@openalex",1),("AX1-20260902-E1-Q1@openalex",2),
            ("AX1-20260902-E1-Q2@openalex",1),("AX1-20260902-E1-Q2@openalex",2)]:
    ds = load(key)
    print(f"=== {key[0]} a{key[1]:02d} pages={len(ds)} ===")
    for i, d in enumerate(ds):
        res = d["results"]
        cur = d["meta"].get("next_cursor")
        dec = None
        if cur:
            try: dec = base64.b64decode(cur).decode()
            except Exception: dec = "?"
        last = res[-1]["id"] if res else None
        print(f"  p{i}: n={len(res)} first={res[0]['id'] if res else None} last={last} next_cursor={dec}")
    # boundary duplicates
    for i in range(len(ds)-1):
        a = [r["id"] for r in ds[i]["results"]]
        b = [r["id"] for r in ds[i+1]["results"]]
        ov = set(a) & set(b)
        if ov:
            for x in ov:
                print(f"  DUP across p{i}/p{i+1}: {x} posA={a.index(x)}/{len(a)} posB={b.index(x)}/{len(b)}")
    print()

# locate the differing IDs
for leaf in ["AX1-20260902-E1-Q1@openalex", "AX1-20260902-E1-Q2@openalex"]:
    d1, d2 = load((leaf,1)), load((leaf,2))
    s1 = {r["id"] for d in d1 for r in d["results"]}
    s2 = {r["id"] for d in d2 for r in d["results"]}
    for tag, only, ds in (("only-a01", s1-s2, d1), ("only-a02", s2-s1, d2)):
        for wid in only:
            for i, d in enumerate(ds):
                for j, r in enumerate(d["results"]):
                    if r["id"] == wid:
                        print(f"{leaf} {tag} {wid}: page={i} ordinal={j}/{len(d['results'])} "
                              f"rel={r.get('relevance_score')} pubdate={r.get('publication_date')} "
                              f"created={r.get('created_date')} updated={(r.get('updated_date') or '')[:19]}")
                        print(f"    title={str(r.get('title'))[:90]}")
```

## digest.py — 実測 3 — production の primary_key_digest 定義の再現と独立再走の一致検査

```python
"""P1-4 の裏取り: production の primary_key_digest 定義を再現し、独立再走の digest が一致するか測る。

定義の出所: orchestrator/axis1_search/runner.py の _write_ledger
    primary_payload = "".join(f"{item}\n" for item in sorted(set(work_ids))).encode("utf-8")
    primary_key_digest = sha256(primary_payload).hexdigest()
"""

import gzip
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

BUNDLE = Path("/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle")
RAW = BUNDLE / "raw"
PAT = re.compile(r"^(?P<leaf>.+)_p(?P<page>\d+)\.a(?P<att>\d+)\.body\.gz$")


def load_runs():
    runs = defaultdict(dict)
    for path in sorted(RAW.iterdir()):
        m = PAT.match(path.name)
        runs[(m.group("leaf"), int(m.group("att")))][int(m.group("page"))] = path
    return runs


def work_ids(pages):
    ids = []
    for ordinal in sorted(pages):
        body = json.loads(gzip.open(pages[ordinal]).read())
        ids.extend(r["id"] for r in body["results"])
    return ids


def primary_key_digest(ids):
    payload = "".join(f"{item}\n" for item in sorted(set(ids))).encode("utf-8")
    return hashlib.sha256(payload).hexdigest()


def main():
    runs = load_runs()
    per_leaf = defaultdict(dict)
    for (leaf, att), pages in runs.items():
        ids = work_ids(pages)
        per_leaf[leaf][att] = (primary_key_digest(ids), len(set(ids)), len(pages))

    print("=== primary_key_digest (production 定義の再現) ===")
    for leaf in sorted(per_leaf):
        for att in sorted(per_leaf[leaf]):
            digest, distinct, npages = per_leaf[leaf][att]
            print(f"{leaf} a{att:02d}: pages={npages} distinct={distinct} digest={digest}")

    print()
    print("=== 独立再走の digest 一致 (条件 5 の第 2 走要求と同じ関数) ===")
    for leaf in sorted(per_leaf):
        atts = sorted(per_leaf[leaf])
        if len(atts) < 2:
            continue
        a, b = atts[0], atts[1]
        da, db = per_leaf[leaf][a][0], per_leaf[leaf][b][0]
        npages = per_leaf[leaf][a][2]
        print(f"{leaf}: pages={npages} a{a:02d}=={b and ''}a{b:02d} -> {'MATCH' if da == db else 'MISMATCH'}")

    print()
    print("=== 頁数と gap の対応 (gap = declared - distinct) ===")
    print("gap は差そのものであって『取りこぼした件数』ではない。")
    print("その解釈には失敗走の申告母集合が固定されていることが要り、本 bundle からは言えない。")
    single, multi = [], []
    for leaf in sorted(per_leaf):
        for att in sorted(per_leaf[leaf]):
            pages = runs[(leaf, att)]
            first = json.loads(gzip.open(pages[0]).read())
            declared = first["meta"]["count"]
            _, distinct, npages = per_leaf[leaf][att]
            gap = declared - distinct
            row = (leaf, att, npages, declared, distinct, gap)
            (single if npages == 1 else multi).append(row)
            print(f"{leaf} a{att:02d}: pages={npages} declared={declared} distinct={distinct} gap={gap}")

    def tally(rows, label):
        ok = sum(1 for r in rows if r[5] == 0)
        print(f"{label}: {ok}/{len(rows)} 走が gap 0 (保証ではなく、この bundle での観測)")

    print()
    tally(single, "1 頁 leaf")
    tally(multi, "多頁 leaf")


if __name__ == "__main__":
    main()
```

## boundary.py — 実測 4 — 申告総数の到達可能性と、非返却 record の境界位置

```python
"""非返却 record が頁境界に位置するかを測り、代替仮説 (申告総数が実在しない record を数えている)
を凍結 bundle だけで切り分ける。
"""

import ast
import base64
import gzip
import json
import re
from collections import defaultdict
from pathlib import Path

BUNDLE = Path("/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle")
RAW = BUNDLE / "raw"
PAT = re.compile(r"^(?P<leaf>.+)_p(?P<page>\d+)\.a(?P<att>\d+)\.body\.gz$")


def load_runs():
    runs = defaultdict(dict)
    for path in sorted(RAW.iterdir()):
        m = PAT.match(path.name)
        runs[(m.group("leaf"), int(m.group("att")))][int(m.group("page"))] = path
    return runs


def pages_of(runs, key):
    return [json.loads(gzip.open(runs[key][o]).read()) for o in sorted(runs[key])]


def cursor_key(page):
    """next_cursor は base64 の中に「JSON 文字列に包まれた配列リテラル」が入る二重構造である。
    1 度の literal_eval では文字列が返るので 2 度剥がす。"""
    raw = page["meta"].get("next_cursor")
    if not raw:
        return None
    decoded = ast.literal_eval(base64.b64decode(raw).decode())
    if isinstance(decoded, str):
        decoded = ast.literal_eval(decoded)
    return decoded


def main():
    runs = load_runs()

    print("=== 代替仮説の切り分け: 申告総数は到達可能か ===")
    print("同じ leaf の別の走が申告総数ちょうどの distinct を返していれば、")
    print("その申告総数は実在 record だけで満たせる = 幻の件数ではない。")
    per_leaf = defaultdict(list)
    for (leaf, att) in runs:
        pages = pages_of(runs, (leaf, att))
        declared = pages[0]["meta"]["count"]
        distinct = len({r["id"] for p in pages for r in p["results"]})
        per_leaf[leaf].append((att, declared, distinct))
    for leaf in sorted(per_leaf):
        rows = sorted(per_leaf[leaf])
        best = max(d for _, _, d in rows)
        declared = rows[0][1]
        verdict = "到達可能 (幻でない)" if best == declared else "未到達 (幻を排除できない)"
        print(f"{leaf}: declared={declared} 最良 distinct={best} -> {verdict}")

    print()
    print("=== 非返却 record は頁境界にあるか ===")
    for leaf in ["AX1-20260902-E1-Q1@openalex", "AX1-20260902-E1-Q2@openalex"]:
        p1, p2 = pages_of(runs, (leaf, 1)), pages_of(runs, (leaf, 2))
        s1 = {r["id"] for p in p1 for r in p["results"]}
        s2 = {r["id"] for p in p2 for r in p["results"]}
        for tag, only, having, lacking in (
            ("a01 のみ", s1 - s2, p1, p2),
            ("a02 のみ", s2 - s1, p2, p1),
        ):
            for wid in sorted(only):
                for i, page in enumerate(having):
                    for j, r in enumerate(page["results"]):
                        if r["id"] != wid:
                            continue
                        n = len(page["results"])
                        dist_start, dist_end = j, n - 1 - j
                        at_boundary = min(dist_start, dist_end) <= 1
                        print(f"{leaf} {tag} {wid}")
                        print(f"    返した走での位置: 頁 {i} の {j}/{n} "
                              f"(頁頭から {dist_start}、頁尾から {dist_end}) "
                              f"-> 境界隣接: {at_boundary}")
                        print(f"    その走の score={r.get('relevance_score')}")
                        if i > 0:
                            print(f"    直前頁の cursor 鍵={cursor_key(having[i-1])}")
                        if i < len(having) - 1:
                            print(f"    この頁の cursor 鍵={cursor_key(having[i])}")
                        # 落とした走の対応する境界
                        print(f"    落とした走の同じ境界付近の cursor 鍵:")
                        for k in range(max(0, i - 1), min(len(lacking), i + 1)):
                            print(f"      頁 {k} -> {cursor_key(lacking[k])}")

    print()
    print("=== 境界重複は隣接頁の末尾/先頭に集中するか ===")
    for key in sorted(runs):
        pages = pages_of(runs, key)
        for i in range(len(pages) - 1):
            a = [r["id"] for r in pages[i]["results"]]
            b = [r["id"] for r in pages[i + 1]["results"]]
            for wid in set(a) & set(b):
                ia, ib = a.index(wid), b.index(wid)
                print(f"{key[0]} a{key[1]:02d} 頁{i}/{i+1}: {wid} "
                      f"前頁の頁尾から {len(a)-1-ia}、次頁の頁頭から {ib}")


if __name__ == "__main__":
    main()
```

## tuple.py — 実測 5 — 境界重複 record の三つ組比較と 2 走間の score 差分

```python
"""レンズ A が提案した切り分け: 頁境界で重複した record の
(relevance_score, publication_date, id) 三つ組を、前頁・cursor 鍵・次頁で突き合わせる。

- 次頁で三つ組が cursor 鍵を跨いで変わっていれば -> 走査中の再採点を直接支持する
- 三つ組が同一のまま cursor 鍵と一致して再出現するなら -> inclusive cursor / replay が代替説明
"""

import ast
import base64
import gzip
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BUNDLE = Path("/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle")
RAW = BUNDLE / "raw"
PAT = re.compile(r"^(?P<leaf>.+)_p(?P<page>\d+)\.a(?P<att>\d+)\.body\.gz$")


def load_runs():
    runs = defaultdict(dict)
    for path in sorted(RAW.iterdir()):
        m = PAT.match(path.name)
        runs[(m.group("leaf"), int(m.group("att")))][int(m.group("page"))] = path
    return runs


def pages_of(runs, key):
    return [json.loads(gzip.open(runs[key][o]).read()) for o in sorted(runs[key])]


def cursor_key(page):
    """next_cursor は base64 の中に「JSON 文字列に包まれた配列リテラル」が入る二重構造である。

    base64 復号すると `"[0.76, 1600819200000, 'https://openalex.org/W3089320326']"` のように
    外側の二重引用符ごと出てくる。1 度の literal_eval では**文字列**が返り、添字は文字になる。
    2 度剥がして初めて三つ組になる。
    """
    raw = page["meta"].get("next_cursor")
    if not raw:
        return None
    decoded = ast.literal_eval(base64.b64decode(raw).decode())
    if isinstance(decoded, str):
        decoded = ast.literal_eval(decoded)
    return decoded


def triple(record):
    return (record.get("relevance_score"), record.get("publication_date"), record["id"])


def main():
    runs = load_runs()
    changed = same = 0
    cursor_equal = 0
    rows = []
    for key in sorted(runs):
        pages = pages_of(runs, key)
        for i in range(len(pages) - 1):
            prev_by_id = {r["id"]: r for r in pages[i]["results"]}
            ck = cursor_key(pages[i])
            for r in pages[i + 1]["results"]:
                if r["id"] not in prev_by_id:
                    continue
                before = triple(prev_by_id[r["id"]])
                after = triple(r)
                is_same = before == after
                same += is_same
                changed += not is_same
                on_cursor = ck is not None and ck[2] == r["id"]
                cursor_equal += on_cursor
                rows.append((key, i, r["id"], before, after, is_same, on_cursor, ck))

    print("=== 頁境界で重複した record の三つ組比較 ===")
    print(f"重複 occurrence 総数: {same + changed}")
    print(f"  三つ組が同一のまま再出現: {same}")
    print(f"  三つ組が変わって再出現:   {changed}")
    print(f"  そのうち前頁の cursor 鍵の ID と一致: {cursor_equal}")
    print()
    for key, i, wid, before, after, is_same, on_cursor, ck in rows:
        tag = "同一" if is_same else "変化"
        print(f"{key[0]} a{key[1]:02d} 頁{i}->{i+1} {wid}")
        print(f"    前頁: score={before[0]} date={before[1]}")
        print(f"    次頁: score={after[0]} date={after[1]}   三つ組={tag}")
        print(f"    前頁 cursor 鍵 = {ck}")
        print(f"    cursor 鍵の ID と一致: {on_cursor}")

    print()
    print("=== 2 走に共通する ID の score 差分 (Q1 / Q2) ===")
    for leaf in ["AX1-20260902-E1-Q1@openalex", "AX1-20260902-E1-Q2@openalex"]:
        a = {r["id"]: r.get("relevance_score")
             for p in pages_of(runs, (leaf, 1)) for r in p["results"]}
        b = {r["id"]: r.get("relevance_score")
             for p in pages_of(runs, (leaf, 2)) for r in p["results"]}
        common = set(a) & set(b)
        diff = [wid for wid in common if a[wid] != b[wid]]
        print(f"{leaf}: 共通 ID={len(common)} score が変わった ID={len(diff)} "
              f"({100.0 * len(diff) / max(len(common), 1):.1f}%)")
        if diff:
            sample = sorted(diff)[:5]
            for wid in sample:
                print(f"    {wid}: {a[wid]} -> {b[wid]}")
            rel = [abs(a[w] - b[w]) / max(abs(a[w]), 1e-12) for w in diff
                   if isinstance(a[w], (int, float)) and isinstance(b[w], (int, float))]
            if rel:
                rel.sort()
                print(f"    相対差 中央値={rel[len(rel)//2]:.3e} 最大={rel[-1]:.3e}")


if __name__ == "__main__":
    main()
```

## chain.py — 実測 6 — page evidence の field による走の連続性・独立性検査

```python
"""レンズ A 所見 5 への対応: probe が束ねた「走」が production の page evidence 上でも
首尾一貫した 1 本の走査であることを、証拠側の field で確かめる。

検査する束縛:
  - identity の epoch / catalog_sha256 / registration_commit / leaf_query_id / pass_number
  - 頁 0 の request.position_in が cursor 先頭 ("*") であること (= 先頭からの独立走)
  - 頁 n (n>0) の request.parent_response_sha256 が 頁 n-1 の response.sha256 と一致すること
  - 頁 n の request.position_in が 頁 n-1 の parse.position_out と一致すること
  - response.status と保存 body の sha256 が一致すること
"""

import gzip
import hashlib
import json
import re
from collections import defaultdict
from pathlib import Path

BUNDLE = Path("/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle")
PAGES = BUNDLE / "pages"
PAT = re.compile(r"^(?P<leaf>.+)_p(?P<page>\d+)\.a(?P<att>\d+)\.json$")


def load():
    runs = defaultdict(dict)
    for path in sorted(PAGES.iterdir()):
        m = PAT.match(path.name)
        if not m:
            print("UNMATCHED", path.name)
            continue
        runs[(m.group("leaf"), int(m.group("att")))][int(m.group("page"))] = path
    return runs


def main():
    runs = load()
    print(f"評価対象の走: {len(runs)}")
    all_ok = True
    for key in sorted(runs):
        pages = [json.load(open(runs[key][o])) for o in sorted(runs[key])]
        problems = []

        ident = pages[0]["identity"]
        for field in ("catalog_sha256", "registration_commit", "leaf_query_id",
                      "logical_query_id", "pass_number", "attempt_number", "index"):
            values = {p["identity"].get(field) for p in pages}
            if len(values) != 1:
                problems.append(f"identity.{field} が頁間で不一致: {values}")

        if pages[0]["request"].get("position_in") != "*":
            problems.append(f"頁 0 が先頭でない: position_in={pages[0]['request'].get('position_in')!r}")

        for i in range(1, len(pages)):
            prev, cur = pages[i - 1], pages[i]
            if cur["request"].get("parent_response_sha256") != prev["response"].get("sha256"):
                problems.append(f"頁 {i}: parent_response_sha256 が前頁の response.sha256 と不一致")
            if cur["request"].get("position_in") != prev["parse"].get("position_out"):
                problems.append(f"頁 {i}: position_in が前頁の position_out と不一致")

        for i, p in enumerate(pages):
            if p["response"].get("status") != 200:
                problems.append(f"頁 {i}: status={p['response'].get('status')}")
            body = BUNDLE / p["response"]["body_path"]
            if not body.exists():
                problems.append(f"頁 {i}: body 不在 {p['response']['body_path']}")
                continue
            # evidence の sha256 / byte_count は非圧縮の応答 bytes に対する値である
            # (保存は gzip)。実測で確認済み。
            decoded = gzip.decompress(body.read_bytes())
            if len(decoded) != p["response"].get("byte_count"):
                problems.append(f"頁 {i}: 非圧縮 byte 数が evidence と不一致")
            if hashlib.sha256(decoded).hexdigest() != p["response"].get("sha256"):
                problems.append(f"頁 {i}: 非圧縮 body の sha256 が evidence と不一致")

        verdict = "OK" if not problems else "NG"
        all_ok &= not problems
        print(f"{key[0]} a{key[1]:02d}: 頁数={len(pages)} pass={ident.get('pass_number')} "
              f"attempt={ident.get('attempt_number')} 先頭={pages[0]['request'].get('position_in')!r} -> {verdict}")
        for item in problems:
            print(f"    {item}")

    print()
    print("全走が先頭からの首尾一貫した独立走として検査を通った" if all_ok else "検査に失敗した走がある")


if __name__ == "__main__":
    main()
```

## crosscheck.py — 実測 7 — 凍結実行記録・checkpoint・catalog との照合と、条件 5 の現在の状態

```python
"""レビュー A 所見 4 への対応: 本文が主張する照合値を、実際に生成する。

1. 凍結実行記録 §3 の表と probe の rows / distinct / 境界重複の一致
2. bundle の checkpoint が持つ production の primary_key_digest と probe 再現値の一致
3. catalog の leaf 件数、independent_pass_required の真偽別件数、未走 leaf 件数
"""

import gzip
import hashlib
import json
import re
from collections import Counter, defaultdict
from pathlib import Path

BUNDLE = Path("/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle")
RAW = BUNDLE / "raw"
CHECKPOINTS = BUNDLE / "checkpoints"
CATALOG = Path(
    "/work/1/SFC/tanab/izanagi/.claude/worktrees/"
    "dev-wave-t2258-axis1-cond5-confirmations/"
    "docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json"
)
PAT = re.compile(r"^(?P<leaf>.+)_p(?P<page>\d+)\.a(?P<att>\d+)\.body\.gz$")

# 凍結実行記録 docs/related-work/claim-survey/2026-09-03-axis1-search-execution.md §3 の表を
# 逐語で写したもの。leaf -> (申告総数, 取得行数, distinct, 頁境界の重複)
RECORD_TABLE = {
    ("AX1-20260902-E1-Q1@openalex", 1): (736, 736, 736, 0),
    ("AX1-20260902-E1-Q2@openalex", 1): (1606, 1607, 1605, 2),
    ("AX1-20260902-E1-Q4@openalex", 1): (4698, 4705, 4694, 11),
    ("AX1-20260902-E1-Q5@openalex", 1): (6122, 6130, 6116, 14),
}


def load_runs():
    runs = defaultdict(dict)
    for path in sorted(RAW.iterdir()):
        m = PAT.match(path.name)
        runs[(m.group("leaf"), int(m.group("att")))][int(m.group("page"))] = path
    return runs


def measure(pages):
    per_page, ids, counts = [], [], []
    for ordinal in sorted(pages):
        body = json.loads(gzip.open(pages[ordinal]).read())
        counts.append(body["meta"]["count"])
        page_ids = [r["id"] for r in body["results"]]
        per_page.append(page_ids)
        ids.extend(page_ids)
    boundary = sum(
        len(set(per_page[i]) & set(per_page[i + 1])) for i in range(len(per_page) - 1)
    )
    payload = "".join(f"{item}\n" for item in sorted(set(ids))).encode("utf-8")
    return {
        "declared": sorted(set(counts)),
        "rows": len(ids),
        "distinct": len(set(ids)),
        "boundary": boundary,
        "digest": hashlib.sha256(payload).hexdigest(),
    }


def main():
    runs = load_runs()
    measured = {key: measure(pages) for key, pages in runs.items()}

    print("=== 1. 凍結実行記録 §3 の表との照合 ===")
    ok = True
    for key, (declared, rows, distinct, boundary) in RECORD_TABLE.items():
        got = measured[key]
        want = (declared, rows, distinct, boundary)
        have = (got["declared"][0], got["rows"], got["distinct"], got["boundary"])
        match = want == have
        ok &= match
        print(f"{key[0]} a{key[1]:02d}: 記録={want} probe={have} -> {'一致' if match else '不一致'}")
    print(f"照合対象 {len(RECORD_TABLE)} 件: {'全件一致' if ok else '不一致あり'}")

    print()
    print("=== 2. checkpoint の production digest との照合 ===")
    ok = True
    n = 0
    for path in sorted(CHECKPOINTS.iterdir()):
        data = json.load(open(path))
        leaf = data.get("leaf_query_id")
        want = data.get("completed_ledger", {}).get("primary_key_digest")
        have = measured[(leaf, 1)]["digest"]
        match = want == have
        ok &= match
        n += 1
        print(f"{path.name} {leaf}: production={want[:16]}… probe={have[:16]}… "
              f"-> {'一致' if match else '不一致'}")
    print(f"照合対象 {n} 件: {'全件一致' if ok else '不一致あり'}")

    print()
    print("=== 3. catalog の leaf 件数と independent_pass_required ===")
    catalog = json.load(open(CATALOG))
    openalex = [q for q in catalog["logical_queries"] if q.get("index") == "openalex"]
    kinds = Counter(q.get("kind") for q in openalex)
    flags = Counter(q["independent_pass_required"] for q in openalex)
    leaves = [q for q in openalex if q.get("kind") == "leaf"]
    ran = {leaf for (leaf, _) in runs}
    unrun = [q for q in leaves if q["query_id"] not in ran]
    print(f"OpenAlex の論理 query: {len(openalex)} 件 (内訳 {dict(kinds)})")
    print(f"  independent_pass_required=True : {flags[True]} 件")
    print(f"  independent_pass_required=False: {flags[False]} 件")
    print("  False の内訳:")
    for q in openalex:
        if not q["independent_pass_required"]:
            print(f"    {q['query_id']}")
    print(f"登録 leaf: {len(leaves)} 件 / 走行のある leaf: {len(ran)} 件 / 未走 leaf: {len(unrun)} 件")

    print()
    print("=== 4. 条件 5 の現在の状態 (検査器は最後の attempt を採る) ===")
    print("gap = declared - distinct。最後の attempt の gap が 0 でない leaf が現在の不成立である。")
    failing = []
    for leaf in sorted({leaf for (leaf, _) in runs}):
        last = max(att for (name, att) in runs if name == leaf)
        got = measured[(leaf, last)]
        gap = got["declared"][0] - got["distinct"]
        mark = "" if gap == 0 else "  <- 条件 5 不成立"
        if gap:
            failing.append(leaf)
        print(f"{leaf}: 最終 attempt=a{last:02d} gap={gap}{mark}")
    print(f"現在 条件 5 が不成立の leaf: {len(failing)} 件 -> {failing}")


if __name__ == "__main__":
    main()
```
