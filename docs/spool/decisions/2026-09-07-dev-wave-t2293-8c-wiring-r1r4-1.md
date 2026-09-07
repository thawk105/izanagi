---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2293-8c-wiring-r1r4
seq: 1
---

## {{D:origin-lifecycle-loader-cannot-enforce-the-iff}}. lifecycle loader は起点束縛の必要十分条件を強制できないので、実在する層で強制する

**決定:** lifecycle start 行の `origin_run_plan_sha256` と `launch_admission.origin_binding` の
必要十分条件は、launch admission が実在する層 — 書き手 (`record_trial_start_once`)、
terminal (`record_trial_terminal`)、acceptance — で強制する。**loader は自分が見えるものだけを
検査する** (key 集合の 2 択、digest の形式、start 行の起点主張と terminal の projection の対応)。

D1667 が裁定した「起点専用 optional key」の範囲を超えて、start 行へ launch admission の
record 全体を載せることはしない。

**理由:**
- `_load_lifecycle_rows` は lifecycle 台帳の bytes だけを受け取る。start 行が持つのは
  `launch_admission_sha256` (digest) であって record 本体ではない。digest からは
  `origin_binding` の有無を判定できない。したがって loader は新しい情報なしには iff を強制できない。
- record 全体を載せる案は、D1667 が認めた optional key 1 本の範囲を超える未裁定の wire 拡張である。
  同じ record が digest と実体の 2 か所に載り、永久に整合を保つ義務が生じる。
- 2026-08-12 のユーザー方針 (研究最優先・プロトタイプ基準) に照らすと、手で改竄した台帳行への
  防御のために wire を広げる投資は現時点の根拠を欠く。

**却下した選択肢:**
- start 行へ `launch_admission` record 全体を載せる — 未裁定の wire 拡張であり、
  同じ record の二重化を招く。
- `origin_terminal_projection` の有無を `origin_binding` の代理にする — 代理は推測であり、
  start-only の台帳では判定できない。

**保証しないこと:** loader 単体では、手で書いた start 行の起点主張が本物かを判定できない。
偽の start-only 行は trial ID を占有し、正式な再入を拒否させうる。最終 acceptance はこれを
拒否するので、certified 選択と材料レポートの値には到達しない。この限界を塞いだと書いてはならない。

## {{D:origin-failure-terminal-without-projection}}. 起点試行の失敗終端は projection 無しで許す

**決定:** `terminal_status` が `indeterminate` または `partial` で、かつ非空の `failure_reason` を
持つときに限り、起点試行が **projection 無しの base terminal 形**で終端できるようにする。
`complete` は従来どおり projection を必須とする。loader の start ↔ terminal 対応にも、
失敗 status のときだけ同じ緩和を適用する。

**理由:**
- 受入要件 11 の順序是正で lifecycle start が observation 開始より前へ移った結果、
  observation 開始後の失敗が terminal を書けなくなった。`record_trial_terminal` は
  origin binding と projection の有無が食い違う terminal を拒否するためである。
- 塞がないと、試行台帳に「開始だけあって終端がない」行が残る。その行は再試行を阻止しながら
  acceptance も成立させないので、slot が死んだまま残る。
- 緩和は失敗 status に限られ、成功終端の受理集合は 1 つも動かない。

**却下した選択肢:**
- 順序を元に戻す — D1667 が envelope digest を start 行へ束縛すると裁定したので、
  start は envelope の後・observation の前でなければならない。
- 失敗時に非永続の partial dict だけを返す — 台帳には何も残らず、
  「開始だけあって終端がない」行がそのまま残る。

## {{D:origin-lock-path-computed-not-declared}}. 起点 consumer は錠前の場所を計算し、呼び手に申告させない

**決定:** formal consumer は `exploration_campaign_layout(planned_campaign_run_identity,
campaign_output_root)` で canonical な layout root を**計算**し、その配下の `campaign.lock` を
読んで物理 identity と論理 campaign を再導出する。`result-evidence` の schema に
content-addressed ref を足すことはしない。

**理由:**
- 設計文書 §D は錠前を content-addressed ref で解決する形を書いていたが、
  `result-evidence/v1` は exact 9 key で ref が 2 本しかなく、3 本目を足すと
  R1〜R4 のいずれの裁定にも含まれない schema 変更になる。
- 計算で導く形は呼び手に場所を申告させないので、**content-addressed ref 案より受理集合が狭い。**
  「plan identity と整合する錠前と WAL を、計算どおりでない directory に後置した入力」も拒否できる。
- schema の bytes も受理集合も変えずに済む。

**却下した選択肢:**
- `result-evidence` に `campaign_lock_ref` を足す — 未裁定の schema 変更であり、
  しかも呼び手の申告を信じる分だけ受理集合が広い。

**保証しないこと:** 実行後に、計算どおりの canonical root へ整合した錠前と WAL を後置した入力は
拒否できない。D1674 が明記した trusted-writer 運用前提の外側であり、この限界は狭めていない。
