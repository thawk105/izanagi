---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-09-16
wave: dev-wave-t2641-cleanup-gate-order
seq: 1
---

## 新規

### {{F:cleanup-status-writes-index}}. 掃除手順が命じる裸の `git status` が、同手順自身が禁じる index 書き換えを行っていた [恒真ゲート]

- 事象: `/cleanup-branches` §0 は「surviving worktree の tracked/untracked file・index・設定の
  作成/編集」を禁じるが、同 command §1 は全 worktree に対して裸の `git status --short` を命じていた。
  本 wave の親が実測したところ、tracked file の mtime を変えた直後に裸の `git status --short` を
  走らせると worktree の index の md5 が `622f9487ca7db6e31d7cab9adedbf62e` →
  `107713b4710d1cdbf74ffd6734743ec0` へ変化した。同条件で
  `GIT_OPTIONAL_LOCKS=0 git status --short` を走らせた場合は md5 が変化しなかった (負の対照)。
  つまり入口が、自分の禁止に反する命令を出していた。
- 根本原因: `git status` は stat cache が古いと index を書き戻す。掃除手順はこれを知らずに
  読み取り probe として扱っていた。同じ repo の `tools/check_branch_rescue.py` は子 git へ
  `GIT_OPTIONAL_LOCKS=0` を渡しており、対策は既に別経路に存在していた。
- 恒久対応: `.claude/commands/cleanup-branches.md` §1 で `GIT_OPTIONAL_LOCKS=0 git status --short`
  を明示する。
- 再発検知: 掃除実行後の §4 事後検査 (surviving worktree・index・repo file に新しい差分が無い)。
  index の bytes 不変までは §4 の status 比較では証明できないため、疑う場合は index の
  digest を直接取る。

### {{F:occupancy-checker-sees-reader-argv}}. 占有 checker が読み取り probe の argv を「占有」と数え、並列化が過剰な保持を生む [恒真ゲート]

- 事象: `tools/check_worktree_occupancy.py` は自分と checker 起動祖先を除く全 process の
  `/proc/<pid>/cmdline` を走査し、対象 path を argv に含むものを占有源 (`cmdline`) に数える
  (`_argv_matches_targets`)。`/cleanup-branches` §1 は各 worktree の `git status` を、
  §3 は「削除の直前に対象ごと」占有検査を命じるが、**両者の時間的関係を書いていなかった**。
  対象 path を argv に持つ読み取り (`git -C <wt> status`、
  `check_branch_rescue.py --retire-worktree <wt>`) を占有検査と並走させると rc1 になり、
  削除してよい worktree が「占有」として保持される。並列化の利得を打ち消す。
  同型は dev-wave 側でも既知で、wave 撤去が rc=21 になる原因と同じ機序である。
- 根本原因: checker は「対象を名指す process が生きている」ことを占有の証拠にする設計で、
  読み手の種別を区別しない。手順側に順序制約が無かった。
- 恒久対応: `.claude/commands/cleanup-branches.md` §1 に
  「読み取り・占有検査の起動親/wrapper (検査時も生存する親含む) の argv に対象 path 禁止」と
  「対象入り argv の全読み取り終了後に §3 の占有検査へ」を置く。
  checker 側は変更しない (読み手を無条件に無視させると占有検知そのものが弱まる)。
- 再発検知: 掃除で rc1 (占有) が想定外に多い場合、まず自分の読み取り probe と wrapper の
  argv を疑う。

### {{F:t316-scratch-dir-in-repo-root-breaks-acceptance}}. repo 直下に一時 dir を作る test が、並列受入で作業ツリー清浄を前提にする test を落とす [テスト代表性]

- 事象: 2026-09-16 の受入全走 4 回すべてが child-verdict の赤で返った。赤の node は毎回異なるが
  (1 回目 10 件、2 回目 2 件、3 回目 4 件、4 回目 4 件)、本文はいずれも作業ツリーが test 実行中に
  変化したことを示していた。完全な本文に現れた実体は
  `FileNotFoundError: .../.t316-live-5i6hap18` と
  `assert {'.t316-live-butbiy4g/'} <= {...}` である。
  生成元は `orchestrator/tests/test_t316_sandbox_probe.py:1736` の
  `tempfile.TemporaryDirectory(prefix=".t316-live-", dir=_REPO)` で、**repo 直下**に一時 dir を作る。
  導入は commit `168ad3d0bebc5f910e4ffa6aba9f445c101634ef` (2026-09-15 16:35、[T-2607])、
  main に着地済み。
- 被害者 (いずれも作業ツリーの清浄・不変を前提にする):
  `test_p3_b4_producer_auth_experiment.py::test_case_failure_records_aborted_and_remaining_cases_continue`、
  同 `::test_disposable_tree_mutation_does_not_change_main_worktree` (`ScratchTreeError:
  main worktree status changed during experiment`)、
  `test_run_tests_preflight.py::test_headroom_short_queue_unavailable_cap_oom_stops_without_dispatch`、
  `test_check_ai_provenance.py::test_provenance_headroom_short_queue_unavailable_cap_oom_stops`、
  `test_p3_b4_wiring_probe.py::test_source_and_test_are_the_only_non_output_worktree_changes`、
  `test_t338_submission_gate_unit5.py::test_receipt_publish_call_sites_are_path_aware_and_allow_event_sink`。
- 根本原因: 一時 dir の親が `_REPO` である。並列 shard の受入では、この dir が存在する数秒の間に
  別 shard の test が `git status` / `git ls-files --others` を撮るため、同じ worktree を共有する
  test 間で競合する。どの node が落ちるかは shard の割り当てと実行順で変わるので、赤は毎回違う。
  変更を出した wave の受入では緑だったとみられるが、これは競合が確率的であるためで、
  欠陥が無かったことを意味しない。
- 恒久対応: 一時 dir を repo 外 (`tempfile.gettempdir()` 配下または専用 scratch root) へ移す。
  repo 内に置く必要があるなら `output/` 配下など `.gitignore` 済みの場所にする。
  本 wave の編集面 (`.claude/commands/cleanup-branches.md`、`tools/check_docs.py`、
  `orchestrator/tests/test_check_docs.py`) の外なので、別 wave が Codex author で直す。
- 同型の生成箇所 (2026-09-16 に `git grep -n "dir=_REPO" -- orchestrator tools` で実測、2 件):
  `orchestrator/tests/test_t316_sandbox_probe.py:1736` (`prefix=".t316-live-"`) と
  `orchestrator/tests/test_hooks.py:1513` (`prefix="t2146-hardlink-"`)。
  `orchestrator/tests/test_run_tests_testops_observation.py:1083` は `dir=_REPO.parent` なので
  repo 外であり該当しない。**独立 2 例あるので局所修復でなく族としての是正を検討してよい**
  (`DW-G03`)。
- 再発検知: 受入の赤 node が走行ごとに変わり、本文が worktree の状態変化を指す場合に本エントリを
  引く。`git grep -n "dir=_REPO" -- orchestrator tools` で同型の生成箇所を数える。
- **判定の注意:** 被害者 test を `flaky_test_holds.py` へ登録して迂回しない。落ちているのは
  被害者であって原因ではなく、登録すると作業ツリー清浄の検査が受入から消える。
