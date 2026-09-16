---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-17
wave: dev-wave-t2703-role-input-docs
seq: 1
---

## {{D:role-input-docs-applied-version}}. 役割入力文書の訂正は適用版を文書自身に書き、凍結の記述は 8c 自動 trial に限り、runbook の `last_delta_pct` は D2104 に基づく後続訂正として除く

**決定 (1): 6 本の入力文書を実配線へ合わせ、各文書に「適用版: 2026-09-17 改訂以降の走行。それ以前に開始した走行の入力は当時の版であり読み替えない」を書く。** 対象は `src/coder-leakproof-context.md` (Measurement Setup を `p3_s4_loop.default_perf()` = 100k records / 4 threads / skew 0.9 / rr 50 / rmw false / extime 1 / reps 2 と、段 4b = legacy 小規模 verify 1 rep・sort / trigger-gating = さらに S2 pass、throughput = 有効 rep の中央値 (2 rep は算術平均) に一致)、`.claude/agents/critic.md` と `critic-experiment.md` (latency を独立指標から外し、`latency[ns] = 1e9 × thread_num / throughput` の恒等変換を注記、列は `orchestrator/critic/digest.py` の `INDICATORS` に一致)、`.claude/agents/planner-v4.md` と `coder-v4-autonomous-trigger-gating.md` (下の決定 2)、`docs/phase3-s4b-runbook.md` と `phase3-s5-sort-runbook.md` (下の決定 3)。D2104 項 4 の実施であり、role payload の schema_version・`_PERF_KEYS`・`latency_ns` key (D118 閉列挙)・代表 rep (偶数有効 reps で上側中央)・`REPORT_SCHEMA_VERSION`・`DECIDER_VERSION` は変えない。

**決定 (2): planner / coder の「凍結」の記述は 8c 自動 trial に限定し、手動 runbook 経路へ一般化しない。** 8c 自動 trial では `current_perf` / `leading_indicators` / `baseline` を workload ごとに初期 metrics 定数 (現行は数値指標がすべて `null`) から 1 回だけ射影して凍結し世代を跨いで更新しない (D410 決定 1)。手動 runbook (段 4b / 段 5 sort / 段 8a) ではメインセッションが runbook に従って射影する、とだけ書く。段 3 の敵対相談が、K2 の手動 loop 1 巡 (2026-09-16、insight `output/insights/2026-09-16/t2588-k2-loop-roundtrip/`) で 2 周目の `current_perf` に 1 周目の実測が入っていることを現物で示し、手動経路の「毎 iteration 同じ値」は規定でも実績でもないと反証したため、runbook へ凍結規則を新設しない (新しい運用規定の密輸になる)。

**決定 (3): runbook 2 本の射影 JSON から `last_delta_pct: null` を除く。これは D1860 (削除せず `null` へ揃える) の後続の限定訂正であり、D1860 当時の判断は保持する。** D1860 の根拠「`last_delta_pct` は planner 入力例に存在する field で、削除すると role と runbook が乖離する」は、D2064 の wave (2026-09-16、commit 4c6f03048) が planner 入力例から同 field を除去した時点で成立しなくなり、現在は runbook 側に残す方が role と乖離する。除去は D2104 項 4 が明示的に授権した範囲内で行い、凍結済みアームとそれ以前に開始した走行の記録 (`last_delta_pct: null` を含む射影) はそのまま保持する。

**決定 (4): 「実装差分ゼロ」は「schema・検査規則・受理述語・runtime 挙動の差分ゼロ」と読み、役割文書の bytes を pin する台帳の追随は実装面として Codex author に書かせる。** `.claude/agents/*.md` は `orchestrator/codex_roles/review_ledger.py` の `SOURCE_FILE_SHA256`、`.codex/role-adapters/<role>.json` (`source_file_sha256` / `source.sha256` / `semantic_digest` / `developer_instructions`)、`orchestrator/tests/test_reflux_originless_compatibility.py` の originless baseline (planner・critic・coder = trigger-gating) に pin されており、D118 残余 (b) が「是正は review_ledger の source hash 更新と adapter 再生成を伴う」と明記する。D1936 項 23 / 25 の先例 (2026-09-11) と同じく、ledger と baseline は Codex author、adapter は親が既存 renderer で再生成し、docs 本文と合わせて 1 つの整合 commit にする (`tools/check_ai_provenance.py` は `.codex/` を実装面に数える)。役割本文・prompt bytes・source sha・semantic digest は意図的に変わり、LLM の応答まで同一とは主張しない。

**pin 閉包の第 4 機構 (開示):** `orchestrator/campaign/p3_b4_closed_critic.py` は B-4 receipt の再読で `critic.md` の live bytes と projection 閉包を照合し、`p3_b4_raw_record_producer.py` も同じ snapshot 照合を持つ。本決定時点で repo 内 `output/` に role sha を束縛する B-4 receipt は 0 件、B-4 事前登録 §5 の projection / prompt hash 欄は未記入であり、陳腐化する記入済み値は無い。将来の B-4 receipt は記入時点の `critic.md` bytes に束縛される。

**却下した選択肢:**
- **role schema を上げる** — D2104 項 4 が D2064 の誤引用として却下済み。key 契約は変わらない。
- **runbook の `last_delta_pct` を D1860 どおり `null` で残す** — role 例に無い field を手動射影だけが渡し続け、乖離が逆向きに残る。
- **手動 runbook へ「baseline は毎 iteration 同じ値」を書く** — 実績 (K2 1 巡) に反し、裁定されていない運用規定の新設になる。
- **`coder-v4-autonomous.md` / `-sort.md` / `-k2.md` も編集する** — 手動経路専用で機械凍結が無く、誤りの記述も無い。pin 追随の面を広げるだけになる。
- **役割文書の意味を pin する semantic test を新設する** — D1936 項 24 が却下済み。gate・検査の追加は本依頼の scope 外。
