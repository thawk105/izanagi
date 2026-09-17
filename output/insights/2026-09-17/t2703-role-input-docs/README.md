# [T-2703][T-2717][T-2705] 役割入力文書を実配線へ合わせ、適用版を明示し、source pin を追随した

authority: none
default_effect: no-state-change

D2104 項 4 (第 20 回 /rulings 全件、main 着地済み) の実施。統合 commit は `dd6d0466e` (docs 7 file +
review ledger + originless baseline + adapter 4 本の 1 commit、Codex author / reviewer と親 integrator の trailer)。
設計判断は同 wave の decisions fragment (`docs/spool/decisions/2026-09-17-dev-wave-t2703-role-input-docs-1.md`、
land 時に採番) に置く。段ごとの逐語は `verbatim/`。

## 何を直したか (実配線との一致)

| 文書 | 食い違い (改訂前) | 一致させた現物 |
|---|---|---|
| `src/coder-leakproof-context.md` Measurement Setup | 1m records / 48 threads / extime 3 / 3 runs 中央値 (旧文の 1m / 48 / 3 は S2 verify 構成の値だった) | bench = `p3_s4_loop.default_perf()` (100k / 4 / skew 0.9 / rr 50 / rmw false / extime 1 / reps 2、3 driver 共通)。verify = 段 4b は legacy `CorrectnessWorkload` (200 records / 4 threads / rmw / max_ope 5 / extime 1 / 1 rep)、sort / trigger-gating は `VERIFY_LEGACY_PLUS_S2` でさらに S2 構成 (1m / 48 / extime 3) の pass。throughput = 有効 rep の `statistics.median` (2 rep は算術平均、`calibrator/analyze.py`)。build は trace 版 / perf 版の 2 本 |
| `.claude/agents/critic.md` L14 / L26 / L27 / L36 | latency を独立指標として列挙・帰属例に使用 | `orchestrator/critic/digest.py` `INDICATORS = [throughput_tps, abort_rate, llc_miss_rate, ipc]`。`latency[ns] = 1e9 × thread_num / throughput` (`external/ccbench/common/result.cc`) の恒等変換を注記。帰属例は待機コストを候補仮説に改め、uncertainty へ残す形にした (段 6 レビュー A must-fix 2) |
| `.claude/agents/critic-experiment.md` L36-38 | 同上 (online digest も `digest.build_digest` / `render_text` を共有) | 同上 |
| `.claude/agents/planner-v4.md` L17 + 入力節 | 「現行測定値」 | 8c 自動 trial: `_INITIAL_ROLE_METRICS` (数値指標は全 None) を workload ごとに 1 回 `_role_metric_payloads` へ通して凍結、`_planner_current_perf_payload` は世代更新値を捨てる (D410 決定 1)。第 2 世代以降は `critic_feedback` (D410 決定 2) も届く。手動 runbook はメインセッションが毎 iteration 射影 |
| `.claude/agents/coder-v4-autonomous-trigger-gating.md` L62-63 | 「baseline は本ループ自身の直近実測」 | 8c では `_coder_baseline_payload` が凍結 snapshot を返す。手動 runbook (段 8a) はメインセッションが射影 |
| `docs/phase3-s4b-runbook.md` L52 / `docs/phase3-s5-sort-runbook.md` L44 | 射影 JSON に `last_delta_pct: null` (実装 0 件、planner 例からは T-304 (4c6f03048) で除去済み) | 除去。適用版 (2026-09-17 改訂以降に開始する走行) と非遡及 (K0 / K1 / B-4、T-2588 の K2 走行を含むそれ以前の走行) を明記 |

各文書に「適用版: 2026-09-17 改訂以降に開始する走行。それ以前に開始した走行の入力は当時の版であり読み替えない」を置いた。
leakproof 文書 (coder LLM へ inline) には実験アーム名・裁定番号・命令形を置かず、`default_perf()` は file 名を伴う
参照として残した (段 4 裁定 A4 の例外、焦点再レビュー nit 3 で partial と判定された記録側の残件はこの 1 文で閉じる)。

## 前提の訂正 (親 brief の誤り、段 3 / 段 6 で覆った)

- **「docs (.md) のみ、実装差分ゼロ」は文字どおりには成立しない。** 4 role .md の bytes は
  `orchestrator/codex_roles/review_ledger.py` `SOURCE_FILE_SHA256`、`.codex/role-adapters/<role>.json`
  (`source_file_sha256` / `source.sha256` / `semantic_digest` / `developer_instructions`)、
  `orchestrator/tests/test_reflux_originless_compatibility.py` の originless baseline (planner・critic・coder =
  trigger-gating、journal 6 行 + report 1 行ずつ) に pin される。D118 残余 (b) が明記する帰結であり、
  同型先例 T-2528 (D1936 項 23 / 25) と同じく Codex author が ledger + baseline を追随し、親が既存 renderer で
  adapter を再生成した (他 10 本不変)。「実装差分ゼロ」は「schema・検査規則・受理述語・runtime 挙動の差分ゼロ」と読む。
- **pin の第 4 機構 (段 3 レンズ A):** `p3_b4_closed_critic.py` は B-4 receipt 再読で `critic.md` の live bytes と
  projection 閉包を照合し、`p3_b4_raw_record_producer.py` も同じ snapshot 照合を持つ。再受理対象の B-4 receipt は
  repo 内 `output/` の `role_file_sha256` 全数検索で未発見 (hit は test dispatch receipt と selector-8b の凍結記録だけ)、
  B-4 事前登録 §5 は prompt / projection hash 欄が未記入 (他欄は一部記入済み)。旧 sha は
  `output/insights/2026-08-26/t1697-closed-critic-invocation/verbatim/` の実 CLI provenance に歴史記録として残る。
  repo 外・未追跡成果物までの不在は主張しない。
- **手動 runbook の baseline を「毎 iteration 同じ値」とは書けない (段 3 両レンズ):** T-2588 の K2 手動 loop は
  2 周目の `current_perf` に 1 周目の実測 (`materials/planner-input-2.json`) を入れていた。runbook の `<baseline>` は
  固定規定ではないので、凍結の記述は 8c 自動 trial に限定し、runbook へ凍結規則を新設しなかった。
- **verify の一般化 (段 3 レンズ B):** 段 4b は legacy のみだが sort / trigger-gating は legacy + S2。文書は軸別に書いた。
- **8c で世代を跨いで届くのは whiteboard だけではない (段 6 レビュー A must-fix 1):** 第 2 世代以降の planner は
  `critic_feedback` も受け取る (`ROLE_PAYLOAD_KEY_SPEC["planner-generation-next"]`)。coder には届かない。

## 棄却した所見 (refuted)

- perf preflight receipt が PerfConfig を差し替える (レンズ B): `use_perf_from_receipt` は perf counter の可否だけを返す。
- reject 世代が凍結 baseline を上書きする (レンズ B): 凍結 snapshot は世代ループの外で 1 回だけ作られる。
- schema / manifest / template pin が動く (両レンズ): manifest entry に本文 sha は入らない。`ROLE_MANIFEST_SHA256`・
  `DEVELOPER_INSTRUCTION_TEMPLATE_SHA256`・`ROLE_IO_CONTRACTS`・`_PERF_KEYS`・schema_version は不変。
- hardware 行の削除・critic-experiment・trigger-gating の編集が scope 外 (レンズ A): いずれも名指しの Measurement Setup 内、
  T-2717 の名指し、「coder の凍結表現」の直接対象。

## 検査 (親の実測)

| 検査 | 実測 |
|---|---|
| 焦点走 focus1 (統合後、fix 前、15 file、Pegasus 2759.nqsv) | 2084 passed / 5 skipped / child rc=0、137 s |
| 焦点走 focus2 (`-rs`、2799.nqsv) | 走行中に親が docs を編集したため 8 failed (adapter parity drift、自傷)。合否には使わず skip 理由の参考のみ |
| **焦点走 focus3 (fix + render 後、`-rs`、2837.nqsv、権威)** | **2084 passed / 5 skipped / child rc=0、135 s**。skip 5 件は環境 skip (bundled Codex/bwrap/busybox 不在 ×3、pinned Codex runtime 不在 ×1、template patch 未適用の条件付き未実走 ×1)。growth hold なし |
| `tools/check_codex_agents.py` | ledger 更新前 rc=1 (`reviewed SOURCE_FILE_SHA256 drift`)、ledger 更新 + render 後 rc=0 (0 native / 14 static dormant) |
| `tools/check_docs.py` | 違反なし (docs 編集後・fix 後の 2 回) |
| `git diff --check` | rc=0 |
| 三軸語・placeholder 走査 (`s8b_holdout_freeze search`) | rc=0 (hit なし) |
| commit trailer preflight (`check_ai_provenance.py --message-file`) | 1 件、違反なし |

焦点走の 15 file: test_codex_agents / test_codex_role_runtime / test_reflux_originless_compatibility /
test_p3_autonomous_workload_trial / test_autonomous_trial_completeness / test_p3_b4_closed_critic /
test_p3_b4_raw_record_producer / test_claude_transport / test_role_session_isolation /
test_s8c_preregistration_predicates / test_s8c_schedule / test_effort_levels / test_hooks / test_p3_s4_loop /
test_s8c_generation_projection (plan の 14 + レンズ A 推奨の raw record producer)。

## 変異 matrix

事前登録は `verbatim/s4-ruling.md` の表。container worktree `.codex/worktrees/t2703-mutcontainer` (実装 commit
`dd6d0466e` の使い捨て detached worktree、submodule 初期化済み) で `tools/mutation_harness.py --runner-mode dispatch
--detached`、runner は `python3 tools/run_tests.py test_reflux_originless_compatibility.py test_codex_agents.py -q -rf
--force-dispatch`、D612 の queue-wait / grace 上書き 1800 / 600。spec と台帳は本 dir の `mutation-spec-probe.json`
(sha256 `b9fa4a17…`) / `mutation-ledger-probe.json`、`mutation-spec-final.json` (sha256 `f5e63268…`) /
`mutation-ledger-final.json`。

- probe 走 (全件 SURVIVED 登録、観測 node を集める): baseline PASSED (48 passed 15.2 s)、M0 SURVIVED、M1 / M1a / M1b /
  M1c は全部 MISMATCH (= 赤 node を観測)。観測 node を本走 spec の `expected_nodes` へそのまま写した。
- **本走: baseline PASSED (48 passed 15.3 s)、負例 4 件 (M1 呼出し除去 / M1a planner / M1b critic / M1c coder のタプル除去)
  すべて KILLED で期待 node と観測 node が完全一致 (`test_reflux_originless_compatibility.py::test_originless_default_preserves_every_nonvolatile_leaf_and_closed_key_set`、
  matching 5/5)、等価変異 M0 (Reviewed コメント文言だけ) は SURVIVED、MISMATCH 0、TIMEOUT 0、harness rc=0。**
  M1 は「追随 helper の呼出し欠落」を一理由として検出し、M1a / M1b / M1c は 3 role の追随が個別に load-bearing で
  あることを示す (どれか 1 role の old sha が baseline に残るだけで同じ比較が失敗する)。対照 node
  `test_originless_harness_rebuild_is_deterministic_control` は現行出力同士の比較なので全変異で PASS のまま。
- **M2 (ledger の critic sha を旧 `cd1c3652…` へ戻す) は harness 外の login probe** (`verbatim/mutation-m2-login-probe.txt`):
  `tools/check_codex_agents.py` rc=1 (`reviewed SOURCE_FILE_SHA256 drift; ledger明示更新が必要`)、
  `pytest --collect-only test_codex_agents.py` rc=2 (errors=1 / failed=0 = collection error、個別 node に到達しない)。
  anchor 1 箇所、即時復元後 sha 一致・status clean、無変異対照 rc=0。harness の KILLED には数えない (失敗 node 0 件 +
  rc≠0 は PARSE_ERROR 停止) — 既存の一般 source pin 検査による拒否として記録する。
- 役割本文の**意味**を独立に pin する semantic 防壁は新設していない (D1936 項 24)。例・ledger・baseline・adapter の
  全 surface を協調して書き換える主体への防壁が無いことは D1860 の既知の限界のまま。

## verbatim の可逆正規化 (DW-S07)

`verbatim/` の 6 file (plan / 敵対相談 2 / レビュー 2 / focus3 log) は codex の出力の行末空白 (markdown の強制改行) が
`git diff --check` に抵触したため、行末の空白だけを除去した (可視文字不変)。原文 sha256・byte 数・除去 byte 数・復元法は
`verbatim-normalization.json` (path は `output/` 相対) に記録し、原文は wave の job directory に保持する。

## 工数

codex 子 8 本 (plan 1、consult 2、author 1、review 2、fix 1、focus 1、全段 `gpt-6-astra` / `medium`、全件 accepted)。
親の実測は焦点走 3 本 (計算ノード)、checker、render、変異 2 走 (probe 6 request + 本走 6 request、計算ノード)、
M2 login probe 1 本。受入全走は記録 commit 後に 1 回投入する (本 README 作成時点では未実施)。
