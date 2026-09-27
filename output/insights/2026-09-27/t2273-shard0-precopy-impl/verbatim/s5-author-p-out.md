## 変更

- [集計器](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-probe/probe-t2273pi/t2273pi_ab_analyze.py): `expected-added-nodes.json` を必須入力とし、E1 を追加 node の集合で判定。4 通りの記録区分と、各 B 走の W_max の 300 秒超過を Markdown・JSON に追加。
- [系列起動器](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-probe/probe-t2273pi/t2273pi_run_series.sh)、[測定起動器](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-probe/probe-t2273pi/t2273pi_run_measure.sh)、[温め起動器](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-probe/probe-t2273pi/t2273pi_run_warm.sh)、[門番設定](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pi-probe/probe-t2273pi/t2273pi_gate.conf): job dir、slug、接頭辞、import 名を移植。入力ファイルの欠落・空・形式不正は投入前に拒否する。

## 実走

- `python3 -m py_compile probe-t2273pi/*.py`、全 `.sh` への `bash -n`: 成功。
- 前回 `runs/` を読み取り専用で集計: 対差 `+19.111 / +19.679 / −4.341` 秒、対率中央値 `5.2%`、B の W_max 中央値 `348.387` 秒で一致。land・5 分とも `not-met`、記録区分は `no-land-next-b`。
- 新 wave の測定系列は**実装済み・未実走**。

## 移植元のまま残したもの

門番、投入台帳、hash 照合、有効性判定は維持。赤走は親が書く `classification.json` だけで分類し、B の早期 memo 超過も自動で infra 扱いしない。

## 総括

`probe-t2273pi/` に移植用の 5 ファイルを用意しました。前回系列と E1 の集合判定を確認済みです。tracked file は変更せず、commit も作成していません。