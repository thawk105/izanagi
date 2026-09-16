## 1. 実測による到達可能性の主張は強すぎる

**real / scope 内（brief の根拠修正）。** 根拠：`brief-t559.md:54–61`、`verbatim-F108.md:3–22`、`verbatim-D155.md:24–30`。

親の 6 件が示すのは、**CLI 終了後の wrapper 観測に全標本帯内の列が存在した**ことまで。新 gate が読む benchmark 直後の `static_post` が通った証拠ではない。生データは射影に含まれず、親の集計自体も独立検証できない。

F108 の 23 件は重複除去した**標本列数**、親の 7 件は **attempt 数**であり、単位が違う。識別子・取得日時・対応表がないため、包含・重複・独立性は不明。「計算ノードでの因果は未立証」は「計算ノードでは再現していない」を意味しない。なお後者の断定は、提示された brief 本文にはない。

したがって、次回 job が benchmark を全部走らせてから新 gate で落ちる確率は推定できない。`0/6` を失敗確率とすることも、F108 の `23/23` から必ず落ちるとすることも不当。「self 通過かつ新 gate のみ失敗の歴史的実例は 0 件」も、親が調べた範囲に限定すべきである。

## 2. 入力形の恒偽化と、標本列の逆転による見逃し

**疑わしい / scope 内（plan 自体の射影は正しい）。** 根拠：`stage2-plan.md:13–25,131–136`、`execution_guard.py:324–405,414–444`。

clock 全体を渡す、または射影済み expected／observed をそのまま交換すると、key 数が合わず常に拒否する。reason 単独では帯外と区別できないが、予定の sidecar により区別できる。

- shape 不正：`input_valid=False`、`out_of_band_count=None`。
- 正常入力の帯外：`input_valid=True`、`policy_matches=True`、`band_pass=False`。
- policy 不一致：帯内でも `policy_matches=False` により拒否。

区別を検証しない負例は、入力を壊した恒偽実装でも成功してしまう。主要負例では reason に加え、上記の帯外診断と違反位置を確認する必要がある。

**key 形を維持して標本列だけ逆転する場合は見逃す。** plan の主要負例では post の中央値も 2101。逆転すると正常な pre 全標本だけを検査するため通る。expected の全標本を帯検査する述語ではないためである。予定の spy は記録だけでなく、expected が dynamic pre、observed が post と一致することを assert する条件が必要。

## 3. 負例の中央値・帯は成立する

**real / scope 内（検算結果は plan を支持）。** 根拠：`stage2-plan.md:108–125`、`execution_guard.py:405–416`、`cli.py:515–519`。

凍結 pre をソートすると、第24・25要素はいずれも 2101。偶数個の中央値も `(2101+2101)/2 = 2101` となる。

- 許容差：`2101 × 0.02 = 42.02 MHz`。
- 帯：`2058.98–2143.02 MHz`。pre の 2110 は帯内。
- post の 3079.456 は中央値から `978.456 MHz ≈ 46.571%`、上限から `936.436 MHz` 超過。

policy が 2.0 のままで他の fixture 条件を維持すれば、early／late self と既存 static 比較は通り、新 gate だけが拒否する。位置 0・24・47 のいずれでも成立する。

## 4. reason 保存と early 拒否の受理集合

**疑わしい / scope 内（静的検査では破壊経路なし）。** 根拠：`cli.py:893–905,1014–1035,1108–1113`、`report.py:121–128`、`test_calibrator_certify.py:972–1013`、`stage2-plan.md:89,135,140`。

plan どおり末尾に append すれば、順序は既存品質 reason → 既存 self reason → 新 reason。消去・上書き・統合はない。CV との複合負例は、`["within-run-cv-invalid", "effective-clock-post-comparison-failed"]` の順序まで検証できる。

既存の benchmark 中 policy 変更テストは self reason の**包含**検査なので、新 reason の追加で期待値は壊れない。publish 直前の変更テストも既存 reason を保持する。

early の未評価一覧は拒否決定後に診断へコピーされるだけで、受理判定には使われない。新検査名の追加は拒否成果物の記述を変えるが、early の受理集合や self-only 拒否の特例を変えない。

## 5. policy 窓は緩まないが、sidecar の再計算主張には不足がある

**real / scope 内。** 根拠：`cli.py:637–651,877–882,1044–1054`、`execution_guard.py:381–388`、`stage2-plan.md:78–83,125`。

新 gate は凍結 tolerance と呼出時の policy を照合する。既存 late self と publish 直前の三者一致検査を残すため、新たな再束縛の受理窓は開かない。ただし新 gate も一時点の検査であり、policy の変更履歴を保証しない。

一方、**「sidecar だけから canonical 判定を再計算できる」は一般には成立しない。** 既存テストのように開始時 2.0 → benchmark 中 3.0 と変わると、全標本 2101 でも拒否する。予定の sidecar は expected の 2.0 と `policy_matches=False` を残すが、照合した current policy 値を残さない。後日 policy 2.0 で再実行すると通ってしまう。

scope 内の条件として、既存 sidecar に照合時 policy 値も記録して再計算条件を明示するか、再計算可能性の主張を帯計算・hash に限定する必要がある。新しい gate や canonical 改訂は不要。

## 6. 「publish 前照合」は満たすが、継続安定性は保証しない

**real / scope 外（継続監視の不在）。** 根拠：`verbatim-T559-entry944.md:1`、`cli.py:991–1008,1067`、`brief-t559.md:28–30`。

裁定の「凍結した事前状態と事後の観測値を公表前に照合」は満たす。次の限定を明記すれば名乗りは妥当であり、今回の実装条件として scope 拡張は不要。

> benchmark 中に帯外へ振れて post 観測までに戻った変動は検出しない。
> post 観測後から publish まで、またその後のクロック安定性は保証しない。
> probe の観測者効果を除去せず、観測値が benchmark 中の動作クロックを代表することも保証しない。

## 総括

- 親の wrapper 観測は、新 gate の実環境通過実績でも次回 job の成功確率の根拠でもない。主張を限定する。
- 主要負例は数値的に成立する。入力逆転と shape 不正を区別する assertion を具体化する。
- policy 変更時は sidecar の入力だけでは判定を再現できない。照合時 policy の記録か、再計算主張の限定が必要。

**判定：条件付き。** 上記を plan に反映すれば実装してよい。静的検査のみで、pytest は実行していない。