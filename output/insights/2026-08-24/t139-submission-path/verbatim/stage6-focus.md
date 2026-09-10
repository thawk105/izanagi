## 対応表

| 所見 | 状態 | 再review結果と根拠 |
|---|---|---|
| A-F1 | closed | new recordは`approved.manifest_ref`を記録し、legacyだけD282へfallbackする。照合も同じauthorityを要求する。[_binding.py:81](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_binding.py:81)、[_manifest.py:424](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:424)、[test_t139_submission_path.py:275](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t139_submission_path.py:275) |
| A-F2 | closed | sealed authorityを生成するproduction callsiteは固定ref wrapperだけ。explicit-ref seamはprivate projection型を返し、`ApprovedManifest`を返さない。[_manifest.py:234](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:234)、[_manifest.py:259](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:259)、[test_t139_submission_path.py:253](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t139_submission_path.py:253) |
| A-F3 | closed | 採用部分を修正済み。固定projection refsに加え、D282の6 fieldとD574の4 fieldをcanonical再導出し、manifest/projection indexも一致確認する。[_manifest.py:307](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:307)、[test_t139_submission_path.py:289](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t139_submission_path.py:289) |
| A-F4 | partial | raw evidence TOCTOUは残るが、親裁定どおり今回差分固有でないscope外。writerはsemantic後にbindingだけ再検査する。[_writer.py:71](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:71)、[_writer.py:79](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:79)、[adjudication.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage6-focus/inputs/adjudication.md:17) |
| A-F5 | closed | D282 predecessor、base/effective fold、D574 canonical authorityは固定tupleとのexact比較を維持。generic successor探索もない。[_manifest.py:263](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:263)、[_manifest.py:268](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:268) |
| A-F6 | closed | 親裁定でproduction到達不能として閉じられ、今回fixはsemantic pathを変更していない。既存raw CMake拒否検査も維持。 [adjudication.md:18](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage6-focus/inputs/adjudication.md:18)、[test_t338_submission_gate_unit3.py:825](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit3.py:825) |
| A-F7 | closed | 固定private namespace、入力`raw_bytes`の直接publish、create-only、nonexportを維持。[_writer.py:22](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:22)、[_writer.py:58](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:58)、[_writer.py:81](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:81) |
| A-F8 | closed | V1 literal pin、historical bytes、worktree bytes、旧42件を維持し、V2検査が追加された。 [test_t338_submission_gate_unit5.py:45](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:45)、[test_t338_submission_gate_unit5.py:356](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:356) |
| B-F1 | closed | A-F2と同じ。協調変更した非固定refから得られるのはunsealed projectionだけである。[_manifest.py:259](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:259)、[test_t139_submission_path.py:253](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t139_submission_path.py:253) |
| B-F2 | closed | M3はmanifest、payload projection、indexの同名差替えを新HEADへcommitし、通常fixed loaderを呼ぶ。historical index負例もprojection validation全体を通る。 [test_t139_submission_path.py:225](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t139_submission_path.py:225)、[test_t338_submission_gate_unit5.py:638](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:638) |
| B-F3 | closed | receipt正例はpretty JSONと末尾LFで、compact再serializeと異なる。publish後も入力bytesとのexact一致を要求する。 [test_t338_submission_gate_unit3.py:653](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit3.py:653)、[test_t338_submission_gate_unit5.py:597](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:597) |
| B-F4 | closed | V2に独立literal tripleがあり、historical、worktree、production projection refの三者を照合する。 [test_t338_submission_gate_unit5.py:50](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:50)、[test_t338_submission_gate_unit5.py:362](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:362) |
| B-F5 | partial | 安全面はclosed。`object.__new__` helperはunit1/unit3のlegacy consumer fixtureだけにあり、production mintにはない。writer全経路でも書込前に拒否される。一方、既存consumer群がlegacy fixtureを使うという元の検出力制限自体は親裁定どおり残る。 [test_t338_submission_gate_unit1.py:147](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit1.py:147)、[test_t338_submission_gate_unit3.py:89](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit3.py:89)、[_writer.py:38](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:38)、[test_t338_submission_gate_unit5.py:397](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:397) |
| B-F6 | closed | projection型はmodule-private名となり、旧public名がapproval moduleとpackageの双方にないことを検査する。 [approval_payload.py:178](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/preregistration/approval_payload.py:178)、[test_t139_submission_path.py:164](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t139_submission_path.py:164) |
| B-F7 | closed | `object_pairs_hook`は全階層へ適用され、vector projectionとmanifest namespace双方にnested duplicate負例がある。 [approval_payload.py:243](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/preregistration/approval_payload.py:243)、[test_t139_submission_path.py:112](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t139_submission_path.py:112)、[test_t139_submission_path.py:146](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t139_submission_path.py:146) |
| B-F8 | partial | 6,199行で上限内。長いsignatureやtupleは残るが、canonical再導出やseal検査は削られていない。[_manifest.py:259](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:259)、[_manifest.py:307](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:307)、[fix-output.md:41](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-submission-path/stage6-focus/inputs/fix-output.md:41) |

集計はclosed 13、partial 3、regressed 0。

## 新規所見

新規blocker、must-fix、受理穴は検出しなかった。DW-G05成果物への新たな悪影響もない。

再確認したtrust chainは次のとおり。

- new receiptはD574 manifest refを記録する。
- production上の`ApprovedManifest`生成callsiteは固定wrapper内の1箇所だけである。private tokenをPython上で参照できる点は既知のD563限界だが、任意fieldを持つnew authorityはcanonical intact検査を通らない。
- intact検査は`approval_ref`、`target_core`、`approved_blobs`、erratum順、`composed_sha256`、`prereg_commit`、固定manifest/projection refs、base/effective fold、canonical authority、vector indexを再導出して比較する。
- legacy helperはtest fixtureだけに存在する。D574 fieldが全欠落ならlegacy扱いだがwriterはvector authority不在で拒否する。部分的にD574 fieldを加えたobjectはintact検査が先に拒否する。[_manifest.py:310](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_manifest.py:310)、[_writer.py:32](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/submission_gate/_writer.py:32)

## 検出力再評価

| 変異・検査点 | 再評価 |
|---|---|
| M1 writer guard恒真化 | 検出。legacy bindingをfull writerへ渡す負例がpublish前の例外と空destinationを要求する。 |
| M2 manifest/payload比較削除 | 検出。片側index ref変更の2vectorがprojection validationを通る。 |
| M3 fixed artifactをHEAD読取 | 検出。同名3 artifactを新HEADへcommitした後もfixed loaderがhistorical bytesを返すことを要求する。 |
| M4 token検査弱化 | 検出。wrong token constructorとunsealed binding負例がある。既知のprivate token参照限界はcanonical再導出で補う。 |
| M5 binding保持・再検査削除 | 採用scopeでは検出。normal resolver authorityの`vector_index`変更後に`binding.assert_intact`が失敗する。raw evidenceのsemantic後TOCTOUは別scope。 |
| M6 raw bytes再serialize | 検出。pretty JSON、末尾LF、compactとの差、published exact bytesを連言する。 |
| M7 raw CMakeを申告値へ置換 | 検出。申告0に対してraw CMakeだけ1の負例が残る。 |
| M8 新必須vector削除またはpin不整合 | 検出。独立V2 pin、46件、旧42件一致、末尾4 ID、全entry parametrizeを連言する。 |

新4vectorはindex末尾へ固定され、46件全体をparameterizeするtestから実行分岐へ到達する。特にhistorical replacementはhelper直呼びではなく、両projectionを変更して`_resolve_projection_authority`を通す。 [test_t338_submission_gate_unit5.py:370](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:370)、[test_t338_submission_gate_unit5.py:555](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t139-submission-path/orchestrator/tests/test_t338_submission_gate_unit5.py:555)

親の関連9 file 345 passedを実走証拠として採用する。fix担当時点の0件実走とは後続の親実測であり矛盾しない。このfocus review自身はpytestを実走していない。

## scope外の妥当性

- raw evidence TOCTOUは今回fixで新設された穴ではなく、writer差分もないため実装へ戻さない。
- B2 sealed series/receipt-set、producer、driver、collector、report、ledger consumerは今回authority chainの後続であり、new receipt受理穴にはならない。
- D292/D264 export、PBS、qsubはwriterから到達せず、固定private namespaceと`__all__ = ()`が維持される。
- generic successorは固定D282 predecessorと固定D574 effective authorityのexact比較があるため発効しない。
- CMake overrideは親裁定のschema到達不能境界を変更していない。

## 総括

段6 focus再reviewは受理可能。blocker 0、must-fix 0、regression 0である。

new receiptからD574 manifestとV2 authorityを復元でき、非固定explicit refsはsealed authorityへ昇格せず、new authorityの全canonical fieldが再導出される。legacy forgeもproduction経路へ漏れず、writerで書込前に拒否される。

残るpartialは、scope外のraw evidence TOCTOU、既存legacy consumer fixtureの検出力境界、6,199行での可読性nitだけであり、DW-G05成果物をblockしない。親実測は345 passed、6,199行、fix commit後provenance新規違反0。本review自身のtest実走は0件。