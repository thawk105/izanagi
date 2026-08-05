実装済み・未実走です。commit、docs、所有外ファイルは変更していません。

変更前の acceptance は、6件の report/journal、manifest、registry 履歴・束縛・completeness を検査し、partial を含む整合済み結果を受理して `certifying=False` の summary を返していました。既存の拒否集合は維持し、以下を追加しています。

- sealed effective preregistration の必須再計算
- 各 trial の lifecycle start/terminal 各1件と実 bytes の照合
- registry introduction commit の一意性検査
- canonical non-certifying receipt の固定 path 排他作成
- receipt の strict parse、tracked HEAD bytes、参照 bytes 再 hash
- Layer 3 材料 report の `acceptance_receipt: null`
- sealed receipt 専用 `build_accepted_report`
- m10〜m15 および機構単位正例・meta-test

波及候補:

- `assert_trial_registry_acceptance` caller は production CLI、`test_trial_registry.py` の明示 seam のみ。
- Layer 3 production consumer は `p3_autonomous_workload_trial.py` と `autonomous_trial_completeness.py`。
- consumer test は `test_layer3_report.py`、`test_autonomous_trial_completeness.py`、`test_t126_qualification_artifacts.py`。
- 所有外の `layer3_schema.json` は未変更のため、同 JSON を直接使う外部 consumer は新 field を認識しません。
- certified-selection consumer は現 checkout に存在せず、実結線は未完です。

## 総括

(a) 実装した検査:

- lifecycle canonical/schema 分離
- effective capability 再計算
- lifecycle terminal 欠落拒否
- receipt exclusive-create
- strict schema/path/canonical JSON
- tracked receipt・HEAD bytes 一致
- report/journal/registry/lifecycle 再 hash
- v1 の `certifying=false` と理由2件の構造固定
- sealed receipt・campaign/trial 照合
- rc/stdout 非依存 API

(b) 実行結果:

- pytest nodeid: なし（Pegasus ログインノードのため未実走）
- pytest rc: N/A
- 対象6コード・テストファイルの `py_compile`: rc=0
- `git diff --check`: rc=0

(c) 残る赤・波及:

- m10〜m15、追加 meta-test、対象3 test file は計算ノードでの実測待ち。
- B-0 の既知赤はテストを二分して静的修正済みだが未実走。
- 所有外 consumer test と共有 schema への波及は親の計算ノード全走で確認が必要です。