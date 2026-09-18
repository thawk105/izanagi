## 総括

**F-MF1は実装済み・未実走です。closedとは判定していません。**

- 変更は[所有ファイル](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2775-a1-sized-results-recovery/orchestrator/tests/test_plot_a1_sized_paired.py:471)のみ。全欠落skipを除去し、既存assertで全欠落・部分欠落を拒否します。全存在時のclosure検査と生成器は変更していません。
- 全欠落1ケース、部分欠落6パターンを追加。実際の着地testを呼び、検査本体のstub化はありません。旧skip復活時はpytest／`_run`双方でAssertionErrorへ変換します。
- 静的確認：AST構文解析、`git diff --check`成功。test関数28件、重複なし。テスト・build・dispatchは起動していません。
- consumer波及：所有外の直接callerは検索上なし。共有`skiputil.py`・`conftest.py`・既存fixtureは変更なし。列挙meta-testの`test_plain_runner_coverage.py`、収集設定の`test_pytest_collection_config.py`を確認。新規2件は既存`_run`の自動列挙対象です。

M13の置換候補（old＝修正後、new＝旧skip復活）。oldは現物で**一意に1件**です。

```python
# old
    readme = (prefix.parent / "README.md").read_text()
    assert all(path.is_file() for path in paths), "fig9 integration bundle is incomplete"
```

```python
# new
    readme = (prefix.parent / "README.md").read_text()
    if not any(path.exists() for path in paths):
        skip("fig9 integration artifacts are parent-owned and not landed yet")
    assert all(path.is_file() for path in paths), "fig9 integration bundle is incomplete"
```

期待kill nodeは`orchestrator/tests/test_plot_a1_sized_paired.py::test_landed_fig9_rejects_all_missing_outputs`です。未probeです。

残件は、親dispatch終端後の対象file・meta-test実走、最終図着地後の既存closure正例確認、M13実走です。図未着地中は既存着地testの赤を期待します。commit・stageは行っていません。