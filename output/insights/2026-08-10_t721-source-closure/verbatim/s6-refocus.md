## 対応表

| 所見 | 状態 | 判定根拠 |
|---|---|---|
| D-01 | closed | 完全 binding 作成後に disk を汚し、live verifier を直接呼ぶ8-path検査が追加された。[test_t671_source_binding.py:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:183) |
| D-02 | closed | M3 は digest map を8 path維持したまま、capture/live の disk 比較だけを先頭2 pathへ縮める変異に再照準済み。期待12 nodeと観測12 nodeが一致。 |
| D-03 | closed | M6 は required-subset 化でextra keyを許す変異となり、extra-key nodeが単独で検出。[mutation-ledger.json:665](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/mutation-ledger.json:665) |
| D-04 | closed | 記録blobと一致するlockを作り、live diskだけを汚してもcommitted admissionが通る正例が追加された。[test_artifact_admission.py:963](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:963) |
| D-05 | closed | P1の期待nodeはv2正例2本へ修正され、両方とも観測失敗集合に含まれる。 |
| D-06 | **partial** | 32 path・全件v1 schemaは固定したが、evidence 2本のclassification/error結果は固定していない。[test_artifact_admission.py:728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:728) |
| D-07 | closed | M2の誤ったmissing-blob副期待は除去され、現expected 26件はすべてobservedに含まれる。 |
| D-08 | closed | production-derived tuple equalityは削除され、独立exact-8 sentinelは維持された。[test_t671_source_binding.py:119](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:119) |
| D-09 | closed | recorded-HEAD化で失われたのはfixture構築時の意図しないlive-disk拒否。capture/live driftは専用8-path検査に移されており、意図したproduction検出力の欠落はない。 |
| D-10 | closed | production call-siteのexact Counter censusは維持されている。[test_t671_source_binding.py:349](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:349) |
| L2-01 | **partial** | D-06と同根。32本の存在/schemaは固定したが、追加2本の分類結果までは固定していない。 |
| L2-02 | closed | 記録は共有fixture consumer 16、decode-only 4、production binding 2へ訂正済み。 |
| L2-03 | closed | Layer3固有helperもrecorded-HEAD blob経路へ変更された。[test_layer3_report.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_layer3_report.py:53) |
| L2-04 | closed | dirty recorded-blob正例が8 path化され、各caseで独立Git取得値と比較する。[test_t671_source_binding.py:308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:308) |
| L2-05 | closed | 期待値反転・skip・xfailはなく、拒否理由の単一化も維持。 |
| L2-06 | closed | exact-2拒否・exact-8受理・codecのexact集合比較はいずれも維持。残件はL2-01だけ。 |

## 新規所見

### FR-01 / evidence 2 lockのclassification不変が未固定

- 一行要約: 32-lock censusはpathとschemaしか検査せず、追加されたevidence 2本のclassification/error結果を検査しない。
- 判定: **real**
- 重要度: **must-fix**
- 根拠: censusはschema versionまでで終了し、classification mappingは`output/campaigns`だけを走査する。[test_artifact_admission.py:728](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:728) [test_artifact_admission.py:749](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_artifact_admission.py:749)。evidence 2ディレクトリにはWALがないため、現状の既定結果は入口のexact errorである。[artifact_admission.py:577](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/artifact_admission.py:577)
- 成果物影響: evidence 2本が将来、拒否から別classification／admissionへ変化しても「既存32 artifact不変」検査が緑のままになる。
- 最小の修正案: evidence 2 pathをparameterizeし、`classify_campaign`が現行のexact `ArtifactAdmissionError` 理由で拒否することを固定する。

### FR-02 / recorded-HEAD化で意図したdrift検査が失われた、は反証

- 一行要約: 共有fixture・Layer3 helperが捕まえなくなったのはfixture setup時のlive driftであり、production live gateの検出力ではない。
- 判定: **refuted**
- 重要度: **nit（修正不要）**
- 根拠: 両helperは記録HEAD blobだけを読む。[campaign_lock_test_support.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/campaign_lock_test_support.py:10) [test_layer3_report.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_layer3_report.py:53)。一方、専用検査は完全binding作成後にdiskを汚し、production verifierを直接呼ぶ。[test_t671_source_binding.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:188)
- 成果物影響: なし。保存済みcampaignのlive drift拒否は専用8-path検査が保持する。
- 最小の修正案: なし。

### FR-03 / MISMATCH 5件に期待node欠落がある、は反証

- 一行要約: expected/failed nodeを集合差分で独立照合した結果、5件すべてmissing=0のstrict supersetだった。
- 判定: **refuted**
- 重要度: **nit（修正不要）**
- 根拠:

| 変異 | expected | observed | missing | extra |
|---|---:|---:|---:|---:|
| M1 | 26 | 28 | 0 | 2 |
| M2 | 26 | 27 | 0 | 1 |
| M5 | 8 | 9 | 0 | 1 |
| M7 | 10 | 38 | 0 | 28 |
| P1 | 2 | 78 | 0 | 76 |

台帳の各expected/failed集合は[M1:42](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/mutation-ledger.json:42)、[M2:219](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/mutation-ledger.json:219)、[M5:525](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/mutation-ledger.json:525)、[M7:709](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/mutation-ledger.json:709)、[P1:880](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/mutation-ledger.json:880)。

- 成果物影響: 期待gateの見逃しはない。ただしextraの多いM7/P1は波及範囲が広いという診断情報を持つ。
- 最小の修正案: なし。台帳ではMISMATCHをKILLEDへ読み替えず、superset注記を維持する。

### FR-04 / M4は意図した独立testによるkill

- 一行要約: M4の8 failureはすべて追加された直接live-verifier testで、副作用nodeはゼロ。
- 判定: **refuted**（副作用kill説）
- 重要度: **nit（修正不要）**
- 根拠: 変異はlive verifierのdisk不一致条件だけを無効化する。[mutation-ledger.json:494](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/mutation-ledger.json:494)。expected 8とobserved 8は順序を除き完全一致。[mutation-ledger.json:467](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/mutation-ledger.json:467)。testはcapture完了後にdiskを汚し、直接`verify_live_contract_loader_binding`を呼ぶ。[test_t671_source_binding.py:188](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_t671_source_binding.py:188)
- 成果物影響: resume時のlive source drift拒否に、意図どおり独立した検出証拠がある。
- 最小の修正案: なし。

### FR-05 / 親の「全部フレーク」説明は粗い

- 一行要約: 5件は同じlocal環境依存赤であり、残る1件には本差分から到達可能な時間依存経路がある。
- 判定: **real**
- 重要度: **nit**
- 根拠: local 2走では同じexploration-root 5件が共通して失敗している。[parent-run4.log:433](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/parent-run4.log:433) [parent-run5.log:441](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/parent-run5.log:441)。これはtmp pathのGit祖先を拒否する別機能である。[layout.py:321](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/layout.py:321)。一方、6件目は`now`取得後にlock fixtureを作り、8 blobのGit読取を挟んでから現在時刻を測る経路があり、文字列に`1860`を要求する。[test_campaign.py:4399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign.py:4399) [test_campaign.py:3363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/tests/test_campaign.py:3363) [pipeline.py:923](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t721-source-closure/orchestrator/campaign/pipeline.py:923)。compute-node再走は272 passedだが、同一環境での再現否定ではない。[parent-run8.log:15](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t721-source-closure/parent-run8.log:15)
- 成果物影響: なし。screening判断自体はpayloadの`age_s >= 1860`で検査されており、赤は診断文字列の時間依存。
- 最小の修正案: noteの`1860`文字列assertを削り、既存のreason・`age_s >= 1860`・threshold検査へ一本化する。5件は「flake」ではなくlocal `/tmp` Git祖先汚染として分離記録する。

## 総括

- **NO-GO**
- 残 must-fix: **1件**（D-06 / L2-01と同根のevidence 2 lock classification未固定）
- MISMATCH 5件はすべてstrict supersetで、期待node欠落は0。
- M4は意図した直接live-verifier 8 nodeだけによる正当なKILL。
- recorded-HEAD化によるproduction drift検出力の喪失は認めない。
- `test_campaign.py`の5件は環境依存、1件は差分から到達可能な時間依存nit。
- pytestは再実行しておらず、本報告は指定どおり静的検査と既存ログ照合による。