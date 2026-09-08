## 実装した内容

- [paper_story_a2_certification.py:4533](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/campaign/paper_story_a2_certification.py:4533): 再読した full evidence の receipt chain 検査と、裁定どおりの `SchemaChainError` 文言を追加。レビュー B 所見 1 対応。
- [test_paper_story_a2_certification.py:3010](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:3010): 再読 receipt bytes と manifest SHA を検証する正例を追加。レビュー A 所見 2 対応。
- [test_paper_story_a2_certification.py:3037](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2366-full-cert-rederive/orchestrator/tests/test_paper_story_a2_certification.py:3037): forged full fields の背後にある partial receipt chain を拒否する負例を追加。
- レビュー A 所見 1 の `dict ==` 問題は裁定どおり変更していない。

## 実走した検査

- `orchestrator/tests/test_paper_story_a2_certification.py` 全 node:
  - rc=0
  - 175 passed / 0 failed
- 最終復元後の新規 2 node:
  - `test_full_materializer_writes_reread_receipt_bytes_not_supplied_bytes`
  - `test_full_materializer_rejects_reread_partial_receipt_chain_behind_forged_full_fields`
  - rc=0、2 passed / 0 failed
- M06 一時変異:
  - chain 条件を `if False:` に変更して負例を単独実行。
  - rc=1、1 failed。`DID NOT RAISE SchemaChainError` となり、fix なしでは materialize が成功することを確認後、即時復元。
- M05 一時変異:
  - `return canonical_full_evidence` を `return evidence` に変更して正例を単独実行。
  - rc=1、1 failed。生成 receipt が forged bytes だったため byte 一致 assert で失敗することを確認後、即時復元。
- `git diff --check` は rc=0。

## 波及可能性

- 所有外の `materialize` 直接 caller: v4 full を装いながら、再読すると partial chain になる入力は新たに `SchemaChainError` となる。
- production `_collect_command`: canonical full chain を渡す通常経路の挙動は不変。
- 共有 fixture:
  - `_full_materializer_forgery_case` は既存 3 負例と新規正例で共有。
  - `_partial_materializer_forgery_case` は既存 partial 負例と新規 cross-chain 負例で共有。
- consumer test: materialized receipt bytes と artifact manifest SHA は supplied copy ではなく再読 evidence に由来することが固定された。
- legacy v3 full、v1/v2 partial、成果物形状・schema 識別子への変更はない。

## 未了・判断を仰ぐ点

なし。commit、stage、stash、台帳・docs 編集は行っていない。最終 `git status --short` の変更対象は指定された 2 file のみ。

## 総括

段 6 裁定の fix 1 を指定 2 file に実装した。  
全 175 node と最終状態の新規 2 node は緑。  
M05・M06 の一時変異はいずれも期待どおり新規 test が検出した。  
scope 外の JSON 型比較問題には触れていない。