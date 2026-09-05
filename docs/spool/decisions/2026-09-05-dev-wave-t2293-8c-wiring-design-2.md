---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-05
wave: dev-wave-t2293-8c-wiring-design
seq: 2
---

## {{D:v8-two-layer-campaign-identity}}. V-8 (a) は論理 campaign と物理 campaign run の 2 層 identity で実行形を持たせる — 物理 identity は slot capability digest と query ordinal から決定的に導き、formal consumer は campaign.lock から再導出する

**決定 (設計、D1616 の解消案):** 8c 結線設計 §11 V-8 (a) 「1 query ordinal = 1 campaign run」の実行形を次で与える。
実装はしない。詳細は `docs/phase3-8c-wiring-design.md` の追記 (2026-09-05) 節。

1. **論理 campaign** (`binding.campaign_id` = `PreparedCampaignIdentity.campaign_id` = `OriginBindingCapability.campaign_id` =
   attempt slot の `campaign_id`) は 1 trial に 1 つの**座標**のまま変えない。capability は `campaign_id` を 1 つしか持たなくてよい。
2. **物理 campaign run** は query ordinal ごとに 1 つ (33)。`search_config["origin_campaign_run"] =
   {"attempt_capability_sha256": <AttemptSlotCapability.capability_digest_sha256>, "query_ordinal": q}` を足した cfg から
   `ident.campaign_id` で導き、`run_plan.members[q].planned_campaign_run_identity` を正本にする。claim / layout / WAL / `done` 集合が
   すべて q 別になる。時刻・PID・乱数を含まず、同一 slot への再入は同 identity (claim / resume gate で fail-closed)、
   別 attempt は別 identity。
3. 順序は capability 発行 → slot 予約 → 33 identity 導出 → envelope create-only → envelope digest の durable 束縛 → observation 開始 →
   executor。§8 の「run plan digest を capability へ束縛」は循環するため撤回し、参照は envelope → capability の一方向にする。
4. `execution-provenance` に `campaign_run_identity` を足し、FC03 の論理 3 項等式は残す。formal consumer は各物理 run の
   `campaign.lock` を decode して物理 identity と論理 campaign を再導出し、envelope を disk から再読し、WAL ref をその layout 配下に
   束縛する。provenance の文字列同士の比較を物理束縛としない。
5. origin topology mode は単一 layout 作成より前で分岐し generation loop に入らない。同一 process で捕捉した失敗だけ tombstone suffix、
   process crash は非終端 (§7.5)。
6. originless の bytes と受理集合は不変。t524 の attempt slot の `campaign_id` は論理値のまま、s8b (t1851) は変更 0。

**理由:**
- 33 行で変わるのは genome でなく trigger wire で、source 行と同 mask の validation 行は同 wire になるため、wire では識別できず
  ordinal だけが衝突しない。
- Pegasus (`allow_resume=False`) では同 identity の 2 run 目を claim より先に `_assert_resume_allowed` が拒否し、同 layout の WAL が
  `done` seed で同 variant を skip する。claim だけ通しても解消にならず、layout と WAL も分ける必要がある。
- D1190 (s8b) の同型 — 効果 key は座標、測定世代は run ごとに決定的 — を 8c に写すと「論理 campaign = 座標、物理 run = slot 世代 + q」
  になる。論理 cfg と q だけでは同 trial の別 attempt の 33 run が同 identity になり過去 WAL を流用できる (敵対レンズが実証)。
- `trial` 文字列の接尾辞は generic な `CampaignConfig.trial` 名前空間と構文分離できない。structured な `search_config` key は
  D75 (完全修飾) を満たし、completeness の origin 分岐はどちらの seam でも要るので費用は同じ。
- provenance の文字列比較だけでは §10 が却下した issuer 文字列型の恒真化で、別 trial の 33 WAL を流用し provenance だけ書き換えれば
  通る。`campaign.lock` は loop が実際に使った preimage を持つので、そこからの再導出が物理束縛になる。
- envelope は capability digest を含み、capability は envelope より前に発行されるため、双方向の digest 束縛は循環する。

**却下した選択肢:**
- claim に release / per-attempt key を足す — 拒否分岐の弱体化。
- identity に trigger wire を入れる — source 行と同 mask の validation 行で衝突する。
- `generations` を 33 にする — manifest は 2 を exact 要求し、generation は物理 run の単位ではない。
- 時刻・PID・乱数で identity を分ける — D1190 が却下した乱数発行と同型。
- 論理 cfg と q だけから物理 identity を作る (段 2 plan の案) — 別 attempt の流用穴。
- capability に 33 identity を足す / 33 capability を発行する — envelope との二重化、33 origin への分裂。
- FC03 の `execution_provenance.campaign_id` を物理値に置き換える — 3 項等式を崩し別 trial の流用穴を開ける。
- 「33 layout が実在する」だけで物理実行を認める — 事前登録が恒真になる。

**本決定が決めないもの:** envelope digest の durable な束縛先、origin cell の completion 権威、`execution-provenance` の schema 世代、
受理集合が動く 3 写像の確認 (裁定パッケージ R1〜R4)。ledger producer の状態機械・witness normalizer・material report renderer
(§9 の未存在層)。V-6 / V-9 / V-10。発行 3 条件 0/3 と結線実装 wave の起票制限は不変。
