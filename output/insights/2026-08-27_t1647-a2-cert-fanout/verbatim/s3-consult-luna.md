結論: 現行の段 2 plan はそのまま実装へ進めません。P1・P2、6 contract の bump 方針、6 時間維持は採れますが、P4 の共有 root と fan-in 経路は再設計が必要です。

## 所見

### 1. 並行投入の条件 1 を満たしていない

該当: [s2/out.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:17)、[run_workload:2204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2204)、[finalize:2253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2253)、[判定枠組み:48](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/refs/fanout-independence.md:48)

| 条件 | 判定 | 根拠 |
|---|---|---|
| 1. read/write 集合が独立 | **不成立** | 2 job が同じ attempt、`raw/`、`campaigns/`、claim namespace を共有し、finalizer が親 `raw/` を走査する |
| 2. protocol が順序・単一テナントを要求しない | **成立** | workload 内だけ stock→adopted を維持し、workload 間の実行順序は要求されない。[run_workload:2182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2182) |
| 3. 固定費が見合う | **成立。ただし walltime 根拠には不足** | 必須 5 反復の verifier だけで rr5 約1,202秒、rr50 約2,277秒。各cell 1観測で、ばらつき・legacy correctness は未測定。[cost:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/output/insights/2026-08-26_a2-4cell-walltime-cost.md:16)、[同:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/output/insights/2026-08-26_a2-4cell-walltime-cost.md:72) |

さらに両 job は `attempt/campaigns` を共用し、同じ claim directory を列挙します。[run_workload:2204](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2204)、[campaign_claim:348](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/campaign_claim.py:348)。B-10 の先例は workload ごとに完全に別の top-level root を切っており、今回の共有 attempt とは同型ではありません。[submit_b10:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/submit_b10_backoff_grid.sh:87)

具体的な退化経路: job 専用の `raw/rr5` と `raw/rr50` を作っても、後段 `finalize-raw` が親 `raw/` の inventory を判断材料にするため、「親 consumer を共有しない」という条件を満たしません。

成果物影響: fan-out を「独立 job」と記録できず、並行投入の裁定根拠が成立しません。

推奨: **P4 を落とす。** `jobs/$workload/{raw,campaign-output,cache,reservation,scheduler}` を完全な job-owned subtree とし、`run_workload` の `output_root` と `cache_root` もそこへ移す。finalizer は親 directory を列挙せず、policy から導いた4本の exact pathを直接開く形にする。

---

### 2. preregister と compute-preflight が同じ directory の作成権を主張している

該当: [s2/out.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:17)、[同:33](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:33)、[同:68](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:68)、[compute_preflight:2537](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2537)

計画は preregister が `raw/{rr5,rr50}` を作る一方、compute-preflight にも同じ `raw/$workload` の create-only 作成を要求しています。現行述語は「既に存在すれば拒否」してから `mkdir(exist_ok=False)` するため、そのまま実装すると1本目から停止します。

これを安易に `exist_ok=True` へ緩めると、同じ workload の重複 qsub が同時に fresh 検査を通り、測定開始前の原子的 one-shot claim が消えます。

成果物影響: 現計画どおりなら raw cell は1件も生成されず、緩和で直すと同一 cell の再取得面が開きます。

推奨: **落とす。** preregister は `raw/` 親と job/scheduler container だけを作り、`raw/$workload` は compute-preflight の原子的 `mkdir` に残す。事前作成が必要なら、別の `job-claim` を `O_EXCL` で取得してから測定する。

---

### 3. fresh 緩和による workload 単位の選択的取り直しは、上記修正後なら反証できる

該当: [job body:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:37)、[同:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:89)、[同:152](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:152)、[同:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:217)、[run_workload:2185](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2185)

**反証:** workload root を preflight が原子的に作る構成なら、

- 測定前に raw directory が one-shot claim になる
- 失敗時も trap が workload 別 compute-result を publish する
- reservation、allocation qstat、cell JSON も create-only
- 一方だけ nonzero なら group completion が manifest を受けない

ため、同じ attempt 内で「良い値が出るまで片側だけ再実行」は通りません。job が raw directory 作成前に死んだ場合は測定前なので、値の選別にもなりません。

成果物影響: 修正後は certified cell 集合を変えず、失敗単位だけ workload に縮められます。

推奨: **採る。** ただし同一 workload の2回目を、compute-result／reservation／raw claimそれぞれ単独で拒否する負例を追加する。

---

### 4. 投入束縛の恒真化・job取り違え懸念は条件付きで反証

該当: [submission validator:778](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:778)、[同:810](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:810)、[同:816](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:816)、[completion:997](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:997)、[reservation:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:1040)

**反証:** `job_body_sha256`、argv末尾、`submission_cwd`、`source_commit` が2件で同値なのは意図された group-level 束縛であり、別 script・別 repo・別 commit を拒否するので恒真ではありません。job識別は次で行えます。

- entry の workload と `qsub -v` の workload
- workload別 stdout/stderr path
- qsub stdout・qstat visibility の request ID
- compute-result の workload・PBS ID・canonical path
- reservation の job ID・script hash

rr5/rr50 の request ID だけを交換すると、workload別 compute-result の `pbs_jobid` で拒否されます。entry 全体を交換すると policy 順／workload mapping で拒否できます。

成果物影響: exact distinctness と全交差照合を実装すれば、2 job を取り違えた group receipt は certification に到達しません。

推奨: **採る。** v4 validator で workload集合・順序・request ID distinctness・log path distinctnessを明文化し、submission-only と completion cross-binding の両段に別々の swap 負例を置く。

---

### 5. group completion/acquisition の実 producer が計画にない

該当: [s2/out.md:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:51)、[同:55](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:55)、[record_completion:1189](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:1189)、[CLI recorder:2662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2662)

新 submitter の予定範囲は2回の qsub と submission receipt 作成で終わります。現行 `record-completion` は caller が用意した JSON を検証して保存するだけで、2 request の終端観測、log hash、compute/reservation hashを生成しません。

具体的な突破・退化経路: 正式走では operator が completion payload を手書きするか、別の未記載 script が必要になります。これは到達可能な正規 producer がない wire contract です。

成果物影響: job が両方完走しても group completion/acquisition を正規生成できず、collect へ到達できません。

推奨: **落とす。** 同じ submitter に create-only な `finish-group` modeを設け、submission receiptの exact IDsだけをpollし、terminal観測・hash・finalize・completion・acquisitionを一続きで生成させる。

---

### 6. login-side finisher と新 `local-ok` 分類は既存 admission 規則に反する

該当: [s2/out.md:75](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:75)、[runbook:479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/docs/pegasus-runbook.md:479)、[同:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/docs/pegasus-runbook.md:482)、[Pegasus README:11](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/README.md:11)

runbook は grandfather 対象を既存4本に限定し、その他を `local-ok` にするには所定の実測が必要と明記しています。計画の `static login-side submitter classification` はその例外に入りません。また README は最終 collector の login 実行を blocked と記録しています。

成果物影響: 新 submitter／finisher の実走が admission 上正当化されず、gate配線の実測自体が規則違反になります。

推奨: **裁定へ返す。** login finisher の admission 実測経路を先に確定するか、軽量な第3 qsub jobへ fan-inを移す。runbook の表だけでなく §7.5 と3段連鎖の記述も更新する。

---

### 7. `IZANAGI_A2_WORKLOAD` の到達可能性は反証できる

該当: [s2/out.md:132](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:132)、[既存実走記録:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/output/insights/2026-08-25_paper-story-a2-certification-run-defects.md:31)、[B-10 submitter:168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/submit_b10_backoff_grid.sh:168)

**反証:** A-2 の既存実走は qsub の必須環境6本が compute nodeへ到達したことを実測済みで、B-10 も同じ `qsub -v` workload径数化を使っています。さらに v2 compute-result に workloadを書けば、request IDと実効値を同じ compute processから観測できます。未実測の `Variable_List` を採らない判断も妥当です。

成果物影響: 新 workload field は実環境で観測可能であり、未観測 scheduler field に依存しません。

推奨: **採る。** ただし live gate runで rr5/rr50 の両値を取得するまでは「配線済み」とのみ書き、「実測済み」とは書かない。

---

### 8. walltime 縮小は現 plan には入っていない。将来縮小すれば受理集合を変える

該当: [s2/out.md:16](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:16)、[同:92](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:92)、[reservation check:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/loop.py:191)、[collector:2589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2589)

**反証:** 射影された段1 briefには縮小方針はなく、段2 planは明示的に `06:00:00` を維持しています。

将来縮める場合、reservation gate は `required_s=1` の存在検査にすぎず、campaign全体の完走時間を保護しません。scheduler kill時は、trapが動けば nonzero driver→indeterminate、動かなければ compute-result欠落となります。false passにはなりませんが、受理集合と終端分類は狭まります。

現実測の母集合は Pegasus・pin `511c953`・4 cell各1反復だけで、反復間変動、小correctness、cooldownは未観測です。[cost:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/output/insights/2026-08-26_a2-4cell-walltime-cost.md:72)

成果物影響: 今回は不変。別途縮小すると、同じ科学的結果でも scheduler termination により indeterminate が増えます。

推奨: **現planの6時間維持を採る。** 短縮は exact full-chain の workload別分布を取った別wave・別裁定にする。

---

### 9. 6 contract bump は妥当だが、consumer inventory が不足

該当: [schema constants:41](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:41)、[compute producer:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:47)

現物で確認した現行値は以下です。

- submission v3、completion v2、acquisition v2
- certification result v2、compute result v1、raw manifest v2

取り残し候補:

- submission v3 の explicit golden: [test:727](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/test_paper_story_a2_certification.py:727)
- 実 qstat fixture は旧単一log pathを保持: [fixture:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/fixtures/paper_story_a2/qstat-visibility-945411.stdout:21)。計画は「job名が同じなので変更不要」としていますが、v4の workload別pathとは矛盾します。
- acceptance ledger は既存A-2 nodeを [9031–9116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/tests/acceptance_duration_ledger.json:9031) に固定。新規testを追加する以上、「旧名を変えた場合だけ更新」では不足です。
- 歴史的逐語は submission v3据置きを記録: [run-defects:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/output/insights/2026-08-25_paper-story-a2-certification-run-defects.md:78)。これは過去記録なので書き換えず、後継文書からsupersedeする対象です。
- repo内に6 schemaを持つ tracked な既存receipt/result JSONはありません。JSON fixtureはtest helperが定数から生成しています。

成果物影響: fixtureがscheduler pathとの自己矛盾を保持するか、新規test nodeが受入所要台帳から欠落します。

推奨: **6 bump自体は採る。** 旧 qstat fixtureは歴史物として残し、fan-out実走からrequest別fixtureを2本追加する。acceptance ledgerは正規生成器で新nodeも含め再生成する。

---

### 10. `docs/failures.md` 直接編集は明示的な規則違反

該当: [s2/out.md:87](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:87)、[spool規則:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/docs/spool/README.md:3)、[failures fragment:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/docs/spool/failures/README.md:43)

対象は F498 です。[failures:13806](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/docs/failures.md:13806)。既存行の直接改稿ではなく、

- `## 再発` / `### F498` に2-request実測を記録
- 古い「人間手番が解除条件」という記述の訂正は `## supersede 追記` の1物理行

とする必要があります。

成果物影響: canonical ledgerを直接変えると、land/fold契約違反になり履歴の逐語性も壊します。

推奨: **直接編集を落とす。** `docs/spool/failures/` の正式fragmentへ置換する。

---

### 11. 計画された負例だけでは変異の帰属が立たない

該当: [s2/out.md:83](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:83)、[既存mutation erratum:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/output/insights/2026-08-25_paper-story-a2-certification-driver.md:78)

具体的な mask は次です。

- shellのraw fresh検査を残したまま compute-preflightのfresh述語を変異すると、shellが先に拒否します。[job body:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/tools/pegasus/paper_story_a2_certification.sh:217)、[preflight:2540](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2540)
- request/workload/pathをまとめてswapする負例は、terminal ID→log accounting→compute ID/workload→reservation IDの最初の不一致で落ち、後段防壁の変異を帰属できません。[completion:926](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:926)
- nested raw inventoryは finalizer と manifest loader の両方が検査するため、通常生成経路だけでは一方の変異が他方にmaskされます。[finalizer:2257](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2257)、[loader:2329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2329)

成果物影響: `KILLED`でも対象防壁を殺した証明にならず、後段防壁の変異が`SURVIVED`しても検出漏れとは限りません。

推奨: **現matrixを落とす。** 各fieldを1件だけ不整合にし、それ以前の全fieldをcanonicalに保つfixtureを作る。fresh二層とraw二層は直接unit callまたはpair mutationとして別帰属にする。

---

### 12. 別wave所有物への越境懸念は反証

該当: [s2/out.md:19](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1647-a2-cert-fanout/s2/out.md:19)、[closure list:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/campaign_lock.py:29)

**反証:** 計画は `campaign_lock.py`、`contract_loader_binding.py`、`artifact_admission.py` を変更対象に含めていません。A-2 driver/job/policyも現行25-path enforcement closureには入っていません。

成果物影響: T-1629の編集面やclosure digestを本変更が直接動かす計画にはなっていません。

推奨: **この境界は採る。**

## 裁定パッケージ候補

### 既存の「attemptを変えて良い結果だけ採る」面

該当: [create_attempt_root:600](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:600)、[preregistration:623](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:623)、[materialize:2423](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1647-a2-cert-fanout/orchestrator/campaign/paper_story_a2_certification.py:2423)

`automatic_retry: false` は記録されるだけでconsumerがなく、異なる attempt IDを何個でもpreregisterできます。複数の完全attemptを走らせ、悪いattemptをmaterializeせず、良いattemptだけ固定destinationへmaterializeする経路は現行から存在します。fan-out v4の同一attempt交差束縛は「rr5をattempt A、rr50をattempt Bから混ぜる」ことは防げますが、attempt全体の選別は防ぎません。

成果物影響: 既存のA-2 certification全体に、attempt単位の測定値選別余地が残ります。

推奨: **裁定へ返す。** attempt IDまたは投入回数を事前登録authorityへ束縛する設計が別waveで必要です。

## 総括

- 最重: 共有 `raw/`・`campaigns/` と親走査finalizerにより、fan-out独立条件1が不成立。
- 次点: preregisterとpreflightが同じ `raw/$workload` を作る自己矛盾があり、緩和すると再取得面が開く。
- 次点: group completion/acquisitionのproducerとlogin admission経路が計画に存在しない。
- P1・P2、6 schema bump、6時間維持、別wave所有境界は採用可能です。
- pytest・PBS・Webは実行せず、静的読解のみです。