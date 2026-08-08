段 6 fix v3 を実装しました。段 6 裁定との食い違いは確認していません。

- [wave_land_window.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/tools/wave_land_window.py:243)
  - sidecar lease の `claim` / `release` / `status` / `message` を実装。
  - `O_CREAT|O_EXCL|O_NOFOLLOW`、fd の `fstat` mtime、owner digest 照合、stale 回収を実装。
  - `flock` と inode 再照合で stale 回収・release 間の競合を保護。
  - slug は SHA-256 先頭 12 桁だけを出力。`prog=wave-land-window` に固定。
  - land JSON の status 型、allowlist、40hex、duplicate key、64 KiB 上限を fail-closed に維持。
  - production は 537 行から 460 行へ縮小。
- [test_wave_land_window.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-peer-land-coordination/orchestrator/tests/test_wave_land_window.py:95)
  - 必須正例、MX1〜MX7、2399/2400/2401 境界、命令風 slug の全出力経路を収録。
  - oracle は独立 literal で、production 定数を参照していません。
  - list / dict / 数値 status の rc=3 も固定しました。

削除した機能と波及:

- `declare` / `peers` / `land-intent`、handoff の読み書きを production から完全削除。
- repo 内の実行可能 consumer に旧 API の参照はありません。
- 対象テストは旧 handoff 契約から全面的に差し替えました。
- 旧参照は段 4 裁定、レビュー、ログ等の履歴 artifact にのみ残ります。
- 親所有の `.claude/commands/dev-wave.md` と `docs/pegasus-runbook.md` の既存差分には触れていません。

検査状況:

- Python AST 構文確認: 成功。
- CLI help smoke: rc=0、固定 `prog` を確認。
- 一時 directory で `claim→held→release→別 wave claim→status→release`: rc=0。
- pytest、MX1〜MX7 変異、meta-test、受入全走: **実装済み・未実走**。緑は主張しません。

## 総括

- 実装範囲: production tool と専用テストのみ。
- handoff 経路と旧 3 機能を削除し、sidecar lease へ差し替え済み。
- 構文確認と逐次 CLI smoke は成功。
- pytest・変異・並行 race・全受入は未実走。
- 主な残存リスクは実 lease filesystem 上の並行競合検証と親 caller 統合。
- docs 編集・commit は行っていません。