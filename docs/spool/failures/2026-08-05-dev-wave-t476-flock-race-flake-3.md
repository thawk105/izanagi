---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t476-flock-race-flake
seq: 3
---

## 新規

### {{F:mutation-run-vs-acceptance-run}}. 変異注入中の worktree で受入全走を投入し、mutant 入りの木を計測した [計測汚染]

- 事象: 変異 harness が wave worktree へ mutant を注入して走らせている最中に、同じ worktree から
  受入全走を dispatch した。全走は mutant 入りのテストを実行し、`1 failed / 5899 passed` を返した。
  traceback に `mutant: drop the PROBE notification` が写っていたため気づいた。
  この赤は成果物の欠陥ではなく計測の無効である。
  同じ wave でもう 1 件、**全走の実行中に spool fragment を編集し `git add` した**ため
  `test_check_docs.py::test_real_repo_clean` が中間状態を拾って赤くなり、`git add` が
  real_repo 系テストの `index.lock` とも衝突した。受入全走は worktree に対して git 操作を行う。
- 根本原因: 変異 harness の repo lock (`flock` 単一走行) は**他の harness だけ**を排除する。
  素の `dispatch_compute` / `run_tests.py` は lock を取らないため、同じ worktree で
  並行投入できてしまう。親の側にも「harness 走行中は本走を投入しない」という規律が無かった。
  `DW-O19` は「本走は統合 commit 後に限る」までしか言っておらず、
  変異注入中という別の禁止区間を持っていない。
- 恒久対応: memory `no-acceptance-run-during-mutation` —
  「**計測中の worktree は読むだけにする**。harness 走行中の worktree へ全走・部分走を投入せず、
  全走の実行中は編集・stage・commit・merge をしない。投入前に `pgrep -f` を worktree path で
  一意化して不在を確認し、harness / 全走の `.done` 後の走行だけを受入結果に数える。同時に進めたい
  ときは片方を別 clone へ逃がす」。`docs/dev-wave/mutation.md` の `DW-M05` へ入れる案は、
  同 directory の byte 予算が上限まで残り 4 bytes で入らず、**上限を上げない方針**に従って
  memory へ置いた。`dispatch_compute` 側で harness 生存時に fail-closed で拒否する機械 gate は
  防壁の新設にあたるため実装せず、裁定パッケージとしてユーザーへ返す。
- 再発検知: 受入結果の traceback / stdout に `mutant:` を含む赤は計測汚染として扱い、
  実装差分へ帰属させない。harness の `.done` が出た後の走行だけを受入結果に数える。
