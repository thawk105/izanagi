1. **変更箇所**
   - `tools/b5_llm_round.py:419` の `record_models`：版の異常を `reasons` から新設の `version_notes` へ移動。
   - `orchestrator/tests/test_b5_llm_round.py:223`：`test_model_record_version_is_recorded_only` を追加。実物の `record_models` を呼び、null・空文字・数値の版と `"2.1.278"` の混在を検査します。

2. **一致判定の前後**
   - 修正前：版の異常も `matches_expected=false` の原因。
   - 修正後：ファイルの可読性・JSON の正常性、assistant 行が1件以上、全 assistant の model 存在、model 集合が `{expected}`、role 一致だけで判定。版の異常は記録のみ。rc の挙動は維持しています。

3. **静的検査**
   - `PYTHONPYCACHEPREFIX=/tmp/t2797-b2-pycache python3 -m py_compile tools/b5_llm_round.py orchestrator/tests/test_b5_llm_round.py`：rc=0。

4. **変異の検出先（未実証）**

   全 node は `orchestrator/tests/test_b5_llm_round.py::` 配下です。

   | 変異 | 落ちるはずの node |
   |---|---|
   | MB5 | `test_models_collect_all_assistant_ids` |
   | MB6 | `test_model_record_metadata_and_raw_hashes` |
   | MB7 | `test_model_record_flags_mismatch` |
   | MB8 | `test_registered_round1_prompt_golden` |
   | MB9 | `test_model_record_version_is_recorded_only` |

5. **未実走**

   テスト・変異検証は実行していません。既存テストの期待値は変更せず、所有2ファイルだけを編集しました。docs 編集・commit は行っていません。

## 総括

R1／MB9 は実装済み・未実走です。静的コンパイルは成功しました。