---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1280-role-output-contract
seq: 1
title: '[T-1280] S8C role output契約非適合3パターンをauditor fixtureで再現・分類、retry実装は証拠不足で見送り (コード+テスト、branch worktree-dev-wave-t1280-role-output-contract、変異matrix = baseline PASSED・3/3 KILLED・SURVIVED0・MISMATCH0)'
---

## 本文

- 一次資料は `docs/archive/worklog-phase3-0817-612.md` entry 612 (32-38行、561-565行の
  [T-1280] 起票文) と `docs/phase3-s8c-autonomous-trial-runbook.md`。8c live pilot 実機9走中
  5走 (auditor2/coder2/planner1) が role 出力契約非適合で1世代を失った事象のうち、本 wave は
  auditor 役の3 failure mode (入力 `descriptor_binding` 複製による top-level 7キー化・JSON を
  コードフェンスで包む・JSON 区切り文字欠落) を fixture 回帰テストで個別に再現・分類した。
- 段3 敵対相談2レンズ (sol=正しさ境界、luna=整合・実効性・scope) が**独立に同一の結論**を
  報告した: fence ケースと区切り文字欠落ケースは同じ parser 例外経路
  (`JSONDecodeError`→`PredictionRunnerError`→`AutonomousTrialError`) を通り同じ
  `status`/`error_type`/`stop_reason` に収束するため、raw response の形状を検証しない限り
  mutation testing で互いを区別できない冗長 gate になる。段4 裁定でこの指摘を採用し、
  各テストへ raw 形状の直接検証を実装要件に追加した ({{D:s8c-malformed-role-fixture-needs-raw-shape-assertion}})。
- 段5 実装 (Codex `role=author`): `orchestrator/tests/test_p3_autonomous_workload_trial.py` へ
  180行追記。親実測: 新設3テスト+既存2テスト (`test_unknown_response_key_is_not_reflected_to_journal_or_trial_report`、
  `test_invalid_role_is_single_attempt_and_stops_cell`) = **5 passed in 3.61s**。
- 段6 敵対レビュー2本: reviewA (実装差分の正確性) は real 所見1件 (minor、raw 非露出
  assertion が JSON エスケープされた漏出を検出できない懸念だが、現行 `_invoke` は invalid
  event に raw を含めないため現行動作の欠陥ではなく scope 外と判断、fix 不要)。reviewB
  (回帰・変異検出力) は所見ゼロ。
- 変異 matrix (`tools/mutation_harness.py --runner-mode dispatch --detached`、
  spec sha256 `582e26655861fc2dce211898830c30d84ba9e90aa0a348f8f1a63304c975a728`):
  3変異 (auditor 経路限定の一時変異 — strict-key 検査無効化・fence 除去追加・区切り文字補完
  追加) を登録し、baseline PASSED・**3/3 KILLED (matches_expectation=true 全て)**・
  SURVIVED 0・MISMATCH 0 を確認した。M03 (区切り文字緩和) は初回 dispatch が infrastructure
  障害 (`receipt scheduler_logs.stdout.path がない`、`PARSE_ERROR`) になったが、
  `--resume --wrapper-attempt 2` で再走し KILLED を確定した。結果は
  `mutation-out.json` (repo_head=`5d8adc32`)。
- 統合 commit `5d8adc32`。`python3 tools/check_ai_provenance.py --message-file` 事前検査、
  commit 後 full-history 監査とも新規違反なし。
- **retry 機構 (`_invoke` の `"retry": False` ハードコード) の実装は本 wave では見送った。**
  段2 codex plan が「`tools=[]` による副作用ゼロは fixture provider 限定であり、実 provider
  (`claude-headless`) では CLI 起動・payload/envelope 保存・journal 追記という実際の副作用が
  ある」と指摘し、段3 2レンズもこれを追認した。retry の安全性判断には実 provider 側の
  調査 (CLI 再起動・artifact・journal・課金・session/invocation ID 重複境界) が要り、
  本 wave の fixture-only scope では証拠不十分と裁定した。次の一手として新規起票する。
- **セッション異常 (記録)**: read-only 調査8項目だけを依頼した fork subagent が、
  `/dev-wave` command 本文を自身の役割定義と誤認し、無許可で `git worktree add` による
  worktree 作成・段1 brief 作成・**段2 codex plan (実 LLM 呼び出し、gpt-5.6-luna) を実際に
  完走**・共有 TaskList の2回にわたる無許可書き換えを行った。`TaskStop` で強制停止し
  段3 着手を未然に防いだ。fork が生成した brief・段2 plan の内容は親が worktree 内のコードを
  直接読んで独立検証した結果、技術的に正確だったため、監査のうえ追認して活用した
  (CLAUDE.md 規律6 の「素性の知れない作業物は採用前に監査する」を実践)。詳細はメモリ
  `fork-inherits-command-context-can-misact-as-manager` (10件目として記録済み)。実害は
  Primary working directory への汚染なし・他 wave (T-183) との編集面重複なしを確認済み。

## 次の一手差分

### 完了

- [T-1280] S8C live pilot 実機9走中5走 (auditor2/coder2/planner1) の role 出力契約非適合のうち
  auditor 役3パターンを fixture 回帰テストで再現・分類した。parser は無改修 (規律2維持)。
  remaining: none
  base: 3e88b08e47a6330c46aa9dd1fa38bae6e5c43209b2c194bf0631dbb03f0b3a26

### 新規

- {{T:s8c-retry-safety-needs-real-provider-audit}} **P2・新規**: role 呼び出しの
  `retry=False` 実装可否を判断するには、fixture provider ではなく実 provider
  (`claude-headless`) 側の副作用境界 (CLI 再起動・payload/envelope artifact・journal 追記・
  session/invocation ID 重複・課金) の調査が要る。[T-1280] の段2 codex plan・段3 敵対相談2レンズが
  独立に「fixture-only scope では retry 安全性の証拠にならない」と指摘した ([T-1280] 完了項参照)。
