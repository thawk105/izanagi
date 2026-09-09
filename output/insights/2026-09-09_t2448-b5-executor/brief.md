# 段 1 brief — [T-2448] 軸 B5 の実行器 (parser・fixture・schema・runner)

- wave: `dev-wave-t2448-b5-executor` / branch `worktree-dev-wave-t2448-b5-executor` / 起点 main `7f17e1c63`
- 実測環境: login node `pegasus02`。受入は `tools/dev_wave_wait.py acceptance`、test は `tools/run_tests.py`。

## 研究前進

軸 B5 は `RW0`。閉包記録 (`2026-09-08-backoff-axis-b5-closure-record.md` §0) は実行前に残るものを 3 つ挙げ、
そのうち **(a) 部分登録 §5.3 の registration preflight は「実行器が未実装」だけを理由に閉じていない**。
本 wave が実行器を作れば (a) が閉じ、(b) live preflight と (c) 人間の実行認可だけが残る。
完了判定: 親が registration preflight を実データで 1 回通して rc=0 を得ること、および live preflight が
3 索引 30 member の ID lookup request を anchor 表と登録 request 形から組み立てられることを fixture で示すこと。

## 確定済みユーザー裁定

- **D1895**: 軸 B5 は登録どおり走らせ、走行前に語彙を緩めない。→ 検索語彙・除外規則・枝・cutoff を触らない。
- **D95 決定 2**: 実装面は Codex `role=author` が書く。親は `orchestrator/**` の非 .md を直接編集しない。

## 不変条件 (破ったら停止)

1. `docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json` の bytes 不変
   (SHA-256 `7eb8385e35bd24edac8a227a72ba5bc6b568ca8bc7cac2c8250af8b4ea4c346f` を `test_axis_b5_search_catalog.py:29` が pin)。
2. `orchestrator/axis_b5_search/catalog.py`・3 つの凍結事前登録 md の bytes 不変。
3. 語彙・ブロック所属・枝・cutoff・control anchor・補助探索範囲・完走述語を実行器側で緩めない (D1895、部分登録 §5.4)。
4. **live preflight を本 wave で実行しない** — 実行は人間の認可事項 (閉包記録 §0 (c))。本 wave は network-zero。
5. 観測値をそのまま期待値に据えない (部分登録 §2.3、§5.3)。fixture は過去の生応答をそのまま置くだけとし、
   期待 echo・期待 AST は凍結文の逐語から独立に書く。
6. 規律 2: 完走述語を通りやすくする実装 (実要素数の代わりに `meta.per_page` を使う等) を採らない。

## scope (成果物 6 点)

| # | 成果物 | 放置したときの成果物影響 (DW-G05) |
|---|---|---|
| S1 | `orchestrator/axis_b5_search/parsers.py` | 応答から索引固有 work ID・実要素数・位置値を取れず、実行記録 (部分登録 §7) の全 field が空になる |
| S2 | `orchestrator/axis_b5_search/preflight.py` (registration + live) | registration preflight が閉じず、閉包記録 §0 (a) が残り続けて軸は `RW0` から動かない |
| S3 | `orchestrator/axis_b5_search/runner.py` (leaf 実行・6 完走条件・証拠出力) | 1622 query の `完走`/`未完走` を判定できず、部分登録 §5.2 の論理積を 1 行も評価できない |
| S4 | `orchestrator/schemas/axis_b5_search_*.schema.json` | 実行記録の型が固定されず、後続 wave が field を後付けして事後登録になる |
| S5 | `orchestrator/tests/fixtures/axis_b5_search/` | parser・runner の正例/負例が実応答に接地せず、恒真な緑になる |
| S6 | `orchestrator/tests/test_axis_b5_search_executor.py` + 受入台帳行 | 受入で自走 harness 不在と台帳欠落の 2 件が赤になる |

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- **(P1)** 軸 B5 は `orchestrator/axis1_search/parsers.py` を import せず、自前の parser を持つ。
  理由: registration preflight は parser の bytes を seal するので、import すると軸 1 の凍結物へ seal が結合し、
  軸 1 側の amendment が軸 B5 の登録を黙って壊す。反論があれば段 3 で出す。
- **(P2)** 軸 1 の `runner.py` は再利用しない。軸 1 の runner は page size・retry・content type を
  catalog document から読むが、**軸 B5 の catalog は bytes 凍結済みでこれらの field を持たない**。
  よって B5 の実行方針は凍結文から逐語で転記した実行器側の定数とし、その bytes を §5.3 が seal する。
- **(P3)** checkpoint / resume (部分登録 §5.3 の「窓をまたぐ実行」、7.7.8) は本 wave の scope 外。
  依頼が列挙した 4 点に含まれず、無くても registration preflight は閉じる。次 wave の題として記録する。

## gate 入力の実在と値域 (DW-O13)

本 wave は 2 つの判定器を新設する。どちらも述語は**凍結文からの転記**であり、親が設計するものではない。

- **registration preflight:** 入力は repo 内 file の bytes。実在する。要求値 (bytes 一致) は到達可能で、
  親が本 wave 中に実データで 1 回通す。
- **live preflight:** 入力は 3 索引の ID lookup 応答。field の実在と値域のうち実測済みなのは、
  OpenAlex の 16/16 `収録` と arXiv member 1 件の `収録` である。
  **DBLP は違う。閉包記録 §2 は anchor 固有 request を 1 本も送っておらず、`不達` は共有 endpoint へ出した
  環境 probe からの外挿だと明記している。13 member の個別 live 値は未観測である。**
  したがって「全 member が `収録`」という要求値が到達可能かは、DBLP については**まだ測っていない**。
  live preflight で 13 本を実際に出すことには情報価値がある。
  DW-O13 に従い、測った範囲と測っていない範囲をここで分けて書く。
  実行器は 3 値をそのまま記録し、`不達` または `非収録` が 1 件でもあれば走行を開始しない。
  通るように緩めてはならない (D1895、規律 2)。

## 分割方針

段 5 は 2 単位。A = S1 + S5 (parser と fixture、応答の読み)、B = S2 + S3 + S4 (preflight・runner・schema、実行と判定)。
S6 は各単位が自分の test を書く。B は A の型 (`ParsedPage` 相当) に依存するので、A の型定義を brief で先に固定して渡す。
