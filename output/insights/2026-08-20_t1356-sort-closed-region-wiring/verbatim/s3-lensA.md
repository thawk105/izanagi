## 総括

独立再検算では、`ROLE_IO_CONTRACTS`・auditor input schema・`check_codex_agents.py`・兄弟 adapter に、追加すべき別の violation 語彙 pin は見つからない。一方、型17を global gallery として受理するなら、trigger 側の説明だけを1–16のまま残す判断には不整合がある。また、段2案の文面には D511 の配置要件と auditor の「見逃し機序」要件に未解決箇所がある。

### 1. pin 閉包

- `orchestrator/codex_roles/review_ledger.py:155-161` → `ROLE_IO_CONTRACTS["auditor"]` は `working_diff` 等の input と `verdict`・`violations` 等の output フィールド契約だけを持ち、violation type の語彙・最大値を固定していない → 型17追加でこの契約を変更する必要はないが、output schema の pin は別途更新が必要になる。

- `orchestrator/codex_roles/manifest.json:63-86` → auditor input は `working_diff`、`diff_digest`、`designated_sources`、`abort_digest` の4項目だけで、今回の型17変更に関係するフィールドがない → input schema hash を変更すると無関係な pin を巻き込む。

- `orchestrator/codex_roles/manifest.json:111-140` → violation の `type` に `maximum: 16` がある → 変更対象は output schema 側であり、`review_ledger.py:79-83` の `SCHEMA_SHA256["auditor"]["output"]` と manifest hash の更新が必要になる。

- `orchestrator/codex_roles/spec.py:342-429,655-683` → schema validator は `minimum`/`maximum` を汎用的に検証し、input/output の両 hash と I/O 契約を検査するが、auditor の型数を直接固定していない → `ROLE_IO_CONTRACTS` や spec 本体に追加 pin は不要である。

- `tools/check_codex_agents.py:44,296-320` → role spec のロードを通じて schema・adapter・consumer・ledger pin を間接検査するが、auditor の violation 語彙や最大値を独自には固定していない → 型17対応の直接変更点はこの checker ではなく schema/gate 側である。

- `.codex/role-adapters/auditor.json:158-161` → adapter に output `maximum: 16` の生成結果が残っている → schema と source の更新後、adapter の byte parity 更新が必要になる。

- `.codex/role-adapters/coder-v4-autonomous-sort.json:39-143` → sort coder の proposal schema であり、auditor violation type の語彙を埋め込んでいない → 兄弟 role からの追加波及は確認できない。

- `orchestrator/campaign/auditor_gate.py:29,54-69` → 実際の violation 集合を `range(1,17)` で固定している → schema だけを17へ広げても gate が拒否するため、ここは pin 閉包に含める必要がある。

- `orchestrator/campaign/coder_effect_gate.py:58-75`、`orchestrator/campaign/sort_swo_oracle.py:486-505,1450-1455` → CC の deny table と sort-SWO 判定は auditor gallery とは別の受理集合である → 型17追加によってこれらへ語彙を追加する根拠はなく、実装時に混入しないことだけを確認すべきである。

### 2. D105 waiver

- `tools/check_ai_provenance.py:93-96` → `WAIVER_VALUE` は `reason=<IDENT>; ratified=YYYY-MM-DD` の構文しか検査せず、reason の allowlist、日付の実在性、最新性を検査しない → `reason=codex-sandbox-readonly-dotcodex; ratified=2026-08-18` を保持しても、この regex からは失敗しない。

- `tools/check_ai_provenance.py:1038-1104` → waiver は最終 trailer block に1行だけ存在し、同じ block に `AI-Agent` の `role=author` があることを検査するが、ratified 日付の新しさは見ない → 2026-08-18 を当日の日付へ更新しないことは、checker の機械的要件ではなく裁定・承認記録の扱いである。

- `tools/check_ai_provenance.py:1231-1255,1499-1514` → implementation path に対して exact waiver があれば author finding を抑制するが、日付や reason の意味検証はない → 段2案の「旧日付を保持」は機械検査上の必須条件ではないが、保持しても具体的な検査失敗は生じない。

- `s2-plan.md:127-132` → `AI-Agent` の例に `model=<model>; reasoning=<reasoning>` が残っている → `<` `>` は `AGENT_VALUE` の identifier 規則に合わないため、文字通り追記すると `_waiver_audit()` が author trailer を認識できず、waiver が発火しない。

### 3. `.claude/agents/auditor.md` の実装面判定

- `tools/check_ai_provenance.py:59-70,1215-1228` → implementation prefix は `orchestrator/`、`tools/`、`.codex/` 等で、suffix に `.md` はなく、`.claude/agents/auditor.md` はいずれにも該当しない → このファイル単体は `_is_implementation_path()` で `False` になる。

- `tools/check_ai_provenance.py:1215-1228` → `.codex/role-adapters/auditor.json` は `.codex/` prefix、manifest と gate は `orchestrator/` prefix に該当する → `.claude/agents` が非実装面でも、今回の wave 全体は implementation path を含むため D105 対象から外れない。

### 4. 型17・checklist14 の文面

- `docs/decisions.md:21296-21305` → D511 は「非検査は許可ではない」を禁止事項の列挙前と、実行範囲の直後に置くことを要求している → `s2-plan.md:39-44` は5項目を先に列挙し、同趣旨の文を最後に1回置くだけなので、前置きの配置要件を満たしていない。

- `s2-plan.md:48-54` → checklist14 も `(a)`〜`(e)` の列挙前に非許可の明記がない → auditor の checklist へ移した時点でも、D511 の二重配置が再現されていない。

- `s2-plan.md:41-44,48-54`、`.claude/agents/auditor.md:95-101` → 段2案は「機械 gate が検査しない」「検査が部分的」と分類するが、なぜ verifier が見逃すかの具体的な機序までは示していない → auditor 規律の「見逃す領域の主張には機序を必ず添える」を、実際の violation 出力でどう満たすかが曖昧である。境界条件を列挙せず、検査対象外・部分検査という機序を各項目に対応づける必要がある。

- `s2-plan.md:48-54`、`orchestrator/codex_roles/manifest.json:63-86` → checklist は「silo-writeset-sort の implementation」を確認すると書くが、auditor の mediated input に `implementation` というフィールドはない → `working_diff` または `designated_sources` を指すのか不明で、auditor が実際に受け取る対象との対応が曖昧になる。

- `s2-plan.md:39-54`、`docs/decisions.md:21309-21335` → 具体的な bypass のコード形状を列挙しているわけではなく、5つの禁止義務と検査カテゴリを述べている → D48/D511 の境界条件開示を直接増やす内容ではないが、上記の「機序」要求を満たす文面へ整理しないと、単なる「部分検査」という抽象説明に留まる。

### 5. `p3_autonomous_workload_trial.py:298` を変更しない判断

- `orchestrator/campaign/p3_autonomous_workload_trial.py:39-40,254-262` → driver は `p3_s4_loop_trigger_gating` と trigger 用 planner/coder/auditor/critic のみを参照し、sort role や `p3_s4_loop_sort` を持たない → 通常の実行経路が sort auditor 呼び出しに使われる根拠はない。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:1499-1511,4011-4014` → preview、marker、source path、既定の `drive` はすべて trigger 用である → line298 を変更しない理由として「この driver に sort 経路がない」は成立する。

- `orchestrator/campaign/p3_autonomous_workload_trial.py:297-303,562-572`、`orchestrator/campaign/auditor_gate.py:29,54-69` → driver の説明は gallery code を1–16とする一方、parser は共有 `parse_auditor_dict()` を経由し、gate の受理集合を共有する → global gate を1–17へ変更すると、trigger 側も型17を受理でき、line298 の文面だけでは sort 専用性を隔離できない。

- `.claude/agents/auditor.md:58-64`、`orchestrator/campaign/p3_autonomous_workload_trial.py:297-298` → 既存の型13–15も auditor では sort 関連なのに、trigger driver の説明上は1–16に含まれている → 既に gallery code は axis 専用集合として機械分離されていない。

- `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:1718-1725`、`s2-plan.md:138-166` → 段2案は trigger 側の受理範囲を `range(1,18)` に広げる案である → 型17を sort 専用と扱うなら、これは trigger での受理を明示的に認めるテストになり、line298を据え置く説明と衝突する。型17を global gallery とするなら line298 も1–17へ更新し、sort 専用とするなら axis 別 rejection/test が必要になる。

- `orchestrator/campaign/p3_s4_loop_sort.py:78-82,375` → sort loop も共有 `parse_auditor_dict()` を使用する → sort 側だけに型17を追加する実装にはならず、型17の所属（global か axis-specific か）を先に確定しないと、trigger 側の受理集合と説明がずれる。