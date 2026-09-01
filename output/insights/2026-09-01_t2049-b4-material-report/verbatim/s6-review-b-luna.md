## 総括

受理不可です。親の診断どおり、現在の9件の赤は、fixture生成時とreport再導出時で `critic.md` の絶対pathが変わる単一原因から連鎖しています。正常assemblyからevaluatorへ進む経路は0回です。  
これとは独立に、R4のcampaign rootを `runs/` と誤認する実在欠陥があり、campaign直下の兄弟directoryへreportを書けます。writerも2成果物を原子的かつdurableには公開していません。  
直接CLIのbootstrap、JSONの決定論、実装上のbytecode抑止は成立しています。焦点走39.21秒は5分以内ですが、現在は9 failedなので受入結果ではありません。  
禁止既存fileの差分は0です。対象2fileだけがuntrackedです。

## 所見

### F1. fixtureのrole-file pathが再導出時に変わる

- 深刻度: Critical
- 判定: **regressed**
- 根拠:
  - 新fixtureは証拠生成と最初のpublishを[test_p3_b4_material_report.py:65](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/tests/test_p3_b4_material_report.py:65)で終え、そのpatchが外れた後に[line 77](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/tests/test_p3_b4_material_report.py:77)と[line 78](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/tests/test_p3_b4_material_report.py:78)で再assemblyします。
  - 既存helperは一時admission repositoryのrole fileを使い、元のrole bytesをコピーします: `test_p3_b4_closed_critic.py:683-686`。
  - 既存の正例は `C.REPOSITORY_ROOT` と `C.ROLE_FILE` のpatch内でpublishとassemblyを完了します: `test_p3_b4_raw_record_producer.py:1523-1547`。
  - producerはその時点の `closed_critic.ROLE_FILE` をsnapshotします: [p3_b4_raw_record_producer.py:833](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_raw_record_producer.py:833)。その絶対pathを `transitive_evidence[].path` に入れます: 同 `:898-905`, `:1415-1418`。
  - assemblyは再導出したcanonical bytesと記録bytesを完全一致比較します: 同 `:1928-1947`。
  - 既存正例が先に行うseed/replica不変条件検査 `test_p3_b4_raw_record_producer.py:1498-1520` を新fixtureは呼んでいません。
- bytesの具体差:
  - 記録時: `/tmp/izanagi-b4-closed-admission-.../.claude/agents/critic.md`
  - report再導出時: `/work/.../material-report-author/.claude/agents/critic.md`
  - role fileの内容とSHA-256は同じですが、`evidence.transitive_evidence[*].path` のUTF-8 bytesが異なります。
- 壊れ方: 最初のattempt artifactから `evidence_binding / recorded judgments differ from source evidence rederivation` となり、全行がrejected-row形になります。M07の文字列変異はdictへの `+=` となり、M08、R4、ledger分岐も到達しません。
- 成果物影響: 正常な402 sourceと分析結果を一度も検査せず、拒否reportだけでCLI成功を装えます。
- 最小修正案: attempt artifactをclean subprocessと同じcanonical `C.ROLE_FILE` pathで生成し、patch無しの `assemble_b4_raw_analysis()` が成功するassertを置く。その前に `_assert_replicas_match_real_except_identity` 相当も実行する。
- 区分: **実在欠陥**。親の「9件は1根本原因の副作用」という診断は正しいです。

### F2. campaign rootを`runs/`と誤認している

- 深刻度: High
- 判定: **regressed**
- 根拠:
  - root抽出はWAL pathの`.parent`です: [p3_b4_material_report.py:790](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:790)。
  - 実際のWALは `<campaign-root>/runs/wal.jsonl` です: [layout.py:203](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/layout.py:203)。
  - test側も同じ誤りを複製しています: [test_p3_b4_material_report.py:322](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/tests/test_p3_b4_material_report.py:322)。
- 壊れ方: `<campaign-root>/material-report-output` は実campaignの配下ですが、誤って得た `<campaign-root>/runs` とは祖先・子孫関係がないため、[三方向検査](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:803)を通過します。
- 成果物影響: campaign内に `report.json` と `report.md` が混入し、campaign完全性検査と成果物集合を汚染します。
- 最小修正案: `evidence.campaign_lock.path` のparent、またはWAL pathの `parents[1]` をcampaign rootとする。testも実campaign rootのequal/below/aboveを使う。
- 区分: **実在欠陥**。fixtureを直しても現行testでは検出できません。

### F3. 2成果物の公開は原子的でもdurableでもない

- 深刻度: High
- 判定: **partial**
- 根拠: [p3_b4_material_report.py:827](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:827)。
  - 両一時fileをfile単位で`fsync`後、JSON、Markdownの順に別々にhard linkします: `:843-863`。
  - 2本目失敗時の1本目unlinkはbest effortで、失敗を握り潰します: `:864-869`。
  - output directoryは成功時、rollback時とも`fsync`されません。
  - `except Exception`なので、process停止や`KeyboardInterrupt`はpair rollbackの対象外です。
- 壊れ方: 1本目link後のprocess停止、または2本目link失敗後にrollback unlinkも失敗すると、`report.json`だけが残ります。
- 成果物影響: JSONとMarkdownが別世代または片方だけになり、Markdown内のJSON hashによるpair bindingが成立しません。
- 最小修正案: directory単位のstagingとatomic rename、またはcommit marker方式を使い、fileとdirectoryを順に`fsync`する。rollback失敗を握り潰さない。
- 区分: 逐次公開は**実在欠陥**、突然停止経路は**実在する障害リスク**。hard linkによる既存file非上書き自体はclosedです。

### F4. Markdownが出力規約を満たさず、escapeも完全ではない

- 深刻度: Medium
- 判定: **partial**
- 根拠:
  - JSONにはprovenanceと`reproduction_argv`があります: `p3_b4_material_report.py:583-607`。
  - Markdown rendererはそれらを一切表示しません: [p3_b4_material_report.py:653](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:653)。
  - 出力規約は`report.md`自身にprovenanceと再現コマンドを束ねるよう要求します: [material-report-conventions.md:8](/work/1/SFC/tanab/dev-wave-jobs/2026-09-01_t2049-b4-report-generator/verbatim/material-report-conventions.md:8)。
  - `_display()`は`|`とLFだけを処理し、backslashとCRは未処理です: [p3_b4_material_report.py:641](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/campaign/p3_b4_material_report.py:641)。
- 壊れ方: `report.md`だけを読む人は入力artifact hashと再現argvを得られません。将来、直接scalarに `\|` やCRが入るとtable delimiterや行境界を壊せます。
- 成果物影響: 人間可読report単体のproof chainが欠落し、まれなsource文字列では表示値と行構造が食い違います。
- 最小修正案: Markdownへartifact hash、publication root、再現argvを追加する。escapeはbackslashを先に二重化し、pipeをescapeし、CR/LFを正規化する。
- 区分: provenance欠落は**実在欠陥**。現行の直接scalar domainでのtable破壊は**仮想リスク**です。

### F5. 自走harnessと一覧検査は見かけ上のみ一部closed

- 深刻度: Medium
- 判定: **partial**
- 根拠:
  - `pytest.main([__file__])` は存在します: [test_p3_b4_material_report.py:494](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/tests/test_p3_b4_material_report.py:494)。
  - `test_plain_runner_coverage.py:35-74` の文字列検査には適合します。
  - ただし`orchestrator` importは[line 17](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/tests/test_p3_b4_material_report.py:17)で行われ、test fileにはrepo rootのbootstrapがありません。clean環境の `python3 orchestrator/tests/test_p3_b4_material_report.py` はrepoが`PYTHONPATH`やsystem siteに無いと、harness到達前に失敗します。
  - campaign module本体のbootstrapは一覧検査のexact文字列に一致し、relative importより前です: `p3_b4_material_report.py:26-43`。
  - subprocessは`-B`と`PYTHONDONTWRITEBYTECODE=1`の両方を持ちます: `test_p3_b4_material_report.py:437-480`。
  - ただしcheckerは第一引数がlist/tuple literalの場合だけ認識します: `check_subprocess_bytecode_guard.py:103-105`。現行は変数`argv`なので2呼出ともcheckerの検査対象外です。
- 壊れ方: standalone testが環境依存でimport失敗します。また将来guardを削除してもcheckerが赤になりません。
- 成果物影響: plain-runner経路ではreport欠陥の検査結果が得られず、将来のsubprocessがworktreeへpycを残す変更をgateが見逃せます。
- 最小修正案: test先頭でrepo rootをbootstrapする。subprocess argvを認識可能なliteral形にするかcheckerを1代入追跡へ拡張する。
- 区分: standalone importは**環境依存の実在欠陥**。checker盲点は**仮想リスク**です。今回のchecker実走自体はrc=0でした。

### F6. 直接CLI起動と決定論

- 深刻度: なし
- 判定: **closed**
- 根拠:
  - stdlib import後、relative importより前にpackage bootstrapがあります: `p3_b4_material_report.py:26-43`。
  - repo外cwd、`PYTHONPATH`無し、`PYTHONNOUSERSITE=1`、`-B`で`--help`を実走しrc=0でした。
  - JSON keyはsorted、separator無し、UTF-8、末尾LFです: `p3_b4_material_report.py:139-169`。
  - `Fraction`は`[numerator, denominator]`: `:116-118`。Decimalは有限値をlexeme文字列で出力し、sourceの元UTF-8も別fieldで保持します: `:147-150`, `:322-368`。
  - outputに時刻、乱数、未整列set反復はありません。campaign-root setも出力前にsortされます: `:785-792`。
- 壊れ方の具体例: 現在のコードから同一args・同一filesystem状態でbyte driftする経路は見つかりません。
- 成果物影響: fixtureを直せば、同一入力からJSONとMarkdownはbyte決定論的に生成可能です。
- 最小修正案: なし。ただし正常assemblyでの2回byte一致testは必要です。
- 区分: 静的にclosed。正常経路の実走確認は未了です。

### F7. 死んだ状態

- 深刻度: nit
- 判定: **partial**
- 根拠:
  - `_ImmutablePublication.root` は保存後に読まれません: `test_p3_b4_material_report.py:35`。
  - `B4MaterialReportInputs.contract_binding` も格納後に参照されません: `p3_b4_material_report.py:85,191,219`。
  - TODO、FIXME、書きかけdocstring、到達不能なplaceholderは見つかりません。
- 壊れ方の具体例: なし。
- 成果物影響: なし。must-fixではありません。
- 最小修正案: 不要fieldを削除するか、projection/provenanceに実際に使う。
- 区分: **nit**。

### F8. 禁止fileの無変更

- 深刻度: なし
- 判定: **closed**
- 根拠: base `24014bdb2`に対する裁定§6列挙file、`hooks/`、schema面の`git diff --quiet`はいずれもrc=0でした。path指定のstatusでは対象2fileだけが`??`です。
- 壊れ方の具体例: なし。
- 成果物影響: 既存contract、producer、docs、hook、schemaの混入変更はありません。
- 最小修正案: 対象2fileだけを修正・追加する。
- 区分: 実物確認済み。

## テスト所要の実数え

- 実`invoke()`回数: **2回**。module-scope fixtureのreal seedでon/off各1回です。replica 200 blockはwriterによる複製で、追加invokeはありません。根拠は `test_p3_b4_material_report.py:45-75` と `test_p3_b4_raw_record_producer.py:380-381,703-767`。
- fixture scope: `xdist_group("p3-b4-material-report")` とmodule scopeにより、親の48 worker走でも単一worker上の1 fixtureです。
- producer全assembly回数: **7回**。
  1. module fixture内の最初のpublish
  2. fixtureの`R._load_and_evaluate`
  3. fixtureの`build_material_report_document`
  4. M01/M02用fresh publicationのpublish
  5. missing leaf後のreport生成
  6. ledger testのreport生成
  7. CLI初回
- 実file `fsync`数: 現行の赤い走行では**6 file**です。fixtureとfresh publicationの大量fsyncはmockされています。実際にreportを書いたM01、到達失敗したledger test、CLI初回の3生成が各2 temporary fileを`fsync`します。directory `fsync`は0です。fixture修正後、ledger testが正しく書込み前に拒否すれば4 fileになります。
- 隠れた全走: **別pytest suiteやglobの起動はありません**。subprocessはgeneratorを同一argvで2回起動するだけで、2回目は`p3_b4_material_report.py:887-889`によりpublication再読前に拒否します。`pytest.main([__file__])`は直接実行時だけです。
- 実測比較: 親走は**28 items、9 failed / 19 passed、39.21秒**。ledger最遅nodeは [acceptance_duration_ledger.json:8185](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2049-material-report-author/orchestrator/tests/acceptance_duration_ledger.json:8185) の140.0秒です。焦点suite全体はその約28%、5分上限まで260.79秒の余裕があります。ただし赤なので受入済みとは扱えません。

## 裁定 R1〜R9 の履行表

| R | 判定 | 根拠 file:line |
|---|---|---|
| R1 | partial | `p3_b4_material_report.py:184-193,376-458`; 402 frameは出るがM01はfixture由来の先行rejectionで赤 |
| R2 | partial | `p3_b4_material_report.py:322-368,467-494`; 正常source projection未到達、M07もTypeError |
| R3 | partial | `p3_b4_material_report.py:207-214,531-558`; `floor=None`実装は正しいがM08正常評価未到達 |
| R4 | regressed | `p3_b4_material_report.py:772-815`; WAL parentをcampaign rootと誤認 |
| R5 | closed | `p3_b4_material_report.py:358-363,406-411`; anomaly absent、precursor classesとissuesは別名 |
| R6 | partial | `p3_b4_material_report.py:175-205`; issuer境界は成立、ledger境界testは未到達で赤 |
| R7 | closed | `p3_b4_material_report.py:26-43`; `test_p3_b4_material_report.py:437-480`; clean CLI起動rc=0 |
| R8 | partial | `test_p3_b4_material_report.py:30,45-78`; invokeは2回だが正常publication fixtureとして機能せず、assemblyを3重実行 |
| R9 | closed | `p3_b4_material_report.py:323-338,393-400`; transcribed限定とnon-guaranteeを同じ行に保持 |

## 検査できなかったこと

- sandbox read-onlyのためpytestは再走していません。緑とは報告しません。
- 正常assembly後のreport byte、正常evaluator結果、M01〜M18の全変異killは、fixture修正後の親実走が必要です。
- hard-link 2本目失敗、rollback unlink失敗、process停止、directory durabilityのfault injectionは未実走です。
- 3 meta-testは未実走です。campaign import形とplain-runner判定は静的確認、bytecode checkerだけ実走rc=0です。
- 無指定の`git status`はこのLustre worktreeでuntracked cacheにより空でした。path指定statusと`git ls-files --others`では対象2fileを`??`として確認しました。