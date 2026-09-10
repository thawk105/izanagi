# 段 4 裁定 — [T-337]/[T-479]/[T-318] 種別宣言

親裁定 2026-08-18 18:5x JST。段 2 プラン 1 本、段 3 敵対 2 レンズを受領し、親が実測で裏取りした。

## 親の実測 (裁定の根拠)

- **[T-318] の裁定文は D123 決定 (2) を名指ししている。**
  `docs/archive/worklog-phase3-0802-113-116.md` の (116):
  「producer ごとに `artifact_role` を宣言させ閉表で管理する。ファイル名列挙は **D123 決定 (2) 自身が
  弱点と自認しており**、新規 producer の更新漏れで静かに崩れる」。
- **[T-337] は T-318 の枠への適用先である。** 同 (121):
  「正例 artifact の適格性は新 D で権威境界を定義し `artifact_role=qualification` を **[T-318] 準拠で置く**。
  [T-318] で既に『producer に種別を宣言させ閉表で管理する』方向を採用済みであり、その枠へ乗せるのが一貫する」。
- **凍結 source pin の不一致は wave 前から存在する。**
  `output/s1-freeze/known_axes_freeze.json:206` の記録 `9b64f34bac37…67dbf4` に対し、
  現 checkout の `orchestrator/campaign/p3_s4_loop_sort.py` は `9a27a97ac271…89e3c`。
  検証 (`s1_known_axes_freeze.py:845-858`) は `source_resolver` 経由であり、テストは fixture resolver、
  `s8b_oracle_driver.py:469` は計測 root を渡す。**live working tree に束縛されていない。**
- **8c は `run_campaign` を通らない。** `p3_autonomous_workload_trial.py:2831` が
  `exploration_campaign_layout(campaign_id)` を直接呼ぶ。`--no-build` 時は
  `CampaignLayout(run_root/"campaigns"/campaign_id)` を直接構築する (D123 決定 (4) が型分離を別裁定へ送済み)。
- **`artifact_role` の production は 2 file。** `s8b_oracle_exploration.py` / `s8b_oracle_artifacts.py`。
  親 brief の「3 file」は test を数えた誤りで、訂正する。
- layout constructor の呼び手: `campaign_layout(` 76 hit / production 15 file、
  `exploration_campaign_layout(` 43 hit / production 8 file。読み取り経路を含むため constructor は絞り点でない。

## レンズ A の裁定

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| A1 | 必須引数化だけでは恒真になる | real | **部分採用**。宣言は権威ではない (D162 決定 (1))。防げるのは省略であって誤申告ではないと主張を縮小し、閉包 meta-test を宣言由来へ変える |
| A2 | `official` 自己申告が受理集合を広げる | real | **主張縮小で採用、追加実装は不採用**。D162 決定 (1) が「caller の自己申告は意味 gate でない」と既に条文化済みで、producer identity 束縛は本 wave の scope 外 |
| A3 | 旧 `campaign_namespace` 併存で迂回できる | real | **全面採用**。`campaign_namespace` を削除し `declared_use_class` へ一本化する。二重 selector を残さない |
| A4 | `qualification`/`dry` の受理拡大 | refuted | **採用**。負例は `ValueError` だけでなく cid と output directory の未生成まで固定する |
| A5 | 凍結 source pin が不変主張を破る | real (観測) | **閂としては refuted**。不一致は wave 前から存在し、検証は live tree に束縛されない。無処置、worklog へ実測記録 |
| A6 | campaign-id への漏洩なし | refuted | **採用**。既存 `test_campaign.py:8499-8521` を keyword 置換で維持 |
| A7 | 族は 5 でなく 6、8c が gate 外 | real | **採用**。8c にも宣言を付け閉包検査へ含める。ただし runtime gate は `run_campaign` 経路のみで、8c 直呼び経路の型分離は D123 決定 (4) の別裁定事項として残余に明記 |
| A8 | 親の数値は分母を明記しないと結論が変わる | real | **採用**。移行対象 = production 15 / test 30、族 = 6、`artifact_role` production = 2 file へ訂正 |
| A9 | 9 層は別 protocol の実体であり RF 実体ではない | real | **採用**。所在表を insights へ置き、RF 被覆と誤認しない注記を付ける |

## レンズ B の裁定

| # | 所見 | 判定 | 採否 |
|---|---|---|---|
| B1 | P1 は非同値な読み替えで、本 wave は実装せず裁定へ返すべき | **refuted** | 一次資料が P1 を支持する (上記実測)。T-318 の裁定文が D123 決定 (2) を名指ししている。**不採用** |
| B2 | D282 単独を D162 決定 (11) の解除権威にできない | real | **全面採用**。新 D の解除根拠は [T-479] の「実装 wave の新 D で確定」という委任とし、D282 は名前の実在証拠として引く |
| B3 | campaign-only なら D500 抵触は未成立 | refuted | **採用**。新 D・worklog に「RF producer 実装ではない」と明記する |
| B4 | 利用意図 / campaign path / RF 分類の関係を束ねる条文がない | real | **全面採用**。新 D に「宣言は利用意図であり、namespace はそこから導く非 identity の派生値」を条文化する |
| B5 | DW-G03 の独立 2 例がない | real (事実) | **停止根拠としては不採用**。DW-G03 は単発事故からの AI 自走一般化を禁じる gate であり、ユーザーが明示裁定した制度化 ([T-318] 択 (a)) には適用しない。独立 2 例が無い事実は worklog へ記録する |
| B6 | DW-G04 が real | 分離して採用 | campaign 宣言は条件付き機能ではなく、既存の live code path を fail-closed 化する変更である。RF 側は条件付き機能であり実装しない。brief の分離を新 D へ明記 |
| B7 | 実効性の主張が過大 | real | **全面採用**。「探索由来 campaign が official 受理集合へ入る経路を閉じる」を「宣言の省略による暗黙 official 配線を閉じる」へ縮小する |
| B8 | 数値の誤り | real | **採用** (A8 と同じ) |

## プラン v2 (実装する形)

1. `orchestrator/campaign/loop.py` の `run_campaign` から `campaign_namespace` を**削除**し、
   既定値なしの keyword-only 必須引数 `declared_use_class: str` へ**一本化**する (A3)。
   二つの selector を併存させない。
2. 閉表と処理: `official` → `campaign_layout`、`exploration` → `exploration_campaign_layout`、
   `qualification` / `dry` → `ValueError`。拒否は `ident.campaign_id` 計算と `layout.ensure()` より前。
3. 6 producer に module-level `DECLARED_USE_CLASS` を置く。8c (`p3_autonomous_workload_trial.py`) も含む。
   `run_campaign` を呼ぶ 5 本は `declared_use_class=DECLARED_USE_CLASS` を渡す。
4. 既存 official caller (`p2_2.py` / `backoff_repro.py` / `backoff_sweep.py` / `demo.py` /
   `s6_sort_sweep.py` / `s8a_trigger_sweep.py` / `sanity_silo.py` ほか production 15 本) は
   明示的に `declared_use_class="official"` を渡す。
5. 閉包 meta-test を**宣言由来**へ変える。`test_p3_exploration_namespace.py:39-47` の手書き
   `_DRIVERS` tuple と位置依存の `_CAMPAIGN_DRIVERS = _DRIVERS[:-1]` を、
   `orchestrator/campaign/` の production module を AST 走査して
   「campaign root を作る module は `DECLARED_USE_CLASS` を宣言する」を固定する形へ置換する。
6. `declared_use_class` を `CampaignConfig`・canonical preimage・campaign-id へ入れない。
   既存 `test_campaign.py:8499-8521` を keyword 置換で維持する。
7. `layout.py`・`s1_known_axes_freeze.py`・凍結 3 artifact には触れない。既存 5 producer の
   出力 root が変わらないことを runtime test で固定する。

## scope 外 (実装しない)

- RF/qualification の 9 層 (D162 決定 (10)、D500 決定 (1)(2)(3))。所在表のみ insights へ。
- producer identity 束縛による誤申告検出 (A2 の残余)。D162 決定 (1) が既に条文化済み。
- `artifact_role` (探索 oracle 文書種別) の改名 ([T-479] が (a) を不採用)。
- 8c の trial-local layout 型分離 (D123 決定 (4) が別裁定へ送済み)。
- 投入 gate / `PreregBinding` の解除 (D264/D292)。

## 変異事前登録 (DW-M01)

実効 gate へ照準した対。**wave 前の実コードの形 (既定値による暗黙 official) を第 1 対に必ず含める。**

| # | 壊す production 位置 | 期待して落ちる test |
|---|---|---|
| 1 | `loop.py` の `declared_use_class` に `= "official"` 既定値を戻す | 省略が `TypeError` になる負例テスト |
| 2 | `qualification` を許可へ倒す | qualification 拒否テスト (cid/dir 未生成込み) |
| 3 | `dry` を許可へ倒す | dry 拒否テスト (cid/dir 未生成込み) |
| 4 | 未知値の `ValueError` を握り潰す | 未知値拒否テスト |
| 5 | official mapping を exploration constructor へ倒す | official root 到達テスト |
| 6 | exploration mapping を official constructor へ倒す | exploration root 到達テスト |
| 7 | 拒否位置を `campaign_id` 計算より後ろへ移す | 拒否時に cid/dir が作られないテスト |
| 8 | 宣言を `CampaignConfig` / preimage へ混ぜる | campaign-id 不変テスト |
| 9〜13 | 5 producer の `DECLARED_USE_CLASS` を `"official"` へ倒す / 削除する | 各 producer の root 到達テストと閉包 meta-test |
| 14 | 8c の `DECLARED_USE_CLASS` を削除する | 閉包 meta-test |
| 15 | 閉包 meta-test の AST 走査を宣言由来から固定 tuple へ戻す | 新規 producer 検出テスト |

対の確定 (anchor 逐語と期待 node の完全集合) は実装後に `DW-M07` に従って再検証する。
