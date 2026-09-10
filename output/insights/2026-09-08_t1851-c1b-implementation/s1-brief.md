# [T-1851] 単位 C1b 実装 — 段 1 brief

base `8924c0ef3` (継承 tip `b2a3d9ce2` + local main `5d4a28b16` の merge)。
branch `worktree-dev-wave-t1851-unit-a`。**land しない (D1341)。**

## 1. scope

契約 `output/insights/2026-09-08_t1851-unit-c1b-sealed-terminal-evidence/contract-v3.1.md` を
実体化する。手順は同 dir の `plan-v2.md`。**契約と plan は本 wave では書き換えない。**

**段 2・3 は前 wave の成果物を流用する** (読み込み契約の規定。変更面の骨格が同一)。
再検査は段 6 レビューへ寄せる。本 wave は `1 → 4 → 5 → 6 → 7 → 8 → 9`。

## 2. 確定済みユーザー裁定

- **land しない (D1341)。** 6 単位が揃うまで branch 上の checkpoint に留める。
- 実装子は **2 本・直列** (leaf → 統合)。中途半端な分割は却下済み。
- 規模が 1 wave に収まらないと段 5 の途中で判明した場合、**leaf が閉じた時点を checkpoint とし
  統合子を次 wave へ送る** (plan v2 §6)。production の途中分割はしない。

## 3. 段 1 で実測した前提 (base `8924c0ef3`)

| 対象 | 契約 / plan の記載 | 実測 | 判定 |
|---|---|---|---|
| `s8b_attempt_profile.py` `_S8B_V2_EVENT_KEYS` | `:490` | `:490` | 一致 |
| launcher の捕捉集合 | `:777` `(RuntimeError, TimeoutExpired, OSError)` | 同一 | 一致 |
| campaign の捕捉集合 | `:6264` `(RuntimeError, TimeoutExpired)` | 同一 | 一致 |
| `_AttemptState` の 3 digest | `:182-184`、綴りは `observation_event_sha256` | 同一 | 一致 |
| core の `finished_at` | `:1039` は text 検査のみ | 同一 | 一致 |
| durable claim の identity | `s8b_holdout_admission.py:1719-1722` | `cell_id` `records` `threads` `workload` を確認 | 一致 |
| `_JOURNAL_KEYS["session"]` | exact 30 key | **exact 30 key、語も完全一致** | 一致 |
| perf semantic inventory | `test_official_perf_closure.py:44/531/903` | `:44` `:531` `:905` (assert は 905) | **微差** |
| 既存 4 test file の関数数 | 175 | 68+9+75+23 = **175** | 一致 |
| 新 identifier / path の pin | production・test hit 0 件 | **0 件** (17 語を実装面 6 tree で走査) | 一致 |
| 触る 8 file の whole-file sha256 golden | 0 件 | **0 件** (8 hash を repo 全体で走査) | 一致 |

## 4. 実測が plan v2 を覆した点 (P1・段 4 で裁定する)

**(P1) plan v2 §4.4 の「transition callback の呼出し閉包」は caller 数ではなく出現数である。**

| 対象 | plan v2 の記載 | 実測した caller | 実測した出現数 (def・comment 込み) |
|---|---:|---:|---:|
| `_atomic_update_locked()` | 4 | **2** (`:1752` `:1801`) | 4 (def `:1666` + comment `:1658`) |
| `_atomic_update()` | 7 | **6** (`:2030` `:2306` `:2470` `:2596` `:2652` `:2697`) | 7 (def `:1739`) |
| `_atomic_update_with_consumption_marker()` | 3 | **2** (`:2011` `:2454`) | 3 (def `:1763`) |

親の裁定: **plan v2 の「10 本すべてを同じ commit で直す」という結論自体は覆らない** —
数え方が違うだけで、規約を変えるなら全 callable を直すという要求は不変である。
ただし**実装子は数を plan から写さず、自分で call site を数え直す。**

**(P2) `record_attempt_terminal` の consumer は s8b 系の外にもある。**
plan v2 は「直接・関数渡し caller は 8 箇所 (production 3 / test 5)」と書くが、実測では
`p3_autonomous_workload_trial.py` `trial_registry.py` `s8c_preregistration_evidence.py` と
その test も同 API を使う (計 14 file)。**keyword-only + 既定値を守る限り変更不要**という
plan の結論は保たれるが、**その保証は実装子が実際に確かめる。**

## 5. 不変条件 (破ったら停止)

- **規律 2:** anomaly を検出する既存 gate を 1 つも緩めない。v1 の key 集合・受理集合を 1 bit も変えない。
- **契約 9 節:** `expected_use_perf` の導出は launcher の既存 gate (`:565-588`) 1 本のまま。
  leaf に perf 述語の新しい直接 call を置かない (`test_official_perf_closure.py` の
  semantic inventory が落ちる)。generic helper の背後へ隠す逃げ方も取らない。
- `attempt_registry_core.py` に `aborted=False` の keyword 呼び出しと `OriginSealed(False, ...)` を
  書かない (`test_reflux_formal_consumer.py` の AST 走査下)。
- 証拠の canonical bytes は既存の holdout-safe gate を必ず通す。専用 bypass を作らない。
- 実装子は docs を編集せず commit もしない。

## 6. 成果物

- `orchestrator/campaign/s8b_terminal_evidence.py` (新設) と
  `orchestrator/tests/test_s8b_terminal_evidence.py` (新設) — 実装子 1
- 既存 8 file の改修 — 実装子 2 (leaf 完了後)
- 変異 matrix、受入全走の結果、insight、spool fragment

## 7. 分割方針

plan v2 §2 のとおり **2 本・直列**。leaf は他 8 file を import しない純関数層 (import は
`attempt_registry_core.canonical_json_bytes` と `s8b_floor_stats` の 2 つだけ) なので単独で閉じる。

## 8. 受入・実測環境

login node で焦点走、受入は `tools/dev_wave_wait.py acceptance --wave t1851-unit-a`。
**前 wave の受入は非帰属の赤 1 件 (`test_g5_real_ledger_covers_at_least_90_percent_of_real_collection`、
被覆率 26/29 = 89.655%) で `child-verdict` になった。** 台帳
`orchestrator/tests/acceptance_duration_ledger.json` の最終更新は依然 `d53c91a2b` (2026-09-07) で、
main 側の保守事項 (F684) である。本 wave の leaf test は subprocess を使わない純関数 test なので
real collection の行数を増やさない見込みだが、**受入の実測で確かめる。**
