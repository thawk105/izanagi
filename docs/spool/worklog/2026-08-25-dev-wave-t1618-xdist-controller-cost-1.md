---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1618-xdist-controller-cost
seq: 1
title: [T-1618] xdist controller の 2 経路を分離計測した。合わせて 3.9 秒で、61.3 秒の残差は説明できない (計測 harness + 記録、branch worktree-dev-wave-t1618-xdist-controller-cost、変異登録なし)
---

## 本文

- 依頼は「受入全走の未解明残余 61.3 秒について、controller の `worker_collection.index()` 線形探索と
  `_pending_of` 累積再走査が占める量を分離計測する measurement-first wave」。
  実測の全文は `output/insights/2026-08-24_t1618-xdist-controller-cost/RESULTS.md`。

- **結論: 問われた 2 経路は 61.3 秒を説明しない。** K=1 の実 production 順で
  (A) `index()` が 3.53 秒、(B) `_pending_of` が 0.38 秒、合わせて約 3.9 秒。(A) は (B) の約 9 倍。

- **親の主張が 3 件、子とレビューに反証された。** (1) 「D746 は比較を安くしうる」は段 3 の
  2 レンズが独立に数学的に反証した (比較 pair の集合は全順序対で順序不変)。
  さらに実測では **CPU が約 2 倍高くなる** (1.778 対 3.530 秒) ことが分かり、
  向きまで逆だった。(2) 「`tests_finished` は枯渇後に全 48 node を走査する」は誤りで、
  `pending >= 2` で short-circuit する。実測では全 worker 走査は **8 回だけ**。
  (3) 「61.3 秒の regime は完全に固定できる」も (B) については偽で、実 event 列は残っていない。

- **親の裁定そのものにも誤りが 2 件あり、段 6 レビューと実走が突いた。**
  (1) 採用した「失敗 pair の prefix 統計総和が順序不変」gate は**恒真**だった。
  全 unordered pair の総和なので no-op も任意 shuffle も誤った並べ替えも通す。
  gate をやめ数学的不変量として記録に落とした。(2) 「certification が 1 件でも失敗したら
  B 計測を開始しない」は粗すぎた。`certify()` には正しさ検証 (oracle 等価性) と
  採用判定 (occupancy 一致) が同居しており、後者の不一致で **K=1 の結果まで含めて
  成果物が全部消えた**。2 種類を分けた。

- **「61.3 秒は算術残差であって費目ではない」を段 3 の 2 レンズが独立に指摘した。**
  `229.41 − 12.86 − 155.3` のうち 155.3 秒は model 出力で、10% ずれれば残差は
  45.7 から 76.8 秒へ動く。裁定で成果物の枠組みを「占有率」から「regime 付きの絶対量」へ変えた。
  依頼された分離計測の scope は縮めていない。

- **段 6 の fix は 6 巡になった。`DW-O16` の 3 巡上限を超えた理由を裁定へ記録した。**
  NO-GO の反復ではなく、各巡は自分の対象を閉じて親が実走で検証しており、新しい欠陥は
  その巡で初めて可能になった実行で見つかっている。巡 3 の `/proc/<pid>/stat` の comm parse crash は
  「親が login node で pilot を実走できるようになって」初めて出た。巡 4 と 5 は
  「計算ノードへ実際に dispatch できるようになって」初めて出た。

- **子の pilot 成功は親の実走の代替にならない。** 巡 3 の crash は、引き金になる
  `(tmux: server)` 形式の process が子の実行時にたまたま居なかったため子の pilot では出なかった。
  親が実走して踏み、修理後は**同じ process が居る状態で**通ることまで確認した。

- **この機体では `PYTHONPATH` 一律拒否が構造的に成立しない。** oneAPI module が
  計算ノード側の環境に設定するため、投入シェルで `unset` しても届く (2 回の実測で確定)。
  guard を「pin された xdist の path と SHA-256 の直接照合 + 先行 `sys.path` の shadow 検査」へ
  置き換えた。**proxy より強い保証**であり緩和ではない。

- **本計測の投入は 6 回目で成功した。** 失敗の内訳は import path 欠陥 1、完走不能 1
  (fresh process 8,960 本が必要で deadline 内に終わらない)、`PYTHONPATH` 拒否 2、
  occupancy gate による全体停止 1。**完走不能の 1 回は job を qdel して計算ノードを解放した。**
  live な dispatcher を残したまま止めたので通常の失敗経路を通り、orphan hold は自動で消え
  F47 latch は武装しなかった。

- **occupancy の exact 一致は達成できず、許容幅は設けなかった。** group 割当は両 shard とも
  完全一致し median も近いが、48 件の完全一致には至らない。いま数値を通すために事後に幅を
  決めるのは正しさゲートを緩める方向なので、非採用のまま差分ごと記録した。

- **単独性は証明できなかった。** gen_S は Exclusive submit が OFF で、48 CPU の割当は
  専有の証拠にならない。`isolation_status = isolation-unverified`、`authoritative = false` を
  raw result 自身が自記する。

- **変異事前登録は行わなかった。** 実装面は `output/insights/` 配下の計測 harness だけで、
  `pytest.ini` の `testpaths` と `norecursedirs` により受入 collection に 1 件も入らない。
  受理集合は wave の前後で不変であり、変異の帰属先が無い。受入全走は免除していない。

- **子の工数 (receipt 実測):** codex 子 11 本。内訳は plan 1 / consult 2 / author 1 /
  review 3 / fix 6 のうち 1 本が未採用。fix round 6 の子は hook に `rm -rf` を拒否されて
  途中終了し `outcome=not_accepted` になったが、作業自体は完了していたので
  **親が gzip の lossless 性・summary の内容・pilot 回帰を独立に検証して採った。**

## 次の一手差分

### 完了

- [T-1618] 2 経路を分離計測し、61.3 秒を説明しないことを確定した。
  実測と限界は `output/insights/2026-08-24_t1618-xdist-controller-cost/RESULTS.md`。
  remaining: none
  base: 37808dc340c906247481b0d38938bbec4c1bda3dea9e1665c6bc07e7a97a0465

### 新規

- {{T:t1618-o1-index-causal-ab}} **P2・新規**: `worker_collection.index()` を O(1) の
  index map へ置き換える試作を作り、現行 K=2 の受入全走で wall の因果 AB を測る。
  本 wave の harness が機械生成した次の一手であり、K=2 の path A 集計
  1.570 秒 [1.559, 1.581] が事前 threshold 0.5 秒を上回ったことが起点。
  **CPU 秒から wall 秒へは渡れない**ので、削減量の主張は因果実験の結果だけに基づかせる。
  xdist は third-party なので、置き換えは upstream 改変ではなく本 repo 側の
  注入 seam で行えるかを先に確かめる。
- {{T:t1618-index-order-cost-mechanism}} **P3・新規**: 同一の slot probe 数
  (104,654,278) に対し collection 順で CPU が約 2 倍違う機序を特定する。
  候補は identity shortcut の配分、cache locality、分岐予測の 3 つ。
  D746 の所要降順が (A) を約 2 倍高くしている事実の説明であり、
  受入の順序方針を再検討する材料になる。
