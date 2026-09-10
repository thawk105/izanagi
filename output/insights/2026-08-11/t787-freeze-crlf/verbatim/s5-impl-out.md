実装済みです。編集は指定された 2 ファイルのみで、docs・output・発効層・契約 JSON・commit には触れていません。

変更前は exact `path` の文字列で NUL のみを拒否し、CR/LF は hash を返していました。変更後は NUL を全域優先で即時拒否し、CR/LF は文書順で最初の pointer を保留して、NUL がなかった場合のみ `evidence-contract-path-crlf` で拒否します。その他の制御文字、非 `path`、非文字列 `path` は引き続き受理します。

変更箇所:

- [s8c_preregistration.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/campaign/s8c_preregistration.py:344)
  - helper を `_assert_no_forbidden_control_chars_in_contract_paths` に改名。
  - 明示 stack による単一走査を維持。
  - canonicalization 後・hash 前の検査位置を維持。
  - detail は `repr(pointer)` のみ。

- [test_s8c_preregistration_core.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t787-freeze-crlf/orchestrator/tests/test_s8c_preregistration_core.py:160)
  - 38 path × CR/LF、interior、root、malformed shape。
  - F1〜F7、文書順、NUL 優先、過剰拒否防止を追加。
  - CR/LF 受理固定 4 param を拒否側へ反転。
  - CR/LF legacy g1 の validation / activation report 反転を追加。
  - 受理 hash と legacy hash は標準ライブラリによる独立計算でも literal を照合。
  - 現行契約 hash、既存 g1 pin、path inventory 38 の既存テストは変更なし。

確認済み:

- Python AST parse: 2 ファイルとも成功。
- `git diff --check`: 成功。
- 独立 inventory: 38 path、CR/LF matrix 76 cases。
- legacy CR/LF hash literal と全受理側 literal: 独立計算と一致。
- 変更ファイルは所有範囲の 2 件のみ。
- pytest は実走していません。状態は「実装済み・未実走」です。

所有外への静的波及候補は、同 module 内の `validate_condition_freeze_at` と `prepare_revision`、発効層の `semantic_contract_sha256` caller、ならびに activation report を消費する preregistration invariant・predicate・trial registry 系テストです。発効層自体の `_safe_path` と理由語は変更していません。

## 総括

- CR/LF path を凍結層で fail-closed 拒否する実装を完了。
- NUL の理由語・pointer・単一契約内の全域優先を維持。
- F1〜F7 と 38×2 matrix を実装。
- 受理 hash は production から独立して固定。
- 現行契約・g1 pin は不変。
- 編集は指定 2 ファイルのみ。
- pytest は親実走待ち。