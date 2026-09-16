# [T-304] / [T-305] — throughput_ops_sec を実体名へ改め、live role 定義の記述 drift 3 種を直す

本 wave の一次資料。裁定は `s4-adjudication.md`、段 1 brief は `brief.md`。
変異の spec と台帳は本 directory の `mutation-spec.*.json` / `mutation-ledger.*.json`。

## 何を直したか

`throughput_ops_sec` の実体は transactions/sec である。producer の源値は
`outcome["fitness_tps"]`、その源は `pipeline.py` の `bench.median_tps`、CCBench 側は
`common/result.cc` の `throughput[tps]`。YCSB 既定 `ycsb_max_ope=10` (`include/ycsb.hh`) の下で
名前どおり operations/sec と読むと名目 10 倍ずれる。**値は正しく名前だけが誤りであった。**

新名は `throughput_tps`。role schema は `p3-autonomous-workload-trial/v4` へ上げ、report schema は
v3 のまま据え置いた。設計判断の正本は decisions fragment
(`docs/spool/decisions/2026-09-16-dev-wave-t304-throughput-rename-2.md`)。

## 変異 matrix

`mutation-spec.final.json` (5 変異) を `tools/mutation_harness.py` で走らせた。
runner は `python3 tools/run_tests.py --force-dispatch -rf` に `-k` で designated gate 4 本を選び、
`test_s8c_generation_projection.py` / `test_p3_autonomous_workload_trial.py` /
`test_codex_agents.py` / `test_reflux_originless_compatibility.py` を対象とした。

| ID | 位置 | 変異 | 結果 |
|---|---|---|---|
| M1 | `s8c_generation_projection.py` `_PERF_KEYS` | 新名 → 旧名 | KILLED (3 node) |
| M2 | `autonomous_trial_completeness.py` 独立 `_PERF_KEYS` | 新名 → 旧名 | KILLED (2 node) |
| M3 | `p3_autonomous_workload_trial.py` `SCHEMA_VERSION` | v4 → v3 | KILLED (2 node) |
| M4 | `.codex/role-adapters/planner-v4.json` の source sha256 | 新 → 旧 | KILLED (1 node) |
| M5 | `test_reflux_originless_compatibility.py` の golden 補正 | 呼出しを削除 | KILLED (1 node) |

### 保証の射程 (主張しないこと)

- **`test_reflux_originless_compatibility.py` の凍結 golden は M1 / M2 / M3 に対して冗長 gate である。**
  payload bytes が変われば発火するので、意味の gate とは別に数える。単独変異の証拠としては
  M1 は projection の exact-key 検査、M2 / M3 は producer 実走経路を読む。
- **期待値が被検査対象から導かれる恒真経路が 3 つ実在する** (段 3 レンズ A が摘出)。
  `test_trial_registry.py` の receipt fixture は `completeness._PERF_KEYS` から、
  `test_s8c_generation_projection.py` の fixture は `P.ROLE_SCHEMA_VERSION` から、
  `test_autonomous_trial_completeness.py` の fixture は `C._PERF_KEYS` から期待値を作る。
  **これらの局所テストだけでは片側 drift を検出できない。** 本 matrix は producer 実走経路を
  通す node を選んでこれを避けた。
- 変異が覆うのは改名と schema 版の同期だけであり、`throughput_tps` という**名前が実体と
  合っていること自体**は変異では示せない。それは一次資料の読解 (CCBench の `throughput[tps]` と
  `ycsb_max_ope`) が根拠である。

## erratum — 変異 spec を 2 度組み直した

`DW-M02` に従い、初回の結果を消さずに残す。

1. **`mutation-ledger.probe.json` (attempt 1)。** 焦点走と同じ広い対象集合で走らせたところ、
   kill 集合が M1=153 / M2=70 / M3=214 node になり、失敗行の中継上限に当たった。
   `M4` は `PARSE_ERROR`、`M5` は記録に到達しなかった。
2. **`mutation-ledger.probe2.json` (attempt 2)。** designated gate 4 本へ `-k` で絞り、
   kill 集合は 1〜3 node に縮んだ。しかし `M4` は依然 `PARSE_ERROR` だった。
   原因は中継上限ではない — **`review_ledger.py` の source pin を旧値へ戻すと
   `orchestrator/codex_roles/spec.py` が module import 時に `RoleSpecError` を上げ、
   `test_codex_agents.py` が collection 段階で 48 件の error になる。**
   node 抽出は `FAILED` 行から test node ID を取るので、file 級の collection error からは
   1 件も取れない。
3. **`mutation-ledger.probe3.json` (attempt 3)。** 同じ pin 閉包を **adapter 側の source sha256**
   で突く形へ差し替え (2026-09-09 の T-2249 wave と同型)、5/5 が観測できた。
   `mutation-spec.final.json` はこの観測 node を完全集合として登録したものである。

**ledger pin を直接戻す経路が gate を通ること自体は、上記 2 の 48 件の collection error
(`reviewed SOURCE_FILE_SHA256 drift; ledger明示更新が必要`) が示している。**
matrix へ載せないのは検出力の不足ではなく、node 抽出がこの形を表現できないためである。

## 親が段 3 / 段 6 の外で実測したこと

- **`DECIDER_VERSION` の bump は不要。** `s8c_preregistration_evidence.py` に
  `_PERF_KEYS` / `_SOURCE_METRIC_KEYS` / `throughput` は 0 件。評価器が射影 module へ要求するのは
  module 級代入 `_CRITIC_KEYS` / `_DIAGNOSTIC_METRICS` と関数 `apply_critic_feedback` /
  `_validate_critic_projection` / `validate_planner_payload` の実在だけである。
  `_projection_module_identity()` は blob 同一性しか見ない。過去 9 回の bump はすべて条件の
  machine_checkable 昇格または証拠契約の変更だった。
- **`src/coder-spec.md` §4 は歴史記録。** 本文 L128-131 が「旧設計 (D39 以前) で superseded」
  「現行運用で coder に一切渡らない」「経緯記録として残す」と自ら宣言している。改名しない。
- **編集面の重複 (wave 起動時)。** 全 worktree を対象 path に絞って走査し、未 commit の実質衝突は
  `.codex/worktrees/t2293-impl` の 1 件だけだった。その差分に旧名は 0 件である。
  **「旧名 0 件」は実測であり、「行が競合しない」はそこから導けない推論なので主張しない。**
  他の 7 worktree の未 commit は `acceptance_duration_ledger.json` だけだった。

## 実測

- 焦点走: 2608 passed / 9 skipped / 0 failed (110.77 秒、Pegasus request `792.nqsv`)。
- 受入全走: 23966 passed / 68 skipped / 0 failed (24034 collected、3 shard、login node の loadgroup scheduler、verdict = child-green、tested_main da3812e7c、tested_tip b93fba877)
- `tools/check_codex_agents.py` rc=0、`tools/check_ai_provenance.py` 全史 rc=0。
