## 変更内容

- [paper_story_a1_paired.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/campaign/paper_story_a1_paired.py:41)
  - 共有 request-ID regex と `target_bound_qstat_state_result` を導入。
  - visibility を canonical `{QUE, RUN}`、rc=0、空 stderr、実機 execution queue の全体一意性・位置・`gen_S` に限定。
  - disappearance を A-2 と同じ fullmatch 意味論と対象 request ID に束縛し、producer と completion validator の双方へ適用。
  - 既存 terminal state/exit-status 述語と 12 語 reader は維持。

- [test_paper_story_a1_job_contract.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/test_paper_story_a1_job_contract.py:248)
  - M1〜M10 を殺す production-wiring テストを追加。
  - 正例 receipt は `validate_acquisition_receipt` / `validate_completion_receipt` を通す構成。
  - 既存 repository-root テストの qstat 入力を実機 RUN 全文へ変更。request ID を対応させたが assertion は変更していない。
  - 新規 test file は作成していないため、test file 登録・命名 meta-test の追加対象はない。

- 実機 bytes をそのまま追加:
  - [RUN fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/fixtures/paper_story_a1/qstat-f-980043.nqsv.txt)
  - [PRR fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/fixtures/paper_story_a1/qstat-f-980062.nqsv.txt)
  - [Queued fixture](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/fixtures/paper_story_a1/qstat-f-queued-978193.excerpt.txt)
  - [不存在 stdout](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/fixtures/paper_story_a1/qstat-f-absent-900001.stdout)
  - [不存在 stderr](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2349-author/orchestrator/tests/fixtures/paper_story_a1/qstat-f-absent-900001.stderr)

提示元との `cmp` および SHA-256 一致を全 5 file で確認した。

## テスト結果

実走できた pytest nodeid はありません。以下の 24 case は実装済み・未実走です。

- `test_real_nqsv_visibility_flows_through_acquisition_validator` 全3 parameter
- `test_visibility_rejects_each_noncanonical_observation` 全12 parameter
- `test_real_nqsv_disappearance_flows_from_producer_to_completion_validator`
- `test_terminal_observer_rejects_nonterminal_nqsv_observations` 全5 parameter
- `test_completion_validator_reparses_disappearance_stdout` 全2 parameter
- `test_submit_runs_real_qsub_call_from_repository_root`

`tools/run_tests.py` から最終状態で起動したが、`qstat -Q` preflight が rc=1となり、pytest child 起動前に rc=16 で停止した。直接確認した理由は `NQSconnect: [API EACCTAUTH] Unknown user-id`。走らせていないため緑とは報告しない。

静的確認は成功:

- 両変更 Python file の AST parse
- `git diff --check`
- 実機 fixture の byte/hash 一致
- RUN/PRR/Queued の正規化結果 `RUN/RUN/QUE`
- queue 一致数各1
- disappearance の対象 ID 束縛

## 既存テストの赤

既存テストを含め pytest child が起動しなかったため、観測した赤はありません。既存テストが緑だったという意味ではありません。

## 静的な波及可能性

- visibility producer の caller は V3 fan-out submit と direct submit。新規 receipt state は canonical `QUE/RUN` になる。
- group submission、acquisition、prior-visibility の reader は既存 12 語集合を維持しており、新 canonical 値を受理する。
- terminal producer の caller は V3 group completion と direct completion。
- completion validator を使う V3 projection、consumer、materializer は、別 ID・非 signature の disappearance receipt を新たに拒否する。
- job shell は receipt の state/queue を読むが、canonical 値と `gen_S` は現行契約内。
- `scheduler_nqsv.py`、A-2、dispatcher の挙動は変更していない。
- source closure は裁定 §4 に従い変更していない。共有 leaf は curated closure 外のまま。
- 既存 visible-terminal producer/consumer test は state/exit-status 述語を変えていないため、静的には維持される。
- 本変更は F852 の既知 blocker と disappearance 過剰受理を閉じるだけで、bench 到達は保証しない。

## 裁定 §7 対応

1. 実装済み。共有 regex を alias import し、全 request-ID 参照へ適用。
2. 実装済み。rc、stderr、canonical state、queue 全体一意性・位置・形式・名称を論理積化。
3. 実装済み。disappearance fullmatch、ID 束縛、prior visibility を producer/consumer 双方へ適用。
4. 実装済み。12 語集合、terminal 集合、terminal state/exit-status 述語は不変。
5. 実装済み。正負例は production observer を通し、保存 receipt は validator を通す。
6. 実装済み。RUN、PRR、Queued、不存在 stdout/stderr を実機 raw bytes からコピー。

## 総括

裁定 §7 の全6項目を許可範囲内で実装した。docs、verifier、anomaly/correctness gate、変更禁止 file には触れていない。`git add`、commit は行っていない。pytest は NQSV 認証による dispatch infrastructure failure のため未実走。