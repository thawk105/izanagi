# [T-244] P6「構造化 anomaly からの禁止範囲再導出」契約案

## 位置づけと結論

本案は契約設計のみであり、実装・テスト実行・成果物書き込みは行っていない。

重要な結論は次の 4 点である。

1. P6 の成功は、「同じ anomaly class を再現した mask の明示集合」までなら定義できる。
2. 未実走 mask を含む座標 cut を認めるには、5-bit 全 32 mask の反実仮想 matrix を検査する必要がある。単一の atom-toggle 1 回では相互作用を排除できない。
3. draft v1 の候補値 `Qmax=2` では、この義務を満たせない。したがって現在許せるのは exact-mask cut のみである。
4. 現行 trigger-gating には固定 5-bit IR も実 campaign 由来 anomaly も無いため、現在 P6 を発火できる入力は 0 件である。fixture 由来 M2 は帰属が偽なので使用禁止である。

## 1. 契約の署名

型名は設計上の契約語彙であり、現行実装の存在を意味しない。

```text
derive_p6_cut(
    origin: RefluxOriginManifest,
    source: WalAbortRecordRef,
    axis: FiniteAxisContract,
    validation: PrecommittedValidationPlan,
    ordered_wal: OrderedWalView,
) -> P6Derived | P6NotDerived | P6NotApplicable | P6ContractError
```

### 1.1 入力

`WalAbortRecordRef` は WAL path だけでなく、`campaign_id / record_ordinal / variant /
payload_sha256` を持つ。内容ハッシュだけでは同内容 record の位置関係を復元できないため、ordinal を必須とする。

既存 field は次の名前で読む。裸の `anomalies` という変数名は禁止する。

| 契約上の名前 | 実 field path | 型・用途 |
|---|---|---|
| `verify_done_reported_witness_count` | `stage="verify_done"` の `payload.anomalies` | `int`。構造化 witness ではない |
| `abort_cycle_witnesses` | terminal `stage="abort"` の `payload.verify.anomalies` | `list[CycleAnomalyWitness]`。P6 が読む構造化 witness |
| `abort_reported_witness_count` | `payload.verify.anomaly_count` | `int`。上記 list の件数 |
| `abort_total_cycles` | `payload.verify.total_cycles` | `int`。切り詰め前の SCC 全数 |
| `abort_verdict` | `payload.verify.verdict` | `"non-serializable"` 必須 |
| `abort_integrity_clean` | `payload.verify.integrity.clean` | `true` 必須 |
| `workload_tag` | outer `payload.workload.tag` | companion `verify_done.payload.workload.tag` と一致必須 |
| `attempt_id` | abort の `payload.build_attempt_id` | source build attempt の束縛 |
| `candidate_source` | `build_start.payload.genome` / `src_token` | 現状は source identity であって mask ではない |

Python 内部の `EdgeReason.etype` は、WAL 直列化後には `reasons[].type` となる。契約は wire field の `type` を読む。

WAL の照合は `records_by_stage()` を使わず、順序付き record 列から行う。`verify_done` 自体には `build_attempt_id` が無いため、次をすべて満たす区間が一意でなければ `ambiguous-wal-binding` とする。

- 同一 `variant` の matching `build_start` と terminal `abort`。
- `abort.payload.build_attempt_id` がその `build_start` と一致。
- 両 record 間に、outer abort と同じ workload tag を持つ `verify_done` が一意。
- `verify_done_reported_witness_count == abort_reported_witness_count == len(abort_cycle_witnesses)`。
- `abort_total_cycles == abort_reported_witness_count`。切り詰められた witness から「同じ理由」を判定しない。
- outer `payload.reason == abort_verdict == "non-serializable"`。
- `certified=false`、`serializable=false`、`integrity.clean=true`。

型根拠は [model.py:61–88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/verifier/model.py:61)、直列化は [report.py:15–75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/verifier/report.py:15)、二義化の producer は [pipeline.py:778–807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/pipeline.py:778) にある。

### 1.2 現在欠けている入力

P6 は candidate mask と実行された source bytes を一意に束縛する `CandidateBinding` を必要とする。しかし現行 WAL の `genome` は trigger-gating の gate mask を表さず、proposal は自由な C++ 文字列である。

将来は draft v1 の `reflux-control` に少なくとも次を置く必要がある。

```text
stage = "reflux-control"
payload.event = "query-bound"
payload.origin_id
payload.candidate_schema_sha256
payload.candidate_key          # trigger-gating なら canonical 5-bit mask
payload.emitter_sha256
payload.variant
payload.build_attempt_id
payload.source_sha256
```

これは新規契約であり、現行の実 field ではない。これが無い artifact は `candidate-unbound` となり再導出不能である。proposal の C++ 文字列を後から解析して mask とみなしてはならない。

### 1.3 軸契約

`FiniteAxisContract` は次を持つ。

```text
axis_id
candidate_domain_sha256
ordered_candidates: tuple[CandidateKey, ...]
coordinates: tuple[Coordinate, ...]
intervene(candidate, coordinate, value) -> CandidateKey
emit(candidate) -> source bytes
```

trigger-gating の将来契約では、mask bit の順序を
`GATEABLE_REASONS = (lock-conflict, update-absent, readvali-tid,
readvali-locked, node-vali)` に固定し、`1 = その理由で backoff を行う` とする。

`emit()` と source bytes の一致を独立 golden で検証できない軸は P6 非適用である。

### 1.4 出力

enforcer が読む禁止範囲は、圧縮 predicate ではなく常に正準ソート済みの明示集合とする。

```text
P6Derived {
    origin_id,
    axis_id,
    witness_class_id,
    forbidden_candidate_keys,
    basis: "reproduced-set" |
           {"kind": "coordinate-halfspace", "coordinate": ..., "bad_value": ...},
    source_refs,
    validation_refs,
    validation_matrix_sha256,
    claim_scope: "fixed-origin-registered-replicates/v1",
}
```

`basis` は説明用であり、enforcer は `forbidden_candidate_keys` だけを使用する。predicate の実装差で集合が拡大する事故を避けるためである。

### 1.5 失敗様式

| 結果 | 意味 | generalized cut |
|---|---|---|
| `P6Derived` | 全証明義務を満たした | 明示集合だけ追加可 |
| `P6NotDerived(code)` | 発火対象だったが再導出実験が不成立 | 追加禁止 |
| `P6NotApplicable(code)` | exact-only policy、対象外 failure kind、有限 IR 不在など | 追加禁止。cap-lift の失敗には数えない |
| `P6ContractError(code)` | schema、WAL binding、origin proof、ledger topology が壊れている | 追加禁止。origin を seal |

`P6NotDerived` の reason code は少なくとも次を閉集合にする。

```text
budget-insufficient
replicate-policy-undefined
source-reproduction-failed
counterfactual-did-not-remove-class
interaction-found
witness-truncated
witness-invalid
candidate-unbound
ambiguous-wal-binding
strict-superset-not-derived
```

`not applicable` と `derived` の二値にしてはならない。二値にすると、未定義軸を「P6 成立」と扱う恒真化が再発する。

## 2. 「同じ理由で危険」の同値関係

### 2.1 witness の正規化

`w ≈ w'` は `normalize(w) == normalize(w')` と定義する。

正規化は次を行う。

1. `length == len(cycle) == len(edges) >= 2` を検査する。
2. `cycle` の txid が重複せず、各 `edges[j].from/to` が cycle の隣接関係と一致することを検査する。
3. 各 edge に 1 件以上の reason があり、`type ∈ {ww,wr,rw}` であることを検査する。
4. `edges[].types` が `reasons[].type` から導いた重複なし列と一致するかだけ検査し、fingerprint からは捨てる。
5. cycle の開始位置は意味を持たないため、全 rotation のうち辞書式最小表現を採る。辺方向は意味を持つため reverse は同一視しない。
6. 具体 txid は捨て、cycle 内の位置だけを残す。
7. key の hex 値は捨てるが、同一 key が複数 reason に現れるという同値分割は `k0,k1,...` として残す。
8. version の具体的な epoch/tid は捨てる。ただし次は残す。
   - genesis `(1,0)` か。
   - `u_ver` / `v_ver` の有無。
   - 同一 key 内での version の等値関係と順序。
9. reason の順序は意味を持たないため、各 edge 内で正準ソートする。重複件数は残す。
10. `phenomenon` は reason type から再導出した分類と一致するか検査し、正準表現にも含める。

### 2.2 捨てる根拠

- txid は実行ごとの grouping identity であり、機序ではない。
- key の具体値は workload 内の対象レコード identity であり、同一 origin が workload を別途束縛する。具体値を残すと同型 write-skew が別 class になる。
- version の絶対値は schedule identity を強く含む。一方、genesis・等値・順序は `ww/wr/rw` の成立構造に関与するため残す。
- `length`、`from/to`、`types` は cycle/reasons から再導出可能な冗長 field なので、検査には使うが class entropy には含めない。

### 2.3 同値類から mask 部分集合への写像

固定 origin、事前登録 replicate 集合 `R`、事前凍結した試験 mask 集合 `M` に対して、

```text
S_e(M, R) =
  { m ∈ M |
    R の全 replicate で、normalize(w) = e となる witness が 1 件以上出た }
```

とする。

- `reproduced-set cut` は `S_e(M,R)` をそのまま明示集合として返す。
- `|S_e(M,R)| <= 1` なら P6 は `strict-superset-not-derived`。source exact-mask を言い換えただけなので P6 成立と数えない。
- 試験していない mask は `S_e` に絶対に入れない。

座標 `i`、値 `b` の半空間

```text
H(i,b) = {m ∈ U | m[i] = b}
```

を座標 cut と名乗れるのは、`M=U` かつ

```text
S_e(U,R) = H(i,b)
```

が成立するときだけである。すなわち全 bad-side context で同じ class が再現し、全 paired good-side context でその class が消える必要がある。

部分的に試した context から `H(i,b)` 全体へ拡張してはならない。

## 3. 「独立に再導出」の意味と証明義務

次をすべて満たした場合だけ独立再導出と認める。

1. generator、critic、caller が提示した自然文の failure reason や cut 範囲を入力にしない。
2. trusted machine が WAL の構造化 witness から `witness_class_id` を再計算する。
3. axis adapter の candidate domain と intervention 関数は source failure より前に hash 固定されている。
4. validation mask、replicate ID、実行順、予算予約は最初の validation result より前に一括 commit される。
5. source attempt を validation 成功例として再利用せず、新しい attempt で source mask の class を再現する。
6. counterfactual は同一 origin の commit、workload、verifier policy、environment contract、IR schema、emitter、role bundle を維持し、candidate key だけを変える。
7. 各 validation run は通常 verifier を通り、WAL に独立した source ref を残す。
8. 欠測、timeout、build failure、trace integrity 不良は「class が消えた」と扱わず、matrix 不成立にする。
9. 座標 cut では全 32 mask を被覆し、どの残り 4 bit の context でも例外が無いことを確認する。
10. validation transcript と最終明示集合を別経路で再計算し、一致を検査する。

### P3 への評価

親の P3 の中核、「現行 witness から mask 座標を静的に一意導出できず、反実仮想実験が予算を消費する」は支持する。

`reasons[].type/key/u_ver/v_ver` はデータ依存辺を説明するが、trigger-gating の 5 abort reason のどの bit が原因かを表していない。sort-strategy の `permutation_violations` にも comparator 座標は含まれない。

ただし「atom を 1 回戻して同じ anomaly が消えた」だけでは座標 cut の証明にならない。他の 4 bit との相互作用を排除するには全 context が必要である。したがって P3 は必要条件として支持するが、親の例示する単発反実仮想は十分条件ではない。

静的 theorem/proof-carrying adapter で全 context を覆う代替は概念上あり得るが、proof language、trusted checker、C++ 意味論の範囲が未定義である。本設計では書けないため、static-proof mode は受理しない。

## 4. 健全性の主張と非主張

### 4.1 主張してよいこと

`P6Derived` のときだけ、次を主張できる。

- 明示された全 mask は、同一 origin の登録済み全 replicate で、同じ正規化 anomaly class を実際に再現した。
- `coordinate-halfspace` basis がある場合、有限 candidate universe の全 context で paired intervention matrix が条件を満たした。
- 禁止集合は generator の自然文理由でなく、trusted machine の witness 正規化と実験記録から再計算された。
- この origin の以後の探索で、その明示集合を build 前に拒否してよい。

### 4.2 主張してはならないこと

- mask が全環境・全 workload・全 schedule で常に危険である。
- coordinate が C++ 上の根本原因である。
- good-side で対象 class が出なかったことをもって、その mask が certified または安全である。
- anomaly class が出なかった未試験 mask が安全である。
- 禁止集合が完全である、最適 mask を残している、探索性能を改善する。
- finite replicate で anomaly が出なかったことを数学的な不存在証明と呼ぶ。
- P6 が verifier の代替になる。

規律 2 は次の条項で固定する。

> 禁止集合に含まれない候補も、各 candidate query ごとに通常の verifier を必ず通す。P6 proof、過去の good-side run、近傍 mask の certified 結果を理由に verifier を省略・短縮・緩和してはならない。

「certify できなかった」以上に言えるのは、「登録条件下で同じ構造 class が独立再現した」までである。

## 5. 予算と bit 会計

### 5.1 iteration/query/build

P6 validation も通常探索と同じ `reflux-origin` 予算を使い、無料の診断 run にしない。

- validation 1 run ごとに、実行前に `iteration +1`、`query +1` を原子的に予約する。
- planner/coder を呼ばない trusted-machine query でも iteration を消費する。直接呼出しによる予算迂回を作らないためである。
- malformed result、build failure、timeout、witness mismatch、duplicate、infrastructure failureも no-refund。
- source の元 run は既に消費済みなので二重計上しない。
- batch freeze 採用済み裁定に従い、全 validation candidate と replicate を結果取得前に予約し、未使用 slot は tombstone にする。
- `Kmax` は class 公開数であり validation query 数ではない。

座標 cut の最小規模は、5-bit universe では source 元 run に加えて全 32 mask の独立 validation を `R` replicate 行うため、

```text
追加 I = 32R
追加 Q = 32R
origin 全体 Q >= 1 + 32R
```

となる。`R>=1` でも `Qmax=2` と両立しない。

2 mask の `reproduced-set` でも、source の独立再現と別 mask の再現に最低 2 validation query が要るため、元 run を含め `Q>=3` である。

build の正確な上限は現在は書けない。現行 `evaluate()` は verifier 前に trace/perf の 2 build-resolution を行う一方、将来 P6 専用 runner が既存 trace binary を再利用するかは未定義だからである。次を origin manifest に追加しなければならない。

```text
Bmax
build_counting_mode
reuse_policy
```

`build_counting_mode` 確定までは `Bmax` 充足を主張できない。cache hit も build admission 呼出しとして記録し、fresh compile かを別 field で残す。

### 5.2 bit 会計への追加行

| 面 | generator への量 | caller / 公開面 | 契約 |
|---|---:|---:|---|
| P6 witness、class、validation matrix、cut | 0 bit | trusted machine 内部 | active window 中は projection 外 |
| 将来候補への P6 membership enforcement | 既存の 1 bit/query に含む | accepted/rejected | subtype や class を返さない |
| `derived/not-derived/non-applicable` status | 0 bit が目標 | 見せれば最大 2 bit + reason-code 分 | active window 中は非公開 |
| validation 件数・順序・停止位置 | 固定 batch なら 0 bit | 可変なら stop topology を漏らす | 事前 commit + tombstone |
| timing、artifact size、build cache hit | 上界未定義 | analog side channel | 本契約では閉じない残余 |
| seal 後の明示 mask 集合 | 5-bit universe で最大 32 bit | formal report | `Kmax` だけでは bit 上界にならない |
| seal 後の coordinate basis | kind 固定なら最大 `log2(10)≈3.322 bit` | formal report | 5 座標×2値 |
| witness class fingerprint | 上界未定義 | 公開する場合 | cycle/reason 長の上限または閉辞書が必要 |

したがって `Kmax=1` だけでは「最大 1 class = 小さい bit 数」とは言えない。fingerprint は active window 中に公開せず、seal 後の公開 schema と最大 witness サイズが決まるまで単一の有限 bit 上界は主張しない。

同一 UID の caller が control ledger の path、mtime、size を読める問題も本契約では解消しない。

## 6. 発火条件と非適用条件

### 6.1 発火条件

次をすべて満たす source failure だけが発火対象である。

- finite canonical IR に束縛された candidate。
- diff quarantine・構文 gate・auditor gate を通過済み。
- `abort.reason == verify.verdict == "non-serializable"`。
- clean integrity、非空かつ非切り詰めの cycle witness。
- real candidate binary、real trace、origin、attempt の帰属が成立。
- origin 内に事前登録済み validation plan と十分な未予約予算がある。
- axis adapter が candidate intervention を一意に実装する。

build error、trace timeout、empty trace、parse error、liveness、diff/auditor/syntax reject、role-invalid、infrastructure failure、`indeterminate` integrity failure、fixture 注入からは発火しない。

### 6.2 trigger-gating の評価

現在は非適用である。ただし理由は「anomaly への因果路が存在しない」ではない。

非適用理由は次の 3 点である。

1. 現行 proposal は canonical 5-bit IR でなく自由な 1 行 C++。
2. production 8c campaign に real structured anomaly が 0 件。
3. M2 は fixture trace を stock genome に結び付けた帰属偽の artifact。

さらに親 P1 の「遅延以外の因果路が構造的に無い」は現行受理集合について反証される。

- parser が強制するのは物理 1 行だけである（[p3_autonomous_workload_trial.py:324–347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/p3_autonomous_workload_trial.py:324)）。
- machine syntax gate は 5 識別子の blacklist だけである（[axis_trigger_gating.py:53–64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/axis_trigger_gating.py:53)、[p3_s4_loop_trigger_gating.py:114–124](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/p3_s4_loop_trigger_gating.py:114)）。
- diff quarantine 自身も C++ 意味 admission を保証しないと明記している（[diff_quarantine.py:14–22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/diff_quarantine.py:14)）。

例えば `status_` は blacklist に無いため、`izanagi_gate_pass = (status_ = TransactionStatus::inflight, true);`
という 1 行は少なくとも blacklist と領域検疫の拒否条件に当たらず、`abort()` の状態を直接変え得る。auditor が拒否する可能性はあるが、それは構造的不可能性ではない。

canonical emitter に閉じた将来でも、backoff 時間は thread interleaving を変えるため、observed anomaly への timing-mediated causal path まで不存在とは言えない。したがって将来 real anomaly が出た場合、trigger-gating を永久非適用にせず通常の P6 発火判定へ送る。

### 6.3 sort-strategy

現行 sort failure の代表である `permutation_violations` は `payload.verify.integrity.permutation_violations`
の整数であり、cycle anomaly list ではない。verdict は `indeterminate`、`anomalies=[]` になる
（[model.py:126–150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/verifier/model.py:126)）。

したがって本 `dsg-cycle/v1` witness 契約をそのまま適用できない。sort に適用するには、
欠落/複製要素、comparator 呼出し、前後 permutation を持つ構造化 integrity witness が別途必要である。
現行の整数と自然文 notes だけから「同じ理由」の同値関係を書くことはできない。

外側の `derive_p6_cut` protocol は軸非依存にできるが、witness-kind と axis adapter の意味契約まで単一化はできない。

### 6.4 D121 決定 (7) との整合

cap evaluator は次の三値規則を使う。

```text
installed generalized cut が無い:
    P6 = NA       # pass ではないが失敗数にも入れない
installed generalized cut がある:
    matching P6Derived proof がある -> PASS
    それ以外                         -> FAIL
```

`not applicable` を `PASS` と数えてはならない。過去に validation が失敗していても、generalized cut を導入せず exact-only のままなら cap-lift 判定上は `NA` とする。他の無条件前提条件は当然そのまま残る。

## 7. 検査可能度

| 条項 | 分類 | 現状 |
|---|---|---|
| `verify_done` 整数と abort witness list の型分離 | 機械検査できる | field は実在 |
| witness の内部整合・正規化・class hash | 定義後ならできる | 本節の canonical golden が必要 |
| ordered WAL の attempt/workload 照合 | 機械検査できる | `verify_done` の attempt ID 欠落時は位置で一意性検査 |
| origin proof と candidate mask の束縛 | 定義後ならできる | origin ledger / query-bound event が未実装 |
| fixed finite domain と emitter 全点一致 | 定義後ならできる | 5-bit IR が未実装 |
| source の real trace 帰属 | 定義後ならできる | 現行 M2 は明確に不合格 |
| validation batch の事前 commit、予約、tombstone | 定義後ならできる | 軸 (iii) 実装が未了 |
| 全 mask × replicate の matrix 完全性 | 定義後ならできる | `R` と runner contract が未決 |
| `S_e(U,R) == H(i,b)` | 機械検査できる | matrix が存在すれば純粋比較 |
| finite replicate から普遍的因果を主張すること | 人間 gate | 本契約では主張しない |
| `R`、`Bmax`、schedule/seed policy の妥当性 | 人間 gate | 値を恒真な既定値で埋めない |
| generator への 0 bit | 定義後ならできる | observable surface の閉集合が未定義 |
| formal report の source-ref 完全性 | 定義後ならできる | report schema 更新が必要 |
| exact-mask を削除・解除しないこと | 機械検査できる | 集合包含として検査可能 |
| trigger-gating に因果路が無いこと | 人間 gate / formal proof | 現行受理集合では反証済み |
| sort permutation failure の同値関係 | 書けない | 構造化 witness が存在しない |

恒真な条項は 0 件である。特に「generalized cut を使わなければ P6 成立」は採らず、`NA` とする。

## 8. exact-mask cut との関係

P6 は exact-mask no-good cut の上乗せであり、置換ではない。

source mask を `p`、既存禁止集合を `C_t`、P6 導出集合を `B` とすると、

```text
P6Derived:
    C_{t+1} = C_t ∪ {p} ∪ B

P6NotDerived / P6NotApplicable / P6ContractError:
    C_{t+1} = C_t ∪ {p}
```

ただし `{p}` 自体も draft v1 §3.2 の全帰属条件を満たす場合に限る。fixture M2 からは追加しない。

追加条項は次のとおり。

- P6 failure は既存 exact cut を削除、弱化、expiry、成功による解除に使えない。
- validation 中に別 mask が独立した qualifying red になった場合、その mask の exact cut は P6 全体の成否と独立に追加できる。
- P6 出力で候補を書き換えない。membership hit は build 前 reject とし query を消費する。
- P6 proof が破損・欠落した generalized 部分だけを不採用にし、exact 部分は維持する。
- 非禁止候補の verifier 必須条項は不変。

## 9. 本設計で実装しないもの

- `reflux-control` stage、event grammar、origin ledger。
- fixed 5-bit IR、candidate parser、canonical emitter、全 32 mask golden。
- witness normalizer、class hash、P6 validation runner。
- counterfactual batch freeze、replicate/schedule policy。
- `I/Q/B/K` の reservation/CAS/crash replay。
- generalized cut enforcer。
- generator/caller/critic の非干渉検査。
- Layer3 report の `control_events` / `reflux_constraints` 区画。
- cap-lift と P6 tri-state の機械結線。
- sort `permutation_violations` の構造化 witness。
- static semantic proof mode。
- `MAX_APPROVED_GENERATIONS = 1` の変更。
- trigger-gating の自由文字列受理集合縮小。
- critic ablation、`prior_reverse`、択一 1〜4 の実装。
- 性能・正しさ・効果の実測。

## 10. 将来実装が触る面の file:line 地図

### 10.1 producer・WAL・8c

| 面 | 実ファイル |
|---|---|
| anomaly 型 | [orchestrator/verifier/model.py:61–88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/verifier/model.py:61) |
| cycle reason 再構成・分類・witness 生成 | [orchestrator/verifier/dsg.py:200–274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/verifier/dsg.py:200) |
| verifier 集約 | [orchestrator/verifier/core.py:97–113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/verifier/core.py:97) |
| wire 直列化 | [orchestrator/verifier/report.py:15–75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/verifier/report.py:15) |
| `verify_done` count と abort witness の分岐 | [orchestrator/campaign/pipeline.py:732–807](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/pipeline.py:732) |
| WAL stage allowlist / record 型 | [orchestrator/campaign/model.py:20–32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/model.py:20)、[同:89–102](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/model.py:89) |
| WAL wire schema・append | [orchestrator/campaign/wal.py:190–256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/wal.py:190)、[同:301–390](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/wal.py:301) |
| ordered reader | [orchestrator/campaign/wal.py:529–581](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/wal.py:529) |
| attempt topology / replay | [orchestrator/campaign/wal.py:606–747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/wal.py:606) |
| last-wins なので P6 ledger に使用不可 | [orchestrator/campaign/wal.py:750–765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/wal.py:750) |
| 8c candidate parser | [orchestrator/campaign/p3_autonomous_workload_trial.py:324–347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/p3_autonomous_workload_trial.py:324) |
| 8c preview / syntax result | [同:560–578](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/p3_autonomous_workload_trial.py:560) |
| 8c generation・reject・critic 経路 | [同:1286–1515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/p3_autonomous_workload_trial.py:1286) |
| machine/auditor reject | [orchestrator/campaign/p3_s4_loop_trigger_gating.py:358–402](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/p3_s4_loop_trigger_gating.py:358) |
| build 後 outcome / last-wins record 射影 | [同:461–530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/p3_s4_loop_trigger_gating.py:461) |
| iteration・provenance・critic digest | [同:604–670](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/p3_s4_loop_trigger_gating.py:604) |
| red consumer | [orchestrator/critic/digest.py:232–264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/critic/digest.py:232) |
| whiteboard leak 面 | [orchestrator/campaign/p3_s4_loop.py:254–309](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/p3_s4_loop.py:254) |

### 10.2 trigger-gating 軸

| 面 | 実ファイル |
|---|---|
| 軸 identity・5 要因 universe・blacklist | [orchestrator/campaign/axis_trigger_gating.py:22–64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/axis_trigger_gating.py:22) |
| 現行機械列挙の subset→predicate | [orchestrator/campaign/s8a_trigger_sweep.py:215–248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/s8a_trigger_sweep.py:215) |
| EVOLVE-BLOCK 1 行と immutable consumer | [patches/silo-backoff-trigger-gating-variant.patch:75–111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/patches/silo-backoff-trigger-gating-variant.patch:75) |
| reason stores と reset | [同:117–196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/patches/silo-backoff-trigger-gating-variant.patch:117) |
| diff containment の保証範囲 | [orchestrator/campaign/diff_quarantine.py:3–29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/diff_quarantine.py:3) |

### 10.3 正式材料レポートと consumer 取り残し

| consumer | 取り残し・必要な契約 |
|---|---|
| Layer3 stage allowlist | [layer3_report.py:39–117](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/layer3_report.py:39) は未知 `reflux-control` を即 reject する |
| Layer3 variant 集約 | [同:205–229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/layer3_report.py:205) は全 record を variant 集約する |
| phantom reject | [同:438–467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/layer3_report.py:438) は `"reflux-origin"` を `commit-event-absent` candidate にする |
| source-ref bijection | [同:155–187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/layer3_report.py:155) は primary placement が variants/whiteboard のみ。`control_events` を一次配置へ追加しないと脱落する |
| report schema | [layer3_schema.json:5–21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/layer3_schema.json:5) は top-level 閉集合、[同:57](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/layer3_schema.json:57) は `mechanism_hypotheses` を空固定している |
| formal chain | [autonomous_trial_completeness.py:914–1081](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/autonomous_trial_completeness.py:914) は persisted Layer3 と fresh rebuild を deep compare する |
| artifact admission | [artifact_admission.py:497–589](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/artifact_admission.py:497) は attempt topology しか検証しない。新 stage を allowlist に足すだけでは control event grammar が無検査になる |
| WAL replay | [wal.py:730–747](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/wal.py:730) は control variant を phantom `EvalState` にする。candidate state と control state を分離する必要がある |
| critic | [critic/digest.py:232–264](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/critic/digest.py:232) は abort witness を読む。P6 control fields をこの経路へ混入させない非干渉検査が必要 |
| 8b pipeline truth table | [s8b_outcome_stage_contract.py:12–123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/s8b_outcome_stage_contract.py:12) は pipeline stage の閉集合。control stage を安易に追加せず、明示的に filter する |
| 8b stage ordering | [s8b_oracle_report.py:1183–1186](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/campaign/s8b_oracle_report.py:1183) は固定順序。control plane を pipeline 順序に混ぜない |
| qualification snapshot | [qualification/contract.py:151–160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/qualification/contract.py:151) は歴史的 5-stage topology を exact 固定している。P6 のために広げてはならない |
| verifier role schema | [codex_roles/policy.py:245–287](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/codex_roles/policy.py:245)、[review_ledger.py:227–237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t244-p6-contract/orchestrator/codex_roles/review_ledger.py:227) が既存 verifier field を固定。class ID は verifier payload に足さず control plane で派生させる方が安全 |

新 stage を `WAL_STAGES` に追加するだけでは、Layer3 hard failure、phantom candidate、control grammar の恒真化、ordered event の last-wins 消失が同時に起きる。以上が最低限の consumer 閉包である。

## 総括

**一文要約:** P6 は、clean な構造化 cycle witness を正規化し、同一 origin の事前凍結反実仮想 matrix で同じ class を独立再現した mask だけを明示集合として禁止する契約であり、座標 cut は全 32 mask を検査した場合に限って許し、それ以外は exact-mask を維持する。

| 親 provisional | 評価 | 根拠 |
|---|---|---|
| P1 | **反証** | 現行は自由な 1 行 C++ と 5 識別子 blacklist であり、`status_` 等への副作用を構造的に塞いでいない。canonical IR 後も timing-mediated path は残る |
| P2 | **反証** | 軸非依存の外側 protocol は有効だが、trigger の永久非適用は不成立。sort の `permutation_violations` は cycle witness と異なる整数で、同一意味署名では扱えない |
| P3 | **支持** | anomaly edge から mask 座標への静的一意写像は無い。ただし単発 toggle は不足し、座標 cut には全 context の実験が必要 |
| P4 | **支持** | repo 検索では draft v1 の byte pin consumer は見つからず、docs の一次資料参照だけだった。新規 dir に置き draft を保持する方針は一次資料の安定性に適う |

最も自信のない点は次の 3 つである。

1. 必要 replicate 数 `R` と schedule/seed 制御が未定義であり、有限実験の科学的強度を契約だけでは決められないこと。
2. origin ledger、candidate mask、build attempt を一意に束縛する wire schema が未実装で、特に `verify_done` に attempt ID が無いこと。
3. active window 中の artifact path・mtime・size・同一 UID 観測を含む bit 上界が未定義で、generator 0 bit を end-to-end に証明できないこと。