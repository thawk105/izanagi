# [T-1806] 事前登録契約 C10 の証拠 field 拡張 — 逐語と限界

wave: dev-wave-t1806-prereg-c10-fieldpaths
実装 commit: 9feff6b07 / fix commit: 3bd9b5d3a
base local main: cb4a11b6e
一次資料: docs/decisions.md の D967 (ユーザー裁定)

---

## 1. 親が実測した原典事実

### 1.1 契約と実装の差は 1 件だけだった

契約 C10 の `cross_binding_verifier.field_paths` は 12 件、実装の
`S8C_CROSS_BINDING_FIELDS` は 13 件。差は `proposal_build_source_bindings` の 1 件で、
T-1749 (commit 1e10a081) が足した arm から source への因果束縛の証拠である。
T-1749 の insight README §3 の 4 番が「契約の記述が実装より弱いままである」と明記して
裁定へ返した当のものである。

### 1.2 契約 JSON は判定器に読まれていない

`_evaluate_c10` (`orchestrator/campaign/s8c_preregistration_evidence.py`) が照合するのは
Python 定数 `_C10_FIELDS` であって契約 JSON ではない。**したがって契約だけを広げても
正式 gate の検知集合は 1 件も増えない。** D967 が理由に挙げた「後から実装を弱めても正式 gate が
検知できない」を実際に解消するには、判定器側も広げる必要がある。

### 1.3 D967 の前提は後発裁定で成立しなくなっていた

D967 は既存 campaign が `E1-stale` になることを想定するが、**その翌日のユーザー裁定 D1163
(絶対規律 7 の新設) が `recorded-current-closure-mismatch` の拒否経路を名指しで撤去していた。**

| 検査 | 実測 |
|---|---|
| `artifact_admission._require_verifier_epoch_for_purpose` の現行実装 | 現在の閉包が取得可能かだけを見る。コメントに `D1163 keeps only the availability prerequisite here.` |
| tracked `campaign.lock` | 32 件 |
| うち `contract_loader_blob_sha256s` を持つもの | **0 件** |
| 本件で newly stale になる campaign | **0 件** |

親は段 1 brief でこれを見落とし、段 3 の敵対レンズが独立に反証した。実装前に是正したため実害なし。
D967 の 3 行動はすべて実行し、記録だけを事実へ合わせた。

### 1.4 凍結 g12 は規範文書を変えずに閉じた

`prepare_revision` CLI で発行した。g11 との差は 7 field だけで、
`section6_condition_hashes` は 12 件とも不変だった。

| 変わった | 変わらなかった |
|---|---|
| `decider_version` (v6 → v7) | `normative_body_sha256` |
| `evidence_contract_sha256` | `section5_field_names_sha256` |
| `generation_number` (11 → 12) | `section6_conditions_sha256` |
| `protected_sha256` | `section6_condition_hashes` (12 件すべて) |
| `supersedes_sha256` | `schema_version` / `normalization_version` / `source_path` |
| `revision_reason` / `ruling_reference` | |

`spurious-revision` guard を通過したこと自体が、契約が実際に変わったことの機械的証拠である。

---

## 2. この実装が証明すること・しないこと

| 辺 | 種別 | 内容 |
|---|---|---|
| 契約 field path ↔ 判定器の期待集合 | 完全一致 | 単一対応表から両側を導出し `frozenset(...) == 期待集合` で照合する |
| 判定器の期待集合 → verifier の文字列 | 部分集合 | `_C10_FIELDS <= _strings(verify)`。**関数 AST に literal が在るかだけ**を見る |
| field の値束縛 | **証明しない** | 到達しない枝に literal を残して照合だけ恒真化する弱体化は本 gate を通る |

**閉じていないこと:**

1. **値束縛。** C10 は値の生成・再読・照合を証明しない。producer 側の functional test の責務である。
   §3 の変異でこの境界を機械化した。
2. **g12 と v7 の実 repository 検証。** これを行う 5 node
   (`test_s8c_preregistration_invariant.py` の candidate-fixture 群) は 2026-08-29 の T-1434
   ユーザー裁定で growth hold にかかっており、解除条件は明示のユーザー指示のみ。
   **既存の hold であって本 wave が作った状態ではなく、迂回もしていない。**
   g12/v7 の正しさは §1.4 の実測と、親および段 3 レンズ B の独立再計算に支えられている。
3. **`_cross_binding_source_bindings` の path 正準性検査に負の対照が無い。** §3 の erratum を参照。

---

## 3. 変異 matrix — 同じ変異が層によって結果を変える

最終巡は 2 本に分けた。runner を分けた理由は単一理由性の回復である。

| 走 | runner の範囲 | 変異 | 期待 | 実測 |
|---|---|---|---|---|
| A | C10 の述語 node | `M01-UNCOND` 対応表から 1 組削除 | KILLED (5 node) | **KILLED** |
| A | 同上 | `M04` 完全一致を片方向の包含へ戻す | KILLED (2 node) | **KILLED** |
| A | 同上 | `M01-COND-E2` literal を残し E2 digest 等式だけ恒真化 | SURVIVED | **SURVIVED** |
| B | producer の functional test | `M01-COND-E2` (同じ変異) | KILLED (2 node) | **KILLED** |

baseline はいずれも PASSED、MISMATCH 0、期待 node は全件完全一致。`repo_head=3bd9b5d3a`。

走 B が落とした 2 node の 1 つは
`test_verify_s8c_cross_binding_rejects_each_reference_mutation[proposal_build_source_bindings]`
で、今回追加した field そのものの参照変異テストである。**同一の変異が C10 では生存し
producer では死ぬ**ことで、pin の射程が機械で確定した。

`M04` が KILLED になったことは、段 3 の 2 レンズと段 6 の 2 レビューが独立に出した must-fix
(片方向の包含では契約側の余剰 field を許す) の修正に、実際の検出力があることの直接の証拠である。

### 登録しなかった変異 (冗長 gate)

契約 JSON 自体を変える 2 変異 (field を削る / 14 件目を足す) は、凍結 contract hash pin が
先に赤にする過剰決定である。単独変異の証拠から外した。この経路の検出力は、実 file を触らない
新設テストの param 側で担保している。

### erratum — 親が変異設計で 2 回間違えた (初回結果は消さない)

1. **過剰決定。** 初回 probe で `M01-UNCOND` と `M04` が 55〜60 node を落とした。
   `s8c_preregistration_evidence.py` が契約 loader 閉包の中にあるため、変異すると
   `capture_contract_loader_binding()` が壊れ campaign chain 系まで連鎖する。
   runner を絞って回復した。台帳は `mutation-ledger-probe.json`。
2. **条件版の照合点が無検査だった。** 最初に選んだ
   `expected_path != path or proposal_sha256 in source_artifacts` を恒真化しても、
   `test_autonomous_trial_completeness.py` 全体で **0 node しか落ちなかった**
   (`mutation-ledger-probe.json`)。実際に検査されている E2 digest 等式へ再照準した
   (`mutation-ledger-probe-b.json`)。**この照合点に負の対照が無いことは実測された事実**であり、
   等価変異か真の無検査かの切り分けを別タスクへ起票した。

---

## 4. 実測した検査

計算ノードへ dispatch した焦点走。login node は pytest が hook で拒否され、
user cgroup も headroom ゼロだった。

| 対象 | 結果 |
|---|---|
| `test_s8c_preregistration_predicates.py -k c10` | 5 passed (4.06s) |
| `test_s8c_preregistration_core.py` + `_invariant.py` | 403 passed, 5 skipped (24.60s) |
| `test_autonomous_trial_completeness.py -k cross_binding` | 18 passed (10.29s) |
| `test_acceptance_schedule_order.py` + `test_real_repo_serialization.py` | 135 passed, 1 skipped (50.45s) |

5 skipped の内訳は §2 の限界 2 を参照。

---

## 5. 子の工数と実行環境

plan / consult 2 / author / review 2 / fix の 7 子はすべて `gpt-5.6-sol`、effort は xhigh。

**実装子と fix 子はいずれも pytest を実走できず、「実装済み・未実走」と正直に申告した。**
codex sandbox 内で `qstat -Q` が uid 認証に失敗して rc=16、local も cgroup headroom ゼロだった。
**同じ `qstat -Q` は親からは rc=0 で通る。** 子の sandbox 固有の制約であってクラスタ側の
不調ではない。実テストはすべて親が dispatch して走らせた。

---

## 5.5 並行 wave との統合

同じ条件 10 を扱う別 wave と同一 file を別方向から書き換えた。land 前に相手の差分を読み、
**merge して赤を見る前に相互破断を 3 件、静的に特定した。**
一晩で観測された 6 軸を、発火する走の種類つきで
`parallel-wave-static-check-axes.md` へ残した。**静的検査の限界は検査の質ではなく
軸の列挙にある**という総括も同文書にある。

## 6. 逐語

- `verbatim/s1-brief.md` — 段 1 brief (provisional 裁定 P1〜P4)
- `verbatim/plan.md` — 段 2 プラン
- `verbatim/lensA.md` / `verbatim/lensB.md` — 段 3 敵対相談
- `verbatim/s4-adjudication.md` — 段 4 裁定
- `verbatim/impl.md` — 段 5 実装子の報告
- `verbatim/revA.md` / `verbatim/revB.md` — 段 6 敵対レビュー
- `verbatim/fix.md` — 段 6 fix の報告
- `mutation-spec-final-a.json` / `mutation-spec-final-b.json` — 本走 spec
- `mutation-ledger-final-a.json` / `mutation-ledger-final-b.json` — 本走台帳
- `mutation-ledger-probe.json` / `-probe-b.json` / `-probe-c.json` — probe 巡 (erratum の一次資料)
