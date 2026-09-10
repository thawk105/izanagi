実装は完了しましたが、必須テストは dispatch 基盤障害により未実走です。緑とは判定していません。

変更内容:

- [build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/campaign/build_admission.py:169)
  - 自前 C++ 字句解析 2 helper を削除。
  - BEGIN/END を raw bytes regex の全 match で判定。
  - file 全体の BOM・NUL・UTF-8 decode 検査を削除。
  - raw bytes 1 回読み、ENOENT のみ no-op、他の `OSError` は reject を維持。
- [test_build_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_build_admission.py:320)
  - comment visibility、BOM、NUL、invalid-UTF8 の負例を削除。
  - `N16-reversed-directives` を追加。
  - precedence test は診断順序 pin であり、単独 kill 証拠ではない旨を docstring に明記。
  - pristine 正例は維持。
- [test_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t897-trigger-admission/orchestrator/tests/test_campaign.py:5361)
  - `_write_materialized_trigger_source` を `FROZEN_TEMPLATE_BLOCK_BYTES` 由来に変更。
  - `hole_line`、`line_ending`、戻り値の意味は維持。

| 所見 | 状態 | 対応 |
|---|---|---|
| A-F1/F2・B-1: 字句解析と全体検査 | partial | 実装・静的確認済み、pytest 未実走 |
| B-2: campaign fixture の既存 2 node 赤 | partial | fixture 修正済み、指定 2 node 未実走 |
| A-F3・B-3: テスト帰属 | partial | 不適切な負例削除、逆順負例・docstring 追加済み、未実走 |
| B-4: 例外優先順位 nit | closed | 段 6 裁定どおり変更対象外 |
| regressed | なし | 静的確認範囲。動的判定は未実施 |

検査状況:

- 指定された 2-file invocation を2回実行。
- 両方ともテスト起動前に `rc=16`。
- 原因: `qstat -Q` が `NQSconnect: Can't create socket (errno: 1)`。
- 実走 nodeid: **0件**。指定の正経路2件、負例10件、両ファイル全体はいずれも未実走。
- `git diff --check`: 成功。
- 3編集ファイルの Python AST parse・UTF-8 NFC: 成功。
- docs 編集・commit・stage 操作: なし。
- 既存 staged `axis_trigger_gating.py` は未編集。

静的な波及候補は、`derive_build_admission` を使う `pipeline`、各 coverage/floor/calibration driver、および `require_build_admission` を使う legacy/v2 buildcache です。共有 fixture は `test_campaign.py` 内の負例10件と統合経路2件が利用します。receipt replay の `validate_build_admission_receipt` には validator を結線していないため影響しません。

## 総括

F-1〜F-3 は権限内で実装済みです。必須テストは sandbox から Pegasus dispatch socket を作れず未実走のため、状態は `partial` です。期待値の変更、受理 gate の無効化、docs 編集、commit は行っていません。