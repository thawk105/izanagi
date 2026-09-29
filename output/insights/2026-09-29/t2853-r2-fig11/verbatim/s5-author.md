## 作ったもの

[scratch/t2853_r2_fig11_plot.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig11-plot-author/scratch/t2853_r2_fig11_plot.py) を実装しました。SHA-256 は `1f94ca5d604a6e14755c50a796d61c3190a619c357e552889109a9698c6846a7` です。commit は作成していません。

## CLI と実走結果

以下はすべて元 attempt `a6-20260908b` の入力で実走しました。R2 側には同じ入力を見立てとして渡しています。出力は [scratch/out/](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2853-r2-fig11-plot-author/scratch/out/) にあります。

| CLI・検査 | 実走 command の要点 | rc・結果 |
|---|---|---|
| `control` | `python3.10 -B scratch/t2853_r2_fig11_plot.py --generator "$PWD/tools/plotting/plot_a2_certification.py" control --measurement-root <元root> --certification <元certification> --raw-manifest <元manifest> --reference-provenance <既存fig11 provenance> --out-prefix "$PWD/scratch/out/fig11_control"` | **0**。`artist_series` が既存 fig11 と完全一致 |
| `r2` | 同じ wrapper と `--generator` で `r2 --measurement-root <元root> --certification <元certification> --raw-manifest <元manifest> --attempt-label a6-r2-20260929a --original-attempt a6-20260908b --results-document output/insights/2026-09-29/t2853-r2-fig11/README.md --out-prefix "$PWD/scratch/out/fig11_r2_surrogate"` | **0**。control と `artist_series` が完全一致、caption は差し替わり、外部入力・repo 閉包検査とも通過 |
| provenance の `reproduction.argv` | 記録された argv と cwd をそのまま再実行 | **0**。`artist_series` 再一致、閉包検査通過 |
| `table` | `table --original-root <元root> --original-certification <元certification> --original-raw-manifest <元manifest> --r2-root <元root> --r2-certification <元certification> --r2-raw-manifest <元manifest> --out "$PWD/scratch/out/fig11_comparison.md"` | **0**。元・R2 を別々に読み込んだ表を生成 |

`<元root>` は `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a6-cert-20260902/a6-20260908b`、certification と manifest は指定された `2026-09-08_t2411-paper-story-a6-certification` 内の各ファイルです。stock の raw 5 標本から独立計算した中央値 `10088796.0` と t95 CI 半幅 `165646.18668188356` は表と一致し、`effects.rr95 = -0.057841193339621455` も certification と一致しました。`check_codex_agents.py` と `check_docs.py` はともに rc=0 です。テスト nodeid はなく、上記 CLI を実走しました。

## caption の差し替え一覧

各置換は出現回数を **1 回**と検査し、外れれば描画前に停止します。

- `formal certification attempt` を、元 attempt と別の R2 再現パッケージ試行を示す文言に変更。
- `This is one attempt of five samples per cell` の試行の位置づけを R2 用に変更。
- 限定 `(i)〜(v)` の参照先を「元 attempt の結果稿」と明記し、R2 insight の path を追加。
- B-10 の `historical concordance` を「元 attempt の結果稿での記述」と明記。

5 標本、中央値・効果・CI、正しさの別走、性能判定と一般化の限定、測定条件の説明は残しました。生成器の受理検査とレイアウト検査も変更していません。

## provenance の扱い

wrapper 内だけで生成器の `_caption` と `build_provenance` を差し替えました。同じ caption 置換が `validate_repo_closure` の再計算にも使われます。R2 の tracked 2 入力の `authority_scope` は、canonical pin ではなく **collect 後の bytes に対する自己計算 SHA-256** と記録します。生成器の SHA-256 は作業前後とも `aac636595ec0b211133edcc18bc1f72f984e346f58e7146da444396ea8d86448` でした。

## 未了・懸念

実際の R2 入力は未到着のため、R2 実データでの描画と表は**実装済み・未実走**です。見立て出力の測定 attempt ID は元 attempt のままであり、正式な R2 成果物には使えません。表の nodes は policy と、reservation に束縛された allocation qstat から読める範囲を示します。

静的検索で、この使い捨て wrapper を呼ぶ所有外 caller、共有 fixture、repo 内 consumer test は見つかりませんでした。新しい負例は作成していません。

## 総括

元 attempt を使った陽性対照、R2 見立て描画、再現 command、対照表の実走は完了しました。実 R2 入力が collect された後、同じ CLI をその入力で実行する必要があります。