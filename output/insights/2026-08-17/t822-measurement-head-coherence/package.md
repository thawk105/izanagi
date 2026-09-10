# [T-822] 8c 正式受入の恒真保証 — 1 件を閉じ、2 件を裁定へ返す

- wave: `dev-wave-t822-tautology-guards`
- 実施日: 2026-08-17 (JST)
- 実装 commit: `06396d0c`
- 元裁定: 2026-08-11 /rulings「閉じる」(アーカイブ worklog 555 の [T-822] 項)
- 一次資料: `verbatim/` の段 3 敵対相談 2 本と段 6 敵対レビュー 2 本、`mutation/` の変異 spec と台帳

---

## 1. 閉じたもの — (iii) 6 report 間の `measurement_head` 一致検査

### 変更前の受理挙動

`assert_trial_registry_acceptance` は各 report の `measurement_head` を個別に検証していた
(full commit ID 形式、prereg 祖先性、その commit での manifest / registry blob 一致、registry prefix、
append-only history)。しかし **6 本が互いに同じ head を指すことは検査していなかった**。
`history_checked: set[str]` は履歴 walk の重複抑止であり、複数の head を許容する形である。
standalone receipt verifier も trial row の `measurement_head` を個別に形式検査するだけだった。

### 発生経路 (恒真でないことの根拠)

`load_launch_binding` は trial 起動ごとに現在 HEAD を解決し、その値が run-start と report へ写る。
HEAD 移動検査は単一 run の preflight 後だけである。したがって HEAD `H0` で 3 trial を起動し、
manifest と registry に触れない無関係 commit `H1` を作ってから残り 3 trial を起動すると、
両 head とも単独では正当で、変更前は受理された。

### 実装

| 層 | file | 拒否 |
|---|---|---|
| acceptance | `orchestrator/campaign/trial_registry.py` | 6 本が 1 種類でなければ `measurement-head-coherence` |
| standalone receipt | `orchestrator/campaign/s8c_acceptance_receipt.py` | trial row の相異なり数が 1 でなければ `receipt-measurement-head-coherence` |

**現在 HEAD との一致は要求しない。** 計測は main の進行より前でよく、要求すれば正当な束を過剰に
拒否する。この方向の防壁は `test_t822_acceptance_allows_coherent_past_measurement_head` が担い、
変異 M-3 がその検出力を実測している。

receipt の schema・key 集合・`MANDATORY_NON_CERTIFYING_REASONS`・`certifying=false` は不変。
差分は 97 行の純増で、既存テストの期待値は 1 件も変えていない。

### 変異による裏取り

probe (全件 SURVIVED 期待) で観測 node を集め、3 変異それぞれがちょうど 1 node を落とすことを
確認してから完全集合として再登録し、本走で **3/3 KILLED** を得た。

| ID | 変異 | 期待 node (完全集合) | 結果 |
|---|---|---|---|
| M-1 | acceptance の一致判定を除去 | `test_trial_registry.py::test_t822_acceptance_rejects_mixed_measurement_heads` | KILLED |
| M-2 | receipt の相異なり数要求を除去 | `test_s8c_acceptance_receipt.py::test_t822_tracked_receipt_rejects_mixed_measurement_heads` | KILLED |
| M-3 | 一致条件を「現在 HEAD と一致」へ過剰強化 | `test_trial_registry.py::test_t822_acceptance_allows_coherent_past_measurement_head` | KILLED |

M-3 が落とすのは新設の正例 1 本だけである。既存正例は過去 head を使っていないため、
過剰拒否方向の防壁は新設 node が単独で担っている。

---

## 2. 閉じられなかったもの — 裁定パッケージ

2026-08-11 の裁定「閉じる」は、次の 2 つの前提欠落を未見のまま下されている。裁定文にも
アーカイブ worklog 555 の [T-822] 項にも記録がない。**どちらも「今実装する」と恒真な assert か
偽の positive になるため、本タスク自身の要求 (恒真な保証を作らないこと) により実装を見送った。**

### 問 1 — (i) Layer-3 chain の必須化

`assert_campaign_layer3_chain` は cell の `workload` が producer の `WORKLOADS`
(`ycsb-a` / `ycsb-b` / `ycsb-c`) に含まれることを要求する。正式 holdout は `rr80` / `rr20` である。
したがって acceptance の必須経路へ入れると、**正式 6 report の受理集合が空になる**。

`WORKLOADS` へ 2 件足すだけでは済まない。正式 freeze (`output/s8b-freeze/holdout_freeze.json`) は
両 holdout を 1,000,000 records / 48 threads と定めるが、producer の campaign / perf / descriptor の
3 sink はいずれも 100,000 / 4 を固定している。名前だけ足せば **正式 scale で測ったと読める成果物**が
できる (規律 2 の面)。加えて originless compatibility の 2 node が「no-build report が正式 acceptance を
通る」を既存契約として pin しており、fixture 育成では両立しない。

- **(a) 前提タスク {{新規 T}} (正式 workload profile) を先に立て、その後で (i) を閉じる wave を起票する。**
  親の推奨。正式 scale の偽装を作らず、Layer-3 の保証本体 (WAL 再構築との一致) を落とさない。
- (b) (i) の scope を「chain の workload / campaign identity 検査を除いた部分だけ必須化」に縮める。
  → **非推奨。** 除く部分こそが persisted layer3 と producer 導出の一致を担う。閉じたと呼べない。
- (c) originless の no-build acceptance 契約を明示的に supersede し、no-build を正式受入から外す。
  → 受理集合を狭める方向だが、既存契約の反転であり単独のユーザー裁定が要る。

### 問 2 — (ii) 宣言 arm の実走認証

実走 arm を示す field が現行 artifact に 1 つも無い。manifest / registration /
`launch_admission.binding.arm` / receipt の arm はすべて同一宣言のコピーであり、`_campaign_for` も
`_prepare_campaign_identity` も proposal path も planner / coder / auditor / critic の invocation ID も
arm を受け取らない。`OriginProducerInputs.enforcement_arm` は caller が渡す非空文字列で、
formal consumer の実行検査がすべて終わった後に receipt へ記録されるだけで manifest arm と照合されない。

**すり抜け入力が構成できる**: 同一 holdout の `on` と `off` のラベルだけを manifest 内で交換し、
manifest hash・registry・launch admission・receipt の宣言コピーを再生成する。trial_id・campaign_id・
proposal・invocation・実行 descriptor は不変のまま通る。

さらに `off` の「凍結済み中立入力」は設計文書 (`docs/phase3-8b-descriptor-design.md`) に要求だけがあり、
canonical bytes も schema も実体が無い。

- **(a) 前提タスク {{新規 T}} (arm execution authority) を先に立てる。** 親の推奨。arm が選ぶ凍結入力から
  sealed execution digest を導出し、descriptor・campaign identity・proposal bytes/path・invocation
  namespace・run-start・terminal report の各 sink へ同じ digest を消費させる。
- (b) `report["executed_arm"] = binding.arm` を足して照合する。
  → **不採用。** 宣言値の往復であり定義上恒真。本タスクが明示的に禁じている。
- (c) receipt v2 を導入して `c02-arm-binding-unproven` を外す。
  → arm authority の完成後の話。v1 のまま arm 検査だけ足す形は、実装と receipt の主張が一致する
  (「非認証 receipt に対する arm mismatch 拒否」) ので矛盾しない。

### 問 3 — 証拠契約層 (C09) の実名不整合

`s8c_preregistration_evidence.py` の C09 述語は `trial_registry` に **`accept_trial` という名の関数**を
探すが、実名は `assert_trial_registry_acceptance` である。現状は `UNSATISFIED` を正直に返しており
偽緑ではないが、(i) を閉じても自動では追随しない。修正は contract JSON の bytes を変え、
凍結 hash・freeze generation・token-only fixture・snapshot へ波及する。

- **(a) (i) を閉じる wave に含める。** 親の推奨。gate と証拠契約を同時に動かすほうが整合する。
- (b) 単独の小 wave にする。→ contract bytes の凍結手順を 2 回踏むことになる。

---

## 3. 成果物影響

閉じた (iii) により、8c 正式受入 receipt は 6 trial が別 commit で測られた束を発行しなくなった。
`trials[*].measurement_head` は 1 種類であることが acceptance と standalone verifier の両方で保証される。

閉じられなかった (i)(ii) により、正式受入 receipt は依然として (a) 持続 layer3 レポートが WAL 再構築と
食い違っていても、(b) 宣言と違う arm で走った run でも受理する。**[T-822] は完了ではない。**
receipt は `certifying=false` かつ `c02-arm-binding-unproven` を必須理由として保持し続けるため、
対外主張の射程は正直なままである。
