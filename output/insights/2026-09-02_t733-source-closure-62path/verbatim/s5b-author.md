## 総括

`HISTORICAL_RAW` 専用の exact-24 decoder を別型で実装しました。  
certified、通常 decoder、encode、resume、`classify_campaign()` は exact-62 のままです。  
記録 commit の全24 blob 照合、当時の path 順序・scope、現行適合 `unknown` を維持しています。  
許可された4 file だけに未 commit 差分を残しました。pytest は基盤障害により未実走です。

## 変更した file と要点

- [campaign_lock.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/campaign_lock.py:117)
  - 独立 literal の pre-T733 exact-24 ordered grammar を追加。
  - [専用 authority・decode 型](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/campaign_lock.py:200)を追加。
  - [歴史専用 text/bytes decoder](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/campaign_lock.py:567)を追加。
  - 通常 decoder と exact-62 定数は変更なし。

- [artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/artifact_admission.py:84)
  - exact-24 当時の scope 文言と専用 epoch 型を追加。
  - [purpose 確定後の decoder 選択](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/artifact_admission.py:987)を追加。
  - [記録 commit の24 blob 照合](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/artifact_admission.py:999)と、記録順による epoch 計算を実装。
  - [認証 tuple・WAL contract 検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/campaign/artifact_admission.py:1158)を歴史型でも維持。
  - `classify_campaign()` は明示的に certified 用通常 decoder を使用。

- [test_campaign_lock_codec.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/tests/test_campaign_lock_codec.py:149)
  - 専用返却型、通常 decoder 拒否、未知 grammar、順序違いを追加。

- [test_artifact_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t733-author/orchestrator/tests/test_artifact_admission.py:1750)
  - P3、P4、両目的の負例、commit blob 不一致を追加。

## 受理・拒否の変化

- certified 目的
  - 変更前後とも exact-62 のみ受理候補。
  - exact-24、8、12、14、25、27、未知集合、順序違いは拒否。
  - encode、resume、通常 decoder、`classify_campaign()` の受理集合は不変。

- historical 目的
  - 変更前: v1と現行 exact-62を受理し、exact-24を拒否。
  - 変更後: 上記に pre-T733 exact-24だけを追加。
  - subset、superset、同数別集合、順序違いは拒否。
  - exact-24 epoch は当時の24 path順序とscopeを使用し、現行適合は `unknown`。

## 足したテスト

- P3:
  - `test_p3_pre_t733_exact_24_is_readable_only_as_recorded_historical_epoch`
- P4:
  - `test_p4_same_pre_t733_exact_24_bytes_are_rejected_for_certified_use`
- 負例:
  - `test_unknown_pre_t733_grammar_is_rejected_for_both_read_purposes[...]`
  - `test_pre_t733_historical_decode_rejects_recorded_commit_blob_mismatch`
  - `test_pre_t733_exact_24_uses_dedicated_historical_decoder_type`
  - `test_pre_t733_exact_24_remains_rejected_by_normal_decoder`
  - `test_historical_decoder_rejects_unknown_blob_map_grammars[...]`
  - `test_historical_decoder_rejects_reordered_blob_map_wire_keys`
- 既存の exact-2、exact-12 拒否テストは変更していません。

## 実走したテスト

pytest実走は0件です。以下はすべて `tools/run_tests.py` が pytest child 起動前にrc=16となったため、実装済み・未実走です。

- `orchestrator/tests/test_campaign_lock_codec.py`
- 新規 artifact admission 4 nodeid群
- `test_throughput_ci_is_wal_t95_and_abort_has_no_ci_in_canonical_data`
- 2 test fileのcollection

原因はPegasus dispatchの `qstat -Q` が `EACCTAUTH Unknown user-id` で失敗し、local実行もuser-slice headroom不足で選択されなかったためです。

非pytest検査では、4 fileの`py_compile`と`git diff --check`が成功しています。

## 赤の内訳

- 回帰: pytest未起動のため未評価。
- contract-loader-drift由来: 未観測。全走時には production 2 fileの未 commit 差分による既知赤が想定されます。
- その他: dispatch基盤エラーrc=16。テスト失敗ではありません。

## 波及可能性 (所有外)

- 中央 historical APIへ追随: `plot_backoff.py`、`plot_s1_9pair.py`、`online_digest.py`、`replay.py`、`layer3_report.py`。
- B10の観測済み経路: `test_plot_b10_extended_backoff.py`。
- view値のconsumer: `critic/digest.py`、`p2_2_report.py`。歴史epochは既存epochのsubclassでfield互換です。
- 共有fixture: `campaign_lock_test_support.py`は引き続き現行exact-62のみ生成します。
- 波及候補consumer test: `test_s1_9pair_figure_provenance.py`、`test_critic.py`、`test_layer3_report.py`、`test_campaign_lock_wal_consumers.py`。
- `qualification/artifacts.py`、`s1_report.py`、A2 certificationなど直接通常decoderを使う経路は、意図どおりexact-24を拒否し続けます。

## 編集しなかったが必要かもしれない file

現時点で追加編集が必要と判断したfileはありません。所有外consumer testは、実行基盤復旧後の検証対象です。