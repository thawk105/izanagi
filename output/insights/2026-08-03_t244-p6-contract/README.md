# [T-244] P6 契約 — 構造化 anomaly から禁止範囲を再導出する契約の設計 (2026-08-04)

- `authority: none`
- `default_effect: no-state-change`

(`output/README.md` の insights 規約。本ディレクトリは設計・相談の凍結スナップショットであり、
可変状態の正本ではない。可変状態の正本は worklog 末尾と現行 phase doc。)

## この文書の地位 (先に読むこと)

- **設計だけである。実装はゼロ**であり、本文が定義する機構はいずれも repo に存在しない。
- 本文は D121 が起草した還流設計 draft v1 (`output/insights/2026-08-01_t244-reflux-design/`) の
  **前提条件 P6 だけ**を扱う。draft v1 の本文は改変していない。
- 本文は「T-244 が解決した」とは主張しない。**T-244 本体は未解決のまま**である。
  本 wave が変えたのは「なぜ未解決なのかが構造的に判明した」という状態だけである。
- 成果物 (certified 選択、層 3 材料レポート、proof chain、試行台帳) の値・受理集合・参照は不変である。

## ファイル

| file | 内容 |
|---|---|
| `README.md` | 本文 (P6 契約の設計) |
| `brief.md` | 段 1 親 brief と前提実測 M1〜M8' |
| `s2-plan.md` | 段 2 codex プラン起草の逐語 |
| `s3-lensA.md` | 段 3 敵対レンズ A (正しさ境界) の逐語 |
| `s3-lensB.md` | 段 3 敵対レンズ B (実効性と成果物影響) の逐語 |
| `s4-adjudication.md` | 段 4 親裁定 (所見台帳、(P1)〜(P4)、裁定パッケージ) |

## erratum — 逐語 1 ファイルへの可逆最小正規化 (`DW-S07`)

`s3-lensB.md` の**行 3 のみ**が行末に半角空白 2 個 (Markdown の強制改行) を持ち、
`git diff --check` に抵触した。`DW-S07` に従い、**可視文字を変えない可逆最小正規化**として
その 2 byte だけを除去した。他の 2 逐語 (`s2-plan.md` / `s3-lensA.md`) は抵触 0 件で無改変である。

| 項目 | 値 |
|---|---|
| 原文 sha256 | `44291f6fae75bddc16310238596874e45fc1f1b1ca597f8efc54a99544c2e7b6` |
| 原文 byte 数 | 19,652 |
| 正規化後 sha256 | `1109ca6bf6da9a91f56769bc6cfb1eaec7d1fb9523f92ec5693c83ce26292c3e` |
| 正規化後 byte 数 | 19,650 |
| 変更 | 行 3 の末尾 U+0020 × 2 を除去。当該ファイル内で行末空白を持つ行はこの 1 行だけであった |
| 復元法 | `sed '3s/$/  /' s3-lensB.md` |

**復元法は実行で検証済み**である — 上記コマンドの出力が原文 sha256 を正確に再現することを確認した。
逐語の可視文字は 1 文字も変えていない。

`s2-plan.md` / `s3-lensA.md` の sha256 は
`c8ce4720c70846bf6c2c15512aa8896796be9cfe027946628a5d31da6406385a` /
`0177cbfbb33f7f4ca06b7c82563cfb1720cdb3c308cfce6cd737291742a9e4b3` であり、
codex の `-o` 最終メッセージから無改変である。

---

# 1. 問題 — 択一 7 が問うていたこと

D121 決定 (4-b) は自らこう書いた。

> exact-mask cut だけでは軸 (i) を満たさない。1 点の禁止は「既知 red の重複実行防止」であって、
> 構造化された anomaly を消費してもいなければ generator の提案分布も狭めていない。
> 軸 (i) を名乗るには、**構造化 anomaly から禁止範囲を独立に再導出する契約** (P6) が要る。

裁定パッケージの択一 7 は、これを次の形で返した。

> exact-mask (安全だが封じ込め相当) と座標 cut (軸 (i) を満たすが根拠が要る) の
> **中間**をどう設計するか。

ユーザー裁定 (worklog (126)) は「**P6 を先に設計する**」であった。本文はその設計である。

---

# 2. 中心定理 — 中間は存在しない

## 2.1 定理

P6 に「**実測した候補だけを禁止する**」という健全性要求を課す。すなわち導出集合 `B` の各元は、
validation で qualifying red を実際に観測した mask に限る。このとき:

> 赤を実測した各 mask は、**それ自体が exact-mask cut の 3 条件** (draft v1 §3.2) **を満たす**。
> よって `B` の各元は exact cut として独立に追加される。したがって
>
> ```
> C ∪ {p} ∪ B  =  C ∪ {p} ∪ (⋃_{m∈B} {m})
> ```
>
> であり、**`B` は受理集合に 1 点も足さない。**

座標 cut の場合も同じである。座標 cut を名乗る条件は `S_e(U,R) = H(i,b)` — すなわち
半空間 `H(i,b)` の 16 点**すべて**で同じ anomaly class を実測すること — なので、
主張が成立した時点で 16 点すべてが exact cut 済みである。

## 2.2 系

**P6 が受理集合を実際に狭めるには、少なくとも 1 つの「実測していない候補」を禁止しなければならない。**
それは測定からは導けない **帰納段** である。

したがって択一 7 の問いには次の形で答えが出る。

> **連続的な「中間」は存在しない。** 帰納段を踏むか踏まないかの二者択一である。
> 「根拠が要る」の正体は**帰納の正当化**であって、測定の量ではない。
> 測定を `32R` 回まで増やしても、帰納段を踏まない限り受理集合への効果はゼロのままである。

## 2.3 この定理の出所と強度

- 段 3 の 2 レンズが**独立に**到達した (レンズ A BLOCKER 2、レンズ B B1)。合議ではない。
- D121 決定 (4-b) の「安全側に振った結果、候補 A (現状維持 = 封じ込め) に**近い**強度しか持たない」は
  正しかったが、**受理集合に関しては「近い」ではなく「同一」**であった。ここを本文が訂正する。
- これが D106 残余 1 から 9 wave にわたって T-244 本体が解けなかった構造的理由である。
  設計が下手だったのではなく、**健全性と実効性が両立しない要求だった**。

---

# 3. 契約 — 明示的帰納契約として書く

§2 により、P6 を「健全な再導出」として書くことはできない。**明示的帰納契約**として書く。

## 3.1 署名

```text
derive_p6_cut(
    origin:      RefluxOriginManifest,
    source:      QualifyingFailureRef,
    axis:        FiniteAxisContract,
    hypothesis:  PrecommittedHypothesis,
    validation:  PrecommittedValidationPlan,
    enforcement: RefluxEnforcementArm,        # 択一 4 の on/off
    ordered_wal: OrderedWalView,
) -> P6Derived | P6NotDerived(code) | P6NotApplicable(code) | P6ContractError(code)
```

段 2 案からの差分は 2 点である。

- **`hypothesis` を必須入力に加えた** — 帰納段を隠さないための中核 (§3.4)。
- **`enforcement` を加えた** — 択一 4 の裁定 (reflux on/off は「機械が導いた制約を適用するか」で
  切る) を署名で表現できなかった段 2 案の欠落 (レンズ B B4) を閉じる。

**4 値の結果型を二値にしてはならない。** 二値にすると未定義軸を「P6 成立」と扱う恒真化が再発する。

## 3.2 入力 — 二義化の解消と、証拠の閉じた和

### 3.2.1 `anomalies` の二義化 (実測、`DW-O13`/D75)

同じ名前が stage によって型を変える。契約は裸の `anomalies` を禁止し、次の名前で読む。

| 契約上の名前 | 実 field path | 型 |
|---|---|---|
| `verify_done_reported_witness_count` | `stage="verify_done"` の `payload.anomalies` | `int` (構造化 witness ではない) |
| `abort_cycle_witnesses` | terminal `stage="abort"` の `payload.verify.anomalies` | `list` (P6 が読む構造化 witness) |
| `abort_reported_witness_count` | `payload.verify.anomaly_count` | `int` |
| `abort_total_cycles` | `payload.verify.total_cycles` | `int` (切り詰め前の SCC 全数) |

**構造化 witness は `verify_done` には無く `abort` にしかない。**
Python の `EdgeReason.etype` は wire 上では `reasons[].type` になる。契約は wire 名を読む。

`records_by_stage()` は stage 単位 last-wins なので**使ってはならない**。順序付き record 列から読む。
`verify_done` payload には `build_attempt_id` が**無い** (実測) ため、attempt 束縛は
`build_start` / `abort` の区間一意性で行い、一意でなければ `ambiguous-wal-binding` とする。

### 3.2.2 証拠は「candidate 起因の正しさ違反」の閉じた和とする

段 2 案は clean DSG cycle だけを入力にしていた。これは **variant 起因と正本が明記している 3 counter を
構造的に取りこぼす** (レンズ A BLOCKER 3、および親の独立発見)。
`orchestrator/verifier/model.py` は `lock_coverage_violations` (D38)、
`write_intent_violations` (T-152)、`permutation_violations` (D41) を
「trace-hook の問題ではなく **variant が引き起こした CC 正しさ違反**」と定義している。
実 artifact にも存在する (`s3_lock_coverage.json` の `1016002`、`s5_permutation_coverage.json` の `249252`)。

これらを除外すると、**optimizer は失敗を cycle channel から integrity channel へ移すだけで P6 を回避できる。**
よって入力を次の閉じた和とする。

```text
CandidateAttributableEvidence =
      CycleWitness      (verdict="non-serializable", integrity clean, 非切り詰め)
    ∪ IntegrityWitness  (lock_coverage / write_intent / permutation の candidate 起因 3 種)
```

- **未知の witness kind は fail-closed** とし、`P6ContractError` にする。
- `IntegrityWitness` の構造化表現は**現行に存在しない** (整数 counter と自然文 notes だけ)。
  したがって sort 軸への適用は、その新設を前提条件とする (裁定パッケージ U5)。
- 環境起因の失敗 (build error、trace timeout、empty/parse error、liveness、
  role-invalid、infrastructure、`competing-tenant`) からは**発火しない**。

## 3.3 同値関係 — 「同じ理由で危険」

`w ≈ w'` を `normalize(w) == normalize(w')` で定義する。正規化は cycle witness について:

1. 内部整合を検査する (`length == len(cycle) == len(edges) >= 2`、`edges[j].from/to` が
   cycle の隣接と一致、各 edge に 1 件以上の reason、`type ∈ {ww,wr,rw}`)。
2. cycle の開始位置は意味を持たないので全 rotation の辞書式最小を採る。**辺方向は同一視しない。**
3. 具体 txid は捨て、cycle 内の位置だけを残す。
4. key の hex 値は捨てるが、**同一 key が複数 reason に現れるという分割**は `k0,k1,...` として残す。
5. version の絶対値は捨てるが、genesis `(1,0)` か・`u_ver`/`v_ver` の有無・
   同一 key 内での等値関係と順序は残す。
6. 各 edge 内で reason を正準ソートする。重複件数は残す。
7. `phenomenon` を reason type から再導出して一致を検査し、正準表現に含める。
8. `edges[].types` は冗長なので検査にだけ使い、class entropy には含めない。

**追加の証明義務 (レンズ A MAJOR1 / レンズ B M4 を閉じる):**

- **key-renaming / version-shift 対称性**を、その workload について示すこと。
  示せなければ「別 record 上の偶然同型な G2」を同じ class と数えてしまう。示せなければ
  `P6NotDerived(symmetry-not-established)` とする。
- source abort が**複数 anomaly を持つ場合の決定規則**を置くこと。単数の `witness_class_id` に
  黙って 1 件を選んではならない。全件を処理する class-set 規則とする。
- 切り詰められた witness (`abort_total_cycles != abort_reported_witness_count`) からは
  「同じ理由」を判定しない (`witness-truncated`)。

**正規化は症状の分類であって機序の同定ではない。** 契約はこれを明示的に認める。

## 3.4 帰納段 — 本契約の中核

### 3.4.1 仮説の事前登録

`PrecommittedHypothesis` は **source failure を観測する前に** hash 固定される。最低限:

```text
hypothesis_id
class:              仮説クラス (例: "coordinate-monotonicity/v1")
statement:          反証可能な命題 (例: 「要因 i を gate しないことは、他 4 bit の値に
                    よらず同じ anomaly class を生む」)
extrapolation_set:  この仮説が成立したとき禁止する「未実測」候補の集合 (明示列挙)
falsification_test: 仮説を反証する paired test の事前登録 (実行順・replicate・seed を含む)
evidence_plan:      被覆する context 数と replicate 数 R
```

**`extrapolation_set` を空にできない。** 空なら §2 の定理により効果がゼロであり、それは
P6 の成立ではない (下記 3.4.2)。

### 3.4.2 成立条件 — 効果ゼロを「成立」と呼ばない

> **`P6Derived` を返してよいのは、`B \ C_exact ≠ ∅` のときだけである。**
> ここで `C_exact` は、同じ validation で観測した赤から exact cut として独立に追加される集合。

これが §2 の定理を契約として閉じる唯一の方法である。効果がゼロなら
`P6NotDerived(no-marginal-effect)` を返す。**「複数の exact cut を同じ class 名で束ねただけ」を
P6 成立と数えてはならない。**

### 3.4.3 反証されたら seal する

事前登録した `falsification_test` が仮説を反証したら、**その origin を seal する**。
仮説を差し替えて再試行してはならない (差し替えを許すと、赤を見てから仮説を選べてしまう)。

### 3.4.4 静的導出経路

レンズ B が示したとおり、precommitted な key-mask 軸のように
`reasons[].key / u_ver / v_ver` から座標が一意に定まる軸は原理的に構成できる。
契約はこれを second path として許す。ただし:

> **静的導出も §2 の定理を免れない。** 静的に導いた範囲が未実測候補を含むなら、
> それは軸契約という仮定の下での**帰納**であって証明ではない。
> よって静的経路も `PrecommittedHypothesis` を要求し、主張は同じく有界化する。

現行の trigger-gating 軸と sort 軸には、この静的写像は**存在しない** (3 者一致)。

## 3.5 出力

```text
P6Derived {
    origin_id, axis_id, hypothesis_id,
    witness_class_set,                # 単数にしない (3.3)
    forbidden_candidate_keys,         # 正準ソート済みの明示集合
    marginal_keys,                    # = B \ C_exact。空なら Derived を返せない (3.4.2)
    basis, source_refs, validation_refs, validation_matrix_sha256,
    enforcement_arm,                  # 択一 4
    claim_scope: "fixed-origin-registered-replicates/v1",
    generator_closure {               # レンズ B M6
        deriver_sha256, normalizer_sha256, runner_sha256, enforcer_sha256,
        axis_adapter_sha256, emitter_sha256, verifier_policy_sha256,
        environment_contract_sha256, role_bundle_sha256, registry_revision,
    },
}
```

`basis` は説明用であり、**enforcer は `forbidden_candidate_keys` だけを使う**
(predicate の実装差で集合が拡大する事故を避ける)。

`P6NotDerived` の reason code は閉集合とする:
`no-marginal-effect` / `budget-insufficient` / `hypothesis-falsified` /
`symmetry-not-established` / `source-reproduction-failed` /
`counterfactual-did-not-remove-class` / `interaction-found` / `witness-truncated` /
`witness-invalid` / `candidate-unbound` / `ambiguous-wal-binding` / `replicate-policy-undefined`。

## 3.6 健全性の主張と非主張

**主張してよいこと** (`P6Derived` のときだけ):

- 明示集合のうち**実測した** mask は、この origin の登録済み全 replicate で同じ正規化 class を再現した。
- **`marginal_keys` の禁止は、事前登録した仮説 `H` のもとでの帰納である。**
- 禁止集合は generator の自然文理由ではなく、trusted machine の witness 正規化と実験記録から
  再計算された。

**主張してはならないこと:**

- mask が全環境・全 workload・全 schedule で常に危険であること。
- coordinate が C++ 上の根本原因であること。
- good-side で class が出なかったことをもって、その mask が certified または安全であること。
- 有限 replicate で anomaly が出なかったことを、数学的な不存在証明と呼ぶこと。
- 禁止集合が完全であること、最適 mask を残していること、探索性能を改善すること。
- **`marginal_keys` について「証明した」と言うこと。** それは帰納である。
- P6 が verifier の代替になること。

**規律 2 の固定条項 (弱化不能):**

> 禁止集合に含まれない候補も、各 candidate query ごとに通常の verifier を必ず通す。
> P6 proof、過去の good-side run、近傍 mask の certified 結果を理由に、
> verifier を省略・短縮・緩和してはならない。

## 3.7 exact cut との関係 — 従属させない

```text
P6Derived:                                    C_{t+1} = C_t ∪ {p} ∪ B
P6NotDerived / NotApplicable / ContractError: C_{t+1} = C_t ∪ {p}
```

段 2 案は exact cut の追加を P6 の結果式の中にだけ置いていた。これは exact cut を
P6 の予算・発火可否・crash 復旧に従属させる (レンズ A BLOCKER 5)。よって:

- **qualifying red の直後に、exact cut `{p}` を P6 とは独立・先行して原子的に append する。**
  P6 の eligibility も予算も参照しない。
- P6 failure は既存 exact cut の削除・弱化・expiry・成功による解除に使えない。
- validation 中に別 mask が独立の qualifying red になったら、その exact cut は
  P6 全体の成否と独立に追加する。
- P6 proof が破損・欠落したら generalized 部分だけを不採用にし、exact 部分は維持する。
  ただし **install 後の proof 欠落は origin 全体を seal する** (下記 3.8)。
- P6 出力で候補を書き換えない。membership hit は build 前 reject とし query を消費する。

## 3.8 単調性と install

draft v1 §3.4 の単調性 (追加のみ、削除・弱化・expiry なし) は維持する。加えて
レンズ A MAJOR2 を閉じるため:

- generalized cut の install は **two-phase** とし、proof と cut を原子的に結ぶ。
- **install 前**の proof 欠落は cut を作らない。**install 後**の proof 欠落は
  受理集合の再拡大になるので、cut を外さず **origin 全体を seal** する。
- cut key に `origin_manifest / emitter / verifier_policy / environment_contract / IR schema` の
  hash を直接束縛する。いずれかが変われば **新 origin** とし、cut を持ち越さない。

## 3.9 規律 3 — 次の一手より前に消費する

規律 3 は「毎 iteration 回して、結果を次の一手のシグナルにする」ことを要求する。
段 2 案には source red → P6 → 次 query の順序が無く、後付け検査へ退化できた (レンズ A MAJOR4)。

> qualifying red を観測した時点で origin を **`P6_PENDING`** にし、**次の candidate admission を閉じる**。
> exact cut の append と P6 の terminal (`Derived` / `NotDerived` / `NotApplicable` / `ContractError`)
> が確定するまで、generator への query を許さない。

crash window (予約後 provider 前 / red 後 exact-append 前 / append 後 P6 terminal 前 /
terminal 後 seal 前) の正規回復状態を状態機械として定義する義務を契約に含める。
**本文はその状態機械を書いていない** — 未設計である (§5)。

## 3.10 予算と bit 会計

### 3.10.1 予算

P6 validation も通常探索と同じ `reflux-origin` 予算を使い、無料の診断 run にしない。
validation 1 run ごとに実行前に `iteration +1` / `query +1` を原子的に予約し、
malformed・build 失敗・timeout・mismatch・duplicate・infrastructure failure も **no-refund**。

座標 cut の下限は 5-bit universe で

```text
追加 I = 32R,  追加 Q = 32R,  origin 全体 Q >= 1 + 32R + E_min
```

(`E_min` = P6 後に探索を成立させる最小余白)。**draft v1 の候補値 `Qmax = 2` とは両立しない。**
値は択一 1 の裁定事項なので本文では決めない (裁定パッケージ U4)。
`Bmax` / `build_counting_mode` / `reuse_policy` は未定義であり、確定するまで build 上限の充足を主張しない。

### 3.10.2 bit 会計 — draft v1 §4② への追加行

| 面 | generator への量 | caller / 公開面 | 閉じ方 |
|---|---:|---|---|
| P6 witness / class / matrix / cut | 0 bit (目標) | trusted machine 内部 | active window 中は projection 外 |
| **P6 validation の通常 `abort` → critic digest** | — | **witness 全文 × 最大 `32R` run** | attempt に purpose tag を署名束縛し、探索 critic から閉集合 filter |
| **validation attempt → Layer3 `variants`/`rejects`** | — | **mask ID・順序・件数・verdict・停止 topology** | `validation_events` を一次配置し候補集計から分離 |
| 将来候補への membership enforcement | 既存の 1 bit/query に含む | `accepted`/`rejected` のみ | subtype も class も返さない |
| `derived/not-derived/non-applicable` status | 0 bit が目標 | 見せれば 2 bit + reason code | active window 中は非公開 |
| validation 件数・順序・停止位置 | 固定 batch なら 0 bit | 可変なら stop topology が漏れる | 事前 commit + tombstone |
| seal 後の明示 mask 集合 | — | 5-bit universe で最大 32 bit | `Kmax` だけでは bit 上界にならない |
| witness class fingerprint | — | **上界未定義** | 閉辞書か最大 witness サイズを決めるまで公開しない |
| timing / artifact path / mtime / size / cache hit | — | **上界未定義** | 本契約では閉じない受容残余 |

**レンズ A BLOCKER 6 / レンズ B B3 の核心:** P6 validation run を通常の verifier / WAL に載せる限り、
`critic/digest.py` が全 `abort.payload.verify` から witness を無差別に読み、
`layer3_report.py` が全 record を variant 集約する。**したがって「generator へ 0 bit」は
現行 consumer のままでは成立しない。** 非干渉検査を伴う分離が前提条件である。

## 3.11 発火条件と非適用

### 3.11.1 発火条件

- candidate が有限 canonical IR に束縛されている (`candidate_key` / `emitter_sha256` / `source_sha256`)。
- diff 検疫・構文 gate・auditor gate を通過している。
- 証拠が §3.2.2 の閉じた和に属し、切り詰められていない。
- real candidate binary・real trace であり、origin と attempt への帰属が成立する
  (**fixture 由来は不可**)。
- 事前登録済みの `PrecommittedHypothesis` と `PrecommittedValidationPlan` がある。
- 未予約の予算が `1 + 32R + E_min` を満たす (満たさなければ発火せず `budget-insufficient`)。
- axis adapter が candidate intervention を一意に実装し、`emit()` が独立 golden で検証済み。

### 3.11.2 非適用の二分 (レンズ A BLOCKER1 / レンズ B B2)

段 2 案は「generalized cut を導入しなければ `P6 = NA`」としていた。これは
**P6 を 1 行も実装せずに cap-lift を通せる**恒真化である。よって NA を二分する。

```text
P6 handler・全 witness-kind adapter・正負 calibration・未知 kind の fail-closed が未実装:
    -> NOT_IMPLEMENTED   (cap-lift 判定は FAIL)

上記が実装済みで、かつ generalized cut を主張していない (exact-only を選んだ):
    -> NOT_CLAIMED       (cap-lift 判定は NA。失敗に数えない)
```

D121 決定 (7) は「非適用を無条件必須にすると cap が永久解除不能になる」ことを懸念して
非適用を免責した。その懸念は `NOT_CLAIMED` だけを免責すれば回避できる。
**`NOT_IMPLEMENTED` の免責は決定 (7) の意図ではない** と本文は読むが、
これは記録済み決定の改訂にあたるので**裁定パッケージ U2 としてユーザーへ返す**。

### 3.11.3 軸ごとの現況

| 軸 | 現況 | 理由 |
|---|---|---|
| trigger-gating | **現時点で発火不能。ただし永久非適用ではない** | (a) proposal が canonical IR でなく自由 1 行 C++、(b) 実 campaign の構造化 anomaly が 0 件、(c) 唯一の witness は fixture 由来で帰属が偽。**「因果路が構造的に無いから」ではない** — 親の (P1) はその形で反証された |
| sort-strategy | **現時点で発火不能** | 代表的失敗 `permutation_violations` は整数 counter で `verdict=indeterminate` / `anomalies=[]`。構造化 integrity witness が存在しない (裁定パッケージ U5) |

**軸非依存にできるのは外側の dispatch envelope までである。** witness 契約と axis adapter の
意味契約は軸ごとに別に書く (親の (P2) の半分は反証された)。

## 3.12 検査可能度 (恒真な条項を作らない)

| 条項 | 分類 | 現状 |
|---|---|---|
| `verify_done` 整数と abort witness list の型分離 | 機械検査できる | field は実在 |
| ordered WAL の attempt / workload 照合 | 機械検査できる | `verify_done` に attempt ID が無いので区間一意性で行う |
| `B \ C_exact ≠ ∅` (効果の非ゼロ性) | **機械検査できる** | 純粋な集合演算。§3.4.2 の中核 |
| exact cut を削除・弱化しないこと | 機械検査できる | 集合包含で検査可能 |
| `S_e(U,R) == H(i,b)` | 機械検査できる | matrix があれば純粋比較 |
| witness の内部整合・正規化・class hash | 定義後ならできる | 正準 golden が要る |
| key-renaming / version-shift 対称性 | **定義後ならできる** | workload ごとの証明義務。未定義なら `symmetry-not-established` |
| origin proof と candidate mask の束縛 | 定義後ならできる | origin ledger / `query-bound` が未実装 |
| 有限 domain と emitter 全点一致 | 定義後ならできる | 5-bit IR が未実装 |
| validation batch の事前 commit・予約・tombstone | 定義後ならできる | 軸 (iii) 実装が未了 |
| generator への 0 bit | 定義後ならできる | **現行 consumer のままでは成立しない** (§3.10.2) |
| `NOT_IMPLEMENTED` と `NOT_CLAIMED` の区別 | 機械検査できる | 実装存在の検査に帰着する |
| `R` / `Bmax` / schedule / seed policy の妥当性 | **人間 gate** | 恒真な既定値で埋めない |
| 有限 replicate から普遍的因果を主張しないこと | **人間 gate** | 本契約は主張しない |
| sort の integrity witness 同値関係 | **現時点では書けない** | 構造化 witness が存在しない |

**恒真な条項は置かない。** とくに「generalized cut を使わなければ P6 成立」は採らない (§3.11.2)。

---

# 4. 将来の実装が触る面 (consumer 取り残しの地図)

新 stage を `model.WAL_STAGES` に足すだけでは足りない。以下は親が独立に実測したものを含む。

| consumer | 取り残し |
|---|---|
| `orchestrator/campaign/layer3_report.py` | 自前の閉じた `STAGES` を持ち、**未知 stage を例外で拒否**する (親が実測)。`model.WAL_STAGES` とは別集合 |
| 同上 (variant 集約) | 全 WAL record を `variant` で集約し、`commit` の無い variant を `commit-event-absent` の reject として数える (親が実測)。control plane の固定 variant が**実在しない棄却候補**として材料レポートに混入する |
| 同上 (source_refs) | 一次配置が variants / whiteboard のみ。`control_events` / `validation_events` を一次配置に足さないと bijection から脱落する |
| `orchestrator/campaign/wal.py` の `records_by_stage()` | stage 単位 last-wins。順序付き event ledger の読取に使えない |
| 同 WAL replay | control variant を phantom `EvalState` にする。candidate state と control state の分離が要る |
| `orchestrator/critic/digest.py` | 全 `abort.payload.verify` から anomaly / integrity / stats を無差別に読み、自然文へ展開する。P6 validation の witness がここから漏れる |
| `orchestrator/campaign/autonomous_trial_completeness.py` | 閉じた event grammar と 4 role 列を要求し、persisted Layer3 と fresh rebuild を deep compare する |
| `orchestrator/campaign/artifact_admission.py` | attempt topology しか検証しない。stage allowlist を広げるだけでは control event grammar が無検査になる |
| `orchestrator/campaign/s8b_outcome_stage_contract.py` / `s8b_oracle_report.py` | pipeline stage の閉集合と固定順序。control plane を pipeline 順序に混ぜない |
| `orchestrator/qualification/contract.py` | 歴史的 5-stage topology を exact 固定。P6 のために広げてはならない |
| `orchestrator/codex_roles/review_ledger.py` | role ごとの入出力 field 集合を**独立 pin** している (親が実測)。class ID を verifier payload に足さず control plane で派生させる方が安全 |

---

# 5. 本設計で実装しないもの / 書けなかったもの

**実装しないもの** (本 wave はコード・テスト・設定を 1 行も変更していない):

`reflux-control` stage と event grammar、origin ledger、固定 5-bit IR、candidate parser、
正準 emitter と全 32 mask golden、witness normalizer、class hash、P6 validation runner、
counterfactual batch freeze、replicate / schedule policy、`I/Q/B/K` の予約・CAS・crash replay、
generalized cut enforcer、非干渉検査、Layer3 の `control_events` / `validation_events` 区画、
cap-lift と P6 状態の機械結線、sort の構造化 integrity witness、
`MAX_APPROVED_GENERATIONS = 1` の変更、trigger-gating の受理集合縮小、
択一 1〜4 の実装、性能・正しさ・効果の実測。

**書けなかったもの (正直に書く):**

- **crash window の正規回復状態機械** (§3.9)。義務として契約に含めたが、状態機械自体は書いていない。
- **`R` (replicate 数) と schedule / seed policy**。有限実験の科学的強度を契約だけでは決められない。
- **generator への 0 bit の end-to-end 証明**。artifact path / mtime / size / cache hit /
  同一 UID 観測を含む observable surface の閉集合が未定義。
- **sort 軸の同値関係**。構造化 integrity witness が存在しないため書けない。
- **`Bmax` と build 計数規則**。`evaluate()` が verifier 前に 2 build-resolution を行う一方、
  P6 専用 runner が既存 trace binary を再利用するかが未定義。

---

# 6. T-244 本体の状態

**未解決である。** 本文は P6 契約を設計したが、実装はゼロであり、規律 3 の還流は実現していない。

本 wave が変えたのは次の 1 点だけである。

> **なぜ未解決なのかが構造的に判明した。** 設計が下手だったのではなく、
> 「実測したものだけを禁止する」健全性と「受理集合を狭める」実効性が**両立しない要求**だった。
> 前へ進むには帰納段を踏むというユーザー裁定が要る (裁定パッケージ U3)。
> 踏まない選択も正当だが、その場合 T-244 は「還流は実現しない」と結論して閉じるべきであり、
> 未解決のまま残すべきではない。
