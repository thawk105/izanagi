## 変更前の受理・拒否挙動

- `tools/acceptance_receipt_signature.py:46-48,127-129,185,212,351`（変更前）では、`lease_generation` と `expected_lease_generation` はともに `[0-9a-f]{64}` 完全一致のみ受理していました。
- `"not-acquired"`、大文字、前後空白、63/65 桁、非16進文字、空文字、非文字列は `invalid lease_generation` または `invalid expected_lease_generation` で拒否されていました。
- `tools/acceptance_issuer_reference.py:100,463-464`（変更前）も `[0-9a-f]{64}` のみ受理していました。

## 実装した内容

| file:line | 変更内容 | 裁定のどの項目に対応するか |
|---|---|---|
| [tools/acceptance_receipt_signature.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:16) | 取得ごとの粒度、非取得 marker、自己申告、関門が不可避でない旨を明記。 | signature 5、D1443 |
| [tools/acceptance_receipt_signature.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:53) | `LEASE_NOT_ACQUIRED = "not-acquired"` と厳密 union helper を追加。strip・casefold・正規化なし。 | signature 1–2 |
| [tools/acceptance_receipt_signature.py:202](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:202) | projection、canonicalization、expected の3経路だけを union 検査へ変更。他 hash 検査は不変。 | signature 3–4 |
| [tools/acceptance_issuer_reference.py:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:15) | claims 表を取得あり・なしと live lease 非検査の説明へ更新。 | issuer 2 |
| [tools/acceptance_issuer_reference.py:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:464) | issuer の入力検査を署名 module の helper へ委譲。`--lease-generation` は単一 required option のまま。 | issuer 1、3 |
| [orchestrator/tests/test_external_acceptance_signing.py:294](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/orchestrator/tests/test_external_acceptance_signing.py:294) | 実 fixture・実 Ed25519 鍵を使う T1〜T5 を追加。既存 pin・期待値・root field 集合は不変。 | T1〜T5 |

公開5関数の signature は HEAD と AST 比較し、すべて `signatures_unchanged=True`。`git diff --check` も rc=0 です。

## 実走結果

- pytest: `python3 tools/run_tests.py ... test_external_acceptance_signing.py -q` は rc=16。Pegasus の `qstat -Q` preflight で停止し、`child_started=false` のため実走 nodeid はありません。生成された dispatch receipt directory は削除済みです。
- したがって pytest は「実装済み・未実走」です。計算ノードへの job 投入は発生していません。
- plain runner: `python3 -B orchestrator/tests/test_external_acceptance_signing.py` は rc=0、22 passed / 0 failed。追加5本を含む file 内の全 `test_*` を実走しました。
- 制約 meta-test の探索・pytest 実走は、射影外 file を読めないため未実施です。

## 波及の静的列挙

親 brief の全 repo grep によれば、consumer は署名 module と issuer、両者の repo 内 importer は当該 test file のみです。指定3 file 内の全転送箇所は次のとおりです。

- 署名 module: `:414`
- issuer: `:518, :530, :578`
- test: `:126, :149, :159, :227, :244, :300, :317, :323, :331, :346, :361, :382, :419, :429, :469`

公開 signature、CLI option、production-v5 fixture、canonical hash/length、root field 集合は変えていないため、既存 caller の変更は不要です。waiter/lander からの配線はなく、repo 外運用 copy は未測定です。

## 期待赤

この差分単独で想定する赤は、親所有の docs が未 land であることに対応する `check_docs.py` の worklog・phase・decisions 同期 finding のみです。コード・既存 signing test に期待赤はありません。pytest rc=16 は test failure ではなく dispatch infrastructure failure です。

## 総括

厳密な `"not-acquired"` marker と取得ごとの意味論を、指定3 file だけに実装しました。  
状態引数、追加 CLI option、pair gate、公開 signature 変更はありません。  
plain runner は全22本 rc=0、pytest は子未起動のため未実走です。  
親は対象 pytest、関連 meta-test、docs land 後の checker を実測してください。  
working tree には指定3 file の未 commit 変更だけを残しています。