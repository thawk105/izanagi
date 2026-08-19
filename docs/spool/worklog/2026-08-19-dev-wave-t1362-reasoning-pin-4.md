---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-19
wave: dev-wave-t1362-reasoning-pin
seq: 4
title: T-1362 の受入投入で repo 全体を塞ぐ未着手の2件を検出した (docs のみ、branch worktree-dev-wave-t1362-reasoning-pin)
---

## 本文

- T-1362 本体の実装・レビュー・fix・変異matrix・記録は commit `70fb8eab` までで完了済み
  (前 fragment 参照)。段9 の local main 取り込みで `b7f7d934` (main) を merge (`b7fd16d8`)
  したうえで受入全走を投入したところ、T-1362 と無関係な2件の repo 全体の問題を検出した。
  T-1362 自体を巻き戻す必要はないが、land はこの2件が解消するまで完走できない。
- 検出1: `orchestrator/campaign/s8c_preregistration.py` の `MAX_BATCH_REQUESTS = 50_000`
  (`_batch_oids`) を、`test_s8c_preregistration_invariant.py` の2テストが実測50072で超過した。
  main単独 (`b7f7d934`) では合格、本waveのtip単独 (`b7fd16d8`、mainに対しcommit 7件追加) では
  失敗を実測確認済み — 対象範囲の commit 数に比例して増える計算であり、T-1362 の変更内容とは
  無関係 (`orchestrator/campaign/s8c_preregistration.py` 等は一切触れていない)。**main は
  このテストの限界にほぼ到達しており、次にlandするどのwaveも同じ形で超過しうる。**
  成長比例costをテスト経路に入れない既存規律 (`test-time-regression-rule`) との関係を
  含め、恒久対応の判断はユーザー裁定へ返す (下の新規task参照)。
- 検出2: `tools/check_acceptance_reds.py` の probe worktree 経由の非帰属判定を3回連続で
  試みたが、3回とも `orphan-hold` (`job-may-remain-without-terminal-evidence`、
  `gate.reason=request-absent`) で `status=invalid-input` に終わった。`qstat` の出力内容
  (rcでなく) で対象requestの不在を都度確認し、probe worktreeも都度cleanと確認したうえで
  scratch (`/tmp` 配下、repo外) を破棄して再試行したが同じ結果だった。F383 の「併発した
  二次障害」と同じ orphan-hold 機構だが、F383 の根本原因 (変異走行中のdocs編集による
  共有木byte変化検出) とは異なり、今回は変異走行や tree 編集と無関係な単発の
  `check_acceptance_reds.py` 起動そのもので発生した — 別トリガーの再発として記録する。
- 上記2件により、`tools/dev_wave_wait.py acceptance` は受入command自体はrc=1で完走した
  (child log は repo外 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1362-reasoning-pin/
  acceptance-child-1.log` に保全済み) が、非帰属判定を確定できず `stage=acceptance-red-check
  rc=70` で lease は自動解放された (`wave_land_window.py status` で `state=free` を確認済み)。
  T-1362 自身の変更ファイルに起因する赤は0件 (受入全走 687件中この2件だけが赤)。

## 次の一手差分

### 新規

- {{T:s8c-batch-limit-blocks-land}} **P1・新規**: `s8c_preregistration.py` の
  `MAX_BATCH_REQUESTS=50_000` が repo 履歴成長で実測超過し (50072)、`test_s8c_preregistration_invariant.py`
  の2テストがmain上でも今後の任意waveのtip上で赤になりうる。`test-time-regression-rule`
  (成長比例costをテスト経路に入れない・成長比例テストは削除でなく恒久保留・解除はユーザー
  明示命令のみ) との関係を含め、恒久対応をユーザー裁定へ返す。
- {{T:check-acceptance-reds-orphan-hold-non-mutation-trigger}} **P2・新規**:
  `tools/check_acceptance_reds.py` のprobe worktree dispatchが、変異走行や tree 編集を伴わない
  単発起動でも3/3の頻度で `orphan-hold` に到達した (2026-08-19、本 job のPegasus環境)。
  F383 の記録は変異走行中のdocs編集という別トリガーのみを前提にしており、
  今回のトリガー非依存の再現性は未調査。dispatch/qstat応答性の環境要因か
  `check_acceptance_reds.py` 自身のqstat判定条件の欠陥かを切り分ける追加調査が必要。
