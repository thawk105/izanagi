# 親が現物で実測した事実 (段 4 裁定の基礎。base = cc9bba523)

## 凍結範囲と hash

- `#### 5.1.1 分析契約の一括凍結 (D1082)` = 312 行、`## 6. 実走の前提条件…` = 597 行。
- したがって `_locate_section()` が切り出す凍結範囲は **312–596 行**。
- `sed -n '312,596p' <doc> | sha256sum` =
  `0ceab4cd064eb8ff6c5dba22364fff04a6d708de8acb9d9cde52115f0891df30`
  → `PREREGISTRATION_SECTION_5_1_1_SHA256` と exact 一致。**編集後に同じ 1 行で再検算できる。**
- 文書全体の sha256 = `2a29f2faabca0c09e76686d2cbc64b930c1c8480f1f0cbc614a4ccec27293b30`。
  repo 全体を grep して pin 0 件。**whole-file pin は無い。**

## 逐語アンカー (すべて実在を確認済み)

- 215 行: `**その artifact path と sha256 を値として書けるとき**だけである (§6 の前提条件も参照)。`
- 262 行: `実際の開始時刻は実走成果物側に別途記録し、**本欄を後から実測値へ書き換えない。**`
- 680 行: `不都合な campaign を別 root へ出す、report 前に止める、台帳に載せない経路が残る。`
- 887 行: `- file-drawer の機械強制 (manifest・append-only registry・完全性 consumer)。`
- 997 行: `上表が割り当てた決定主体は変えない。他の 11 項目についてはここでは何も述べない。`
- 1002 行: `区別する。**本節は測定を許可も要求もしない。** 案の側は、ユーザーが裁定するまで発効しない。`

## (a) の裏取り

`orchestrator/campaign/p3_b4_analysis_path.py:67-73` の `_SOURCE_CLOSURE_PATHS` は 5 member。
現在の sha256 は §5 の primary outcome 値セルに書かれた 5 値と **順序も値も exact 一致**する。

- `p3_b4_analysis_contract.py` = `528ee2fa5795bf36fcd966bed47efb025b24a070c8c4e4303c8615957893d2a3`
- `p3_b4_analysis_adapter.py` = `cf056566a7bc2c23b0a5af14a537450fe4d160b042eda9df26fd41ad200cc0b6`
- `p3_b4_analysis_ledgers.py` = `71393e8d3ffc60e8af3421c1caf80abc1cf2395551173d96524b724ab5785cda`
- `p3_b4_analysis_path.py` = `eeb397fcf8cfebf454bdacc00af9943010b53b59c6cf64dcdded0acf3217ea86`
- `p3_b4_analysis_prereg_consumer.py` = `fe3aeb804fc09733434c8974500bba9f46cbd942e39bd33b2c6063134d96b31a`

→ 「本 wave の記入を維持する」は base 時点で事実として支持される。

## (T-2414) 算術の裏取り

`orchestrator/campaign/floor_pair_driver.py:1428-1441` が pair-sample ごとに次を exact 要求する。

- `len(sample_sessions) == 2` かつ side_id 集合 == `("candidate_1", "candidate_2")`
- 各 session の `len(measurements) == 2`
- `len(sample_measurements) == 4`
- role == "reference" の測定数 == `REFERENCE_MEASUREMENTS_PER_PAIR_SAMPLE` == **2**
- 各 session の role 集合 == `("candidate", "reference")`

→ 1 pair-sample = 2 session = 4 測定 (candidate 2 + reference 2)。
→ 1 セル・n=62・2 campaign = 124 pair-sample = **248 session = 496 測定
  (candidate 248 + reference 248)**。
→ 起草時の名目単位 (1 測定 = 5 反復 x 3 秒 = 15 秒) を引き継ぐと **7,440 秒 (約 124 分)**。
→ 起草時: candidate 248 測定 = 3,720 秒、reference 124 測定 = 1,860 秒、合計 5,580 秒。
  **candidate 側 3,720 秒は変わらない。reference 側が 1,860 → 3,720 秒になり、
  かつ別セッションではなく候補と同じ 248 session の中に入る。**

## (d) の裏取り

- `orchestrator/campaign/p3_b4_analysis_ledgers.py` は実在。module docstring 1 行目
  "B-4 scheduled registry, analysis manifest, and assignment schedule."
  定数 `B4_SCHEDULED_REGISTRY_SCHEMA_VERSION` / `B4_ANALYSIS_MANIFEST_SCHEMA_VERSION` /
  `B4_MANIFEST_COMPLETENESS_SCHEMA_VERSION` が実在。
  violation は "One append-only protocol-violation event" として chained row で積む。
- `orchestrator/campaign/p3_b4_prerun_issuer.py` が `ledgers.assert_analysis_manifest_complete` を
  2 か所で呼ぶ。
- **同 module 自身が閉じないと宣言している (逐語):**
  "The scheduled registry can only be sealed from one issuer-bound batch receipt.
  That receipt binds the complete normalized batch, but this module does not create
  or identify the authoritative producer. Consequently it does not claim to close
  the file-drawer risk while that producer is absent."
- `output/` 配下を schema version 文字列で grep した hit は
  `output/insights/*/mutation-*-report.json` の**変異走行レポートだけ**で、
  権威ある producer が発行した manifest / registry の実体は 1 件も無い。

→ 陳腐化しているのは「機構が存在しない」だけ。結論「file-drawer は開いている」はなお真。
