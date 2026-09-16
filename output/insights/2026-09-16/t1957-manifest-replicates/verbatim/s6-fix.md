## 直した 2 件

- `orchestrator/tests/test_trial_registry.py:8785,8809`：`tail-float` を追加。先頭は整数 `3`、後続は `3.0`。両 source で `[field] {label}[1].n must be an integer` を完全一致検査します。既存 12 ケースの入力・期待は変更していません。
- `orchestrator/campaign/trial_registry.py:1594`：docstring の列挙に `n` を追加。比較ロジックは変更していません。

## 実走結果

**実装済み・未実走。**

試行した対象 nodeid：
`orchestrator/tests/test_trial_registry.py::test_t1957_rejects_n`（既存 24＋追加 2 ケース）。

`python3 tools/run_tests.py -q <上記nodeid>` は **rc=16**。`qstat -Q` の事前確認失敗で子プロセスが起動せず、実走した nodeid はありません。

## 触っていないことの確認

M8 関連の test・実装、反復添字 0 固定の受入 gate、事前登録 doc 2 件、未使用 `_registration_value`、観測反復集合と登録 `n` の exact 一致は変更していません。docs 編集・git 操作・commit も行っていません。

## 所有外への波及

- 所有外 caller：実行ロジック・API は不変です。
- 共有 fixture：変更なし。追加入力は対象テスト内で構築します。
- consumer test：レビュー B が挙げた autonomous workload・origin binding・originless compatibility は未変更・未実走です。
- 外部の件数検査があれば、負例が 24→26 ケースになる影響があります。射影外は未確認です。

## 期待赤と回帰の区別

`test_s8c_preregistration_predicates.py` は未実走です。指定された commit 参照との差は「未 commit に由来する」期待赤として区別します。今回の rc=16 は実行基盤の失敗であり、テスト回帰ではありません。

## 総括

指定の 2 件のみ修正済みです。
テスト開始前に停止したため、closed・緑とは報告しません。
受入全走は親側に残ります。