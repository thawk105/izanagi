# 段 1 brief — [T-244] 8c 結線の前提設計 (実装しない)

**wave:** `dev-wave-t244-8c-wiring-design` / branch `worktree-dev-wave-t244-8c-wiring-design`
(base `c9990bc2`) / worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-8c-wiring-design`

## scope

U-10 批准後に**唯一起票できる設計 wave** (`output/insights/2026-08-06_t244-u10-budget-values/README.md`
§7 の順序 2)。次の 5 点の**前提設計だけ**を書く。コード・テスト・機械設定は 1 行も書かない。

1. **source closure** — cell 同一性 (`cell_key`) の閉包: referent 集合とその実在・一致検査。
2. **V-2 の exact 化** — 物理実行点で trusted harness が create-only の result-evidence record を
   発行する schema と outcome 対応、issuer、formal consumer (U-10 批准の乙方向)。
3. **32 mask producer topology** — P6 validation sweep を batch / iteration / query ordinal へ
   割り付ける形。
4. **origin binding capability** — launch admission が発行する束縛 (8c V-4 裁定 (b))。
5. **失敗・crash の event 対応と receipt 喪失照合** (8c V-5)。

## 確定済みユーザー裁定 (前提。動かさない)

- **8c V-1〜V-5 = 推奨どおり** (2026-08-06、decisions §33)。V-1 = (c) 設計メモに留める、
  V-2 = U-10 と同じ裁定面、V-3 = (a) 同一 wire を R 回、V-4 = (b) launch admission 発行の
  capability、V-5 = 配線の前提として設計する。
- **U-10 = 批准済み** (decisions §34)。`imax=4 / qmax=68 / kmax=1 / 行数下限 2 / 候補下限 1 /
  floor=(1, 32, R=1, E_min=0)`、`F=33`。**実発行は「V-2 evidence 正本 + producer topology +
  許可実行経路」の 3 条件成立後の人間承認 provisioning**。それまで本番 authority は entry 0。
- **D201** = 8c への結線は実装しない。**D183** = 本番 authority は空のまま。**D114** = cap 1。
  **D205** = アカデミアのプロトタイプ基準。**D211** = repo 内 ever-issued 台帳は作らない。

## 不変条件

- certified 選択・材料レポート・試行台帳・proof chain の現在値と参照はすべて不変。
- 本番 authority (`orchestrator/campaign/reflux_origin_authority_v2.json`、71 bytes、
  sha256 `76fb551f…`、origins 0 件) を 1 byte も変えない。
- `docs/phase3-8b-descriptor-design.md` は holdout freeze の `design_source` に pin されている
  (`s8b_holdout_freeze.py:30,552,709`)。**触らない**。
- 実装面ゼロ = 段 5・6 は対象外、変異 matrix と受入全走も対象外 (`DW-S04`)。
- 設計は「発行 3 条件」を満たすための材料であって、結線の許可ではない。

## 段 1 で実測した前提 (現 HEAD `c9990bc2` の worktree、`probe_premises.py`)

- 批准値は現 parser を通る。`F=33`、codec feasibility = origin 75,206 / head-tx 30,753 bytes
  (u10 wave の `verification.md` §1 と一致)。`batch_count = min(imax, qmax // 2) = 4`。
  `_MAX_BATCH_MEMBER_ROW_COUNT = 2248`。
- `batch_member_row_count_min` は parser が `minimum=2` を課す (`reflux_origin_ledger.py:320`)。
- outcome 受理表 (実測 8 例): `accepted` は evidence 必須・constraint 禁止、`rejected` は
  evidence + constraint 必須、`tombstoned` は evidence 禁止、他の語は拒否。
  tombstone は batch 内で終端 suffix でなければならない (`:1515`)。
- `derive_cell_key` = sha256(domain + [workload.descriptor_sha256, axis_semantics_sha256,
  verifier_policy_sha256, environment_contract_sha256]) の 4 要素 (`:485`)。
- event は `BatchReserved / BatchReservationAbandoned / BatchCommitted / BatchResultsPrepared /
  BatchSealed / OriginSealed` の 6 種。phase は
  `IDLE → BATCH_RESERVED → BATCH_COMMITTED → RESULTS_PREPARED → IDLE → ORIGIN_SEALED`。
- 再送は `(origin_id, operation_id, base_state_commitment, event payload)` 一致で冪等
  (`_same_committed_request`)、`EventReceipt.replayed` で区別。不完全 tail は replay 時に truncate。
- 公開 API (`read_origin` / `commit_event` / `read_sealed_batch`) は `_production_store()` 固定。
  fixture store は private (`_fixture_store_for_test`)。
- launch admission は `TrialLaunchAdmission` (sealed、`binding: TrialBinding | None`、
  `assert_issued_trial_launch_admission` / `assert_rederived_launch_admission` /
  `launch_admission_record`) として実在する。
- 32 mask の正準集合は `emit_predicate(TriggerGateIR(mask)) for mask in range(32)`
  (`trigger_gate_binding.py:99`)。

## 成果物の形

- `docs/phase3-8c-wiring-design.md` (新規) — 5 点の設計本文。docs 予算 (`check_docs.py`) は
  command / reference / skill / provenance 族にだけ掛かり、本ファイルは対象外 (実測)。
- `output/insights/2026-08-07_t244-8c-wiring-design/` — brief・plan・敵対 2 本・裁定の逐語凍結。
- `docs/spool/` fragment (worklog 1、必要なら decisions 1)。canonical 台帳は段 9 の land が畳む。

## 親の provisional 裁定 (`(P1)`〜`(P6)`。**攻撃対象**)

- **(P1) source closure** = `cell_key` の 4 referent それぞれに「どの producer のどの bytes か」を
  対応づけ、発行時に実在と digest 一致を検査する closure record を設計する。**series 横断の
  再利用検査は設計しない** (D211 で repo 内台帳は不可と裁定済み)。閉包は 1 authority series 内に限る。
  — 書かないと `cell_key` が「同じ細胞」を指す根拠が prose だけになり、材料レポートの
  cell 参照が別条件の測定を同一視しうる。
- **(P2) V-2** = 物理実行点の trusted harness が create-only の result-evidence record を発行し、
  seal 直前の builder がそれだけを読んで member を組む。outcome 対応は上の実測表に一致させる。
  — 決めないと配線しても書けるのは tombstone だけで `sealed_queries` は 0 のまま、材料レポートが
  「oracle query 1 回」と誤参照すれば証拠の意味が反転する。
- **(P3) topology** = P6 の 32 mask sweep を producer にすると 1 batch = 複数 mask 行になるため
  行数下限 2 が自然に満たされ、V-3 (1 generation = 1 drive) の不整合は**探索側 (8c) にだけ残る**。
  33 行 (base 1 + 32 mask × R=1) を 4 batch 以下へ割る形を決める。
  — 決めないと `Imax` / `Qmax` の批准値が指す対象が定まらず、topology 確定時に再批准になる。
- **(P4) binding** = launch admission が sealed capability を発行し、ledger client は capability
  なしでは動かない。fixture 経路では本番既定解決を拒否する。
  — (a) の素 dataclass だと別 campaign の予算を消費でき、`report.json.launch_admission` と
  ledger の `iterations_used` が別 origin を指して台帳とレポートの参照が分裂する。
- **(P5) 失敗・crash** = 失敗モードを既存 6 event へ写す表を作り、receipt 喪失は
  `operation_id` 再送 + `state_commitment` CAS + `replayed` で照合する。新 event は足さない。
  — 未設計だと crash した origin が I/Q を消費したまま `BATCH_COMMITTED` /
  `RESULTS_PREPARED` に留まり、新規予約と `OriginSealed` の受理集合から永久に外れる。
- **(P6) 置き場** = 設計本文は `docs/` の新規 1 ファイル、逐語は insights。
  — 誤ると pin 済み文書を汚すか、正本が insights に埋もれて次 wave が引けない。

## 分割方針

- 段 2: codex read-only 1 本 (5 点の設計起草、file:line 粒度)。
- 段 3: codex read-only 2 本並列 (レンズ A = 正しさ境界と恒真化、レンズ B = 受理集合・順序・
  既定経路・親 brief と実測値の一般化)。
- 段 5・6 なし (実装面ゼロ)。段 4 の裁定後に親が docs を書く。
