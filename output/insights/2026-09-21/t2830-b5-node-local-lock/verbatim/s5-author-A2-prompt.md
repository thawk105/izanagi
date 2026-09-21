単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a2

必読事項の射影: (下記をすべて読む。読めなければ即停止し、読めなかった path を報告する)

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/s4-adjudication.md — **段 4 裁定とプラン v2 (本作業の正本)。「A2」節に従う**。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/brief.md — 親 brief (追補 2 = D2200 項 1 の確定裁定)。読めなければ即停止
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2830-b5-node-local-lock/codex/s3-consult-B.md — 過剰・削除レンズ (v2 が採った縮小の根拠)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a2/tools/pegasus/b5_contrast_launch.py — 所有 file 1 (編集対象)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a2/orchestrator/tests/test_b5_contrast_launch.py — 所有 file 2 (編集対象)。読めなければ即停止
- /work/1/SFC/tanab/izanagi/.codex/worktrees/t2830-unit-a2/output/insights/2026-09-20/t2797-b5-contrast/pilot/submit_pilot.py.txt — 試走で launcher API を呼んだ実例 (読むだけ、変更しない)。読めなければ即停止

## 作業 (プラン v2 の A2)

**編集してよい file はこの 2 つだけ** (どちらも tracked だが編集対象):
`tools/pegasus/b5_contrast_launch.py`、`orchestrator/tests/test_b5_contrast_launch.py`。

現行の挙動 (変更前に報告へ明記すること): `main` は `--repo-root` 1 本を `validate_submit_tree` で検査し、`launch(jobs, tree, ...)` が
4 job すべてを同じ `SubmitTree` から組んで、同じ `cwd=tree.repo` で qsub する。4 job が 1 つの checkout (同じ CCBench・同じ build cache) を共有する。

1. `launch(jobs, trees_by_arm, *, submit, runner=None)`: `trees_by_arm` は arm (`PILOT_ARMS` の各値) → 検証済み `SubmitTree`。
   各 job で `tree = trees_by_arm[job.arm]` を取り、**`build_job_environment(job, tree)` と `runner(argv, cwd=tree.repo)` の両方に同じ tree を使う**
   (command ごとに tree を保持する)。`validate_pilot_cap`・全 job の env / argv 組立て・freshness 検査を最初の mkdir / runner より前に終える既存の順序は維持。
2. `SubmitTree` / `validate_submit_tree` / `pilot_jobs` / `build_job_environment` / `qsub_argv` / `_qsub_argv` / `_validate_job` / `validate_pilot_cap` は**変更しない**。
3. `main`: `--repo-root` を `--repo-root-random` / `--repo-root-sweep-matched` / `--repo-root-llm` / `--repo-root-stock` の 4 必須引数へ置き換える。
   共通の `--expected-head` で、各 path を `PILOT_ARMS` 順に既存 `validate_submit_tree` → `replace(..., thirdparty_source_root=...)` し、
   mapping を `launch` に渡す。単一 `--repo-root` の fallback や互換層を作らない。
4. **足さない:** path 重複の拒否、common repo 一致の比較、`launch` 内での git 検証、その他の新しい拒否条件。
5. module docstring を「4 job をそれぞれ専用の clean checkout から投入する」旨に合わせる (試走の暫定 walltime の記述は残す)。
6. test:
   - `_pilot` fixture と `_expected_environment` を arm ごとの tree (`tmp_path / f"submit-tree-{arm}"` のような 4 つの異なる path) に対応させる。
   - `test_four_qsub_argv_and_explicit_environment_are_exact`: 各 job を自分の arm の tree で組んだ env・argv と完全一致比較する。
   - submit の test (`test_submit_only_mkdir_then_argv_runner` など): fake runner が `(argv, cwd)` を記録し、**rc=0 のケースで**全 4 件の cwd が
     各 arm の tree であること、argv の `IZANAGI_S4_REPO_ROOT` がその cwd と一致することを検査する。rc 非零で後続を呼ばない既存検査は維持する。
   - `test_main_dry_run_validates_tree_and_prints_four_jobs`: 4 つの CLI 引数を渡し、validator の spy が `PILOT_ARMS` 順に 4 回・共通 HEAD で
     呼ばれること、出力 4 件の `IZANAGI_S4_REPO_ROOT` が各 arm の tree であることを検査する。
   - `launch` を呼ぶ他の既存 test (dry-run、freshness、出力先の検査など) を新しい引数に追従させる。検査内容は弱めない。
   - `validate_submit_tree` の既存 test (単一 tree fixture) はそのまま。
   - tree の対応づけ (検査対象の機構) である `launch` / `build_job_environment` / `_qsub_argv` を test で差し替えない。外側の `validate_submit_tree`
     を spy に差し替える既存の形は可。

## 制約 (すべて守る)

- **`git commit` を一度も実行しない。** 残差の commit は起動器が行う。
- **docs を編集しない** (`docs/` 配下、`docs/handoff/` への file 作成、`tools/pegasus/README.md` を含む — README は親が更新する)。所有 2 file 以外の file を作成・編集しない。
- **テストを走らせない** (`tools/run_tests.py`、`python3 -m pytest`、`pytest.main` の埋め込み、test file の自走 harness のいずれも使わない)。
  親が計算ノードで焦点走を行う。報告は「実装済み・未実走」と書く。静的検査 (`python3 -m py_compile <file>`) は行ってよい。
- test の新設・改名をしたら、それに関わる制約 meta-test (例: test file 一覧・plain runner の網羅を検査する test) を**自分で洗い出して**静的に確認する。
- テストを甘くして緑にしない (期待値の緩和、`in` 検査への置換、既存 assert の削除をしない)。期待値に揮発値を焼き込まない。
- 指示外の受理集合を変えない (既存の拒否条件を足さない・外さない)。
- 予算が尽きそうなら、途中までの内容を下記の報告形式どおりに書いて終える。

## 報告形式

1. 変更前の挙動 (上記の確認)
2. 変更した file と箇所 (関数名・行)
3. 静的検査の結果 (実行したコマンドと rc)
4. 洗い出した meta-test と影響
5. 所有外の caller・共有 fixture・consumer (`tools/pegasus/README.md` の実行例、`test_hooks.py` の登録簿 test、試走の `submit_pilot.py.txt` など) への波及の静的列挙
6. 未実走であることの明記と、親が走らせるべき nodeid の候補
最後に `## 総括` を置く。
