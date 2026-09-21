1. **認証条件の静的確認**
   `require_persisted_certified_commit` は、対象 COMMIT の所属、非空 attempt ID、同 variant・attempt の先行 verify、`verdict="serializable"`、`certified is True`、整数の `anomalies=0`、非空 workload tag、receipt の妥当性・operation identity・証拠列一致を検査します。変更前の不足は `anomalies`。他の payload 値と receipt 呼出し引数は整合しています。receipt の生成・受理結果は未実走です。

2. **変更箇所**
   [_base_selected_commit の7256行](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_s4_loop.py:7256) に `"anomalies": 0` を追加しました。

3. **静的検査**
   - `python3 - <<'PY' … PY`：`compile()` と AST・差分検査、**rc=0**。helper 以外が不変で、helper が基準 `36fb14a3d` に存在しないことを確認。
   - `git diff --check`：**rc=0**。追加ファイル生成なし。

4. **共有 helper の影響**
   WAL の件数・順序・attempt 束縛は不変。refs は WAL から計算されるため固定期待値の修正は不要です。両テストの assert は変更していません。

5. **実装済み・未実走**
   親が走らせるべき nodeid：

   ```text
   orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_duplicate_reuses_selected_attempt
   orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_keeps_all_attempt_records
   ```

## 総括

**実装済み・未実走**。所有ファイルの helper だけを変更しました。production・docs の編集、テスト実行、commit は行っていません。
