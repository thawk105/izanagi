---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2288-binder-precheck
seq: 1
title: [T-2288] B-4 床値 spec 凍結の binder precheck — placeholder 3 spec で凍結 checkout の `place` と `--validate-only` が実 record・実較正・実 binary で通り、負対照 5 本が binder の各検査で落ちた (docs のみ、branch worktree-dev-wave-t2288-binder-precheck、変異 matrix = 実装面差分ゼロにつき免除)
---

## 本文

- ユーザー依頼は「A-5 (2 窓・campaign_id・seed_hex・relpath) はユーザー裁定待ちなので値は決めず、捨て branch に
  placeholder 値の 3 spec (`floor-pair-spec/v3`、D2088 の perf_config・D2089 の 3 cell・D2090 の較正) を commit し、
  凍結 checkout での binary `place` と `floor_pair_driver.py --validate-only` (binder 全体) を通し、成否と落ちた箇所を
  insight に返す。準備が本番一式の再構築になるなら中止して理由だけ返す。gate・検査の追加は scope 外。規律 2 を
  緩めない」。
- **binder 全体が実 checkout で初めて通った。落ちた箇所は無い。** 一次資料は
  `output/insights/2026-09-17/t2288-binder-precheck/README.md`。3 spec (rr95 / rr50 / rr5) とも `--validate-only`
  rc=0・stderr 空で `floor-pair-plan/v2` (248 session・496 測定・2 窓 × 124、§11.2 の名目と一致) を返した。
  `place` は rc=0 で `output/env/pegasus/binaries/7cdf0dc3…` (701,760 bytes、ignored) を置いた。再構築は要らなかった。
- **負対照 5 本を同じ checkout で実走し、binder の各検査が拒否することを確かめた** (gate・test は足していない)。
  (a) 期待 sha 1 桁違い → `frozen spec sha256 不一致`、(b) 未 commit の 1 byte → `loaded HEAD tracked blob と byte
  一致しない`、(c') 祖先でない `source_commit` → `祖先でない`、(d) 配置 binary 不在 → `binary b4-candidate を lstat
  できない`、(e) 出力 relpath の parent dir 不在 → `output[0].parent を lstat できない`。brief の「(c) `source_commit`
  == HEAD」は tracked spec が自分を含む commit hash を書く不動点で到達不能なので (c') に置き換えた。
- **凍結 wave への注意点 (実測):** `place` は checkout ごと・出力 dir は先に用意・`source_commit` は spec commit の
  親・spec 後に commit が積まれても plan bytes は不変 (HMAC 入力は spec sha256)・`place` の policy 時間依存 (D2069 項 6、
  本日 `949ddcc2…` で一致)・spec の置き場と命名は本 wave の placeholder であって先例ではない。
- 実測前提 (段 1): record `rr20--stock_common.json` は tracked で validator を通り policy sha が現行と一致、durable
  binary 実在、較正 3 件は driver と同じ入口で ADMITTED (値は D2089 と一致)。`--validate-only` と `store_binaries` に
  site gate は無く、計算ノード job・新規 Pegasus 実行体 (F660) は不要だった。
- 裁定 inbox: 段 4 前に local main が `abc7085ae` → `ad12ba35b` (rulings 第 20 回、39 項) へ進み ff-only で取り込んだ。
  39 項に T-2288 / A-5 / 凍結 spec への言及は無い。
- 捨て branch `precheck-t2288-placeholder-specs` (起点 `ad12ba35b`、commit `3ec30125f` → `b84275b6` → `d587547b6`) は
  land しない。placeholder spec・plan を凍結にも正式 evidence にもしない (事前登録 §11.1)。削除はユーザー指示時のみ。
- 受入・検査: 本記録 commit 前に `check_docs`・`spool_fold --dry-run`・三軸語走査を実走した結果は insight の
  「受入・検査」表。受入全走は本記録 commit を含む最終 tip に対して land 前に 1 回だけ投入し、child-green でなければ
  land しない (受領証は job dir)。
- 段 8 の自己改善: 候補 0 件。踏んだ guard 拒否 (heredoc と防護 path の同居、隔離 session の複合形) は既知の型で、
  docs の新規収容も F の再発追記も無い。
- エージェント工数: codex 子 0 本 (軽量版、実装面なし、設計択一なし)。親の実走は `place` 1 本、`--validate-only`
  正例 4 本 (3 spec + HEAD 進行後の再走 1 本)、負対照 5 本、いずれも login node。

## 次の一手差分

### 更新

- [T-2288] **P1・凍結前の binder precheck は通った。spec 凍結までに残るのは A-5 の裁定と凍結作業だけ**:
  A-3 = `extime 3 / reps 5 / ycsb_max_ope 10` (D2088、`reps` は AI の選択)、
  A-4 = 3 workload × 1 セル (t48・skew 0.9・rmw 0) の 3 cell (D2089)、C 群 = 5 条件 + 最早順
  (D2090、rr50 は g2 `94a4b79f…`)。rr5 の accepted 較正 (1535)、binary record (T-2636)、配置規則 (T-2697、
  `output/env/<env_tag>/binaries/<sha256>` の ignored 複写) は着地済み。**binder 全体 (spec ⇔ HEAD blob・
  `source_commit` 祖先・binary sha256・build receipt・較正) は placeholder 3 spec で実 checkout を通り、負対照 5 本で
  各検査が落ちることも実測した** (insight `2026-09-17/t2288-binder-precheck`、捨て branch
  `precheck-t2288-placeholder-specs` は land しない)。**残る前提は A-5** (2 窓の `not_before` / `not_after`・
  `campaign_id`・`seed_hex`・`artifact_relpath` ×2・`summary_relpath`・実行設定。§11.1 は無裁定の AI 起草値を既定値と
  して凍結へ入れることを禁じる。裁定パッケージは entry 1581 の insight)。凍結 wave の手順は insight の「凍結 wave への
  注意点」(place は checkout ごと・出力 dir を先に用意・`source_commit` は spec commit の親・policy の時間依存)。
  凍結後の工程として床値実測、集約、採用裁定、§5 floor 欄の記入が残る。
  base: 5a5b935fe9a63f0da5fa424beaf6de6ce1eca8cb0e8f5cf598a25803ad310347
