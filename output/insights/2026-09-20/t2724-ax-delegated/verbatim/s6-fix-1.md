## 変更差分

standalone `gate_check` の tmp repo 補完テストを1本追加し、指定の docstring 2箇所を修正しました。

`git diff --stat`:

```text
 orchestrator/campaign/s8b_ratified_freeze.py       |  8 +++--
 orchestrator/tests/test_s8b_binding_driftguards.py | 35 +++++++++++++++++++++-
 2 files changed, 40 insertions(+), 3 deletions(-)
```

`git status --porcelain --untracked-files=all`:

```text
 M orchestrator/campaign/s8b_ratified_freeze.py
 M orchestrator/tests/test_s8b_binding_driftguards.py
```

## fix-1 の経路根拠 (gate_check の行番号)

`_t080_repo(receipt="never-issued")` は active pointer を作りません。`s8b_oracle_driver.py:639` の loader が `no-active` を返すと、`:640–647` は `standalone_manifest_verification=True` と `ratified_error` を指定して core へ進みます。

core の `:534–546` が manifest を検証し、binding schema 例外を `manifest-verify:` refusal へ翻訳します。新テストは承認済み spec を注入し、memo を使わず、この翻訳と `freeze-ratify: [no-active]` の集約を検査します。

## 静的列挙 (anchor 行の不変・consumer への波及)

- production file は対象 docstring 以外の全 bytes が HEAD と一致。指定の変異 anchor も不変です。
- 既存テストの関数本体・期待値は不変。既存6 node の名前・root・memo・hold は変更していません。
- 共有 fixture、他 consumer、production の実行ロジックは未変更です。

## 未実走・限界

2ファイルの `py_compile`、静的比較、`git diff --check` は成功しました。

**テストは実装済み・未実走**です。拒否全文を実測できないため、新テストは `any` 2条件と拒否件数2件で検査しています。pytest・変異検証は親の dispatch に引き継ぎます。

## 総括

RA-1、RA-8 の3、RB-8 の docstring nit を修正しました。編集は指定2ファイルのみ。add・commit・push はしていません。