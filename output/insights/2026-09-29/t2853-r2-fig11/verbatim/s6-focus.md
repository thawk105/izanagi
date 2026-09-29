## 判定

**GO（修正の受入）。** 対象 commit `12cd17a2b` で、A-F1 と node 表示の問題は閉じています。B-F2 は受入費用の実測待ち、B-F3 は重複記述を残す判断として、未完了のまま明示します。静的再レビューであり、描画の再実行はしていません。

## 対応表

| 所見 | 判定 | 照合結果 |
|---|---|---|
| A-F1 | **closed** | [wrapper](/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/tools/t2853_r2_fig11_plot.py) は R2 描画・表の両経路へ固定 hash を渡す。入力から期待値を計算する旧経路は削除済み。定数 `0a6008d1…` と `7799a064…` は collect 原本の SHA-256 と一致し、[provenance](/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/figure/fig11_r2_a6_certification.provenance.json) の入力 hash・`authority_scope` も [insight](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/output/insights/2026-09-29/t2853-r2-fig11/README.md) §5.1 と一致。 |
| A-F2 | **closed** | R2 表は `policy 5; receipt 5`。reservation が hash で束縛する qstat に `bnode087`〜`bnode091` の **5 host** を確認。 |
| B-F1 | **closed** | 同じ node 表示の問題。元 attempt も表の `receipt 1` と割当て記録の **1 host** が一致。 |
| B-F2 | **partial** | §6 は 1.47 node 時間を実測、約 0.25 と合計約 1.72 を見積り込みと明記した。受入の実測値はまだ記載されていない。 |
| B-F3 | **partial** | §0 は維持し、§7 の重複も残る。§9 に受容判断が記録されており、今回の修正による回帰ではない。 |

## 新規所見

[insight §9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/output/insights/2026-09-29/t2853-r2-fig11/README.md) の「provenance の `authority_scope` と再現コマンドが変わった」は後半が原本と一致しません。旧版と新版の provenance を比較すると `reproduction` は同一です。変化したのは `authority_scope`、生成時刻、PDF の出力 hash です。記述を訂正するのが適切です。

## 照合したもの

- R2 の certification・raw manifest、wrapper、生成器の SHA-256。生成器 hash は記載の `aac63659…` と一致。
- reservation と allocation qstat の束縛 hash、および元 attempt・R2 の host 数。
- [旧版](/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/figure/superseded-v1/fig11_r2_a6_certification.png) と[新版](/work/1/SFC/tanab/izanagi-measurements/t2853-r2-fig11-20260929/figure/fig11_r2_a6_certification.png)の R2 PNG は双方 `7cf4e1a7…` で **bytes 一致**。control PNG も一致。PDF は前後で hash が異なるため、図の全形式が bytes 不変とは扱えません。
- 図・表・provenance の repo 内写しは repo 外原本と一致。旧新版 provenance では caption・`artist_series`・`reproduction` に差はありません。親の[実行ログ](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2853-r2-fig11/output/insights/2026-09-29/t2853-r2-fig11/verbatim/draw-r2-fix1.log) は control、R2 描画、表の成功と外部入力・repo 閉包検査の通過を記録しています。

## 総括

固定 hash と node 表示の修正に回帰は見つかりませんでした。親が記録を仕上げる際は、受入費用の実測値と、§9 の再現コマンドに関する一文を更新してください。