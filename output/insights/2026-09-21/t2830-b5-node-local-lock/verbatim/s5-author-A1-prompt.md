単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a1

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/s4-adjudication.md — **段 4 裁定とプラン v2 (本作業の正本)。「A1」節に従う**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/brief.md — 親 brief (用語「既存 3 経路」・不変条件)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s2-plan.md — 段 2 プラン (参考。v2 と食い違う箇所は v2 が優先)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a1/tools/pegasus/p3_s4_loop_pegasus.sh — 所有 file 1 (編集対象)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a1/orchestrator/tests/test_p3_s4_loop_job_contract.py — 所有 file 2 (編集対象)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a1/tools/pegasus/b10_backoff_grid.sh — 先例 (280 行付近の node-local lock)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a1/orchestrator/campaign/lock.py — lock path の決定。読めなければ即停止

## 作業 (プラン v2 の A1)

**編集してよい file はこの 2 つだけ** (どちらも tracked だが編集対象):
`tools/pegasus/p3_s4_loop_pegasus.sh`、`orchestrator/tests/test_p3_s4_loop_job_contract.py`。

現行の挙動 (変更前に報告へ明記すること): B-5 mode (`IZANAGI_S4_B5_MODE` 設定時) の driver は `IZANAGI_BENCH_LOCK` 未設定で起動され、
bench lock は既定の `~/.izanagi/bench.lock` (home 共有) になる。非 B-5 の 3 経路 — (a) proposal 単独、(b) proposal + pair
(`IZANAGI_S4_STOCK_CONTROL=1`)、(c) fixture — も同じ。

1. job body: B-5 分岐内の `  b5_rc=0` と B-5 driver 起動行 (`"$PY" -B -m orchestrator.campaign.b5_generator_contrast ...`) の間に、
   1 行 `  export IZANAGI_BENCH_LOCK="$TMPDIR/bench.lock"` を足す。**他の行は 1 byte も変えない** (非 B-5 経路・prebuild・trap・既存 pin 対象の literal)。
2. test harness `_run_actual_job_body_through_driver`:
   - harness が組む環境から `IZANAGI_BENCH_LOCK` を除去する (外部の値で観測が汚れないように)。
   - fake driver (`python3.10` stub の `-m` 分岐) が driver 起動ごとに `{"TMPDIR": <値>, "IZANAGI_BENCH_LOCK": <値または null>}` を
     別 file に JSON lines で追記する (path は harness が新しい env 変数で渡す。例 `IZANAGI_TEST_DRIVER_ENV`)。
   - **harness の戻り値の形 (3 要素) と、既存の `driver-evidence.json` の辞書比較は変えない。** 観測 file は呼出し側 test が読む
     (読み出し用の小さい helper を足してよい)。
3. 既存 test に観測の assert を足す (新しい test 関数は原則作らない):
   - `test_b5_actual_shell_one_driver_and_trap_rc` (全 arm・全 rc): driver が観測した `IZANAGI_BENCH_LOCK` が
     `<scratch-base>/<PBS_JOBID の path 成分>/bench.lock` と完全一致し、`TMPDIR` がその親と完全一致する。
     **期待値は job body の path 規則 (harness が置換する `scratch_base` と job body の `pbs_jobid_path_component` の作り方) から独立に組み、
     観測値から作らない。**
   - `test_default_job_invokes_driver_once` (proposal / fixture、stock 未設定・0) と `test_pair_job_invokes_one_driver_with_both_modes`:
     driver が観測した `IZANAGI_BENCH_LOCK` が null。
4. 次は**足さない**: 新しい静的 pin (`B5_PINS` / stage order marker への追加)、継承値専用の test、argv の NUL bytes 記録。

## 制約 (すべて守る)

- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない** (`docs/` 配下、`docs/handoff/` への file 作成、`tools/pegasus/README.md` を含む)。所有 2 file 以外の file を作成・編集しない。
- **テストを走らせない** (`tools/run_tests.py`、`python3 -m pytest`、`pytest.main` の埋め込み、test file の自走 harness のいずれも使わない)。
  親が計算ノードで焦点走を行う。報告は「実装済み・未実走」と書く。静的検査 (`bash -n tools/pegasus/p3_s4_loop_pegasus.sh`、
  `python3 -m py_compile orchestrator/tests/test_p3_s4_loop_job_contract.py`) は行ってよい。
- 追加した 1 行が既存の制約 meta-test に触れないかを**自分で洗い出して静的に確認する** (親の名指しを網羅と見なさない)。
  少なくとも: `_assert_static_job_stage_order` の marker 出現回数、`B5_PINS` と `test_b5_fragment_mutants_have_one_static_failure`、
  `test_b5_duplicate_driver_and_late_branch_are_rejected`、`test_job_body_has_valid_stdin_shell_syntax`、`test_k2_argv_expansion_is_proposal_only`、
  実 shell harness のアンカー置換 (`count == 1`)、`_shell_submitter_violations`。他にもあれば挙げる。
- テストを甘くして緑にしない (期待値の緩和、`in` 検査への置換、既存 assert の削除をしない)。期待値に揮発値 (tree hash 等) を焼き込まない。
- 指示外の受理集合を変えない (job body の refuse 条件・rc を変えない)。規律 2 を緩めない。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 変更前の挙動 (上記の確認)
2. 変更した file と箇所 (関数名・行)
3. 静的検査の結果 (実行したコマンドと rc)
4. 洗い出した meta-test と、それぞれが追加行で影響を受けるか
5. 所有外の caller・共有 fixture・consumer test (`test_pegasus_tools.py`、`test_hooks.py` など) への波及の静的列挙
6. 未実走であることの明記と、親が走らせるべき nodeid の候補
最後に `## 総括` を置く。
