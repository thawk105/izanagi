実装は完了しています。commit と docs 編集は行っていません。

- core に exact 7-key proof validator を追加しました。4 digest、正整数 `row_count`、nonzero head、proof/schema literal を検査し、固定順の新規 dict を返します。
- registry に capture / inspection API を追加しました。read-only lock、expected binding 由来の exact 2 段 path、全行 replay、N 行目 head 比較を実装しています。
- registry schema は core の閉じた定数とし、adapter で profile の v2 定数との一致を確認しました。任意 schema 引数と所有外 profile 編集を避けるためです。
- M1〜M6、M8〜M10、M17、M18、D1522 の直接検査を含む 41 node を追加しました。
- v1 reader/writer、既存 `read_attempt_registry`、recovery、v2 terminal 二層拒否、不変 pin は変更していません。
- `check_codex_agents.py`: OK。`check_docs.py`: 違反なし。
- pytest は runner が Pegasus dispatch を選択しましたが、`qstat -Q` preflight の rc=1 により child 未起動、rc=16 でした。したがって実装済み・未実走であり、緑とは申告しません。
- 新規 test file はないため file 列挙 meta-test の追加発火はありません。direct-import と `test_check_docs` node の実走も同じ infra failure で未実走です。
- runner が ignored な dispatch receipt を `output/pegasus-dispatch/` に生成しましたが、tracked な所有外変更はありません。

所有外への静的波及候補は `s8b_floor_stats.py`、`s8b_floor_attempt_launcher.py`、`s8b_floor_campaign.py`、holdout / ratified consumer、共有 fixture の `s8b_v2_freeze_fixture.py` と `s8b_floor_evidence_fixture.py`、対応する floor / holdout / ratified test 群です。

## 総括

- [attempt_registry_core.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-unit1/orchestrator/campaign/attempt_registry_core.py): +81 行
- [s8b_attempt_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-unit1/orchestrator/campaign/s8b_attempt_registry.py): +231 行
- [test_attempt_registry_core_s8b_profile.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-unit1/orchestrator/tests/test_attempt_registry_core_s8b_profile.py): +114 行、19 node
- [test_s8b_attempt_registry.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1851-b2-d1-unit1/orchestrator/tests/test_s8b_attempt_registry.py): +518 行、22 node
- 実走範囲: 上記 2 test file 全体、0 passed / 0 failed、child 未起動 rc=16
- 所有外波及: unit 2、C、D2 の caller・fixture・consumer test
- 未実装項目: unit 1 内なし。pytest 実走のみ未完了
