---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-10-01
wave: vhash-ro-novelty-sota
seq: 1
title: VHash の読み続ける read-only tx の前進 (主張 A) の新規性と比較相手を、性能結果の前に決めた。比較相手は精密 GC の系 (Steam 型と range-tracking 型) を Cicada に移したもので本案はその上に載せる。「大きく速い」は仮説、索引検索は A の検出 0・要裁定 20 (docs のみ、branch worktree-vhash-ro-novelty-sota)
---

## 本文

- 依頼: 並行 VHash wave の md_43 (`/work/1/SFC/tanab/tmp/vhash-2026-09-29/md_43.txt`)。一次資料 `output/insights/2026-09-30/vhash-ro-novelty-sota/README.md`、事前記述 `search-registration.md`
  (追加検索と性能結果 md_42 の前に commit `b9c429cc8` で凍結)、判定 `judgements.tsv`。設計の判断は {{D:vhash-ro-novelty-sota}}。md_42 の出力は開いていない。
- 段構成: 軽量版 (docs のみ)。段 2 は省略、段 3 相当として凍結前の事前記述を read-only の別系統モデル 2 本 (検索の網羅 / 判定基準の公正さ) に攻撃させ 14 件すべて採用。
  段 6 は read-only レビュー 1 本 (must-fix 3・should-fix 4、すべて real で反映) と、索引検索の結果を書いた後の焦点再レビュー 1 本。原典の抽出と OpenAlex 505 件の判定は Claude sonnet の読み取り役 (7 本)。
- 棄却・訂正: 段 6 レビューの反例 2 件を採用 — (1) 既読の版が前進先で見えるだけでは read-only tx の一貫性に足りない (不在を読んだキーへの挿入)、Cicada の read-only は read set を検証しない。
  (2) 「M 単独は精密 GC に構造上勝てない」は全称として誤り。親の最初の推奨は C を事前記述より狭く書いており、主条件と評価上の部分条件に分けた。
- 異常と逸脱: (1) arXiv の生死確認に件数取得用の `max_results=0` を使い、同じ HTTP 500 を 5 回 (2026-09-30 22:40〜10-01 00:00 JST) 索引の停止と読み、本走を 1 時間半止めた (`max_results=1` は 200)。
  事前記述の追記で訂正し、arXiv だけ先に本走した逸脱を記録した ({{F:vhash-index-liveness-probe-shape}})。(2) OpenAlex の匿名検索は 22:30〜00:14 に本当に 503 → 429 で、00:14 の 200 を確かめて本走した。
  (3) 凍結前の相談 1 本が原典テキストの非 NFC 文字で不受理 (F728 の再発)。(4) DIVA・OneShotGC は ACM が機械取得に 403 (EPFL は人間確認) で本文未確認。
  (5) ユーザーの指示 (2026-10-01 00:1x JST「ツールが使えなくなったから無限に待ちますは無しです」) により、索引の待ちと要裁定の本文探しに上限を置いた。
- 索引検索: 事前登録の R01〜R09 を OpenAlex (00:15〜00:19 JST)・arXiv (00:02〜00:03 JST)・DBLP (2026-09-28 20:23 GMT の全件書き出し) で完走。一意のレコードは OpenAlex 505・arXiv 46・DBLP 2、
  A の検出 0、要裁定 20 (OpenAlex 19・DBLP 1)。陽性対照 4 本はすべて期待どおりの式に出た。U1′ (R06) は 3 索引で検出 0・要裁定 0。
- 計算: 計算ノードは使っていない (DBLP の照合は login で約 80 分、メモリ上限 4 GiB)。

## 次の一手差分

### 新規

- {{T:vhash-ro-precise-gc-port}} **P2・新規**: VHash 論文の比較相手として、読み手を固定したまま必要な版だけ残す精密 GC を Cicada に移す (md_18 の区間 GC 試作 `patches/cicada-interval-gc-variant.patch` を土台に、更新されない版の列も掃除し、ro-gcflag 修正と組む)。
  強さの基準は Wei ほか PPoPP 2023 の range-tracking 型 (公開実装 Java)、DB の同系は Steam の EPO。移植で落とした機能を列挙する。根拠は一次資料 `output/insights/2026-09-30/vhash-ro-novelty-sota/README.md` §5.2・§7。
- {{T:vhash-ro-advance-phantom}} **P1・新規**: 読み続ける read-only tx の前進の確認に、不在を読んだキーへの挿入と範囲読み取りの条件を入れる (段 6 レビューの反例: 時刻 1 で不在を読み、時刻 2 の挿入の後に時刻 3 へ前進して読むと同じ tx が「無い」と「有る」を観測する)。
  Cicada の read-only は read set を検証しないので commit でも塞がれない。この条件が揃うまで主張 A の直列化可能を書かない。並行の md_44 (前進の成立条件) と重なるので、先に md_44 の一次資料を確かめる。
- {{T:vhash-ro-eval-main-comparison}} **P2・新規**: 評価計画に、主比較「精密 GC + M」対「精密 GC」(同じ Cicada・同時刻) と、効果が小さいときに主張 A を芯から外す判定規則を、結果の前に置く。
  主条件 C (読み続ける長い read-only tx) と評価上の部分条件 (開始のずれた複数の読み手 + 未読の範囲に集中する更新) を並べる。数値の閾値は評価計画で決める (一次資料 §5.5)。
- {{T:vhash-ro-retrieval}} **P3・新規 (人間の手番)**: 図書館経由の取り寄せ — OneShotGC (10.1145/3588699)、Hegner 2018 (Thalheim 記念論文集 pp.122–145)、主張 A の索引検索の要裁定 20 件の本文 (一次資料の `judgements.tsv` の `要裁定` 行)。
  DIVA は既存の取り寄せの項に含まれる。A について索引に基づく不在の文を書くには、要裁定を全件解く必要がある。
