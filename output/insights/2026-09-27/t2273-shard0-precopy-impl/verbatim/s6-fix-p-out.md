## 変更
[集計器](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-probe/probe-t2273pi/t2273pi_ab_analyze.py) に A/B の事前 collection と追加 node 入力の検査を追加しました。系列 preflight と単走の投入前検査は集計器を通じて欠落・空・形式不正・差集合の不一致を拒否し、集計時も走自身の collection へ戻りません。

## 実走
`python3 -m py_compile` と `bash -n` は成功。前回系列の読み取り専用データから対差 `+19.111 / +19.679 / −4.341` 秒と `no-land-next-b` を再現し、3 入力の欠落・空・形式不正と差集合の不一致が拒否されることを確認しました。

## 総括
変更は `probe-t2273pi/` 内の 1 ファイルだけです。移植元の job dir への書き込みと commit は行っていません。