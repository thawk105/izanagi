---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-b10-signal-trap
seq: 1
title: b10 job の signal handler が set -u で落ちて打ち切り理由を失っていた欠陥を直す (コード + docs、branch worktree-dev-wave-b10-signal-trap)
---

## 本文

- **ユーザー指示で起票した単発修正。** エントリ 1186 の機構欠陥 4 (`local name=$1 number=$2
  rc=$((128 + number))` が語展開順序により `set -u` で落ち `write_failure` へ到達しない) は
  「本 wave では未修正」と記録されていた。本 wave はその 1 箇所だけを直し、
  仮想リスク向けの gate・検査・台帳・一般化は scope 外とした。
- **族一般化は成立しないと実測で確定した。** `tools/`・`orchestrator/`・`hooks/` の全 shell script
  (`.sh` / `.pbs` / shebang 付き) を「同一 `local` 文の中で先行代入名を後続 RHS が参照する」形で
  機械走査した結果、hit は当該 1 行のみ。`tools/pegasus/` の姉妹 handler 6 本はいずれも
  `local` を分けているか算術を同じ文へ入れていない。DW-G03 の独立 2 例が無いため
  検査 tool の新設も他 script の予防的書き換えも行わなかった。
- **既存テストは恒真に近い存在検査だった。** `assert "on_signal" in job_text` は壊れた handler も
  通す。追加したテストは production file から handler の実体を一意に切り出して実行し、
  記録引数と終了 status を見る。変異検査で両方向とも期待どおり赤になることを確認した。
- **計算資源の飽和を実測した。** 焦点走は 3 回連続で `queue-wait-timeout` (rc=16)。login node は
  実効天井 15.03 GB に対し回収不能量 7.79 GB・他 wave の生存予約 6.47 GB で予算が負になり、
  自動判定は必ず dispatch を選ぶ。同時刻の queue には同一アカウントの `izdw-*` が 7 件。
  1 度 `qstat -f` 自体が 30 秒で応答せず失敗した。いずれも混雑由来で自分の差分に帰属しない。
- **変異 harness の走行後検査が並行 wave で落ちた。** 1 回目は変異結果 (両 KILLED、baseline PASSED、
  matching=2) を得た後、wrapper の「source/main 共有木の観測 bytes が不変」だけが不成立で中止した。
  共有 checkout を別 wave が触ったためで、harness 自身の検査は通っている。source worktree の
  clean・HEAD・修正 bytes を確認して 2 回目を走らせ、`shared_snapshot_matches=true` で完走した。
- 材料は `output/insights/2026-09-02_b10-signal-trap/` (README、変異 spec・報告、実装子逐語)。

## 次の一手差分
