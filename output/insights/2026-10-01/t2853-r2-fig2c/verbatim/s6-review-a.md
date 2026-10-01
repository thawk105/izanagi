must-fix・should-fix はありません。軽微な明確化を 1 件指摘します。

| ID | 重大度 | 根拠（path・値） | 修正案 |
|---|---|---|---|
| A-01 | nit | [README §4・§5.1](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/README.md:110) の「最大」「単調」は、採用範囲 **0〜900 µs** では正しい。ただし全29点では成立しない。原 read-heavy 最大は **README: 0 µs、10.248 ± 0.136 / 全29点の再計算: 1000 µs、10.274779 ± 0.140612 M tps**。また両 attempt・全 workload の abort rate は 900→1000 µs で増加する。[comparison.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/t2853-r2-fig2c/output/insights/2026-10-01/t2853-r2-fig2c/comparison.md:113) は1000 µsの除外を明記しており、計算誤りではない。 | 最大点表の導入と単調性の記述に「F718 除外後の 0〜900 µs」を明記する。 |

WAL の5反復から、平均と `2.7764451051977987 × 標本標準偏差 / √5` を独立計算しました。採用範囲の最大点は次のとおりで、README の6セルすべてが丸め後に一致します。

| workload | 原 attempt：最大点、平均 ± CI半幅（M tps） | R2：最大点、平均 ± CI半幅（M tps） |
|---|---|---|
| write-heavy | 6 µs、3.989635 ± 0.046238 | 8 µs、4.036174 ± 0.049731 |
| balanced | 2 µs、4.424343 ± 0.094238 | 2 µs、4.388117 ± 0.130673 |
| read-heavy | 0 µs、10.248284 ± 0.135569 | 0 µs、10.310146 ± 0.146434 |

## 総括

**GO — 静的レビューの範囲で、結果を覆す不一致はありません。**

| 照合項目 | 結果 |
|---|---|
| R2 の job・host・開始終了・完走 | **3/3 一致**。40679/bnode074、40680/bnode076、40681/bnode077。開始終了は `.stderr` の NQSV 会計と一致。 |
| Elapse | **3/3 一致**。3,658 + 3,594 + 3,584 = **10,836 s = 3.01 node 時間**。原 attempt は10,741 s、差95 s。 |
| source・CCBench・凍結 digest | 両 attempt の **6/6 job 一致**。`78c7a2c1408…`、`511c9538e4e…`、`c405c742f60e…`。job script のhashも原commitのblobと一致。 |
| campaign identity | preimage のdigest **6/6 一致**。原/R2間のpreimageも **3/3 完全一致**。 |
| 正しさ・commit | WAL **6本・930行**を集計。各 attempt **93/93 certified・serializable、anomaly 0**。全186 variantに build→verify→bench→commit が各1回あり、失敗・欠落なし。 |
| 対照表 | 0 µs・最大点・900 µsを含む **全174点**を再計算。平均・CI半幅・abort rate **522/522 値が表示桁まで一致**。DAT/WALの4指標も **696/696 一致**。 |
| 単調性 | 0〜900 µsでは、両 attempt のread-heavy throughputと全workloadのabort rateが厳密に減少。write-heavy・balancedも最大点以降は減少。 |
| provenance | 外部入力hash **原22/22、R2 22/22 一致**。生成器・依存・wrapper・表・両図のPNG/PDFも **8/8 一致**。描画系列はWALからの計算と **18/18 系列一致**。 |
| wrapper | 差し替えは §5.2 の列挙内。文言の置換回数チェックあり。受理条件・レイアウト・provenance検査の差し替えや迂回なし。 |
| §0・原図不変 | §0 は `0221383cf` から本文不変。commit時刻10:26:10は投入開始10:26:35より前。合成・再現精度評価・結果隠蔽なし。指定commit間で原図3ファイル・生成器・依存に差分なし。 |

親の brief の「5分分割を適用しない」「設計択一なし」は不適切な判断ですが、README §6で誤りとして明示されています。

未実施・独立に確認できない範囲は、描画・レイアウト検査・負例の再実行と、保存されていないtraceの再判定です。これらの実行結果は保存ログと静的コードで確認しました。書き込み・委任は行っていません。