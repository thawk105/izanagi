---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-23
wave: dev-wave-stage9-self-cleanup
seq: 3
---

## 新規

### {{F:occupancy-zombie-permanent-block}}. zombie 1 本で占有検査が恒久的に判定不能になり、worktree 掃除が構造的に不可能だった [恒真ゲート] [誤前提]

- 事象: `tools/check_worktree_occupancy.py` が、対象 path に関係なく
  `status=indeterminate` / rc=2 を返し続けた。pid 1035937 (`State: Z (zombie)`、python3) で
  2 回連続再現した。`/cleanup-branches` §3 は「rc0 のみ進み、rc2=判定不能は停止」と定めるため、
  **掃除の関門を誰も通れない**状態が続いていた。実際の滞留は worktree 31 本・branch 114 本で、
  land 済み wave のものも残っていた。
- 根本原因: zombie は `/proc/<pid>/cwd` を持たないが `/proc/<pid>/` 自体は残る。
  `_pid_disappeared()` が False を返すため `issues` へ積まれ、`status` が `indeterminate` に
  倒れる。zombie は cwd も fd もアドレス空間も持たず、定義上何も占有できない。
- 恒久対応: {{D:occupancy-zombie-and-bounded-rescan}}。zombie を非占有として数え、
  件数を `unreachable.zombie` へ出す。`orchestrator/tests/test_check_worktree_occupancy.py` の
  zombie 正例・非 zombie 負例で固定する。
- 再発検知: 変異 MUT-5 (zombie 判定を落として従来どおり issue へ積む) が
  `test_main_zombie_missing_cwd_is_counted_without_issue_mut5` を殺すこと。

### {{F:gate-predicate-unreachable-value-range}}. gate の述語を到達可能な値域を測らずに採用し、同じ wave で 2 度撤回した [誤前提] [恒真ゲート]

- 事象: (1) 敵対所見を採って `unreachable.cwd_permission == 0` を要求したが、この共有
  login node の実測は 2,020〜2,213 (cwd を読めない他ユーザーの process 数) で恒久的に不成立
  だった。(2) 代替として same-uid 到達不能 process の comm 固定 allowlist を入れたが、
  焦点走が 11 件赤になり全件の理由が `comm is not allowlisted: 'nqs_shpd'` だった。
  `nqs_shpd` はバッチスケジューラの常駐 process で、**テストを計算ノードへ dispatch した
  瞬間に同 uid で現れ**、走行終了直後には消える。撤去が必要になるのはまさにその直後である。
- 根本原因: `DW-O13` は「gate 入力が実成果物のどの field に存在するか確認する」と定めるが、
  親は field の実在だけを確かめ、**その field が取りうる値**を測らなかった。
- 恒久対応: {{D:gate-predicate-needs-reachable-value-measurement}}。
- 再発検知: 述語を追加する裁定に、実測した値域を書く欄が無ければ段 4 で止める。

### {{F:preflight-gate-masked-by-post-destruction-layer}}. preflight の安全検査が壊れても既存テストが 1 件も落ちず、2 層目は破壊の後にしか無かった [恒真ゲート]

- 事象: `tools/dev_wave_cleanup.py` の preflight branch ancestry 検査を無効化する変異
  (MUT-1) が SURVIVED した。mask 源は `branch-recheck` 段の 2 つ目の ancestry 検査だが、
  それは `rm -rf` と `worktree prune` の**後**にある。つまり preflight が退行すると
  「worktree を消してから拒否する」挙動になり、既存の負例はその差 (rc=20 で無傷 /
  rc=30 で撤去済み) を区別していなかった。同じ probe で、allowlist へ
  `worktree remove --force` を足す変異 (MUT-4) も SURVIVED した。禁止 verb のテストが
  source 走査と実行 argv spy の 2 面だけで、allowlist が禁止 argv を拒否すること自体を
  検証していなかったためである。
- 根本原因: 防壁が 2 層あるとき、下層のテストが上層の破れを吸収する。テストが
  「最終的に拒否されたか」だけを見て「どの段で、何を保存したまま拒否されたか」を見ていない。
- 恒久対応: preflight 拒否を単独で pin し、rc=20・phase・directory / tracked file /
  administrative record / branch ref / worktree HEAD / lock の全保存を要求する
  `test_preflight_ancestry_gate_rejects_before_any_removal`。allowlist は
  `test_git_argv_validator_directly_rejects_forbidden_commands` で禁止 argv を直接拒否させる。
- 再発検知: 変異 MUT-1 / MUT-4 が上記 2 node をそれぞれ殺すこと。
  敵対レビュー 2 本ではどちらも出ず、変異でだけ顕在化した。

### {{F:codex-launcher-evidence-invalid-on-healthy-output}}. launcher が健全な成果物を evidence 不正として 3 回不採用にした [手順漏れ]

- 事象: 本 wave の codex 子 11 本のうち 3 本 (author / review-luna / fix5) が
  `outcome=not_accepted` / `evidence_status=invalid` で終わり、成果物 md が書かれなかった。
  親が rollout を検算すると、`session_meta` 1 件・`turn_context` 1〜2 件・
  events jsonl の全行が妥当な JSON・`termination_verified: true`・`codex_exit_code=0`・
  上限抵触なしで、いずれも内容の欠陥ではなかった。3 本とも編集は完了しており、
  attempt 出力から回収して `tools/check_codex_output.py` rc=0 を確認できた。
- 根本原因: 未特定。`_evidence_status()` は `stdout_invalid` / `stdout_pending` /
  rollout の `invalid` / `pending` / `session_meta_count != 1` / `context_count < 1` の
  いずれかで `invalid` を返すが、事後の artifact はどれにも該当しなかった。
  supervision 中の tailing 状態に由来する疑いが強い。
- 恒久対応: 未了。{{T:codex-launcher-evidence-flake}} で条件を特定する。
  暫定の運用は「`not_accepted` を見たら rollout と events を親が検算し、
  健全なら attempt 出力を回収して `check_codex_output.py` rc=0 で採用する」。
- 再発検知: receipt の `outcome` と `evidence_status` を wave 末に集計する。

## supersede 追記

- F26 **supersede: 2026-08-23** — 2026-08-01 と 2026-08-05 の再発が指摘した「dev-wave の段 9 は自分の worktree を畳むよう求めるが、その手順の正本が `/cleanup-branches` §3 にあることを指していない」は、経路の新設で閉じた。実測すると段 9 に撤去義務自体が存在しなかった。`docs/dev-wave/operations.md` の `DW-O28` と条件 dispatch 27、および `tools/dev_wave_cleanup.py` が正本である ({{D:dev-wave-self-cleanup-after-land}})。`/cleanup-branches` §3 の撤去順と F51 由来の記述の是正は {{T:cleanup-branches-procedure-drift}} で別途行う。
