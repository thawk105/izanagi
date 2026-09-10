# 段 4 裁定 — [T-2293] V-8 (a) の identity / capability 衝突の解消案

親が段 2 plan と段 3 の 2 レンズ (A = 整合・実効性、B = 正しさ境界・恒真化) を real / refuted で裁定し、設計 (plan v2) を確定する。
検査対象 HEAD は `97ee3cd3a` (plan・レンズの時点)。裁定時点の local main は `b152eec77` (D1644〜D1649、本件に無関係、設計文書は不変) で、docs 編集前に ff で取り込んだ。
裁定 inbox の再走査: wave 開始後に V-6 / V-7 / V-9 / V-10 の新裁定は無い。V-8 (D1616) だけが裁定済み。

## 1. 所見の裁定

| # | 出所 | 所見 | 裁定 | 根拠・処置 |
|---|---|---|---|---|
| 1 | B blocker 3 | 物理 identity が論理 cfg と q だけから決まり、slot / attempt / prereg 世代を含まない。同 trial の過去 attempt の 33 run が同じ planned identity になり流用できる (偽装 (c)) | **real / 採用 (設計変更)** | D1190 の正しい同型は「座標 + sealed attempt slot 世代 + q → 物理 identity」。物理成分に `AttemptSlotCapability.capability_digest_sha256` を入れる。同一 slot への再入は同 identity (claim / resume で fail-closed)、別 attempt は別 identity |
| 2 | B blocker 5 | `trial` 文字列接尾辞は generic `CampaignConfig.trial` 名前空間と構文分離されず、一意性証明が 8c workload 集合内でしか成立しない | **real / 採用 (設計変更)** | 物理成分は `trial` でなく `search_config["origin_campaign_run"]` (exact 2 key: `attempt_capability_sha256`, `query_ordinal`) に置く。structured かつ domain-separated (D75)。completeness の origin 分岐はどちらの seam でも必要 (`autonomous_trial_completeness.py:840-893` が exact key 集合と素の trial を要求) なので費用は同じ。plan の却下案 (d) を覆す |
| 3 | B blocker 1、B must-fix 1 | FC03 に足す物理 identity 比較が provenance の自己申告値同士の比較で、§10 が却下した issuer 文字列型の恒真化。completeness で lock を再読しても formal terminal は先に commit 済み | **real / 採用 (設計要件)** | formal consumer 自身が各物理 run の `campaign.lock` を content-addressed ref (§3.7) 経由で decode し、preimage から物理 identity を再計算して planned 値と、物理成分を除いた論理 cfg から `capability.campaign_id` を再導出して比較する。WAL ref はその layout 配下に束縛する。completeness は再確認に限る |
| 4 | B blocker 2、A blocker F2 | envelope は capability digest を含むが、capability / launch admission / lifecycle は envelope digest を含まない (hash cycle)。consumer は in-memory envelope を検査し disk の create-only file を再読しない | **real / 採用 (設計要件 + 裁定 R1)** | 一方向参照 (envelope → capability) で固定し、envelope digest の durable な束縛先を R1 で裁定する。consumer は evidence root の `origin/recovery-envelope.json` を再読し digest 一致を要求する。§8 の「capability へ束縛」は循環のため撤回し「lifecycle (R1) へ束縛」に改める |
| 5 | B blocker 6 | envelope の現行 write は `begin_attempt_observation()` より後。observation 開始後・envelope 作成前の crash で事前登録済み bytes が無い | **real / 採用 (設計要件)** | 順序を「slot 予約 → 33 identity 導出 → envelope create-only → digest 束縛 → observation 開始 → executor」に固定する |
| 6 | B blocker 4 | q 別 claim / layout、native WAL shape、origin report 形は上位写像の受理集合を広げるのに裁定へ返していない | **refuted (blocker として) / real (記載義務として)** | 述語は不変で、写像 cfg→identity が変わるのは D1616 (a) が命じた結果そのもの。native WAL shape の修理は D1555 が「provisioning と独立に必要」と明記。origin report 形は §6.5 の originless 不変規律の内側。設計文書に「受理集合が動く 3 写像」の表を置き、確認項目 R4 として裁定パッケージへ添える |
| 7 | A blocker F1 / F3 / F4 / F5 | ledger producer (reserve〜seal の FSM)、`drive_iteration` の origin 専用入口、単一 campaign 前提の report / completeness / Layer 3 / registry acceptance、qualifying rejection → witness class の変換が無い | **real / scope 外 (§9・§12 の既知残余)** | いずれも本文書 §9 が「未存在」と列挙した層 (physical writer、witness normalizer、formal consumer 入力、renderer)。本 wave は identity 衝突の解消だけを設計する。ただし executor の分岐点 (単一 layout 作成 `p3_autonomous_workload_trial.py:3804` より前)、trigger module の origin 専用 sealed entry point、origin cell の completion 権威 (R2) を §12 の受入要件と裁定パッケージに足す |
| 8 | A must-fix F6 | `trial_registry.py` の acceptance issuer は `cells[0].campaign_root` を必須にするので「変更 0 file・t524 と semantic overlap 0」は誤り | **real / 採用 (訂正)** | 実装 wave は `trial_registry.py` の report / measurement-target 部分を origin-aware にする。t524 着地後に着手し、attempt registry 部分は不変 |
| 9 | A must-fix F7 | reservation と `max_wall_s` が 33 run の実行時間を保護しない (既定 3600 s、33 × 374〜908 s = 3.4〜8.3 h) | **real / 採用 (設計要件)** | preflight の `ReservationCheck` を保持し、各 q の前に次 member の保守的上限で `ensure_remaining()` を検査、不足なら以降を tombstone suffix にする。`max_wall_s` の既定は origin mode で別値にする |
| 10 | A must-fix F8 | 「crash を tombstone 化」は過大。process crash で seal を失えば非終端 (§7.5) | **real / 採用 (表現訂正)** | 「同一 process で捕捉した失敗」だけ tombstone suffix、process crash は §7.5 どおり非終端と書き分ける |
| 11 | A must-fix F9 | registry 照合と capability 発行に論理 cfg を渡す保証が呼出し順だけに依存 | **real / 採用 (設計要件)** | 「registry / capability の再導出は物理成分を足す前の exact `PreparedCampaignIdentity` だけを受ける」を受入要件と負例にする |
| 12 | A must-fix F10 | completeness に `campaign_runs` を拒否する exact cell key gate は無い。拒否点は単一 root・素の trial・2 generations・Layer 3 chain | **real / 採用 (訂正)** | 存在しない gate の更新と書かず、新設 `_CAMPAIGN_RUN_KEYS` と semantic gate 4 点を個別に列挙する |
| 13 | A must-fix F11 | A6「identity が違えば protocol digest も違う」は `spec_slug` が preimage に無いので一般則として偽 | **real / 採用 (親 brief 訂正)** | 一般則と P1 固有則を分ける。33 cfg は slug / search_tag が同じなので short identity の相異から full digest の相異が従う |
| 14 | A / B 共通 | `execution-provenance` の schema 世代: plan は v1 in-place、A は v2 | **real / 裁定 R3** | 親推奨は v2 (同じ schema 名が異なる exact key 集合を表す先例を作らない。attempt registry v1→v3 と同じ運び) |
| 15 | B | V-10 (writer trust) は未裁定なので「残る択一 0 件」は誤り | **real / 採用 (訂正)** | V-6 / V-9 / V-10 は本 wave の外で未裁定のまま。§9 の 0/3 と実装 wave の起票制限は不変と明記する |
| 16 | B nit | plan 時点の HEAD と現在の local main を分けて書く | **real / 採用** | 本裁定の冒頭に記載 |
| 17 | B | FC05a / FC05b は「どの layout で実行されたか」を保証しない。物理 identity 検査が追加で拒否すべきは「q10 / q11 の root と config を交換し provenance を整合的に再生成した入力」 | **real / 採用 (変異事前登録の候補へ)** | 所見 3 の lock 再導出があって初めて追加拒否になる。文字列比較だけなら F28 型の冗長 gate |
| 18 | A nit A8 / A9 / A12 / A13 / A15 | 一般化の過大と anchor 不足 | **real / 採用 (親 brief 訂正)** | 設計文書には訂正後の表現で書く |

**refuted は所見 6 の「blocker」性だけ。** 他は file:line で裏付けられ、親が現物で追認した (completeness `:840-893`、`AttemptSlotCapability.capability_digest_sha256` `trial_registry.py:436-450`、`wal.log_trigger_binding` `:1595-1611`、`layer3_report.py:930-945`、`s8b_holdout_admission.py:782-802`)。

## 2. 親 brief の訂正

- (P1) を改める: 物理成分は `trial` 接尾辞でなく `search_config["origin_campaign_run"]`、入力は (論理 cfg, attempt slot capability digest, q)。
- A6: 「identity が違えば protocol_digest も違う」は 33 cfg (同 slug・同 search_tag) にだけ成り立つ。
- A8: `run_campaign` 直呼びは `_assert_resume_allowed` を通らない。8c の `drive_iteration` 経路に限る。
- A12: create-only writer は在る (`reflux_result_evidence.py:431-442`)。無いのは production の record builder と caller。
- A13: run plan の ordinal / replicate / wire は consumer が読む。未参照は `planned_campaign_run_identity` だけ。
- A15: 測定世代の導出は `s8b_holdout_admission.py:782-802`。

## 3. plan v2 (確定した設計) — 設計文書の追記節に書く内容

1. **2 層 identity。** 論理 campaign (`binding.campaign_id` = `PreparedCampaignIdentity.campaign_id` = `OriginBindingCapability.campaign_id` = attempt slot の `campaign_id`、1 trial 1 つ、座標) と、物理 campaign run (`run_plan.members[q].planned_campaign_run_identity` = `execution_provenance.campaign_run_identity`、33 個)。
2. **物理 identity の導出。** `cfg_q = replace(logical_cfg, search_config={**logical_cfg.search_config, "origin_campaign_run": {"attempt_capability_sha256": slot.capability_digest_sha256, "query_ordinal": q}})`、`campaign_run_identity[q] = str(ident.campaign_id(cfg_q))`。決定的、時刻・PID・乱数を含まない。同一 slot 再入 = 同 identity、別 attempt = 別 identity。
3. **claim / layout / WAL / `done` の分離。** `loop._authorize` の claim、`exploration_campaign_layout(campaign_run_identity[q])`、`_assert_resume_allowed`、`done` seed がすべて q 別になる。33 identity と 33 preimage の相異を run plan 作成前に検査する。
4. **順序。** capability 発行 → attempt slot 予約 → 33 identity 導出 → envelope create-only → envelope digest の durable 束縛 (R1) → observation 開始 → executor (q = 0..32)。
5. **証拠側。** `execution-provenance` に `campaign_run_identity` を足す (schema 世代は R3)。formal consumer は (i) 論理 3 項等式 (FC03) を残し、(ii) 各 record の `campaign.lock` ref を decode して物理 identity と論理 campaign を再導出し、(iii) envelope を disk から再読して digest 一致を要求し、(iv) WAL ref をその layout 配下に束縛する。
6. **実行器。** origin topology mode は `_run_workload` の単一 layout 作成より前で分岐し、generation loop に入らない。各 q で fresh check・identity 一致・残時間検査を行い、捕捉した失敗は tombstone suffix。report は論理 `campaign_id` + `campaign_runs[33]` (exact 3 key)。
7. **既定経路。** すべて origin capability 発行時だけ発火。originless の bytes・受理集合は不変。
8. **稼働 wave。** t524: attempt slot の `campaign_id` は論理値のまま、slot / receipt v5 / `prereg_generation` に物理 identity を足さない。ただし `trial_registry.py` の report / measurement-target 部分は変わるので t524 着地後に着手。t1851 (s8b): 変更 0。

## 4. 裁定パッケージ (ユーザーへ返す)

| # | 択一 | 親の推奨 | 採らない場合の成果物影響 |
|---|---|---|---|
| R1 | run plan (envelope) digest の durable な束縛先。(a) lifecycle `start` 行に origin-only optional key `origin_run_plan_sha256` を足す (§6.5 の projection 規律) (b) ledger `BatchReserved` payload に載せる (ledger 受理集合の変更、V-6 と同型) (c) in-process seal だけ (durable でない) | **(a)** | 束縛が無いと、別 object / 別 path の envelope を consumer へ渡して 33 identity を宣言し直せる (偽装 (d)(e))。(c) は process crash で消える |
| R2 | origin cell の「complete」の権威。(a) issued capability + formal-consumer receipt + 33 `campaign_runs` の lock / WAL 再検査からなる origin 専用 completion を、通常 cell の「全 campaign が admitted」と分けて置く (b) 33 物理 campaign すべてに通常 Layer 3 admission を要求する | **(a)**。(b) は P6 が qualifying rejection を必要とするため成立しない | 決めないと completeness と registry acceptance が単一 root 前提のまま origin cell を拒否し、結線実装 wave が受入条件を持てない |
| R3 | `execution-provenance` の schema 世代。(a) `execution-provenance/v2` を新設し v1 は historical decoder (origin consumer は v2 のみ受理) (b) v1 を in-place で 8 key に拡張 | **(a)** | (b) は同じ schema 名が異なる exact key 集合を表し、fixture と将来 artifact の世代判別ができない |
| R4 | (確認) 受理集合が動く 3 写像 — q 別 claim / layout の受理、native WAL `stage/payload` shape の受理 (D1555 の修理)、origin cell の report 形 — を D1616 / D1555 / §6.5 の範囲内として実装 wave へ渡してよいか | **可** | 否なら V-8 (a) は実行形を持てず D1616 に戻る |

V-6 / V-9 / V-10 は未裁定のまま。発行 3 条件 0/3、本番 authority 0 件、結線実装 wave の起票制限 (2026-08-12) は本 wave で変わらない。

## 5. 段 5・6 の省略と検査

実装面の差分ゼロ (docs のみ) なので段 5・6 と変異 matrix を免除する (DW-S04)。受入は `tools/check_docs.py` と docs を読む test (`test_check_docs.py`) の焦点走。
