実装済み・未実走です。commit と docs 編集は行っていません。

変更:
- [s8c_preregistration_evidence.py:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1352-c07-result-judge/orchestrator/campaign/s8c_preregistration_evidence.py:71) に ReasonCode 追加。
- `_evaluate_c07`（1823–2149）で entrypoint、floor fields、3 条件、3 表、cell-set data flow、ratified loader を検査。
- [test_s8c_preregistration_predicates.py:566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1352-c07-result-judge/orchestrator/tests/test_s8c_preregistration_predicates.py:566) に fixture、789–800 に負例、848–980 に直接 probe テストを追加。

新規 nodeid は7件追加しました（token-only、負例、ratified 欠落、decoy、validator戻り値破棄、registry pin、実体 blob）。

所有外の A ファイル2件は未追跡状態のまま無変更です。既存 caller は fallback 経路のみで、共有 fixture・既存 consumer test の期待値も変更していません。

`_MACHINE_EVALUATORS`、`MACHINE_CHECKABLE_CONDITION_IDS`、`SATISFIABLE_CONDITION_IDS`、`NEGATIVE_CONTROL_CASES` は変更していません。構文、`diff --check`、AST形状、禁止文字列を静的確認済みです。

## 総括

C07 の静的 evaluator と専用テストを実装しました。  
契約外の同名 module は読みません。  
validator と cell-set 検査の戻り値を data flow で確認します。  
C07 は registry 非登録のままです。  
pytest は親が実走するため未実走です。