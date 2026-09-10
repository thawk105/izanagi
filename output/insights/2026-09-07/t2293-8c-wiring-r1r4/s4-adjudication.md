# 段 4 裁定 — [T-2293] 8c 結線 R1〜R4

段 2 plan (998 行) と段 3 レンズ 2 本 (整合・実効性 / 正しさ境界・恒真化) を裁定する。
両レンズとも独立に **判定「作り直し」** を返し、根本原因も一致した。

## 1. 裁定の骨子 — 本 wave は「契約 wave」に絞る

依頼は「R1〜R4 の結線」であり、裁定 D1667〜D1670 は動かさない。しかし実測の結果、
**R2 と受入要件 12・18 は、親 brief 自身が scope 外と宣言した層 (ledger producer FSM、
物理 evidence writer、witness normalizer、材料レポート renderer = 設計文書 §9 の未存在層) を
必要とする**ことが確定した。scope 外の層を作らずにこれらを実装すると、
発火する producer を持たない gate を足すことになり、ユーザーが明示した
「仮想リスク向けの gate・検査の追加は scope 外」と DW-G04 の双方に反する。

したがって本 wave の scope を次に確定する。

| 受入要件 | 本 wave | 根拠 |
|---|---|---|
| 9 (33 cfg_q / identity の決定的導出と相異検査) | **実装する** | 依存する未存在層が無い |
| 10 (registry 照合と capability 発行は論理 identity だけを受ける) | **実装する** | 同上 |
| 11 (envelope を予約後・observation 開始前に create-only で書く) | **実装する** | §C の順序欠陥を直す。crash 時に事前登録 bytes が無い穴を塞ぐ |
| 13 (provenance の `campaign_run_identity` 必須 key、R3 の世代) | **実装する** | R3 そのもの |
| 14 (formal consumer が `campaign.lock` から物理 identity を再導出) | **実装する** | 下記 §3 で carrier 問題を解消した |
| 15 (envelope を disk から再読し R1 の束縛値と digest 一致) | **実装する** | R1 の束縛先が本 wave で生まれるため実装可能 |
| 16 (FC05a の `build_attempt_id` 相異) | **実装済み** | `reflux_formal_consumer.py:768-780` に実在。親が現物で確認した。本 wave の差分 0 |
| 17 (native WAL shape の検証と shape family 固定) | **一部実装する** | native decoder は既に実在 (`:727-765`)。**設計文書 §D の「fixture 形を要求する」は古い。**残るのは mixed shape 拒否だけ |
| 12 (sealed executor) | **実装しない** | 物理 evidence producer が無く、実行結果が ledger / result-evidence / formal consumer へ届かない (レンズ A B1、レンズ B blocker 2)。`_run_one_iteration_resolved` が `CampaignSummary` を捨てるため actual ID 検査も恒真になる (レンズ A B2、レンズ B blocker 4) |
| 18 (origin report の `campaign_runs` 再検査) | **実装しない** | producer 側 finalizer が単数 `campaign_root` を要求し、通常 Layer 3 admission が positive のときだけ `complete` になる (レンズ A B3)。要件 12 の産出物が無いと検査対象が存在しない |
| R2 (起点専用 completion) | **実装しない** | 要件 18 に依存する。加えて提案 API は receipt の実在を証明できない (レンズ B blocker 1) |

本 wave が閉じるのは **「8c の物理束縛契約」**である。**「8c 結線完了」「発行 3 条件を満たした」
「P6 が発火する」「本番で物理実行を保証する」とは名乗らない。**
発行 3 条件は 0/3、本番 authority は 0 件のまま変わらない。

この切り方は段 2 plan の第一 wave 案とレンズ A の第一段案の共通部分であり、
両者が独立に「意味のある中間状態」と判定した位置である。

## 2. 所見の real / refuted と採否

### 採用 (real、本 wave で直す)

| 出所 | 所見 | 裁定 |
|---|---|---|
| レンズ A M5 | lifecycle start の現行 key 数は 14 でなく **15** | **real。**親が `trial_registry.py:204-210` で数え直して確認。plan のコードをそのまま使うと既存 field を落とす。plan v2 で訂正 |
| レンズ A B4 | R1 の key 追加が originless の受理集合を広げる。loader と acceptance が `origin_binding` と key 有無を照合しない | **real、must-fix。**規律 2 に直接触れる。`origin_binding` の有無と `origin_run_plan_sha256` の有無を **iff** にし、`record_trial_start_once` の引数間だけでなく loader (`:4420-4427`) と acceptance snapshot でも強制する |
| レンズ A M1 | 順序表から attempt classification が落ちている | **real。**順序を「slot 予約 → classification → initial ledger snapshot → 33 identity 導出 → envelope create-only → lifecycle start → observation 開始」に確定する。envelope 失敗は lifecycle 前なので preflight failure、lifecycle 後の失敗は report 付き partial とする |
| レンズ B must-fix 1 | 物理 root を canonical layout へ束縛していない | **real。**§3 の解法で同時に解決する |
| レンズ B must-fix 3 / D1723 | 4 件の変異候補が他層に先に拒否される | **real。**事前登録から外す (§4) |
| レンズ B nit 1 | brief の「v1 実在成果物 0 件」は tracked corpus の範囲でしか言えない | **real。**測定の射程を「repo の tracked corpus」と限定して記録する。D1669 の択一は戻さない |

### real だが本 wave の scope 外 (裁定パッケージへ)

| 出所 | 所見 |
|---|---|
| レンズ A B1 / レンズ B blocker 2 | 物理 evidence producer が無く、`result_record_bytes` は実行前の caller 入力のまま |
| レンズ A B2 / レンズ B blocker 4 | `_run_one_iteration_resolved` が `CampaignSummary.campaign_id` を捨てるため actual ID gate が恒真 |
| レンズ A B3 | origin cell が通常 Layer 3 finalizer と status 計算で complete になる前に止まる |
| レンズ A B5 / レンズ B blocker 1 | 提案 completion API が capability と formal receipt の実在を証明できない |
| レンズ A 裁定パッケージ候補 | 材料レポート renderer に ledger / result-evidence / 33 run と D1674 の保証限界が出ない |
| レンズ B (e) | 整合した lock/WAL まで後置した 33 directory は拒否できない。D1674 の trusted-writer 運用前提の外では物理実行 0 件の偽材料を排除できない |

### refuted

| 出所 | 所見 | 反証 |
|---|---|---|
| レンズ B blocker 3 / レンズ A M2 / plan 段 4 争点 1 | `campaign_lock_ref` carrier が無いので要件 14 は実装不能。`result-evidence/v2` の新設が要る | **refuted。**§3 のとおり carrier を足さずに実装できる。しかも計算で導くほうが自己申告より強い |
| plan 依存順序 | 段 5 を A/B/C 完全並列にできない | **refuted。**親が本裁定で公開境界の signature を先に固定する (§5)。plan の順序制約は「誰かが後で決める」ことが前提だった |

## 3. 要件 14 の carrier 問題の解消 — 計算で導く

plan とレンズ 2 本は「`campaign.lock` を content-addressed ref で解決するには
`result-evidence` に 3 本目の ref が要り、それは R1〜R4 の裁定範囲外」と結論した。
親はこれを **refuted** と裁定する。

実測: `exploration_campaign_layout(campaign_id, output_root)` は
`<root>/exploration/campaigns/<cid>` を**決定的に**返す (`orchestrator/campaign/layout.py:589-597`)。
formal consumer は `run_plan.members[q].planned_campaign_run_identity` を既に受け取っている
(`evaluate_formal_origin` の `run_plan: RecoveryEnvelope`)。

したがって consumer は次を自力で行える。

1. `campaign_output_root` (新しい必須 kwarg) と member の identity から
   `exploration_campaign_layout(identity, campaign_output_root).root` を**計算**する。
2. その path の `campaign.lock` を読んで decode し、preimage から identity を再計算して
   member の `planned_campaign_run_identity` と `execution_provenance.campaign_run_identity` に一致させる。
3. 同じ preimage から `origin_campaign_run` を除いた論理 cfg を再構成し、
   `capability.campaign_id` と `attempt_capability_sha256` に一致させる。
4. `evidence.ordered_wal_ref` の解決先が **計算した root の配下**であることを要求する。

**caller が lock の場所を申告する経路が無いので、レンズ B must-fix 1 の
「plan identity と整合する lock/WAL を任意 directory に後置する」入力も同時に拒否できる。**
content-addressed ref 案より狭い受理集合になる。schema の bytes も受理集合も変えない。

**保証しないこと:** レンズ B の偽装入力 (e) — 実行後に計算どおりの root へ整合した lock/WAL を
後置した入力 — は本 wave でも拒否できない。これは D1674 が明記した trusted-writer 運用前提の
外側であり、本 wave はこの限界を狭めない。記録に明記する。

## 4. 変異事前登録 (実装前、DW-M01)

plan の 18 候補から、他層が先に同じ入力を拒否する 4 件を **D1723 に従って外す**。

外す (レンズ B must-fix 3 の実測による):
- 要件 9 の `query_ordinal` 固定 0 — `reflux_origin_topology.py:368-370` の既存相異検査が先に拒否する。
- 要件 10 の issuer へ `cfg_q` — `reflux_origin_binding.py:559-562` が registry campaign ID 不一致で先に拒否する。
- 要件 12 の q0 layout 再利用 — 本 wave では要件 12 を実装しないため対象外。
- 要件 18 の receipt 欠落 — 本 wave では要件 18 を実装しないため対象外。

登録する変異 (単一理由で kill されること、実装後に F820 のとおり確認する):

| # | 位置 | 無効化する述語 | 期待する赤 |
|---|---|---|---|
| MU-1 | 要件 11 の envelope write 位置 | create-only write を `begin_attempt_observation` の後へ移す | 呼出し順 test だけが赤 |
| MU-2 | 要件 11 の envelope 材料 | producer 導出 identity でなく caller 値を通す | 導出一致 test だけが赤 |
| MU-3 | 要件 13 / R3 | `execution-provenance/v2` の exact key から `campaign_run_identity` を外す | v2 欠落 key の負例だけが赤 |
| MU-4 | 要件 13 / R3 | origin consumer が v1 も受理するようにする | v1 record を渡す負例だけが赤 |
| MU-5 | 要件 14 | lock から再導出せず provenance の文字列比較だけにする | q10/q11 の root と config を交換し provenance を整合再生成した負例だけが赤 (FC05a〜c は通る) |
| MU-6 | 要件 14 | 計算した canonical layout root との一致検査を外す | plan identity と整合する lock/WAL を別 directory に置いた負例だけが赤 |
| MU-7 | 要件 14 | ordered WAL の layout 所属検査を外す | 別 layout の WAL ref 負例だけが赤 |
| MU-8 | 要件 15 | disk から再読せず in-memory の run plan だけを検査する | lifecycle start 後に disk の envelope を差し替えた負例だけが赤 |
| MU-9 | 要件 17 | mixed shape family の拒否を外す | native + legacy 混在の負例だけが赤 |
| MU-10 | R1 | loader の `origin_binding` ↔ `origin_run_plan_sha256` の iff を片側だけにする | originless start に key を足した負例と、origin start から key を落とした負例が赤 |

## 5. 公開境界の固定 (段 5 を並列にするため親が先に決める)

```python
# 単位 A が提供、単位 B が呼ぶ
record_trial_start_once(..., origin_run_plan_sha256: str | None = None) -> TrialLifecycleToken
```

- `origin_run_plan_sha256` は `launch_admission.origin_binding` が在るときだけ非 None を許す。
  在るのに None、無いのに非 None はどちらも拒否 (iff、レンズ A B4)。

```python
# 単位 A が固定、単位 C が読む
_EXECUTION_PROVENANCE_V2_KEYS = frozenset({
    "schema_version", "build_attempt_id", "campaign_id", "workload",
    "contract_sha256", "trigger_binding", "execution_receipt_sha256",
    "campaign_run_identity",
})
RESULT_EVIDENCE_SCHEMA_VERSION = "result-evidence/v1"   # 変えない
```

- `schema_version` の値は `"execution-provenance/v2"`。origin consumer は v2 だけ受理する。
- **v1 の歴史 decoder は作らない** (D1669 の条件不成立、実測は repo の tracked corpus の範囲)。
  fixture は v2 へ移す。

```python
# 単位 C が変える公開 signature
evaluate_formal_origin(..., campaign_output_root: str) -> FormalConsumerResult
```

- 必須 kwarg として足す。既定値を置かない (origin 経路だけが呼ぶため originless に影響しない)。

## 6. 単位の所有 (排他)

| 単位 | 排他所有 file |
|---|---|
| A | `orchestrator/campaign/trial_registry.py`、`orchestrator/campaign/reflux_result_evidence.py`、`orchestrator/tests/test_trial_registry.py`、`orchestrator/tests/test_reflux_result_evidence.py`、`orchestrator/tests/reflux_origin_fixture_builder.py`、`orchestrator/tests/test_reflux_origin_fixture_builder.py`、`orchestrator/tests/reflux_origin_fixture_baseline.json`、`orchestrator/tests/test_reflux_originless_compatibility.py` |
| B | `orchestrator/campaign/p3_autonomous_workload_trial.py`、`orchestrator/campaign/p3_s4_loop_trigger_gating.py`、`orchestrator/tests/test_p3_autonomous_workload_trial.py`、`orchestrator/tests/test_p3_s4_loop_trigger_gating.py` |
| C | `orchestrator/campaign/reflux_formal_consumer.py`、`orchestrator/tests/test_reflux_formal_consumer.py` |

`autonomous_trial_completeness.py`、`layer3_report.py` は本 wave では変更しない (要件 18 が scope 外)。
`reflux_origin_topology.py`、`campaign_claim.py`、`loop.py`、`ident.py`、`model.py`、
`s8c_acceptance_receipt.py`、`s8b_*` も変更しない。

## 7. 受理集合の変化 (D1721 に従い「拡張」と記録する)

本 wave が動かす受理集合は次の 2 件である。「緩めていない」とは書かない。

1. lifecycle `start` 行: base 15 key の 1 択から、base 15 key と base+`origin_run_plan_sha256` の
   2 択へ**制御された拡張**。`origin_binding` の有無との iff で拡張分を限定する。
2. `execution-provenance`: v2 という新しい世代を**追加**する。origin consumer の受理は
   v2 だけに**縮小**する (v1 を拒否するようになる)。

要件 14・15・17 の変更は受理集合を**縮小**する側であり、拡張しない。
`campaign_output_root` の追加は wire でなく呼出し規約の変更である。

## 8. 裁定パッケージ (ユーザーへ返す)

§2 の「real だが scope 外」6 件を、次の 1 件の択一としてユーザーへ返す。

**Q. 8c の物理実行の producer 層 (ledger producer FSM、物理 evidence writer、
witness normalizer、材料レポート renderer) を作るか。**

- 作らない限り、要件 12・18 と R2 は実装しても発火する producer を持たない。
- 作る場合、設計文書 §9 が「未存在」と書いた 4 層の設計 wave が先に要る。
- 現状は発行 3 条件 0/3、本番 authority 0 件なので、作らなくても certified 選択・
  材料レポート・試行台帳の現在値は 1 つも変わらない。

親の推奨: **本 wave の契約を land してから、producer 層の設計 wave を 1 本立てる。**
R2 と要件 12・18 はその後の実装 wave で閉じる。

---

## 追記 (段 6、2026-09-07 21:30) — §5 の「loader で iff を強制する」要求を訂正する

段 6 の fix 第 2 巡で、**§5 の要求が実装不能であることが判明した。**親自身の裁定の訂正である。

### 事実

`_load_lifecycle_rows(data: bytes)` は lifecycle 台帳の bytes だけを受け取る。start 行が持つのは
`launch_admission_sha256` (digest) であって launch admission の record ではない。
**digest からは `origin_binding` の有無を判定できない。**したがって loader は、新しい情報を
与えられない限り iff を自力で強制できない。

fix 第 2 巡の単位 a はこれを、start 行へ `launch_admission` record 全体を埋め込むことで解こうとした
(`_LIFECYCLE_START_ORIGIN_CARRIER_KEY`)。

### 裁定 — carrier を採らない

**revert する。**理由:

- D1667 が裁定したのは「lifecycle start 行の起点専用 **optional key** `origin_run_plan_sha256`」である。
  admission record 全体の埋め込みは、この裁定が認めた形ではない。
- 受理集合の変更としても、§7 に記録した 2 件を超える。**未裁定の wire 拡張**である。
- ユーザーは「仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明示した。
  手で改竄した台帳行は、まさにその型の想定である。
- 同じ record が digest と実体の 2 か所に載り、永久に整合を保つ義務が生じる。

### 代わりに置く形

iff は、**launch admission が実在する層**で強制する。

- 書き手 (`record_trial_start_once`): `state.origin_binding` を直接見て iff を強制する (実装済み)。
- terminal (`record_trial_terminal`): `state.origin_binding` と projection の対応を強制する (実装済み)。
- acceptance: report の `launch_admission` と lifecycle 行を照合する (実装済み)。
- loader: **自分が見えるものだけを検査する。**key 集合の 2 択、digest の形式、
  start 行の起点主張と terminal の projection の対応。

### 名乗らない限界 (記録義務)

**loader 単体では、手で書いた start 行の起点主張が本物かを判定できない。**
偽の start-only 行は trial ID を占有し、正式な再入を拒否させうる。
最終 acceptance はこれを拒否するので、**certified 選択・材料レポートの値には到達しない。**
この限界を「塞いだ」と書いてはならない。

## 追記 2 (段 6) — 起点の失敗終端を足す

### 事実

受入要件 11 の順序是正により lifecycle start が observation 開始より**前**へ移った。
その結果、observation 開始後の失敗が **terminal を書けない**。
`record_trial_terminal` (`trial_registry.py:4934`) は
`(state.origin_binding is None) != (projection_record is None)` を拒否するため、
projection を作れない失敗では起点試行を終端できない。

**これは本 wave が入れた退行である。**台帳に「開始だけあって終端がない」行が残り、
再試行を阻止しながら acceptance も成立しない。

### 裁定 — 失敗終端に限って projection 無しを許す

- `terminal_status` が `"indeterminate"` または `"partial"` で、かつ非空の `failure_reason` を持つときに限り、
  起点試行が **projection 無しの base terminal 形**で終端できるようにする。
- `"complete"` は従来どおり projection を必須とする。**成功側の関門は 1 つも外さない。**
- loader の start ↔ terminal 対応も、失敗 status のときだけ同じ緩和を適用する。

### 受理集合の記録 (D1721)

§7 の 2 件に**次の 1 件を追加**する。「緩めていない」とは書かない。

3. lifecycle terminal: 起点試行が projection 無しで終端できる場合を、
   **失敗 status かつ非空 failure_reason のときに限って**追加する。**制御された拡張**である。
   成功終端の受理集合は不変。
