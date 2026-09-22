1. 変更箇所
   - `test_ccbench_spawn_sites.py`：旧2853行の `test_b5_submitter_process_launch_inventory_is_exact`（24行）を除去し、指定 base に復元。
   - `test_b5_contrast_launch.py:329`：`test_registered_schedule_llm_four_per_stage` を各 `(block, stage)` の LLM 4本検査だけに整理。
   - 同335行：`test_registered_schedule_six_orders_twice` に6順序×2回・先後均衡の検査を集約。共通 helper を除去し、出力から独立に数える検査と期待値を維持。他の test は変更なし。

2. base との bytes 一致
   ```bash
   git show 8fd2a2f5c775954d6a32cee019ac7ce276298e4d:orchestrator/tests/test_ccbench_spawn_sites.py | cmp - orchestrator/tests/test_ccbench_spawn_sites.py
   ```
   **rc=0、一致。**

3. 静的検査
   - `python3 -m py_compile orchestrator/tests/test_ccbench_spawn_sites.py orchestrator/tests/test_b5_contrast_launch.py`：**rc=0**
   - `git diff --check`：**rc=0**

4. 変異の検出先（すべて `test_b5_contrast_launch.py`）

   | 変異 | 落ちるはずの node | 検出根拠 |
   |---|---|---|
   | MA5 | `test_registered_schedule_coordinates` | 固定した系列→block 対応 |
   | MA6 | `test_registered_schedule_six_orders_twice` | 回転除去による6順序×2回の崩れ |
   | MA7 | `test_registered_schedule_six_orders_twice` | 逆順欠落による順序頻度・先後均衡の崩れ |
   | MA8 | `test_registered_stage_job_counts` | stage 別件数・stock の stage=2 |

5. **テスト・変異は未実走。** commit・docs・production code・登録簿の変更は行っていません。

## 総括

R5・R6 は実装済み・未実走です。base との bytes 一致と静的検査は確認済みです。