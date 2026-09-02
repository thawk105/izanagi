---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-02
wave: dev-wave-acceptance-overhead
seq: 1
title: 受入 collection の内訳を測った — 費用の 4 分の 1 が 1 file に集まり、conftest の hook は費用ではなかった (docs のみ、branch worktree-dev-wave-acceptance-overhead、実装面 0・Codex 枠切れで段 3 と段 5・6 は不成立)
---

## 本文

- ユーザー依頼は「受入全走の改善。計算ノードジョブ実行待ちはしょうがないと割り切る。並列化の余地、
  より賢い方法で全体を速くするアプローチ、不要なテストを棚卸しするなどして受入全走を改善してほしい」。

- **依頼の 3 軸はいずれも既裁定で閉じていた。** 並列化は D1287 / D1103 / D1019 / D820、
  テスト削除は D747、一時領域 I/O は 2026-08-29 の insight、排他閉包の細分化は D1035 と T-2097。
  段 1 の閉包で純増を探し、**D747 自身が「削除は collection 処理も減らす。これらは 15.1 秒に
  含まれておらず、安いテストを減らしても wall に効かないは未証明」と書いた穴**へ入った。

- **本 wave の数時間前に land した T-2097 の残差分解が、同じ量を計算ノードで既に測っていた。**
  残差 58.16 秒の 95% は「session 開始から最初の report まで」で、その大半が
  48 worker の全 collection (約 51.7 秒)。同 insight は **「worker 内部の import・conftest・
  fixture 収集・deselect の別は測っていない」**と明記しており、本 wave はその内側を測った。

- **最大の所見: 1 file が file collection 費用の 27.4% を占める。**
  warm collection 14.36 秒の走で 319 file の collector 所要を個別に測ると合計 12.54 秒 (全体の 87%)、
  うち `orchestrator/tests/test_p3_exploration_namespace.py` が単独で 3.44 秒だった。
  この module は `:70` の module 直下 setcomp で 187 個の source を `ast.walk` で全走査する。
  上位 10 file で 44.9%。**この費用は 48 worker × 3 shard + login、合わせて 145 回払われている。**

- **conftest の collection hook は費用ではないと実測で確定した。**
  `pytest_collection_modifyitems` が 0.375 秒、`pytest_collection_finish` (controller prewarm を含む)
  が 0.388 秒で、合わせて collection の 5% 未満。growth hold / flaky hold の完全性検査も
  shard の deselect も費用ではない。**ここを触っても速くならない。**

- **report 外費用は仕事量に依らない。** 同一 session の shard-1 と shard-2 は仕事量が
  中央値 1.38 倍 (p90 2.32 倍) 違うのに report 外費用の差は中央値 1.0 秒 (1.7%) で、
  仕事量比が大きい半分でも差は広がらなかった (n=401 session)。
  universe 件数との傾きは shard-1 が 4.68 秒 / 1000 件 (r=0.548)、shard-2 が 4.03 (r=0.485)。
  universe を 3 帯に切った帯内の前半後半差は 1.2〜2.0 秒で、**時期交絡では説明できない**。

- **D747 の穴の向きは支持されたが、大きさは観測範囲内でしか言えない。**
  1000 件あたり各 shard 4.0〜4.7 秒は、D747 の実行 work 側 (0.04 秒 / 1000 件) の約 100 倍である。
  ただし切片はすべて負で観測範囲は 15.5% しかなく、**「7750 件消せば約 46 秒」という外挿は無効**。
  親は一度これを書いてから撤回した。**結論は「テストを消せ」ではない** — D747 の却下理由
  (検出力を失う、規律 2) は有効で、費用が collection にあるなら 1 件も消さずに安くできる。

- **件数だけでは説明できない差を数で置いた。** T-2097 が並べた D711 の 12.86 秒 (14479 node) と
  55.73 秒 (19572 node) に本 wave の傾きを当てると、件数で説明できるのは約 24 秒で、
  実際の増加 43 秒との差 **約 19 秒**が残る。2 値は日付・機体・checkout が異なる対なので、
  **「超線形である」と断定できる対照は取っていない。**

- **Codex の使用枠が 2026-09-02 23:48 に尽きた (復帰は 2026-09-07 23:06)。**
  段 3 の敵対相談 2 本は 7 model call 時点で枠に当たり出力 0 byte、`f45_missing_output` で終了した。
  凍結境界により実装面は Codex 実装子だけが書けるため、**段 5・6 へ進まず docs-only で終えた**。
  従量経路への切替は行っていない。**本 wave の内容は独立した敵対検査を受けていない。**

- **親自身の誤りが 4 件出た。** (1) shard-0 固有分を異なる集合の中央値の差で「約 37 秒」と書いた
  (対にすると 23.5 秒、T-2097 の 21.9 秒と整合)。(2) 範囲外の外挿を書いて撤回した。
  (3) report 外費用を「テストが 1 件も動いていない時間」と書いたが、`worker_occupancy` は
  TestReport duration の和にすぎず lock 待ち・idle・scheduler gap を含まない
  (段 2 プランが指摘)。(4) 段 1 の閉包で D918 / D634 / T-2097 残差分解を引けていなかった。
  いずれも `output/insights/` の別名 artifact に入っており、値の文字列でも節名でも当たらなかった。

- 一次資料: `output/insights/2026-09-02_acceptance-collection-internals/README.md`
  (段 2 プランの逐語は同 `verbatim/`、cProfile の生出力と file 別所要も同 directory)。

## 次の一手差分

### 新規

- {{T:collection-prefilter}} **P2・新規**: `test_p3_exploration_namespace.py` の module 直下
  AST 全走査に字句 prefilter を置く。全 187 file の `ast.parse()` は残し、source text に
  対象 identifier が無い file で `ast.walk` を省く (該当 13 file)。単一 process で 3.44 秒のうち
  約 2.7 秒が上限。計算ノードの wall への効果は未測定。Codex 枠の復帰 (2026-09-07) 以降に着手する。

- {{T:collection-contention}} **P2・新規**: 計算ノードの collection 約 51.7 秒と、
  ログインノード単一 process の 12〜14 秒の約 3.6 倍の開きを分解する。48 並列の contention が
  CPU か Lustre metadata か memory 帯域かで、collection 短縮策の効果量が変わる。

- {{T:duration-ledger-compress}} **P3・新規**: duration ledger (19519 entry・2513728 bytes) を
  workerinput で圧縮する。現行は 48 worker へそのまま送っており shard あたり約 118 MB。
  圧縮すると約 19 MB。効果は worker bootstrap 側で 1〜5 秒と見積もられているが未測定。

- {{T:prewarm-overlap}} **P3・新規**: controller prewarm を背景化して worker の collection と
  重ねる。上限 22 秒程度だが通知のばらつきが小さければ 0 秒。`conftest.py` が T-2145 と
  編集面で衝突しているため、同 wave の決着まで着手できない。
