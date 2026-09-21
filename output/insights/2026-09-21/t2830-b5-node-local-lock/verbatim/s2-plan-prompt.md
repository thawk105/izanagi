単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/brief.md — 親 brief (scope・不変条件・用語「既存 3 経路」・provisional 裁定 P1〜P3)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/T-2830-origin.md — 依頼の逐語。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/d2199.md — D2199 の逐語 (試走で確定した運用事実)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/d2205.md — D2205 の逐語 (T-2795: pair mode は driver 1 起動)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/insight-6-3.md — 試走の所要実測。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/verbatim/insight-8.md — 本走認可に向けた裁定パッケージ。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/p3_s4_loop_pegasus.sh — 変更対象 1 (job body、681 行)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/b5_contrast_launch.py — 変更対象 2 (login 側 launcher)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/b10_backoff_grid.sh — 先例 1 (280 行で node-local lock を設定)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/tools/pegasus/a5_second_boot_backoff_sweep.sh — 先例 2 (259 行)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_p3_s4_loop_job_contract.py — job body の静的契約と実 shell harness。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/tests/test_b5_contrast_launch.py — launcher の argv exact 検査。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/lock.py — bench lock の既定 path。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/p3_s4_loop.py — cache root の決定 (`isolate_worktree` 分岐)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/patchharness.py — `checkout()` の `git worktree add`。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2830-b5-node-local-lock/orchestrator/campaign/buildcache.py — build cache の claim (`_acquire_v2_claim`)。読めなければ即停止

## 親の実測 (段 1、本 prompt 作成時点)

- bench lock を取るのは driver 内部だけ (`pipeline.py` の 3 箇所、`backoff_overthrottle.py` / `backoff_requested_us.py` / `b10_backoff_shape_sweep.py`)。
  job body の prebuild 段 (heredoc の Python) は取らない。`verify_fanout_worker.py` は `IZANAGI_BENCH_LOCK` を一時的に書き換えて復元する。
- 試走の submit-tree (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/submit-tree`) は main repo の git worktree で、
  git dir = `<main>/.git/worktrees/submit-tree`、その CCBench の git dir = `<main>/.git/worktrees/submit-tree/modules/external/ccbench`
  (worktree ごとに独立)。git common dir は 4 本とも `<main>/.git` になる。
- job body の現 sha256 = f72fd861…、launcher = e199015b…。どちらも repo 内に literal pin は無い (試走の reservation.json は旧 sha の記録)。

## 依頼

file:line 粒度の実装プランを起草する。次を必ず含める。

1. job body への node-local lock の挿入位置 (行・前後のアンカー文字列)。親の provisional は **B-5 分岐内・driver 起動直前 (P1)**。
   B-5 mode の全 bench lock 取得を覆うことの根拠と、反証 (job 全体にすべき理由) があれば示す。
2. launcher を job ごとの submit-tree に対応させる設計 (P2 / P3)。`SubmitTree` / `validate_submit_tree` / `pilot_jobs` /
   `build_job_environment` / `qsub_argv` / `_qsub_argv` / `launch` / `main` のどれをどう変えるか。CLI 引数の形 (例: arm ごとの
   `--repo-root-<arm>` か、`--submit-tree ARM=PATH` の反復か)。4 本の相互関係の検査 (同じ HEAD、互いに別 path、同じ common repo) を
   新しい gate にせず既存 `validate_submit_tree` の反復で済ませる形。qsub の cwd (`runner(argv, cwd=tree.repo)`) の扱い。
   代替案 (1 本共有のまま cache 公開競合を検査) と比べて、本走で落ちない方を根拠つきで選ぶ。
3. 既存 3 経路 (brief の用語) の driver argv の bytes 不変を固定する test の具体案 (file・test 名・アサートする literal)。
   既存の `test_complete_k2_environment_reaches_actual_job_driver_argv` などとの重複は避け、足りない分だけにする。
4. B-5 mode の driver が node-local lock path を環境で観測することの test 案 (実 shell harness `_run_actual_job_body_through_driver` の
   fake driver が env を記録する形に拡張できるか)。非 B-5 経路では `IZANAGI_BENCH_LOCK` が設定されないことの test 案。
5. 触ると壊れる既存 pin の一覧 (静的契約の marker 列 `_assert_static_job_stage_order`、`B5_PINS`、実 shell harness の
   アンカー文字列、`test_four_qsub_argv_and_explicit_environment_are_exact`、`test_main_dry_run_validates_tree_and_prints_four_jobs`) と、その更新方法。
6. 変異負例の候補 (どの 1 行を変えるとどの test が落ちるか、最低 5 件)。

## 制約

- sandbox は read-only で書込可能な tmp が無い。**静的検査だけでよい。** テストの実走・計測は親が行うので、実走していない事柄を「確認した」と書かない。
- B-5 本走は未認可。投入手順・qsub の実行は書かない。
- gate・検査・台帳の新設は scope 外 (既存 test の拡張と、launcher の既存検査の反復は scope 内)。
- `orchestrator/campaign/loop.py` / `p3_s4_loop.py` は編集しない (contract loader closure、D2205 の結合検査)。
- 規律 2 を前提にする。lock の所在を変えても、performance verify pass と bench が lock 下で回る構造は変えない。
- 予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終える。

## 出力形式

項目 1〜6 を見出しで分け、最後に `## 総括` を置く (採否の要点を 5 行以内)。
