# 静的設計監査

結論は **NO-GO**。設計案は局所的な配線を追加できるが、authority/evidence の成立、正の production 発火証拠、予約後回復、formal consumer が欠けたままであり、現状では「実装済みの成果層」と会計できない。

以下の「静的確定」は今回のコード・文書検査、「親記録」は既存成果物の記載、「推論」はそれらから導く設計上の帰結を指す。pytest・計測・受入全走は実行しておらず、緑は主張しない。

## 所見

### 1. `blocker` — 11層は最大でも6/11、成果として閉じる層は0/11

**主張:** 設計者に最も有利に「案をすべて実装した」と数えても、局所機構として埋まるのは第2〜7層の6層、空のままなのは第1・8〜11層の5層である。ただし第1層が空で正の artifact path もないため、end-to-end の研究成果として有効に閉じる増分は0層である。

| # | 前waveの11層 | 全案実装後 |
|---:|---|---|
| 1 | authority 値・発行 | **空**。値・発行者の具体物を本案は決めない |
| 2 | public authority reader/live cell | 機構として埋まる |
| 3 | runtime bootstrap/storage/migration | 機構として埋まるが、回復と世代選択は未確定 |
| 4 | producer translator/batch journal | 非認定8c用に埋まる |
| 5 | production caller | 非認定8c用に埋まる |
| 6 | durable origin-proof issuance | sidecar 発行面だけ埋まる |
| 7 | report schema/current consumer check | report v3/completeness の局所 consumer は埋まる |
| 8 | trial registry origin binding | **空** |
| 9 | P7 formal consumer | **空** |
| 10 | Layer3/WAL/formal material report | **空** |
| 11 | positive runbook/audit/crash recovery | **空** |

要求された別の切り口では、producer・CLI・pilot driver・局所 batch policy は埋まる。registry/issuer・正式記録・formal consumer・end-to-end proof chain は埋まらない。storage/lock admission は機構だけで、安全閉包は埋まらない。

**根拠:**

- `[静的確定]` 11層の正本は `output/insights/2026-08-05_t244-p3-producer-wiring/s3-lensB.md:24-40`。
- authority 値は未決定で、人間 issuer の入力だけを列挙している。`output/insights/2026-08-05_t244-p3-design/s2-plan.md:124-184`
- reader/bootstrap/producer/driver/sidecar/report は提案されている。`s2-plan.md:231-403`, `s2-plan.md:407-469`, `s2-plan.md:556-612`
- formal H1/H2・P7・formal material report 等は残余として明記される。`s2-plan.md:637-663`
- trial registry は declaration-only、`certifying=False`、`arm_binding="declared-only"` のまま。`orchestrator/campaign/trial_registry.py:2-6`, `trial_registry.py:124-129`

**設計への効き:** 「6層実装」とは機構面の最大値に限って記録し、成果層・proof chain・budget binding 完了とは記録してはならない。authority発行、formal consumer、positive artifact が閉じるまで成果会計は増やせない。

---

### 2. `blocker` — 現在、予算が減る production path は存在しない

**主張:** 現コードで予算カウンタが動くのは `BatchCommitted` reducer だけである。しかしそのAPIを呼ぶ production caller はない。単一候補×R replicate は「同じwireを複数commitmentにできる」だけであり、現時点で「batch freezeを結線した」「予算束縛を実現した」とは名乗れない。

**根拠:**

- `[静的確定]` iteration/query counter は `BatchCommitted` 受理時にだけ増える。`orchestrator/campaign/reflux_origin_ledger.py:1077-1127`
- ledger 自身が prototype であり、producer/driver/formal consumer は未結線と明記する。`reflux_origin_ledger.py:2-23`
- 現8c driverは planner/coder/auditor/critic を回すだけで、ledgerを呼ばない。`orchestrator/campaign/p3_autonomous_workload_trial.py:1442-1682`
- 同一wireの正例は fixture test にしかない。`orchestrator/tests/test_reflux_origin_ledger.py:2247-2289`
- sealed query 行数は物理query数ではない、という限定は設計案自身も認める。`s2-plan.md:14-22`

**設計への効き:** P3の「第1段が予算束縛を実体化する」という provisional 裁定は撤回が必要である。名乗れる上限は、正の実走後でも「非認定8cの同一wire reserved-replicate 配線」に限る。

---

### 3. `blocker` — DW-G04を満たす受理artifact/計測IDがない

**主張:** 受理側が候補を受け取り、予算を消費し、sealまで到達した既存 production artifact path または計測IDは書けない。計画が列挙するものは現在系を拒否する検査と、実装後に行う予定の検査である。

**根拠:**

- DW-G04は既存の発火artifact pathまたは計測IDを要求する。`docs/dev-wave/core.md:57-60`
- authority registry は空。`orchestrator/campaign/reflux_origin_authority_v2.json:1`
- production initialization は現コードで明示的に禁止される。`reflux_origin_ledger.py:2554-2639`
- 計画の検査1〜8は現baselineの拒否、正例は将来形の9番だけである。`s2-plan.md:616-633`
- fixture testはproduction artifactでも計測IDでもない。`orchestrator/tests/test_reflux_origin_ledger.py:2247-2289`

**設計への効き:** G04の条件を満たすまで、予約FSM・8c report v3・proof sidecarは設計メモ止まりにすべきである。「実装後に正例を作る」はG04先行条件の代替にならない。

---

### 4. `blocker` — DW-G01の最安生死実験が先行していない

**主張:** 計画はauthority schema、provisioning、epoch router、reservation FSM、8c改修、report v3、sidecarを一括してから正例を作ろうとしている。これは最安の生死確認ではない。

**根拠:**

- DW-G01は大型機構前に既存driverまたは100行以内の使い捨てdriverを要求する。`docs/dev-wave/core.md:42-45`
- 既存E driverには機械経路と実走CLIがある。`orchestrator/campaign/p3_s4_loop_trigger_gating.py:783-835`
- 実在コマンドは `docs/phase3-s8a-trigger-runbook.md:64-84` にある。
- 計画の最初の正例は全機構実装後のテストとしてのみ置かれる。`s2-plan.md:616-633`

**設計への効き:** 次へ縮約すべきである。

1. 有効なauthority entry 1件と最小の明示provisioningだけを先に成立させる。
2. 100行以内の使い捨てwrapperで、同一wire・R=2を現行batch APIへcommitし、既存E driverを呼び、prepare/seal receiptを1個保存する。
3. 既存CLIは次を用いる。

```bash
python3 -m campaign.p3_s4_loop_trigger_gating --preview-wire 11111
python3 -m campaign.p3_s4_loop_trigger_gating \
  --run-iteration <scratch>/prop.json \
  --allow-coder-derived-build
```

成果物候補は `reports/p3_s8a_trigger_loop_provenance.json` とledger receiptを束ねた一時artifactでよい。この実験は「受理・counter更新・sealの生死」だけを証明し、kill-before-commit対策や科学的有効性は名乗らない。

---

### 5. `major` — 8cへの結線で得られるのはpilot配線証拠だけ

**主張:** 8cはycsb-a/b/cしか走らず、正式holdout H1/H2を走らせない。この宿主から得られる研究成果は、非認定pilotでproducerが生きること、物理replicateとledger cross-referenceを保存できることまでである。certified選択、正式材料レポート、正式trial registryの前進ではない。

**根拠:**

- 8cのworkload集合はycsb-a/b/c。`p3_autonomous_workload_trial.py:139-175`
- 8cの出力は `scientific_claim=false` のpilot。`p3_autonomous_workload_trial.py:1002-1019`
- 正式holdoutはH1=rr80、H2=rr20。`trial_registry.py:41-49`
- registry受理は6 reportsとrr80/rr20を要求する。`trial_registry.py:1298-1425`
- 設計案はpilot限定を明記し、正式値を変えないとしている。`s2-plan.md:409-411`, `s2-plan.md:528-554`, `s2-plan.md:637-655`

**設計への効き:** 宿主選択そのものと名乗り上限は妥当である。ただし `s2-plan.md:469` の「材料レポート」や `s2-plan.md:502` の「certified selection」はpilot成果に置き換える必要がある。

---

### 6. `blocker` — N7のlinux-baremetal再測定可否は不明で、authority bootstrapが測定待ちになる

**主張:** repository内の証拠から、linux-baremetalで再測定できるとは判断できない。Pegasus compute nodeで走らせられることは、別environment cellの計測可能性であり、linux-baremetalの代替証明ではない。またproducerのclock hardcode修正だけではworkload不一致も解消しない。

**根拠:**

- `[静的確定]` artifactは `env_tag=linux-baremetal` なのに `clocks_per_us=2100`。`output/env/linux-baremetal/calibration/s8a_trigger_gating_coverage.json:2-5`
- env registryはlinux=1800、Pegasus=2100。`orchestrator/campaign/env_contract.py:169-193`
- producerはlinux tagと2100を別々にhardcodeする。`orchestrator/campaign/s8a_trigger_coverage.py:63-65`, `s8a_trigger_coverage.py:243-245`
- 同producerの形状はtuple=200/rr=50/rmw=true/threads=4で、8cのycsb-a/b/c evidenceとは同一でない。`s8a_trigger_coverage.py:74-84`, `p3_autonomous_workload_trial.py:139-175`
- 過去記録は約4分のcharacterizationで「計測なし」とする。`docs/archive/worklog-phase3-0702-0713.md:1695-1697`
- runbookはlinuxホストまたはjob IDを固定していない。`docs/phase3-s8a-trigger-runbook.md:127-145`
- Pegasus上の重い処理はcompute nodeで行い、Pegasus用env contractを使う。`docs/pegasus-runbook.md:298-313`, `docs/pegasus-runbook.md:472-517`

**設計への効き:** linux資源を確保できなければauthority manifest用evidenceを発行できず、production genesisも開始できない。したがってauthority bootstrapは独立した測定タスクに依存する。P6は「clockをenv由来にする」だけでなく、workload別artifact、full pin closure、実行host/job IDまで固定する必要がある。

---

### 7. `major` — 親briefのN6は誤り、設計案の訂正は必須

**主張:** `ccbench_commit_oid` の既存preimage規則は完成していない。`CURRENT_PIN` は7桁だがmanifest parserは40桁を要求する。

**根拠:**

- 親はN6で既存規則として数えている。`output/insights/2026-08-05_t244-p3-design/brief.md:46-57`
- `CURRENT_PIN` は7文字。`orchestrator/campaign/pin.py:28`
- manifest OID validatorは40-hexを要求する。`reflux_origin_ledger.py:364-390`
- 設計案自身がN6を訂正している。`s2-plan.md:78-93`

**設計への効き:** full captured Git OIDへの解決規則をauthority preimageの一部にしなければならない。ここは設計案の訂正をそのまま採るべきである。

---

### 8. `blocker` — reservation後のcrash recoveryが設計されていない

**主張:** 予約・commit後にprocessが落ちると、再開に必要なwire、salt、opening、resultをpublic recovery handleから取得できない。8cも既存run rootへのresumeを拒否する。予算を非返却にするなら、abort terminalと回復WALを先に定義しなければoriginを永久停止させ得る。

**根拠:**

- 現open stateはcommitmentしか保存せず、openingはseal時にだけ検査する。`reflux_origin_ledger.py:1122-1125`, `reflux_origin_ledger.py:1173-1265`
- 提案する`OpenBatchHandle`はwire、commitment、replicate ordinal、result等を返さない。`s2-plan.md:362-403`
- reservation失敗のterminal表現は未決のR7。`s2-plan.md:481-500`, `s2-plan.md:665`
- 8cは既存run rootへのresumeを拒否する。`p3_autonomous_workload_trial.py:1746-1792`
- 前waveもopening喪失による永久停止をreal所見A-5として残した。`output/insights/2026-08-05_t244-p3-producer-wiring/s4-adjudication.md:67`

**設計への効き:** reservation FSMをlandする前に、private recovery WAL、abort terminal、replay、kill injection、再開後のcounter不変性を同じD96単位で決める必要がある。

---

### 9. `疑い` — epoch routerと全origin CASの並行性契約がない

**主張:** global state commitmentは全originを含み、更新は厳密CASである。epoch routerと複数producerを追加するなら、lock粒度、再読込、CAS失敗時のretry/rebase契約が必要だが計画にない。

**根拠:**

- global commitmentは全originを含む。`reflux_origin_ledger.py:2183-2203`
- commit時は現global commitmentとの厳密一致を要求する。`reflux_origin_ledger.py:2885-2888`
- runtime rootはgit-common-dir共有。`reflux_origin_ledger.py:1432-1451`
- 前waveのA-6も共有global state/CASをreal所見として残した。`s4-adjudication.md:68`
- epoch router案は世代意味を説明するが並行更新契約を説明しない。`s2-plan.md:315-360`

**設計への効き:** 直ちに破綻するとまでは静的に断定できないが、複数origin・複数worktreeの競合テストなしにstorage/lock admissionを「閉じた」と数えてはならない。

---

### 10. `major` — sidecarはcross-referenceであってproof chainではない

**主張:** 提案sidecarは必要だが、それだけではproof chainにならない。現在のregistry/formal consumerは読まず、event receipt hashを後から検証する公開経路も設計されていない。

**根拠:**

- `EventReceipt`はcommit呼出し時に返されるだけ。`reflux_origin_ledger.py:561-569`
- `SealedBatch`はorigin/batch/membersしか返さない。`reflux_origin_ledger.py:539-558`
- sidecarはevent hash/state commitmentを要求する。`s2-plan.md:556-612`
- formal consumer未承認を設計案自身が認める。`s2-plan.md:612`, `s2-plan.md:663`
- `TrialBinding`にorigin proof fieldはない。`trial_registry.py:103-114`
- D121のP7はformal consumerによるproof要求を前提とする。`docs/decisions.md:5842-5854`

**設計への効き:** 名称は「producer-side durable cross-reference」に限定する。proof chain完成を名乗るには、公開検証API、report/registry binding、欠落・改竄mutation、formal consumerが必要である。

---

### 11. `blocker` — 1 waveでは安全に閉じない

**主張:** 本案は7件の未裁定を残したまま、authority schema、測定、bootstrap、migration、reader、予約FSM、8c、report/completeness、sidecarを同時に変更する。所有分割・変異事前登録もない。外部測定依存を含むため1 wave完結は成立しない。

**根拠:**

- 未裁定R1〜R7。`s2-plan.md:665`
- 一括変更対象はproduction initializer、authority schema、reservation、report v3、completeness、trial registry。`s2-plan.md:616-633`
- D96は受理集合変更とboundary testを同一単位に要求する。`docs/decisions.md:4269-4297`
- mutationは単一破壊理由の事前登録を要求する。`docs/dev-wave/mutation.md:5-10`, `docs/dev-wave/mutation.md:29-37`
- 所有はdisjoint、依存変更は順次処理が原則。`docs/dev-wave/workers.md:19-24`, `docs/dev-wave/workers.md:46-69`

**設計への効き:** 次の境界で切るべきである。

1. **測定・authority wave:** R1/R2、full OID、workload別linux evidence、authority値の人間裁定。runtime成果は名乗らない。
2. **ledger runtime wave:** provisioning、reader、epoch/recovery、CAS/lock、D96、最小G01/G04正例。
3. **8c pilot wave:** reserved replicate、per-replicate evidence、report v3/completeness、sidecar、pilot artifact。
4. **formal wave:** H1/H2、trial registry origin binding、P7 consumer、formal material report。

各waveが独立したD96・mutation・受入単位を持つべきである。

---

### 12. `major` — 成果物影響欄の一部が実効を過大申告している

**主張:** 多くの節には成果物影響が1行あるが、次は実際の変更範囲を超えているか、影響記述が欠けている。

**根拠:**

- `s2-plan.md:184` はauthority予算がcertified selectionを決めるとするが、値・issuer・formal consumerが未実装。
- `s2-plan.md:469` は「材料レポート」とするが、宿主は `scientific_claim=false` のpilot。
- `s2-plan.md:502` はreservationがcertified selectionの上限を実効化するとするが、8c/registryは非認定。
- `s2-plan.md:612` はproof chainへの追加とするが、formal consumer・検証APIがない。
- `s2-plan.md:554` はcertified selection、正式材料レポート、registry flagが変わらないと正直に明記する。これは実効ゼロの正式成果であり、成果層に数えてはならない。
- D96/検査案 `s2-plan.md:616-633` とR1〜R7 `s2-plan.md:665` には、各選択を放置した場合に四成果物の値・受理集合・参照がどう変わるかの1行がない。
- `s2-plan.md:225` のevidence効果は「再測定後」という条件付きであり、現waveの効果ではない。

**設計への効き:** 影響欄を「pilot journal/report」「formal registry/certified selection」「proof cross-reference」の三段に分離し、現在変わるものだけを書くべきである。とくに3.1、3.2、3.5は現在の表現のままlandすると実効ゼロを正式成果として会計する。

---

### 13. `major` — P2の「既存型を適用し新機構を発明しない」は成立しない

**主張:** s8bから再利用できるのはpointer、transition table、tombstoneという構造パターンだけである。origin追加、既存counter保持、open batch、seal/abort、global commitmentを扱うepoch routerは新しいstate machineである。

**根拠:**

- 親P2は「既存型を適用し、新機構を発明しない」と裁定する。`brief.md:117-124`
- s8bはholdout freeze固有のschemaとtransitionを持つ。`orchestrator/campaign/s8b_ratified_freeze.py:60-141`, `s8b_ratified_freeze.py:914-1021`
- 設計案自身が「origin ledger固有に作り直す部分」を列挙する。`s2-plan.md:321-358`

**設計への効き:** P2は「s8bの構造パターンを参照する」に弱めるべきである。drop-in reuseとして工数・リスク・D96範囲を小さく見積もってはならない。

## 総括

### (a) GO / NO-GO

**NO-GO。** 正のproduction受理artifactがなく、authority bootstrapが未確定の測定に依存し、予約後回復とformal consumerを欠いたまま複数の受理集合変更を1 waveでlandしようとしているため。

### (b) blocker

- 所見1: 11層の成果会計が閉じない
- 所見2: 予算が減る現production pathがない
- 所見3: DW-G04の正のartifact/計測IDがない
- 所見4: DW-G01の最安生死実験が先行していない
- 所見6: linux-baremetal evidence再測定が未確定
- 所見8: reservation後の回復・terminal設計がない
- 所見11: 1 waveで安全に閉じない

### (c) 親briefで誤りと判定したN/P

- **N6: 誤り。** 7桁`CURRENT_PIN`を40桁manifest OIDとして使えず、preimage規則は未完成。
- **P2: 中核表現が誤り。** s8bの構造は参考にできるが、「新機構を発明しない」は成立しない。
- **P3: 誤り。** 単一候補×Rだけでは予算束縛もDW-G04証拠も実体化しない。
- **P6: 解消策として不完全。** 現artifactを拒否する裁定と「再測定可否は不明」は正しいが、clock hardcode修正だけではworkload・pin・artifact closure不一致が残る。

静的範囲では、N1〜N5およびN7〜N14そのものを誤りとする反証は得ていない。

### (d) そのまま採ってよい部分

- N6をfull captured Git OIDへ訂正すること。`s2-plan.md:78-93`
- 現s8a artifactをauthority evidenceとして拒否し、再測定可否を未確定と扱うこと。`s2-plan.md:186-225`
- public APIを`create=False`に保ち、lazy-createを禁止し、明示provisioningへ分離する原則。`s2-plan.md:231-313`
- authority readerとopaque recovery handleをrole projectionから隔離する境界。`s2-plan.md:362-403`
- 同一wire×Rがledger上合法でも、行数は物理queryの証明ではないという限定。`s2-plan.md:14-22`
- 8cをpilot専用宿主とし、certified selection・P3/P4/P7・H1/H2完了を名乗らない上限。`s2-plan.md:528-554`, `s2-plan.md:637-655`
- producer側sidecarにcross-referenceを置く方針。ただし名称はproof chainではなく「必要なcross-reference」に限定する。