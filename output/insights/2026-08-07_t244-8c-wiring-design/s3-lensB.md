## 0. 読んだもの

- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-8c-wiring-design/brief.md:6-38,40-62,71-102`。docs-only の 5 点設計、本番 authority 不変、(P1)〜(P6)、段 5・6 対象外を確認した。
- 段 2 設計: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-8c-wiring-design/s2-plan.md:21-526`。source closure、result evidence、one-batch 33-row topology、capability、crash/replay を確認した。
- 前 wave 裁定: `output/insights/2026-08-06_t244-p3-8c-wiring/s4-adjudication.md:141-169`。V-1〜V-5 と、再起票時の必須要件 8 項目を確認した。
- U-10: `output/insights/2026-08-06_t244-u10-budget-values/README.md:168-391`。`imax=4 / qmax=68 / kmax=1 / Bmin=2 / candidate_min=1 / F=33 / R=1`、物理実行 0 件でも ledger 単体では certifiable になりうる残余、topology 後の再計数・再批准義務を確認した。
- ledger: `orchestrator/campaign/reflux_origin_ledger.py:1298-1638,1965-2011,2510-2542,2604-2878,2917-2985,3099-3216,3392-3485`。FSM、global CAS、global `operation_id`、`_same_committed_request` の exact 比較、production 固定 API、fixture-only 初期化を実読した。
- trial registry: `orchestrator/campaign/trial_registry.py:124-149,1071-1357,1532-1688,2080-2138`。in-process seal、launch record、lifecycle token、acceptance 側の exact record 再導出を確認した。
- 8c caller: `orchestrator/campaign/p3_autonomous_workload_trial.py:1321-1597,1600-1913,1941-2231`。`run_trial → _finish_trial → _run_workload → drive()`、workload 例外の partial report 化、1 generation 1 drive を確認した。
- downstream: `orchestrator/campaign/autonomous_trial_completeness.py:63-70,379-432` と `orchestrator/campaign/layer3_report.py:1-24,91-120`。completeness の exact launch-admission keys と、材料レポートが現在 WAL/whiteboard だけを読むことを確認した。
- HEAD は `c9990bc27eb6d14374ff53df857091a1393f4d26`。authority は 71 bytes、SHA-256 は brief 記載どおり、runtime directory は不在だった。静的検査のみで、pytest・probe・物理実行・編集・commit は行っていない。

## 1. 所見

### 1. 33 evidence row と 33 物理 attempt の双射がない

- 重大度: **blocker**
- 根拠: 設計は record に `build_attempt_id / ordered_wal_ref / execution_provenance_ref` を持たせるが、これらの一意性・WAL 区間の非重複・WAL 内 trigger binding と record の `mask/wire/commitment` の一致を formal consumer の必須条件にしていない。`s2-plan.md:113-124,182-191` の「member ごとに exact 1 record」は member→record の全域性だけで、record→物理 attempt の単射ではない。ledger 自身は digest を dereference しない。`reflux_origin_ledger.py:205-209`
- 具体経路: qualifying rejection を 1 回、accepted を 1 回だけ物理実行し、その 2 本の WAL/provenance/build-attempt を 33 個の record から使い回す。`ledger_member` と claimed `trigger_binding` だけを query 0〜32、mask 0〜31 に変えれば record digest は33通りになる。設計本文どおりの最小 consumer は terminal WAL と outcome を各 record で確認できるが、同じ attempt の再利用と claimed wire≠WAL wire を拒否する義務がないため、2 実行を 33 行へ水増しできる。
- 成果物影響: `sealed_queries=33` と 32-mask matrix が物理実行 2 件から生成され、偽の `P6Derived` が certifiable 選択・材料レポート・試行台帳の受理集合へ入る。

### 2. formal-consumer receipt は schema も発行権限もなく、seal gate になっていない

- 重大度: **blocker**
- 根拠: raw `commit_event` 迂回を塞ぐ必要性は認識しているが、定義は「formal consumer の exact receipt」だけである。`s2-plan.md:180-195,325`。receipt の exact keys、canonical bytes、issuer seal、fresh re-derivation、入力 state commitment、consumer/generator closure、`enforcement_arm`、P6 出力との束縛がない。P6 正本は `enforcement` と generator closure を要求する。`output/insights/2026-08-03_t244-p6-contract/README.md:118-127,254-270`
- 具体経路: capability を持つ正規 caller が、形式だけ整えた 33 行と任意の mapping/digest を「formal receipt」として `OriginSealed(aborted=False)` に添える。client は正規 consumer が発行した値か、どの ledger/evidence/P6 出力に対する値かを判別できない。逆に in-process object identity だけを採れば、通常の process crash 後に再取得不能になる。
- 成果物影響: plain receipt を受ければ物理 0 件の certifiable origin が増え、厳格に拒否すれば certifiable origin は永久に 0 件のままになる。

### 3. 「許可された実行経路」に production bootstrap と public fixture 正例がない

- 重大度: **blocker**
- 根拠: production API は `_production_store()` 固定だが、`_locked(..., create=False)` を使う。`reflux_origin_ledger.py:1965-2011,3454-3485`。runtime 初期化 `_initialize_locked()` は production を明示拒否し、呼べるのは private fixture helper だけである。`同:2917-2985`。設計は capability client の規則だけを置き、bootstrap、client 型、`run_trial` からの forwarding を定義していない。`s2-plan.md:315-323`
- 具体経路:
  1. 人間が authority entry を provision し、launch gate が production capability を発行する。
  2. 最初の `read_origin`/reserve が production lock/head を開く。
  3. runtime が未初期化なので失敗する。安全に初期化する public operation は存在しない。
  
  fixture 側も、現 `run_trial`・`_finish_trial`・`_run_workload` に ledger client 引数がない。厳格実装なら public 正例は拒否され、raw APIを残せば省略時に `_production_store()` へ落ちる。
- 成果物影響: 安全側では試行台帳に origin row が一件も作られず report は partial、弱い補修では fixture caller が production の I/Q を不可逆に消費する。

### 4. crash recovery は restart-safe でなく、global CAS の連鎖も誤っている

- 重大度: **blocker**
- 根拠:
  - envelope が保存するのは capability の digest だけで、capability 自体の durable 再発行契約がない。`s2-plan.md:362-375`
  - 設計自身が Python seal は同一 process 限定と認める。`同:327-331`
  - trial lifecycle も exact in-memory token を要求し、同じ trial の再 start は拒否する。`trial_registry.py:1532-1615,1622-1644`
  - state commitment は全 origin と global runtime head を含む。`reflux_origin_ledger.py:2510-2542`
  - 設計は replay の `resulting_state_commitment` を次 event の expected state にすると書く。`s2-plan.md:396`。receipt は historic `resulting` と現在の `current` を別々に返す。`reflux_origin_ledger.py:3204-3212`
  - `operation_id` は origin 単位でなく authority 全体で一意である。`同:2656-2694`
- 具体経路: origin A の reserve が base `C0` で commit した後に receipt を失い、origin B が event を commitして current が `C2` になる。A の exact resend は `replayed=True / resulting=C1 / current=C2` を返す。設計どおり次の BatchCommitted に `C1` を使うと `state commitment CAS mismatch` で拒否される。さらに process crash なら origin capability と lifecycle token の双方を失い、別 process は ledger terminal と trial terminal のどちらも発行できない。
- 成果物影響: origin は `BATCH_RESERVED/BATCH_COMMITTED/RESULTS_PREPARED`、trial registry は start-only のまま残り、report・材料レポート・ledger の参照が永久に分裂する。

到達状態の被覆は次のとおりである。

| 状態 | 設計の被覆 |
|---|---|
| `IDLE`（reserve 前） | 扱った |
| `BATCH_RESERVED` | abandon と receipt replay は扱ったが、global CAS interleave 後の次操作を誤る |
| `BATCH_COMMITTED` | missing record→tombstone は扱ったが、row 0 開始前 crash と public caller への回復主体が未定義 |
| `RESULTS_PREPARED` | BatchSealed の receipt 喪失は扱うが、seal 呼出し前 crash、capability 再取得、create-only file の exact-existing retry が未定義 |
| `IDLE`（batch seal 後） | consumer 再実行を主張するが、consumer receipt と lifecycle recovery がない |
| `ORIGIN_SEALED` | exact resend の形だけは扱った |

違法な FSM 遷移を直接提案してはいない。しかし failure 表は「不明」を endpoints に分解せず、回復主体・durable capability・global CAS を省いているため、全状態被覆にはなっていない。

### 5. `origin_binding` 追加は originless 既定 bytes と downstream exact gate を壊す

- 重大度: **must-fix**
- 根拠: 設計は `TrialLaunchAdmission` の serialized record に `origin_binding` を追加するとする。`s2-plan.md:304-313`。現 record は exact 7 keys で、completeness も同じ exact set を要求する。`trial_registry.py:1295-1321`、`autonomous_trial_completeness.py:63-70,379-425`。registry acceptance も独立に旧 record を再構成する。`trial_registry.py:2080-2138`
- 具体経路: authority が空の通常 `run_trial` でも record に `origin_binding:null` を足す実装なら、run-start、report、`launch_admission_sha256`、lifecycle start row の bytes が変わる。consumer を更新しなければ completeness/acceptance が拒否する。optional unknown field を許す補修なら exact schema の受理集合が広がる。
- 成果物影響: originless 試行台帳の hash・参照が変わるか、全 report が completeness 前後で拒否され、既定経路の現在値不変が失われる。

### 6. topology は parser 上は成立するが、producer と post-commit crash 余裕は成立していない

- 重大度: **must-fix**
- 根拠: one batch 33 rows は `s2-plan.md:223-257`。現 8c は generation ごとに `drive()` を一回だけ呼び、一つの outcome しか要求しない。`p3_autonomous_workload_trial.py:1693-1913`。設計自身も現在の実行経路では未成立と認める。`s2-plan.md:248,259-264`
- 検算:
  - `Qmax >= F`: `68 >= 33` — 成立。
  - `ceil(F/2248)=ceil(33/2248)=1`
  - `min(Imax, Qmax // max(Bmin,candidate_min)) = min(4,68//2)=4`
  - よって `1 <= 4` — 成立。
  - 成功時 `I/Q=1/33`、pre-commit abandon 1 回＋retry は `2/66`。
  - 行数 33≥2、相異 candidate 32≥1、R=1、exact class が1種なら Kmax=1。
- 具体経路: current `drive()` を一回だけ使えば non-tombstone は最大1行で残り32行が tombstoneとなり、`sealed_queries<33`。一回の結果を32 maskへ複写すれば所見1の偽実行になる。また commit 後に任意の1行が record 作成前に落ちると non-tombstone は最大32で floorを割る。設計は post-commit retry を禁止するため、Qmaxに35の差があっても certifiable recoveryには使えない。
- 成果物影響: 安全実装ではすべて aborted となり certified 選択は増えず、誤実装では一つの drive が32回の物理 queryとして材料レポートへ水増しされる。

したがって `4/68` は数値上受理されるが、保証できる異常余裕は「33-row reserve の pre-commit abandon 1 回」だけである。post-commit crash 1 回を生き残る批准値ではない。U-10 の内訳変更とこの liveness 低下を明示して再批准する必要がある。

### 7. 前 wave の必須要件と downstream 層を親 brief が scope 外へ落としている

- 重大度: **must-fix**
- 根拠: 前 wave は再起票時に 8 項目を「必須」とした。`s4-adjudication.md:151-169`。一方、親 brief は設計対象を5点に限定し、変異 matrix も対象外とした。`brief.md:6-17,37`。plan も public failure、default bytes、mutation prereg、completeness、材料 report consumer を設計していない。
- 具体経路: ledger/harness だけ実装し、private helper の低層正例だけを通す。public `run_trial` は origin を渡さないか partial reportへ変換し、completeness は新 field を拒否、layer3 renderer は ledger/result evidence を読まない。それでも「V-2 + topology + 許可経路を設計済み」と名乗れてしまう。
- 成果物影響: ledger row と trial/report/material report の間に proof-chain edge がないまま、実装済みと見なす受理集合だけが広がる。

層別には次の状態である。

| 層 | 設計の到達 |
|---|---|
| ledger | capability化・FSMを扱うが、production bootstrapとformal receiptが不足 |
| trusted harness | issuer位置は扱うが、33 attempt producer APIとattempt双射が不足 |
| trial registry | admission拡張は扱うが、lifecycle recovery・acceptance再導出が不足 |
| terminal report | 同一 record projectionを述べるだけでschema/version/error projectionが不足 |
| completeness | 未着手。現 exact-key gateは新 recordを拒否 |
| formal P6 consumer | 概念のみ。receipt schema・issuer・generator closureが不足 |
| 材料レポート consumer | 未着手。現 renderer は WAL/whiteboard のみ |
| certified 選択 | scope 外で現在値不変。閉じたと名乗ってはならない |

## 2. 前 wave §7 要件 8 項目の対応表

| # | 必須要件 | 判定 | 根拠 |
|---:|---|---|---|
| 1 | `run_trial` から実 fixture client までの公開正例 | **不足** | fixture 規則はあるが、public signature・forwarding・client型・bootstrapがない。`s2-plan.md:315-323` |
| 2 | fixture binding で production default resolution を拒否 | **扱った** | fixture capability＋client省略、scope不一致を明示拒否。`同:317-323` |
| 3 | launch admission 発行 capability | **扱った** | 発行主体と capability fields を設計。`同:288-315`。ただし durable seal/reissue は所見4の不足 |
| 4 | `_finish_trial` 追加引数は originless default | **未** | `_finish_trial` への引数有無・default・active scope経由の選択を規定していない |
| 5 | 既定経路 bytes 不変を literal SHA 以外で守る | **未** | `origin_binding` 追加時の omission/version規則も、非揮発 field集合による比較もない |
| 6 | private sentinel・module rebinding等の保証限界 | **扱った** | 同一 process改変は保証外、fixture fallbackは保証外にしないと明記。`同:327-331` |
| 7 | 変異事前登録の再構成 | **未** | brief が変異 matrixを対象外化。設計本文にも後続実装用の正例・単一理由変異がない。`brief.md:37` |
| 8 | ledger failure の公開経路での扱い | **未** | failure表は ledger controller内だけ。`_finish_trial` の partial report変換とlifecycle terminalを扱っていない |

## 3. 親 brief への不同意

### `(P1)`〜`(P6)`

| 裁定 | 判定 |
|---|---|
| **P1** | 方針には同意するが、「1 authority series 内」は過大。現 loader が保証するのは一つの authority blob 内だけで、plan 自身の `s2-plan.md:68,495` の訂正が正しい。 |
| **P2** | 不同意。builder が create-only recordを読むだけでは足りず、さらに現 plan の formal consumerにも attempt双射とsealed receiptが欠ける。 |
| **P3** | 不同意。one-batch 33-row なら Bmin は満たすが、「自然に満たされる」だけで物理 producerは生まれない。V-3の不整合は探索側だけでなく、33 outcomeを一 drive内で生成する harness側にも残る。 |
| **P4** | 方向には同意するが、閉じたとは認めない。production bootstrap、public fixture forwarding、durable capability、report/completeness consumerがない。 |
| **P5** | 「新 event不要」は条件付きで妥当。ただし recovery envelopeだけでは不足し、global CAS、capability/lifecycle再取得、formal receipt、public partial-report順序が必要。 |
| **P6** | 同意。pin済み文書を避け、新規 docs を正本にする配置は妥当。 |

### 段 1 実測値の過大な一般化

- `brief.md:43` の `batch_count=4` は `_check_budget_codec_feasibility` が最大容量計算に用いる値で、実 producer topology の batch 数ではない。one-batch 33-row の証拠にはならない。`reflux_origin_ledger.py:2284-2383`
- `brief.md:54-55` の冪等性説明は不完全である。`operation_id` は originごとでなく global、CASも全 originを含む global state commitment に対する。`reflux_origin_ledger.py:2510-2542,2656-2694,3099-3216`
- `brief.md:58-60` の「sealed launch admission」は同一 process 内の object identity gateであり、durable recovery capabilityではない。`trial_registry.py:138-149,1251-1259`
- `brief.md:61-62` の32 mask正準集合は emitterの有限集合を示すだけで、32物理attempt producer、WAL双射、report consumerを示さない。
- outcome matrix、Bmin=2、FSMの合法遷移、public APIの `_production_store()` 固定は静的コードと一致した。これら自体への不同意はない。

## 総括

**判定は NO-GO。blocker 4 件、must-fix 3 件。**

最も危険なのは、物理 attempt の使い回しを拒否する双射がなく、formal-consumer receiptも発行済み capabilityになっていない点である。このまま設計どおりに実装すると、少数の物理実行から33行を作って certifiable 集合を広げられる。

一方、厳格側でも production runtime bootstrap、public fixture forwarding、restart-safe capability/lifecycleがないため、正規経路は発火または回復できない。数値 tuple は parser上成立するが、post-commit crash後の floor回復余裕はない。

現 HEAD の certified 選択・材料レポート・試行台帳は、今回のread-only監査では一切変更されていない。