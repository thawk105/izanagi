実装完了です。変更は指定された3パス内だけで、docs・commit・実ログには触れていません。

### 実装

- [codex_worker_ledger.py](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/tools/codex_worker_ledger.py:39)
  - stage 規則表: 39行目。`focus → fix → author/review` の重なりを持たせ、順序依存を明示。
  - outcome 優先順位: 96行目、分類実装は260行目。`aborted_turn → incomplete → fragment → completed`。
  - streaming JSONL 集計: 182行目。
  - 既存 validator の定数・fence除去述語再利用: 248行目。既存受理集合は未変更。
  - retry 集計: 287行目。
  - worklog 解析・突合: 335、386行目。
  - strict 理由別診断: 474行目。
  - validator import による bytecode 書込みも抑止し、stdout 以外へ書かない。
- [test_codex_worker_ledger.py](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/test_codex_worker_ledger.py:194)
  - compaction、完全ID衝突、unclassified、fragment、incomplete、retry、健全波、9対10 worklog、壊れたJSON、meta欠落、決定性、規則順序、read-onlyなどを独立検証。
- [codex_ledger fixtures](/home/SFC/tanab/.claude/jobs/51d55fec/tmp/t179-wave/author/orchestrator/tests/fixtures/codex_ledger/)
  - 罠ごとに分離した合成JSON fixtureとread-only実行用 rollout。実prompt・実ログは不使用。

### 検査結果

- `orchestrator/tests/test_codex_worker_ledger.py`: **28 passed / 0 failed**
- `orchestrator/tests/test_check_codex_output.py`: **18 passed / 0 failed**
- `orchestrator/tests/test_check_docs.py`: **132 passed / 0 failed**
- `python3 tools/check_codex_agents.py`: OK
- `python3 tools/check_docs.py`: 違反なし
- `git diff --check`: rc=0

実装初走では **2 passed / 20 failed**。全20件はfixture builderの `zip(..., strict=True)` がpytest実行環境で非対応だった同一原因で、互換形へ変更後は上記の最終結果です。残存する赤はありません。

### 波及可能性

- `tools/check_codex_output.py` のprivate定数とfence除去述語をimportするため、それらの改名・意味変更は台帳へ波及します。同ファイル自体は変更しておらず、既存consumer test 18件も通過済みです。
- 新規CLIの既存callerはありません。親の実ログ受入と、後続T-180〜T-184が主なconsumer候補です。
- fixtureは新規専用tree内に閉じ、既存共有fixtureへの影響はありません。
- meta-testは新規テストファイルの追加登録を要求せず、132件すべて通過しました。

## 総括

合成データだけで決定的・streaming・read-onlyなworker資源台帳と全指定回帰を実装しました。変更はすべて未stageで、commitは作成していません。親は実ログで10 session / 434 turns / 2,757,982 CLI reported tokens、stage別値、worklogの9対10不一致を受入確認し、その後の変異・統合・docs記録・commitを担当してください。