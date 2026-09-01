# 訂正 (2026-09-01、段 3 の 2 レンズによる反証を親が現物確認して確定)

本メモは段 1〜2 時点の親の実測である。段 3 で次の 3 点が反証された。読むときは訂正を先に見ること。

- **M6 は過剰一般化だった。** 「`D121` を参照する実装が 0 件」から「P1〜P9 の評価器が 0 件」は導けない。
  P1 は D160 が充足を記録しており、`orchestrator/campaign/reflux_formal_consumer.py` に条件評価の実装がある。
  合接を閉じているのは P6 の 1 件である (`FormalReasonCode.P6_UNAVAILABLE`)。不在は識別子ではなく性質で測る。
- **M3 の一部が stale。** `condition-freeze.v1.g11.json` は既に実在し、`ruling_reference` は D1066 である。
  D882 が想定した「後続 wave が g11 を発行する」という前提は現物と食い違う。
- **M4 の層 3 先例の位置づけが強すぎた。** `layer3_report.build_accepted_report` の受理枝は
  `certifying=true` を要求する一方、受領証 parser は `certifying=false` を構造的に強制する。
  docstring 自身が「結線済みの証拠ではない」と書いており、正例が発火する先例としては数えられない。
- **N3 も refuted。** 条件 11 は受領証の runtime consumer ではない (成功末尾も `EVIDENCE_UNDEFINED`)。

以下は訂正前の原文である。

---

# [T-434] 親が段 1〜2 で実測した事実 (2026-09-01、worktree = main 08a17b3b3)

これは親の実測メモである。**この内容自体も検査対象**であり、裏が取れないもの・
一般化しすぎているものがあれば名指しすること。

## M1. 承認上限の現行値

- `orchestrator/campaign/p3_autonomous_workload_trial.py:143` — `MAX_GENERATIONS = 10`
- `orchestrator/campaign/p3_autonomous_workload_trial.py:144` — `MAX_APPROVED_GENERATIONS = 2`
- `orchestrator/campaign/p3_autonomous_workload_trial.py:501-510` — `_validate_generation_budget`。
  `1..MAX_GENERATIONS` の範囲検査の後、`generations > MAX_APPROVED_GENERATIONS` を
  「D106 残余 1 の裁定まで承認済み上限 2 以下必須」で拒否する。
- 3 入口はいずれもこの純関数を呼ぶ: `main` (`:5064`)、`run_trial` (`:4397`)、
  `_run_workload` (`:3717`)。
- したがって設計メモ (2026-08-04) §2 の「receipt 無しなら実効 cap = literal 1」は、
  現行の受理集合 (2 が通る) を狭める変更になる。D410 が 1→2 を裁定済みである。

## M2. 事前登録の条件 11 が同じ定数を読む

- `orchestrator/campaign/s8c_preregistration_evidence.py:2525-2537` — `_evaluate_c11` が
  AST で `MAX_APPROVED_GENERATIONS` を取り、`cap is None or cap < 2` を
  `GENERATION_CAP_NOT_LIFTED` で UNSATISFIED にする。続けて 3 入口が
  `_validate_generation_budget` を呼ぶことも AST で要求する。
- `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json` の condition 11
  `required_evidence` が `MAX_APPROVED_GENERATIONS`・`main.args.max_generations`・
  `run_trial.generations`・`_run_workload.generations`・`_run_workload.apply_critic_feedback` を
  `field_paths` に pin する。
- 契約 file の内容 hash は literal で凍結されている:
  `orchestrator/tests/test_s8c_preregistration_core.py:1195-1198`
  (`test_current_evidence_contract_hash_is_frozen`)。
- `docs/phase3-8c-preregistration.md:91-95` は全 cell を厳密に `G=2` と定め、
  起動側既定が `G=2` ではないため世代数の明示指定を要求する。

## M3. D882 が条件 11 まわりを T-435 の変更単位として予約している

- D882 決定 (1)(3)(5) を参照。改訂対象は 6 locus + 生成閉包 (契約 hash pin 4 nodeid) +
  `output/s8c-preregistration/condition-freeze/condition-freeze.v1.g11.json` で、
  後続 wave が**同一 commit** で land する。`DECIDER_VERSION` は v6 のまま bump しない。
- D882 は却下選択肢として「条件 11 の `required_evidence` へ機構を足す」を挙げ、
  「`DECIDER_VERSION` bump と評価器改訂を要し、確定した変更単位を超える。
  必要なら独立の裁定として起こす」と却下している。
- T-435 は実装待ちで、branch も worktree も存在しない (非稼働)。

## M4. 既存の同型機構 (再利用候補)

- `orchestrator/campaign/s8b_ratified_freeze.py` — 人間承認 commit topology の実装済み検査。
  - `_raw_ai_agent_lines` (:518)、`_parsed_ai_agent_values` (:528)、
    `_is_none_commit` (:546) が `AI-Agent: none` を raw 行ちょうど 1 本 + parse 値 `["none"]` の
    二重判定で確認する。
  - `_assert_user_commit` (:558) が 非 merge + `AI-Agent: none` 逐語 + H ancestry を
    fail-closed で要求する。
  - `_assert_candidate_commit` (:573) が世代導入 commit G を別基準で検証する
    (非 merge、かつ `none` trailer なら拒否)。
  - 設計メモ §3 の発効 topology (非 merge・親が承認対象・create-only・`AI-Agent: none` 1 本) は
    これと同型である。
- `orchestrator/campaign/s8c_acceptance_receipt.py` (1244 行) — 受領証の完成形。
  canonical bytes (:172)、重複 key 拒否 (:233)、`_exact_keys` (:259)、
  `_require_sha256` / `_require_commit` / `_require_posix_path`、HEAD blob 読取 (:658)、
  git env allowlist (:95)、封印済み `VerifiedAcceptanceReceipt` (:152)、
  `parse_acceptance_receipt_bytes` (:357)。
- 層 3 は既に top-level optional の受領証 property を持つ:
  `orchestrator/campaign/layer3_schema.json:243` の `acceptance_receipt`。
  top-level は `additionalProperties: false` かつ `required` に入っていない。
  `layer3_report.py:239-242` が `certifying_input is True` と非 null の同値を要求する。

## M5. exact 述語の照合状況 (親が確認した範囲)

- `p3_autonomous_workload_trial.py` の `_strict_keys` (:526) の呼出しは role response
  (`proposal` 系、:551/:555/:579/:583/:603/:616) に限られ、run-start / report には掛からない。
- `autonomous_trial_completeness.py:2944` の `set(event) != expected_event_keys` は
  generation-accounting event 専用の exact key 集合である。run-start には掛からない。
- `autonomous_trial_completeness.py:2215-2295` の `_check_run_envelope` が run-start と report を
  field 単位で突き合わせ、`:2289` で `budget > producer.MAX_APPROVED_GENERATIONS` を拒否する。
- `autonomous_trial_completeness.py:4829` の campaign-chain gate にも同じ上限判定がある。
- `REPORT_SCHEMA_VERSION` の literal pin: `orchestrator/tests/test_autonomous_trial_completeness.py`
  の `:54`、`:2916`、`:2918`。
- 層 3 の top-level は `additionalProperties: false`、`required` は 16 key。
  `runs.items` も `additionalProperties: false`、`required` は 7 key。

**注意:** M5 は親が確認できた範囲であり、網羅の主張ではない。
未照合の exact 述語が残っている前提で検査すること。

## M6. 受領証の受理枝の到達可能性

- D121 の前提条件 P1〜P9 の独立評価器は repo に存在しない
  (`D121` を参照する `orchestrator/` 配下の実装 0 件)。
- したがって全 P が `SATISFIED` になる状態は現環境で到達不能であり、
  受領証を実際に発行して受理させることは現状できない。
- 親の provisional 判断は「受理枝は fail-closed のまま実装し、正例は実体を stub せずに
  置けるかを段 3 で判定する」である。**この判断自体を検査すること。**
