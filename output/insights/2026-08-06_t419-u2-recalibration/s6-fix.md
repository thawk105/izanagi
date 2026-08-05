実装済み・未実走です。指定されたコード・テスト4本だけを変更し、docs 編集・commit は行っていません。

| 所見 | 状態 | 対応 |
|---|---|---|
| F-1 | partial | public 述語の shape→policy→band の旧短絡順を復元。band 走査も先頭違反で短絡し、診断側だけ全件評価。`OverflowError` を構造化拒否に変換し、指定2反例を追加 |
| F-2 | partial | `rejection.json` に全48 samples、tolerance、method、governor、canonical profile SHA-256を保存。保存入力から canonical 判定を再計算する assertion を追加 |
| F-3 | partial | clock-only early rejection の reason を exact 1件に修正 |
| F-4 | partial | temp write を cleanup 範囲へ移動。部分ファイル削除と、削除不能時の構造化 reason を追加 |
| F-5 | partial | `not_evaluated` をテスト側 literal list 化。quality/reason/tolerance/禁止成果物を exact 固定 |
| F-6 | partial | final assembly/schema validation、published-bytes 検査を追加し、dynamic-pre 名称を具体化 |
| F-7 | partial | 許可された3 parameter node＋metamorphic 1 nodeだけを、旧保証を維持して強化 |
| F-8 | partial | rename 後の target bytes だけを再読し、判定・入力SHA・policy identityを `published-self-comparison.json` へ記録。不一致時も published artifact は削除しない |
 
`partial` の理由は、Pegasusログインノード上のためpytestを実走していないことです。静的検査は以下が成功しました。

- 変更4ファイルの `python3 -m py_compile`
- `git diff --check`
- 変更対象が指定4ファイルだけであることのexact検査

未実走の焦点nodeは、追加したoverflow/診断、early rejection、temp cleanup、published-bytes改竄検査、および以下の許可4 nodeです。

- `test_cli_effective_clock_self_failure_is_quality_rejected_before_publish[0|24|47]`
- `test_effective_clock_policy_metamorphic_wiring_producer_loader_issuer_consumer_self`

所有外への波及候補は、`receipt_matches_contract` 経由のcampaign loop、floor、oracle driver/report、ratified freeze、`silo_ladder_rung1` のlive/receipt再導出、および対応するenv/floor/oracle/silo consumer testsです。共有fixtureは `_profile`、`_pegasus_shaped_probe`、`_invoke`。新sidecarによるattempt manifest/collectorへの波及も未実走です。

既存期待値の変更は、F-7で許可された4 node以外は0件です。受理集合は、裁定済みのpolicy再束縛拒否とpublished-bytes不一致のfail-closed以外、追加で拡大・縮小していません。

## 総括

- public述語の例外・短絡回帰を修正した。
- early rejectionを完全なprofile/input/hash proofへ強化した。
- reason重複、temp orphan、`not_evaluated`漏れを修正した。
- publish後bytes再読検査と専用receiptをproductionへ追加した。
- 指定4ファイル以外、docs、commitには触れていない。
- 静的検査は成功、pytestはPegasus規律により未実走。
- 残るriskはconsumer/collectorを含む計算ノード実走が未完なこと。