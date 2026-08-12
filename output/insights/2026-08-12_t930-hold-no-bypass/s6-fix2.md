## F4

判定: partial

- `__main__` の終端 statement が `raise SystemExit(pytest.main(...))` または `sys.exit(pytest.main(...))` の場合だけ `pytest-delegating` と分類
- dead branch, nested function, `getattr`, alias call は `manual` とする負例を追加
- 既存 3 file は静的確認で strict shape に適合
- 実走不能のため closed とは判定せず

挙動差分:

- 変更前: `__main__` 配下の任意位置に `pytest.main` があれば受理
- 変更後: main guard が 1 個であり終端から直接 `pytest.main` へ委譲する場合だけ受理

## F5

判定: partial

- `explicit-typo`
- `explicit-user-command-extra`

上記 2 literal で軽量 held module を直接 import する fresh subprocess 負例を追加

- exact token は従来どおり受理
- 非 exact の非空値は import 段階で拒否
- held body と fixture には到達しない O(1) 検査
- M5 の `startswith("explicit")` 変異では subprocess が rc=0 となり検査が赤になる構造
- production 実装は変更なし
- 実走不能のため closed とは判定せず

## 変更 file

[test_growth_test_holds_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t930-hold-no-bypass/orchestrator/tests/test_growth_test_holds_contract.py:337)

- lines 337-376: strict AST 分類
- lines 535-546: F4 負例 4 件
- lines 684-708: F5 import guard 負例 2 件

変更はこの test file 1 件のみです. docs, conftest, production, hold 台帳は未変更です. commit も作成していません.

## 実走結果

- `orchestrator/tests/test_growth_test_holds_contract.py` 全件
  - rc: 16
  - 実行件数: 0
  - `qstat -Q preflight rc=1` による dispatch infrastructure failure
- `orchestrator/tests/test_plain_runner_coverage.py` 全件
  - rc: 16
  - 実行件数: 0
  - 同じ dispatch infrastructure failure

login node での直 pytest は実行していません. 両方とも実装済み・未実走です.

静的確認のみ `AST parse OK`, `git diff --check` 成功です.

## 総括

F4 と F5 は scope 内の検査実装まで完了しました. ただし指定の force-dispatch が投入前に rc=16 となったため両方とも partial です. scope 外の nested pytest session BLOCKER には触れていません.