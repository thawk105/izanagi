実装単位 B の変更を完了しました。commit・stage・docs・submodule の変更はありません。全 25 ファイルが指定所有内です。

### 実装内容

- pin 閉包 A=23 を `511c953` / full SHA `511c9538e4e8efa54b45cda62e72389ed3b706ec` へ更新。
- B=19 の historical preimage、fixture、golden、`PREVIOUS_PIN` / `KICKOFF_PIN*` は据置。
- R1 の 4 artifact を機械再 pin。patch bytes と `patch_sha256` は不変。
- current campaign-id を再導出し、T343/T530 などの historical 集合を保持。
- protocol canonical golden SHA を再導出。
- [test_silo_ladder_rung1_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-s4-unit-b/orchestrator/tests/test_silo_ladder_rung1_evidence.py) から凍結 v1 trace の再検証だけを退役。記録済み verifier、trace 要約、build、compile commands、attestation、seal、manifest の検査は維持。
- 凍結 evidence の旧 pin・旧 ledger SHA は historical golden として固定し、現行 pin・ledger とは異なることを検査。
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-s4-unit-b/orchestrator/tests/test_campaign.py) と [test_silo_ladder_rung1_driver.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-s4-unit-b/orchestrator/tests/test_silo_ladder_rung1_driver.py) の parser 到達 trace を v2 化。
- [silo_ladder_rung1.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t816-s4-unit-b/orchestrator/campaign/silo_ladder_rung1.py) の acceptance・exact schema、およびテスト側 fixture/mirror に `framing_violations` を追加。

### 検査結果の分類

(i) 自分の所有内

- pytest の実緑・実赤: なし（環境停止により本体 0 件）。
- 静的検査は緑:
  - `git diff --check`
  - 変更 Python 21 ファイルの AST parse
  - artifact の pin field 以外が HEAD と同一
  - `FROZEN_MANIFEST` と実 byte SHA の一致
  - patch SHA と ledger の一致
  - current campaign-id / protocol golden の独立再導出
  - `python3 tools/check_codex_agents.py`
  - `python3 tools/check_docs.py`
- R2 の 3 calibration、`output/campaigns/**`、凍結 raw trace 4 本は差分なし。

テスト投入範囲:

- 1回目: `test_frozen_artifacts.py`、`test_silo_ladder_rung1_evidence.py`、`test_t152_write_intent_coverage.py` の全 nodeid。
- 2回目: 変更したテスト 11 ファイルの全 nodeidを `--collect-only`。
- いずれも `run_tests.py` が予約台帳を更新できず dispatch へ移行し、`qstat -Q preflight rc=1` でテスト本体前に停止。実装済み・未実走です。pytest 直起動による迂回はしていません。

(ii) 単位 A 未統合による期待赤

- v2 trace literal を現行 v1 parser が読む node:
  - `test_campaign.py::test_pipeline_write_intent_violation_aborts_without_commit`
  - `test_campaign.py::test_pipeline_tail_loss_witness_reaches_verifier`
  - rung1 driver の synthetic raw bundle 再検証系
- verifier 出力に `framing_violations` がまだ無いため、rung1 exact-schema/acceptance 系も単位 A 統合前は期待赤。

(iii) gitlink 未前進による期待赤

- `test_s8b_approved.py` の実 gitlink 照合。
- `test_s8b_protocol_builder.py` の builder 系。
- 実 submodule HEAD と再 pin 済み freeze を照合する S1 freeze 系。
- 現在の gitlink は確認どおり旧 `d706650c...`。

(iv) 所有外の要修正

- 単位 A: `orchestrator/verifier/**`、`test_verifier.py`、verifier fixtures の trace v2 実装。
- 親: `external/ccbench` gitlink の前進。
- 親 docs: R2/R4 の歴史記録、`patches/README.md` の trace v2 記述。
- 新たな未裁定の所有外波及は見つかっていません。

## 総括

更新した pin（file:識別子）:

- `pin.py:CURRENT_PIN`
- `s8b_approved.py:CCBENCH_FULL_SHA`
- `axis_trigger_gating.py:PIN binding`
- `s5_permutation_coverage.py:PIN binding`
- `s6_sort_sweep.py:PIN binding`
- `backoff_sweep.py:CCBENCH_COMMIT`
- `p3_s4_loop_sort.py:PIN binding`
- `p3_s4_loop_trigger_gating.py:current trigger pin`
- `silo_ladder_rung1.py:PIN`
- `silo_ladder_rung1_contract.py:base_commit`
- `patches/ledger.json:base_commit`
- `test_p3_build_authority_cli.py:_EXPECTED_REPO_STOCK_PIN`
- `test_p3_s4_loop_sort.py:independent pin`
- `test_p3_s4_loop_trigger_gating.py:independent pin`
- `test_s6_sort_sweep.py:expected_pin`
- `test_s8a_trigger_sweep.py:_CHARACTERIZATION_PIN / expected_pin`
- `test_s8b_protocol_builder.py:canonical ccbench_pin`

再 pin artifact:

- `s8a_trigger_freq_t48.json`
- `known_axes_freeze.json`
- `measurement_freeze.json`
- `patches/ledger.json`
- freeze byte SHA: `7d6790d2…` / `4d4fa53f…`

退役した検査は凍結 d706650 期 v1 bundle の `verify_trace_dir` 再計算と recorded-result equality のみです。

実走結果は runner infrastructure 停止により 0 件。残件は単位 A の統合、親による gitlink 前進、その統合 tip 上での対象テスト再走です。