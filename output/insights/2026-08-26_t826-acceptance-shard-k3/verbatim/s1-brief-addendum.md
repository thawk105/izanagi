# 段 1 brief 追補 — 親の前提を覆す新事実 (段 4 で再裁定する)

段 2 plan の指摘を受けて親が裏取りした結果、`s1-brief.md` の (P1) と (P4) は**現 tip では
成立しない**。事実関係は次のとおり。

## 覆った事実

- 親が scope 1 に置いた「`real-repo` の単一 loadgroup を worker 直列化が要る node だけへ狭める」は、
  **本日 2026-08-26 13:19 の commit `5ac63895`「受入の real-repo 排他鎖を資源別 RW lock へ
  細分化する」で既に land 済み**である。
- `5ac63895` は親が引用した計測 tip `9463bcbc` の**祖先ではない** (`git merge-base --is-ancestor`
  rc=1) が、現 HEAD `b253e0b7` の祖先である (rc=0)。したがって a1k2 実走が測った
  排他鎖 222.68 秒は**この修正の前**の値であり、現 tip の律速ではない。
- 現在 loadgroup が残っているのは `REAL_REPO_PROCESS_MEMO_NODES` の 4 node だけで、
  台帳の所要は合計 0.00 秒である。`real-repo` の worker 直列鎖は事実上消えている。

## 現 tip で残っている律速 (台帳による算出。実測は baseline 計測で確定する)

| 機構 | 台帳 | a1k2 実測換算 (×1.87) | 状態 |
|---|---|---|---|
| `real-repo` worker 直列鎖 | 0.00 秒 / 4 node | ほぼ 0 秒 | `5ac63895` で解消済み |
| `s8c-preregistration-candidate` group | 83.5 秒 / 5 関数 | 156.2 秒 (a1k2 実測値) | **現行の最長鎖** |
| `s8c-predicate-snapshot` group | 52.0 秒 / 3 関数 | 64.3 秒 (a1k2 実測値) | 2 番目 |
| `dev-waves-runtime` group | 11.0 秒 / 12 node | 18.3 秒 (a1k2 実測値) | 小さい |
| shard あたり並列容量 `W_shard/48` | K=2 で 3937.1 秒 → 82.0 秒 | 187.1 秒 (a1k2 実測) | K で縮む |
| 残差 (wall − 最遅 worker) | — | 39.2〜84.6 秒 | K で縮まない |

`real-repo` の marker 自体は全 resource node に残っており (`conftest.py:1756-1757`)、
`tools/acceptance_shards.py` の `_canonical_item` は**marker** を読むので、
**16 file を 1 連結成分へ束ねる効果は現在も生きている**。よって
「K を 4 より上げても最大 shard 仕事量が 2174.1 秒 (台帳) で一定」という (P6) の算出は
現 tip でも成立する。

## 差し替える provisional 裁定

- **(P1')** worker 直列化の細分化は既に済んでいる。本 wave の残る scope は
  (a) shard affinity を group から分離して K の上限を上げること、
  (b) `s8c-preregistration-candidate` と `s8c-predicate-snapshot` に `5ac63895` と
  同型の細分化を適用すること、の 2 つである。(b) は [T-716] が
  「排他閉包の体系化は [T-826] (M0) の設計で一括判断する」として先送りした項目である。
- **(P4')** 期待利得は次の順で効く。K=3 では `W/(48*3)` が s8c 鎖 (156 秒) を下回るため、
  **K を上げるだけでは 156 秒 + 残差で頭打ちになる**。両方やって初めて
  `残差 + max(短縮後の鎖, W/(48K))` まで下がる。
- **(P7 新設)** `5ac63895` は受理集合を変えずに loadgroup を外した先例である。同じ手法が
  s8c 群へ転用できるかは、その群が守っている資源 (候補 commit の生成、HEAD snapshot) が
  reader/writer lock で表現できるかに依る。**転用可能性は未確認**であり、段 3 と段 4 で決める。

## 親が新たに取った計測

現 tip (= local main `b253e0b7`) で、実装ゼロのまま `IZANAGI_ACCEPTANCE_SHARDS` を
2 と 3 に切り替えた 2 走を投入した (計測として投入。受入 receipt は作らない)。
目的は (i) `5ac63895` 後の真の wall を確定すること、(ii) K=3 が現 regime で効くかを
実装前に確かめること (DW-G01 の生死実験)、(iii) 新しい鎖と残差を junit から測ること。
一次資料は `arm1-k2.log` / `arm2-k3.log` と shard session root。
