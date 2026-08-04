## BLOCKER

### B1 — 裁定が禁じた P3/token 語彙を新規 leaf に持ち込んでいる

- 主張: 段4は新規 leaf で `token` 等を使わないと明記し、U-2/P3 origin ledger を非接触面にしています。しかし docstring が双方を直接記述しています。
- file:line: [role_session_isolation.py:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/role_session_isolation.py:7)、[s4-adjudication.md:102](/work/1/SFC/tanab/dev-wave-jobs/t244-p5-injection-gate/s4-adjudication.md:102)
- 具体的な失敗シナリオ: この差分を「P3 非接触」として land 対象へ入力すると、実際には P5 leaf が未実装 U-2/P3 の契約語彙を所有しており、scope 適合成果物として誤受理されます。
- 最小修正: docstring の7–8行を削除し、未実装 U-2 は段4裁定・後続 decision だけに残す。
- 放置すると成果物: 試行台帳の実行値は直ちに変わりませんが、wave のソース成果物が明示 scope 外となり、「P3非接触」であるとの記録を正しく land できません。

## MAJOR

### M1 — D96 の `child_id` 型境界が truthiness と欠落を分離していない

- 主張: “non-string” 負例が `None` だけで、空値検査でも拒否できる値です。また helper は常に `child_id` キーを作るため、`.get()` の欠落時既定値も固定していません。
- file:line: [test_role_session_isolation.py:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_role_session_isolation.py:97)、[test_role_session_isolation.py:234](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/tests/test_role_session_isolation.py:234)、[role_session_isolation.py:39](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/role_session_isolation.py:39)
- 具体的な失敗シナリオ: 検査を `if not session_id` に弱めると、現テストは全部通ったまま `child_id=1` の Claude artifact が complete として受理されます。欠落時に `.get("child_id", "unknown")` とする回帰も未検出です。
- 最小修正: truthy 非文字列（例: `1`）を追加し、非空 provenance から `child_id` だけを欠落させた独立負例も追加する。
- 放置すると成果物: 型検査または既定値の回帰が赤にならず、Claude 試行台帳の再検証受理集合が数値・欠落 `child_id` まで拡大し、complete 判定が偽陽性になります。

## MINOR

### m1 — formal 経路では恒真な helper 拒否がある（nit、変異 credit 対象外）

- [role_session_isolation.py:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/role_session_isolation.py:26) の container/pair 検査は両 caller が exact tuple を内部生成するため、formal artifact から発火しません。
- role 名検査も consumer では先行 `_logical_id`、非-Mapping provenance の fallback は先行 shape 検査で拒否済みです。[autonomous_trial_completeness.py:205](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/autonomous_trial_completeness.py:205)
- 同一 provider instance の重複は既存 `_observed_session_ids` が先に拒否します。[claude_projected_provider.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/claude_projected_provider.py:308)
- 最小修正: 実装変更は不要ですが、これらを P5 の新規検出力や mutation kill に数えないこと。
- 成果物影響: なし。したがって must-fix ではありません。

## 変異 ID の静的判定

| ID | 判定 | 根拠 |
|---|---|---|
| MX1 | KILLED | 新 gate を無効化すると `providers={}` が partial artifact を生成でき、artifact 非生成 assertion が赤になる。 |
| MX2 | SURVIVED（予定どおり） | [新 gate](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/p3_autonomous_workload_trial.py:1550) が旧 transport gate を完全に包含する。 |
| MX3 | KILLED | tracker の拒否を無効化すると、別 provider instance 2個の同一 session が通る。instance-local gate は mask しない。 |
| MX4 | KILLED | [observe 呼出し](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t244-p5-injection-gate/orchestrator/campaign/claude_projected_provider.py:362) を消すと別 instance 負例が通る。consumer を使わない独立 node。 |
| MX5 | KILLED | role ごとに tracker を作れば identity assertion が赤になる。runtime fail-closed の構造固定として成立する。 |
| MX6 | KILLED | consumer の拒否を無効化すると、runtime tracker を経ない合成 duplicate artifact が受理される。 |
| MX7 | KILLED（登録された `if False` に限る） | 条件全体の無効化は空文字/`None` node が殺す。ただし型だけの弱体化は M1 のとおり生存する。 |
| MX8 | KILLED | Claude 限定を外すと `provider="fixture"` の valid provenance に `child_id` がなく、正例が過剰拒否される。 |
| MX4+MX6 | mask なし | 両方を消すと runtime duplicate と合成 duplicate の双方が受理され、それぞれ独立テストが赤になる。 |

既存テストの assert・fixture・期待値・skip・xfail の変更はありません。変更された既存ファイルは production 3本だけで、テストは新規ファイルのみです。`_EVENTS`、report/run-start schema、P1、cap-lift、事前登録文書には差分がありません。pytest は実行せず、`git diff`、未追跡ファイル全行、`git status --short`、`git diff --check` による静的確認だけを行いました。

## 総括

BLOCKER は **1件**、MAJOR は **1件**、MINOR は **1件（nit）**です。P5-1 の拒否位置、tracker の4 role共有、別 instance 間の重複拒否、consumer による valid attempt の非空・相異再計算は、現行コード上はいずれも到達し、MX1〜MX8の登録変異も予定された意味で概ね kill できます。実行時層を消しても consumer が残り、consumer 層を消しても tracker が残るため、二層の直接的な相互 mask はありません。しかし、実装正本が語単位で禁じた P3/token の持込みは明白な scope 違反です。また D96 境界テストは `None` を「非文字列」として兼用しており、truthy 非文字列や欠落既定値への弱体化を検出できません。したがって現時点の判定は **NO-GO** です。B1 の削除と M1 の独立境界ケース追加後に、親が変異 matrix と受入を実測する必要があります。