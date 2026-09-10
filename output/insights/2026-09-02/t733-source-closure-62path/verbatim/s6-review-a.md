## 総括

静的な敵対レビューでは、正しさロジックと裁定 §10 の不変条件はすべて維持されています。  
ただし、裁定 §3 と異なる保証説明が 3 個の docstring に残っているため、文言修正後の統合を推奨します。  
exact 62、発見集合 131、未収載 69、固定 known-answer、receipt slice は実値で一致しました。  
pytest は制約どおり実走しておらず、緑とは判定していません。

## 不変条件の逐一照合

- 守られている — 規律 2 と anomaly 検出時の即 reject に関する分岐は変更されていない。
- 守られている — fig2b / fig2c / fig4 の PNG、PDF、provenance JSON は commit 差分に含まれず、bytes は不変。
- 守られている — 既存 24 path は親 commit の tuple と順序・綴りが完全一致する。
- 守られている — `_CAMPAIGN_VERIFIER_EPOCH_DOMAIN` は `campaign-verifier-epoch/v1` のまま。
- 守られている — `_require_verifier_epoch_for_purpose` は D1163 の可用性検査だけを行い、記録 closure と現行 closure の bytes 差を拒否していない。
- 守られている — curated exact tuple のままで、静的 AST 解析器を正本にしていない。
- 守られている — 歴史 grammar decoder は追加されず、pre-T733 exact-24 専用拒否テストも追加されていない。
- 守られている — 新規 gate、台帳、一般化はなく、変更は production 3 file、test 3 file に限定されている。
- 守られている — docs は編集も commit もされておらず、worktree も clean。

## real な所見

1. 裁定 §3 と異なる保証説明が docstring に残っている  
   file:line: [artifact_admission.py:162](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:162)、[artifact_admission.py:903](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:903)、[artifact_admission.py:984](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t733-source-closure-transitive/orchestrator/campaign/artifact_admission.py:984)  
   所見: `exact 24` を `exact 62` に替えただけの旧説明が残り、`curated`、未収載 69、非 import 委譲、`source-import 推移閉包ではない`という裁定上の限定が欠落している。  
   成果物影響: artifact 値と受理集合は変わらないが、`help()`、pydoc、ソース参照では裁定より強く不完全な保証説明が表示される。  
   具体的な修正案: 3 箇所の範囲説明を `CAMPAIGN_VERIFIER_EPOCH_SCOPE` と `CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE` が保証文言の正本である、という参照だけに置換するか、裁定 §3 の 2 文を逐語で記載する。

## refuted な所見

1. refuted — production の 62 path は旧 24 pathと `suffix38.txt` の 38 path に完全一致し、suffix は辞書順かつ重複なし。静的 import 再導出も 131 module、未収載 69 moduleで一致した。

2. refuted — runtime の `CAMPAIGN_VERIFIER_EPOCH_SCOPE` と `CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE` 自体は裁定 §3 の逐語と完全一致する。

3. refuted — テストの削除、skip、xfail、期待値緩和はない。exact key 検査と全 62 member の drift 検査が維持されている。

4. refuted — 固定 known-answer は production tupleから独立再計算して一致した。ordered-list SHA-256 は `b274...067a`、synthetic E1 は `E1:7892...04e9` で、working tree hashなどの揮発値を含まない。

5. refuted — `_RECEIPT_IMPLEMENTATION_PATHS` の実値は旧 tuple の 19:24 に当たる 5 pathだけで、新規 suffix 38との積集合は空。

6. refuted — 受理集合の変化は意図された exact-24 map から exact-62 mapへの非互換置換だけで、subset 許容などの追加拡大はない。

## nit / 裁定パッケージ候補

- `test_enforcement_source_closure_is_the_independent_exact_twenty_four_paths` など旧 count を含む nodeid は実態とずれるが、duration ledgerとの互換目的が報告されており nit。今回の修正対象にはしなくてよい。
- 新しい裁定パッケージ候補はなし。旧 exact-24 lock の歴史 decode 問題などは、裁定 §5 の所有外事項として据え置かれている。