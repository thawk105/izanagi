## 現行の受理・拒否

実装前の land は v5 受領証だけを受理し、別 schema や余分な field を拒否していました。

## 実装内容

指定された 7 file だけを編集しました。分類・選択 CLI、tested main の blob を使う縮小 launcher、`dev_wave_wait.py acceptance --scoped`、land の別 schema 検証と forward-main blob 比較を追加しました。v5 の field・検査条件と、flag なしの経路は維持しています。commit は作成していません。

分類器が使う `tools/` 変更拒否とは別に、land 自身にも `tools/` を含む tip の拒否を置きました。`run_tests.py` には縮小選択の実行形を追加し、既存の全受入形判定は変更していません。これは恒久除外と loadgroup などを既存 runner 経由で効かせるためです。

## 実走結果

指定された両 pytest コマンドは、Pegasus ログインノードの PreToolUse hook に実行前に拒否されました。**pytest の緑は確認していません。**

代替として、合成 repo の fixture を作ってテスト関数を直接呼び、A の 29 ケースと B の 21 ケースが通りました。B には縮小受領証による land 成功、v5 正例、実装面混入の拒否、受領証 drift、forward-main の各 blob drift、直接 gate が rc=1 のとき受領証を出さないケースを含みます。許可 path 判定をプロセス内で一時的に緩めると負例が赤になることも確認しました。`py_compile`、`git diff --check`、`check_docs.py` は通りました。`.scoped-tmp` は作成されていません。

## 所有外への波及

静的に確認した caller・consumer は、v5 の `acceptance_issuer_reference.py`、`check_wave_startup.py`、`check_docs.py`、既存の launcher・wait・land・runner 関連テストです。共有面は `conftest.py`、`growth_test_holds.py`、`acceptance_duration_ledger.json` です。台帳は未登録 node を fail-soft に扱い、`check_docs.py` も違反なしだったため、所有外 file は編集していません。

## 未解決と判断

pytest は hook の拒否により未実走です。また、実際の縮小受入から land までの通し実行と所要比較は、この作業木では未確認です。直接呼出しの結果を pytest 実走や実環境の受入結果とは扱いません。

## 総括

plan v2 の実装と合成 repo での主要な正負確認は完了しました。統合判断には、計算ノードでの pytest と実際の縮小受入・land の通し確認が残ります。