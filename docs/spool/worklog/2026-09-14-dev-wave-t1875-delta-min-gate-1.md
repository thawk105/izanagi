---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-t1875-delta-min-gate
seq: 1
title: [T-1875] delta_min 参照測定の前提を実測し、層が 1/12 で閉じていないため測定せず止めた (docs のみ、branch worktree-dev-wave-t1875-delta-min-gate)
---

## 本文

- 依頼は「参照測定を投入して欄を記入する。ただし D1326 の順序前提を着手前に実測し、
  満たされていなければ測定せず不足を構造化して返す」。**実測の結論は未充足で、参照測定は
  1 件も投入していない。§5 の欄も `未記入` のままである。**
- **前提は 2 件あった。** 依頼文は完了証明層 (D1326) だけを挙げるが、T-1875 の carry と
  D1640「記入の時期」は §10.2 の検証 consumer の実在も並べている。両方を測った。
- **検証 consumer は充足していた (実測)。** `_validate_iteration_contrast_parameters` が
  production の parse 経路から到達し、正例は通り負例 6 件 (負値・ゼロ・文字列・単位空白・
  向き空・n=1) がすべて別々の理由コードで発火する。恒真ではない。2026-08-18 の wave の
  成果がそのまま生きていた。carry の「consumer の実在待ち」は現物と合っていない。
- **完了証明層は閉じていない (実測)。** commit `d9bbdb6b0` で評価器を回すと 12 条件中
  充足 1 (C10) / 不充足 1 (C03) / 証拠未定義 10。`SATISFIABLE_CONDITION_IDS` は D1363
  (2026-09-01) 以降 `{"C10"}` のまま増えていない。
- **「機構が入ったから着地」という緩い読みは一次資料に否定される。** D1363 自身が
  「本決定の後も未発効、測定認可は 1 件も変わらない」と書き、D1640 (C10 着地の 4 日後) が
  「記入と実装の着手は D1326 の順序を変えない」と明記し、D1649 項 3 が「順序規定は上流の
  完了証明層に従属し、D959 が入れ替えを名指しで禁じている」と再確認している。
  D1326 を解除する裁定は台帳に存在しない。
- **新事実 — D1640 の H1/H2 割り当てが凍結の権威と逆。** D1640 逐語は「H1 = rr20、H2 = rr80」。
  凍結側 (`s8b_holdout_freeze.HOLDOUTS`、および `trial_registry.HOLDOUT_BINDINGS`) は
  rr80 が H1・rr20 が H2 で、`31426fb9a` (2026-08-29) から HEAD まで不変。**D1640 起草時点で
  既に逆**であり、凍結が後から変わったのではない。逐語適用すると各 holdout の実質効果境界が
  他方の throughput 水準から作られ、片側は境界が過小になって環境ばらつき程度の差を
  「成立」へ通しうる。受理集合を広げる向きなので規律 2 の面に触れる。**この wave では
  直していない** — 事前登録の判定閾値の束縛先を変える訂正であり、裁定待ちとして起票した。
  失敗の型は {{F:ruling-identifier-not-checked-against-freeze}}。
- **probe が 1 度恒真になった。** 結果 field を `section5_violations` と誤って綴り、
  `getattr` の既定値で負例 6 件が全部「違反なし」を返した。正しくは
  `section5_value_violations`。負例が全件通ったら機構でなく probe を先に疑う。
  この取り違えに気づかなければ「consumer は発火しない」という逆の結論を報告していた。
- 参考: 8c 事前登録 §6 前提条件 1 の本文「現行 `WORKLOADS` は rr50/rr95/rr100 の 3 点、
  records/threads は 100k/4 で hard-code」は現行コードと不一致。`FORMAL_WORKLOADS` が
  凍結から 1,000,000 records / 48 threads を導出している。本文の事実記述が古いだけで、
  前提条件 1 が充足したとは言わない (arm・非干渉性は測っていない)。
- 実装面の変更はゼロ。Codex 子は起動していない (docs のみの軽量版)。
- 成果物と生証拠 = `output/insights/2026-09-14_t1875-delta-min-gate/`。

## 次の一手差分

### 更新

- [T-1875] **P2・裁定済み (2026-09-05、AI 委任) → 参照測定と実装は D1326 の順序のまま待ち
  (2026-09-14 に前提を実測)**:
  `delta_min` は holdout ごとに「pilot 前に凍結 `PerfConfig` で測る stock silo の
  session-median × 0.03」、向きは on − off、単位は絶対 tps (D1640)。
  **2026-09-14 の実測で、§10.2 の検証 consumer は既に実在し発火することを確認した
  (充足)。残る blocker は完了証明層で、12 条件中の充足は C10 の 1 件だけである
  (`d9bbdb6b0`)。** さらに §10.2 の解除条件のうち pilot の完全 block 成立・schedule
  generator と manifest の固定・§8 の再凍結とユーザー承認が未了。
  着手前に {{T:d1640-holdout-label-inversion}} の裁定が要る。
  証拠 = `output/insights/2026-09-14_t1875-delta-min-gate/`。
  base: fe4f6aad877e5680104079f1b49d66f0604179d75bcdf5070ca89fd303b43680

### 新規

- {{T:d1640-holdout-label-inversion}} **P2・ユーザー裁定待ち**: D1640 の「H1 = rr20、
  H2 = rr80」は凍結の権威 (rr80 が H1 / rr20 が H2) と逆である。訂正の形を決める —
  (a) D1640 側の label を正す追補、(b) 凍結側を正す再凍結、(c) どちらでもない読み替え。
  凍結は 2026-08-29 から不変で D1640 起草時点で既に逆だったため、(a) が素直に見えるが
  AI は裁定しない。放置すると T-1875 の参照測定が各 holdout へ他方の水準の閾値を与え、
  片側の実質効果境界が過小になる (規律 2)。
  根拠 = `output/insights/2026-09-14_t1875-delta-min-gate/`。
