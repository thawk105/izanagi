## 総括

exact 24 path を既存順序のまま exact 62 path へ拡張し、文言・golden・固定 known-answer を同期しました。  
コード 3 file、テスト 3 file のみ変更し、docs・凍結成果物・domain・D1163 挙動は未変更です。  
sandbox 制約により差分は `t733-author` worktree にあります。指定 parent worktree は書込拒否され、現在も clean です。  
commit・add・push は実施していません。

## 変更した file と要点

- [campaign_lock.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/campaign_lock.py:47)
  - 既存 24 path を維持し、確定 suffix 38 path を指定順で追加。exact 62 に更新。

- [contract_loader_binding.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/contract_loader_binding.py:2)
  - count 文言のみ 62 に更新。検査ロジックは未変更。

- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/artifact_admission.py:72)
  - scope と excluded scope を裁定 §3 の文言へ更新。
  - docstring 3 箇所を exact 62 に更新。
  - epoch domain と目的別 gate は未変更。

- [test_t671_source_binding.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/tests/test_t671_source_binding.py:37)
  - pre-T733 exact-24 literal と T733 suffix-38 literal を分離。
  - receipt paths を pre-T733 tuple の `[19:24]` に固定。
  - exact 24/38/62 count と exact tuple 順序を検査。
  - 既存 nodeid は duration ledger との整合のため維持。

- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/tests/test_artifact_admission.py:46)
  - 独立 literal を 62 path へ拡張し、count・scope golden を更新。
  - synthetic E1 と ordered path-list SHA-256 を固定値で pin。

- [test_s1_9pair_figure_provenance.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/tests/test_s1_9pair_figure_provenance.py:74)
  - `CURRENT_E0_EPOCH` のみ更新。
  - exact-27 の `FROZEN_E0_EPOCH` は未変更。

## 実走したテスト

pytest の実走はありません。以下の両走行とも `tools/run_tests.py` が dispatch 前に `qstat -Q preflight rc=1`、最終 `rc=16` となり、`child_started=false` でした。

- 4 file 範囲:
  - `test_t671_source_binding.py`
  - `test_campaign_lock_codec.py`
  - `test_artifact_admission.py`
  - `test_s1_9pair_figure_provenance.py`

- 縮小 nodeid:
  - `test_enforcement_source_closure_is_the_independent_exact_twenty_four_paths`
  - `test_certified_acceptance_admits_exact_e1_fixture`
  - `test_real_e0_is_rejected_only_by_certified_epoch_gate`
  - `test_p1_independent_real_wal_projection_matches_frozen_report`

したがって実装済み・未実走です。静的 tuple/scope/AST 監査と `git diff --check` は PASS。`check_codex_agents.py`、`check_docs.py` も PASS しました。

## 赤の内訳

- 回帰: 観測なし。pytest child が起動していないため判定不能。
- contract-loader-drift 由来: 観測なし。未 commit の production 3 file により、実走時には既知の drift 赤が予想されますが回帰ではありません。
- その他: runner infrastructure failure 2 回。いずれも `rc=16`、`dispatch-error`、`child_started=false`。

## 固定 known-answer の計算方法

ordered-list SHA-256 は、62 path を tuple 順に、各 `UTF-8(path) + 0x00` として連結し SHA-256 を計算しました。

`b274387d0be033a98e86d54e5225667221bde79776832e73fb3d07cebfc6067a`

E1 は次を連結して SHA-256 を計算し、`E1:` を付加しました。

1. ASCII bytes `campaign-verifier-epoch/v1`
2. tuple 順の各 pathについて:
   - `UTF-8(path)`
   - `0x00`
   - synthetic blob `epoch closure fixture {1始まりindex}\n` の SHA-256 raw 32 bytes

固定値:

`E1:78920efc47f4eb280b956a8fb92abed16b888495db544b62b1a15bf1f61004e9`

HEAD の既存 24 tupleと確定 suffix38 から別経路でも再計算し、一致を確認しました。

## 波及可能性 (所有外)

- caller / producer:
  - `ident.py`
  - `layer3_report.py`、`s1_report.py`、`backoff_sweep_report.py`、`p2_2_report.py`
  - `s6_sort_sweep.py`、`s8a_trigger_sweep.py`
  - `s8b_oracle_artifacts.py`、`s8b_oracle_judge.py`、`s8b_oracle_report.py`
  - `autonomous_trial_completeness.py`、`critic/digest.py`
  - `tools/plotting/plot_s1_9pair.py`、`plot_backoff.py`、`plot_b10_extended_backoff.py`

- 共有 fixture:
  - `orchestrator/tests/campaign_lock_test_support.py`
  - `orchestrator/tests/commit_receipt_support.py`

- consumer test:
  - `test_campaign_lock_codec.py`
  - `test_bench_first_real_wal.py`
  - `test_env_contract_activation.py`
  - `test_layer3_report.py`
  - `test_paper_story_a2_certification.py`
  - `test_s6_sort_sweep.py`
  - `test_s8a_trigger_sweep.py`
  - `test_s8b_oracle_report.py`
  - `test_t762_ident_wrapper.py`
  - 各 report、oracle、plot、critic の対応 test 群

受理・拒否挙動は、v2 の受理 mapが exact-24 から exact-62 へ非互換置換されます。既存 exact-2 / exact-12 拒否、v1 E0、HISTORICAL_RAW、D1163 の current closure 可用性のみを見る挙動は維持しています。pre-T733 exact-24 専用拒否テストは追加していません。

## 編集しなかったが必要かもしれない file

なし。`test_campaign_lock_codec.py` は production tuple の動的参照により 62 path へ追随するため編集不要です。