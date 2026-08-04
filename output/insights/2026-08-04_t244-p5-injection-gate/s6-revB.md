## 所見

### BLOCKER 1 — 既存テストが 1 node 赤化する

- **主張:** 新しい completeness 検査により、既存の成功系テストが `child_id` 欠落で失敗する。既存テストの赤化は静的調査上この 1 node。
- **file:line:** [`test_claude_transport.py:1561`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_claude_transport.py:1561)、[`test_claude_transport.py:1607`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_claude_transport.py:1607)、[`autonomous_trial_completeness.py:275`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/autonomous_trial_completeness.py:275)
- **具体的な失敗シナリオ:**  
  `test_success_consumer_keeps_valid_receipt_in_journal_and_report` は `_DeepCopyReceiptFixtureProvider` を全 role に渡す。この provider の valid provenance は `fixture` と `transport_receipt` だけで `child_id` がない。report provider は `claude-headless` なので、新検査が planner の `child_id=None` を拒否する。`_finish_trial` は既に `run-finish` を journal に追記した後、report 書込み前に例外となる。
- **最小の修正:** `_DeepCopyReceiptFixtureProvider` に role を保持させ、各 role 固有の安定した `child_id`（例: `fixture-{role}`）を provenance に追加する。テストの成功期待自体は変えない。
- **放置すると成果物の何がどう変わるか:** この node の成果物は `attempts.jsonl` に終端 event だけが残り、期待される `report.json` が生成されなくなる。

### MAJOR 1 — 独立 verifier / CLI の拒否がテストされていない

- **主張:** 実装上は独立検証経路にも接続されているが、新規の duplicate-session テストはすべて `assert_autonomous_trial_completeness` の直接呼出しである。配線 1 行を失っても P5 テストは緑のままになる。
- **file:line:** [`autonomous_trial_completeness.py:1111`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/autonomous_trial_completeness.py:1111)、[`autonomous_trial_completeness.py:1133`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/autonomous_trial_completeness.py:1133)、[`test_role_session_isolation.py:220`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_role_session_isolation.py:220)
- **具体的な失敗シナリオ:** `verify_autonomous_trial_files()` の line 1122、または CLI `main()` の line 1142 から呼出しを削除しても、新規 negative test は失敗しない。保存済みの重複 `child_id` artifact を運用者が独立 CLI で検査すると、正常と判定され得る。
- **最小の修正:** duplicate-session artifact を実ファイルとして配置し、`verify_autonomous_trial_files()` が例外になるテストと、直接 CLI が非 0 終了して `role-session-isolation` を報告するテストを追加する。
- **放置すると成果物の何がどう変わるか:** 改竄または退行で同一 session を共有した永続成果物が、運用者向け verifier から valid と認定され得る。

### MAJOR 2 — runbook の実効 cardinality と部分失敗を検出できない

- **主張:** 現在の positive test は最大 4 個の valid observation、実 subprocess 系は 1 workload・3 valid role に留まる。§3.2 の 3 workloads を通す positive と、`claude-headless` の invalid partial を許容する positive がない。また拒否が実際に発火した artifact path / 計測 ID も提示されていない。
- **file:line:** [`phase3-s8c-autonomous-trial-runbook.md:74`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/docs/phase3-s8c-autonomous-trial-runbook.md:74)、[`test_role_session_isolation.py:97`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_role_session_isolation.py:97)、[`test_claude_transport.py:1019`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_claude_transport.py:1019)、[`autonomous_trial_completeness.py:281`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/autonomous_trial_completeness.py:281)
- **具体的な失敗シナリオ:**
  - `len(observations) > 4` を拒否する 1 行を入れても既存 positive は通るが、runbook §3.2 は第 2 workload で拒否される。
  - filter を `status in {"valid", "invalid"}` に退行させても skipped-only 検査では捕まらず、provider-init 後などの正当な invalid partial が `child_id` 欠落で拒否される。
  - shim の session ID は `wrapper-{role}` で role 間では異なるが、呼出し間では固定である。3 workloads に流用すれば、正当な fresh-context 証明にはならない。
- **最小の修正:** workload と invocation を含む session ID を返す shim で §3.2 相当の 3-workload positive を追加する。さらに current-schema の invalid attempt を含む positive、共有 ID を注入した negative control を通常の `run_trial` と独立 verifier の双方で実行し、安定した run root または計測 ID を記録する。
- **放置すると成果物の何がどう変わるか:** `claude-abc-g1` の正当な複数-workload report が途中で消失する退行、または共有 session の report が通過する退行の双方を検出できない。

### MINOR — 実経路に存在しない exact-type gate が mutation credit を占有する

- **主張:** tracker subclass の拒否は段 4 の P5 成果物条件ではなく、正式 `_provider_set` は必ず exact class を生成するため artifact acceptance に寄与しない。
- **file:line:** [`claude_projected_provider.py:130`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/claude_projected_provider.py:130)、[`test_role_session_isolation.py:163`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_role_session_isolation.py:163)、[`p3_autonomous_workload_trial.py:945`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:945)
- **具体的な失敗シナリオ:** subclass を拒否する行を消しても正式 CLI が生成する report は一切変わらないが、専用テストだけは赤くなる。
- **最小の修正:** exact-type 拒否と専用テストを削るか、少なくとも成果物 mutation の検出力として数えない。

## 既存テスト赤化の全数

静的に赤化すると判定した node は次の 1 件だけである。

- `orchestrator/tests/test_claude_transport.py::test_success_consumer_keeps_valid_receipt_in_journal_and_report`

要求された残りの経路は以下の理由で赤化しない。

- `_provider_set` の既存 caller は `**kwargs` を受ける fake、または実 constructor であり、新引数追加を許容する。
- `ClaudeProjectedRoleProvider` の直接 constructor 呼出しは新引数を省略し、既定値 `None` になる。
- `test_autonomous_trial_completeness.py` の既存 role artifact は provider が `fixture` で、新検査の対象外。
- `_transport_admitted_trial` は role attempt が 0 件で、空 observation は受理される。
- claude-headless shim の成功 node は 1 workload のみで、planner/coder/critic の ID は role ごとに異なる。auditor は skipped なので対象外。
- provider-init-error、pre-workload wall-budget、terminal transport paths は valid role attempt がなく、空集合として受理される。
- retry artifact は新検査以前から `attempt=1` / `retry=False` 制約で不受理であり、新規の過剰拒否ではない。

## 段 4 実測の独立検証

- 「claude-headless + `providers` 注入で成功を期待する既存テストは 0 件」: **真**。
- 「`_transport_admitted_trial` は role attempt が 0 件」: **真**。
- 「`_role_event` の fixture provenance は fixture report にしか使われない」: helper の既存利用に限れば **真**。ただし別 fixture `_DeepCopyReceiptFixtureProvider` を見落としており、「consumer fixture は壊れない」という段4の結論は BLOCKER 1 により反証される。
- 「shim executable は role ごとに相異な session_id を返す」: **真**。ただし `wrapper-{role}` は invocation 間で固定であり、複数 workload の fresh-context 証明にはならない。

## 並行 wave と発火経路

P1 の編集面は `reflux_ir.py` とそのテスト群であり、今回の変更ファイルとの重複はない。P3 は段4で停止して実装を持たず、現時点のコード衝突もない。ただし新 module の「P3 ledger が issuance を所有する」という説明は、現在の P3 実装状態より先行している。

runbook §3.1 は fixture provider なので本検査は発火しない。§3.2 では valid role response と `_finish_trial` から検査へ到達し、既定成果物候補は `output/exploration/autonomous-trials/claude-abc-g1/{attempts.jsonl,report.json}` である。しかし、共有 ID を実際に拒否した current-schema の artifact path / 計測 ID は見つからなかった。既存の計測 `876813` は schema v1 かつ全 role invalid であり、P5 拒否の証拠にはならない。

## 総括

**BLOCKER 1 件、MAJOR 2 件、MINOR 1 件。判定は NO-GO。** 最優先の問題は、既存成功テストが report 書込み前に確実に失敗する点である。さらに、独立 verifier と直接 CLI の拒否配線は実装されていても negative test に拘束されておらず、保存済み成果物に対する実効性を保証できない。runbook §3.2 が要求する複数 workload の cardinality、invalid partial、共有 ID の実発火についても、現在のテストと計測証拠では守れていない。BLOCKER の fixture provenance を修正し、3-workload positive・invalid partial positive・永続 artifact を使った verifier/CLI negative control を追加し、その run root または計測 ID を記録するまでは段 7 へ進めるべきではない。なお本レビューは指定どおり静的検査のみであり、pytest の結果は主張していない。