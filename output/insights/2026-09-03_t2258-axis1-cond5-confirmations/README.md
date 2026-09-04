authority: none
default_effect: no-state-change

# [T-2258] 軸 1 条件 5 — D1331 の 3 確認の証拠 sidecar (2026-09-03)

分析結果の正本は `docs/related-work/claim-survey/2026-09-03b-axis1-cond5-confirmations.md` である。
本 sidecar は可変状態を持たず、そこから参照される逐語証拠だけを置く。

## 何のための材料か

D1331 が要求した 3 確認 — (a) 返却されなかった別 ID が実在するか、(b) 連続 2 走で集合が安定するか、
(c) 索引側の snapshot drift があるか — を軸 1 について測った、その逐語である。
D1564 はこの 3 確認を完了させ、結果を持って条件 4 と条件 5 の改訂範囲を決めよと定めている。

## 身元

| 項目 | 値 |
|---|---|
| 入力 commit | `39086303b5c36a9e5523dc9f3e9480678a2b2f35` |
| 登録 epoch | `AX1-20260902-E1` |
| 登録 commit | `4ec3eba04354f9ba86117a2dd488c72d007045e6` |
| run ID | `t2090-openalex-20260903` |
| 生証拠 bundle | `/work/1/SFC/tanab/axis1-bundles/2026-09-03-t2090-openalex/bundle` |
| bundle manifest SHA-256 | `ff25f09af3840d35b4bc3cb36c0fa8b9df283f0cce055c6c117b71707832e9ca` |
| catalog | `docs/related-work/claim-survey/2026-09-02-axis1-search-catalog.json` |
| catalog SHA-256 | `8e23d63a799c8ab9d25151012c34bc738dbb422ac3dfb237999c359137c816ab` |
| **新規 HTTP** | **0 件** (無償枠の窓を 1 つも使っていない) |

**取得は 1 件も行っていない。**材料は 2026-09-03 の走行が残した凍結 bundle だけで、
そこに 14 run / 93 頁の生応答が保存されている (`Q1` と `Q2` は attempt 2 本ぶん)。

## file inventory

| file | 由来 |
|---|---|
| `verbatim/probe-src.md` | 親が書いた repo 外の使い捨て probe 7 本の逐語ソース |
| `verbatim/measure-premise.md` | leaf ごとの rows / distinct / 申告総数 / 重複内訳と、attempt 間の集合差 |
| `verbatim/measure-mech.md` | 頁ごとの first / last / next_cursor、境界重複の位置、差分 ID の素性 |
| `verbatim/measure-digest.md` | production の `primary_key_digest` 定義の再現と独立再走の一致検査 |
| `verbatim/measure-boundary.md` | 申告総数の到達可能性と、非返却 record の境界位置 |
| `verbatim/measure-tuple.md` | 境界重複 record の三つ組比較と、2 走間の `relevance_score` 差分 |
| `verbatim/measure-chain.md` | page evidence の field による走の連続性・独立性検査 |
| `verbatim/measure-crosscheck.md` | 凍結実行記録・checkpoint・catalog との照合と、条件 5 の現在の状態 |
| `manifest.json` / `MANIFEST.sha256` | 上記 8 file の path・bytes・SHA-256 の束縛 |

**probe は `.py` のまま repo へ置かない** — 逐語は `.md` へ貼る。
**HTTP 応答本文の全文は保存しない** (`output/README.md` の規則)。
ここに載るのは集計値と、名指しした少数の work ID だけである。

## probe が production の経路を測っていることの裏取り

- **ID 抽出:** production の `parse_openalex_page` は `results` の全要素の `id` を順に occurrence 化し、
  申告総数に `meta.count` を使う。probe は同じ母集合を同じ順で取る。
- **数値:** probe が出した rows / distinct / 頁境界重複は、
  凍結実行記録 `2026-09-03-axis1-search-execution.md` §3 の表と 4 leaf 全件で一致した
  (`measure-crosscheck.md` §1 が実際に照合している)。
- **digest:** probe が再現した `primary_key_digest`
  (`sorted(set(work_ids))` を改行で連結した SHA-256) は、
  bundle の checkpoint 8 件に production が書いた値と全件一致した
  (`measure-crosscheck.md` §2)。
- **走の連続性:** `measure-chain.md` のとおり、14 run 全件が page evidence の束縛を通った。
- **catalog の件数:** `measure-crosscheck.md` §3 が
  OpenAlex 80 論理 query (leaf 78 + aggregate 2)、`independent_pass_required` 真 76 / 偽 4、
  未走 leaf 66 を数えている。§4 は現在 条件 5 が不成立の leaf を 3 件と判定している。

## 限界 — ここから言えないこと

- **単一機序は立証していない。** 欠落した走のその時点における当該 ID の索引側スコアも、
  全頁に共通する snapshot 識別子も証拠に無く、新規取得でも過去時点は復元できない。
- **登録された独立第 2 走の digest 不一致は観測していない。**
  `independent_pass_required` が真の leaf は 1 本も pass 2 を走らせていない。
- **「1 頁 leaf なら gap 0」は保証ではない。** 言えるのは
  「この bundle の 7 run で `declared − distinct == 0` だった」までである。
- **`declared − distinct` (逐語では `gap`) を非返却件数と読んではならない** (正本文書 §2.3)。
- **cursor の境界規則は否定できていない。** 否定できたのは
  「cursor 位置の record が内容を変えずにそのまま再送される」という説明までで、
  境界重複 32 件のうち 23 件は前頁の cursor 鍵が指す record 自身である。
  なお `measure-tuple.md` の初版はこの一致件数を 0 と誤って出していた
  (cursor の二重包装を親の probe が剥がしきれていなかった)。段 6 のレビューが発見し、直して測り直した。

## 関連

- 正本 = `docs/related-work/claim-survey/2026-09-03b-axis1-cond5-confirmations.md`
- 凍結実行記録 = `docs/related-work/claim-survey/2026-09-03-axis1-search-execution.md`
- 既裁定 = D1331 / D1564
