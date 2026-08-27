## 前提の確認

射影された 3 文書は全文確認済みです。実装前検査で、次の指示衝突を検出したため停止しました。

- 必須挙動: 壊れた registry bytes の loader failure は `FIELD_MISSING_OR_ILL_TYPED`
- 既存期待値: [test_p3_b4_analysis_path.py:425](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/tests/test_p3_b4_analysis_path.py:425) は同じ loader failure に `BINDING_DOMAIN_ERROR` を要求
- 絶対不変条件: 既存テストの期待値を変更してはならず、期待値が誤りなら実装せず停止

両方を同時には満たせないため、1 byte も編集していません。

## 所見の対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| 所見 1 | partial | 単位 A は整数比 tuple を受理し、単位 B の独自変換は拒否することをコード上でも確認した。修正は所見 2 の停止条件により未実施。 |
| 所見 2 | partial | [p3_b4_analysis_path.py:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2001-b4-analysis-path/orchestrator/campaign/p3_b4_analysis_path.py:109) 以降の一括捕捉と誤分類を確認したが、既存期待値との直接衝突により未実施。実走していないため `closed` ではない。 |

`regressed` はありません。変更自体を行っていないためです。

## 変更したもの

変更なしです。指定された 6 ファイルを含め、作業ツリーへ新たな編集は加えていません。

`git status --short` に表示された B-4 の未追跡 8 ファイルは、作業開始前から存在していた成果物です。

## 実走結果

| command | nodeid | rc | 結果 |
|---|---:|---:|---|
| `python3 tools/run_tests.py ...` | 0 | 未実行 | 停止条件に該当したため実走せず |

親の既存記録は `test_p3_b4_analysis_path.py` が 9 failed / 3 passed、失敗 9 件はすべて `BINDING_DOMAIN_ERROR` です。これは今回の実走結果ではありません。

## 受理集合

受理について、意図された `int` / `Fraction` / 整数比 tuple の共通受理は未実装であり、`reference_tps=(100, 1)` を持つ 201 件の正例は現在も統合経路で成立 verdict まで到達しません。

拒否について、`float` / `bool` / `Decimal` / 非有限 / 非正の値を拒否する既存集合には変更を加えておらず、`reference_tps=100.0` の負例は引き続き domain error となる設計です。ただし今回は実走確認していません。

## 波及可能性

静的検索で確認した波及面は次のとおりです。

- 所有外 producer: `p3_b4_analysis_ledgers.py` の `build_contract_binding()` が整数比 tuple を生成する。編集していません。
- 所有外テスト: `test_p3_b4_analysis_ledgers.py` が同 producer を検査する。編集していません。
- caller: 現時点で `evaluate_b4_artifacts()` の実 caller は指定された path テスト内だけです。
- 共有 fixture: `conftest.py` 等に共通 B-4 fixture は見つからず、`_artifacts()` と `_binding()` は各所有テスト内のローカル fixture です。
- consumer: preregistration consumer は source-closure の固定 path に列挙されていますが、静的検索では実在 caller または consumer test は見つかりませんでした。

## 未了と限界

所見 2の新しい理由分類を採用するには、既存テストの `BINDING_DOMAIN_ERROR` 期待値を `FIELD_MISSING_OR_ILL_TYPED` へ変更する必要があります。これは今回の絶対不変条件に抵触します。

進行には、次のどちらを正とするかの裁定が必要です。

- 新しい loader 分類を優先し、該当する既存期待値の変更を許可する
- 既存期待値を維持し、loader failure を `BINDING_DOMAIN_ERROR` のままにする

## 総括

既存テスト期待値と所見 2 の必須挙動が同一入力で矛盾しています。「期待値が誤りなら実装を変えず停止」の指示に従い、修正・テスト実走とも行わず `partial` で停止しました。