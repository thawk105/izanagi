## 変更

[test_verifier.py:3399](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-u4/orchestrator/tests/test_verifier.py:3399) の新規 v3 試験・helper のみ修正しました。

- 今回：追加 **71 行**、削除 **21 行**、計 **92 行**。
- R9 累計（`eef04f5a7` 起点）：追加 **486 行**、削除 **0 行**。上限 **800 行以内**。
- 既存試験と自走 runner は変更前との完全一致を確認。`git diff --check` 成功。
- production・docs の変更、commit・branch 操作なし。

## B1〜B4 の充足

以下の行番号はすべて `orchestrator/tests/test_verifier.py` です。

| 項目 | 修正と根拠 |
|---|---|
| B1 | **3799、3817〜3826**：parse／edge の子を実際に異常終了させ、packed／tuple 各呼出し直後に親 PID への fallback と終了した子 PID を確認。障害なしの結果・v3 出力との完全一致を検査。**3435〜3442** で graph・取引 metadata も legacy と比較。 |
| B2 | **3417、3640、3651**：legacy は各入力につき一度、compact は workers=1／2 で実行。経路間比較を維持。 |
| B3 | **3665**：R／W を `_v3_frame` の reads／writes から生成し、宣言件数を実際の行数に一致させた。 |
| B4 | **3411、3426〜3431**：通常 fixture の packed 型と、tuple builder が対象 graph を構築した事実を肯定 assertion。 |

## 実走結果（逐語）

最終版で次を実行し、終了コード **0** を確認しました。

```text
PYTHONPATH=. python3 orchestrator/tests/test_verifier.py
```

結果末尾：

```text
132 passed, 0 failed, 0 skipped
```

[実走ログ全文](/tmp/t2854-u4-fix2-run.log)。v3 試験は全18件 PASS。pytest・run_tests.py は指定どおり実行していません。

## 未解決

今回の B1〜B4 に未解決事項はありません。受入全走・変異 KILLED の実証は今回の実走範囲外です。production と変異対象位置は変更していません。

## 総括

B1〜B4 を v3 試験・helper 内で修正しました。
parse／edge 障害後の逐次復帰を、対象呼出し直後に確認します。
復帰後の表・取引種別・結果の比較を維持・強化しました。
legacy の重複実行を除き、compact の workers 別比較を維持しました。
table 拒否 fixture の件数を修正し、packed／tuple の経路確認を追加しました。
最終版の自走結果は `132 passed, 0 failed, 0 skipped` です。
R9 累計は 486／800 行で、既存試験・production は変更していません。