# brief erratum 1 (2026-08-04、段 4)

brief.md は履歴として不変のまま残す。以下 3 点は brief の記述を本 erratum が上書きする。
正本は s4-adjudication.md。

1. **P1 (provisional) の根拠差し替え。** 「ユーザーの本 wave 起票 = U-A〜U-G 採用の意思表示と
   読む」という黙示推論は D147 却下案 (a) と同型であり破棄する。実際には
   `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-04-rulings-session-5rulings.md`
   (12:44 着弾) にユーザー明示裁定「５件は推奨通りで」があり、U-A〜U-G 全件が推奨どおり
   採用済み、「P3 実装 wave を再起票できる」も明記されている。結論は同じだが根拠が異なる。
2. **「全 root 削除への committed-bytes anchor」は過大。** 正しくは「committed authority
   anchor + missing-required-runtime fail-closed」。削除・未初期化・整合した再構築の区別、
   Git rollback・別 clone の検出は主張しない (プラン §11 の異議と レンズ A-3 を採用)。
3. **受入環境の訂正。** 「受入は login node」ではなく、login node から `tools/run_tests.py` で
   計算ノードへ dispatch する (AGENTS.md の規律。pytest を login node で直接走らせない)。
