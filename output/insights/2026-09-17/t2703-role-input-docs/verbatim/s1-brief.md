# 段 1 brief — [T-2703][T-2717][T-2705] 役割入力文書の食い違いを実配線へ合わせて直す

wave: dev-wave-t2703-role-input-docs / worktree: /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2703-role-input-docs / base: main b4631a92e (clean)

## 研究前進 (土台)
役割文書は LLM 合成 (段 4 自律ループ・8c・K2・B-4) の**入力**である。coder に誤った workload 像 (1m/48 threads/3 runs) を、critic に digest に無い latency 列を、planner に「現行測定値」という凍結値の誤読を渡したまま走ると、論文 §段 4 / §8c の「leakproof 入力からの合成」の主張が「入力が実配線と一致していた」と言えなくなる。本 wave は入力文書 6 本を実配線 (現物コード) に一致させ、適用版を明示する。完了判定 = 各文書の記述が名指しの現物 (`p3_s4_loop.default_perf`、`critic/digest.INDICATORS`、`_PERF_KEYS`、`_planner_current_perf_payload` / `_coder_baseline_payload`) と一致し、pin 閉包 (review ledger / adapter / originless baseline) が緑で、受入全走が緑。

## 確定済みユーザー裁定 (D2104 項 4、main 着地済み)
- 直す対象: `src/coder-leakproof-context.md` Measurement Setup、critic 役割文書の latency 列挙、手動射影 runbook の `last_delta_pct`、planner / coder の凍結表現。
- 射程: 入力文書の**適用版を明示**し、凍結済みアーム (K0 / K1 / B-4) には遡及適用しない。
- role payload の schema は上げない。`latency_ns` key (D118 閉列挙) と代表 rep (偶数有効 reps で上側中央) は変えない。D2064 の版分けは誤引用 (schema 改版の根拠にしない)。
- gate・検査・台帳・汎用化の追加は scope 外。CCBench は改変しない。

## 実配線 (親が現物で確認した事実)
- bench: `p3_s4_loop.default_perf()` = records 100_000 / threads 4 / skew 0.9 / rr 50 / rmw false / (max_ope は CCBench 既定 10) / extime 1 / reps 2。verify は legacy `CorrectnessWorkload` (200 records / 4 threads / rmw true / max_ope 5 / extime 1 / 1 rep)。throughput は `statistics.median` (2 rep = 算術平均)。build は trace-enabled / trace-disabled の 2 本。
- critic digest: `orchestrator/critic/digest.py` `INDICATORS = [throughput_tps, abort_rate, llc_miss_rate, ipc]` — latency 列なし (T-2702、latency[ns] = 1e9 × threads / throughput の恒等変換)。critic-experiment の `online_digest` も同じ `digest.build_digest` / `render_text`。
- planner `current_perf` / coder `baseline`: 8c 自動 trial (`p3_autonomous_workload_trial.py`) は `_INITIAL_ROLE_METRICS` (全 key None) を workload ごとに 1 回凍結し全世代同一 (D410 決定 1、`_planner_current_perf_payload` / `_coder_baseline_payload` は generation-updated metrics を捨てる)。8c の coder role は `coder-v4-autonomous-trigger-gating` で、同文書は「baseline は本ループ自身の直近実測」と書く (誤り)。手動 runbook (段 4b / 段 5 sort) は `<baseline>` を毎 iteration 同じ値で射影する。
- `last_delta_pct`: 実装 0 件 (`_PERF_KEYS` にも planner-v4.md にも無い、T-304 で例から除去済み)。残るのは runbook 2 本の射影 JSON だけ。D1860 (「削除せず null」) の前提「planner 例に存在する」は T-304 以後は成立しない。
- 8c の `leakproof_context` は `s8c_generation_projection.LEAKPROOF_CONTEXT` の固定短文であり `src/coder-leakproof-context.md` は手動 runbook 経路 (段 4b / 段 5 sort / 段 8a) でだけ inline される。

## (P1) 親の provisional 裁定・攻撃対象 — 「docs (.md) のみ、実装差分ゼロ」の前提は成立しない
4 role .md (critic / critic-experiment / planner-v4 / coder-v4-autonomous-trigger-gating) の bytes は `orchestrator/codex_roles/review_ledger.py` `SOURCE_FILE_SHA256`、`.codex/role-adapters/<role>.json` (`source_file_sha256` / `source.sha256`)、`orchestrator/tests/test_reflux_originless_compatibility.py` の originless baseline (planner・critic・coder=trigger-gating の journal 6 行 + report 1 行) に pin される。D118 残余 (b) が「是正は review_ledger の source hash 更新と adapter 再生成を伴う」と明記し、同型の先例 T-2528 (D1936 項 23) は Codex author が ledger + baseline を追随し親が adapter を render した。**親裁定: 同じ形で進める。** schema・manifest・受理集合・runtime blocked は不変。「実装差分ゼロ」は「受理集合・schema・挙動の差分ゼロ」と読む。
(P2) `critic-experiment.md` (P2-5 誘導アーム、Phase 2 で実走済み) は裁定の名指し外だが T-2717 が名指す。記録済み結果は不変 (規律 7) なので直す。
(P3) leakproof の「hardware: 96 core × 2 NUMA」は `default_perf()` に無い機体固有事実。削除する (横断 docs にマシン密結合を持ち込まない)。
(P4) `coder-v4-autonomous.md` / `-sort.md` / `-k2.md` の baseline 記述は誤りを含まない (「本ループ自身の baseline」) ので触らない。凍結表現の是正は planner-v4.md と trigger-gating.md に限る。

## 不変条件
- role payload の key 集合・schema_version・`REPORT_SCHEMA_VERSION`・`DECIDER_VERSION` 不変。role の frontmatter (description / tools / model / effort) 不変 → `ROLE_MANIFEST_SHA256` 不変。
- 入力例 JSON の key 集合不変 (`tools/check_codex_agents.py` の shape parity)。planner 例へ `last_delta_pct` を戻さない。
- B-4 事前登録 §5 の projection / prompt hash は未記入のまま (記入済み値なし → 陳腐化なし)。B-4 受領証 0 件。
- 勝ち筋値・利得・機序を leakproof 文書へ足さない (規律 6 / D39 決定 7)。

## 変更面 (実アンカー)
| file | 箇所 | 変更 |
|---|---|---|
| `src/coder-leakproof-context.md` | L53-77 Measurement Setup / Methodology | 100k / t4 / extime1 / reps2 に合わせ、verify (legacy 1 rep) と中央値 (2 rep 平均) を書く。適用版 1 行 |
| `.claude/agents/critic.md` | L14, L26, L27, L36 | latency を独立指標から外し恒等変換を注記。適用版 1 行 |
| `.claude/agents/critic-experiment.md` | L36-38 | 同上 |
| `.claude/agents/planner-v4.md` | L17 (+入力節末尾) | 「現行測定値」→ campaign ごとに 1 回射影して以後更新しない凍結値 (8c は D410、現行初期値は全 null) |
| `.claude/agents/coder-v4-autonomous-trigger-gating.md` | L62-63 | 「直近実測」→ 世代を跨いで凍結 (D410) |
| `docs/phase3-s4b-runbook.md` L52 / `docs/phase3-s5-sort-runbook.md` L44 | 射影 JSON | `"last_delta_pct": null` を除く。適用版 1 行 |
| `orchestrator/codex_roles/review_ledger.py` | SOURCE_FILE_SHA256 4 件 | 新 sha + Reviewed 行 (Codex author) |
| `orchestrator/tests/test_reflux_originless_compatibility.py` | `_extend_t304_role_name_baseline` の後 | planner / critic / coder(trigger-gating) の old→new 追随 helper (Codex author) |
| `.codex/role-adapters/{critic,critic-experiment,planner-v4,coder-v4-autonomous-trigger-gating}.json` | render | 親が `expected_adapters()` で再生成 (D1861 integrator) |

## 成果物の形・分割
- docs 本文は親が編集。実装面 (ledger + compat baseline) は Codex author 1 本 (workspace-write)。adapter render は親。
- 変異 (実装面あり、免除なし): M1 = baseline 追随 helper 呼出し除去 → originless test 赤 (KILLED 期待)、M2 = ledger の 1 sha を旧値へ戻す → `test_codex_agents` 赤、M0 = ledger の Reviewed コメント行だけ変更 (等価、SURVIVED 期待)。
- 受入環境: 焦点走 + 受入全走は `tools/run_tests.py` (login node 自動判定、必要なら Pegasus dispatch)。
- 残件 (触らない): trigger-gating.md 入力例の `leakproof_context` が file inline と書くが 8c は固定短文 (別 drift)。critic 役割文書の frontmatter description は「throughput + leading indicators」で latency に触れず不変。
