## 対応表 (F1〜F4)

| 所見 | 判定 | 根拠 |
|---|---|---|
| F1 | closed | `AttemptRegistryCoreError` を `B4ProtocolError` へ正規化。対象 node は通過。 |
| F2 | closed | 戸数 pin を裁定どおり 46 に更新。production probe で `closure_count=46`、`attempt_registry_core_visible=True`。pytest node は基盤障害で未実走。 |
| F3 | closed | driver は base、hash は sort proposal と一致する封印 publication を追加。対象 node は通過。 |
| F4 | closed | 束縛引数なし continuation の受理正例を base / sort / trigger に追加。3 case とも通過。 |

## 変更した file と行

- [p3_s4_loop.py:389-394](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/campaign/p3_s4_loop.py:389): canonical 化失敗時の例外適配。
- [test_p3_b4_proposal_binding.py:274-304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_proposal_binding.py:274): M05 の hash 一致・driver 不一致入力。
- [test_p3_b4_proposal_binding.py:307-331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_proposal_binding.py:307): 3 driver の continuation 受理正例。
- [test_p3_b4_wiring_probe.py:324-326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2101-proposal-binding/orchestrator/tests/test_p3_b4_wiring_probe.py:324): 静的 import 閉包の戸数を 45 から 46 へ更新。

## 走らせたテストと結果

自走 harness:

```text
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. PYTEST_ADDOPTS='-p no:cacheprovider' \
python3 -B orchestrator/tests/test_p3_b4_proposal_binding.py
```

結果: `23 passed in 11.17s`。

該当 node:

- `test_canonical_identity_distinguishes_int_float_and_excludes_receipt`
- `test_unknown_duplicate_invalid_hash_and_driver_mismatch_reject`
- `test_continuation_and_non_b4_reject_bootstrap_binding_arguments[base]`
- 同 `[sort]`
- 同 `[trigger]`

F2 node は `tools/run_tests.py` で実行を試みましたが、`qstat -Q preflight rc=1`、`rc=16`、`child_started=false` でした。

- 未実走 node: `test_p3_b4_wiring_probe.py::test_source_segment_helper_matches_stdlib_for_all_static_ifs`
- 代替の production closure probe: `closure_count=46`、`attempt_registry_core_visible=True`
- `git diff --check`: 成功

## 赤の内訳

pytest の赤は 0 件です。

F2 の指定 node はテスト失敗ではなく、dispatch infrastructure failure により pytest child が起動していません。

## 波及の静的列挙

- 共通 binding caller: base loader、sort loader、trigger loader。F1 は canonical 化不能入力の拒否例外型だけを変え、受理集合は変えません。
- 共有 fixture `p3_b4_proposal_binding_support.py` は `test_p3_b4_proposal_binding.py`、`test_p3_s4_loop.py`、`test_p3_b4_closed_critic.py` から利用されています。fixture 自体は未変更です。
- `_production_launch_context` は定義元の 15 呼出し、および launcher、base、sort、trigger、raw producer の consumer test から参照されています。今回の変更による signature 波及はありません。
- 関連 module を参照する consumer test の和集合は現在 26 fileです: `test_artifact_admission.py`, `test_campaign.py`, `test_campaign_import_invariant.py`, `test_codex_agents.py`, `test_floor_pair_driver.py`, `test_layer3_report.py`, `test_p3_b4_closed_critic.py`, `test_p3_b4_launcher.py`, `test_p3_b4_material_report.py`, `test_p3_b4_proposal_binding.py`, `test_p3_b4_raw_record_producer.py`, `test_p3_b4_wiring_probe.py`, `test_p3_build_authority_cli.py`, `test_p3_exploration_namespace.py`, `test_p3_s4_loop.py`, `test_p3_s4_loop_job_contract.py`, `test_p3_s4_loop_sort.py`, `test_p3_s4_loop_trigger_gating.py`, `test_pytest_collection_config.py`, `test_s1_direct_comparison.py`, `test_s6_sort_sweep.py`, `test_s8a_trigger_sweep.py`, `test_s8b_oracle_driver.py`, `test_sort_swo_oracle.py`, `test_t671_source_binding.py`, `test_trigger_gate_binding.py`。

## 変更しなかったもの

- docs、commit、production の continuation・非 B-4 挙動
- `_SOURCE_CLOSURE_PATHS` と凍結 closure 5 file
- `B4_PRERUN_NON_GUARANTEES`
- 台帳、受領証、署名、capability、状態機械、汎用 framework
- F2 の `45` → `46` 以外の既存期待値、assert、test、skip 設定

tracked worktree の変更は上記 3 fileだけです。commit は作成していません。

## 総括

F1〜F4 はすべて実装上 closed です。binding test 23 件は実走して全件通過しました。F2 の production closure は 46 件と確認済みですが、指定 pytest nodeだけは dispatch 基盤障害のため未実走です。