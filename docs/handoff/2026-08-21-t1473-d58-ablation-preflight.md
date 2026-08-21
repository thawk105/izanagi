# [T-1473] D58 bench-first screening v2 初回ablationのPegasus本走 preflight
- 目的: D58 (bench-first screening v2) の初回 ablation (insight §5-7 の4基準) を Pegasus 計算ノードで
  実施する。開始直後に screening/floor/calibration 編集面の並行占有を確認し、本走の可否を判定する。
- 状態: 作業中
- 最終更新: 2026-08-21
- 基準コミット: b1c54220 (worktree: dev-wave-t1473-d58-ablation-preflight, 作業ツリー clean)

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
1. worklog spool fragment を書き `python3 tools/check_docs.py` / `python3 tools/spool_fold.py
   --dry-run` で検査する。
2. commit (docs-only、AI-Agent trailer 付き: `role=author; scope=docs`)。
3. 段8: 本節を適用済み (下記候補を記録、実装はしない)。
4. 段9: 受入全走が必須 (zero-diff wave でも免除されない)。受入 lease は wave 開始時点で
   他 holder 保持中 (`holder=3bf5d510308c`) だった。lease 状態を再確認し、空いていれば
   `tools/dev_wave_wait.py acceptance` で claim → 受入投入 → `tools/dev_wave_land.py` で
   local main へ land。空いたままなら次の一手として記録し、fresh context に引き継いで終了する
   (強行・待機の長時間ブロックはしない)。

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
