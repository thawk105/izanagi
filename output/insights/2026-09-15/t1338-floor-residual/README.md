# 2026-09-15 [T-1338] 床値依存の残件は撤去授権が無く、依頼が名指しした 3 件は既に撤去済みだった

```
status: LANDED
machine_effect: NONE   # production 0 byte。受理集合・certified 選択の値・proof 参照はいずれも不変
```

実装なしで閉じた wave の記録。段 2 (プラン) と段 3 の 2 レンズが独立に同じ結論へ到達し、
親の provisional 裁定を支持したうえで、その**根拠を 5 点訂正した**。

## 本 wave が新しく確定したこと

### 1. 依頼引数が名指した 3 件は、前日に撤去済みだった (最重要)

依頼の破線節は「残った 3 件 = per-pair 床値対表の exact 検査 / `floor_budget_snapshot_sha256` /
oracle driver への `expected_perf_sha256` 供給」と書いていた。**この 3 件は 2026-09-14 の wave が
D1985 に従って撤去済みである** (worklog 1479)。破線節は撤去前の持ち越し文
(`docs/archive/worklog-phase3-0818-643.md:597`) の**括弧内をそのまま写していた**。

台帳が記録する実際の残件は別の 3 件である
(`docs/archive/worklog-phase3-0914-1479.md:186`、前 wave README の U2)。

| # | 残件 | 現物 |
|---|---|---|
| R1 | driver の floor/budget null refusal | `orchestrator/campaign/s8b_oracle_driver.py:524–527` |
| R2 | budget の凍結数値 loader | `orchestrator/campaign/s8b_budget.py:96–118` (`load_oracle_limits`)、呼出しは driver:1433 |
| R3 | report の解決経路 | `orchestrator/campaign/s8b_oracle_report.py:2547–2560` (assertion は :2548) |

親 brief の実アンカー表は**行番号のずれなし**だった (段 3-B が独立に照合)。ずれていたのは
R3 の**範囲**だけで、assertion 1 行と解決経路全体は撤去単位として別物である。

### 2. R1〜R3 のどれにも撤去授権が無い

- **D501 決定 8 は R1〜R3 を名指していない。** 名指したのは撤去済みの 3 述語だけで、しかも
  「いずれの撤去も受理集合を広げるため、本決定では実装しない」と書いている。実際の撤去授権は
  D1985 である。
- **R1 は D1985 が「残すもの」に名指ししている** —「floor/budget の null 拒否と外形・budget 値・
  共有性の検査」。D811 (2026-08-25 ユーザー裁定) の却下選択肢
  「床値を空のまま `floor-null` の拒否だけを個別に解く」もこれを補強するが、**却下選択肢が
  禁じるのはその案に限られ、R2・R3 へは拡張できない** (段 2・段 3-A が独立に指摘、親が採用)。
- **R2 は現用の資源上限供給経路である。** `load_oracle_limits` は freeze の budget を今回の走行の
  資源上限へ射影し、driver:1586 の `create_ledger` へ渡す。**過去 throughput との比較ではない。**
  loader 呼出しだけ消せば limits 供給が壊れる (受理拡大ではなく実行破壊)。
- **R3 は現用の選択・再検証経路である。** D1984 は `assert_g1_floor_selection_identity` の
  現用挙動 (g1 以外では何もせず返る) を事実として記録しただけで、撤去禁止の逐語ではない。
  既存 consumer test (`test_s8b_oracle_report.py:1788`、:1827–1830) が g1 選択規則不一致の
  拒否理由と出力不在を要求している。

### 3. D501 決定 7 の留保は D510 が既に解決していた — 親 brief の誤り

親 brief は「確定済みユーザー裁定」に「D501 決定 7 (条件 3 は逐語凍結、再裁定が要る)」を挙げた。
**これは現在の留保としては誤りである。** 段 3-A が指摘し、親が一次資料で裏取りした。

**D510 (2026-08-18 ユーザー裁定)** 決定 1 が「最終判定から対象別 between-run floor との比較を
撤去し」と定め、決定 3 が**消える保証 4 件** (床値超・scale adequacy・oracle の一意最大・
両構成の eligibility) を名指しで記録している。現行 `s8b_verdict` は床値を選択条件の値比較に
使っていない。

### 4. 「撤去はいずれも受理集合を広げる」は未立証だった

親 brief の断定を段 2・段 3 の両方が崩した。**局所述語の削除・経路の破損・最終受理集合の拡大は
別物である。**

| 対象 | 静的に言える撤去効果 |
|---|---|
| R1 の driver 2 条件だけ | null の診断が消える。`s8b_oracle_manifest.py:603–606` に独立した null 拒否が残るため、実行経路全体の受理拡大は導けない |
| R2 の loader | 呼出しだけ消せば limits 供給が壊れる。予算制約まで外す案なら台帳の計上可能量が変わる。変更案を定義せず「受理拡大」とは言えない |
| R3 の assertion だけ | g1 の選択規則検査を失う。後続 `reverify_published_freeze` は `ReverifiedFreeze` を指定するため選択検査の分岐に入らない |
| R3 の解決経路全体 | freeze/manifest 束縛と store 再検証への供給にも及ぶ (report:2494–2518 で `store_reverification` 出力の有無が変わる) |

### 5. D811 の「門が守っていた性質」は 2 通りに読める

`s8b_oracle_driver.py:524` が見るのは `freeze.get("floor") is None` だけである。**床値が official
由来であること・正値であること・pair 内部整合・性能差が床値を超えることは検査しない。**
「null を拒む性質」と読むなら実装に存在し、「正しい official 床値を保証する性質」と読むなら
この 1 条件だけでは達成されない。本 wave はこの区別を記録するだけで、どちらの読みも採らない。

### 6. 不在の主張の測定範囲 — 親の書き方を訂正した

親 brief の件数は `orchestrator/` 配下の Python に限った測定だったが、repo 全体の件数として
読める書き方をしていた。段 3-B が別 key で取り直した。

| 対象 | 訂正後 |
|---|---|
| `perf_sha_by_cell` | tracked file に 6 行 (decisions と前 wave の記録)。**production は 0 件** |
| `floor_budget_snapshot_sha256` | tracked file に 17 行 (docs/archive 4、Python 負例 1、insight md 8、insight JSON 4)。**JSON の実 key としての一致は 0 件**。`output/s8b-freeze` の 12 件と `output/s8b-freeze-budget-approvals` の 1 件にも不在 |
| `expected_perf_sha256` の production 供給元 | **0 件を維持。** `pipeline.evaluate` の production caller 5 箇所 (`loop.py:782`、`screening_driver.py:639`、`s1_direct_comparison.py:1233`、`s8b_oracle_driver.py:1783`、`qualification/t126_driver.py:543`) のいずれも具体的期待値を渡さない。`**kwargs` 転送 (pipeline:2723–2725) の入口にも無い。**動的呼出しまで排除する全称証明ではない** |
| approved spec | 不在を維持 (`APPROVED_SPEC_SHA256 = None`、`git ls-tree -r HEAD -- output/s8b-oracle-spec/reviewed_spec.json` の **stdout 空**で確認)。ただし「official は必ず `no-approved-spec` を返す」は広すぎ、別の前提条件が先に拒否しうる |

### 7. 仮に R3 を撤去した場合の pin 閉包は空ではない (次 wave のための記録)

本 wave は production 0 byte なので凍結 bytes を変えない。しかし「撤去しても影響先なし」への
拡張は誤りである。

- **file 全体 SHA-256**: `s8b_oracle_report.py` は `generator_versions` の対象
  (`s8b_oracle_manifest.py:67`、:458–496)。現 hash は
  `30fe2b1bcad143f5a85ca32250744522d6049f4c71e9b853618e3af2dd0091c7`。
- **行番号**: `orchestrator/tests/test_ccbench_spawn_sites.py:2959–2964` が
  `s8b_oracle_driver.py` の `run_block` 評価行 **1783** を `_BuildSink` の literal で pin する
  (親が現物で確認)。**前 wave が実際に赤にした型**であり、識別子検索にも hash 検索にも掛からない。
- **正規表現・文字列アンカー**: `test_s8b_budget.py:72` の `match="null"`、
  `test_s8b_oracle_driver.py:1609` の prefix と :2330–2331 の literal。
- **派生 digest**: `test_s8b_oracle_manifest.py:92–93` の golden spec に report hash が埋まり、
  :63–65 の `PIN_GATE_SPEC_SHA256` へ波及する。再生成 manifest では
  `generator_versions` → `manifest_id` → manifest digest → budget ledger 束縛 (driver:1581–1586)
  まで鎖が続く。既存の凍結 JSON が source 編集だけで書き換わる意味ではない。

## refuted と裁定した所見

- **R1〜R3 を残すこと自体が D496 決定 1 に違反する** — refuted。3 者とも過去 throughput との
  比較ではない。D510 と現行 verdict が反証する。
- **実装なしで返すこと自体が絶対規律 2 に反する** — refuted。新たな anomaly 受理も verifier の
  迂回も立証されていない。**受理集合の拡大一般と、anomaly を見逃す正しさ検証の弱体化は
  同義ではない。** 消えた保証は D510 と D1985 が明示的に承認した変更である。

## ユーザーへ返す裁定パッケージ

- **U1 (本体)** [T-1338] の撤去要求そのものを取り下げるか。R1〜R3 はいずれも現用経路で、
  撤去授権が無い。**本 wave は閉じず、carry 本文を測定した事実へ書き換えるに留めた。**
  取り下げるなら T-1338 は閉じられる。取り下げないなら、R2・R3 について
  「何を・なぜ撤去するのか」を新たに裁定する必要がある (R1 は D1985 の残置と正面から衝突する)。
- **U2** `pipeline.py` の generic な `expected_perf_sha256` gate は production 供給元 0 件のまま
  残っている。D1985 は「決定 8 は名指していない。供給元を失うことは記録するが、本 wave で直す
  欠陥ではない」と明示的に残した。本 wave も触れていない。撤去するか、供給元を戻すか、
  現状 (default None で不発、API としては 4 つの既存テストが拒否・続行・不正値・省略時を検査) の
  まま残すかは未裁定である。
- **U3** D811 の「門が守っていた性質」の読み (上記 5)。どちらを採るかで R1 の将来の扱いが変わる。

## 測定

| 走行 | 結果 |
|---|---|
| 実装面差分 | 0 byte (production・test とも編集なし) |
| 変異 matrix | 免除 (`DW-S04` の実装面差分ゼロ) |
| 受入全走 | 段 7 の記録前に実走 (結果は worklog) |

## file

| file | 中身 |
|---|---|
| `brief.md` | 段 1 brief (訂正前。(P1-a)〜(P1-d) の provisional 裁定を含む) |
| `s4-adjudication.md` | 段 4 裁定の全文 (J1〜J7、訂正 5 点、refuted 2 件、変異免除の根拠) |
| `verbatim/s2-plan.md` | 段 2 プランの逐語 |
| `verbatim/s3-lensA.md` | 段 3 レンズ A (正しさ境界と既裁定整合) の逐語 |
| `verbatim/s3-lensB.md` | 段 3 レンズ B (親の実測値とその一般化・不在証明の本物性) の逐語 |
