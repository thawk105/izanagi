## must-fix

**1. [real・親の実測＋静的読解] 旧pinのfixtureが、歴史admissionへ到達する前に壊れる。**

[test_artifact_admission.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/tests/test_artifact_admission.py:60) は `build_admission.CURRENT_PIN` とテスト自身の定数だけを旧pinへ変更する。しかし `_new_schema_campaign` は同 `:847` から `receipt_support.log_receipted_commit` を呼ぶ。

その先の [commit_receipt_support.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/tests/commit_receipt_support.py:83) は、別モジュールへimport済みの**現行pin**で proof source を作り、`:102` で `derive_build_admission` を呼ぶ。比較先だけ旧pinになっているため、`build_admission.py:674` のstock条件が偽となり、`:701` で拒否される。最初のcampaign用receiptではなく、**後段のCOMMIT proof用receipt生成が破綻する**経路である。

これは親の [s6-red-evidence.md:23](/work/1/SFC/tanab/dev-wave-artifacts/t2125-historical-policy-version/s6-red-evidence.md:23) の14件失敗と整合する。私自身は再実行していない。

`test_layer3_report.py:1898` にも同じpatch構成がある。そのため同 `:1918` のclassification単独負例にも到達せず、schema相殺の変異検査も現在は機能していない。fixtureの旧policy発行区間を、呼び出すproof生成処理を含めて整合させる修正が必要。

**成果物影響：本題であるpin前進後の歴史閲覧と、構造・bytes・epoch・schema境界の追加検証が未成立のまま残る。**

## 重い所見

**2. [refuted・静的読解＋AST比較] R2違反・現行比較の恒真化は確認しなかった。**

`build_admission.py:839` が記録側から渡す比較値は、policy SHAと `repo_stock_pin` の2点だけ。残る比較は次のとおり現行値を参照する。

| 比較 | 実装 |
|---|---|
| generator登録 | `build_admission.py:589` の `GeneratorId(...)` |
| review登録 | 同 `:769` の `ReviewId(...)` |
| coder authority | 同 `:785` の `_AUTHORITY_KIND` |

現行wrapperは同 `:728` で `expected_policy.sha256` と `CURRENT_PIN` を渡す。呼び出し側も `artifact_admission.py:1011` で独立に現行policyを生成し、`:1012` で記録policyと比較する。receipt自身から期待値を取り出していない。

共有本体について、baseとのAST比較を実施した。build admissionは指定2比較の置換、WALはreceipt validator呼び出しの置換だけで一致した。

**成果物影響：調べた抽出差分に、現行receiptの拒否集合を広げる変更はない。**

**3. [refuted・静的読解] R3の3負例が入口拒否やouter SHA不一致に隠れる問題はない。**

`test_build_admission.py:136` の `entry="current"` を個別に追った。

| 負例 | 到達根拠 |
|---|---|
| 旧stock pin | `:149` でsource commitだけ変更、`:159` でouter SHAを再計算。`build_admission.py:760` のpin比較で拒否 |
| 未登録generator | `:152` でID変更、`:153` でnested SHA、`:159` でouter SHAを再計算。`build_admission.py:589` の登録比較で拒否 |
| 異なるauthority | `:158` でauthority変更、`:159` でouter SHAを再計算。`build_admission.py:785` のauthority比較で拒否 |

`:162` は現行policy SHAの維持を確認する。`:187` の伝播SHAもreceiptに一致し、`:179` と `:190` は各比較固有のエラー文言を要求する。WAL側は `wal.py:2185` でreceipt検査へ入る。旧policyのlock入口拒否を検出成功に数える構成ではない。

**成果物影響：R3の3比較を弱める退行を検出する負例は存在する。所見1の赤14件とは別である。**

**4. [refuted・静的読解] 指定された歴史経路の構造検査は脱落していない。**

| 検査 | 現在の経路 |
|---|---|
| attempt topology | `artifact_admission.py:1398` → `wal.py:2142` の共有本体 |
| knowledge／backoff／contract | `wal.py:2154`、`:2157`、`:2160` |
| historical COMMIT contract | `artifact_admission.py:1409` → `:1210` |
| trigger bindings | 同 `:1420`、`require_build_start=True` |
| trigger provenance | 同 `:1427` |
| build_start source／genome／lock commit | 同 `:1440` |
| variant | 同 `:1452` |
| lock／WAL bytes再読照合 | 同 `:1460` |

通常contract検査が歴史identityだけでは戻り得る点も、専用のhistorical COMMIT検査が引き続き補っている。

**成果物影響：指定検査の削除による不正な歴史材料の受理拡大は見つからない。ただし追加テストによる裏付けは所見1で阻まれている。**

**5. [refuted・静的読解] 新classificationからcertifiedへ昇格する経路は、指定箇所では成立しない。**

`artifact_admission.py:1463` は新classificationに `historical-not-reclassified` を組み合わせる。このstatusは以下で拒否される。

- `layer3_report.py:279`、`:959`
- `autonomous_trial_completeness.py:239`、`:4798`

completenessの `:240` はclassificationも `admitted-new-schema` に限定する。さらに、**`layer3_report.py:966` と `autonomous_trial_completeness.py:4965` のcertified再admissionは残っている**。それぞれ後続でdecisionも照合する。

`layer3_schema.json:17` のcertifying側enumは従来2値だけで、`:298` の新classification追加を相殺する。epoch型だけをpolicy差の防壁として数えてはいない。

**成果物影響：歴史decisionをそのままcertifying成果物へ昇格させる変更は確認しなかった。**

**6. [refuted・静的読解] 歴史policy型がruntime／recoveryへ流入する変更はない。**

`wal.py:2126` と recovery入口 `:2500` の `type(admission_policy) is not BuildAdmissionPolicy` は維持されている。runtime validatorも `build_admission.py:725` のexact型検査へ到達する。`wal.py:2793` の第2照合も変更されていない。

**成果物影響：歴史policy値を渡して現行runtime検査やrecoveryを通すことは、これらの公開された呼び出し経路ではできない〔読解〕。**

## 軽い所見 / nit

**7. [refuted・差分確認] 既存テストの削除・改名・期待値変更・skip／xfail化はない。**

`git diff d97c423bd -- orchestrator/tests/` の削除行を確認した。`---` のファイルヘッダを除く削除行は **0行**。変更は3ファイルでそれぞれ `205/0`、`104/0`、`32/0` の追加／削除だった。

**成果物影響：既存テストの弱体化によって退行を隠す変更はない。**

**8. [refuted・静的読解] 追加されたpolicy形検査に、全入力で恒真・恒偽となる検査は見つからない。**

`build_admission.py:260` のkey集合と `:264` のschemaは独立literalで、入力から期待値を生成していない。`:289` は余分keyで、`:290` はschema違いで偽になる。型検査も異型入力を拒否する。`test_artifact_admission.py:133` は空WALで形だけを変え、receiptの不整合による先行拒否を避けている。

**成果物影響：malformed policyを識別する検査として機能する構成である。記録policyの真正性を証明するものではない。**

独立したnitはない。

## 実装子の報告への指摘

**9. [real・親の実測＋静的読解] 実走待ちだけでなく、fixture修正が必要になっている。**

[s5-impl.md:71](/work/1/SFC/tanab/dev-wave-artifacts/t2125-historical-policy-version/s5-impl.md:71) の「テスト基盤の復旧後に実走検証が必要」は提出当時の記述だが、現在の残作業はそれだけではない。親の実測と所見1により、追加テスト素材の修正が必要と判明している。

**成果物影響：基盤復旧・再実行だけでは、旧pin正例と関連する境界検査を成立させられない。**

**[refuted] 緑の捏造や既存テスト不変更の虚偽は認めない。** 同報告 `:23` は本体未起動、`:51` は静的確認まで、`:63` は変異未確認と明記している。共有本体のAST一致と既存テスト本文不変更も今回の確認と一致した。

## 総括

**must-fixは旧pin発行fixtureの不整合1件。** これが親の赤14件と、schema単独負例を含む検証未到達を説明する。

指定されたproduction境界には、R2逸脱・現行検査の弱体化・構造検査脱落・certified昇格・exact型境界の緩和を確認しなかった。ただし、pin前進という本題の正例はまだ立証されていない。

本レビューは静的読解、読み取り専用git、AST比較による。pytest・変異検査・ファイル書き込み・commitは行っていない。