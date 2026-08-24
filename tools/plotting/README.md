# plot_backoff.py — backoff sweep campaign の論文品質作図

`output/campaigns/<id>` の WAL/dat から、論文品質の backoff sweep 図を生成する
共通スクリプト。図は WAL (throughput の n 反復生値) と dat (abort%/IPC 集約値) を
唯一の入力とし、生成した図の provenance を記録する — 「どの WAL からどの図を作ったか」
が閉じる (proof-chain 思想と整合)。

## 使い方

```
python plot_backoff.py OUT_PREFIX CAMPAIGN_DIR [CAMPAIGN_DIR ...]
```

例 (3 workload を 1 枚に統合):

```
python plot_backoff.py figures/backoff_sweep \
    output/campaigns/backoff-sweep-silo-read-heavy-sweep-610004b9 \
    output/campaigns/backoff-sweep-silo-balanced-sweep-484c663e \
    output/campaigns/backoff-sweep-silo-write-heavy-sweep-493813a7
```

campaign を複数指定するとその順で横並び (workload 比較) になる。1 つだけ渡せば単独図。

## 出力

- `OUT_PREFIX.png` / `.pdf` — 図 (上段 throughput+95%CI・baseline、下段 abort%+IPC)
- `OUT_PREFIX.provenance.json` — 入力ファイルの SHA256・campaign id・スレッド数・env・
  各 workload の best/none/adapt 値。図の再現性記録。

## 設計上の約束

作法の全文は `FIGURE_CONVENTIONS.md` (図種に依存しない規約の本体)。本スクリプトはその backoff sweep 向け実装。

- **入力は WAL/dat のみ**。図の数値はすべてその場で再計算 (記憶・手写しなし)。
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
