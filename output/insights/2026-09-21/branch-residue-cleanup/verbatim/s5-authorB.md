## 変更一覧

- `tools/check_docs.py:286`: 予算を `TextLimit(7_055, 110)` へ。
- `tools/check_docs.py:629`: DW-O28 literal を現物と一致する 994 bytes へ。
- `tools/check_docs.py:788`、`orchestrator/tests/test_check_docs.py:579`: SHA-256 を `3d675f09e6eea7eb6647e0be78f4843fecd6407662cbbe4e849844f559955c2b` へ。
- `orchestrator/tests/test_check_docs.py:189,9499,9696`: DW-O28 fixture と byte assertion を 994 へ。本文の `993` ではなく、正本 `authorB-targets.md` に従いました。
- `orchestrator/tests/test_check_docs.py:630,9958,9959,9964`: command 全文・予算・長さを 7,055 bytes へ。
- `orchestrator/tests/test_check_docs.py:9966,9973`: 超過期待値を 7,059 bytes／予算 7,055 bytes へ。padding は LF＋3 bytes で成立。

## 検証・波及

`python3 tools/check_docs.py` は **rc=0、違反 0 件**。`git diff --check` も成功。

静的確認で literal の現物一致、独立 hash、既存負例の 1-byte 変更成立を確認しました。共有 fixture を使う文書契約テストへ波及します。所有外 caller・dispatch 契約・他の pin は変更していません。

`test_check_docs.py` は **実装済み・未実走**。親の計算ノード dispatch 待ちです。

## 総括

所有する 2 ファイルのみ更新しました。
SKILL の hash は不変です。
commit・branch 操作・push は行っていません。