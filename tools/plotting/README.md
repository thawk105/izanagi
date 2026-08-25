# plot_backoff.py — backoff sweep campaign の論文品質作図

`output/campaigns/<id>` の artifact から、論文品質の backoff sweep 図を生成する
共通スクリプト。図の数値は WAL (throughput の n 反復生値) と dat (abort%/IPC 集約値) から
その場で計算し、CCBench commit は campaign の lock file から読む。生成した図の provenance には
入力・生成器・出力の SHA-256 と、**実際に描いた基準線の label・値・genome** を記録する —
「どの WAL からどの図を作り、図のどの線が何を指しているか」が閉じる (proof-chain 思想と整合)。

## 使い方

```
python plot_backoff.py [--baselines LIST] OUT_PREFIX CAMPAIGN_DIR [CAMPAIGN_DIR ...]
```

`--baselines` は `no-backoff` / `stock-adaptive` の comma 区切り部分集合。既定は
`no-backoff,stock-adaptive` で、従来の 2 基準線を保つ。`no-backoff` だけを描くときは
次のように明示する。未知の値はエラーになる。

```
python plot_backoff.py --baselines no-backoff OUT_PREFIX CAMPAIGN_DIR [CAMPAIGN_DIR ...]
```

例 (3 workload を 1 枚に統合):

```
python plot_backoff.py --baselines no-backoff figures/backoff_sweep \
    output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9 \
    output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e \
    output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7
```

campaign を複数指定するとその順で横並び (workload 比較) になる。1 つだけ渡せば単独図。

## 出力

- `OUT_PREFIX.png` / `.pdf` — 図 (上段 throughput+95%CI・baseline、下段 abort%+IPC)
- `OUT_PREFIX.provenance.json` — schema `izanagi-backoff-figure-provenance/v2`。
  campaign ごとに WAL・dat・lock file の repo-relative path と **full SHA-256**、
  生成器自身の path と SHA-256、出力 PNG / PDF の SHA-256、測定条件 (`conditions`)、
  そして `baselines[]` を記録する。`baselines[]` は **実際に図へ描いた基準線だけ**を、
  図中の label 文字列・その線の y 値 (tps)・95% CI 半幅・genome の組で持つ。
  この list が「図のどの線が何を指しているか」の機械可読な正本である。

## 設計上の約束

作法の全文は `FIGURE_CONVENTIONS.md` (図種に依存しない規約の本体)。本スクリプトはその backoff sweep 向け実装。

- **入力は WAL・dat・campaign の lock file の 3 種**。図の数値はすべてその場で再計算する
  (記憶・手写しなし)。3 種とも provenance で SHA-256 束縛する。
- **95% CI は throughput の n 反復生値から** (点推定 = 標本平均、半幅 = 小 n では
  t 分布 `t_{0.975,n-1}·s/√n`、n≥30 は `1.96·s/√n` の正規近似。正本は
  `FIGURE_CONVENTIONS.md` §2)。n<2 は分散を推定できず CI 計算不能なので、その点は
  誤差棒を描かない (幅ゼロの棒を「95% CI」と偽装しない)。
- **abort%/IPC は dat の集約値** (現状 1 点集約 — 反復値が保存されれば CI 化可能)。
- **依存は matplotlib/numpy のみ**。外部スタイル非依存で自己完結。
- **計測機上では走らせない** (どのマシンが計測機かは時期で変わる — 環境タグの正本を参照)。
  図生成に計測は不要で、単一テナント直列の計測窓を汚さないため、WAL/dat を計測機外に
  取り出して実行する。

## 拡張ポイント

- abort%/IPC の反復値が WAL に入れば、下段にもエラーバーを足せる (`load_campaign` の
  `abort_ipc` を reps ベースに変える)。
- backoff 以外の軸 (sort-strategy 等) は genome パースを差し替えれば流用可能。

## SS2PL lock study command example

```bash
python3 tools/plotting/plot_ss2pl_lock_study.py \
    --sweep /path/to/sweep.json \
    --controls /path/to/controls.json \
    --replication /path/to/replication.json \
    --output-dir /path/to/figures
```
