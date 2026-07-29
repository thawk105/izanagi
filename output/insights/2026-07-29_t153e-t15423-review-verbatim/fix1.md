修正完了です。docs・commit・所有外ファイルには触れていません。

変更:

- [check_ai_provenance.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423-author/tools/check_ai_provenance.py:94)
  - AI-Agent/scope/Codex-author は従来の repo cwd・divider既定 parserを維持。
  - CAB専用 parserのみ `--no-divider`、UTF-8 bytes I/O、LF byte分割、異常record fail-closed。
  - 毎回freshな private temporary ceilingとnested cwdを作成し、local/system/global/env configを隔離。
  - policy検索を `--full-history --no-renames` 付きの指定形へ固定。
- [test_check_ai_provenance.py](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t153e-t15423-author/orchestrator/tests/test_check_ai_provenance.py:291)
  - M1/M2単一理由fixture、CR/VT/FF/NEL/LS/PS、invalid UTF-8、不正recordを追加。
  - hostile ancestor、valid system/global/env alias、rename-in/out、merge retain/drop、0→2→1を固定。
  - 独立policy literal、導入commit自身、backtick/tilde fenceを追加。
- `check_docs.py` とそのテストは段5初版がreview所見を満たしていたため、追加修正なし。

検査結果:

- 指定runner: **184 passed / 1 failed、185 items**
- 唯一の赤:
  `orchestrator/tests/test_check_ai_provenance.py::test_policy_needle_literal_matches_production_and_repo_policy_exactly_once`
  - 理由: 親未landの `docs/ai-provenance.md` でpolicy literalが期待1件に対し現状0件。
- plain provenance runner: **58 passed / 同じ1 failed**
- plain docs runner: **126 passed / 0 failed**
- plain-runner meta-test: **3 passed**
- `check_codex_agents`: 緑
- `check_docs`: 緑
- 現履歴の `check_ai_provenance`: **495件、違反なし**
- `git diff --check`: 緑

所有外波及:

- caller: `CLAUDE.md`、`AGENTS.md`、`docs/dev-wave/operations.md`、`tools/task_run_check.py` のCLI呼出し。CLI引数・rc契約は不変。
- fixture: provenance側の `_policy_history`、`SPLIT_CAB_NONE`、独立policy literal、およびdocs側の `_build_min_repo`。所有外共有fixtureの変更は不要。
- consumer: message-file/default-history/explicit-range、scope epoch、Codex-author gate、docs budgetの`all_limits`、両plain runner。親のmutation・受入全走は別途必要です。
- Git状態は所有4ファイルだけです。段5初版はstagedのまま、fix差分は provenance実装・テストの2ファイルにunstagedで載っています。commitは作成していません。

## 総括

段6のreal所見を所有範囲内で修正しました。既存AI-Agent、scope、Codex-author判定は従来どおりrepo cwdで`git interpret-trailers --parse`を使い、divider既定の受理集合を維持しています。新しいcanonical parserはCAB finding専用に分離し、UTF-8 bytes入出力、LF byteだけのrecord分割、壊れたUTF-8と予期しないrecordのfail-closed、fresh temporary ceilingによるancestor/local repository遮断を実装しました。履歴検出は`--full-history --no-renames`へ固定し、rename-in/out、policyを残す・落とすmerge、needle件数0→2→1、ambient rename設定を実fixtureで検査しています。指定runnerは185 items中184 passedで、赤は親docs未landを検出するexact-doc node 1件だけです。plain docsは126件全緑、plain provenanceは58件緑と同じ期待赤1件、meta-testは3件全緑でした。CLI caller、task-run consumer、message-file/default/range経路、docs budget consumerへのinterface変更はありません。親はdocs literalをexact 1件landした後、この赤の解消、mutation matrix、親受入全走を実施してください。