## 判定

**GO**。R2 の値、非合成の地位、図、測定 job の費用は一次資料と整合する。表と費用記述に局所的な修正を勧める。

## 所見

- **B-F1｜should-fix｜表の node 欄が取得可能な値を `receipt unknown` としている。** `figures/fig11_comparison.md:7` と wrapper `t2853_r2_fig11_plot.py:147-164` は R2 の receipt を読めていないが、一次資料の `jobs/rr95/scheduler/job.stderr` は `Number of Jobs: 5`、`submission-receipt.json` も 5 job と記録する。放置すると対照表だけが 5 node の裏付けを欠くように見える。**推奨:** 表の当該欄を「policy 5; NQSV 会計 5」に局所修正する。汎用 parser の追加は不要。

- **B-F2｜should-fix｜受入費用の実測先を予告しているが、現時点の worklog に実測値はない。** `README.md:148-149` は測定の実測 1.47 node 時間と受入の見積り 0.25 を合算し、「実測は worklog に書く」とする。指定された `docs/spool/worklog/2026-09-29-dev-wave-t2853-r2-fig11-1.md:13` も受入は見積りのままである。放置すると **1.72 node 時間を全 job の実測合計と誤読**し得る。**推奨:** 親の受入実測後に Elapse と合計を追記するか、1.72 は投入前の判定用見積りと明示して予告文を削る。

- **B-F3｜nit｜本題の結論が重複記述に埋もれる。** `README.md:10-39,41-50,93-97,99-118,120-143,146-158` で地位、非合成、値、図、費用の限定を繰り返している。放置しても値・表・図・地位は変わらないが、読者が一次結果へ到達しにくい。**推奨:** 投入前に固定した §0 と逐語資料は保持し、§7 は §0 と結果節への短い参照に圧縮する。成果物 SHA 一覧も必要な入力と図の hash を優先して示す。

## 照合したもの

依頼逐語、insight と図・表・verbatim、phase 行と worklog、R2 の事前登録・receipt・NQSV 会計、collect の certification／raw manifest、図原本・provenance・wrapper、元 attempt の tracked 成果物・結果稿・既存 fig11 provenance、生成器、fig8b 先例を静的に照合した。R2 図と表の写しは repo 外原本と bytes 一致。測定・テストの再実行はしていない。

## 総括

依頼範囲外の恒久 gate・台帳・一般化の追加は見当たらない。fig6 との checkout／出力先の分離と trace 保全口を使えない理由も insight から追える。修正は表の node 表示と費用の実測・見積りの区別に絞れる。