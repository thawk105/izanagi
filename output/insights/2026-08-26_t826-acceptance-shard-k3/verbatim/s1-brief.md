# 段 1 brief — 受入全走の高速化 (real-repo 排他閉包の細分化 + shard 数の引き上げ)

## scope

受入全走の **pytest wall** を短縮する。手段は D532 が認める 3 つのうち (a) 排他鎖の短縮と
(b) 排他閉包の細分化に限る。テストの削除・skip・選択の縮小は規律 2 により検討対象外。

1. `real-repo` の単一 `xdist_group` を、既に存在する資源別 SH/EX flock を実効排他として、
   **worker 直列化を要する node だけ**へ狭める。
2. `tools/acceptance_shards.py` の `allocate()` が拒否する `shard_count` 上限 (現行 {2,3}) を
   引き上げ、分散ジョブ化を可能にする。
3. D358 (2026-08-13、排他機構の変更で速くする路線を閉じる) を、現 regime の実測で再裁定する。

## 確定済みユーザー裁定

- 計算 job の queue 待ちは所要目標から除外する (前 wave 1001 と同じ扱い)。目標は
  pytest wall と job Elapse。
- 並列化・ボトルネック改善・分散ジョブ化を進める。

## 不変条件 (破ったら赤)

- 受理集合を 1 node も変えない。選択 node 数・collection 集合・恒久除外・保留は不変。
- 実 repo (親 / CCBench submodule) への同時書込みと、書込み中の読取りを一切許さない。
- 受入形の判定 (`_is_acceptance_run` 等 4 gate) と受入 receipt の argv 契約を変えない。
- 分割不変性 (T-813/T-826): 分割の取り方で静かに消えるテストが出てはならない。

## 成果物影響 (DW-G05)

本 wave の scope は成果物 (certified 選択・材料レポート・試行台帳) の値・受理集合・参照を
**変えないことが要件**である。逆向きに書く: 排他が緩めば real repo を触るテストが偽緑/偽赤になり、
受入が守っている受理集合の意味が失われる。よって全 scope 項目の must 条件は「受理集合不変」で、
所要短縮はその制約下でのみ採る。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 排他の実体は既に `_real_repo_locks` の資源別 SH/EX flock にあり、`xdist_group("real-repo")`
  はその上に載る粗い第二防壁である。よって reader から loadgroup を外しても排他は保たれる。
- **(P2)** flock は `/tmp` = host local なので、shard (= 計算 job = host) を跨ぐと協調しない。
  したがって real-repo の全 resource node は **同一 shard に留める affinity** が要る。
  現行はそれを `_components()` の file↔group union が偶然担っている。affinity と worker 直列化を
  別概念へ分離する必要がある。
- **(P3)** D358 の反証 2 件は解消済み: optional index lock は [T-991] (entry 524) で
  2 経路とも `GIT_OPTIONAL_LOCKS=0` 化され、閉包は `_REAL_REPO_NODE_INVENTORY` (92 node) と
  重なり/完全性 gate で確定した。残る `silo_ladder_rung1.py` の 2 箇所は受入から到達しない
  (entry 524 の申告) — **要裏取り**。
- **(P4)** 期待利得: 鎖 222.7 秒 → 最長単体 42.8 秒。K=2 のままなら wall 307 → 約 272 秒 (11%) に
  留まり、K=4 と併せて初めて約 170 秒 (45%) になる。**片方だけでは D358 の「利得が無い」を
  再現する。** 両方を 1 wave で採る。
- **(P5)** 残差 (wall − 最遅 worker) 39.2〜84.6 秒 = 固定費 (D532 (c)) は本 wave の scope 外とし、
  次の一手へ送る。K を上げても縮まないため、鎖を割った後の支配項になる。
- **(P6)** K の上限は real-repo 連結成分 (16 file / 2534 node / 台帳 2174.1 秒) が決め、
  K=4 以上で最大 shard 仕事量が一定になる。よって上限は 4 で足り、それ以上は成分の分割 =
  cross-host lock を要するので scope 外。

## 成果物の形

コード + テスト (実装子)、変異事前登録と matrix、受入全走 1 回、insights の逐語、
worklog / decisions の fragment。D358 の改訂は decisions fragment で行う。

## 並列分割方針

段 2 は plan 1 本。段 3 は 2 レンズ (sol / luna) を並列。段 5 は実装子 1 本 (編集面が
conftest と acceptance_shards の 2 file に集中し所有が割れないため)。段 6 は review 2 本並列。

## 受入・実測の環境

受入全走は `tools/dev_wave_wait.py acceptance` 経由で Pegasus の計算ノードへ dispatch する
(D724 の Pegasus LOGIN 受入形、既定 `IZANAGI_ACCEPTANCE_SHARDS` 有効)。所要は job Elapse と
pytest wall を分けて記録し、外側 wall を所要としない (D713)。
