# Unit 2 実装報告

## 1. 変更した file と要点

- [s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_holdout_admission.py)
  - `git rev-parse --git-common-dir` 由来の全 worktree 共有台帳 root を実装。
  - 台帳、claim、消費 marker、lock の親 directory を明示的に provisioning。
  - 指定された 5 field の一回性 key を採用し、`protocol_sha256` は証跡だけに保存。
  - cell claim と attempt ticket を `O_EXCL`、`fsync`、共有 lock で原子的かつ durable に消費。
  - HEAD blob と working tree bytes が一致する canonical protocol／freeze だけを発行 authority とした。
  - 同一 run identity と manifest を証明する resume だけを再発行可能にした。
  - `freeze_holdout_key`、`freeze_candidate_id`、`trial_workload_name` を分離。新 module と ledger に `holdout_id` は残していない。
  - 8 planned session と 2 retry slot、合計 10 ticket/cell を凍結済み schedule から発行。
  - records、threads、workload は cell 改変検査用の証跡に限定。

- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py)
  - perf、probe、measure より前に admission claim を取得。
  - public production entrypoint で `measure_fn`、`probe_fn`、`perf_preflight_fn` 注入を拒否。
  - `_Runner` に全 cell の exact admission mapping を必須化。
  - 外部 4 引数 `measure_fn` を維持したまま、callback 直前に ticket を消費する wrapper を追加。
  - 既定 closure では Unit 1 の observation token を `measure_point` へ転送。
  - ledger 発行済みかつ journal 不在の resume を初期 admission gate で拒否。
  - CLI `--protocol` を canonical floor protocol path に固定。
  - 既存 floor artifact の `holdout_id` は維持し、admission 境界だけで明示名へ変換。

- [test_s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_s8b_holdout_admission.py)
  - 2 worktree 並行競合、key 構造、attempt 数、seed 変更、resume、authority drift、ticket 一回性、M4／M5、座標証跡を追加。

- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_s8b_floor_campaign.py)
  - production seam 拒否、admission 順序、resume 順序、default token 転送、Runner mapping 検査を追加。
  - 既存期待値は反転、緩和、skip、削除していない。合成 fixture の注入だけを private core helper へ移した。

docs は編集していない。commit も作成していない。

## 2. 現行の受理・拒否挙動 → 変更後の受理・拒否挙動

変更前:

- floor campaign には共有 cell 台帳と attempt ticket がなく、Unit 1 の token を既定 `measure_point` へ渡していなかった。
- pilot の注入 seam から、admission より先に perf や測定処理を実行できた。
- 同じ freeze cell を別 worktree や seed 変更後に再測定する一回性拒否がなかった。
- CLI は任意の protocol path を受理した。
- ledger 発行済みで journal がない resume を識別できなかった。

変更後:

- canonical HEAD／working tree bytes が一致する場合だけ admission を検討する。
- 同じ 5-field key の fresh run は、worktree をまたいでも最初の `O_EXCL` 成功だけを受理する。
- `master_seed` など protocol hash だけを変えても同じ key は再受理しない。
- resume は同一 campaign run、run 座標、manifest の証明がある場合だけ受理する。
- 実測 callback 直前に対応 attempt ticket を消費し、二回目は拒否する。
- 座標差分は cell 改変として拒否するが、holdout 判定条件や一回性 key には追加していない。
- downstream verifier、ratified closure、report の受理集合は変更していない。
- 独立 clone 間の一回性、未 commit ledger の削除保護も実装していない。

## 3. 実走したテスト（nodeid・範囲・結果）/ 実走できなかったもの

pytest は判定不能・未実走であり、緑は主張しない。

`tools/run_tests.py` で次を試行したが、すべて collection 前に `qstat -Q preflight rc=1`、runner `rc=16` で停止した。

- `orchestrator/tests/test_s8b_holdout_admission.py`
- `orchestrator/tests/test_s8b_floor_campaign.py`
- `orchestrator/tests/test_holdout_observation.py`
- `orchestrator/tests/test_ccbench_spawn_sites.py`
- `orchestrator/tests/test_plain_runner_coverage.py`
- `orchestrator/tests/test_trial_registry.py`
- M4、M5、admission 順序、resume 順序、token 転送、Runner mapping の個別 nodeid
- 上記二 file の `--collect-only`

補助診断として、新設 admission test の全関数を直接呼び出し、全 10 ケースが完了した。ただし pytest fixture／runner を経ていないため、受入テスト結果には数えていない。

非 pytest 検査結果:

- `git diff --check`: 成功
- 4 所有 file の AST parse、NFC、U+0300〜U+036F 不在検査: 成功
- `python3 tools/check_codex_agents.py`: 成功
- `python3 tools/check_docs.py`: 違反なし
- 新 admission module の曖昧な `holdout_id` 不在検査: 成功

## 4. 事前登録変異の前後層確認（M4/M5）

M4:

- 同一 commit の二つの linked worktree、同一 canonical protocol／freeze、同一 cell key を並行入力している。
- 両入力とも authority、freeze projection、schedule、key 導出までは通過する。
- 現実装では共有 lock 内の `O_EXCL` だけが二番目を拒否し、結果は受理 1、拒否 1。
- `O_EXCL` を外す変異では二番目を拒否する先行層がなく、二重受理になる構造を確認した。

M5:

- 同じ発行済み admission、cell 座標、attempt ID を二回入力する。
- 一回目の callback は `BaseException` で停止させ、callback 後の処理を一切通さない。
- 現実装では callback 前に marker が durable 消費され、二回目は callback 前に拒否される。
- 消費を callback 後へ移す変異では一回目の marker が残らず、二回目も callback まで到達する。先行する admission／座標検査は同じ入力を拒否しない。

正式な mutation runner 実走は、前記 dispatch 障害により未実走。

## 5. 所有外への波及可能性（静的列挙）

- `run_campaign` に副作用可能 seam を渡す外部 caller は、pilot を含めて拒否される。テスト専用経路は private core が必要。
- Unit 1 の `measure_point`／`run_once` caller である `calibrator/sweep.py`、`campaign/pipeline.py`、`pegasus_floor_scoping.py`、`between_run_floor.py`、`backoff_overthrottle.py` は静的波及候補。ただし本 Unit では変更していない。
- 共有 fixture／consumer test の候補は `test_holdout_observation.py`、`test_ccbench_spawn_sites.py`、`test_calibrator.py`、`test_calibrator_certify.py`、`test_campaign.py`、`test_between_run_floor.py`、`test_trial_registry.py`、`test_plain_runner_coverage.py`。
- floor artifact consumer の `s8b_floor_stats.py`、`s8b_ratified_freeze.py`、`s8b_verdict.py` は台帳をまだ検査しない。これは本 wave の非主張範囲。
- Git common directory を共有する全 linked worktree と process が同じ物理台帳へ競合する。独立 clone には波及しない。

## 6. 未完・申し送り

- Pegasus queue preflight が観測不能で、pytest nodeid は一件も実走できていない。queue 復旧後に上記六 file と個別 M4／M5 nodeid の再実走が必要。
- floor test の直接呼び出しは pytest autouse fixture が適用されず、toolchain acquisition receipt 不在で停止したため結果として扱っていない。
- `git submodule update --init` は共有 Git config の read-only 制約で失敗したが、`git submodule status --recursive` と ccbench HEAD の一致は確認済み。
- provenance 検査は commit 未作成のため実施対象外。

## 総括

Unit 2 の admission、一回性 cell 台帳、attempt ticket、floor campaign 結線を所有範囲内へ実装した。  
M4 と M5 は、前後層が同じ入力を先に拒否しない構造までテストコードで固定した。  
docs、Unit 1 所有 file、`trial_registry.py` は変更せず、commit も作成していない。  
静的検査と補助診断は成功したが、pytest は Pegasus dispatch 障害により判定不能・未実走である。