## 所見 RA-1: exact-62 が certified に到達する経路は確認できない

**主張:** certified 受理集合が広がったという疑いは反証できる。

**根拠 (file:line):** `artifact_admission.py:1012` は `HISTORICAL_RAW` だけを歴史 decoder に送る。certified は通常 decoder → `campaign_lock.py:637` の `_validate_authority` → 同 `:402` の現行63キー照合で exact-62 を拒否する。encoder も同 `:833` で通常 decoder による自己検証を行う。resume の `ident.verify_against_lock` も `ident.py:363` で通常 decoder を通る。

さらに exact-62 の epoch は `artifact_admission.py:1099` で歴史型になり、同 `:1146` の目的別 gate が certified への流入を拒否する。`CertifiedCampaignView.__post_init__` も同 `:451` で通常 `CampaignVerifierEpoch` の **exact type** を要求し、歴史 subclass を排除する。

**real / refuted:** refuted。  
**must-fix か nit か:** 修正要求なし。  
**成果物影響:** exact-62 が certified 選択へ追加される経路はない。

## 所見 RA-2: admission の順序負例だけでは wire 順序検査の独立性を証明できない

**主張:** `test_unknown_t733_exact62_grammar_is_rejected_for_both_read_purposes[order]` 単独では、名目上の順序検査を保護した証拠にならない。ただし専用の直接検査が補っている。

**根拠 (file:line):** `test_artifact_admission.py:3073` は非canonicalな wire を作り、`:3084` は広い `codec validation failed` だけを見る。順序検査を緩めても、`campaign_lock.py:721` の outer canonical 検査で拒否されれば、この admission 負例は緑のままである。

一方、`test_campaign_lock_codec.py:628` は兄弟 validator を直接呼び、canonical 検査を介さず順序違反を検査する。同 `:654` は有効な grammar を保持したまま map 順序だけを変え、authority の順序検査を直接保護する。62件の committed mismatch も `test_artifact_admission.py:3101` で有効なhexを維持し、`:3105` で専用エラーと対象pathを要求しており、digest形式検査による先行拒否ではない。

**real / refuted:** real。ただしテスト群全体の保護欠落という疑いは refuted。  
**must-fix か nit か:** nit。独立性の説明を admission 負例だけに帰属させないこと。  
**成果物影響:** 現在の受理集合・成果物値への影響はなく、検査証拠の説明範囲の問題である。

## 所見 RA-3: 固定 known-answer の must-fix は満たされている

**主張:** production と期待path列を同時に並べ替えても検出される。

**根拠 (file:line):** `test_artifact_admission.py:380` と `:381` の期待 E1・path hash は固定文字列。`:3005` はproduction列から計算した**実測側**hashを固定値と比較し、`:3020` は返却epochを固定E1と比較する。期待値の再計算ではない。

ASTから取り出したfixture定義による静的照合でも両固定値は一致した。先頭2要素を交換した列のhashは固定path hashと不一致になることを確認した。pytestやproduction関数は実行していない。

**real / refuted:** refuted。  
**must-fix か nit か:** 裁定のmust-fixは充足。  
**成果物影響:** 宣言順の変更による歴史epochの変動を、期待列との同時変更でも検出できる。

## 所見 RA-4: 既存テストは不変だが「match依存の既存2テスト」という前提は一致しない

**主張:** 既存期待値・parameter・matchの変更はない。ただし指定された「2テスト」の数は現物と異なる。

**根拠 (file:line):** 親commitとの比較で、既存codec 29関数・admission 90関数は本文が一致し、decoratorを含むASTも一致した。`test_campaign_lock_codec.py:341` の missing parameter は現行tuple全件のままで、workerを除くparameterも残っている。現行tuple自体も不変。

既存の `match="歴史 grammar"` は同 `:264` の1関数にある。順序負例 `:269` は `CampaignLockCodecError` のみを要求する。追加された `:628` と `:632` は既存テストではない。

**real / refuted:** 既存改変は refuted。「既存2テスト」という説明の不一致は real。  
**must-fix か nit か:** nit。  
**成果物影響:** 既存の拒否集合を期待値変更で隠す変更はなく、説明の訂正だけが必要。

## 所見 RA-5: exact-24 の検証とepoch導出は維持されている

**主張:** この差分によって既存exact-24のepochが動く根拠はない。

**根拠 (file:line):** `campaign_lock.py:449` の既存validatorは親commitとソース文字列が一致し、検証順・例外文面・返却構築式が不変。exact-24 は同 `:719` から引き続きこのvalidatorへ入る。

`artifact_admission.py:1034` の明示path検証はexact-24について同じ引数を渡す。`:1087` のepoch preimage式、domain、exact-24 tuple、scope文字列は不変で、`:1092` の歴史epoch構築も従来どおり。新しいscope対応検査はexact-24に従来の24path順序を要求する。

**real / refuted:** refuted。  
**must-fix か nit か:** 修正要求なし。  
**成果物影響:** 同じexact-24記録mapから得るE1文字列・scope・返却型は変わらない。

## 所見 RA-6: 未知grammarはexact-24分岐へ進むが、そこで受理されない

**主張:** `else` は存在するが、未知grammarを許容するfallbackではない。

**根拠 (file:line):** `campaign_lock.py:714` はsorted exact-62キー列との完全一致を要求する。不一致は `:719` でexact-24 validatorへ進むが、`:460` がsorted exact-24列との完全一致を要求するため、61件・未知path付き63件・同数別集合62件・順序違い62件はすべて拒否される。

authority直接構築も同 `:279` のordered tuple白名単と `:284` のmap順序照合で拒否する。対応する負例は `test_campaign_lock_codec.py:610` と `:647` にある。新しいsupersetは未知pathを使い、既知の現行63grammarには変化しない。

**real / refuted:** refuted。  
**must-fix か nit か:** 修正要求なし。  
**成果物影響:** 歴史閲覧の拡張は収載したexact-62 grammarに限られ、未知grammarの成果物は追加受理されない。

## 所見 RA-7: 指定scope外への実装変更はない

**主張:** 材料レポート対応や追加frameworkへのscope拡張はない。

**根拠 (file:line):** `impl-diff.txt` とcommit `c8dd0012a` の変更対象はproduction 2・test 2ファイルのみで、作業ツリーの4ファイルもそのcommitと一致した。`layer3_report.py`、`contract_loader_binding.py`、B10の2ファイルは変更対象外。既存 `CAMPAIGN_VERIFIER_EPOCH_SCOPE` を含むproductionの既存定数も不変。

`layer3_report.py:116` は引き続き通常decoderを呼ぶため、exact-62の材料レポート生成は再拒否される。新規gate・台帳・frameworkの追加も差分にはない。

**real / refuted:** refuted。  
**must-fix か nit か:** 修正要求なし。  
**成果物影響:** 中央歴史APIの受理だけが拡張され、材料レポート対応や台帳更新はこの実装差分には含まれない。

## 総括

最も危険な疑いはexact-62 epochの通常型への誤分類だが、歴史型生成・目的別拒否・viewのexact型要求で反証できた。  
採否判定：**静的レビューとして採用可。must-fixなし、証拠説明にnit 2件。**  
pytest・実成果物3本の受入確認は実施しておらず、その成功を本レビューの結論には含めない。