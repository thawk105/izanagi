## 変更点 (file:line)

- [検査器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/tools/check_trace0_preprocess_identity.py:58)：4 引数が揃った header 差分だけに規則 v2 を適用。Git tree 照合、実 CMake の compile database、両 TRACE 値の依存・実効値確認、consumer 選定、完全展開と include 活性の比較、header 専用 report を追加しました。
- [新 test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/orchestrator/tests/test_check_trace0_header_rule.py:113)：実 CMake・g++ を使う小型 fixture を追加しました。
- [判定 script](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/output/runs/t2854-hv2/judge/run_judge.sh:1)：事前確認、GCC 11/12 の並行判定、TPC-C 負例対照を実装しました。このファイルは gitignore 下にあります。

## 自走した確認と変異の赤化確認

`orchestrator/tests/test_check_trace0_header_rule.py::` 以下の関数を **pytest を起動せず直接呼び出し**、11 件すべて成功しました。V1〜V12 の対応 test 10 件は合計 **11.65 秒**で、60 秒以内です。

| test 関数 | 結果 | 秒 |
|---|---:|---:|
| `test_v1_indirect_consumer_value_change` | 成功 | 1.02 |
| `test_v2_generated_header_hides_changed_header_without_build` | 成功 | 1.06 |
| `test_v3_v4_v9_generated_header_and_trace_one_consumer` | 成功 | 1.08 |
| `test_v5_genome_only_production_consumer` | 成功 | 2.11 |
| `test_v6_other_protocol_consumer_under_selected_genome` | 成功 | 1.94 |
| `test_v7_aggregate_requires_dependency_content` | 成功 | 1.46 |
| `test_v8_trace_effective_value_is_checked` | 成功 | 0.62 |
| `test_v10_trace_zero_value_change` | 成功 | 1.23 |
| `test_v11_include_activity_change` | 成功 | 1.09 |
| `test_v12_partial_header_inputs_rejected` | 成功 | 0.03 |
| `test_volatile_builtin_in_expansion_is_rejected` | 成功 | 1.23 |

V1〜V12 は検査器の**メモリ内コード変異**で対応 test がすべて赤になり、元のコードに戻した直接呼び出しですべて緑に戻りました。実ファイルに変異は書いていません。既存の `.cc` 決定的 report test は成功（1.84 秒）、従来の header 拒否 test の `.hh` ケースも成功（0.18 秒）。`bash -n`、Python AST 解析、`git diff --check` も成功しました。

## 未実走・懸念

- 実 CCBench の GCC 11.4／12.3 判定 job、負例対照、pytest suite は実走していません。判定結果を **pass** とは報告しません。
- **V2 の事前登録には不整合があります。** `-MG` 追加と生成 target 省略をそのまま入れた変異は、GCC が未生成 `gen.hh` で失敗し、test は赤になりますが、裁定 §4 が期待する「偽の pass」にはなりません（実測 0.65 秒）。メモリ内の欠落依存を模した V2 変異でも赤化は確認しました。V2 の期待理由を満たした証拠としては扱えません。
- 制約 meta-test は静的に調査しました。新 file は命名・import 規則の対象で、所要台帳に新 node の必須登録はありません。`test_campaign_import_invariant.py` の直接 import は既存の growth hold に拒否されたため、同 meta-test は未実走です。

## 波及の静的列挙

- `tools/pegasus/mocc_trace_pilot.sh`：既存 5 引数の呼び出しは維持。
- `orchestrator/tests/test_mocc_trace_job_contract.py`、`test_mocc_trace_pair.py`：checker 参照を確認。未編集・未実走。
- `orchestrator/tests/test_check_trace0_preprocess_identity.py`：未編集。上記 2 ケースのみ直接自走。

## 総括

指定の 3 ファイルだけを変更し、commit・計算ノード投入はしていません。小型 fixture と変異の確認は済みましたが、実 CCBench 判定と V2 の期待理由は未確定です。