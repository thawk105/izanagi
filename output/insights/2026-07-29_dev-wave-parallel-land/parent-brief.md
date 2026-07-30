# T-173 dev-wave 並行 land — 親 brief

- Claude command と Codex Skill が共有する対話型 dev-wave の段 9 land 契約を並行 session 対応にする。
- repo-local worktree コンテナを ignore し、所有権を検査する local-main land helper と境界テストを追加する。
- ユーザーは `dev-wave a1` / `a2` の並行開発と、他 session 作業物が最終取り込みを妨げないことを要求した。
- tracked/staged/submodule の main dirt、未知 untracked、未監査 commit、stale 受入結果は拒否する。
- 他 session の handoff / worktree を削除・stash・commit・上書きせず、rebase / force / push を使わない。
- local main の変更は監査済み wave tip への fast-forward のみとする。
- 成果物は `.gitignore`、共通 dispatcher/reference、Codex adapter、land helper、境界テスト、D/F/phase/worklog 記録。
- `(P1)` 例外 dirt は形式が正しい他 session handoff と `.claude/worktrees/` /
  `.codex/worktrees/` コンテナだけに閉じ、その他 untracked は拒否する。
- `(P2)` 長時間 lock は採らず、受入に使った main SHA の exact 比較と ff-only の失敗で race を
  fail-closed にし、main 前進時は audit→merge→受入再走を有界反復する。
- `(P3)` main 前進は監査対象の新 upstream とするが、競合解決と受入再走が完了するまで land しない。
- 既存 supervisor checker は main unchanged / dirty / ff-chain、startup checker は fresh base を拒否する。
- 純増検出力は active handoff だけの main を受理し、未知 dirt・stale accepted-main・non-FF・race loser を拒否すること。
- helper は Python 標準ライブラリと allowlist 済み Git argv のみを使い、shell / network / remote を使わない。
- 受入は targeted pytest、mutation、`tools/run_tests.py` 全走、docs / Codex agent / provenance 検査。
- 未実装なら並行 wave が正常成果を作っても別 session の制御ファイルまたは先行 land で停止し、
  local main の開発台帳と次 wave の開始点へ反映できない。
