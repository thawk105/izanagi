---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: cleanup-branches-cherry-3stage
seq: 1
title: cleanup-branches 自己改善 — 取り残し判定と worktree 占有判定を代理指標から実体へ是正した (docs + 検査 pin、branch worktree-cleanup-branches-cherry-3stage)
---

## 本文

- **/cleanup-branches の全量棚卸しを実施した (クラス 2)。削除は 1 件も行っていない。**
  branch 削除は D204 により対象を特定したユーザー指示があるときだけとし、引数なし起動は
  該当しないと判断した。worktree も自セッションでは 1 本も畳んでいない。
- **並行セッション (dev-wave manager) と担当を分割し、相互に誤りを訂正した。** 相手が worktree 残骸の
  撤去と未 land の起票、こちらが branch 棚卸しと dangling 監査を担当した。相手はユーザーから branch
  削除の基準認可を直接受けたと報告したが、**ピア経由の伝聞を自分の削除認可としては扱わなかった**
  (伝言はユーザー承認と同視しない)。相手の 7 本削除・6 件起票はこちらの関与範囲外。
- **相手の誤判定 1 件をこちらが止めた。** `cleanup-submodule-recurrence` を相手は「削除可」に
  分類していたが、failures 側 fragment だけが着地し **worklog 側 fragment が未着地の片肺 land** で
  あることをこちらの ledger 別照合が検出し、相手が撤回して [T-951] を起票した。
- **こちらの誤判定 1 件を相手が止めた。** `t737-loader-issuer-pin` の DW-O18 統合分を「未着地」と
  報告したが、同義の規則が**別文言で** `docs/dev-wave/operations.md` に実在し、wave 自体は
  作り直した別 branch `worktree-dev-wave-t737-rebuild` から land 済みだった。逐語 grep が
  文言変更で外れたのが原因で、こちらで独立に裏を取って撤回した。
- **自己改善 gate が発火し、{{F:cherry-path-existence}} を起票して command §1 / §2 を是正した。**
  占有判定の側は land 時の照合で **main 既着地の F251 + D342 と同一事象**と判明したため新規 F を
  起票せず、F251 への supersede 追記 (D342 の入口反映) だけを残した。
  実測した誤判定は 4 種 — fold 済み fragment の不在を消失と誤る偽陽性、
  path 実在を着地と誤る偽陰性、逐語 grep が文言変更と別 branch land を落とす偽陰性、そして
  `/proc/*/cwd` だけの占有走査が稼働中 worktree を残骸と誤る偽陰性。
- **占有走査の欠陥は独立に実測した。** 稼働中の 5 worktree に対し **cwd 走査は 0 件、cmdline は
  2〜4 件**ヒットした。`codex_worker_launch.py` は worktree の絶対 path を argv に持つが cwd にしない。
- **byte 予算の扱い。** command は上限 4000 に対し wave 前 3959 で余白 24 bytes しかなかった。
  §1 の当初案は +38〜+134 で入らなかったため、詳細を memory 2 本
  (`cherry-plus-judged-by-content-not-path` / `worktree-occupancy-needs-cmdline-scan`) へ置き、
  入口は §1 / §2 合わせて +14 bytes の最小是正に留めた (3973 bytes、余白 10)。
  **予算のために安全義務は削っていない** — §2 の走査対象はむしろ増やした。
- **whole-file SHA-256 pin の同期先は 3 箇所だった。** `tools/check_docs.py` の
  `CLEANUP_COMMAND_SHA256`、`orchestrator/tests/test_check_docs.py` の
  `_EXPECTED_CLEANUP_COMMAND_SHA256`、および同ファイルの逐語コピー literal
  `_SYNTHETIC_CLEANUP_COMMAND`。3 番目を落として 229 failed を実測した。
- **実装面 (Python 2 ファイル) は Codex author が書いた。** 親は自分で入れた変更を revert して
  委譲した。初回は成果物が検証器の `## 総括` 見出し要求を満たさず不受理 (rc=1、内容は正しかった)
  で、prompt へ見出し要求を明記して再投入し受理された。**検証器の見出し要求は既存 memory に
  無かった**ため {{T:codex-validator-heading}} として起票する。
- **`tools/audit_dangling_commits.py` が 900 秒で完走しなかった** (rc=124、出力 0 bytes)。
  上限 5400 秒で再投入したが本セッション内では結果が出なかった。command §1 は rc 0/1/2 の分岐しか
  書いておらず、**時間内に終わらない場合の指示が無い**。予算の都合で入口へ追記せず裁定へ返す。
- 棚卸しの実測: ローカル branch 120 本のうち 101 本が ahead=0、19 本が ahead>0。
  ahead=0 は tip が main の祖先であることと同値で取り残しは原理的に無く、
  `git branch --no-merged main` の母集合と ahead>0 は一致した。
- **land は後続の別 wave が実施した (2026-08-12 23:48 JST 開始、ユーザー依頼)。** 本 branch は
  `t952-residue-sweep` の分類表より後に作られたため群 A〜C のどこにも載らず、稼働 12 wave の
  scope 外だった。起動時に `ListAgents` 14 peer・`git worktree list` 9 worktree・
  `docs/handoff/` (README のみ) を実測し、担当の重複が無いことを確認して着手した。
- **land 側は `+` 行を内容で判定した (本 branch 自身が是正した規律の自己適用)。** 実測は 3 点 —
  (i) main の `.claude/commands/cleanup-branches.md` は旧文言 (`+` 行が真の取り残し /
  `/proc/*/cwd` の readlink 走査) のまま、(ii) main の `CLEANUP_COMMAND_SHA256` は `a92d…` で
  main 実ファイルの sha256 と一致し branch の `c133…` は未反映、(iii) 先行 wave の [T-951] は
  別 branch `worktree-cleanup-submodule-recurrence` を扱っており本 branch を回収していない。
  **path の有無ではなく本文と hash の一致で未着地を確定した。**
- **重複を 1 件検出して起票を取り下げた。** branch の failures fragment 第 2 項
  (worktree 占有判定) は、land 時点の main に既着地の **F251 + D342 と同一事象**である
  (同じ 2026-08-12 の撤去を、削除された側と削除した側から観測したもの)。新規 F を重ねると
  台帳が同じ物語を二重に持つため、**新規起票を取り下げて F251 への supersede 追記 1 行**
  (D342 の入口反映を記録) に置き換えた。command §2 の是正そのものは F251 の再発検知
  「掃除手順の生存判定に cmdline 走査が含まれること」を手順側で満たす。
- **受入は免除しなかった。** 実装面 (`tools/check_docs.py` の pin と
  `orchestrator/tests/test_check_docs.py`) を含むため、受入 lease を取得して全走した。
  byte 予算は command 3973 bytes で、追記型 positive control が要求する実質上限 3983 を
  10 bytes 下回ることを land 前に再実測した。
- **受入全走 1 走目は差分から到達不能な 2 件で赤くなり、2 走目で 2 件とも再現しなかった。**
  1 走目 (tip `32d65c89`、request `908394.nqsv`、124.49 秒) は **2 failed / 10198 passed / 65 skipped**
  で、`test_codex_worker_launch.py::test_launcher_failure_diagnostic_reports_nonzero_codex_exit_code`
  (失敗述語は `process_group_residual` / `termination_verified`。F57 系の既知の外乱型で、
  共有機で他 wave が codex 子を走らせている時間帯に発火する) と
  `test_p3_autonomous_workload_trial.py::test_origin_public_result_distinguishes_partial_from_completed`
  (`operation_id was already used with different payload bytes`、台帳に記録の無い初出) だった。
  2 走目 (tip `808bfb3f`、request `908431.nqsv`、103.50 秒、**1 failed / 10239 passed / 65 skipped**)
  でどちらも再現せず、`DW-O18` に従い実装差分へ帰属しない外乱と判定した。
- **2 走目の 1 件は main 自身の赤で、これが本 wave の land を一度止めた。**
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が `[octopus-merge]` で落ちた。原因は別セッションが 00:45:56 JST に land した 4 親の merge commit
  で、詳細と切り分け実測は {{F:octopus-merge-in-main}} に置く。**ユーザー裁定
  {{D:known-red-does-not-block-acceptance}}** (既知の赤は受入と land をブロックしない) を受けて
  land を再開し、裁定に従って稼働中の並行 12 セッションへ内容と確認手順を通知した。
- **受入は最終 tip で 3 走目を実施した。** 記録 commit を含む tip で走らせないと land が
  `tested_tip` 不一致で拒否されるためで、既知の赤 1 件以外が緑であることを確認して land した。
  合否と件数は本 wave の報告と handoff に残す。

## 次の一手差分

### 新規

- {{T:cleanup-dangling-audit-runtime}} **P3・新規**: `tools/audit_dangling_commits.py` の実行時間を
  実測し、cleanup-branches §1 へ時間切れ時の指示を入れるか監査側を高速化するかを決める。
  900 秒で完走せず、rc=124 に対する手順が無い。
- {{T:cleanup-occupancy-checker}} **P2・新規・要裁定**: worktree 削除前の占有走査
  (cwd + cmdline) を機械強制する checker を作るかを決める。現状 F251 / D342 の恒久対応は
  prompt 規律と施錠だけで、撤去は不可逆に近い。
- {{T:codex-validator-heading}} **P3・新規**: codex 成果物の検証器が要求する `## 総括` 見出しを
  dev-wave の prompt 定型へ入れる。今回 1 投入 (64 秒・model call 6) を空費した。
- {{T:octopus-merge-invariant}} **P1・新規**: `_assert_history_transition` を n 親へ一般化し
  (親状態のうち唯一の後継と state が一致することを見る = 既存 2 親ロジックの自然な延長)、
  併せて land / merge 経路で 3 親以上の merge を機械的に禁じるかを決める。
  {{F:octopus-merge-in-main}} により **main が現在この 1 件で赤**であり、修正が land するまで
  全 wave の受入が同じ赤を踏む。裁定 {{D:known-red-does-not-block-acceptance}} で land は
  止まらなくなったが、赤そのものは残っている。
