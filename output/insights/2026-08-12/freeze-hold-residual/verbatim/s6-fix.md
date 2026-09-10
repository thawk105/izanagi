## 総括

7 件の修正は実装済みです. ただし正式な pytest 実走は Pegasus の `qstat -Q preflight rc=1` により rc=16 で停止したため, closed とは申告しません. 全項目を partial とします.

編集は次の 2 file だけです.

- [tools/hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/tools/hold_inventory.py:15)
- [test_hold_inventory.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-freeze-hold-residual/orchestrator/tests/test_hold_inventory.py:36)

docs 編集と commit は行っていません.

| 所見 | 状態 | 対応 |
|---|---|---|
| F1 | partial | `_run()` と `__main__` を追加. plain runner の assertion body は direct probe で rc=0. 正式 nodeid は未実走 |
| F2 | partial | Human 全文を独立した期待 line sequence と exact 比較. JSON top-level key を exact 固定 |
| F3 | partial | production と test の release field, Pegasus surface 全 field を test literal で exact pin |
| F4 | partial | layer 順序, label, 値, 帰属, item 順序と件数を Human 全文比較で固定 |
| F5 | partial | repo root bootstrap を追加. clean environment の script と module 起動はともに rc=0, `cmp` も rc=0 |
| F6 | partial | 4 bypass 経路と `PYTEST_ADDOPTS` transport を追加. `effective_status_assumption` を追加 |
| F7 | partial | conftest の `_growth_holds_opted_in()` を import し, unset, exact token, 他の非空値を照合 |
| regression | なし | 静的 probe で既知の後退なし. 正式 pytest 未成立 |

実走状況:

- `python3 tools/run_tests.py orchestrator/tests/test_hold_inventory.py -q`
  - 対象範囲: file 全体
  - 結果: rc=16, test collection 前に dispatch infrastructure failure
- `python3 tools/run_tests.py orchestrator/tests/test_plain_runner_coverage.py -q`
  - 対象範囲: file 全体
  - 結果: rc=16, test collection 前に dispatch infrastructure failure
- 両方の `--force-dispatch` も同じ rc=16
- 実走済み pytest nodeid: なし
- green の申告: なし

補助確認は成功しています.

- Human exact renderer と conftest 3 分岐の direct assertion probe: rc=0
- 両 CLI 起動形の exact output 比較: rc=0
- plain runner coverage assertion body の direct probe: rc=0
- non-ASCII mark, symbol, punctuation scan: 該当なし
- `git diff --no-index --check`: whitespace error なし

静的な波及可能性:

- repository 内に新しい inventory schema の caller は見つかりませんでした.
- 外部 CLI consumer が layer key や bypass 件数を exact 固定している場合, 新規 field と surface の追加が影響します.
- shared fixture の `conftest.py::_growth_holds_opted_in()` が変更されると F7 test が赤になります.
- `growth_test_holds.py` の台帳変更は item 行と件数へ反映されます.
- `freeze_verification_hold.py` の release 契約変更と Pegasus env allowlist の変更は exact pin test が検出します.
- `test_plain_runner_coverage.py` は追加した self-run harness を consumer として検査します.

正式な閉鎖には `qstat -Q` が利用可能な状態で上記 2 test command の再実走が必要です.