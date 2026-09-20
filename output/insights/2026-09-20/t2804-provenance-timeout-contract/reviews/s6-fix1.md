## 変更一覧

| file:line | 変更前 → 変更後 |
|---|---|
| `tools/check_ai_provenance.py:2945` | `deadline_at_margin_s=` → `deadline_margin_s=` |
| `orchestrator/tests/test_check_ai_provenance.py:6988` | 期待行の同 field 名を改名 |
| `orchestrator/tests/test_dev_wave_land.py:9960` | fake stderr の同 field 名を改名 |
| `orchestrator/tests/test_t2337_dispatch_timeout_overrides.py:179,205` | 指定2本の先頭に `monkeypatch.delenv(provenance._PROVENANCE_OUTER_DEADLINE_ENV, raising=False)` を追加。期待値は不変 |

## 実走した検査

実行コマンド：

```bash
PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_check_ai_provenance.py', '-q', '-rf', '-k', 'outer_deadline']))"
PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_dev_wave_land.py', '-q', '-rf', '-k', 'provenance']))"
PYTHONPATH=. python3 -c "import sys, pytest; sys.exit(pytest.main(['orchestrator/tests/test_t2337_dispatch_timeout_overrides.py', '-q', '-rf']))"
```

| 実走 nodeid 範囲 | passed | failed |
|---|---:|---:|
| `test_check_ai_provenance.py` の `-k outer_deadline` 選択全件 | 31 | 0 |
| `test_dev_wave_land.py` の `-k provenance` 選択全件 | 38 | 0 |
| `test_t2337_dispatch_timeout_overrides.py` 全件 | 21 | 0 |

全コマンド rc=0。`git diff --check` も成功。

## 所見対応表

| 所見 | 対応 |
|---|---|
| レビュー B must-fix 1：終端 field 名 | closed |
| レビュー B should 3：t2337 の env 隔離 | closed |
| レビュー A should 1：終端 field 名 | closed |

## 総括

指定4ファイル・5箇所の修正を完了し、対象90件が成功しました。値・順序・他 field・名前変更以外の期待値は不変です。`git add` / `commit` / `stash` / branch 操作は実行していません。