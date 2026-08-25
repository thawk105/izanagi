## 現行挙動と変更範囲

変更前は、6 report の `measurement_head` 一致のみを要求し、Layer 3 の計測対象は横断照合していませんでした。no-build／campaignless failure は既存理由コード付きの非 certifying 受領証として受理されます。

変更は指定された 2 ファイルだけです。

- [trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/campaign/trial_registry.py:5402)
  - 各 materialized campaign の Layer 3 report を strict JSON として再読。
  - JSON 重複キー、型不正、空の `meta.ccbench_commit`、単一でない `env_tags` を hard failure。
  - `ccbench_commit` と単一 `env_tag` の横断一致を要求。
  - 完全 build 束では readable Layer 3 report が exactly 6 件でなければ hard failure。
  - 読み取った Layer 3 bytes が受入中に変化していないことも再確認。
- [test_trial_registry.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-evidence-gaps/orchestrator/tests/test_trial_registry.py:1660)
  - 同一対象の 6 report 正例を強化。
  - ccbench 不一致、env tag 不一致、1 件欠落の指定負例を追加。
  - duplicate JSON key、field 型・母数、top-level 関数名重複の制約テストを追加。
  - 3 指定負例は exact gate 文言と receipt 不在を固定。

受領証の `receipt_value` AST は変更前の `HEAD` と完全一致しました。schema、exact key、canonical preimage は不変であり、正しい既存入力の SHA-256 算出内容も変わりません。reason code の追加・削除もありません。

## 検証状況

- `git diff --check`: 成功
- Python AST parse: 両ファイル成功
- top-level 関数名重複: 両 module とも 0 件
- 禁止された 3 production ファイル: 無差分
- `loop_state.iteration` 実装: なし
- commit／git add／acceptance 全走: 未実施

焦点走は `tools/run_tests.py` へ次を投入しましたが、pytest child は一度も起動していません。

- 登録 build 正例
- 新規 ccbench／env tag／母数／strict JSON／型／AST テスト
- 既存 receipt exact-contract 正例
- 既存 campaignless reason-code テスト

実走範囲は 0 nodeid です。Pegasus の共有 user slice が 14 GiB 天井付近で local admission 不可となり、compute dispatch も `qstat -Q` の `API EACCTAUTH Unknown user-id` により `rc=16`, `child_started=false` で停止しました。したがって状態は「実装済み・未実走」で、closed とは申告しません。テスト由来の赤は未観測ですが、焦点テスト結果は未確定です。

静的な波及候補は、同ファイルの CLI caller、originless compatibility consumer、`_build_registered_campaign`／`_prepare_registered_build_report` 共有 fixture、C02/C09/C10 machine-contract検査、formal facade routing 検査、standalone receipt verifier です。

## 総括

- Layer 3 の CCBench commit・単一 env tag・完全 build 母数 6 の hard gate を実装。
- 指定 3 負例、正例、strict JSON／型／D864 制約テストを追加。
- receipt preimage、reason code、禁止ファイルは不変。編集は指定 2 ファイルのみ。
- 焦点走は Pegasus 実行基盤の `rc=16` で child 未起動のため、実装済み・未実走。