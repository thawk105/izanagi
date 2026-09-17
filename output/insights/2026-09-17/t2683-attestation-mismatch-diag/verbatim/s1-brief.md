## 段 1 brief (2026-09-17)

**研究前進 (土台):** T126 資格判定 (certified 選択の evidence 経路) が Pegasus 計算ノードで attestation 不一致に終わると、どの field がどの値で食い違ったかが成果物に残らず (D2052 は login node の 6 field 正当 fail を実測 wrapper でしか見られなかった)、再現・原因判定に生 log が要る。最小差分 = 失敗した子が attempt dir に診断 sidecar を 1 つ書く。完了判定 = 正例 (1 field 不一致 → sidecar に当該行が verdict≠pass で載る) と負例 (一致 → sidecar 不在、accepted payload bytes 不変) が test と変異で立つ。

**scope (実アンカー表):**
| file | anchor | 変更 |
|---|---|---|
| `orchestrator/qualification/t126_driver.py` | `_attest` L449-475 | 不一致時に比較行を持つ typed 例外 (`QualificationDriverError` の subclass、既存 `match="comparison contains a mismatch"` と型を維持) |
| 同 | `run()` 内 `attest` closure L1191-1261 の子側 (`_attest` → `create_json` → `os._exit`) | 不一致時だけ `{prefix}/attestation/{stage}-{n}.mismatch.json` を `create_json` で 1 つ書いてから `os._exit(RC_ATTESTATION)`。子側処理は module-level helper に抽出して fork なしで test 可能にする |
| 同 | 親側 L1242-1243 `AttestationError("attestation child rejected")` | sidecar が実在すれば message に相対 path と failed field 名を含める (`run_series` の reject payload key 集合 stage/type/message は不変) |
| `orchestrator/tests/test_t126_qualification_driver.py` | `_attest_fixture` L270 以降 | 正例・負例・sidecar 形の test を追加 |
| `orchestrator/campaign/execution_guard.py` | L612-624 | **変更なし** (P1) |

**確定済みユーザー裁定:** 第 20 回 /rulings 項 14 (規律 3 の射程、局所修正、新 gate なし、受理集合不変)、項 15 (成功時の receipt は書かない → 一致時は sidecar を書かない)。Codex author (D95) + 変異事前登録。仮想リスク向けの gate・検査・台帳は scope 外。

**brief 前の実測で覆った前提 → 段 4 で再裁定:**
- (P1) `execution_guard.py:612` は比較行を捨てていない: `failures` (非 pass 行) を `json.dumps` で例外 message に載せている (commit 950757e20a、2026-07-19)。production 呼び手 4 本 (`loop.py:187`、`s8b_oracle_driver.py:968/1147`、`screening_driver.py:336`、`s8b_floor_campaign.py:7379`) は `str(exc)` を伝播。floor campaign は失敗時副作用ゼロを `test_required_attestation_comparison_failure_has_zero_side_effects` で pin → file sidecar は既存 pin と衝突。**親の provisional 裁定: execution_guard は既存策で足りる、変更なし。** 例外に構造化属性を足す案は consumer が無く恒真 (DW-G05) なので採らない。
- (P2) sidecar の内容 = accepted payload と同形 (`schema_version` 新値、`status: "rejected"`、stage、round_index、expected/observed profile sha256、projection schema、`comparisons` 全行) + `failed_fields`。全行を載せる (規律 3: なぜ壊れたかの全体像)。
- (P3) sidecar の書込み失敗で rc を変えない (D474)。既存の `except BaseException: os._exit(RC_ATTESTATION)` の内側で書く。
- (P4) `_attest` の `not comparisons` (空) 分岐も同じ typed 例外で sidecar を書く (`comparisons: []`)。probe 例外 (`attestation failed: ...`) は比較行が無いので sidecar なし (現行のまま)。

**不変条件:** (a) 受理集合不変 — 不一致は依然 reject・rc=RC_ATTESTATION=31・`fsm.reject("attestation", ...)` の key 集合不変。(b) 一致時は sidecar を書かず accepted payload の bytes 不変 (test_t541 系の 21 field 完全一致を維持)。(c) 新しい gate・validator・schema file (`validate_json_schema` 登録) を足さない。(d) `execution_guard.py` の bytes 不変。(e) `verify()` と成功 series の evidence_manifest は非接触 (sidecar は失敗 attempt にしか存在しない)。(f) V2_ENV_NEUTRAL_MODULES (env literal 禁止) に触れない。

**凍結 pin 閉包 (DW-O09):** 両 file の現 sha256 は歴史 snapshot (`orchestrator/tests/fixtures/b10_backoff_shape_locks/*.lock` は lock bytes を固定 sha と比較、`output/insights/2026-08-24_paper-story-a1-paired/result.json`、`2026-08-27_t1769-b4-wiring-probe/*`、`2026-09-09/t2344-closure-reachability/trace-*.json`) にのみ出現、live 比較なし。構造 pin: `test_m10_driver_binds_prologue_observation_at_every_member_callsite` (validate_member_evidence 2 call)、`test_campaign.py:5526` (evaluate 1 call)、`test_qualification_entry_constructs_run_context_for_live_member_build` (文字列) — いずれも今回の変更面外。durable manifest の再発行は不要。

**受入・実測環境:** 焦点走は `python3 tools/run_tests.py <files>` (§7.0.0 自動判定)。変異 matrix は container worktree で `tools/mutation_harness.py`。受入全走は `tools/dev_wave_wait.py acceptance`。

**分割方針:** 実装面は 1 file + 1 test file → author 子 1 本。正しさ防壁 (attestation gate の reject 経路・identity file) に触るので軽量版でなく段 2 plan 1・段 3 consult 2・段 6 review 2 を回す。
