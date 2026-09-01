---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-01
wave: dev-wave-t1942-floor-gate-recheck
seq: 2
---

## {{D:floor-official-transport-seam-conflict}}. 床値 official は staged transport が不適格 seam である限り起動できないと確定し、解消案を裁定へ返す

**決定:** 床値 campaign の official 走行は、現行 main では起動できない。D926 が定めた
承認束縛を実装しても起動できない。したがって承認束縛の実装を行わず、解消案をユーザー裁定へ返す。

確定した機構は次のとおりである。

- `tools/pegasus/floor_campaign.sh` は driver へ `--fetchcontent-base-dir` を無条件で渡す。
- `fetchcontent_base_dir` は `REFREEZE_DISQUALIFYING_SEAM_NAMES` の 18 名の一員である
  (`orchestrator/campaign/s8b_floor_contract.py`)。
- official mode は非既定 seam があれば承認 gate の**手前**で拒否する
  (`orchestrator/campaign/s8b_floor_campaign.py`)。
- `_derive_refreeze_eligibility` は official・fresh・非既定 seam ゼロだけを適格にする。

副次的な帰結として、**正規 job script を通る走行は pilot でも `eligible_for_refreeze` に
なれない**。D811 が pilot 値の発効を禁じた事実と整合するが、禁止の根拠は裁定だけでなく
機構にも存在する。

**理由:**

- `DW-G04` は「条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を書ける場合だけ
  実装する。書けなければ設計メモに留める」と定める。official の発火経路を書けない以上、
  承認束縛の実装は発火しない条件付き機能になる。
- 18 名集合と `_derive_refreeze_eligibility` の判定式は D926 が明示的に「変更しない」と
  名指ししている。ここを緩める解は絶対規律 2 に反する。
- 段 2 プラン、段 3 の敵対レンズ 2 本、親の独立実測が、いずれも同じ矛盾を独立に指摘した。

**却下した選択肢:**

- **18 名集合か判定式を変える** — D926 が禁止し、正しさ防壁を緩める。
- **承認束縛だけ先に実装して矛盾は後続 wave へ送る** — 発火経路の無い条件付き機能を
  main へ入れることになり、`DW-G04` に反する。実装が「official は解禁済み」と誤読される。
- **staged transport を argv から外して既定経路で投入する** — 既定経路は FetchContent の
  外部取得を試みる形であり、計算ノードは直結 network 不可である。手順書は依存ソースを
  ログインノードで pinned staging して渡す運用の維持を定めている。実測なしに採らない。

**ユーザーへ返す解消案 (親の推奨は 1):**

1. staged transport を driver 内部の production 既定にする。payload の所在を caller seam でなく
   driver 側で導出できれば、18 名集合も判定式も literal には変えずに解ける。
   設計論点は「発見による暗黙の入力経路を作らないこと」である。
2. 既定経路が計算ノードの offline 条件で通るかを実測し、通れば argv から外す。
3. 18 名集合か判定式を変える。**規律 2 に反するため親は推奨しない。**

## {{D:floor-fresh-claim-authority}}. 床値 fresh 予約の可否は世代 scope の claim で決まり、旧 marker と試行登録簿では決まらない

**決定:** 床値走行が cell を claim できるかを判定するとき、権威は
`measurement-generation-claims/` の path 衝突である。旧 `claims/` と旧 `consumed/`、および
`floor-attempt-registries/` の残枠を判定根拠にしない。

- fresh reservation は旧 effect-key claim を明示的に無視する。
- claim identity は 6 項目の cell effect key に加え、`observation_role` と `campaign_run_id` から
  導かれる世代 digest を含む。新しい `campaign_run_id` は別 identity になる。
- 試行登録簿は scheduler recovery が retry を開く場合だけ読まれ、
  `max_consumptions_per_budget_key` もその replay 内でだけ検査される。
- read-only の観測が言えるのは「ある時点で identity 衝突がない」までである。実際の claim は
  resume marker の全件検査、逐次の排他作成、ledger 全体検証を経て初めて確定する。
  最初の試行消費はさらに現行世代の consumed 全体を claim・両 ledger と再照合する。

**理由:**

- 親は当初、旧 `consumed/` 228 件と試行登録簿の残枠を判定対象と読んでいた。段 3 の敵対レンズが
  コードで反証し、親が独立に裏を取った。**判定対象を誤ると、無関係な歴史 marker を理由に
  走行を誤停止するか、現行世代の衝突を検査し損なう。**
- 現存する試行登録簿は holdout key が実物と異なり、`process_identity.execution_uuid` が
  fixture 値である。さらに現行 consumer の canonical path と階層が違う。
  **テスト由来の成果物を運用判定の根拠にしていた。**

**却下した選択肢:**

- **旧 marker を判定対象に残す** — 現行の予約経路が参照しない。
- **試行登録簿の残枠を予算根拠にする** — recovery replay 限定の機構であり、
  通常の fresh 走行では発火しない。

## {{D:floor-budget-approval-is-post-run}}. 床値の予算承認は走行の前提ではなく、結果を freeze へ昇格させる段の閂である

**決定:** `output/s8b-freeze-budget-approvals/g1.json` の人間承認は、床値 official 走行の
前提条件ではない。走行結果を v2 candidate freeze へ昇格させる段の前提条件である。
D1161 の「official 経路」は「official 結果の freeze 昇格までを含む経路」と限定解釈する。

**理由:**

- 唯一の production consumer は v2 g1 candidate builder であり、**official 走行の結果 path を
  入力に取る**。campaign 側からも投入器からもこの consumer への呼出しは無い。
- D589 も承認 artifact・pin・official result 不在を candidate 生成の三条件として並べており、
  こちらが実装と一致する。

**却下した選択肢:**

- **承認不在を投入前 blocker として扱う** — 実装と一致しない。走行前に承認を完成させようとする
  誘因を生み、AI が承認者になれないという境界を空洞化させる。

**不変のまま残すこと:** AI に許されるのは非承認の skeleton 起草と read-only 検証までであり、
canonical candidate と pin の確定はユーザー手番である。
