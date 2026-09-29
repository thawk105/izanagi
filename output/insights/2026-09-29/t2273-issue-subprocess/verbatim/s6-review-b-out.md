## 所見

該当なし。差分は plan v2 の指定 2 file に収まり、要求された helper、等価性の番人、共通判定回数の番人を備える。commit message の profile 比率と実装・test の説明にも、静的に確認できる食い違いはない。

## 効果の見込み

従来の律速だった全文 regex search は、軸 literal がある場合、その出現位置の窓だけを調べる形になる。共通 literal の `in` も、同じ `search_repository` 内では `(literal, rel)` ごとに一度となる。profile の自己時間 2,311 sample と 806 sample を減らせる余地があるが、その合計を短縮量とは見なせない。

代わりに `_scan_one` の各呼出しで幅を再解析する。発行 child 約 13 回の `search_repository` × 3 回の `_scan_one` なら、memo hit を含め約 117 軸分の `sre_parse.parse` が走る。literal が頻出する長い text では `find` と窓 search が繰り返され、短い text や軸数が多い場合は `(literal, rel)` の key 生成・辞書照会も節約分を食いうる。

事前登録した単独再 profile の 70% 条件は、これらの費用を含む child 全体の改善を系列前に判定できる。隣接 3 対と land 区分は受入時間の判定に十分で、W₁・pre 等の補助量も W₀ から W_max への波及を読むのに適切。一度の profile による停止条件は保守的だが、裁定済みの計測設計を増やす根拠は見当たらない。

## 判定

**GO**（静的 review）。効果と land の可否は、事前登録どおりの実測で確定する。

## 総括

plan v2 を超える削除候補や欠落は見つからなかった。窓検索と共通判定の共有は律速行を直接狙っている。新しい反復・解析費用があるため、短縮率は再 profile と受入系列の結果に委ねる。