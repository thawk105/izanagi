---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2718-layer3-lock-purpose
seq: 1
title: [T-2718] 材料レポートの lock 読取りへ呼び手の purpose を通し、中央の歴史閲覧 admission が受理した exact-62 / exact-24 を decoder 段で再拒否しないようにした (コード + テスト + docs、branch worktree-dev-wave-t2718-layer3-lock-purpose、変異 matrix = baseline PASSED・負例 9/9 KILLED・等価 1 SURVIVED (期待どおり)・MISMATCH 0・期待 node 完全一致)
---

## 本文

- ユーザー依頼は「`layer3_report._read_campaign_lock` が purpose を見ず `decode_campaign_lock` を無条件に呼ぶため、
  中央の歴史閲覧 admission を通った lock でも材料レポート生成段で再拒否される件を直す。呼び手の purpose を読取へ通し、
  certified 経路の受理集合は 1 byte も広げない。実在 3 本の exact-62 lock で材料レポートが生成できることを正例に、
  certified 経路で歴史閲覧 lock が拒否され続けることを負例にする。Codex author + 変異事前登録。本題の読取経路だけ」。
- **段 1 の生死実験が依頼の正例条件を覆した。** 現行 63 grammar の対照 (a6-20260909b rr95) でさえ `build_report` は
  decoder を通過した後 `campaign search_config の records/threads が整数でない` で止まる。実在 3 本は paper-story 認証
  campaign で search_config に records/threads が無く、材料レポートの形 (s4/s8a-loop 形) に合わない。grammar と無関係で
  読取り経路の本題を超えるので、段 4 で正例を「合成 exact-62 / 24 campaign で実 admission を通した完全生成」+「実在 3 本が
  decoder 段を通過し 63 対照と同じ到達点で止まる」へ縮小し、paper-story 形の対応は新規項目へ送った (段 3 レンズ B の B-2)。
- **修正後の実在 corpus (5 本、親が repo 外で probe)**: exact-62 3 本 (t2364-20260907b rr5 / rr50、a6-20260908b rr95) と
  exact-24 1 本は HISTORICAL_RAW で decode 成功、CERTIFIED_ACCEPTANCE では従来どおり `campaign.lock schema が不正` で拒否、
  `build_report` は 5 本すべて (63 対照を含む) が records/threads 検査で止まる。lock / WAL bytes は不変。
- **段 3 レンズ A の must-fix A-1 (decode した bytes と admission digest の非束縛、755→795 行の読取り窓) は、本変更に帰属する
  回帰としては refuted。** 現行 code でも同じ窓で任意の現行 63 lock を差し込めるので、旧 grammar を加えても能力は増えない。
  並行書き手を仮定する検査の新設は依頼の「仮想リスク向けの検査は scope 外」に当たり実装せず、裁定パッケージ候補として
  新規項目へ送った (段 6 レンズ A の RA-6 も同旨)。
- **段 3 の A-2 と段 6 の RB-1 は親の実測で閉じた。** A-2 (identity dict を WAL へ渡す等価性) は wal.py の読解
  (receipt helper は lock を取らず、lock を消費するのは `_knowledge_lock_binding` だけ) と拒否 parity test で閉じ、
  RB-1 (I5 の 63 成功経路が未比較) は同一の合成 63 campaign を旧版 / 新版で report して generator sha256 を除き
  IDENTICAL を得て閉じた。段 3 must-fix 4 件 (A-1 / A-2 / A-5 / B-1)、段 6 must-fix 1 件 (RB-1)、refuted は段 3 で 4 件、
  段 6 で 9 件。逐語は `output/insights/2026-09-17/t2718-layer3-lock-purpose/`。
- **wal.py は enforcement source closure (63 path) の 1 つなので触らなかった。** `DecodedHistoricalCampaignLock` を wal 側で
  受ける案は blob 変更で新規 lock の epoch が動くため却下し、layer3_report 側で `.identity` を渡した。この変更は
  load-bearing で、変異 M07 (decoded object へ戻す) は test_layer3_report の 107 node を落とす。
- 段 5 の実装子は焦点 16 ケース + meta-test 3 ケースを sandbox 内の pytest 直呼びで実走できた (T-2483 の
  `NQSconnect EACCTAUTH` は再現せず)。実 corpus probe の実行形は Codex author が書き、親が repo 外へ退避して実行し、
  repo へは入れていない (逐語を insight に残した)。
- 親の焦点走 (login、変更 2 file + 共有 fixture + consumer 5 file + meta-test): 1429 passed。全史 provenance 監査
  10809 件 新規違反なし。

## 次の一手差分

### 完了

- [T-2718] 材料レポートの lock 読取りへ呼び手の purpose を通し、歴史閲覧の exact-62 / exact-24 が decoder 段で
  再拒否されなくなった。certified 経路の受理集合は不変。実在 3 本の完全生成は search_config の形 (records/threads
  不在) が理由で本 wave の scope 外 ({{T:paper-story-campaign-material-report}} へ)。
  remaining: none
  base: bbc9cff64b91d330961dd794571a760bc448aeb3ebcaa8846f8ae8d93ec72097

### 新規

- {{T:paper-story-campaign-material-report}} **P3・新規・裁定パッケージ候補**: paper-story 認証 campaign
  (search_config に records/threads が無く ordered_cells / workload に持つ形) に対して `layer3_report.build_report` が
  `campaign search_config の records/threads が整数でない` で止まる。exact-62 3 本 (t2364-20260907b rr5 / rr50、
  a6-20260908b rr95) も現行 63 (a6-20260909b rr95) も同じ。「歴史閲覧用途の材料レポートを paper-story 形へ広げるか、
  別の材料レポート producer を使うか」はユーザー裁定。成果物影響 = これらの記録に対する材料レポートが生成できない
  (T-2718 の decoder 修正後も)。
- {{T:layer3-lock-decode-bytes-binding}} **P3・新規・裁定パッケージ候補**: `layer3_report.build_report` は 755 行で decode
  した lock と 795 行で再読して admission digest と照合する lock が同じ bytes である保証を持たない (T-2718 段 3 レンズ A
  の A-1、段 6 RA-6)。並行書き手が居れば任意の現行 63 lock (T-2718 後は旧 grammar も) を decode 段だけに差し込める。
  既存の構造で T-2718 は新設も解消もしていない。同一 bytes の decode + digest 照合へ変えるかはユーザー裁定
  (仮想リスク向けの検査新設は既定で scope 外)。
