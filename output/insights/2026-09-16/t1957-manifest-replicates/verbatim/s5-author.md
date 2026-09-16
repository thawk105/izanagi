## 実装した差分

- `orchestrator/campaign/trial_registry.py:55,117,282,786,800,842,1575`：両schemaをv3へ更新。必須`n`、厳密な整数型・下限2・全6 cell一致、serialization・canonical identityへの格納を実装。
- `orchestrator/tests/test_trial_registry.py:176,187,224,5063,5490,6769`：fixture、v3リテラル、canonical tuple変異`[n]`を追随。
- 同ファイル`:8749,8754,8788`：版定数、`n=3`のround trip、両source×12負例を追加。負例は例外メッセージまで完全一致で検査。
- `test_p3_autonomous_workload_trial.py:7227,10369`、`test_reflux_origin_binding.py:75,96`：fixtureの`n`のみ追加。

## 実走結果

**実装済み・未実走。** harness起動はすべて`rc=16`。`qstat -Q preflight rc=1`、`child_started=false`で、テスト本体は起動していません。

焦点指定したnodeid（接頭辞`orchestrator/tests/test_trial_registry.py::`）：

- `test_t1957_schema_versions`
- `test_t1957_six_cell_n_round_trip`
- `test_t1957_rejects_n`（24ケース）
- `test_acceptance_rejects_registry_canonical_tuple_mutation`（5ケース）
- `test_redundant_registry_duplicate_key_gate_rejects_before_canonical_bytes`

consumer側もorigin binding、originless compatibility、preregistration predicatesの各ファイルと、`test_m13_prime_public_launcher_rejects_producer_campaign_derivation_bypass`を指定しましたが、同じ理由で未実走です。

4ファイルの構文解析と`git diff --check`は`rc=0`。テスト合格とは扱いません。

## meta-test の洗い出し

以下を独自に特定し、harnessで起動を試みました。すべて上記の基盤障害で`rc=16`、未実走です。

- `test_trial_registry.py::test_t822_trial_registry_test_top_level_function_names_are_unique`
- `test_plain_runner_coverage.py`
- `test_pytest_collection_config.py`
- `test_acceptance_schedule_order.py`
- `test_update_acceptance_duration_ledger.py`
- `test_growth_test_holds_contract.py`
- `test_flaky_test_holds_contract.py`
- `test_fold_gate_nodes_contract.py`

追加テストは自走harnessの`__main__`より前に配置しました。

## 所有外への波及

- production呼び手4箇所：`orchestrator/campaign/p3_autonomous_workload_trial.py:988,1530,2148,5490`。それぞれprofile事前検査、launch admission、budget入力、CLIでv3・必須`n`の検査を受けます。
- 共有fixture `test_p3_autonomous_workload_trial.py:7227`の変更は、それを利用するregistered-launch／origin系テストへ波及します。
- `test_reflux_originless_compatibility.py:48,133`は共有fixtureを間接利用します。`:1327`以降の固定baseline比較が確認対象です。manifest hash・measurement headには既存の正規化があり、値変更だけで失敗すると断定できません。
- `s8c_preregistration_evidence.py:1650`の属性検査は部分集合判定で、`n`追加とは静的に両立します。
- 所有外ファイルの修正が必須と判明した箇所はありません。consumerの実走確認は残っています。

## 期待赤と回帰の区別

テスト本体が未起動なので、期待赤・回帰とも観測していません。

`test_s8c_preregistration_predicates.py`はcommit内のコードを読むため、commit前後で結果が変わる可能性があります。その差は**未commitに由来する**ものとして区別する必要があります。

## 裁定に従えなかった点

実装上はなし。検査の実走はdispatch基盤障害により未達です。

## 総括

指定4ファイルに保存・読込・identityの契約を実装しました。
docs編集、commit、Git index操作はしていません。
観測反復とのexact一致、受入gate、連番規約は変更していません。
**closedではなく、実装済み・未実走です。**