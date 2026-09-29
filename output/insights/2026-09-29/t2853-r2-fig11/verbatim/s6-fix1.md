## 直したもの

[scratch/t2853_r2_fig11_plot.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig11-plot-author/scratch/t2853_r2_fig11_plot.py) の SHA-256 は `f8582b5090e9958d344a4347363c228aa6507cc10f376c68d553a703137d31b1` です。

- `r2` と `table` の R2 入力に、wrapper 定数の certification hash `0a6008d175f0b4a13d952b98306621e717ecd8d07e00354e5914a205d550aed0` と raw-manifest hash `7799a0644effe5f89b932be201bba6b9c9ab879f44fbab786a274cd220653dfd` を渡すよう変更しました。`authority_scope` も wrapper 定数による collect 後の固定値と明記しました。
- `Execution Hosts` の同一行に並ぶ複数 host を数えられるようにしました。

## 実走結果

以下の全 CLI は `python3.10 -B scratch/t2853_r2_fig11_plot.py --generator "$PWD/tools/plotting/plot_a2_certification.py"` に続けて実行しました。元入力 root は `…/dev-wave-paper-story-a6-cert-20260902/a6-20260908b`、R2 root は同じ親の `a6-r2-20260929a`、R2 の certification と raw-manifest は指定の `…/t2853-r2-fig11-20260929/collect-root/output/insights/2026-09-08_t2411-paper-story-a6-certification/` 内です。

| command | rc | 確認結果 |
|---|---:|---|
| `control --measurement-root <元root> --certification <元certification> --raw-manifest <元manifest> --reference-provenance "$PWD/docs/paper-story/figures/fig11_a6_certification_reject.provenance.json" --out-prefix "$PWD/scratch/out/fig11_control"` | 0 | 既存 fig11 と `artist_series` 完全一致 |
| `r2 --measurement-root <R2 root> --certification <R2 certification> --raw-manifest <R2 manifest> --attempt-label a6-r2-20260929a --original-attempt a6-20260908b --results-document output/insights/2026-09-29/t2853-r2-fig11/README.md --out-prefix "$PWD/scratch/out/fig11_r2_actual"` | 0 | provenance の入力 SHA-256 が両定数と一致。外部入力・repo 閉包検査も通過 |
| R2 provenance の `reproduction.argv` を記録された `cwd` でそのまま再実行 | 0 | 再実行前後の `artist_series` 完全一致 |
| `table --original-root <元root> --original-certification <元certification> --original-raw-manifest <元manifest> --r2-root <R2 root> --r2-certification <R2 certification> --r2-raw-manifest <R2 manifest> --out "$PWD/scratch/out/fig11_comparison.md"` | 0 | 元 attempt は `policy 1; receipt 1`、R2 は `policy 5; receipt 5` |
| 上記 `r2` に元 root・元 certification・元 manifest を渡し、出力先を `fig11_r2_rejected` に変更 | 2 | `[error] FigureDataError: certification canonical SHA-256 mismatch`。PNG・PDF・provenance はいずれも未作成 |

出力は [scratch/out/](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig11-plot-author/scratch/out/) にあります。`python3 tools/check_codex_agents.py` と `python3 tools/check_docs.py` も各 rc=0 でした。

## 変えていないもの

caption の 4 箇所の差し替えと出現回数検査、control、閉包検査、reproduction の動作は変更していません。生成器の SHA-256 は前後とも `aac636595ec0b211133edcc18bc1f72f984e346f58e7146da444396ea8d86448` です。生成器・docs・他のソースファイルは編集せず、commit も作成していません。

## 未了・懸念

ありません。実走により `scratch/out/` の既存出力は更新され、R2 実入力の出力が追加されています。

## 総括

指定の 2 点を修正し、R2 実入力は描画でき、固定 hash と異なる入力は図を作る前に拒否されることを確認しました。