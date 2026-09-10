## 0. 読んだもの

指定された資料はすべて参照できた。

- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-8c-wiring-design/brief.md:8-38,40-62,71-95` — 5 点の設計 scope、発行 3 条件、実測前提、(P1)〜(P6) を確認。
- 段 2 プラン: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t244-8c-wiring-design/s2-plan.md:38-210,212-340,341-417,493-517` — source closure、V-2、33 行 topology、capability、crash、発行条件の主張を確認。
- 前 wave 裁定: `output/insights/2026-08-06_t244-p3-8c-wiring/s4-adjudication.md:141-169` — V-1〜V-5 と再起票要件を確認。
- U-10: `output/insights/2026-08-06_t244-u10-budget-values/README.md:168-391` — 批准値、33 行偽 digest 経路、発行 3 条件、再計数義務を確認。
- ledger: `orchestrator/campaign/reflux_origin_ledger.py:315-365,485-493,682-726,1298-1638,1824-1892,3099-3216,3454-3485` — 行数下限、tombstone、candidate 下限、floor、replay、公開 API を確認。
- trial registry: `orchestrator/campaign/trial_registry.py:124-149,999-1112,1132-1357,1540-1644` — in-process seal、launch admission、`certifying=False` を確認。
- 親 probe も静的に確認した。`probe_premises.py:25-33,41-61`
- 現 authority は実際に `origins=[]`。`orchestrator/campaign/reflux_origin_authority_v2.json:1`

pytest、probe、物理実行はいずれも実走していない。

## 1. 所見

### 1. create-only は issuer 認証になっておらず、物理実行 0 件経路が残る

- 重大度: **blocker**
- 根拠: `s2-plan.md:115,128-145,199-200` は `issuer.kind` を表示用とし、権限根拠を専用書込経路へ委ねる一方、untrusted role が書けないことを「未確認」と認めている。現 execution receipt も hostname・boot ID・cpuset 等の自己 attestation である。`orchestrator/campaign/execution_guard.py:68-86`
- 具体経路: untrusted candidate または同一 UID の別 process が evidence root を書ける場合、deterministic path に偽の ordered WAL、provenance、result record を先に `O_EXCL` で作る。33 record を相互整合させれば、honest consumer は hash と terminal WAL を検査して受理する。`O_EXCL` は偽 record の上書きを防ぐだけで、最初の書き手を認証しない。生成 variant はそもそも非信頼入力である。`CLAUDE.md:88-95`
- 成果物影響: 物理 query 0 件のまま `OriginSealed` が certifiable となり、certified 選択の受理集合へ偽候補が入り、材料レポートは偽 path/hash を proof ref として公開する。

### 2. formal-consumer receipt が未定義で、存在検査だけの恒真 gate になりうる

- 重大度: **blocker**
- 根拠: `s2-plan.md:195,325` は「exact receipt 必須」とするが、receipt の schema、issuer seal、対象 state、terminal payload、one-shot 性を一切定義していない。formal consumer の入力も単数の `read_sealed_batch()` である。`s2-plan.md:178-195`
- 具体経路: 実装者が「receipt がある」「receipt digest が形式上正しい」だけを検査すると、別 origin・古い ledger state・別 terminal counter 用の receipt を再利用できる。consumer 実行後に batch を追加しても、receipt が current state commitment と exact `OriginSealed` payload に束縛されていなければ通る。
- 成果物影響: terminal の `batch_count`、tombstone、class 集合と consumer が検査した集合が分裂し、材料レポートの P6 receipt が試行台帳の最終 state を参照しなくなる。

### 3. 33 行成功後の全 tombstone batch で Bmin=2 を満たし、certifiable にできる

- 重大度: **blocker**
- 根拠: reserve は 2 行以上を要求する。`reflux_origin_ledger.py:1319-1338`。tombstone は終端 suffix なら合法。`同:1513-1516`。non-aborted seal の candidate 下限検査は `0 < sealed_distinct_candidate_count < minimum` なので、全 tombstone batch の 0 件を検査しない。`同:1618-1629`。プランは 33 行成功時 I/Q=1/33 としながら、批准値 4/68 を残しうる。`s2-plan.md:250-257`
- 具体経路:

  1. 33 non-tombstone 行の batch A を sealする。`sealed_queries=33`。
  2. 残予算で 2 行の batch B を reserve/commit し、両行を tombstone として sealする。
  3. `OriginSealed(aborted=False,batch_count=2,tombstone_count=1,sealed_queries=33,tombstoned_queries=2,...)` を送る。
  4. floor=33 は通り、batch B は sealed distinct=0 のため candidate 下限検査を素通りし、class 集合も変わらない。

  予約放棄後の成功でも Q=66 なので、残り 2 行で同じ経路が成立する。
- 成果物影響: 試行台帳は tombstone を含む certifiable terminal となる一方、材料レポートは検査対象 33 行だけを参照でき、ledger の batch/counter 集合と proof chain が不一致になる。

### 4. source と同じ mask の validation は現 producer では duplicate skip される

- 重大度: **blocker**
- 根拠: topology は source `w_s` と、`m=m_s` の validation で同じ wire を再度使う。`s2-plan.md:225-240`。一方、現 campaign は terminal variant と同一 identity を `done` で skip する。`orchestrator/campaign/loop.py:188-246`。プラン自身も duplicate skip は record 無し・tombstone と定める。`s2-plan.md:149-155`
- 具体経路: query 0 で `w_s` を実行後、mask sweep が `m_s` に達すると同一 variant と判定され、二度目の物理実行が行われない。そこから terminal tombstone suffix にすると `sealed_queries≤32` で floor 33 に届かない。既存 WAL を再利用して record を作れば、per-query 物理実行保証を破る。
- 成果物影響: 正しく fail-closed にすれば producer topology は常に aborted、既存証拠を再利用すれば `sealed_queries=33` を偽装して certified 選択を誤って広げる。

### 5. crash replay は authority 内の別 origin の interleave を扱えない

- 重大度: **must-fix**
- 根拠: envelope が保存するのは「最初の expected state commitment」だけ。`s2-plan.md:362-375`。回復時は前 event の `resulting_state_commitment` を次 event に使う。`同:396`。しかし ledger の state commitment は authority 内全 origin を含む global CAS である。`reflux_origin_ledger.py:2510-2542`。replayed receipt は historical `resulting_state_commitment` と現在の `current_state_commitment` を別々に返す。`同:3204-3211`
- 具体経路: O1 の event A が S0→S1、続いて O2 が event X を commitして S2、O1 の event B が S2 を base に commit後 receipt を失う。回復時に A を再送すると `resulting=S1,current≥S2` が返る。設計どおり S1 で B を再送すると、B の元 base S2 と違うため operation reuse mismatch になる。B が未 commitでも CAS mismatch になる。
- 成果物影響: O1 は `BATCH_RESERVED` / `BATCH_COMMITTED` に残り、I/Q だけ消費した非終端 origin となり、試行台帳の terminal ref と材料レポートが欠落する。

### 6. mask producer と mask 検査器が同じ canonicalizer を使う

- 重大度: **must-fix**
- 根拠: producer は `encode_wire(TriggerGateIR(mask))` を使い、record 検査も同じ式を使う。`s2-plan.md:120,216-230`。source closure の live conformance も現 `reflux_ir` / emitter を参照する。`同:61`。前 wave も同 canonicalizer の共動を既知限界としている。`docs/decisions.md:8969-8971`
- 具体経路: `encode_wire` または predicate emitter が誤って mask を重複・置換する変異を仮定すると、producer と consumer が同じ誤値を生成して全比較が緑になる。`candidate_min=1` も 32-mask 被覆を検査しない。
- 成果物影響: 実際には 32 mask を掃いていないのに P6Derived が発行され、材料レポートの validation matrix と certified 選択の cut が誤る。

### 7. (P1) の「series 内」保証は存在せず、cell の再利用範囲が consumer に伝播していない

- 重大度: **must-fix**
- 根拠: brief は閉包を「1 authority series 内」とする。`brief.md:73-75`。プランは正しく「同一 authority blob 内」へ縮小している。`s2-plan.md:68,495`。現 loader の重複拒否もその blob 内だけである。`reflux_origin_ledger.py:1836-1865`
- 具体経路: 同じ 4 referent のまま `authority_series_id`、budget、その他 manifest field を変えた新 authority blob を provisioning すると、同じ `cell_key` で別 `origin_id` を作れる。新 blob 内に一件しか無ければ重複検査を通り、budget root も新しくなる。
- 成果物影響: 材料 consumer が `cell_key` 単独で集約すると同じ cell を独立試行として二重計上し、試行台帳の予算と certified 選択の証拠数が水増しされる。

### 8. `certifying=False` launch と certifiable origin の意味境界が prose だけである

- 重大度: **must-fix**
- 根拠: capability 発行後も admission の `certifying` は False のままとする。`s2-plan.md:304-313`。同時に formal receipt があれば certifiable `OriginSealed` を許す。`同:325`。現 registry は False を強制し、ledger は non-aborted seal を `"certifiable"` にする。`trial_registry.py:1251-1265`、`reflux_origin_ledger.py:1618-1635`
- 具体経路: registered non-certifying launch が origin capability を受け、P6Derived 後に non-aborted sealする。下流 consumer が ledger の terminal status だけを見ると、launch admission の非認定性を無視して certified 選択へ昇格できる。
- 成果物影響: certified 選択の受理集合だけが拡大し、材料レポートは certifiable origin、試行台帳は non-certifying launch を指す分裂状態になる。

### 9. reserve 前の引き直し残余を、設計が「差し替えない」という prose で閉じたように見せている

- 重大度: **must-fix**
- 根拠: U-10 は予約前の candidate/provider failure が無課金で引き直せる残余を明記する。`README.md:360-363`。プランは candidate/hypothesis を選んだ後に run plan を書き、その後 reserve する。`s2-plan.md:234-240,362-375`。失敗時に「差し替えない」とするだけで、最初の provider call より前の ledger record はない。`同:380-383`
- 具体経路: controller が不都合な candidate/provider outcome を run plan 作成前に捨て、望ましい candidate が出た時点で唯一の create-only plan を作る。ledger と formal consumer には捨てた試行が見えない。
- 成果物影響: 試行台帳の attempt 数が過少になり、材料レポートは事前登録された source と誤認し、certified 選択の母集団が cherry-pick されたものへ変わる。

## 2. 段 2 プランに同意する点

- ledger の evidence digest が claim にすぎず、ledger 受理を物理実行証明と呼ばない判断は正しい。`s2-plan.md:85-93`
- result record に自己 digest を含めず、raw record bytes を外側から hash する形は自己 hash の恒真化を避けている。`同:124`
- accepted/rejected/tombstoned の対応は現 ledger の受理集合と一致する。`同:147-159`、`reflux_origin_ledger.py:682-726`
- P6 の事前一括 commit と一-open-batch FSM から、validation を複数 batch に割らず 33 行を一 batch にする結論には同意する。`s2-plan.md:212-257`
- source batch の 2 行目を tombstone padding にする案を明示的に却下した点は正しい。`同:266-272`
- capability 省略時の production fallback、fixture/production の交差、raw caller-selected origin を拒否する方向には同意する。`同:315-323`
- axis/verifier artifact、formal consumer、physical writer、capability client が未存在であり、発行 3 条件は現在 0/3 のままだと明記した点は正しい。`同:507-517`
- authority を空のまま保ち、設計 land を provisioning 許可としない名乗り上限にも同意する。

## 3. 親 brief への不同意

- **(P1): 不同意。** 「1 authority series 内」は実装に存在しない。段 2 の「同一 blob 内だけ」が正しい。ただし材料 consumer も `(authority_blob_sha256, origin_id, cell_key)` で scope しなければならない。
- **(P2): 不同意。** seal builder が create-only record を読むだけでは U-10 §7-1 を閉じない。issuer 認証と state-bound one-shot formal receipt が必要である。
- **(P3): 一部不同意。** 「4 batch 以下」は誤りで、一 batch 33 行が必要という段 2 の訂正は正しい。ただし同一 source wire の duplicate skip と、残予算で追加 batch を作れる点が未解決である。
- **(P4): 方向には同意、保証には不同意。** capability の field 束縛と fixture fallback 拒否は必要だが、private seal/prose だけでは trusted writer や formal receipt を保証しない。
- **(P5): 条件付き結論にも不同意。** 6 event で意味を表せる点には同意するが、現在の recovery recipe は global CAS の interleave を扱えず、byte-for-byte request を回収できない。
- **(P6): 同意。** 新規 docs 正本と insights の逐語保存は妥当で、pin 済み文書を触る必要はない。

実測値の一般化にも修正が要る。

- `probe_premises.py:32-33` の `batch_count=4` は実 batch 数の実測ではなく、最小行数から計算した上限である。
- `brief.md:51-55` の phase 列は happy path であり、abandon、複数 batch、他 origin の interleave を含む FSM 全体ではない。
- outcome 表は private validator の 8 例だが、同じ validator が seal から呼ばれるため、この局所的結論自体は現コードでも裏付けられる。
- codec bytes は feasibility estimator の合成 frame 値であり、本 topology を production 公開経路で流した実測値ではない。

## 総括

現プランのまま設計本文を確定するのは **NO-GO** である。

特に、V-2 は issuer 認証と formal receipt が未設計、producer topology は tombstone 追加 batch と duplicate skip が未解決、許可実行経路は non-certifying admission との consumer 境界が未設計である。したがって発行 3 条件はいずれも「設計済み」と数えてはならず、本番 authority の provisioning は引き続き禁止すべきである。

この docs-only wave と本静的レビュー自体は、certified 選択・材料レポート・試行台帳・authority の現在値を変更していない。