1. **変更前と失敗理由（静的）**
   採用 commit の後に同 variant の別 attempt の start＋abort があり、最後の終端が abort でした。certified 証拠が拒否され、`_resolve_duplicate` が `aborted` を返していました。

2. **変更箇所**
   所有ファイル [test_p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2632-unit-a/orchestrator/tests/test_p3_s4_loop.py:7239) の2関数だけを変更しました。
   - `_base_selected_commit:7239`：任意引数で失敗 attempt を採用 attempt の前に記録。
   - `test_base_provenance_duplicate_reuses_selected_attempt:7263`：WAL から両 ID を読み、相違を確認。`duplicate`、採用 ID、refs の厳密一致、保存 report entry からの先行 record 除外を assert。WAL bytes 不変の assert も維持。

3. **静的検査**
   - `python3 - <<'PY' … PY`：`compile()` による構文検査と AST 比較、**rc=0**。変更対象2関数が基準 `36fb14a3d` に存在せず、それ以外が HEAD と一致することを確認。ファイル生成なし。
   - `git diff --check`：**rc=0**。

4. **共有 helper の影響**
   `prior_failed_attempt=False` が既定値です。他の呼出元 `test_base_provenance_keeps_all_attempt_records` は従来どおり start・verify 2件・commit の4件を生成し、検証意図は変わりません。

5. **実装済み・未実走**
   親が実走する nodeid：
   ```text
   orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_duplicate_reuses_selected_attempt
   orchestrator/tests/test_p3_s4_loop.py::test_base_provenance_keeps_all_attempt_records
   ```

6. **変異の自己点検（静的）**
   - **S3**：refs の attempt 条件を外すと先行2件が混入し、evidence の厳密一致で落ちる想定です。
   - **再照準 S4**：最初の start の ID に置換すると、有効な先行 start は存在するため start 検査を通り、採用 attempt の取り違えによる evidence 不一致で落ちる想定です。

   いずれも fixture による `aborted` が先行する構造は解消しました。KILL は未確認です。

## 総括

**実装済み・未実走**。所有1ファイルだけを変更しました。production・docs の変更、テスト実行、commit は行っていません。
