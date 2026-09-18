---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2484-watchdog-segments
seq: 1
title: [T-2484] 変異 harness の外側 watchdog の契約区間を決める材料を実測した — dispatch receipt 3,849 件の区間別所要 (Pre-running を分離、p99 398 秒) と発火 15 件の区間別帰結 (QUE 中は qdel 0.3 秒で閉じ、Pre-running / RUN 中は job が残る)、既存 t2195 spec は今日の混雑下で発火せず、hang_timeout 4 秒の派生 spec で発火の機構と復旧 9 秒を観測。契約 (a) は決めず裁定パッケージへ (docs + insight、branch worktree-dev-wave-t2484-watchdog-segments、実装面差分ゼロ = 変異 matrix 免除、Codex author 1 本は receipt 集計 script で repo へ commit せず逐語保全)
---

## 本文

- ユーザー依頼は「[T-2484] (D1910 項 1 → 実測手番、D2044 項 29 で (b) 採らない・(c) 採る は裁定済み) 変異 harness の外側 watchdog の契約区間を決める材料を実測する — queue 待ち / RUN 後 / cleanup の区間別所要と、既存 artifact を混雑下で走らせたときの実際の発火を既存道具で測り、insight に構造化する。契約定義 (a) は本 wave で決めず、実測後に索引へ戻す。(c) の理由付き早期診断は受理集合を動かさない範囲に限る。実装差分は既定ゼロ。着手直前の local main から fresh worktree を作る」。
- **閉じたのは材料の実測で、契約 (a) は決めていない。** 一次資料は `output/insights/2026-09-18/t2484-watchdog-segments/README.md` (§2 区間別所要、§3 履歴の発火、§4 原本 spec の実走、§5 発火の機構、§6 裁定パッケージ)。base は着手直前の local main a0ccb8ad9。
- 区間別所要 (dispatch receipt 3,964 件のうち state_history のある 3,849 件、main + 両 worktree 群 + dev-wave-jobs 配下の複製): 前段 p50 1.3 秒、queue 待ち p50 5.2 / p99 297 / p99.9 900 / max 1,601 秒 (≥900 秒は 0.23%)、RUN p50 20.5 / p99 548 / max 1,784 秒、END 後 p50 5.2 / max 36.5 秒。**receipt の RUN は Pre-running を含む** (dispatcher は Pre-running を RUN と分類する)。計算ノード marker の mtime で分離すると Pre-running p50 3.6 / p99 398 / max 795 秒 (≥300 秒 2.2%)、実 RUN p50 13.7 / p99 207 秒。**投入時の gen_S QUE 数は queue 待ちの予測にならない** (QUE 9 で 902 秒、QUE 67 で 5 秒)。
- 発火の区間別帰結 (receipt の infra 15 件 + 本 wave の実走 1): QUE 中に外側 watchdog (SIGTERM) が切ると dispatcher は fresh-qstat gate で 0.15〜0.26 秒で qdel し job は残らない (4/4、dispatcher 自身の Q timeout も 3/4)。Pre-running / RUN 中に切ると gate が `state-not-cancellable` で qdel せず job は自然終了 (真の hang なら walltime) まで残る (7/7)。harness 側は区間に依らず orphan hold + rc=2 + 変異残置。外側 X 秒の反実仮想発火率は 300 秒 4.6%、900 秒 0.55% (うち 3/4 が Pre-running / RUN 中)、1,800 秒以上 0 件。
- 原本 spec (t2195、timeout 3,600 / hang 900、M9 hang_risk の subset、上書き Q=3000 / G=600) は gen_S QUE 67 / RUN 35 で走らせても 3 dispatch とも queue 待ち 5.2 秒で発火せず (M9 KILLED 27 秒)。発火の機構は hang_timeout を 4 秒にした派生 spec で観測: 発火時 scheduler は Pre-running (qsub から 1 秒で遷移)、dispatcher は 0.1 秒で gate 判定と receipt 書出しを終え harness の 5 秒猶予に収まり、job は変異を当てたまま 10 秒後に走って 21 秒で終わり、復旧 (qstat 終端確認 → checkout → hold 削除) は 9 秒。同じ container で collection と baseline は Pre-running に 11 分ずつ (676 / 668 秒) 留まった。RUN 中の発火を狙う run3 (hang 20 秒) は receipt 6 件が同じ gate の帰結を既に示すため実施しない。
- 裁定パッケージ (insight §6): 候補 (a-1) 全区間を覆う (既定 4,952 / 上書き 7,952 秒、過去 3,849 件で harness 先行発火 0)、(a-2) 現行 gate の Q+G (1,200 秒で 0.26% 発火、9/10 が orphan hold)、(a-3) hang_timeout を外側から外す (DW-M06 改訂が要る)、(a-4) 区間認識 watchdog (= 見送り [T-2071]、新機構)。親の推奨は (a-1) + (a-3) (harness は dispatch job を止められないので先に切っても待ちは減らず hold が増えるだけ)。(c) の具体案 2 つ (起動時の理由付き警告、発火時の区間診断) も §6.3 に置き、本 wave では実装しない。
- 段構成: 軽量版 (設計択一・受理集合の変更なし)。段 5 の Codex author 1 本 (`gpt-6-astra`、receipt 集計 script 414 行、selftest PASS、`check_codex_output` rc=0) は repo へ commit せず job dir へ退避し insight の verbatim に逐語保全 (docs/ai-provenance.md の実装面規約)。段 2・3・6 の review 子は省略。変異 matrix は実装面差分ゼロで免除 (DW-S04)。実走: 変異 harness 2 走 (run1 rc=0、run2 rc=2 = 意図した orphan hold)、計算ノード job 6 本 (5430〜5432、5441、5442、5452)、`--plan-only` 3 回、集計 2 回。受入全走は land 経路で実施し結果は land の受領証に置く。
- 副観測: dispatcher は qsub 前に `pending-qsub` の orphan hold を latch し終端証拠後に消す (正常経路でも一時的に file が現れる)。dispatch 3,964 件のうち 115 件 (2.9%) は `qstat -Q preflight rc=1` で投入前に infra 失敗している。

## 次の一手差分

### 更新

- [T-2484] **P2・ユーザー裁定待ち (実測済み)**: (a) 外側 watchdog が dispatcher のどの区間 (queue 待ち / Pre-running・RUN / cleanup) を覆う契約とするかを決める。材料は `output/insights/2026-09-18/t2484-watchdog-segments/README.md` §6 の裁定パッケージ (候補 (a-1)〜(a-4) と実測値の対応、親の推奨は (a-1) + (a-3))。追加の実測は不要。裁定後の実装 wave が DW-M06 / DW-M07 の改訂と (c) の早期診断 (受理集合不変) を持つ。(b) 不採用・(c) 採用は D2044 項 29 のまま。
  base: a10101e53259c333fa21601f8331c38e4b08527c7348f78ea0d3293b4d24446d

### 見送り追記

- [T-2071] 2026-09-18 に [T-2484] の実測で再訪の材料を得た (Pre-running p99 398 秒・≥300 秒 2.2%、外側 900 秒の反実仮想発火率 0.55% のうち 3/4 が Pre-running / RUN 中 = orphan hold)。裁定 (a) の候補 (a-4) に相当し、(a) と同時に扱う。追加裁定はせず記録のみ。
