1. 変更前の呼出しは次のとおりでした。
   ```python
   commit_receipt_support.log_receipted_commit(
       layout, variant, L.ENV_TAG,
       {"build_attempt_id": attempt, "fitness_tps": 1.0}, operation_identity=attempt)
   ```
   `tags` の既定値は `("legacy",)` ですが、WAL の `verify_done` は `legacy` / `s2` の2件で、受領証の証拠と一致していませんでした。

2. [_base_selected_commit の呼出し](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_s4_loop.py:7257)に `tags=("legacy", "s2")` だけを追加しました。

3. 静的構文検査は **rc=0**。追加ファイルを作らない方法で実施しました。
   ```bash
   python3 -B -c 'from pathlib import Path; p = Path("orchestrator/tests/test_p3_s4_loop.py"); compile(p.read_bytes(), str(p), "exec")'
   ```

4. `test_base_provenance_keeps_all_attempt_records` は静的に点検済みです。WAL の4件の構成と attempt ID は変わらず、refs の期待値も実レコードから生成されます。期待値・assert の変更はありません。

5. **実装済み・未実走**。親が走らせるべき nodeid：
   ```text
   orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_duplicate_reuses_selected_attempt
   orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_keeps_all_attempt_records
   ```

## 総括

指定の1呼出しだけを修正しました。テスト・commit は未実行です。