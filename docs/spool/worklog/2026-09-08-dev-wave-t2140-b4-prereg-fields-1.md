---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2140-b4-prereg-fields
seq: 1
title: [T-2140] B-4 事前登録 §5 の残り欄を解除条件どおりに測ったら、埋まるのは 8 欄中 1 欄だけだった — §10/§11 の陳腐化 2 件は追記で訂正した (docs のみ、branch worktree-dev-wave-t2140-b4-prereg-fields)
---

## 本文

依頼は「floor 以外の 7 欄を §5.1 の解除条件どおりに埋める」で、
前提として「実走前に要る裁定 2 件 (D1694 / D1695) が land 済みなので前提は解けている」を挙げていた。
**この前提は floor 欄にだけ掛かる。** D1694 / D1695 は §5.1 の floor 項への追記であり、
その追記自身が「それでも本欄の解除条件は 1 つも緩まない」と書いている。
親が 7 欄を 1 つずつ現物で測った結果、**解除条件が実際に充足されているのは primary outcome の 1 欄だけ**だった。
残り 6 欄が埋まらない理由は欄ごとに別で、いずれも「記入を怠った」ではない — 母集合欄は台帳の**実体**が
`output/` 配下に 1 件も無く、`PerfConfig` 欄は `default_perf()` が未校正のままで、
env_tag 欄は正式実走 site が未確定 (tag は site で分岐する)、model 欄は §10 が
「人間の指名を含むため AI が確定できない」と明記している。欄別の実測は
`output/insights/2026-09-08_t2140-b4-prereg-fields/README.md` の表が正本。

**段 3 のレンズ A が「primary outcome 欄も埋めるな」と結論し、その根拠が stale だった。**
レンズ A は `p3_b4_analysis_adapter.py` の docstring「raw fields that do not yet have an
authoritative producer」を引いて権威 producer の不在を主張したが、その docstring は
commit 592a08f32 (2026-08-27) 由来で、`p3_b4_raw_record_producer.py` が bab79b6c4
(2026-09-03、[T-2141]) で入って以降は事実に反する。親が commit 日付と実装 (1566-1703 行) で確かめて refuted とした。
**子の所見の根拠が repo 内の説明文のときは、その説明文自体の新しさを疑う。**

**レンズ A の残り 2 件は real だが記入を妨げない**と裁定した。consumer が adapter の contract 一致を
挙動検査しないのは現物で真だが、§5.1.1 が定義するのは母集合規則・n・純関数・enum・verdict であり、
それらは consumer が検査する 3 source に在る。§5.1 の「参照だけで埋めるな」という警告も、
実装 artifact の bytes を書く本件には掛からない。設計判断は {{D:b4-primary-outcome-cell-cites-source-closure}}。

**§10 の陳腐化は一次資料で裏を取ってから直した。** レンズ A が「完了追記には証拠が要る」と指摘したので、
`output/insights/2026-08-27_t1769-b4-wiring-probe/t2341-eligibility/` の 3 件を照合したところ、
sha256 が §5 の値セルの 3 値と exact 一致し、3 件とも `result.passed` が真、`pass_rule` と `run.axis` も
§5.1.0 の凍結値と exact 一致した。訂正の作法は {{D:preregistration-errata-are-append-only}}。

**棄却 finding 1 件、採用 12 件。** レンズ B の検算 (pin 範囲 312-596 行・21,833 bytes・raw sha256、
§5 表 parser の引用行、`sha256=` の横滑り発火なし) はすべて親の実測と一致した。
レンズ B が見つけた親 brief の誤記 2 件 (parser の行番号、§11 の訂正は 1 か所でなく 2 か所) も採用した。

**依頼のうち「§11 の凍結 commit」は作れないと裁定した。** §11 は D1383 に基づく未裁定の案であり、
§11 自身が「誰がどの証拠で floor 欄を発効させるかはユーザーが決める」と書く。
本 wave の commit は §11 の erratum を含む版を固定するが、事前登録としての凍結ではない。

実装面の差分ゼロ (docs 1 file、31 行追加 1 行削除) なので変異 matrix は免除 (DW-S04)。受入全走は免除していない。

## 次の一手差分

### 完了

- [T-2398] 事前登録 §10 の「対象 driver と軸の欄は埋められない」を追記で訂正した。
  probe 成果物 3 件の sha256 が §5 の記入値と exact 一致することを現物で確認したうえで、
  §5.1.0 の決定規則が base を選ぶことと、それでも本書が発効前であることを併記した。
  remaining: none
  base: 19fb50713fc538f0e802d7d67aba72b8bd1acb334d395b86f2792b9daa1f6a2f
- [T-2424] 事前登録 §11 の 2 か所 (§11.0 と §11.3) の「生成器は本書を読まず無条件に floor 不在を渡す」を
  追記で訂正した。非 `None` の floor が渡るのは検証を通る権威ある成果物 pin が §5 に在る場合だけ、
  という条件を明示し、`未記入` を有効な floor と見なさないことを書いた。
  remaining: none
  base: 24e18e8bebfa4197c3d72d5929eec65c272978fd05b0213d292f7c5705ed37f4

### 更新

- [T-2140] **P1・一部前進 → ユーザー裁定 4 件待ち**: §5 の primary outcome 欄を分析 source closure の
  5 member (path + sha256) で記入した。残り 6 欄は解除条件が未充足で、欄ごとの理由は
  `output/insights/2026-09-08_t2140-b4-prereg-fields/README.md` の表にある。
  **裁定 4 件**: (a) §5.1 の「その artifact」を source file と読むか consumer receipt と読むか
  (receipt と読むなら本 wave の記入を差し戻す)、(b) 開始時刻欄の予定日時の指名、
  (c) §11.1 / §11.2 の採否 (これが決まるまで §11 の凍結 commit は作れない)、
  (d) §7.2 と §10 に残る同型の陳腐化 (manifest・registry・完全性 consumer の不存在断言) の訂正範囲。
  floor 行は [T-2412] / [T-2423] 待ちで手を付けていない。
  base: b982597fc3b4e10f92b0b2bc5f2c66b7f4232ce4218d62b2f2e7bdafecb55ccb
