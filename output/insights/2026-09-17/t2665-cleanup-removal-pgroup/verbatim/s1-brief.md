# 段 1 brief — [T-2665] 並列撤去の子 process を親の process group に置き、親 kill で道連れにする

wave: dev-wave-t2665-cleanup-removal-pgroup / worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2665-cleanup-removal-pgroup (main ad12ba35b と同一)

## 研究前進
- 土台 (運用の安全側)。止めている研究は無い。根拠は確定済みユーザー裁定 (第 20 回 /rulings 項 32) が「実装手番」を指示したことで、DW-S04 の「承認済み裁定は不採用にしない」に従い実装する。P3 既定除外の例外は command 引数に明記済み。
- 完了判定: `/cleanup-branches` §3 手順 3 の並列 directory 撤去が、(a) 子 process を親と同じ process group で起動し (setsid / nohup / start_new_session なし)、(b) 親の停止で子も止まり、(c) 中断・不明・失敗を完了と数えず prune へ進まない — を機械 (tool + test + 変異) で示せること。

## 確定済みユーザー裁定 (逐語は docs/spool/decisions/2026-09-17-rulings-all-20260917-1.md 項 32、main 未採番 `{{D:rulings-full20-verdicts}}`)
「撤去の子 process は親の process group に置き (setsid しない)、親 kill で道連れにする。中断・不明は完了扱いせず、prune へ進まない。文書収容 (byte 予算) の部分は D782 の AI 手番のまま。」
「理由: 孤児が削除を続ける形は撤去対象の確定後の安全側でない。」
起票原文 (archive entry 1526 の次の一手 [T-2665]): 「親 kill 時に子が残るか道連れかは launcher の構成次第で未定義。process group の扱いと、不明・中断を完了扱いしない判定手順を決める。入口の byte 予算の外に置けるかも同時に判断する。」

## 段 1 実測 (現物同定・新事実)
1. `tools/dev_wave_cleanup.py` (段 9 の自己撤去専用) は `_remove_verified_tree` (869-871 行) で `shutil.rmtree` を**同一 process 内**で行う。子 process なし・並列なし・prune まで直列。→ 本件の「並列撤去の子 process」はここに無い。**変更対象外**。
2. 並列撤去は `.claude/commands/cleanup-branches.md` §3 手順 3 (57-60 行) の手動手順「dir 撤去は 1 件 1 process・各長い timeout。一括ループ禁止、path 相互非包含時のみ並列可。…全撤去 process 終了・成功確認後 (不明・中断なら停止)」だけ。**launcher は repo に存在しない**。
3. `hooks/guard_bash.py` は `rm -rf <worktree>`、`rm -rf a & rm -rf b & wait`、`nohup setsid rm -rf <worktree> &` を**すべて許可**する (decide() を probe で実測、site=None)。裁定が禁じる setsid 形を機械は止めない。
4. repo の背景 worker 慣行は全て `start_new_session=True` (codex_worker_launch / dev_wave_wait / mutation_*)。F 台帳 4085 行付近「`&` だけでは process group が tool 側に紐づいたまま (殺されるかはタイミング依存)」は codex 子を**生かす**ための記録で、撤去はその逆 (親と共に止める) が裁定。
5. `.claude/commands/cleanup-branches.md` = 6203 bytes / 上限 6204 (`tools/check_docs.py:285`)、whole-file sha256 pin `75939b07…` が `tools/check_docs.py:752` と `orchestrator/tests/test_check_docs.py:580` に 2 箇所。§3 冒頭 2 行は exact literal pin (`CLEANUP_OCCUPANCY_CONTRACT`)。先例 T-2641 (3ce4dafbc) は command + 両 pin + 予算を同 commit で更新。
6. 新規 test file は `test_plain_runner_coverage` により自走 harness (`__main__`) 必須。`tools/README.md` は tool 一覧を持たず、地図追記は不要。

## scope (実装面 = Codex author、D95)
- S1 新規 `tools/cleanup_remove_dirs.py` (名称は plan で確定): 引数 `-- <絶対 path>...` (実在 directory・symlink 不可・相互非包含・cwd が対象外・1 件以上)。1 path = 1 子 process (`rm -rf -- <path>` 相当)、**`start_new_session=False`・preexec_fn なし**、起動直後に `os.getpgid(child) == os.getpgrp()` を実測し不一致なら fail-closed。SIGTERM/SIGINT を受けたら生存子へ同じ signal を転送し、中断として扱う。各子の終了後 `lexists` で不在を検証。判定: removed / failed (子 rc≠0 または残存) / interrupted (signal・timeout) / unknown (判定不能)。rc: 0 = 全件 removed、1 = failed あり (中断なし)、2 = interrupted / unknown あり、64 = usage。**prune・detach・branch 削除は一切しない**。stdout に 1 path 1 行の JSON + 総括。
- S2 新規 `orchestrator/tests/test_cleanup_remove_dirs.py` (自走 harness 付き): 正例 (2 dir 並列撤去 → rc0・不在・子 pgid == 親 pgid の観測)、負例 (中断 → rc2 かつ対象が残る、失敗 → rc1、入れ子 path → 64、cwd 内 → 64、不在 path → 64)。中断の負例は決定的に書く (seam の要否は plan が提案、DW-O14: 機構を構成する呼び出しの差し替え禁止)。
- S3 docs: `/cleanup-branches` §3 手順 3 を launcher へ差し替え (D782: まず既存記述の削減で予算内に収める。収まらなければ上限の最小増分)。`tools/check_docs.py` の sha pin・TextLimit と `test_check_docs.py` の pin を同 commit で更新 (実装面、author)。
- scope 外: `tools/dev_wave_cleanup.py` の変更、汎用 process supervisor (任意 command・再起動・監視)、PR_SET_PDEATHSIG (SIGKILL の親には届かない限界として記録)、prune の自動化、Codex overlay `.agents/skills/cleanup-branches/SKILL.md`、`/cleanup-branches` の削除述語・閾値の変更。

## 不変条件
- `/cleanup-branches` の削除が成立する述語・閾値・評価順は変えない。launcher は与えられた path しか消さず、§1〜§3 の gate を代替しない。
- rc 0 は「全 path について子 rc 0 かつ撤去後 lexists False」の時だけ。中断・不明を 0 にする経路を作らない。
- 子は親の process group (setsid / nohup / start_new_session / preexec_fn=os.setsid を使わない)。
- 新しい gate・台帳・framework を足さない。DW-G05: 放置時の成果物影響 = 掃除中の親停止で孤児 rm が確定前の path を消し続ける (certified 成果物には非影響、作業ツリー安全側)。

## 割れうる前提 (親の provisional 裁定・攻撃対象)
- (P1) 現物 = §3 手順 3 の手動並列撤去であり `dev_wave_cleanup.py` は対象外。
- (P2) 形 = 新規最小 launcher tool。docs-only では機構が検査不能で guard も setsid 形を止めない (実測 3)。「局所修正」の解釈: 未定義だった launcher を定義する最小差分。
- (P3) TERM/INT の子への転送を含める (裁定の機構は process group。転送は「親 kill」が plain `kill <pid>` の時にも道連れを成立させる局所補強。SIGKILL は限界)。
- (P4) 中断の負例は seam なしで決定的に書ける (例: 子が停止するまで親が SIGSTOP 等を使わない設計で、test が親へ TERM を送る前に子の生存を観測する)。書けなければ最小 seam の可否を段 4 で裁定。

## 並列分割方針
- 段 2 plan 1 本 (read-only)。段 3 consult 2 本 (レンズ A: 正しさ境界 — 完了誤判定・孤児経路・pgid 検査の恒真化 / レンズ B: 整合・実効性 — §3 との接続・byte 予算・pin 閉包・test の決定性・scope 膨張)。段 5 author 1 本 (tool + test + docs + pin)。段 6 review 2 本 + fix。
- 受入: login node の焦点走 (`test_cleanup_remove_dirs.py`、`test_check_docs.py`、`test_branch_rescue_ledger.py`、`test_plain_runner_coverage.py`) + 変異 matrix + 全走受入 (計算ノード dispatch)。
