## must-fix

**1. 【real／親の実測＋静的読解】旧 pin fixture が壊れており、主題の pin 前進を立証できていない。**

[test_artifact_admission.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/tests/test_artifact_admission.py:60) は `build_admission.CURRENT_PIN` とテスト自身の pin を変更する。しかし `_new_schema_campaign` は同ファイル `:847` で `receipt_support.log_receipted_commit` を呼ぶ。

その先の [commit_receipt_support.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/tests/commit_receipt_support.py:83) は**変更されていない別 module の `CURRENT_PIN`**で proof source を作り、`:102` で旧 pin に切り替わった `derive_build_admission` に渡す。これが `build_admission.py:701` の拒否につながる。共有 helper には import 時に作る `_PROOF_BUILD_CONTEXT`（`:74`）もあり、pin の名前だけを追加で差し替えれば十分とは断定できない。

Layer3 の追加テストも [test_layer3_report.py:1898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/tests/test_layer3_report.py:1898) で同じ不整合を作る。親の [s6-red-evidence.md:36](/work/1/SFC/tanab/dev-wave-artifacts/t2125-historical-policy-version/s6-red-evidence.md:36) が報告する14件の赤と整合する。

**成果物影響:** 旧 stock pin の歴史閲覧、構造・trigger・bytes 検査、旧 epoch、Layer3 schema の追加検証が対象地点に到達せず、M6・M9 の検出力が未成立。

必要な修正は、既存テスト内で発行時の source・policy・proof の整合を保つこと。production の検査を緩める根拠にはならない。

**2. 【real／静的読解】M2 は赤になっても、裁定の「他の拒否層がない」という説明を満たさない。**

`artifact_admission.py:1006` の policy dispatch だけを certified にも歴史入口へ向けると、topology の選択は `:1394` の certified 側に残る。その結果、[wal.py:2126](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2125-historical-policy-version/orchestrator/campaign/wal.py:2126) の exact `BuildAdmissionPolicy` gate が拒否する。

さらに追加正例の fixture は `test_artifact_admission.py:77` で先に `classify_campaign` を呼ぶため、この変異では本来の certified 負例 `:105` に届く前にも落ちる。

**成果物影響:** M2 の赤を「旧 policy の certified 受理をテストが検出した」と数えると、DW-M01／F820 の単一理由性を誤報する。注入箇所と赤地点を分けて評価する必要がある。

## 重い所見

**3. 【real／静的読解】production の歴史入口には配線されているが、consumer 完走の実測証拠はない。**

中央入口は `artifact_admission.py:1382` → 歴史 topology → `build_admission.py:840` で記録 SHA・stock pin を使用する。親の実測で成功しているのは、追加 admission 正例の `[generator]`・`[review]`。旧 pin 正例と各 consumer の完走を実測済みとは言えない。

| consumer | 静的に確認した到達範囲／残る停止条件 |
|---|---|
| `critic/digest.py` | `:1236` の p2_2 discovery → 歴史 admission → `:730` の `replay_admitted_records`。policy の再拒否はない。`WorkloadDigest`（`:1205`）には新 classification を投影しない。 |
| `critic/online_digest.py` | `:42` → 同 digest 経路。policy 差は解消対象。`:47` の評価回数を超える genome 数による拒否は残る。 |
| `p2_2_report.py` | `:132` → discovery → `:71` の historical view.records 集計。policy の再照合はない。 |
| `replay.discover_*` | `replay.py:149,168` から歴史 admission に到達。`:140` の discovery 一意性条件は残る。 |
| `layer3_report.py` | `:733` の admission は解消対象。ただし `:755` → `:112` の**通常 decoder**が残り、歴史専用 grammar の lock は report 投影で止まり得る。 |
| B10 exploration | `b10_backoff_static_tail_formal.py:352` から歴史 admission。`:354` の `run_kind == "t2418-explore"` と mode の一意性は別途必要。formal 側 `:393` は certified のまま。 |

共通して、記録 blob・activation・contract・trigger・source／variant の既存検査は残る（`artifact_admission.py:1318,1406,1421,1446`）。現行 registry からの削除・改名等も解消対象外（`build_admission.py:768,780,787`）。

**成果物影響:** 解消するのは既存条件を満たす v2 の build policy 値差であり、列挙したレポート全体の復旧件数を示すものではない。

**4. 【real／静的読解】M1〜M9 の判定は次のとおり。変異実走は行っていない。**

「殺せる」は、コード上で変異による緑→赤を予測できるという意味であり、実測した KILLED ではない。

| 変異 | 判定・根拠 |
|---|---|
| M1 | **殺せる見込み。** `[generator]`・`[review]` の正例が `test_artifact_admission.py:94` で現行 policy 不一致拒否になる。旧 pin ケース自体は既に赤。 |
| M2 | **赤にはなるが単一理由性なし。** 上記所見2。fixture の `:77` と WAL exact 型 gate が先行する。 |
| M3 | **殺せる見込み。欠落 key 問題は refuted。** `test_artifact_admission.py:140` は余分 key を使用し、`:136` で WAL を空にして receipt SHA の拒否を除く。`build_admission.py:289` の集合検査だけを除けば後続の既知 field 検査は通る構造。 |
| M4 | **殺せる見込み。** 同テスト `:142` の schema だけを変更。空 WAL により receipt 層の拒否を避け、`build_admission.py:290` を狙う。 |
| M5 | **殺せる見込み。** `[generator]`・`[review]` でも記録 SHA は現行と異なり、歴史正例 `:94` が失敗する。pin fixture の修復に依存しない。 |
| M6 | **現状では検出証拠にならない。** 唯一の旧 pin stock 正例が fixture 発行中に既に赤。他の歴史正例は stock pin が現行と同じなので、この変異を判別しない。 |
| M7 | **殺せる見込み。** `test_build_admission.py:148` で stock source のみ旧 pin にし、`:159` で outer SHA を再計算、`:162` で現行 policy SHA を確認。`:179` の直接 validator 負例は恒真化すると例外が消える。後続 topology の別拒否に依存しない。 |
| M8 | **殺せる見込み。** `[generator]`・`[review]` の classification 期待値 `test_artifact_admission.py:97` が失敗する。 |
| M9 | **現状では検出証拠にならない。** `test_layer3_report.py:1900` の fixture が先に赤。ただし `:1911` 以降の設計は、他の historical marker を除き、従来分類で成功確認後に分類だけ変えるため、fixture 修復後の単一理由性はある。 |

**成果物影響:** 現状の追加テストを「9変異を検出可能」として受入証拠にできない。特に M6・M9 は対象検査未到達、M2 は別層拒否である。

**5. 【refuted／静的読解】schema の相殺そのものに欠落は確認しない。**

`layer3_schema.json:298` が新 classification を一般の enum に追加し、`:17` が `certifying_input=true` の場合だけ従来2分類に制限する。`admission_decision` とその `classification` は required なので、省略による回避もない。

**成果物影響:** 歴史材料 report の新分類を許しつつ、同じ分類の certifying report を schema が拒否する。未成立なのは実装ではなく、M9 の到達証拠。

## 軽い所見 / nit

**6. 【refuted／差分確認】裁定からの scope 逸脱は確認しない。**

`git diff --name-status d97c423bd` は指定された production 4ファイルと既存テスト3ファイルのみ。新 module、新 test file、docs 編集はない。

記録側 registry／authority を受理根拠にする変更もない（`build_admission.py:768,780,787`）。新 classification と既存 status の組合せは `artifact_admission.py:1463`、WAL 第2照合は `wal.py:2793` に残り、epoch の変更も差分にない。

**成果物影響:** 新 test file の登録漏れや、却下済みの受理拡張は今回の差分からは生じていない。

**7. 【refuted／静的読解】R5 に反する図・全レポート回復の主張はない。**

`plot_s1_9pair.py:589` の E0／`v1-authority-absent` 条件と、`layer3_report.py:116` の通常 decoder は不変。`s5-impl.md:59` も両者の回復を成果から明示的に除外している。

**成果物影響:** 有効な v2 が図の receipt 出力まで到達するとの誤った成果計上は、実装報告にはない。

**8. 【real／nit・資料読解】波及列挙は具体性が不足する。**

`s5-impl.md:58` の「上記 consumer 群」では、親が指定した `test_autonomous_trial_completeness.py` と `test_p3_autonomous_workload_trial.py` の既存期待値が明示されない。

ただし、新分類は旧 policy の歴史読取だけで発生する。既存の current-policy 入力・固定 decision は引き続き従来分類であり、certified 再 admission も残る（`autonomous_trial_completeness.py:240,4965`、`layer3_report.py:966`）。`EXPECTED_CAMPAIGN_CLASSIFICATIONS` は v1 corpus の certified 分類比較（`test_artifact_admission.py:1197,1219`）なので、新分類追加による期待値変更は不要。

親の実測対象5ファイルでは既存テストが緑に戻ったが、autonomous 系2ファイルの全件緑までは同資料から確認できない。

**成果物影響:** この列挙不足だけによる成果物の誤りは確認できないため nit。ただし共有 fixture の pin 不整合は所見1の実害がある。

## 実装子の報告への指摘

**9. 【refuted／静的照合】存在しない nodeid、テスト緑の偽報告は確認しない。**

`s5-impl.md:33` 以降の追加11関数は実在し、parametrize を含む33ケースという数も一致する。変更前試行の2関数も `test_artifact_admission.py:1485,1496` に存在する。

報告は `s5-impl.md:23,29,63` で本体未起動・収集未実行・変異未確認と区別している。実装子自身が pytest を緑と書いた箇所はない。構文解析等の成功主張（`:45`）は今回再実行しておらず、独立実測としては認定しない。

**成果物影響:** テスト成功を偽って完了扱いした報告ではない。ただし親の後続実測を踏まえた現状は「追加14件が赤」であり、「未実走」だけでは現在の状態を表さない。

## 総括

**受入保留。** 修正対象は旧 pin fixture と、M2 の変異評価における単一理由性の扱い。

production の歴史経路に記録 SHA・stock pin を使う配線は確認できたが、主題の旧 pin 正例と M9 は fixture で止まっている。consumer 完走を実測済みとは数えられない。

本レビューは静的読解のみ。14件の赤・799件の緑は親資料の実測引用であり、ファイル書込み・テスト実行・commit は行っていない。