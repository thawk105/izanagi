---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-08
wave: dev-wave-t2430-a6-readheavy-mechanism
seq: 1
title: [T-2430] A-6 read-heavy の −5.78% は B-10 の近接条件 3 block で同符号・同程度、名目待機会計と整合 — 反復 attempt は行わない (docs のみ、branch worktree-dev-wave-t2430-a6-readheavy-mechanism、実装面ゼロ)
---

## 本文

- [T-2430] の 2 択 (反復 attempt で確かめる / 機序として説明する) に対し、新しい測定を 1 件も行わず
  記録済み測定の事後再解析で閉じた。成果物は `output/insights/2026-09-08_t2430-a6-readheavy-mechanism/README.md`。
- 発見 1: B-10 read-heavy 本走 (job 977647、bnode088、2026-09-05) が A-6 と同じ 2 genome (`BACK_OFF=0` と
  `BACK_OFF=1, BACKOFF_FIXED=2`) を 1 job 内 3 block × 5 標本で持ち、効果は −6.61 / −5.38 / −5.32% で
  A-6 の −5.78% と同符号・同程度。両 arm の絶対水準は 1.3% 動き、比だけが一致した。実行機会は 2 つで、
  「同条件かつ独立な再現」ではなく近接条件の別実行による履歴的再現と記した。
- 発見 2: A-6 の集約 abort 率から 1 commit あたりの名目待機 `a·b = 0.339 µs` が出、観測された集約時間の増分
  +0.292 µs の大部分を会計項だけで再構成する (会計項のみで −6.66%、別データの abort 費用 r を引くと −5.87〜−5.95%、
  実測 −5.78%)。機序の一意同定ではなく、事後整合性検査として書いた。
- 裁定: 新しい反復 attempt は行わない。反復しても `a4_noise_floor_status` は producer の定数 `"open"` のまま変わらず、
  失うのは attempt 間変動の観測だけである。反復する場合の手順 (事前登録の凍結、policy の tracked_destination
  変更 = 実装面で Codex author) は README §4 に残した。
- 段 3 の敵対相談 (read-only codex 1 本、レンズ A) は MF 6 件・SH 1 件を出し、全件 real・採用した。壊れたのは
  初稿の「同条件で再現」「独立 3 回」「spin 時間 6.0% を実測」「1.6% 一致で機序を確かめた」「A-2 脚注は単独使用
  だけを禁じた」「r=3.165 は式 (1) の fit」の 6 表現。壊れなかったのは A-6 の負の効果、B-10 の同符号・同程度、
  名目会計が差の大部分を占めること、反復不要の裁定。逐語は job dir
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2430-a6-readheavy-mechanism/` の `consult-a.md`・`s4-ruling.md`。
- dev-wave-t2417-policy-arm-perf との編集面重複を起動時に検査し、重複なし (本 wave は insight 1 dir と本 fragment のみ)。
- 実装面ゼロ (D95 の docs-only 条項)。段 5・6 は省略、変異 matrix は免除 (DW-S04)。記録前の焦点走
  (repo を読む `test_ruleops.py` + `test_check_docs.py`、runner 経由) は 722 passed / 4 skipped。check_docs・
  fold dry-run・三軸語走査 (conjunction_hits 空)・provenance 全史監査 (8786 件、新規違反なし) はいずれも緑。
  受入全走の結果は land が読む receipt (job dir) に残り、tested tip 以降に記録 commit を積めないため本文には書かない。

## 次の一手差分

### 完了

- [T-2430] A-6 read-heavy の −5.78% を、既存の近接条件 3 block の再現と名目待機会計との整合で説明し、
  反復 attempt を行わないと裁定した。成果物 `output/insights/2026-09-08_t2430-a6-readheavy-mechanism/README.md`。
  remaining: none
  base: a1c04bd2669ff658f32150298fa7bb380ce324b2ddfefd9273bae4e77c40af45
