### 2.2 現行保存形式が新規走行で残す carrier (code から)

| carrier | 書き手 | 何を持つか | 辺 A に効くか |
|---|---|---|---|
| `loop_state.json` の whiteboard | harness (`project_whiteboard`) | `{iteration, direction, magnitude, result, delta_pct}` の 5 field だけ (D39 決定 3 / D1846) | variant id も proposal hash も無い。dry-pass (`--no-build`) は counter を消費して行を残さない。重複提案 (`_resolve_duplicate`) は前 iteration の WAL を再利用して行だけ足す (docstring: 「whiteboard/checkpoint は id を持たず分類だけが汚染」) |
| `runs/wal.jsonl` | `pipeline.evaluate` / `record_diff_reject` | variant・stage・env_tag・ts・payload。`build_start` に `genome` / `src_token` / `build_attempt_id` (現行) / `build_admission` (現行、`coder-authored` class は `input_sha256: null`) | iteration も proposal hash も無い (`iteration` / `proposal` / `attempt_id` / `parent` / `ancestor` / `snapshot` / `receipt` の文字列出現は 3 campaign の WAL で 0) |
| `campaign.lock` | harness | identity の preimage (現行は `authority` / `identity_preimage` / `schema_version`) | 走行にも proposal にも触れない |
| `reports/p3_s8a_trigger_loop_provenance.json` | **trigger driver の harness** (`p3_s4_loop_trigger_gating._append_provenance_entry`、iteration ごと merge 追記、`save_loop_state` より前) | `entries[iteration] = {proposal_path, auditor_diff_digest, outcome, variant, build_attempt_id (現行), trigger_gate_binding_commitment (現行)}` | iteration → variant を harness が結ぶ。**proposal は path だけ** (bytes / hash は無い)。`auditor_diff_digest` は auditor が審査した working_diff の sha256 (`auditor_gate.py`) でコード片の hash。**base / sort driver にはこの side channel が無い** |
| `runs/agent_outputs.jsonl` (opt-in journal) | `--agent-inputs` (live、評価前、`variant: None`) または `--record-agent-output` (ingested、事後、`--agent-variant` / `--agent-wal-ref` は WAL 実在を検査) | `provenance.source_sha256` (= 指定 file の raw bytes sha256)、`output` (role の出力 object)、`refs` (`wal:<canonical sha256>`) | proposal file の raw bytes と variant / WAL record を結べる。ただし **opt-in・呼び手の申告** (module docstring: 「not proof of delivery」)、live 経路は variant を持たない、B-4 identity (canonical hash) は記録しない。production での実例は K2 手動 loop (§4.3) |
| `reports/layer3_report.json` | `layer3_report` generator | `runs[].variant` と `source_ref = wal:<sha256>` (bench_done record の canonical hash) | 走行 ↔ WAL record の束縛。proposal には触れない (辺 B の record 名指しに使える形) |
| `<run_root>/proposals/<workload>.g<N>.json` (段 8c bounded supervisor、trigger 軸限定) | `p3_autonomous_workload_trial.py` (T-178 の `silo-backoff-trigger-gating` 専用 supervisor。自ら「generic evolution daemon ではない」と書く) | proposal document (planner / coder / auditor / prior_critic_reverse / descriptor_sha256) を保存し、generation record に path・sha256 と harness outcome を持つ。`autonomous_trial_completeness.py` が proposal・provenance・`build_attempt_id`・WAL start・source artifact を照合する | **段 6 レビューが見つけた先例 (親の初稿では欠落)。** trigger 系列の運用記録 (`output/README.md`: 「探索の運用記録であって正式 proof chain ではない」) で、base の precursor には接続されていない。B-4 の canonical identity (`canonical_b4_proposal_sha256`) は持たない |
| `source-bindings/<proposal raw sha256>.preimage` (trigger driver の opt-in) | `p3_s4_loop_trigger_gating._write_source_preimage_artifact` (`require_source_preimage_artifact` 時) | proposal file の **raw bytes sha256 を名前**にした、materialized source の digest preimage (内容は proposal JSON ではない) | 同レビューが見つけた先例。proposal raw hash ↔ source preimage の束縛で、検疫拒否・dry-pass より後の経路。base driver には無い |
| insight (`output/insights/**`) | 親 (人手) | 任意 | 親が写した proposal と run summary (K2 3 巡目) は path + sha256 で結べるが、harness の記録ではなく親の申告 |

### 2.3 消費側

`p3_b4_prerun_caller` (D2100) が読むのは checkpoint の whiteboard と `campaign.lock` だけで、WAL・provenance report・journal は読まない。
`_MISSING_SOURCES` の 12 件は保存形式の既知の制限に基づく静的分類であり、本書はそれを現物で裏付けた (§6)。

**付随して見つけた欠陥 (実装せず §7 の裁定 4 へ):** 同 caller は driver を `lock.get("trial")` (top-level key) で判定するが、現行の
`campaign.lock` は `campaign-lock/v2` (`{authority, identity_preimage, schema_version}`、`trial` は `identity_preimage` の JSON 文字列の
内側) であり、K2 3 巡目の lock (`f1ab4966ec7fb702c477ae022b0652f4478868191623e884c75cf989987f9ce4`) では `trial` が top-level に無い。
したがって現行形式の campaign は `unknown trial: None` → `CampaignInputUnreadable` になり、**不足報告にも空 batch の発行器到達にも至らない**。
tracked 3 campaign (v1 形、top-level `trial` あり) でだけ D2100 の経路が通る。decoder は既存 (`orchestrator/campaign/campaign_lock.py` の `decode_campaign_lock`。`wal.py` が `campaign_lock_codec` の別名で import、
`wal._campaign_lock_value` が使う)。本 wave では test も caller も触っていない。
