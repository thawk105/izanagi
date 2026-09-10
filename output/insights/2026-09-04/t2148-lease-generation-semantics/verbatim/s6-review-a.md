## must-fix

無し。

## nit

- 対象 ([orchestrator/tests/test_external_acceptance_signing.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/orchestrator/tests/test_external_acceptance_signing.py:352)): `test_unreserved_non_sha_lease_generation_is_rejected_on_all_paths` は実装を変更前へ全戻ししても緑になるため、新機構の実在証拠としては冗長です。ただし、union を過度に広げる M1 の防壁としては有効です。成果物影響はありません。

## 正しく実装されていた点

- 裁定のプラン v2 と一致しています。`lease_acquired`、`expected_lease_acquired`、pair helper、新 CLI option、mutually-exclusive group、早期の重複検証はありません。
- 新しく受理される通常の文字列値は、[共通 helper](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_receipt_signature.py:141)による完全一致の `"not-acquired"` だけです。前後空白、大文字小文字違い、部分一致、Unicode 変種・正規化、別 spelling は拒否されます。
- projection（同ファイル:202）、canonical payload（:229）、expected（:368）の3点が同じ helper を使用し、issuer（[acceptance_issuer_reference.py:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2148-lease-generation-semantics/tools/acceptance_issuer_reference.py:464)）もそこへ委譲しています。片側だけ広い、または狭い経路はありません。
- 公開関数の signature、引数名、requiredness は不変です。既存 caller に適応変更はなく、テスト内の private helper `_signed_control` だけが既定値を維持したまま拡張されています。
- 固定公開鍵、Ed25519 検証、v5／signed-v6 の exact root field、canonical JSON、context mismatch、fail-closed 経路は弱化していません。取得あり経路の canonical hash・length pin と既存 root-field expectation も未変更です。
- T1 は実 production-v5 fixture、生成した実 Ed25519 鍵、projection／canonicalization／署名付与／検証の実体を通します。stub や monkeypatch はありません。
- T2・T3 は取得あり／なし双方の context mismatch を検査し、T4 は指定された不正値を3経路で拒否、T5 は実 parser と issuer の共通検査委譲を確認しています。
- 提示された `s5-diff.patch` と作業木の3ファイル差分は逐語一致し、差分外の変更はありません。既存の期待値、literal pin、canonical hash、length pin、root-field 集合も変更されていません。

## 総括

must-fix はありません。最も重い留意点は、T4を新 marker 機構の実在証拠には数えられないことです。  
実在はT1・T2・T3・T5が担い、受理集合は完全一致の `"not-acquired"` だけに閉じています。  
本レビューでは制約どおりテストを実走していません。  
親は変更後の対象 pytest と事前登録済み M1〜M4を実測し、M2・M3が同一 node だけで kill される場合は裁定どおり独立証拠から外してください。