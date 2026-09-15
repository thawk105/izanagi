## 実装した内容

裁定 §3 の正例1本を実装しました。実 issuer → resolver → builder を通し、入力由来の期待値で assert (a)〜(f) を検証します。

| 変更ファイル | 追加／削除行 |
|---|---:|
| `orchestrator/tests/test_p3_b4_material_report.py` | +101 / −0 |
| `orchestrator/tests/test_real_repo_serialization.py` | +1 / −0 |
| `orchestrator/tests/acceptance_duration_ledger.json` | +2 / −1 |

台帳は実測に基づく79.0秒を追加し、`nodeid_count` を23110へ更新しました。

## 実走結果

指定の自走 harness で実行しました。

- `orchestrator/tests/test_p3_b4_material_report.py` 全範囲：**50 passed、rc=0**（304.11秒）。
- 同ファイルの `::test_aggregate_authoritative_floor_reaches_public_material_report` 選択走：**1 passed、49 deselected、rc=0**。
- 単体JUnit所要：78.765秒。共有fixture setupを含め、有効数字2桁で台帳へ登録。
- ASTによるcanonical集合一致、既存テスト不変、既存台帳項目不変、`git diff --check` を確認済み。

## 波及の静的列挙

- 共有 `immutable_publication` のconsumerが1件増加します。fixture自体とmodule級cacheは変更していません。
- 所有外の `_aggregate_public_sources` → `test_floor_pair_driver` helperを再利用します。Git・calibration等のpatchはテスト終了時に復元されます。
- 既存のraw producer・producer auth experiment等のbuilder callerへの本番変更はありません。
- 関連制約は以下です。**meta-test自体は未実走**です。
  - `test_real_repo_group_collection_exactly_matches_canonical_nodes`：golden、fixture consumer集約、xdist契約。
  - `test_shard_assignment_preserves_live_xdist_group_components_and_split_control`：shard閉包。
  - `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`：duration coverage。
  - 追加発見：`test_g7e_checked_in_ledger_has_valid_schema_and_finite_durations`：件数・形式整合。
  - `test_t1574_changed_suite_ledger_node_delta_is_exact` の固定対象に新nodeは含まれません。

実装前後で本番の受理・拒否挙動は変わりません。既存の不在・不正pin・assembly失敗の期待値を維持し、集約v2の最大床値と非保証が公開builderのbytesへ届く正例を追加しました。

## 裁定との差分

ありません。commit・docs・本番コード・編集禁止ファイルの変更はありません。

## 総括

実装と対象ファイル全走は完了しました。親側の全体走・meta-test・変異検証は残っています。実Git凍結、calibration真正性、publish、certification成立を証明したとは扱いません。