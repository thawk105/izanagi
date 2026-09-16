# [T-304] / [T-305] 段 4 裁定 — real / refuted、plan v2、変異事前登録

段 3 の 2 レンズ (`s3-lensA.md` 正しさ境界 / `s3-lensB.md` 射程と実効性) の全所見を裁定し、
親自身の追加実測を加えて plan v2 を確定する。

## 1. 親の追加実測 (段 3 の後に親が行った)

### 1-1. `DECIDER_VERSION` の bump は不要である (最も影響が大きい論点)

レンズ A 所見 2 とレンズ B 所見 2 が、改名が 8c 事前登録の identity へ到達すると指摘した。
`docs/phase3-8c-preregistration.md` の改訂手続きは
「**判定器・評価器・射影のいずれかで受理集合・拒否理由・射影された判定入力の意味を変える変更は、
bytes 差の有無に関わらず `DECIDER_VERSION` を bump し、その版を持つ新世代の record を発行しなければ
ならない**」と定める。これが成立すると D439 により wave を 2 本へ割る必要が生じるため、親が実測した。

- `orchestrator/campaign/s8c_preregistration_evidence.py` に
  `_PERF_KEYS` / `_SOURCE_METRIC_KEYS` / `throughput` は **0 件**。
- 評価器が射影 module に要求するのは、同 file L2557-2564 の
  module 級代入 `{"_CRITIC_KEYS", "_DIAGNOSTIC_METRICS"}` と関数
  `{"apply_critic_feedback", "_validate_critic_projection", "validate_planner_payload"}` の実在だけで
  ある。**本改名はこのどれにも触れない。**
- `s8c_preregistration.py` の `_projection_module_identity()` (L1872-1906) が射影 module に対して
  行うのは、live bytes と登録 commit の blob の**同一性照合だけ**である。`_PERF_KEYS` は読まない。
- 過去に `DECIDER_VERSION` を動かした 9 commit は、すべて**条件の machine_checkable 昇格または
  証拠契約の変更**であり、射影 module 内の key 集合変更による bump の先例は 0 件。

**裁定: bump しない。次世代 freeze record も発行しない。** 本改名は判定器の受理集合・拒否理由・
射影された判定入力の意味のいずれも変えない。

### 1-2. ただし blob 同一性は変わる — これは開示する

`s8c_generation_projection.py` は `campaign_lock.py` L66 の `CONTRACT_LOADER_RELATIVE_PATHS` に
含まれ、`s8c_preregistration.py` L52 の `PROJECTION_MODULE_PATH` でもある。改名は同 file の
bytes を変えるため、**改名前 commit を指す既存の登録は、改名後の live code に対して
`projection-blob-mismatch` を返す**。

- **記録済みの測定は無効にならない (規律 7)。** 当時そのコードでその測定をした事実は変わらない。
- **新しい実走には新しい登録 commit が要る。** これは contract-loader path を触る全変更に共通の
  routine な帰結であり、本 wave が新設する制約ではない。
- 既存実走 (B-7 等) を改名後の checkout で再受理させる必要があるかは **本 wave の scope 外**とし、
  裁定パッケージへ返す。**pin は緩めない。**
- 実装子は改名を commit してから焦点走を行う。未 commit のままだと contract-loader path の
  drift で焦点走が赤になる。

### 1-3. `src/coder-spec.md` は改名しない (両レンズとも指摘していない)

段 2 プランは `src/coder-spec.md:137,147` を live copy に分類したが、**誤りである**。
同 file L126 の節見出しは `## 4. Measurement Results (旧設計の現行値記録)` で、直下 L128-131 に
「**本節は §7 と同じく旧設計 (D39 以前) で superseded。この throughput/abort/latency 値は現行運用で
coder に一切渡らない**」「本節は経緯記録として残す」と明記されている。
`docs/README.md` L117 も現役なのは §1-2 だけと書く。

**裁定: 歴史記録に分類し、改名しない。** 同節の `+692 ops/sec` という記述も当時のままにする。

## 2. レンズ A (正しさ境界) の裁定

| 所見 | 判定 | 裁定 |
|---|---|---|
| 1. `_PRE_T1311_ROLE_PAYLOAD_SHA256` の見落とし | **real** | **採用。** プランの「4 role の payload SHA を新値へ補正」を撤回する |
| 2. 事前登録・campaign lock の identity 閉包 | **real** | **採用 (開示として)。** 1-2 のとおり。bump はしない |
| 3. 恒真経路の列挙漏れ (`test_trial_registry.py:403`、`test_s8c_generation_projection.py:71`) | **real** | **採用。** 変異は producer 実走経路で確認する。2 fixture は保証範囲の注意事項へ書く |
| 4. schema v4 と旧 record の関係 | refuted (方針は支持) | 説明を consumer ごとに精密化する。プランの方針は維持 |
| 5. 共通 pin 4 種は変更不要 | refuted (プラン支持) | `ROLE_MANIFEST_SHA256` / `SCHEMA_SHA256` / `ROLE_IO_CONTRACTS` / `DEVELOPER_INSTRUCTION_TEMPLATE_SHA256` は据え置く |
| 6. brief の検索件数の一般化 | **real** | **採用。** 4 節で brief を訂正する |
| 7. ゲート定義変更は不要 | refuted | 値・判定式・閾値・照合規則は維持する |

## 3. レンズ B (射程と実効性) の裁定

| 所見 | 判定 | 裁定 |
|---|---|---|
| 1. T-305 相乗り論の不成立 | **real (理由について)** | **推論は採用して差し替える。結論は変えない** — 下記 3-1 |
| 2. v4 化は必要 | refuted (v4 維持) | 理由を「exact-key 契約の変更」として書く。report schema は v3 据え置き |
| 3. originless golden の縮小 | **real** | **採用。** レンズ A 所見 1 と同じ結論に独立到達している |
| 4. planner L17 と coder baseline の凍結説明は 3 種を超える | **real** | **採用。外す。** ユーザーの「本題の改名と読み替えだけ」に合致 |
| 5. `throughput_tps` の同名化に実害なし | refuted | `throughput_tps` を採用する |
| 6. brief の「v3 以前の record は旧名を持つ」が広すぎる | **real** | **採用。** decisions の文面を系列つきへ直す |
| 7. 焦点走 51 file は過大 | **real (一部採用)** | 下記 3-2 |
| 8. 「旧名 0 件だから行競合なし」の飛躍 | **real** | **採用。** 2 つの主張を分離する |
| 9. 親編集表の calibrator 例と D118 誤帰属 | **real** | **採用。** `test_codex_agents.py` を編集対象から外す。D118 決定 4 の帰属を訂正 |

### 3-1. T-305 を同一 wave に含める根拠を差し替える

レンズ B は正しい。`docs/phase3.md` L1530 の T-305 の再訪条件は
「現行研究実走のblockerとなり、成果物影響を特定できたとき」であって、
「同一ファイルを触る wave への相乗り」は **T-1008 固有**の条件である。親 brief (P1) の類推は誤り。

**ただし結論は変わらない。** 根拠を次へ差し替える。

- 本 wave のユーザー指示 (2026-09-16) が「裁定は択 (a) 採用で、正本は worklog entry 109 の
  [T-304] / [T-305] 本文。**両者は同一 wave で扱うと裁定文が指定している**」と明示している。
- これは D205 の棚卸し (2026-08-06) より後の、ユーザー本人の直接指示である。
- したがって T-305 は「後発の除外を親判断で覆した」のではなく、**ユーザーが再度名指しで指示した**。

**裁定: T-305 を scope に含める。ただし 3 種の drift だけを直し、それを超える説明変更はしない
(レンズ B 所見 4)。**

### 3-2. 焦点走の縮小

レンズ B の推奨から 2 件だけ外し方を変える。

- **外す (4 件):** `test_effort_levels.py`、`test_sort_swo_oracle.py`、`test_s6_sort_sweep.py`、
  `test_s8a_trigger_sweep.py`。いずれも reasoning policy・SWO・機械列挙が主題で、role metric 名への
  到達根拠が示されていない。
- **残す (レンズ B は外す側に挙げたが親は残す、2 件):**
  `test_update_acceptance_duration_ledger.py` と `test_acceptance_schedule_order.py`。
  本 wave は**所要台帳そのものを更新する**ため、updater と schedule 整合は変更面に直接触れる。
  実装が変わらないことは、その consumer を焦点走から外す理由にならない。
- 残りはプラン問い 8 のとおり。**5 分上限の断定はしない** — 台帳合計を wall と呼ばない (D1620)。

## 4. 親 brief の訂正 (DW-S01 の「親自身の実測とその一般化」)

1. brief 「差分に `throughput_ops_sec` は 0 件で、行は競合しない」→ **2 文へ分離する。**
   前半は実測、後半は推論であり、旧名を含まない schema 定数・pin・golden の hunk が近接しうる。
   **「行は競合しない」を撤回する。**
2. brief の B-7 の記述 → **「親の起動時点・列挙対象 path についての観測」**と限定する。
   閉包全体の非干渉保証にしない。
3. brief の編集面の表から **`test_codex_agents.py` を外す** (calibrator の正規入力の例)。
4. brief (P4) の「D118 決定 4 により意図的な独立二重定義」→ **D118 決定 4 は schema bump と換算影響の
   節であり、二重定義を決めた本文ではない。** 帰属を落とし、「二重定義は実在する」という実測だけを
   残す。
5. brief の編集面の件数は「行数」と「文字列出現数」が混在していた。producer L2021 は 1 行に 2 出現。
   **単位を明示する。**
6. brief から **`src/coder-spec.md` を外す** (1-3 のとおり歴史記録)。

## 5. plan v2 — 確定した編集単位

**新名: `throughput_tps`。値・換算・ゲートは一切変えない。**

| # | 編集面 | 担当 |
|---|---|---|
| 1 | `orchestrator/campaign/p3_autonomous_workload_trial.py` — 旧名 → 新名 (L147, 2005, 2021×2)、`SCHEMA_VERSION` v3→v4 | 実装子 |
| 2 | `orchestrator/campaign/s8c_generation_projection.py` — `_PERF_KEYS` / `_SOURCE_METRIC_KEYS` の旧名 → 新名、`ROLE_SCHEMA_VERSION` v3→v4 | 実装子 |
| 3 | `orchestrator/campaign/autonomous_trial_completeness.py` — 独立 `_PERF_KEYS` の旧名 → 新名、`_ROLE_SCHEMA_VERSION` v3→v4 | 実装子 |
| 4 | 上記 3 つに対応する独立期待値 test の更新 (`test_p3_autonomous_workload_trial.py`、`test_s8c_generation_projection.py`、`test_autonomous_trial_completeness.py`、`test_s8c_preregistration_predicates.py`、`test_s8c_schedule.py`) | 実装子 |
| 5 | `.claude/agents/*.md` 5 件 — 旧名 → 新名。加えて T-305 の drift **3 種だけ** | 実装子 |
| 6 | `orchestrator/codex_roles/review_ledger.py` — 5 role の `SOURCE_FILE_SHA256`、planner の `DESCRIPTION_SHA256` (description を変える場合のみ) | 実装子 |
| 7 | `orchestrator/tests/test_reflux_originless_compatibility.py` — **比較前射影を通過して比較まで残る leaf だけ**補正 (role source SHA、据え置かれない journal schema)。`_PRE_T1311_ROLE_PAYLOAD_SHA256` へ射影済みの payload SHA は触らない | 実装子 |
| 8 | `.codex/role-adapters/*.json` 5 件の再生成 | **親** (子は `.codex/**` へ書けない) |
| 9 | `docs/phase3-s4b-runbook.md`、`docs/phase3-s5-sort-runbook.md` の旧名 → 新名 | **親** (docs) |
| 10 | 所要台帳の add-only 更新 | **親** (焦点走の JUnit 実測後) |
| 11 | decisions / worklog fragment | **親** |

**変更しない:** `src/coder-spec.md` (歴史記録)、`test_codex_agents.py` L619 (calibrator の別契約)、
`ROLE_MANIFEST_SHA256` / `SCHEMA_SHA256` / `ROLE_IO_CONTRACTS` /
`DEVELOPER_INSTRUCTION_TEMPLATE_SHA256`、`REPORT_SCHEMA_VERSION` (v3 据え置き)、
`DECIDER_VERSION` (v9 据え置き)、`output/insights/**` と `docs/archive/**` の既存成果物。

**順序の制約:** 6 (pin 更新) より前に 8 (adapter 再生成) を行うと renderer が拒否する。
7 (golden 補正) は 1-6 の後でなければ確定できない。10 は焦点走の実測後。

## 6. 旧名成果物の読み方 (ユーザー指定の必須項目)

decisions fragment へ次を記録する。機構は足さない。

> role schema `p3-autonomous-workload-trial/v4` 以降は `throughput_tps` を使う。v3 以前の
> role payload に現れる `throughput_ops_sec` は**同じ transactions/sec** を表し、読み替えに
> 数値の乗除は伴わない。既存成果物は書き換えず、再検証には生成時のコード版と契約を用いる。
> role schema の系列と、据え置く report schema `p3-autonomous-workload-trial-report/v3` の系列は
> 別である。旧名を持つのは当該 metric object であり、すべての record がその field を持つ意味ではない。

## 7. 変異事前登録 (DW-M01、実装前に登録)

各変異は実装後に**赤理由が一つに絞れること**を親が確認する。絞れなければ登録を取り下げ、
実効 gate へ再照準する。**新しい gate・閾値は作らない。**

| ID | 位置 | 変異 | 期待する赤 | 単一理由性の根拠 |
|---|---|---|---|---|
| M1 | `s8c_generation_projection.py` `_PERF_KEYS` | 新名 → 旧名へ戻す (producer / completeness は新名のまま) | producer 実走経路が exact-key 照合で赤 | 同 file の exact-key 照合が最初に当たる層。前段に同じ入力を拒否する層はない |
| M2 | `autonomous_trial_completeness.py` `_PERF_KEYS` | 新名 → 旧名へ戻す | durable receipt の nested-key 照合で赤 | projection を通過した後に当たる独立再計算。局所 fixture が追従する経路は避け、**producer 実走 test で判定する** (レンズ A 所見 3) |
| M3 | `p3_autonomous_workload_trial.py` `SCHEMA_VERSION` | v4 → v3 のまま | projection の固定 literal 照合で赤 | 版 literal の照合は key 照合と別の行 |
| M4 | `review_ledger.py` `SOURCE_FILE_SHA256["planner-v4"]` | 旧 SHA のまま | role source drift 検査で赤 | `spec.py` の source hash 照合が唯一の層 |
| M5 | `test_reflux_originless_compatibility.py` の補正した leaf | 補正前の値へ戻す | 凍結 baseline 比較で赤 | 比較前射影を通過して残る leaf に限定済み |

**登録しない変異:** `test_trial_registry.py` / `test_s8c_generation_projection.py` の fixture 経由の
片側変異。期待値が被検査対象から導かれるため恒真であり、DW-M01 の単一理由性を満たさない
(レンズ A 所見 3 が摘出)。この 2 経路は保証範囲の注意事項として insight に書く。

## 8. 裁定パッケージへ返すもの (本 wave では実装しない)

1. **既存実走 (B-7 等) を改名後の checkout で再受理させる必要があるかと、その手順。**
   改名は contract-loader path の blob を変えるため、改名前 commit を指す登録は
   `projection-blob-mismatch` になる。記録済み測定は無効化しない (規律 7) が、
   新しい実走には新しい登録 commit が要る。**pin の緩和は提案しない。**
2. **T-305 の 3 種を超える記述の是正** (planner の世代間凍結の説明、coder baseline の全世代凍結の
   説明)。実装と説明の食い違いは実在するが、裁定 (109) の 3 種に含まれない。
