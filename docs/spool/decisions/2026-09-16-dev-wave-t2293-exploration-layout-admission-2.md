---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2293-exploration-layout-admission
seq: 2
---

## {{D:origin-evidence-issuer-admits-exploration-layout}}. 起点試行の証拠発行器は探索 layout を identity 同一性で受理し、維持する拒否述語を負例で固定する

**決定:** `reflux_result_evidence` の証拠発行器 (`issue_campaign_result_evidence` と、公開 projection 入口が
通る `_ordered_attempt_materials`) の layout 受理集合を、`CampaignLayout` だけから
`CampaignLayout` または `ExplorationCampaignLayout` へ広げる (D2044 項 2 の実装)。判定は
`type(layout) is not CampaignLayout and type(layout) is not ExplorationCampaignLayout` の identity 同一性とし、
`isinstance` にも tuple 所属 (`type(layout) not in (A, B)`) にも落とさない。

同時に、維持する拒否述語を負例で固定する。両型の subclass、metaclass の `__eq__` が対象型と等しいと答える別型、
`root` / `wal_file` を持つ duck typed object、`str` / `Path` / `None` は型 gate で拒否し、exact な探索 layout でも
physical campaign root が evidence root の外なら `_context_roots` の既存包含検査で拒否する。負例は発行入口と
projection 入口の両方に置き、いずれも有効な exact layout で実 WAL を先に作って layout object だけを置き換える。

受理を広げるのは layout の型だけである。record schema (`result-evidence/v1`、`execution-provenance/v2`) と既存入力に
対する生成規則、`_context_roots` の包含検査、create-only 書き込み、検疫・auditor veto・condition gate は変えない。
D2017 の名乗りの上限 (唯一 writer 性は運用前提) も変えない。official と探索で出力 bytes が同一とは主張しない
(physical root が違えば content ref の path・projection・record bytes は違う)。

**理由:**
- `loop.run_campaign` は `declared_use_class="exploration"` で `ExplorationCampaignLayout` を作り、起点試行 driver も
  探索 layout で走る。発行器が `CampaignLayout` しか受理しないままでは起点試行の record が 1 件も発行されない
  (前 wave の結線障害 B1)。consumer 側 (D1747) は `exploration_campaign_layout(...)` で root を計算するので、
  producer が探索 layout を受理して初めて producer の physical root と consumer の計算 root が同じ族になる。
- tuple 所属は `is` または `==` で判定するため、metaclass の `__eq__` を持つ別型が通る。exact-type 規律を保つには
  identity 比較でなければならない (段 3 の相談が指摘し、親が最小再現で確認した)。
- 変異で単一理由性を確かめた。発行入口だけを緩めても内側 gate が同じ入力を拒否するので、緩和変異は projection
  直呼び (内側 gate だけを通る経路) の負例で観測する。

**却下した選択肢:**
- `type(layout) not in (CampaignLayout, ExplorationCampaignLayout)` — tuple 所属の等価比較で impostor が通る。
- `isinstance` / 属性検査 — subclass や duck typed object を受理し、exact-type 規律を破る。
- 探索 layout を `CampaignLayout` の subclass にする、または共通基底を切る — D123 (4) が別裁定へ送った型分離の
  境界を動かす。本件は受理集合の変更だけで足りる。
- Q2〜Q4 (台帳遷移・起点専用 entry point・完了判定) を同時に実装する — D1875 の順序裁定と抵触する。
