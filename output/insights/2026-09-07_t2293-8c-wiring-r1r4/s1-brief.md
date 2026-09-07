# 段 1 brief — [T-2293] 8c 結線の R1〜R4 実装

wave `dev-wave-t2293-8c-wiring-r1r4`、branch `worktree-dev-wave-t2293-8c-wiring-r1r4`、base main `cf4273f56`。

## scope

D1667 (R1)・D1668 (R2)・D1669 (R3)・D1670 (R4) の 4 裁定を、`docs/phase3-8c-wiring-design.md`
§J の受入要件 9〜18 として結線する。ledger producer FSM、witness class normalizer、材料レポート
renderer (§9 の未存在層) は本 wave の scope 外。V-6 (D1672)・V-7 (D1671)・V-9 (D1673)・V-10 (D1674) は
決着済みだが、V-7 の初期化 operation script 起草と V-9 の批准値内訳差し替えは別 wave とし本 wave では扱わない。

## 確定済みユーザー裁定 (前提として動かさない)

- R1 = lifecycle `start` 行の起点専用 optional key `origin_run_plan_sha256` (D1667)。ledger 受理集合は動かさない。
- R2 = 起点専用 completion (発行済み capability + formal consumer receipt + 33 `campaign_runs` の lock / WAL 再検査)。
  通常セルの「全 campaign が admitted」とは別に置く (D1668)。
- R3 = `execution-provenance/v2` 新設、起点 consumer は v2 だけ受理 (D1669)。
- R4 = §G の 3 写像 (q 別 claim / layout、native WAL shape、起点 report 形) は可 (D1670)。
- 仮想リスク向けの gate・検査・台帳・一般化を足さない (ユーザー明示、D205 / 2026-08-12 の研究最優先方針)。

## 親の実測 (brief 前) — 前提の裏取り

| # | 設計文書の前提 | 実測 |
|---|---|---|
| 1 | R1 の optional key は §6.5 の projection 規律に収まる | **先例が実在**。lifecycle `terminal` は既に `_LIFECYCLE_TERMINAL_KEYS` (`trial_registry.py:216-220`) を frozenset の集合にし、起点専用 optional key `origin_terminal_projection` を持つ。`start` は `_LIFECYCLE_START_KEYS` (204-210) が単一 frozenset で `_exact_keys` (4421) に渡る。R1 は terminal と同型に変えるだけ |
| 2 | `execution-provenance/v1` の production producer は不在 | 正。書き手は 0 件、consumer は `reflux_result_evidence.py:555`、生成物は test fixture `reflux_origin_fixture_builder.py:412` だけ |
| 3 | v1 の歴史 decoder を作るか | **作らない。** `output/` 配下に v1 の実在成果物は 0 件 (`git grep "execution-provenance" -- output/` が insight 文書以外に hit なし)。D1669 の「実在成果物を確認できたときだけ」の条件が満たされない |
| 4 | envelope の write が observation 開始より後 | 正。`write_recovery_envelope_create_only` の唯一の caller は `p3_autonomous_workload_trial.py:3812` (`_run_workload`、`_finish_trial:3392` 経由)。`begin_attempt_observation` は `run_trial:4675`。実行順は observation 開始 → envelope write |
| 5 | `planned_campaign_run_identity` に束縛先が無い | 正。`reflux_origin_topology.py:133/159/182/368/412` に実在し 33 相異を要求するが、production の producer / consumer は参照しない。test は `fixture-run-%04d` を入れる (`test_p3_autonomous_workload_trial.py:10292`) |
| 6 | 発行 3 条件・本番 authority | **0/3、0 件のまま。** 本 wave は結線を実装するだけで、発行条件を 1 つも満たさない。本番で発火する経路は生まれない |
| 7 | 稼働 wave との編集面重複 | `dev-wave-t2228-driver-gate-liveness` の編集面は pegasus probe / `test_hooks.py` / docs であり `reflux_formal_consumer.py` を含まない (branch 三点 diff と作業ツリー status の両方で確認、status は clean)。重複なし |

## 不変条件 (破ってはいけない)

- **規律 2**: 正しさゲートを緩める変異を採らない。既存の拒否分岐を弱めない。
- originless 経路の bytes と受理集合は不変 (§6.5)。run-start / report / `launch_admission_sha256` / lifecycle。
- 変更はすべて origin capability 発行時だけ発火する。`launch_admission.origin_binding` を発火条件にする。
- `reflux_origin_topology.py`、`campaign_claim.py`、`loop.py`、`ident.py`、`model.py`、`s8c_acceptance_receipt.py`、
  `s8b_*` は変更しない (§F / §J)。
- FC03 の 3 項等式 (`execution_provenance.campaign_id == trial_binding.campaign_id == capability.campaign_id`) を残す。
  物理値へ置き換えない。
- 物理 identity は `search_config["origin_campaign_run"]` の構造化 key で作る。`trial` 文字列の接尾辞は使わない。
- 時刻・PID・乱数を identity に入れない。
- 「provenance 33 値の相異」単独の変異は登録しない (§J 末尾、単一理由にならない)。

## 成果物の形

- コード + テスト (段 5・6 の Codex 実装子)。docs は親が書く。
- insight `output/insights/2026-09-07_t2293-8c-wiring-r1r4/` に逐語・変異台帳。
- spool fragment (worklog / decisions / failures)。canonical 3 台帳は段 9 の land が fold する。

## 分割方針 (段 5 の並列 3 単位、file 所有を排他にする)

| 単位 | 所有 file | 担当 |
|---|---|---|
| A | `trial_registry.py`、`reflux_result_evidence.py`、`orchestrator/tests/reflux_origin_fixture_builder.py`、`reflux_origin_fixture_baseline.json` | R1 の key 集合と lifecycle 検証、R3 の v2 schema、R2 のうち acceptance issuer の origin 対応 |
| B | `p3_autonomous_workload_trial.py`、`p3_s4_loop_trigger_gating.py` | 33 個の `cfg_q` / identity 導出と相異検査、envelope の順序是正と create-only、R1 の書き手側、起点 executor |
| C | `reflux_formal_consumer.py`、`autonomous_trial_completeness.py`、`layer3_report.py` | R2 の起点専用 completion、lock からの物理 identity 再導出、envelope 再読、native WAL shape decoder、起点 report の `campaign_runs` 再検査 |

各単位の test は自分の所有 file に対応する `orchestrator/tests/test_<file>.py` を持つ。

## 割れうる前提 (親の provisional 裁定・段 3 の攻撃対象)

- (P1) 「R1〜R4 の結線だけ」= §J の受入要件 9〜18 の全体である。R4 は確認裁定なので §G の 3 写像の
  実装を含むと読んだ。含まないと読むなら本 wave は R1・R2・R3 だけになり、q 別 layout も executor も
  生まれず R2 の 33 `campaign_runs` 再検査が検査対象を持たない。
- (P2) 3 単位の file 所有は排他にできる。R1 の書き手側 (単位 B) と key 集合側 (単位 A) の境界は
  `trial_registry` の公開関数 signature で切れる。
- (P3) v1 の歴史 decoder を作らない (実測 3)。v1 fixture は v2 へ移行させ、v1 を読む経路を残さない。
- (P4) 起点 executor は `_run_workload` が論理 campaign の単一 layout を作る前で分岐し、
  `for generation in range(1, generations + 1)` に入らない (§E)。`generations == 2` は論理 trial の
  admission metadata として残す。
- (P5) 受入は repo 全走。実測環境は段 6 で §7.0.0 の自動判定に従う。
