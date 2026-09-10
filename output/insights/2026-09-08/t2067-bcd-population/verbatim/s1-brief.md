# [T-2067] 残件 (b)(c)(d) — 段 1 brief (親)

- wave: `worktree-dev-wave-t2067-bcd-population`、基準 `cc9bba523` (着手直前の local main、乖離 0)
- worktree: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2067-bcd-population`
- 正本: archive worklog の [T-2067] 本文 (`docs/archive/worklog-phase3-0908-1345-1347.md:311`)、
  D1526、D1503、D1370、D1371、D1313、D1241、および `docs/archive/worklog-phase3-0903-1236.md:333`

## 研究前進

床値 (floor) を根拠にした主張は D1241 / D1313 により advisory・non-certifying に据え置かれている。
本 wave は主張の水準を 1 mm も動かさず、**「床値選択規則をまだ強制していない入口の母集合」を今日の
main で確定する**。完了判定は、母集合の全列挙と各要素の帰属 (強制済み / 既裁定 / 未裁定) が一次資料で
裏付けられて台帳に残ること。止めている研究は「後続 wave が既済項目を再実装し、未強制点を取り残す」
状態そのもので、最小差分は母集合の確定と carry の訂正である。

## 確定済みユーザー裁定 (scope)

- (a) は D1526 のとおり実装・着地済み。**触らない。**
- 本題は (b) 母集合の再確定と、それに続く (c)(d) だけ。
- **仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。**
- D1241 / D1313 の advisory / non-certifying 上限は解除しない。

## 親が一次資料で確かめた事実 (子はこれを疑ってよい)

1. carry の (b)「load-only consumer 3 群」は **1236 の時点で 4 群へ訂正済み**。1345 の carry は
   1236 以前の文面を写している (一次資料: `docs/archive/worklog-phase3-0903-1236.md:333-344`、
   `output/insights/2026-09-03_t2067-bcd-selection-closure/README.md`)。
2. (c) の「公開迂回口」は 1236 で private 化により閉じ、負例
   `test_ungated_manifest_apis_are_not_public` が今日も実在する
   (`orchestrator/tests/test_s8b_oracle_manifest.py:1252`)。**残っているのは別内容** —
   `verify_manifest` (`s8b_oracle_manifest.py:1019`) が選択 token を要求しない点、
   `_write_approved_manifest`、および 1345 段 3 が指摘した library 経路
   (`verify_manifest` → `build_observations` / `judge_oracle` / `verify_oracle_verdict` → `judge_combined`)。
3. (d) の「実導出被覆」は 1236 で launch / consumer 経路へ genuine 正例・負例 4 node を張って閉じ、
   今日も実在する (`orchestrator/tests/test_s8b_ratified_verify.py:1031/1046/1060/1075`)。
4. 親の AST 走査 (probe は repo 外、`orchestrator/**` + `tools/**` の 764 file を `ast.parse`)。
   `RatifiedFreeze` の構築点は `load_ratified_freeze` 内の 1 箇所だけ。production の
   `load_ratified_freeze` 呼出しは 9 箇所 / 9 関数 / 7 module で、内訳は次のとおり。
   - 同一関数内で選択強制済み **5**: `s8b_oracle_manifest.py:1206`、`s8c_result_judge.py:2078`、
     `s8b_oracle_report.py:2548`、`s8b_oracle_judge.py:750`、`s8b_verdict.py:829`
   - `launch_validate` 経由で強制 **2**: `s8b_oracle_driver.py` の `gate_check:664`、`run_block:1351`
   - 未強制 **1**: `p3_autonomous_workload_trial.py:4957` (`run_trial` の C06 予算経路 = 残件 (e)、
     D1371 が「実装しない」と裁定済み)
   - 1236 が「強制点ではない」と整理した **1**: `s8b_oracle_driver.py:496` (`_gate_check_core` の
     private core self-load)
5. `_GENERATOR_SOURCES` (`s8b_oracle_manifest.py:65-73`) は `s8b_oracle_report.py` と
   `s8b_oracle_judge.py` の sha256 を pin する。`driver` / `verdict` / `manifest` /
   `p3_autonomous_workload_trial` は非対象。**この 2 file に触らない限り凍結成果物の再発行は起きない。**

## (P1) 親の provisional 裁定 = 段 3 の攻撃対象

- **(P1-1)** (a) 着地後に残る未強制の load-only consumer は **C06 予算群 1 つだけ**で、それは D1371 が
  既に「実装しない」と裁定している。よって (b) の結論は「新規裁定を要しない」。
- **(P1-2)** `_gate_check_core:496` と `gate_check(ratified=...)` の注入 seam
  (`s8b_oracle_driver.py:597`) は母集合に含めない (1236 の整理を踏襲)。
- **(P1-3)** (d) は閉じている。再実装しない。
- **(P1-4)** (c) に残る非対称は production caller が 3 CLI に閉じている以上「仮想リスク」であり、
  今回の scope 制約により実装しない。閉じていない範囲として記録に留める。

## 不変条件

- 正しさゲートを緩めない。既存の強制点・拒否理由集合を減らさない (規律 2)。
- `s8b_oracle_report.py` / `s8b_oracle_judge.py` を編集しない (凍結成果物の再発行を避ける)。
- 3 台帳 (worklog / decisions / failures) は直接編集せず `docs/spool/` の fragment で書く。
- 件数は AST か権威ある閉包に由来するものだけを書き、grep の hit 数を inventory にしない。
- 母集合の主張には「この数の母集合は何で、除外は何か」を 1 行で添える。

## 成果物の形

- `output/insights/2026-09-08_t2067-bcd-population/` — 母集合表、閉包の引き方、閉じていない範囲。
- `docs/spool/` fragment — worklog (carry の訂正を含む)、decisions (母集合の確定)。
- **実装面の差分は既定でゼロ** (段 4 で覆りうる)。ゼロなら DW-S04 により変異 matrix は免除、
  受入全走は免除しない。

## 並列分割

- 段 2: read-only codex 1 本。file:line 粒度で母集合の閉包を**独立に**導出させる。
- 段 3: 2 レンズ。A =「母集合の取りこぼし」(注入 seam・間接消費・別名束縛・新規 module)、
  B =「既済判定の誤り」((c)(d) は本当に閉じているか、carry 訂正の向きは正しいか)。
- 受入は login node から `tools/dev_wave_wait.py acceptance` で投入する (所在は worklog に記録)。
