---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-12
wave: dev-wave-t950-acceptance-floor
seq: 2
---

## {{D:prefilter-binds-to-actual-expressions}}. 検索の前置フィルタは実際に compile する式へ束縛する

**決定:** 三軸検索の必要条件 literal は、**その scan が実際に compile する `expressions` から**
導出する。module の template 定数から導出してはならない。導出できない文法に出会ったら
`None` を返し、その scan は前置フィルタなしで従来経路を走る。

**理由:**

- 式は template から `_expressions` が作るが、`_expressions` は monkeypatch 可能な seam であり、
  テストが現に patch している。template 由来の literal と実際に compile される式が別物になると、
  前置フィルタが**正しい hit を捨てる** = 受理集合が変わる。段 3 の敵対レンズが反例を構成した。
- 同じ理由で、compile と導出は**同一 snapshot** に束縛する。`items()` と `values()` を別に読むと、
  不安定な `Mapping` で両者が食い違う。段 6 の敵対レビューが反例を構成した。
- 値側は導出に使わない。値は正規表現であり、任意 1 文字に一致するメタ文字を含みうる。
  値を literal 扱いすると、正規表現には一致するのに literal を含まない text を捨てる。

**却下した選択肢:**

- **template から導出して scan 間で共有する** — 起草段の案。共有は速いが、上記の seam により
  受理集合が変わりうる。安全側を採り、scan ごとに独立導出する。
- **必要 literal をソースへ直接書く** — 具体的な軸符号化はソースに書けない
  (repo 全文検索が自己汚染するため既存の source guard が禁じている)。また template が変われば黙って壊れる。
- **速度のために正規表現を literal 一致へ置き換える** — 値のメタ文字を無視することになり
  受理集合が狭まる。

## {{D:prefilter-safety-rests-on-slow-path-equivalence}}. 前置フィルタの安全性は独立 slow 経路との bytes 一致で担保する

**決定:** 検索の最適化が受理集合を変えていないことの根拠は、**導出器を無効化した独立 slow 経路との
全 report の canonical bytes 一致**に置く。live gate の通過を根拠にしてはならない。

**理由:**

- live gate が固定するのは (a) candidate 集合、(b) 照合規約、(c) 検索式、
  (d) holdout の conjunction が空、(e) 陽性対照の hit が 0 より大きい、の 5 点だけである。
  `per_axis_counts` と `result_sha256` は live では照合されない。
- 段 3 の敵対レンズが具体的な反例を構成した。必要 literal を「固定陽性対照だけが含む形」に
  固定すると、陽性対照の hit を残したまま通常形式の holdout hit を落とせる。
  凍結側の陽性対照は 41 hit あり、`> 0` の条件は容易に残る。**oracle gate は騙せる。**
- したがって等価テストが唯一の検出者である。変異検査でこの検出力自体を裏取りする。

**却下した選択肢:**

- **live gate の通過を証拠にする** — 上記の反例により不十分。
- **live 値と凍結値の完全一致を要求する** — 凍結側の `per_axis_counts` と陽性対照件数は
  経時変動を許す契約になっている。要求するとその契約を壊す。
- **等価テストを実 repo で走らせる** — 開発するほど遅くなるテストを新設することになる。
  固定 fixture に限定する。
