## 変更

- G1: [test_growth_test_holds_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:1059)
  - guard 前の import 時評価位置だけを走査する visitor に置換。
  - module/class 本体、関数の既定引数・デコレータ・注釈、lambda の既定引数を対象化。
  - 関数・lambda 本体は除外。
  - held 名の `Name Load` と同値文字列リテラルを拒否。
  - `globals()["<held名>"]` の拒否と、実在 `_run()` 由来の関数内参照を受理する回帰検査を追加（1417–1467行）。
- G2: [test_growth_test_holds_contract.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1226-hold-guard-callonly/orchestrator/tests/test_growth_test_holds_contract.py:530)
  - 関数・class scope 内の `import` / `from ... import ...` も alias map に正規名として登録する方式を採用。
  - 関数内 `import runpy` と alias 付き `from runpy import run_path` の回帰検査を追加（1570–1583行）。

## 検証

pytest は環境制約に従い未実走で、75 passed の再確認や緑申告はしていません。解析関数を直接呼ぶ静的 probe では次を確認しました。

- registry: `count == 59`
- digest: `30e646a80e6dfc7c04ec2e249462789ac7cb10f1afaa6979491a3312d5d6508c`
- held file: 13
- 現行13面すべて: `errors=(), self_load=False`
- 実在 `_run()` 形を含む call-only 合成: `(errors=(), self_load=True)` で受理
- module直下の `globals()["<held名>"]`: binding error
- 関数内 `import runpy; runpy.run_path(__file__)`: `(True, ())`
- 既存の shadow・到達不能・未解決 loader の直接契約検査: 成功
- `compile()`、`git diff --check`: 成功
- 編集差分は指定されたテストファイル1件のみ。docs・commit・既存 untracked 成果物には未接触。

## 残件

- pytest、mutation matrix、親受入は未実走です。環境制約により親側での実施が必要です。
- 実装上の未対応所見はありません。

## 総括

G1の穴と過剰拒否を、import時評価位置に限定した走査で同時に修正しました。  
G2は局所importをalias mapへ含め、自己読込の見逃しを閉じました。  
registryと現行13面の静的不変条件は維持されています。  
pytest未実走のため、完了・closed・緑とは申告しません。