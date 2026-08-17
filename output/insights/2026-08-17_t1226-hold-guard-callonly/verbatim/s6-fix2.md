## 変更

- F1 — [test_growth_test_holds_contract.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1060): guard 前の held function 名に対する全 `Load` 参照を拒否する閉じた規則へ変更。default 引数、`setattr`、`partial`、fixture default を含む回帰検査を [同:1359](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1359) に追加しました。
- F2 — [同:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:530): module 直下 import に基づく alias map、局所 shadow、静的到達不能判定を追加。[同:910](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:910) で注釈付き spec と loader alias を逆引きし、解決不能な `exec_module` は binding error へ倒しました。
- F3 — [同:1735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1735): guard 後 module marker と autouse fixture markerを追加。[同:1811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1811) で両 marker が出ないことを固定し、収集時拒否と呼出時拒否を区別しました。
- F4 — [growth_test_holds.py:612](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/growth_test_holds.py:612): `inspect.currentframe()` が `None` の場合を拒否側へ変更。対応する検査は [test_growth_test_holds_contract.py:1631](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1631) です。
- F5 — [同:1788](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1788) に package import 正例、[同:1835](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1835) に `--confcutdir` 拒否 node を追加しました。
- F6 — [同:1386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1386): 実 consumer 2 ファイルの全量読込を廃止し、由来の `file:line` コメントを持つ固定サイズ synthetic 複製へ置換しました。

## 検証

- 2 ファイルの AST parse、`git diff --check`、U+0300〜U+036F 不在を確認しました。
- 純 AST probe で現行 13 held file がすべて `errors=(), self_load=False`。F1 の過剰拒否となる正当な pre-guard 参照はありませんでした。
- registry は `count=59`、held file 13、指定 SHA-256 のままです。
- pytest を介さない spec import、package import、非委譲 main、frame 判定不能の probe は成功しました。
- pytest は指示どおり未実走です。67 passed の再確認や closed の申告はしていません。`ruff` は環境にありませんでした。
- tracked 差分は指定された2ファイルだけです。docs 編集と commit は行っていません。

## 残件

F1〜F6 に未実装項目はありません。裁定どおり、`__wrapped__` / closure 経由、別 thread の pytest import、`__name__` 偽装には触れていません。既存の未追跡 `output/insights/2026-08-17_t1226-hold-guard-callonly/` も変更していません。

## 総括

- pre-guard 退避を列挙ではなく全参照禁止で閉じました。
- self-load 判定は実 import、到達可能性、loader 解決を確認します。
- M3 を検出する module・fixture marker 証拠を追加しました。
- 成長比例 parse を固定サイズ synthetic 検査へ置換しました。
- pytest 未実走のため、最終受入は親の実走対象です。