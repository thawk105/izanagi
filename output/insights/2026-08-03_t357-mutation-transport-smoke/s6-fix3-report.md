指定の [compare_verdicts.py](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:437) だけを修正しました。

### 修正内容

- `tool_sha256` gate

  - Before: `ledger["tool_sha256"] == tool["sha256"]`
  - After: `ledger["tool_sha256"] == _json_sha256(tool)`
  - 旧 gate に含まれていた `tool_identity.sha256` の形式検査は独立 gate として維持しました。
  - `tool_identity.sha256 == head_blob_sha256` も維持しています。
  - 実ファイル SHA-256、identity の `sha256`、`head_blob_sha256` は静的検算で全て `65e3390d...` と一致しました。

- `command[0]` 差

  - `executable_path` を経路差の除外から外し、解決済み path の完全一致 gate にしました。[該当箇所](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:686)
  - `runner_identity.command[1:]` と `procedure.test_command[1:]` は個別 gate で厳密一致を要求します。
  - `command[0]` だけは `executable_path` 一致時に「同一実体の別綴り」と分類しますが、生値の差は完全一覧へ残します。[表示処理](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:738)
  - `executable_path` 不一致は NO-GO です。

- `executable_sha256`

  - verdict 除外は維持しました。
  - 「非等価だが verdict に効かない」名前付き観測として独立表示し、login node／計算ノードの含意も明記しました。[表示処理](/work/1/SFC/tanab/dev-wave-jobs/t357-mutation-batch/g01/compare_verdicts.py:760)

### 同種 hash gate の確認

[mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t357-mutation-batch/tools/mutation_harness.py:169) の生成側と比較しました。

- `runner_sha256`: `_runner_sha256(identity) == _json_sha256(identity)`。比較器も同じで、誤りなし。
- `registration_sha256`: 全 registration object／mutation preflight object をそれぞれ `_json_sha256`。比較器も同じで、誤りなし。
- `collection_sha256`: collection object 全体を `_json_sha256`。比較器も同じで、誤りなし。

### 静的確認

- 行数: 723 → 786 行。
- `gate.require` の AST 件数: 80 → 84。
- 旧 gate 79 件は AST 上不変。削除 1 件は誤った `tool_sha256` gateのみで、修正版を含む5件を追加しました。
- schema／比較 field 集合は12/12すべて不変。
- 除外は37→36件。減ったのは `executable_path` だけで、新しい除外はありません。
- AST parse: OK。
- 比較器・pytestは未実行です。実走は親に残しています。
- repo の tracked/index diff は空です。既存の untracked insight treeには触れず、docs・ledger・spec・worktree・他のg01ファイルも編集していません。commitもありません。
- 外部 caller は `g01/README.md` の比較手順、共有入力は `spec.json` と両 ledgerです。consumer testの追加・変更はありません。

## 総括

- `tool_sha256` を identity object 全体の canonical JSON hashへ是正した。
- `command[0]` は解決済み `executable_path` 一致時だけ別綴りとして扱い、生差分は表示に残した。
- 他の hash gate (`runner`／`registration`／`collection`) に同種の誤りはなかった。
- gate総数増加、比較field不変、除外縮小により、指定2点以外を緩めていないことを確認した。