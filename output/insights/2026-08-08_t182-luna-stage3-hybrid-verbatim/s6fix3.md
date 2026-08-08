選択肢 (a) を採用しました。`DW-O01` 重複は model-pin cardinality と既存 H2 一意性の独立した冗長 gate に触れ、production と reasoning pin の慣行が整合しているためです。`_assert_findings` の完全一致・件数固定を維持し、2 件を期待します。

- Nodeid: `orchestrator/tests/test_check_docs.py::test_dev_wave_model_pin_rejects_duplicate_dw_o01_section`
- 変更箇所: [orchestrator/tests/test_check_docs.py:5335](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t182-luna-stage3/orchestrator/tests/test_check_docs.py:5335)
- `python3 tools/check_docs.py`: rc=0
- pytest: runner の計算ノード dispatch が `qstat -Q` preflight で失敗（rc=16）。テスト本体は「実装済み・未実走」です。
- commit なし。変更ファイルは指定されたテストファイルのみです。

## 総括

冗長 gate であることをコメントに明記し、期待 finding を完全な2件集合へ修正しました。  
`check_docs` は rc=0、対象 pytest は dispatch 障害により未実走です。  
production・docs・他テストは変更していません。