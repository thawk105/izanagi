# 段 4 裁定の追補 — [T-615] の同梱

基準 commit: 8e42a564 (local main a9159bac を取り込んだ merge)。

## なぜ追補が要るか

段 4 の裁定を確定し、実装・レビュー・fix・変異 (9/9 KILLED) まで終えたあと、受入全走の直前に
local main を再確認したところ、**新しいユーザー裁定 [T-615] が「稼働中の [T-529] 実装 wave へ
同梱」と指定していた**ことが判明した (worklog エントリ (286) 相当、commit `be5e4d83`)。

裁定逐語:

> [T-615] = (a) 歴史世代解決。凍結済み floor protocol
> (`output/s8b-freeze/floor_protocol.json`) の検証は、現在 contract との比較でなく
> `resolve_by_contract_sha256` の歴史世代解決で行う — T-529 裁定 (3)
> 「fuse 解除の前に履歴解決を consumer へ配線」の consumer 配線そのもの。
> 凍結 bytes は書き換えない。protocol 世代の別発行 ((b)) と活性化保留 ((c)) は不採用。

これは段 4 時点で未見の新事実であり、かつ scope を**広げる**方向のユーザー裁定である。
`DW-S04` に従い親が不採用にはせず、同梱して実装する。

## 親が独立に裏取りした緊張点

`s8b_floor_contract.validate_protocol` は `contract_sha256_lookup` を**注入**される設計で
(`s8b_floor_contract.py:105-152`)、注入元は production に 2 つある。

| 注入元 | 現状 | 判定 |
|---|---|---|
| `s8b_ratified_freeze.py:2803-2837` | 呼出側から `contract_resolver` を必須注入し、live は current・再検証は historical を渡す | **既に配線済み** |
| `s8b_floor_campaign.py:308-324` | callback が `_env_contract.lookup(env_tag)` を直接呼ぶため常に current | **残る 1 件** |

**単純に historical へ置換してはならない。** 残る 1 件は producer・凍結 artifact 検証・
live admission の 3 用途を兼ねており、全体を historical 化すると
「現在 active でない較正で新しい実測を走らせる」ことを許す。これは D202 が read-only 入口へ
限定した理由そのもの (`decisions.md:9772-9792`) であり、D213 が floor campaign の resume を
current に固定した理由 (`decisions.md:10089-10098`) にも反する。

## 裁定 — 追加する実装単位 (単位 2)

`s8b_floor_campaign.py:308-324` を **2 lane へ分離する**。

1. **凍結 artifact の read-only 意味検証 = historical。** 記録 `contract_sha256` を
   `resolve_by_contract_sha256(recorded, expected_env_tag=env_tag)` で**一度だけ**解決する。
   unknown / ambiguous / cross-env / 不正返却で current へ fallback しない。
   公開 `validate_protocol(document)` はこちらへ束縛する。切替 flag を公開面へ足さない。
2. **producer・fresh run・resume = current。** 用途が明白な private 関数を設け、
   `lookup(env_tag)` と記録 hash の一致を要求し、解決した current contract object を返す。
   builder (`:440`)、発行直後 read-back (`:582`)、live admission (`:2750-2764`) をこちらへ移す。
   `:2755` の二度目の `lookup` は削除し、同一 object を calibration / receipt 全辺へ渡す。
3. **historical 検証済み dict を実行権限 token にしない。** CLI (`:3482-3489`) は
   load 後に historical で artifact を検証し、その後 `run_campaign` 内で current admission を
   **必ず再実行**する二段構成にする。

- **成果物影響 (`DW-G05`):** certified 選択結果・レポート・試行台帳の値、受理集合、
  contract hash 参照、凍結 bytes は**今日は 1 つも変わらない** — registry が 1 env あたり
  1 世代しかないため historical 解決と current 解決は同じ contract を返す (親の実測)。
  実装しない場合、g2 を活性化した時点で凍結済み floor protocol の受理集合が空になり、
  [T-419] (iv) と [T-529] の手前で止まる。
- **やらないこと:** 凍結 bytes の書き換え、`FROZEN_MANIFEST` 期待値の変更、
  `s8b_floor_contract.py` / `env_contract.py` / `s8b_ratified_freeze.py` の変更 (既存 seam で足りる)、
  fuse 除去・g2 登録・activation record / receipt。

## 変異事前登録 (追加分、`DW-M01`)

| # | 位置 | 変異 | 期待 |
|---|---|---|---|
| M9 | historical lane の resolver | `resolve_by_contract_sha256` を `lookup` に戻す | KILLED |
| M10 | historical lane の拒否 | unknown / cross-env の拒否を恒真 pass にする | KILLED |
| M11 | live admission | current admission を historical resolver に替える | KILLED |

過剰拒否検出の正例は「current が変わらない通常系で fresh run と resume が従来どおり進む」
既存試験の維持で担う。

## 手続き上の記録

段 4 の本体裁定・実装・レビュー・fix・変異 (run 1 erratum + run 2 で 9/9 KILLED) は
**単位 1 の証拠として有効なまま残す**。単位 2 の追加後に変異と受入を再走し、両単位を含む
最終状態で確定する。
