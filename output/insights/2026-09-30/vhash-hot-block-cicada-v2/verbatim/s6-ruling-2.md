# 段 6 裁定 2 — 焦点再レビュー 1 (統合 3 = 69f7033dc) の判定 (date 実測 17:57:36 の後に起草)

焦点再レビュー `focus-r1.md`: A1・A2・A5・B1・B2・B4 closed、A3・A4 partial (= 新所見 F1・F2)、NO-GO。

| 所見 | real/refuted | 採否 | 裁定 |
|---|---|---|---|
| F1 (A3 partial) stale-gap の比較は先頭だけを見て、列の途中への挿入を見逃し changed を過少に数えうる | refuted (must-fix として) | 不採用、限界として記録 | **反例を否定する論証:** 検出力の主経路は ro tx の読み (validation が無く古い読みがそのまま commit する経路)。ro の trts = rts = (begin 時の MinWts) − 1 で、走行中の書き手の wts は MinWts 以上なので、比較の間に wts ≤ rts の版が列へ新しく入ることはない (stock の ro 安全性と同じ前提)。よって ro の読みでは比較の途中の挿入が答えを変えず、changed は正確。update tx の読みでは途中挿入で過少になりうるが、update の古い読みは validation (a) が止める経路で検出力の主張に使わない。一次資料では「changed は比較直後の stock 第 1 段との差で、update tx では下限」と書く。 |
| F2 (A4 partial) post-B1 が物理の直後を辿ると GC で切り離された版に届きうる | refuted (must-fix として) | 不採用、限界として記録 | **反例を否定する論証:** 最良設定は REUSE_VERSION=1 で、切り離された版は `reuse_version_from_gc_` に積まれ `delete` されない (pin の include/transaction.hh:185-189、:358-364)。よって解放済み memory の参照にはならない。再利用された版を返すこと自体は誤った読みで、壊しの目的 (判定器が誤りを検出するか) に反しない。ただし「1 つ古い確定版」という名は、選んだ版が GC の切り離し点のときに正確でない。md_23 の B1 も同じ性質を持つ (md_23 一次資料 §3.3 の T2 の orphan read の説明候補)。一次資料では B1 の意味をこの限界つきで書き、orphan read の数を併記する。 |

段 6 のレビューは F1・F2 を限界の記述へ回して閉じる (DW-O16 の 3 巡上限の内、1 巡で親が裁定)。コードは統合 3 = 69f7033dc で固定し、計測と変異へ進む。
