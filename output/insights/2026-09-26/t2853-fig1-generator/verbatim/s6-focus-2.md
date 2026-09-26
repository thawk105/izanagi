## 対応表

| ID | 判定 | 根拠 |
|---|---|---|
| F-M1 | closed | read 比以外の指定された11条件を3 campaign 間で比較し、不一致なら `FigureDataError`。返却前に検査し、caption も検査済みの共通値から書く。[生成器:99](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:99)、[生成器:220](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:220)、[生成器:235](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/tools/plotting/plot_p2_5_search_cost.py:235) |
| F-S1 | closed | balanced の threads だけを変更し、純関数が例外を出すことを検査する。比較を外す変異でも通る恒真テストではない。[test:62](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-fig1-redraw/orchestrator/tests/test_plot_p2_5_search_cost.py:62) |

## 新規所見

なし。前回 closed とした箇所に fix 2 起因の回帰は見当たらず、行数も生成器 395/450、test 217/300。

## 判定

**GO**（静的検査）。テスト実走は親の担当。

## 総括

指定された2件は closed。差分の書式検査も通過した。