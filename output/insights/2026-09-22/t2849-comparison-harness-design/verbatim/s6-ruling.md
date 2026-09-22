# 段 6 裁定 — read-only review (`s6-review.md`、09:38〜09:43:14、NO-GO、must 4 / should 3) への親の判定

親が根拠行を確認した (p3_s4_loop.py:1418-1424 の whiteboard 値域、b5_generator_contrast.py:796-807 / :815-836 の whiteboard 生成と endpoint 不在時の分岐、known_axes_freeze.json:540-549 の read-heavy flags)。

| ID | 判定 | 採否 | 直し方 |
|---|---|---|---|
| R1 LLM への拒否履歴・初期点の射影 | real | 採用 | whiteboard は 5 field と値域 (success / fail / rejected) を変えず、iteration を提出機会 a の順にして、投入前の拒否 (A だけ) を rejected、投入後の失敗 (B) を fail、certified・品質正常を success とする。初期点は whiteboard に入れず、planner / coder 入力の閉じた兄弟 key (v・結果分類・fitness の 3 つ) で渡す。B-5 の継承照合 (iteration == b の連続) は本基盤では a の連続へ変わる。すべて実装単位 4 に含める |
| R2 endpoint 不在時の fallback と品質欠測の衝突 | real | 採用 | B-5 の実装どおりに分ける: endpoint 不在で自系列に品質欠測・機械欠測があれば score 欠測、候補起因の失敗 (anomaly・Tier0・build) だけなら block stock の fallback、再計測の anomaly は fallback、再計測の品質欠測・機械欠測は score 欠測、stock 不成立は判定不能 |
| R3 進化の支持集合と失敗点 | real | 採用 | 表を「許容領域は S1 全体、各提案は親の近傍 (ln v_親 ± λ) に限られ全域到達を保証しない」に直す。進化は失敗点を使わない (親は certified・品質正常の点だけから選び、失敗した子は親を置き換えないだけ)。失敗点の除外集合を持つのは BO だけ |
| R4 `p2_2_flag_opt` を測る経路 | real | 採用 | 実装単位に「明示した参照 genome を stock と同じ共通の検証・計測経路で測る入口」を足す (今の stock / 候補経路は BACK_OFF=1 固定)。read-heavy の flags を列挙する |
| R5 K0 と K2 の差 | real | 採用 | 「役割の並びと還流を揃える。coder の role と proposal 契約は K2 版と通常版で違うので、差は知識射影だけではない」と直す |
| R6 検索範囲の限定 | real | 採用 | 要約・fragment・MOCC 節の不在の断定を「指定範囲の検索では未発見」「確認した package のうち」「参照した記録では」に揃える |
| R7 参照先・量化の不整合 | real | 採用 | D2214 の節番号を「D2214 の設計 insight §x」へ、(μ+λ) の算術に条件 (μ = 4・λ = 4・B = 8 の例) を戻す、R0 の文を「自系列の履歴に加えて渡す初期情報は」へ、「非 LLM の 3 手法」を 4 手法へ、第 31 回裁定に控えの path を付ける |

refuted 0 件。fix は docs だけなので親が直す (実装面の差分ゼロ)。直した後、焦点再レビュー 1 本 (DW-O16 の closed / partial / regressed 表) を投げる。
