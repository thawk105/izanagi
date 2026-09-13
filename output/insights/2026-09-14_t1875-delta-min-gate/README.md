# [T-1875] delta_min 参照測定の前提ゲート実測 (2026-09-14)

wave: `worktree-dev-wave-t1875-delta-min-gate` / 背景 job。
測定対象 commit: `d9bbdb6b09f4f63e8484e5dae9b0359208b2c49a` (= 実測時点の local main)。

依頼は「delta_min の参照測定を投入し、欄を記入する。ただし D1326 の順序前提が満たされているかを
着手前に実測し、満たされていなければ測定せず不足を構造化して返す」。
**実測の結論は「前提は満たされていない」であり、参照測定は 1 件も投入していない。**

## 前提は 2 件ある

T-1875 の carry (archive worklog 1274) と D1640「記入の時期」が要求する前提は 2 件である。

1. **完了証明層の着地** (D1326)。
2. **§10.2 の検証 consumer の実在** — delta_min の型・有限性・符号・単位・向きを機械検証する
   consumer が production 経路に在ること。

依頼文は (1) だけを挙げているが、一次資料は 2 件を並べている。両方を測った。

## 前提 2 (検証 consumer) — 充足。実測。

`orchestrator/campaign/s8c_preregistration.py` の `_validate_iteration_contrast_parameters` が
production の parse 経路 `parse_preregistration_markdown` から到達する。
生きた `docs/phase3-8c-preregistration.md` の bytes を読み、§5 の当該セルだけを in-memory で
置換して parse した (**追跡ファイルは 1 byte も変更していない**)。

| 入力 | `section5_value_violations` |
|---|---|
| 現状 (未記入) | なし |
| 正例 (有限正の delta_min・n=5・単位と向きあり) | なし |
| `delta_min = -1.0` | `H1.delta_min` / `delta-min-range` |
| `delta_min = 0` | `H1.delta_min` / `delta-min-range` |
| `delta_min = "123.4"` (文字列) | `H1.delta_min` / `delta-min-type` |
| `unit = "  "` (空白のみ) | `H2.unit` / `unit-empty` |
| `direction = ""` | `H2.direction` / `direction-empty` |
| `n = 1` | `H1.n` / `n-range` |

負例 6 件がすべて別々の理由コードで発火し、正例は通る。**恒真な充足証明ではない。**

**この probe 自身が 1 度恒真になった。** 最初に結果 field を `section5_violations` と誤って綴り、
`getattr(contract, 'section5_violations', ())` の既定値により負例 6 件すべてが「違反なし」を返した。
正しい field は `section5_value_violations` である。負例が全件通ったら、機構でなく probe を先に疑う。

## 前提 1 (完了証明層の着地) — 未充足。実測。

`orchestrator.campaign.s8c_preregistration_evidence.evaluate_all` を上記 commit に対して実行した。

- `SATISFIABLE_CONDITION_IDS == frozenset({"C10"})`。
- 12 条件の内訳: **SATISFIED 1 (C10)** / UNSATISFIED 1 (C03) / EVIDENCE_UNDEFINED 10。

| 条件 | 状態 | 理由コード |
|---|---|---|
| C01 | EVIDENCE_UNDEFINED | `completion-proof-not-machine-checkable` |
| C02 | EVIDENCE_UNDEFINED | `completion-proof-not-machine-checkable` |
| C03 | UNSATISFIED | `manifest-registry-proof-undefined` |
| C04 | EVIDENCE_UNDEFINED | `completion-proof-not-machine-checkable` |
| C05 | EVIDENCE_UNDEFINED | `schedule-schema-absent` |
| C06 | EVIDENCE_UNDEFINED | `completion-proof-not-machine-checkable` |
| C07 | EVIDENCE_UNDEFINED | `completion-proof-not-machine-checkable` |
| C08 | EVIDENCE_UNDEFINED | `prereg-binding-proof-undefined` |
| C09 | EVIDENCE_UNDEFINED | `completion-proof-not-machine-checkable` |
| C10 | SATISFIED | `cross-binding-readiness-satisfied` |
| C11 | EVIDENCE_UNDEFINED | `completion-proof-not-machine-checkable` |
| C12 | EVIDENCE_UNDEFINED | `completion-proof-not-machine-checkable` |

C10 は D1363 (2026-09-01) が先例として開けた 1 件で、それ以降 `SATISFIABLE_CONDITION_IDS` は
増えていない。**層は 1/12 で、閉じていない。** 8c 事前登録は未発効のままである。

### 「着地」を緩く読んでも解除にはならない

「実装が着地」を「機構と先例 1 件が入った」と読むなら 2026-09-01 に成立している。
しかしその読みは後続の一次資料に否定される。

- **D1363 自身**が「発効は 12 条件すべての充足を要求するため、本決定の後も事前登録は未発効である。
  測定認可・certified 選択・proof chain・campaign 起動可否は 1 件も変わらない」と書いている。
- **D1640 (2026-09-05)** は C10 着地の 4 日後に書かれ、「本決定は値の規則を固定するだけで、
  記入と実装の着手は D1326 の順序 (完了証明層の後) を変えない」と明記している。
- **D1649 (2026-09-05) 項 3** が「順序規定は上流の完了証明層に従属し、D959 が入れ替えを名指しで
  禁じている」と再確認している。

D1326 を解除・読み替える裁定は `docs/decisions.md` 内に存在しない (D1326 への参照は
D1363・D1481・D1640・D1649 の 4 件で、いずれも維持側)。

## 参照測定の投入に足りないもの (構造化)

| # | 不足している前提 | 現在の実測値 | 誰が閉じるか |
|---|---|---|---|
| 1 | 完了証明層が閉じること (D1326) | 12 条件中 充足 1 (C10) | 上流の実装 wave。条件 id を `SATISFIABLE_CONDITION_IDS` へ足す手続きは D1364 の 4 点 |
| 2 | 対計画用 pilot が完全 block として成立 (§10.2 解除条件) | pilot 未実施 | T-1875 本体 (前提 1 の後) |
| 3 | schedule generator・manifest・反復束縛の固定 (同上) | §5 の `master_seed`・`6 cell manifest` はいずれも未記入 | §6 前提条件 5・2〜4 |
| 4 | §8 の再凍結とユーザー承認 (同上) | 未実施 | ユーザー手番 |
| 5 | H1/H2 の割り当ての食い違いの解消 (下記) | 未解消 | ユーザー裁定 |

前提 2 (検証 consumer) は充足済みなので、上表には挙げていない。

## 新事実 — D1640 の H1/H2 割り当てが凍結の権威と逆

**D1640 の逐語:** 「`delta_min = 0.03 × R_h` ... H1 = rr20、H2 = rr80 で別々に持つ。」

**凍結の権威 (`orchestrator/campaign/s8b_holdout_freeze.py` の `HOLDOUTS`):**
`rr80` の `candidate_id` が **H1**、`rr20` の `candidate_id` が **H2**。
`trial_registry.HOLDOUT_BINDINGS` もこれを引き継ぎ、H1 → rr80 / H2 → rr20 を返す。
どちらも 1,000,000 records / 48 threads で、D1640 が指定する凍結 `PerfConfig` と一致する。

この対応は `31426fb9a` (2026-08-29) から HEAD まで不変で、**D1640 起草時点 (2026-09-05) で既に逆**
だった。凍結側が後から変わったのではない (3 commit で逐語照合済み)。

**逐語適用したときに起きること。** H1 (実体は rr80) の delta_min が rr20 の session-median から、
H2 (実体は rr20) の delta_min が rr80 の session-median から作られる。2 つの holdout は
read 比率が 80% と 20% で throughput 水準が異なるため、一方の holdout の実質効果境界が
他方の水準で決まる。**片側は境界が過小になり、環境ばらつき程度の差を「成立」へ通しうる。**
これは受理集合を広げる向きであり、絶対規律 2 の面に触れる。

**この wave では直していない。** D1640 はユーザー裁定 (AI 委任) であり、事前登録の判定閾値の
束縛先を変える訂正である。ゲートが閉じている今、測定も記入も起きないため実害は発生していない。
訂正の形 (erratum か D の追補か、H1/H2 の label を正すか rr20/rr80 の側を正すか) を裁定待ちとして
carry に立てる。

## 既存 docs の陳腐化 1 件 (参考)

8c 事前登録 §6 前提条件 1 の本文は「現行の `WORKLOADS` は rr50 / rr95 / rr100 の 3 点だけで、
records と threads も `_campaign_for` / `_perf_for` / `_descriptor_for` に 100k / 4 で hard-code
されている」と書くが、現行コードと一致しない。
`orchestrator/campaign/p3_autonomous_workload_trial.py` には `FORMAL_WORKLOADS` があり、
`s8b_holdout_freeze.HOLDOUTS` から 1,000,000 records / 48 threads を導出している。
**本節の他の要求 (arm・非干渉性など) を測ったわけではないので、前提条件 1 が充足したとは言わない。**
本文の事実記述が古い、とだけ記録する。訂正は 8c 事前登録の改訂契約に従う別 wave の担当。

## 再現手順

```
PYTHONPATH=. python3 -c "
from pathlib import Path
from orchestrator.campaign import s8c_preregistration_evidence as ev
for r in ev.evaluate_all('d9bbdb6b09f4f63e8484e5dae9b0359208b2c49a', repo_root=Path('.').resolve()):
    print(r.id, r.status, r.reason_code)
"
```

検証 consumer の正例・負例は、上表の値で §5 の当該セルを in-memory 置換し
`s8c_preregistration.parse_preregistration_markdown` へ渡して `section5_value_violations` を見る。

## この wave が入れていないもの

- 参照測定 (stock silo の session-median) — **1 件も投入していない。**
- §5 の欄の記入 — **していない。** 欄は `未記入` のままである。
- gate・検査・台帳・一般化の新設 — 依頼の境界により行っていない。
- 実装面の変更 — 1 file も無い (本 wave は docs と insight だけ)。
