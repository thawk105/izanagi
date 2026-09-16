## 変更した file と差分の要約

変更は次の 2 file のみです。commit は作成していません。

- `orchestrator/tests/test_s8b_oracle_driver.py`：proto/finish 分割、session proto 共有、permanent test、既存 cache test 更新。
- `tools/t080_proto_equivalence_probe.py`：新規の一回限り probe。親による退避・非 commit 対象。

`git diff --check` は成功しました。production・docs・既存 e2e 11 node の assert は変更していません。

## 分割点と proto 共有の実装

- `_build_t080_e2e_proto`（1420 行〜）：境界検査、repo 初期化、既存の全件コピー、historical basis 復元、submodule 準備。
- `_finish_t080_stub_free_e2e_repo`（1498 行〜）：distinct descriptor 変更、basis commit、発行。runtime source は従来どおり key ごとに実 repo から複製。
- 互換 wrapper（1407 行〜）：既存 signature・返却値を維持。単独走はこの入口を使用。
- `_T080SharedBases`（895 行〜）：key → proto の lock 順序、正常 return 後の pending → marker rename、`.git` 込み `copytree(..., symlinks=True)` を実装。
- marker 不在では残骸を再構築し、公開済み JSON 破損・root 欠損は例外を伝播。コピー中の shared lock、process 内 proto memo、proto 専用 cleanup は追加していません。

変更前は key ごとに実 repo の可視集合を再取得し、境界違反や構築失敗を拒否していました。変更後は共有経路の最初の source snapshot を全 key が使用し、同一 snapshot・key・Git 設定・commit metadata を条件とする同値性を保ちながら、境界違反・未完成公開・公開済み proto の欠損を拒否します。

## permanent test

追加した検査は以下です。

- 小型 source の default/distinct 比較：独立に記述した旧順序との path・種類・bytes・mode・link target・tree/commit OID 比較。
- tracked/untracked/ignored、実行 bit、深い path、destination で ignored となる `config.h`、submodule 内 symlink。
- submodule pointer の相対性、proto 削除後の Git 動作、双方向の変更独立性。
- Pipe による正常 return 前の停止と marker 不在確認、失敗後・pending-only からの再構築。
- `proto.lock` の path を識別した EX 待ち観測、異なる 2 key で proto 1 回・finish 2 回。
- proto 入口の書込み前拒否、公開済み JSON/root 破損、finish 失敗時の key marker 非公開。

新規 test は小型 source を使用します。AST 検査の既存 6 function / 11 node は維持しました。

## probe

既定 base `08d56628e` の旧 module を別名で exec し、現行 proto 派生と比較します。両 module の `_sanitized_git_env` で commit metadata を固定し、通常実走では default/distinct の receipt raw bytes・document・各 OID・working tree を照合します。

既存 import guard に対応するため、正規の pytest collection session 内で読み込みます。hold 解除や test 本体の実行は行いません。

`--selftest` は成功しました。

- 小型 source の旧経路・新経路が両 key で一致。
- 1 byte 変更時の比較器の返却値は `1`。
- 結果：`/tmp/t080-proto-selftest.json`

selftest は発行なしです。実 corpus の receipt 同値性の証明には数えていません。

## 実走結果 (nodeid と結果、未実走の列挙)

指定の `PYTHONPATH=. python3 -c "...pytest.main(...)"` 形式で実行しました。以下はすべて `orchestrator/tests/test_s8b_oracle_driver.py::` を接頭辞とする nodeid です。

**24 passed / 132 deselected、134.18 秒：**

```text
test_t080_shared_base_returns_independent_repos_and_documents
test_t080_shared_base_without_completion_marker_is_rebuilt
test_t080_shared_base_waits_for_builder_lock
test_t080_shared_base_missing_session_uses_process_memo
test_t080_shared_base_keeps_all_four_key_fields_separate
test_t080_shared_base_only_last_participant_removes_tree
test_t080_shared_base_cleanup_tolerates_real_disappearance[False]
test_t080_shared_base_cleanup_tolerates_real_disappearance[True]
test_t080_shared_base_cleanup_propagates_other_errors[13]
test_t080_shared_base_cleanup_propagates_other_errors[5]
test_t080_shared_base_cleanup_propagates_other_errors[39]
test_t080_shared_base_cleanup_exhausted_disappearance_is_error
test_t080_shared_base_finish_failure_has_no_marker
test_t080_proto_derivation_matches_direct_small_source[False]
test_t080_proto_derivation_matches_direct_small_source[True]
test_t080_proto_boundary_rejects_before_write
test_t080_proto_incomplete_build_is_rebuilt[False]
test_t080_proto_incomplete_build_is_rebuilt[True]
test_t080_proto_waits_for_identified_lock_across_keys
test_t080_proto_published_damage_propagates[json]
test_t080_proto_published_damage_propagates[root]
test_t080_stub_free_e2e_exact_consumers_and_nodeids_b5
test_t080_output_copy_visibility_matches_production_enumeration
test_t080_stub_free_e2e_temp_roots_fail_closed_at_real_output_boundary
```

最後に独立性・再構築回数の assert を追加し、先頭の 2 node を再実走して **2 passed / 154 deselected** を確認しました。

初回は小型 reference が receipt 除外後の空 directory を再現せず、同値性 2 node が失敗しました。reference を修正して上記の成功を確認済みです。

**未実走：**

- `test_t080_shared_base_builds_real_builder_once_across_processes`。
- 下記の既存 e2e 6 function / 11 node。
- 実 corpus の probe、変異 matrix、受入・焦点走 K=3。
- M1/M2/M8 の追加変異確認はコマンドが PreToolUse guard に拒否され、未実走です。

## 既存 test の期待値更新

- 小型 cache fixture は proto と finish の両方を小型化。
- 5 key は finish 5 回・proto 1 回。
- marker 欠損時は finish 2 回・proto 1 回。
- 最初の close 後も proto payload が存在することを確認。
- 独立性検査は proto を含む 4 個の inode 分離を確認。
- cleanup・lock・process memo の既存期待値は維持。

**仕様との相違が 1 点あります。** 共有経路が finish を直接呼び、wrapper が同じ signature で直組みする仕様では、共有経路の wrapper 呼出し数 `(1, 0)` は維持できません。そのため実 builder の既存 wraps test は、finish と proto の呼出し数をそれぞれ `(1, 0)` とする検査へ変更しました。この実 repo test 自体は未実走です。

## 波及可能性の静的列挙

Python source の検索では、指定 symbol の参照は対象 test file と新規 probe に閉じています。

| symbol | consumer |
|---|---|
| `_t080_stub_free_e2e_repo` | callable fixture `t080_shared_cache_probe`、既存境界 test、下記 e2e 6 function。AST test が direct consumer 集合を検査 |
| `_build_t080_stub_free_e2e_repo` | process memo miss、既存境界 test、probe の旧 module 呼出し |
| `_T080SharedBases` | session join、callable fixture、既存 cleanup tests、新規同値性・未完成・lock・破損・finish 失敗 tests |
| `_copy_git_visible_output` | proto builder、既存 visibility test の正例・欠損負例 |

共有 fixture を通じて影響しうる既存 e2e は次のとおりです。

- `test_t080_stub_free_draft_finalize_commit_and_public_gate_e2e_b5`：1 node
- `test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5`：4 node
- `test_t080_stub_free_e2e_remaining_section_1_4_defects_are_exact_b5`：1 node
- `test_t080_full_valid_history_defects_have_one_baseline_reason_f28`：3 node
- `test_t080_full_valid_post_r_delete_blocks_draft_as_single_precondition_f28`：1 node
- `test_never_issued_generator_tamper_reaches_public_driver_gate_g7`：1 node

所有外の conftest・receipt memo・serialization/collection 検査は変更していません。共有初期化・collection・配置への間接影響は、親の回帰実走で確認が必要です。

## 未完・懸念

- 実装と軽量検証は済んでいますが、実 corpus の receipt 同値性・実 repo shared-base test・e2e 11 node は未実走です。
- wrapper 呼出し数の仕様不整合は上記のとおりです。
- 変異 matrix の killer は実装しましたが、KILLED の実測結果は未取得です。
- 性能改善や採用可否は判断していません。裁定の paired K=3・10% 基準による親の評価が必要です。
- probe は親が repo 外へ退避してから commit 対象から除外してください。

## 総括

指定 2 file に実装を残しました。焦点 24 node、最終追加 assert の 2 node 再走、probe selftest は成功しています。実 corpus 検証・変異 matrix・性能採否は未完として親へ引き渡します。