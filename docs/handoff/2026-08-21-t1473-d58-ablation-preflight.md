# [T-1473] D58 bench-first screening v2 初回ablationのPegasus本走 preflight
- 目的: D58 (bench-first screening v2) の初回 ablation (insight §5-7 の4基準) を Pegasus 計算ノードで
  実施する。開始直後に screening/floor/calibration 編集面の並行占有を確認し、本走の可否を判定する。
- 状態: 中断
- 最終更新: 2026-08-21 (受入 lease 他 holder 保持中のため段9 land 未実行で中断)
- 基準コミット: 5db135b0621b31aeeb94c66fbeb97fc05bf754d8 (worktree: dev-wave-t1473-d58-ablation-preflight,
  作業ツリー clean、tested main = b1c54220)

## 完了した中間成果 (ファイルパス・コミットハッシュつき)
- g++-13 blocker (旧試行 `docs/archive/worklog-phase3-0819-701.md` entry701) が
  T-1444 (D601/D628/D629、2026-08-21 land 済み) の site依存compiler解決で解消済みと確認した
  (`orchestrator/campaign/buildcache.py:1269-1273` `compilers_for_current_site()` が Pegasus では
  無印 `gcc`/`g++` を返す)。
- 資源競合の実測 (詳細は worklog fragment 本文): [T-425]・[T-972] が生存中の claude session +
  実行中 acceptance job として `screening_driver.py`/`between_run_floor.py`/S8b floor 系を
  改変中と確認 (cmdline走査・lock file・ListAgents peer session 一覧の3経路で裏取り)。[T-1438] は
  無関係 (free) と確認。
- `output/env/pegasus/calibration/registered/` の既存2件がいずれも balanced (rratio=50) で、
  read-heavy (rratio=95) 用の Pegasus calibration が未較正と確認した。
- `docs/pegasus-runbook.md:1444-1445` の既知の欠落 (`campaign` dispatch task 未実装、sanctioned
  経路なし) が解消されていないと確認した。

## 未完の作業と次の一手 (具体的に)
1. **完了**: worklog spool fragment + handoff を commit 済み (`5db135b0`)。
   `check_docs.py` = 違反なし。`spool_fold.py --dry-run` = 成功 (新規項目は
   `{{T:d58-ablation-pegasus-preflight}}`、fold 時点の実採番は dry-run 表示 `[T-1471]` だが
   並行 land でずれうるため確定値として扱わない)。`check_ai_provenance.py` = 違反なし (exit 0)。
2. **段8**: 適用済み (改善候補1件を本ファイル末尾に記録、dev-wave docs 予算満杯のため実装せず)。
3. **段9 (未完・ここで中断)**: 受入 lease を2回確認したが、いずれも他 holder
   (`holder=3bf5d510308c`) が保持中 (`state=held`、2回目 age=1585秒≈26分)。
   `python3 tools/wave_land_window.py claim --lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease
   --wave dev-wave-t1473-d58-ablation-preflight --main-sha b1c54220...` は `state=held` のまま
   拒否された (`acquired`/`held-self` に到達せず)。**fresh context が行う再開手順**:
   (a) `python3 tools/wave_land_window.py status --json --lease-dir
   /work/1/SFC/tanab/dev-wave-jobs/land-lease` で lease が空いたか確認、
   (b) 空いていれば `claim` → `python3 tools/run_tests.py` を背景実行し受入 receipt 取得 →
   `tools/dev_wave_land.py` で tested_main=b1c54220.., tested_tip=5db135b0.. を local main へ
   ff-only land (docs-only、変異 matrix・実装は無し)、
   (c) land 成功後に lease を release、`tools/collect_wave_usage.py` を実行 (login で必ず
   block される既知事象、実施記録のみ残す)。
   本 wave 自体の再調査・再投票は不要 — 受入投入だけで完結する。

## 落とし穴・気づき
- ListAgents のピアセッション一覧が、worktree の cmdline 走査・lock file 確認より速く
  T425/T972/T1438 の生死を裏取りできた (名前ラベルに `t-425 between_run_floor validation prep`
  等、タスク内容が直接出る)。cmdline 走査・lock file 確認と併用する価値が高い
  (`worktree-liveness-needs-cmdline-scan` memory の補強候補、docs 予算逼迫のため dev-wave docs
  editは見送り、記録のみ)。
- command 引数の「owner が空いている場合は…」という条件が本文中に2回、異なる帰結
  (本走 / preflightのみ記録) と共に登場していた。直前の指示文「重複または測定資源競合があれば
  本走せず zero-diff preflight に切り替える」と整合させ、2回目は「占有時」の意と解釈した
  (誤読の場合はユーザー訂正を待つ)。

## dev-wave 改善候補 (段8 裁定)
候補1件を発見。dev-wave docs (core/operations/workers/mutation.md) の3層予算は既知で満杯
(`dev-wave-docs-compression-breaks-exact-pins` memoryと一致) のため、即時の追記は試みず
候補記録のみに留めユーザー裁定へ返す。

1. **worktree/wave の生死判定に `ListAgents` のピアセッション一覧を補助手段として明記する候補。**
   現行 `docs/dev-wave/operations.md` の worktree/lease 確認手順 (該当 `DW-O` 節) は cmdline 走査 +
   lock file の中身確認を正本とするが、本 wave では `ListAgents` が同じ結論により速く到達できた
   (セッション名ラベルが対象タスクを直接示す)。「cmdline走査 + lock file」の記述へ
   「ListAgentsのピアセッション一覧も補助的に確認する」旨を1行追加する候補 (新設ではなく既存手順への
   統合)。一次資料は本 handoff・本 wave の worklog fragment。
