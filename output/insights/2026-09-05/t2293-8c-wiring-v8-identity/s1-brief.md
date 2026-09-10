# 段 1 brief — [T-2293] 8c 結線の設計 wave: V-8 (a) の identity / capability 衝突の解消案

## scope

D1616 が採った **V-8 (a) 「1 query ordinal = 1 campaign run」** が現行コードで実行形を持たない原因 2 つ —
(原因 1) campaign identity が `CampaignConfig` だけから決まり 33 run が同じ identity になって claim で拒否される、
(原因 2) identity を分けると `OriginBindingCapability/v1` が `campaign_id` を 1 つしか持てず formal consumer の campaign 一致要求と衝突する —
の**解消案を設計する**。成果物は `docs/phase3-8c-wiring-design.md` の §11 V-8 行の追記と関連節 (§5.3 / §6.2 / §7.1 / §12 と新設の追記節) だけ。
**実装しない (docs のみ)。** 一般化・新 framework・新 gate の実装は scope 外。設計は実装に触れる範囲を file と関数で名指しし、択一が残れば裁定パッケージにして返す。
D1616 の「(b) 1 run 内 33 行」は certifiable にならないので再検討しない。

## 確定済みユーザー裁定 (覆さない)

- D1616: V-8 は (a)。費用は理由にしない。identity と capability の衝突は結線設計で解く。
- D1561 / T-2261 実測: 倍率 1.02〜1.11 倍。scheduler へ 33 回投入する必要はない (reservation は連続 run を妨げない)。止めているのは claim と capability の identity 設計。
- D1555 / D1565: P6 の機械実装は V-8 / V-7 の裁定まで保留。本 wave は設計だけで、実装 wave の起票制限 (発行 3 条件 0/3、本番 authority 0 件、D114 上限 1) は不変。
- D75: 同名で別実体の識別子は必ず完全修飾する。`campaign_id` は `binding.campaign_id` (registry) / `PreparedCampaignIdentity.campaign_id` (8c) / `execution_provenance.campaign_id` (evidence) を区別する。
- D1190 (s8b の先例): 効果 key (座標) は不変のまま残し、run ごとの測定世代 ID を決定的に導出する。`O_EXCL` の一回性は世代の内側へ限定する。
- D1269 / t524 (稼働中、未着地): 8c の実験単位は `(prereg_generation, holdout, arm, replicate_index)` の slot。slot は `campaign_id` を 1 つ持ち、下流は predeclared な全 unit に final terminal が 1 件ずつあることを検査する。**本 wave の案は slot の `campaign_id` を分裂させてはならない。**
- 絶対規律 2 / DW-G05: 既存の拒否分岐 (claim の release 不在、`_assert_resume_allowed`、FC03 の campaign 一致、`assert_campaign_binding`) を弱めない。案は束縛を**足す**向きに限る。

## 不変条件

1. registry / capability / attempt slot / lifecycle / launch admission record の `campaign_id` は**1 trial に 1 つ**のまま (論理 campaign)。
2. 物理 run の identity は query ordinal ごとに相異なり、claim (`campaign_claim.acquire_claim`) と layout (`exploration_campaign_layout`) と WAL を分ける。`done` 集合を跨がせない (§5.3)。
3. 物理 run identity は run plan (recovery envelope) 作成時に決定的に固定され (§7.1 / §8)、時刻・乱数・PID を含まない。
4. formal consumer は「33 record が同じ論理 campaign に属する」と「33 record が 33 個の相異なる物理 run に 1 対 1 で対応する」の**両方**を検査する。片方を落として片方に置き換えない。
5. 既定 (originless) 経路の bytes・受理集合は変えない (§6.5 の projection 規律)。

## 成果物の形

- `docs/phase3-8c-wiring-design.md`: §11 V-8 行へ「裁定済み (D1616、(a))」と解消案の要約 + 新設の追記節「追記 (2026-09-05) — V-8 (a) の実行形: 論理 campaign と物理 campaign run の分離」に、
  (i) 2 層 identity の定義、(ii) 触れる file / 関数 / exact key の表、(iii) 却下した案、(iv) 残る択一 (裁定パッケージ)、(v) 実装 wave への受入要件 (§12 へ追記) を書く。
- 記録: spool fragment (worklog 1、decisions 1 = 解消案の採用)、insight README (逐語 + 親の実測)。
- phase doc のチェックは無い (T-2293 は worklog 次の一手の項で、phase3.md に対応 checkbox は無い)。

## 実アンカー表 (親が現物で確認済み、local main 97ee3cd3a)

| # | anchor | 実測した事実 |
|---|---|---|
| A1 | `orchestrator/campaign/ident.py:196-235` `canonical_preimage` / `campaign_id` | preimage = `spec_content` / `ccbench_commit` / `search_tag` / `search_config` / **`trial`**。genome も trigger wire も含まない |
| A2 | `orchestrator/campaign/model.py:81` `CampaignConfig.trial: Optional[str]` | docstring「入力同一でも別 campaign を切るとき (seed study 等)」。**既存の seam** |
| A3 | `orchestrator/campaign/p3_autonomous_workload_trial.py:794` `_campaign_for` | 8c は `trial=f"{trial_id}-{workload}"` を固定で入れる。`generation_budget` は `search_config` (行 770) |
| A4 | 同 `:1151-1198` `_prepare_campaign_identity`、`:1341` `assert_campaign_binding` | prepared の `campaign_id` は registry `binding.campaign_id` と exact 一致を要求 (`trial_registry.py:4926-4938`) |
| A5 | `orchestrator/campaign/loop.py:194-228` `_authorize` | `campaign_identity = str(ident.campaign_id(bound_cfg))`、`protocol_digest = sha256(canonical_preimage)`。Pegasus (`env_contract.py:260`、`single_process=True`) では claim 必須 |
| A6 | `orchestrator/campaign/campaign_claim.py:170-176, 383-434` | claim path = `<claims>/<identity>.claim`、`O_EXCL`、release 無し、同一 `protocol_digest` の LIVE owner を拒否。**identity が違えば protocol_digest も違う** (trial を含むため) |
| A7 | `loop.py:442-463, 528-533` | `done` は WAL の terminal variant を seed。同 layout の再 run は同 variant を skip (§5.3 の duplicate skip の実体) |
| A8 | `p3_s4_loop_trigger_gating.py:475-492` `_assert_resume_allowed` | Pegasus は `allow_resume=False`: 同 layout に lock / loop_state / WAL / provenance が 1 つでもあれば拒否。**同 identity の 2 run 目は claim 以前にここで止まる** |
| A9 | `p3_s4_loop_trigger_gating.py:767, 811` | 各 iteration は `Genome("silo", _BASE)` 1 個で `run_campaign(campaign_cfg, [genome], ...)`。**33 行で変わるのは genome でなく `TriggerGateBinding` (mask / wire)**。「identity が genome を含まない」は表現が不正確 |
| A10 | `orchestrator/campaign/reflux_origin_binding.py:176-194, 561, 619` | capability は `campaign_id` 1 つ (= `binding.campaign_id`)。発行判断は prepared と binding の一致 (行 561) |
| A11 | `orchestrator/campaign/reflux_formal_consumer.py:614, 697-702, 731-742` | FC03: `trial_binding.campaign_id == capability.campaign_id` と `execution_provenance.campaign_id == trial.campaign_id == capability.campaign_id` (3 項等式)。FC05a: `build_attempt_id` 相異。FC05c: WAL の trigger binding = record |
| A12 | `orchestrator/campaign/reflux_result_evidence.py:97-99, 127-135, 551-592` | `trial_binding` = {launch_admission_record_sha256, campaign_id, workload}。`execution-provenance/v1` exact key = {schema_version, build_attempt_id, campaign_id, workload, contract_sha256, trigger_binding, execution_receipt_sha256}。**producer (書き手) は repo に不在** (grep 0 件) |
| A13 | `orchestrator/campaign/reflux_origin_topology.py:126-186, 368-372` | `TopologyMember.planned_campaign_run_identity` が既に存在し、33 member で相異を要求する。**しかし consumer にも producer にも参照が無い** (topology 外 grep 0 件、test は `fixture-run-0000` 等の固定文字列) |
| A14 | `orchestrator/campaign/campaign_lock.py:30-46, 275-302` | A-1 pilot の non-certifying lock は `common_record.campaign_ids` (exact 3、相異) + `workload_binding.{campaign_id, ordinal}` で「1 共有 record に N 物理 campaign を ordinal で束ねる」先例 |
| A15 | `orchestrator/campaign/s8b_attempt_registry.py:113-130`、D1190 | s8b は `campaign_run_id` を消費 identity に含め、測定世代 ID を `sha256({observation_role, campaign_run_id})` で決定的に導出する先例 |
| A16 | `trial_registry.py:4222-4275` `launch_admission_record` | `origin_binding` key は capability 発行時だけ出す。`origin_record["campaign_id"] == binding.campaign_id` を要求 |
| A17 | `p3_autonomous_workload_trial.py:3790-3808, 3850` | trial は `exploration_campaign_layout(campaign_id)` を 1 つ作り、`for generation in range(1, generations+1)` で同 cfg・同 layout に `drive` を呼ぶ。manifest は `generations == 2` を要求 (`trial_registry.py:772`) |

## 親の provisional 裁定 (攻撃対象)

- **(P1) 2 層 identity。** 論理 campaign = 現行 `campaign_id` (registry / capability / slot / lifecycle、1 trial 1 つ)。物理 campaign run = query ordinal `q` ごとの `campaign_run_identity[q] = str(ident.campaign_id(replace(cfg, trial=f"{cfg.trial}-q{q:02d}")))`。A2 の既存 seam を使い、新 field を `CampaignConfig` へ足さない。これで A5 / A6 / A7 / A8 が全部別 identity・別 layout になる。
- **(P2) 物理 run identity の束縛先は capability でなく run plan。** `TopologyMember.planned_campaign_run_identity` (A13) を「予約前に固定した物理 run identity」と定義し、capability の `campaign_id` は 1 つのまま。capability へ 33 値を足す案、33 capability を発行する案は却下。
- **(P3) 証拠側の結線。** `execution-provenance` に `campaign_run_identity` を**足し**、`campaign_id` は論理値のまま残す。FC03 の 3 項等式は残し、新条件「`execution_provenance.campaign_run_identity == run_plan.members[q].planned_campaign_run_identity`」と「33 値の相異」(envelope 側は既に要求) を足す。`trial_binding` は変えない。producer 不在 (A12) なので凍結 bytes に触れない。
- **(P4) 実行器。** origin topology mode では A17 の generation loop を回さず、`q = 0..32` を順に `drive(cfg_q, layout_q)` する専用 executor を `p3_autonomous_workload_trial.py` に置く (関数名は plan が決める)。report には論理 `campaign_id` と `campaign_runs[q] = {query_ordinal, campaign_run_identity, campaign_root}` を足し、completeness の exact key は同じ変更単位で optional に更新する (§6.5)。
- **(P5) 稼働 wave との整合。** t524 の slot `campaign_id` は論理値で、33 物理 run は 1 slot (replicate_index 0) の内側。t1851 (s8b) には触れない。
- **(P6) 却下する案:** claim に release / per-attempt key を足す (拒否分岐の弱体化)、identity へ trigger wire を入れる (source 行と `m == m_s` の validation 行が同 wire で衝突する)、`generations` を 33 にする (manifest が 2 を要求し意味も別)、identity を時刻・PID で分ける (D1190 が却下した乱数発行と同型)。

## 分割方針・環境

docs-only だが正しさ防壁 (formal consumer の受理条件) に触れる設計なので軽量版にしない: 段 2 plan 1 本、段 3 レンズ 2 本 (整合・実効性 / 正しさ境界・恒真化)、段 4 裁定、段 7 記録。段 5・6 は実装面が無いので省略 (変異 matrix 無し)。
受入は `tools/check_docs.py` と docs 関連 test の焦点走だけ。計測・build・計算ノード job は行わない。

## DW-G05 (放置時の成果物影響)

解消案が無いままだと、V-8 (a) は裁定されたが実行形が無く、P6 の 32 mask 主張・材料レポート・試行台帳の origin 行は 1 件も作れない (D1555 の依存鎖の根が閉じない)。誤った解消 (例: FC03 の campaign 一致を外す) は、別 trial の物理 run を 33 record へ流用できる穴を開ける。
