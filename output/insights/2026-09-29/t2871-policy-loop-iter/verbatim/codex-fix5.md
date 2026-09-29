## 総括

R15 を修正しました。変更は test file の 1 行だけです。

## 変更内容 (file:line)

[orchestrator/tests/test_p3_s4_loop_policy.py:822](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2871-fix5/orchestrator/tests/test_p3_s4_loop_policy.py:822) の子 process 起動 argv に `-B` を追加しました。T1〜T3 の assert は変更していません。

## 代役が production と同じ流れになった根拠 (checkout 回数、evidence の判定、authority の有無)

`main` は checkout を 1 回開き、候補と stock を同じ `sub` で評価します。代役は候補に非 stock の evidence と coder authority、stock に `STOCK` evidence と authority なしの context を渡します。admission は stock evidence を先に判定します。

## 実走した検査と結果 (未実走はそう書く)

- `py_compile`: rc=0
- bytecode guard 検査器: rc=0
- pytest・T1〜T3: 未実走（親が焦点走を実施）

## 未解決・判断が要る点

ありません。