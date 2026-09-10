静的読解と SHA-256 再計算のみのレビューである。pytest・build・書き込みは行っていない。

## 親実測の反証

### High — `s1_known_axes_freeze.py` の SHA pin は「3 箇所」ではない

**claim:** 正しい値は、同一 SHA の literal が **4 ファイル・7 field** である。一方、現行 worktree の bytes を直接比較する防壁は主に freeze verifier であり、7 field 全部が live file 編集で発火するわけでもない。

**evidence:** 親は 3 箇所とする [s1-brief.md:17](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s1-brief.md:17)。実際には freeze JSON に1件 [known_axes_freeze.json:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/output/s1-freeze/known_axes_freeze.json:7)、T080定数に1件 [t080_freeze_migration.py:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/t080_freeze_migration.py:110)、テストに3件 [test_s8b_oracle_driver.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s8b_oracle_driver.py:94) [test_s8b_oracle_driver.py:178](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s8b_oracle_driver.py:178)、T080 receipt に `recorded`/`migration_blob` の2件 [legacy-freeze-repin.receipt.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/output/t080-migration/legacy-freeze-repin.receipt.json:1)ある。ただし T080 は live file でなく `migration_basis_commit` の blob を照合する [t080_freeze_migration.py:1072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/t080_freeze_migration.py:1072)。live file を凍結値と比較するのは [s1_known_axes_freeze.py:718](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s1_known_axes_freeze.py:718) である。

**impact:** 親 brief は保存された pin を過少計上する一方、「1 byte の変更が全 pin を直接発火させる」と読める点では過大一般化している。保守者がどの防壁を更新してよいか誤認する。

**suggested_fix:** brief を「4ファイル・7 field。live-byte 検査と historical-basis 検査は別物」と訂正する。対象 script 自体は編集しない。

### High — 「63 source」と drift 再編集の一般化が不正確

**claim:** 正しい内訳は **63 source record、31 distinct path、15 mismatch record、4 distinct mismatch path** である。中核5ファイルが0件なのは正しいが、「4本を再編集しても新規の検出は生じない」は byte pin に限定しても説明不足で、意味変更まで含めれば誤りである。

**evidence:** source の列挙規則は再帰的で重複を除かない [s1_known_axes_freeze.py:682](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s1_known_axes_freeze.py:682)。静的再集計では mismatch は `backoff_sweep.py`、`p3_s4_loop_sort.py`、`s6_sort_sweep.py`、`s8a_trigger_sweep.py` の4 pathで、合計15 recordだった。`buildcache.py`、`build_admission.py`、`pipeline.py`、`loop.py`、`ident.py` は0 record。一方、現行コードから document を再構築して独立 golden と比較する検査 [test_s1_known_axes_freeze.py:52](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s1_known_axes_freeze.py:52)、backoff grid の直接検査 [test_s1_known_axes_freeze.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s1_known_axes_freeze.py:68)、live document の自己整合検査 [test_s1_known_axes_freeze.py:103](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_s1_known_axes_freeze.py:103) が存在する。

**impact:** コメントだけの再編集なら historical source-pin の不一致種類は増えない可能性が高い。しかし定数・選択・生成ロジックの変更は別の検査入口で検出されうる。凍結 verifier は最初の mismatch で停止するため、追加 drift の個別帰属もできない [s1_known_axes_freeze.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/s1_known_axes_freeze.py:729)。

**suggested_fix:** 「凍結 JSON に対する既存の byte mismatch は4 distinct path」と「各 module の意味契約検査」を分け、再編集無害という一般化を削る。

### Critical — P5 の「旧3 campaign の通常 resume で実発火」は 0/3

**claim:** 旧3 artifact の件数と SHA は正しい。しかし現行 production driver は既に別 namespace を選ぶため、IDを維持しても旧3 directoryへ通常 resumeしない。さらにプランはID自体も変える。P5 の発火主張は二重に成立しない。

**evidence:** 静的再計算値はプラン表と一致した [s2-plan.md:282](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:282)。

- S4: lock `0b53a387…7c9`、WAL `2163b794…611`、`build_start=3` [S4 WAL:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl:1)
- S5: lock `3be89e0d…f97`、WAL `b901f23a…3a5`、`build_start=1` [S5 WAL:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/output/campaigns/p3-s5-sort-loop-s5-sort-autonomous-3be89e0d/runs/wal.jsonl:1)
- S8a: lock `3f72ecd5…de0c`、WAL `a539648d…1ea3`、`build_start=2` [S8a WAL:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/output/campaigns/p3-s8a-trigger-loop-s8a-trigger-autonomous-3f72ecd5/runs/wal.jsonl:1)

ところが旧物は `output/campaigns/` にあり、現行 driver は `output/exploration/campaigns/` を構築する [layout.py:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/layout.py:323) [p3_s4_loop.py:642](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_s4_loop.py:642) [p3_s4_loop_sort.py:224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_s4_loop_sort.py:224) [p3_s4_loop_trigger_gating.py:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/p3_s4_loop_trigger_gating.py:491)。これは明示的な前向き namespace 移行である [decisions.md:5976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/docs/decisions.md:5976)。

加えて、現行 lock は ID を作る canonical preimage そのものである [ident.py:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/ident.py:76) [ident.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/ident.py:94) [ident.py:163](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/ident.py:163)。policyを同じ preimageへ加えてIDを保つことはできず、プランもID変更を選んでいる [s2-plan.md:209](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:209) [s2-plan.md:367](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:367)。

**impact:** synthetic `test_resume_rejects_committed_stage_without_receipt` が成立しても、実3 artifact の resume 発火証拠にはならない。実 artifact が踏まれるのは layer3、critic、qualification などの明示 path consumer だけである。

**suggested_fix:** 「通常 resume」と「明示 path consumer」を別の保証にする。実3件は各 consumer の入口試験に使い、resume test は synthetic campaign の契約試験と明記する。旧 official namespace を通常 driver から再開できるとは主張しない。

## その他の攻撃所見

### Critical — 「現在の source evidence で全 committed attempt を検証」は実装不能か自己照合になる

**claim:** receipt は source の hash しか保存せず bytes を保存しない。複数 iteration が異なる coder source を持つ campaign では、再開時の現在 worktreeから過去全 attempt の source evidenceを再導出できない。

**evidence:** 提案 receipt は `source_bytes_sha256`、diff SHA、pathしか持たない [s2-plan.md:149](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:149)。一方、全 WAL 検証を terminal skip より前に置く [s2-plan.md:230](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:230)。現行 loop はまず campaign 全体を replayし、その後で現在の各 genome/sourceを解決する [loop.py:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/loop.py:145) [loop.py:169](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/loop.py:169)。実S4だけでも異なる `src_token` の attempt が3件ある [S4 WAL:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl:1) [S4 WAL:6](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl:6) [S4 WAL:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/output/campaigns/p3-s4-loop-s4-autonomous-0b53a387/runs/wal.jsonl:11)。

**impact:** 実装は、過去 receipt 内の hash を同じ receipt と照合するだけの恒真検査になるか、正当に admitted された過去 iteration を現在 source と不一致として一律拒否するかのどちらかになる。

**suggested_fix:** replay時に要求するのは receipt canonicality・policy・attempt topologyまでとし、現在 source との一致は現在候補/cache reuse境界だけに限定する。過去 source の再検証が必須なら、attemptごとの immutable source snapshotまたは canonical diff blobを保存する。異なる sourceを持つ2 attemptの再開試験を必須にする。

### High — overlay 台帳が独立 pin を持たず、reader と test が同じ正本を見る危険

**claim:** 新 overlay は既存 freeze familyの外で、プランは raw ledger SHAや独立 key-set sentinelを規定していない。同じ ledgerから期待値を読んで分類を検査すれば、ledger削除・差替えとreaderが共倒れしても検査が成立する。

**evidence:** overlayは新規ファイルとして3 recordだけ置く [s2-plan.md:280](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:280)。既存 `FROZEN_MANIFEST` は明示的に23件だけ [test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_frozen_artifacts.py:38) [test_frozen_artifacts.py:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_frozen_artifacts.py:139)。プランが overlay を identityへ加えるのはT126 code identityだけである [s2-plan.md:327](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:327)。

**impact:** `test_actual_three_legacy_campaigns_are_classified_unclassified` が production ledgerから対象集合を得る実装なら、3件固定の証拠にならない。一般 consumer の受理集合も qualification identityでは保護されない。

**suggested_fix:** test側に独立した exact tuple `(path, id, lock SHA, WAL SHA, count)` と overlay raw SHAを固定し、期待集合をproduction ledgerから導出しない。ledger membershipの独立 sentinelも置く。

### High — 後方互換 sentinel と runbook 再開契約の棚卸しが不足

**claim:** プランは全 identity 変更を認識しているが、既存の「不変」テストや運用文言を変更期待値一覧で取り切れていない。単に期待値を新値へ書き換えると、歴史的互換契約そのものを消す。

**evidence:** legacy stock cache keyは `_GOLDEN_CK0` で固定され、「既存 WAL/cache 整合」と明記されている [test_campaign.py:3319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_campaign.py:3319) [test_campaign.py:3422](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_campaign.py:3422)。代表 campaign ID の固定値もある [test_campaign.py:231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_campaign.py:231) [test_campaign.py:268](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_campaign.py:268)、S8a IDには個別 sentinelもある [test_p3_s4_loop_trigger_gating.py:505](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:505)。runbookは同じ commandでcheckpointを復元して反復継続すると説明する [phase3-s4b-runbook.md:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/docs/phase3-s4b-runbook.md:86) [phase3-s5-sort-runbook.md:136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/docs/phase3-s5-sort-runbook.md:136) [phase3-s8a-trigger-runbook.md:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/docs/phase3-s8a-trigger-runbook.md:78)。

**impact:** stockを含む全cacheは再構築、全campaignは新directory、既存checkpointは自動継続されない。旧値テストを新値へ上書きすると、意図的な互換破壊が将来見えなくなる。

**suggested_fix:** 旧導出値は historical contract testとして残し、新 runtime policyによる値を別テストにする。runbookには「この変更後の初回は新campaign/cacheを開始し、旧checkpointは継続しない」と明記する。

### High — admission receipt が変える producer bytes は次の全域に及ぶ

**claim:** `variant_id` と executable内容が必ず変わるわけではないが、それ以外の主要 producer artifact は連鎖的に変わる。

**evidence:**

| surface | byte/path への影響 | 既存 pin / consumer |
|---|---|---|
| legacy cache | keyとdirectoryが変わりsidecar新設。binary bytes自体の変化は必須ではない | `_GOLDEN_CK0` [test_campaign.py:3331](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_campaign.py:3331) |
| v2 cache | digest、directory、`completion.json` のpreimage/top-level fieldが変わる | exact manifest検査 [buildcache.py:292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/buildcache.py:292)、exact fixture [test_buildcache_v2.py:511](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_buildcache_v2.py:511) |
| campaign | ID/path、`campaign.lock`、WALのSTART/DONE/COMMITが変わる。cache pathを含むbuild commandもWALへ入る | [pipeline.py:633](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/pipeline.py:633) |
| reports | Layer3はWAL record全体、record hash、lock/WALを含む全artifact hash、campaign IDを射影するためreport bytesが変わる | [layer3_report.py:60](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/layer3_report.py:60) [layer3_report.py:192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/layer3_report.py:192) [layer3_report.py:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/layer3_report.py:408) |
| qualification | policy追加でseries ID、attempt ID、attempt directory、`series-identity.json`、submission、marker、ledger、result/receipt全体が変わる | series preimage [t126_driver.py:387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/qualification/t126_driver.py:387)、attempt生成 [t126_driver.py:983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/qualification/t126_driver.py:983) |

さらに現行T126は旧lock/WALをbyte pinする [t126_control_v1.json:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/qualification/t126_control_v1.json:15)。同じP2 WALは独立 goldenにも固定されている [s1_expected_goldens.py:437](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/s1_expected_goldens.py:437)。既存Layer3 reportは再生成しない契約である [layer3_report.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/layer3_report.py:16)。

**impact:** 旧 WAL、report、T126 sourceを上書きして新schemaへ寄せることはできない。新protocolを旧 `t126_control_v1.json` や旧P2 pathへ被せると、別の歴史 pinを破壊する。

**suggested_fix:** producerごとの before/after artifact matrixを受入条件にする。T126は旧control/sourceを保存したまま、新version・新path・新seriesとして作る。旧Layer3 reportも再生成対象にしない。

### High — attempt grouping の最重要迂回路に専用試験がない

**claim:** planはattempt ID単位の検証を謳うが、テスト一覧に interleaved/retried attempt の splice試験がない。

**evidence:** 現行 replayはvariant単位で状態を集約するだけ [wal.py:566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/wal.py:566)、stage helperは最後勝ち [wal.py:586](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/wal.py:586)。プランはattempt単位の `START→DONE→COMMIT` を要求する [s2-plan.md:241](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:241) が、予定試験は単一attemptのreceipt欠落・不一致・正常resumeに留まる [s2-plan.md:413](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:413)。

**impact:** `A.START(receipt A) → B.START(receipt B) → A.DONE → A.COMMIT` や、abort後の古いDONE/COMMIT差込みをvariant単位の集合照合で誤受理しても、予定試験では区別できない。

**suggested_fix:** cross-attempt splice、abort後retry、重複START、別attemptのreceipt SHA流用を個別nodeidにする。各試験は失敗境界をattempt topology validatorへ固定する。

### High — 既存 tail-repair 試験を admission 拒否へ転用すると帰属が壊れる

**claim:** `test_loop_resume_repairs_tail_before_replay_and_surfaces_receipt` はWAL tail修復の試験であり、receiptless resume拒否へ期待を反転すべきではない。

**evidence:** 現行試験は途中切れ4 bytesを作り、修復receipt、残存record、append後のstage列まで検査している [test_campaign.py:4858](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/tests/test_campaign.py:4858)。プランはこれをreceiptless COMMIT迂回路として拒否期待へ変える [s2-plan.md:431](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:431)。

**impact:** admission拒否がtail修復より前なら、元のtail修復契約を一度も踏まない。逆なら、どちらの処理で止まったか分からない。1試験が二つの理由を持ち、回帰帰属が消える。

**suggested_fix:** tail-repair試験には正規attempt/receiptを与えて従来契約を維持する。receiptless committed WALは、tail破損のない最小fixtureで別試験にする。

### High — cache/consumer試験は対象 validator を踏まずに成立しうる

**claim:** key変更後の旧entryを旧pathに置くだけではcache missになり、sidecar/manifest validatorは呼ばれない。unlisted artifactも別の構造不正で拒否されうる。

**evidence:** legacyは新keyから `bdir` を作り、binaryが存在するときだけhit検査へ入る [buildcache.py:691](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/buildcache.py:691) [buildcache.py:709](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/buildcache.py:709)。v2も新digest下のdirectoryが存在するときだけmanifestを検証する [buildcache.py:534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/buildcache.py:534) [buildcache.py:555](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/campaign/buildcache.py:555)。予定試験はこの配置条件を明記していない [s2-plan.md:409](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:409)。

**impact:** 「旧entry拒否」のつもりが単なるmiss、新規build、lock不正、stage topology不正で終わり、sidecar・receipt検査の証拠にならない。

**suggested_fix:** 旧binary/manifestを意図的に**新key/digest下**へ配置し、build関数が呼ばれていないことと、期待したvalidator reasonを同時に固定する。unlisted receiptless fixtureはlock・WAL・stage topologyをそれ以外すべて有効にする。

### High — T126 の正規 positive artifact は現時点で存在しない

**claim:** 現行の唯一の実sourceはreceiptless旧P2で、プランはこれを拒否する。`test_admitted_source_pair_is_accepted` は当面synthetic fixtureしか踏めず、実運用の発火証拠にはならない。

**evidence:** 現行controlは旧P2 lock/WALを固定する [t126_control_v1.json:15](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/qualification/t126_control_v1.json:15)、selectorはまずそのbytesを検査する [artifacts.py:797](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t342-344-provenance/orchestrator/qualification/artifacts.py:797)。プラン自身も新しい admitted P2 sourceの実測は親の後続作業としている [s2-plan.md:392](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:392) が、同じテスト計画でpositive acceptanceを掲げる [s2-plan.md:425](/home/SFC/tanab/.claude/jobs/70fa1240/tmp/wave-t342-344/s2-plan.md:425)。

**impact:** 実装直後から新P2計測完了まで、T126には実在する受理可能sourceが0件となる。synthetic positiveだけではrunbook・protocol・実pathの回復を証明しない。

**suggested_fix:** 二段階の受入にする。第一段は旧source拒否とhermetic positive、第二段は新しい実P2 artifact・新control・実pathでのpositive consumer検査。第二段完了前はT126運用再開を保証しない。

## 総括

最も危険な恒真保証は P5 の「旧3 campaignがresumeで発火する」である。現行driverは既に別namespaceへ進み、プラン後はIDも変わるため、通常resumeで踏む実物は0/3である。

後方互換で最大の破壊面は、legacy/v2 cache、campaign ID、checkpoint、T126 seriesを同時に新namespaceへ切る点である。既存cache再利用とcampaign継続を失い、T126は新しい実測sourceが作られるまで実運用上の受理対象を持たない。