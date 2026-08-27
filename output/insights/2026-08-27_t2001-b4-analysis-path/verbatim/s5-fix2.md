## 前提の確認

指定された5資料を全文確認し、親の裁定に従って修正しました。Web検索、docs 編集、commit、所有外コードの編集は行っていません。

## 所見の対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| 所見1 | `partial` | 単位Aへ exact ratio 変換と binding domain 述語を公開正本として集約し、単位B/Dから利用した。実走できていないため `closed` とはしない。 |
| 所見2 | `partial` | loader、binding 再生成、違反件数導出、割当照合、最終評価の例外境界を分離し、未知例外を受け皿へ写した。実走できていないため `closed` とはしない。 |

`regressed` と確認できた所見はありません。ただし実走未了のため回帰なしを動的には証明していません。

## 変更したもの

- [p3_b4_analysis_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_contract.py:227)
  - `as_b4_exact_fraction()` を公開。
  - `b4_binding_domain_is_valid()` を公開。
  - 契約内の全 exact ratio 変換と binding 検証をこの正本へ統一。

- [p3_b4_analysis_adapter.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_adapter.py:125)
  - 独自変換を正本への委譲へ変更。
  - 重複していた binding domain 実装を削除し、単位Aの公開述語を使用。
  - tuple の `reference_tps` を過剰拒否していた経路を解消。

- [p3_b4_analysis_path.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_path.py:111)
  - loader failure を `FIELD_MISSING_OR_ILL_TYPED` へ分類。
  - 広い一括捕捉を段別の境界へ分割。
  - 各段の `B4LedgerError` を個別捕捉し、未知例外はすべて受け皿へ分類。
  - 単位Aの binding 述語と exact ratio 変換を利用。

- [test_p3_b4_analysis_path.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_path.py:425)
  - 親が許可した loader failure の理由 literal だけを変更。
  - verdict、`analysis_invalid`、破損 bytes の各 assertion は維持。

## 変更した期待値

| nodeid | 変更前 | 変更後 | 凍結文面の逐語根拠 |
|---|---|---|---|
| `test_p3_b4_analysis_path.py::test_loader_failure_is_returned_as_analysis_invalid_not_raised` | `B4AnalysisInvalidReason.BINDING_DOMAIN_ERROR` | `B4AnalysisInvalidReason.FIELD_MISSING_OR_ILL_TYPED` | `binding_domain_error` は「`contract_binding` の hash・id・期待値が欠落、型違反、または `expected_block_count` が正の整数でない」。一方、`field_missing_or_ill_typed` は「上のいずれにも分類されない欠落または型違反 (受け皿)」。registry bytes の読取失敗は前者ではない。 |

ほかの期待値は変更していません。

## 実走結果

| 対象 | command | 実走 nodeid | rc | 結果 |
|---|---|---:|---:|---|
| 統合経路全ファイル、静的には12 test | `python3 tools/run_tests.py orchestrator/tests/test_p3_b4_analysis_path.py -q -rf` | 0 | 16 | `qstat -Q preflight rc=1`。dispatch child は未起動。 |

緑と記録できる nodeid はありません。

静的検査として、変更3 module、path test、既存の contract・adapter・ledgers の module/test に `py_compile` を実行し、rc=0でした。これはテスト実走ではありません。

## 受理集合

受理の含意は `int`、`Fraction`、整数比 tuple を単位A/B/Dで同じ正本により扱うことであり、静的な正例 `reference_tps=(100, 1)` は `Fraction(100)` へ変換され、201件の binding を単位Bが過剰拒否しない経路になりました。

拒否の含意は `float`、`bool`、`Decimal`、非有限値、非正値を引き続き拒否することであり、静的な負例 `reference_tps=100.0` は exact ratio 変換で拒否され、binding domain error になります。

## 波及可能性

- 所有外 producer の `p3_b4_analysis_ledgers.build_contract_binding()` は整数比 tuple を生成します。今回そこは編集せず、consumer 側を受理可能にしました。
- `evaluate_b4_artifacts()` の実 caller は静的検索上、path test 内だけです。
- adapter test、contract test、ledgers test は共通型と binding を利用するため再実走対象ですが、期待値は変更していません。
- B-4 用の共有 fixture は `conftest.py` に見つからず、各 test module のローカル helper が使用されています。
- source-closure receipt は変更した3 moduleの hash が変わるため再生成時に値が変わります。
- preregistration consumer module/test は現在の作業ツリーには存在せず、直接の consumer test は確認できませんでした。
- 旧 private 変換・述語を呼ぶ所有外コードは静的検索で見つかりませんでした。

## 未了と限界

- Pegasus dispatch failure により、path 12件、contract 38件、adapter 27件、ledgers 13件の変更後実走は未了です。
- 親の既存実走結果は変更前の基準であり、今回の緑として数えていません。
- source-closure の実 repository member は consumer 不在のため、現時点では完全生成できません。
- docs、`p3_s4_loop.py`、driver、ledgers本体とそのtestには触れていません。

## 総括

所見1の重複値域実装と所見2の広域例外分類は、コード上では指定方向へ修正済みです。構文と静的な配線は確認できましたが、dispatch が `rc=16` で停止したため、両所見とも `partial` とします。