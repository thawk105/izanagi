## 対応表

- **G1: closed。** `README.md:47`、`materials/reconstruction-log.md:124,143–148` は、数値列挙・epoch 範囲照合を `start_wall` に限定し、`reverse_recommendations` の値は「未検証」と明記している。生 stdout の検証範囲（`materials/reconstruction-stdout.txt:75–101`）と整合する。
- 両ファイルの `reverse_recommendations` 全7出現を確認。その他の出現（README:68、log:49,120,143）は語の走査・key 順の説明であり、値の不在断定は残っていない。

## 新規所見

無し。今回の限定修正に新しい過大は認めない。

## 総括

**GO。** G1 は閉じた。指定5資料の静的照合のみ実施し、追加実測・pytest・ファイル書込みは行っていない。