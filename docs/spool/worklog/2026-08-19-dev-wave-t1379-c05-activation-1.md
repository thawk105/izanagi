---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1379-c05-activation
seq: 1
title: 8c 条件5 (C05) の証拠契約・評価器を machine_checkable へ昇格し DECIDER_VERSION を v5 へ bump した — §5/schedule artifact は authority 構築不可能につきユーザー裁定で scope 外 (コード + テスト + 記録、branch worktree-dev-wave-t1379-c05-activation、変異 matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- **段3 敵対相談 2 本 (レンズA/B) が独立に「本物の authority は scope 内で構築不可能」と
  指摘した。** production 側の権威解決関数は明示的に unavailable を送出し、暫定値での
  commit は将来の再現不能リスクがあると判定。ユーザー裁定 (AskUserQuestion) で
  「4 項目 (契約反転・registry 登録・DECIDER_VERSION bump・凍結世代発行) のみ実装し、
  §5 `master_seed` 記入と `schedule.v1.json` commit は T-1380 待ちとして scope 外」に確定した。
  詳細は {{D:c05-authority-deferred}}。
- **並行 wave `dev-wave-t1355-c04-c07-decider-bump` (T-1355) と SendMessage で
  DECIDER_VERSION/凍結世代の資源調整を行った。** 着手時点で main の DECIDER_VERSION は
  既に v3→v4 (別 wave 消費済み)。その後 T-1355 が先に v4/g8 を着地させたため、
  本 wave は次の未使用版 v5/g9 を使った。
- **段6 敵対レビューAが変異事前登録#2 (到達性検査を弱める変異) の実効性欠陥を実測で
  指摘した。** `required_calls`/`required_targets` の両方を対象にしていたが、新設 fixture は
  `required_targets` 層だけを検証しており、`required_calls` 層の弱体化は fixture 側の
  到達不能で先にマスクされ SURVIVED になると判明。登録を `required_targets` 単独へ
  限定して解決した (詳細は insight package)。
- **変異 spec 組成中に `@pytest.mark.xdist_group` 付き 2 test の node ID 表現問題が再発した
  (F408 の再発)。** T-1355 が同じ 2 test で同じ問題を独立に発見・記録していたことが
  SendMessage のやり取り中に判明した。同じ `--deselect` workaround を適用し、
  再発として F408 へ記録した (異なる wave での 2 度目の独立再現、族一般化条件 DW-G03 を満たす)。

## 次の一手差分

### 完了

- [T-1379] 8c 条件5 (C05) の証拠契約・評価器を machine_checkable へ昇格し、
  DECIDER_VERSION を v5 へ bump、第9世代 condition-freeze record を発行した。
  §5・schedule artifact は {{D:c05-authority-deferred}} により scope 外へ確定した。
  remaining: none
  base: 863a90c8afe3806b2a30a32b2f98e0337a810a6aea2e5178869c1ce6a9b52bdf
