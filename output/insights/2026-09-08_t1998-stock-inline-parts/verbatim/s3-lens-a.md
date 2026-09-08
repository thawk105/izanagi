## 所見

### 所見 1 — 診断 build 拒否は effective な `BACKOFF_NOINLINE=1` を証明できない

**根拠 (file:line)**

プランは「genome に `BACKOFF_NOINLINE=1` がない」「configure override がない」「記録 commit の default が 0」の組合せから非診断 build を導きます。[s2-plan.md:54](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/s2-plan.md:54>) [s2-plan.md:155](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/s2-plan.md:155>)

しかし producer の genome はそもそも `BACKOFF_NOINLINE` を持たず、[backoff_sweep.py:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/backoff_sweep.py:198)、build command も genome にある flag と `CCBENCH_TRACE` だけを明示します。[model.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/model.py:61) [buildcache.py:1936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/buildcache.py:1936)

さらに backoff sweep の事前 gate は `BACKOFF_FIXED` しか検査しません。[backoff_sweep.py:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/backoff_sweep.py:378) 一方、build admission は allowlist 内の `cmake/Options.cmake` と `include/backoff.hh` の変更を machine-generated evidence として受理できます。[source_digest.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/source_digest.py:95) [build_admission.py:641](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/build_admission.py:641)

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

`CCBENCH_BACKOFF_NOINLINE` の default が `1` になった allowlist 内 source から、現行と同じ genome、`CCBENCH_TRACE=0`、`BACKOFF_NOINLINE` override なしで certified WAL を作る。両 arm の tracked diff と toolchain を同じにし、result/reservation の自己整合も取る。

予定述語では明示値 `1` がどこにもないため `diagnostic-build` が発火せず、実際には noinline 診断 binary の throughput を `accepted` と結論できます。WAL の source digest は変化しますが、プランには preregistered commit から導いた期待 source digest との比較がありません。

**直し方の方向**

欠如を `0` と解釈しないこと。既存 evidence から preregistered commit の patch bytesと recorded source identity を結合して effective value を再導出するか、この producer に限って build-bound な明示的 `BACKOFF_NOINLINE=0` を限定的に残す必要があります。

### 所見 2 — sanctioned launcher と実 repository commit が consumer まで束縛されない

**根拠 (file:line)**

consumer は `reservation.binding.script_sha256` を読む予定ですが、受理条件にはその比較先も拒否条件もありません。[s2-plan.md:134](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/s2-plan.md:134>) [s2-plan.md:149](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/s2-plan.md:149>)

launcher 自身は実行 script、submitted digest、commit 内 blob の三者を照合しますが、これは実行時検査です。[a5_second_boot_backoff_sweep.sh:378](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/tools/pegasus/a5_second_boot_backoff_sweep.sh:378) 事後 consumer が読む result/reservation はその検査結果を認証する receipt ではありません。

実 repository commit に最も近い durable field は `campaign.lock.authority.contract_loader_commit` で、lock 作成時に記録されます。[campaign_lock.py:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/campaign_lock.py:152) [ident.py:583](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/ident.py:583) ところがプランの lock 入力一覧は CCBench commit と environment digest だけで、この field を source commit と比較する経路を示していません。[s2-plan.md:138](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/s2-plan.md:138>)

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

正常な producer root の `reservation.binding.script_sha256` だけを `00…00` に変更する。予定受理条件の残りはすべて同じなので、sanctioned launcher と一致しない入力でも `accepted` になります。

同様に、commit A の certified campaign に対し、result と reservation の `repository_commit` を preregistration が期待する commit B にそろえ、lock の `contract_loader_commit=A` を残す。詳細計画どおり lock fieldを読まなければ「commit B で sanctioned launcher が作った」と誤認します。

**直し方の方向**

第2部品を純増ゼロとするなら、少なくとも第3部品で `repository_commit == authority.contract_loader_commit` と、`binding.script_sha256` がその commit の A-5 script blob digest に一致することを束縛する必要があります。

### 所見 3 — gitlink の「exact 比較」は実物の 40桁対7桁で成立しない

**根拠 (file:line)**

A-5 result/reservation は full 40桁 gitlink を記録します。[a5_second_boot_backoff_sweep.sh:763](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/tools/pegasus/a5_second_boot_backoff_sweep.sh:763) 実物も `511c9538e4e8efa54b45cda62e72389ed3b706ec` です。[reservation.json:1](</work/1/SFC/tanab/a5-second-boot-runs/a5-second-boot-backoff-sweep-20260906T171922Z-31812-write-heavy/reservation.json:1>)

一方、campaign config と WAL source evidence は `pin.CURRENT_PIN = "511c953"` を使います。[pin.py:28](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/pin.py:28) [backoff_sweep.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/backoff_sweep.py:55) 実 campaign.lock も7桁です。[campaign.lock:1](</work/1/SFC/tanab/a5-second-boot-runs/a5-second-boot-backoff-sweep-20260906T171922Z-31812-write-heavy/campaigns/backoff-sweep-silo-write-heavy-sweep-8e82cd3f/campaign.lock:1>)

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

実在する A-5 root を入力し、preregistered gitlink に full 40桁を渡す。プランどおり result、reservation、lock、WAL を exact 比較すると、`511c9538…` と `511c953` が不一致になり、正当な入力を `pair-identity-mismatch` と誤って拒否します。

これを prefix 比較へ緩めると、今度は「exact gitlink identity を検証した」という結論が偽になります。

**直し方の方向**

比較前に同じ canonical 表現へ解決する必要があります。producer root だけから full object を一意に解決できないなら、この identity に限った schema 拡張が「schema 拡張不要」より先です。

### 所見 4 — pair 間の「source patch identity」は比較 field が未確定で、実正例の `src_token` は一致しない

**根拠 (file:line)**

プランは両 arm の source patch identity 一致を要求しますが、どの field を等値比較するかを定義していません。[s2-plan.md:153](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/s2-plan.md:153>)

実 balanced WAL では baseline の `src_token` は `stock`、`source_bytes_sha256` は `2d691b…` です。[wal.jsonl:1](</work/1/SFC/tanab/a5-second-boot-runs/a5-second-boot-backoff-sweep-20260906T171922Z-31812-balanced/campaigns/backoff-sweep-silo-balanced-sweep-0dd37c05/runs/wal.jsonl:1>) fixed-5 は `src_token=21def7…` で、source bytesも異なります。[wal.jsonl:16](</work/1/SFC/tanab/a5-second-boot-runs/a5-second-boot-backoff-sweep-20260906T171922Z-31812-balanced/campaigns/backoff-sweep-silo-balanced-sweep-0dd37c05/runs/wal.jsonl:16>) これは genome-dependent preprocess identity なので正常です。両者で同じなのは tracked diff と tracked path 集合です。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

上記実 balanced WAL に将来正当な result が付いたものを入力する。author が `src_token` または `source_bytes_sha256` を「source patch identity」と解釈すると、正常な stock-inline pairを `pair-identity-mismatch` と誤って拒否します。

**直し方の方向**

pair 間で同一であるべき patch-level fieldと、genomeごとに異なる effective source fieldを分離して名指しすること。少なくともテスト名の `source drift` を具体的な field へ落とす必要があります。

### 所見 5 — `pair-cardinality` は genuine producer の出力集合上で発火不能

**根拠 (file:line)**

A-5 finalizer は result 作成前に8個の canonical genome、abort 0、全commitを要求します。[a5_second_boot_backoff_sweep.sh:649](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/tools/pegasus/a5_second_boot_backoff_sweep.sh:649) さらに exact baselineとworkload別 targetを一意選択してから、[a5_second_boot_backoff_sweep.sh:735](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/tools/pegasus/a5_second_boot_backoff_sweep.sh:735) 初めて result をpublishします。[a5_second_boot_backoff_sweep.sh:770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/tools/pegasus/a5_second_boot_backoff_sweep.sh:770)

したがって genuine `result.json` の存在が、baseline/fixed-5 の一意存在を既に含意します。

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

fixed-5 を欠く genuine A-5 run を入力すると finalizer が result を作らず、consumer は `producer-artifact-missing` で止まります。完成 root から fixed-5 WAL recordsだけを消すと、先に `wal_sha256` 不一致で止まります。

よって予定する `pair-cardinality` の赤は単独変異では到達できず、「consumer が producer から独立して片側欠損を検出した」というテスト結論は誤りです。

**直し方の方向**

`pair-cardinality` を独立した producer-facing 保証として数えないこと。維持するなら、これは synthetic/tamper 診断であり genuine A-5 の欠損分類ではないと契約を狭める必要があります。

### 所見 6 — reject は診断文字列だけで、規律3に必要な原因を残さない

**根拠 (file:line)**

reject 型は `T1998PairRejected(code: str)` だけです。[s2-plan.md:163](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/s2-plan.md:163>) 構造化された返却値は `accepted` と `inconclusive` だけで、rejected decision はありません。[s2-plan.md:178](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/s2-plan.md:178>)

特に `pair-identity-mismatch` は source、gitlink、contract、env tag、toolchain を一つの code に畳みます。[s2-plan.md:170](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/s2-plan.md:170>)

**壊れる筋 (具体的な入力と、そのとき出る誤った結論)**

target の `build_done.toolchain.cxx.realpath` だけが baseline と異なる入力を渡す。consumer が残す情報は `pair-identity-mismatch` だけなので、source drift、environment drift、toolchain driftのどれだったかを後から判定できません。「toolchain不一致で拒否した」という帰属は成果物から再検証不能です。

**直し方の方向**

既存 reject ごとに `field`、`expected`、`actual`、対象 variant/attempt を持たせること。新しい一般 gate は不要で、予定済み拒否理由の証拠投影だけに限定できます。

## 親 brief 自身への所見

- **(P1-a) は自己矛盾しています。** brief は「T-1998 の producer として名指す別経路が要る」と認定していますが、[brief.md:46](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/brief.md:46>) プランは launcher を0 byteとし、script digestの束縛も追加しません。[s2-plan.md:83](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/s2-plan.md:83>) D1244 が要求した3部品のうち、第2部品の「T-1998 への束縛」は未充足です。

- **(P1-c) の「schema 拡張不要」は確定できません。** full gitlink対7桁pinの不整合と、`BACKOFF_NOINLINE=0` が明示 evidence でない問題が残っています。brief 自身も noinline state が result に無いと認定しています。[brief.md:59](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/brief.md:59>)

- **(P1-d) の「consumer の入力 field は実環境で到達可能」は一般化しすぎです。** 実在する complete result は write-heavyだけで、balancedには resultがありません。[brief.md:54](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/brief.md:54>) [a5-measured.md:14](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/verbatim/a5-measured.md:14>) したがって balanced consumer の完全な正例が実環境で到達した事実はまだありません。

- **2026-09-07 の値は raw WAL 上の実測値だが、T-1998 の主張へは転用できません。** none 3,803,883、fixed-5 4,294,095 は実在します。[a5-measured.md:35](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/verbatim/a5-measured.md:35>) ただし run は commit `0ade09d5e…` に束縛され、[a5-measured.md:8](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/verbatim/a5-measured.md:8>) 本 wave の基準 `c5754d1f…` と異なります。[brief.md:3](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/brief.md:3>) 加えて result 欠損で予定 consumer が拒否し、3部品land後の prospective preregistration と正式認可より前の測定です。[d1244.md:3](</home/SFC/tanab/.claude/jobs/be613c5f/tmp/t1998-wave/verbatim/d1244.md:3>) 数値の存在とT-1998適格性を同一視できません。

## 変異の帰属が成立しない箇所

- `test_missing_preregistered_arm_is_pair_cardinality_reject`: genuine runでは result欠損、既存完成rootの単独WAL変異では先に WAL SHA 不一致です。

- `test_pair_identity_drift_is_rejected`: repository commitとenvironment contractはarm固有fieldではありません。gitlinkはlock-globalで、片arm変更は artifact admission の source/lock 一致検査に先に落ちます。[artifact_admission.py:1407](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/artifact_admission.py:1407>) contractの片arm変更も WAL topology が先に拒否します。[wal.py:2104](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/wal.py:2104>) `pair-identity-mismatch` へ単独で届くのは実質 toolchain driftだけです。

- `test_backoff_noinline_one_is_diagnostic_build_reject`: target genomeへ keyを足すと current A-5 finalizerの canonical genome集合から外れます。完成rootの単独変異なら WAL SHA、genome/variant、receipt bindingにも先に落ちます。さらに full-genome exact selectorなら `pair-cardinality` が先です。

- `test_real_commit_receipt_rejection_dominates_pair_values`: 名前どおり `require_admitted_campaign` が全COMMIT receiptを先に検査します。[artifact_admission.py:1491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/artifact_admission.py:1491>) 後段の `admit_replay_evidence()` の拒否へは届かず、consumer固有gateの変異試験にはなりません。

- `test_larger_off_grid_tps_cannot_replace_fixed_five`、`test_trace_enabled_command_is_not_performance_evidence`、`test_unstable_either_arm_is_inconclusive`: 完成rootのWALを単独変更すれば、いずれも先に result の WAL SHA gateが赤です。狙った層へ届かせるには result SHA、commit payload、receiptなども再発行する必要があり、「同じ入力への単独変異」ではありません。

- `producer-rejected-variant` の anomaly、非serializable、receipt不正: persisted COMMITについては共通 admission が先に拒否します。[artifact_admission.py:752](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1998-stock-inline-parts/orchestrator/campaign/artifact_admission.py:752>) この code に帰属できるのは主に明示 abortで、表の4分類を一つのconsumer gateとして扱えません。

## 総括

このプランのままでは、D20の診断build排除、sanctioned launcher/source commitの束縛、full gitlink identityの3点が成立しません。さらに pair-cardinality と複数の負テストは上流gateに隠れ、予定した拒否理由へ単独変異で到達できません。

2026-09-07 の balanced 数値は raw 測定として存在しますが、T-1998 の formal claimへは転用不可です。静的検査のみで、file変更・test・build・測定は行っていません。