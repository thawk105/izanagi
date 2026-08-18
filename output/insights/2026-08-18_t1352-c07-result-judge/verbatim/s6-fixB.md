実装済みです。commit・docs 編集・pytest 実走はしていません。

| 所見 | 状態 | 対応 |
|---|---|---|
| reviewA3 #6 | closed | 到達使用、floor field、二 artifact、loader 呼出し、receipt、chain を静的検査 |
| reviewA3 #9 | closed | dead assignment・loader 除去・宣言 path decoy・literal floor のテストを追加 |
| reviewB #1 | closed | A の二 artifact / receipt 形へ fixture を追随 |
| reviewB #2 | closed | A 側の同一 prediction 境界を確認 |
| reviewB #3 | partial | pytest 未実走のため単独 runner の実測は親へ委譲 |
| reviewB #4 | partial | docs/worklog は本単位の所有外かつ編集禁止 |

編集ファイル:

- [s8c_preregistration_evidence.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1352-c07-result-judge/orchestrator/campaign/s8c_preregistration_evidence.py:1866)（1866–2492）
- [test_s8c_preregistration_predicates.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1352-c07-result-judge/orchestrator/tests/test_s8c_preregistration_predicates.py:566)（fixture 566–661、C07 tests 922–1091）

追加 nodeid は loader 除去、宣言 path decoy、dead assignment、literal floor fields の4件です。既存 C07 fixture も二 artifact / receipt 形へ変更しました。

`_MACHINE_EVALUATORS`、`NEGATIVE_CONTROL_CASES`、machine/satisfiable ID 集合、既存 fallback は変更していません。A 所有ファイルは読み取りのみで、並行変更が残っています。A の receipt validator bare call は B の静的検査が正しく拒否しています。

静的 AST、禁止文字、`git diff --check`、`check_codex_agents.py`、`check_docs.py` は通過。pytest は未実走です。

## 総括

- C07 の dead assignment を受理しない data flow 検査を追加しました。
- floor field は literal だけでは通過しません。
- loader 呼出しと二 artifact を確認します。
- 宣言 path 自体の decoy を拒否します。
- C07 は registry 未登録のままです。
- commit と docs 編集はしていません。