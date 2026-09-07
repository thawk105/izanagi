## 対応表

| 所見 | 状態 | 結果 |
|---|---|---|
| `launch_admission` carrier の revert | partial | 静的には完全に除去。実走未確認 |
| start の iff 検査配置 | partial | writer・terminal・acceptance に維持。loader 専用負例を撤去 |
| 起点失敗終端 | partial | 限定された第 3 terminal 形を実装。実走未確認 |
| complete と originless の不変性 | partial | 負例・bytes 不変検査を追加。実走未確認 |
| 架空の `campaign_runs` 試験除去 | partial | 除去を維持し、baseline 比較を保持 |
| 回帰検査 | partial | runner が rc=16、子プロセス未起動 |
| regressed | 0件 | 静的監査で新たな退行は未検出 |

## 実装内容

[trial_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-a/orchestrator/campaign/trial_registry.py:221) を次の形にしました。

- lifecycle start は base 15 key、または base + `origin_run_plan_sha256` の 2 択だけです。
- `_LIFECYCLE_START_ORIGIN_CARRIER_KEY` は存在しません。
- `record_trial_start_once` が start 行へ `launch_admission` を書く処理はありません。残るのは従来の `launch_admission_sha256` と、起点専用 digest だけです。
- loader による admission record 展開・束縛検査をすべて撤去しました。
- loader は start の key 集合、digest 形式、start の起点主張と terminal 形だけを検査します。
- `record_trial_terminal` に keyword-only の `failure_reason: str | None = None` を追加しました。

前巡の loader 専用負例は削除し、同じ 2 条件は writer の [start iff 試験](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-a/orchestrator/tests/test_trial_registry.py:3958) と [acceptance iff 試験](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-a/orchestrator/tests/test_trial_registry.py:2633) に残しています。

## 受理集合の制御された拡張

新たに受理されるのは、既存の token・attempt status・artifact 束縛をすべて満たした上で、次の全条件を満たす入力だけです。

- start token の `state.origin_binding` が存在する。
- `terminal_status` が `partial` または `indeterminate`。
- `origin_terminal_projection` が存在しない。
- `failure_reason` が空でない文字列。

対応する lifecycle wire は `base terminal keys + failure_reason` です。loader 側でも、start に `origin_run_plan_sha256` があり、上記失敗 status、projection 無し、非空 reason の場合だけこの形を受理します。

`complete` の projection 無しは writer と loader の双方で拒否します。originless の従来 base terminal bytes は変更せず、originless に `failure_reason` または projection を追加した行も引き続き拒否します。これらは [追加試験](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-a/orchestrator/tests/test_trial_registry.py:4319) で固定しています。

## caller への波及

repo 内の直接 call expression は計 13 件です。

所有外の本番 caller は [p3_autonomous_workload_trial.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-a/orchestrator/campaign/p3_autonomous_workload_trial.py:4518) の 4 件です。

| 行 | 経路 | 波及 |
|---|---|---|
| 4518 | `_record_indeterminate_terminal` | 起点かつ projection 無しなら非空 reason の引渡しが必要 |
| 4573 | `mark_experiment_indeterminate` | 同上 |
| 4978 | budget insufficient 終端 | 起点 token へ波及する場合は reason が必要 |
| 5193 | 通常 finish | 起点成功は projection を渡すため不変。originless も不変 |

所有内テストの直接 caller は 9 件、行 4218、4235、4240、4245、4364、4372、4437、4500、4677 です。所有外 `test_p3_autonomous_workload_trial.py` の 5 参照は spy、`*args/**kwargs` wrapper、元関数の退避・復元であり、固定 signature の test double はありません。

現在の所有外 caller はまだ新しい reason を渡していません。実運用経路の結線は同時進行中の caller 単位に残ります。

## scope と検査

[test_reflux_originless_compatibility.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-fix2-a/orchestrator/tests/test_reflux_originless_compatibility.py:1189) では架空の `campaign_runs` 試験除去を維持し、非揮発 leaf と closed key 集合の比較を残しています。

- `git diff --check`: 問題なし
- 変更 3 ファイルの AST parse: 成功
- carrier symbol と carrier 書込み経路の静的検索: 0 件
- 変更ファイルは指定された排他所有 3 ファイルだけ
- docs 編集・commit: なし
- 指定した 7 nodeid の `tools/run_tests.py`: rc=16
- 原因: `qstat -Q preflight rc=1`
- `child_started=false` のため、テストは 1 件も実走していません

## 総括

- `launch_admission` の lifecycle start carrier は静的に完全撤去しました。
- start は従来の 15/16 key 形へ戻しました。
- 起点失敗だけに `base + failure_reason` terminal 形を追加しました。
- complete の projection 関門と originless bytes は維持しています。
- 架空の `campaign_runs` 試験除去も維持しています。
- AST と差分検査は成功しました。
- テスト runner は rc=16 で子が起動せず、実装済み・未実走です。
- 残る赤は親による実走と、所有外 caller からの failure reason 結線です。