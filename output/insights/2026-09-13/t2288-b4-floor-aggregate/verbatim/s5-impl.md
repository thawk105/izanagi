## 変更した file と関数

**実装追加済みですが、段 5 は未完了です。**

- [issuer](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2288-impl/orchestrator/campaign/p3_b4_floor_artifact_issuer.py:1031)：集約 API、期待 spec・閉包検査、Fraction 最大の合成、v2 再構成 loader、CLI 分岐を追加。
- [issuer test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2288-impl/orchestrator/tests/test_p3_b4_floor_artifact_issuer.py:787)：15 関数、静的展開で 48 ケースを追加。

既存テスト・decorator は変更していません。docs・duration ledger の編集、git add、commit はしていません。

## 受理集合の変更 (前と後)

変更前は単一 summary の自己整合を検査し、v1 を発行・読込していました。spec 全体の被覆は要求していませんでした。

変更後もこの経路を維持します。`issue_authoritative_floor`、`load_floor_pair_summary`、`_authority_value`、publisher の本文は不変です。

新規集約経路では明示期待 spec 列・2 窓・閉包一致を要求し、v2 を受理します。旧 CLI の省略形・反復時の最終値採用を維持し、新専用引数の混入は拒否します。n=62・24 時間分離は検査しません。

## 実走結果 (nodeid と範囲)

**実走した pytest nodeid は 0 件です。**

```text
python3 tools/run_tests.py orchestrator/tests/test_p3_b4_floor_artifact_issuer.py -q
```

`qstat -Q` 失敗で rc=16、子は未起動でした。

指定された代替コマンドも試しました。

```text
PYTHONPATH=. python3 -m pytest orchestrator/tests/test_p3_b4_floor_artifact_issuer.py -q
```

PreToolUse hook が Pegasus ログインノードでの直接 pytest を拒否しました。

材料レポート・直列化、および自己列挙した collection／shard／schedule／duration 関連テストも runner で試しましたが、同じ理由で未起動です。構文解析、既存関数の静的比較、`git diff --check` は通りました。

## 負例の到達段階

以下の停止理由を assert するテストを追加しました。**到達の実走確認は未実施です。**

|対象|assert する停止理由|
|---|---|
|窓の欠落・余剰・重複・帰属変更|`aggregate_window_binding_error`|
|層・セル被覆欠落|`aggregate_strata_error`／`aggregate_cell_coverage_error`|
|標本の欠落・予定外 index・非交差違反|`aggregate_sample_partition_error`|
|sample／record／campaign／stratum 件数|`aggregate_sample_count_error`|
|欠測率・閾値・admissible|`aggregate_drop_policy_error`|
|統計識別子|`aggregate_statistics_error`|
|集約 identity 不一致|`aggregate_identity_error`|
|v999／aggregation 欠落|`artifact_schema_error`／`schema_error`|
|既存成果物への再発行|`artifact_exists`|

閉包負例は既存の自己整合検査を先に呼ぶ構成です。identity 負例は合成関数単位であり、単体有効な spec の公開 API 負例を代替しません。

## 波及の静的列挙

- `test_p3_b4_material_report.py` の v1 fixture・非保証期待は維持。v2 では全 source と spec の保存が必要になります。
- private `_authority_value` を直接呼ぶ既存テストへの本文変更はありません。
- 共有 fixture、material-report の group 構成は変更していません。
- raw-record producer から report builder への接続、consumer／serialization 関連の回帰は未実走です。
- 新規 nodeid の duration 登録は親の実測待ちです。

## 未実走・未完了

- **3 spec・各 2 窓の公開発行 → loader → resolver → material report の正例は未作成です。**
- 再構成改変、source 脱落、期待 spec 閉包、窓数などの公開 API 負例も未完了です。
- 追加済みテストは機構単位の確認であり、上記正例を代替しません。
- 指定済み fixture の Git／calibration stub は新規テストへ流用していません。追加読取の回答がないため、射影範囲を維持しました。
- 全テスト、変異検査、親の受入全走は未実走です。

## 総括

集約実装と機構単位テストは追加済み・未実走です。  
必須の公開 API 正例と負例が残るため、段 5 完了とは報告しません。