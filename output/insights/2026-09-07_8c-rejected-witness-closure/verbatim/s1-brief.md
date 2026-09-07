# 段 1 brief — 8c formal consumer の rejected 側 producer/consumer 不整合を閉じる

## scope

FC07 の rejected 枝が要求する 3 field と、production が実際に書く field の食い違いを閉じる。
`reflux_source_closure.py` の token 表が挙げる別名 `wal.abort.payload.witnesses` も同じ単位で正す。
これ以外は入れない — terminal 外枠の exact gate、result-evidence record 全体の producer 新設、
仮想リスク向けの gate・検査・台帳・一般化は scope 外 (ユーザーが明示)。

## 確定済みユーザー裁定

- 規律 2 を緩めない。anomaly を出した variant の即 reject は不変。
- 方向 (producer を書く / consumer を実在 field へ合わせる) は**実測した現物の field 名**を根拠に決める。
- 実装子は Codex `role=author` (D95)。親は実装面を直接編集しない。
- 着手直前の local main から fresh worktree。base = cf4273f5671ecda87c6f1b76148df239ce043ead。

## 実測した現物 (アンカー表)

| 対象 | 位置 | 実測した中身 |
| --- | --- | --- |
| production abort payload の外枠 | `orchestrator/campaign/pipeline.py:1249` | `{reason, build_attempt_id, build_admission_receipt_sha256, **extra, workload?}` |
| verifier reject の abort 呼び出し | `orchestrator/campaign/pipeline.py:1603` | `extra = {"verify": result_to_dict(vr) - trace_dir}`、`workload_tag=tag` |
| `verify` の key 集合 | `orchestrator/verifier/report.py:96` | `verdict, certified, serializable, stats{...}, integrity{...}, anomaly_count, total_cycles, anomalies[]` |
| consumer の rejected 要求 | `orchestrator/campaign/reflux_formal_consumer.py:866-880` | `candidate_attributable is True`、`truncated is False`、`witness_class_sha256s == [physical.constraint_sha256]` |
| token 表 | `orchestrator/campaign/reflux_source_closure.py:86` | `verifier_policy_sha256` の runtime path に `wal.commit.payload.verify_configs` と `wal.abort.payload.witnesses` |
| 同表の exact 比較 | `orchestrator/campaign/reflux_source_closure.py:236` | 成果物の `runtime_field_paths` と `tuple` 一致を要求 |
| commit 側 token の実在 | `orchestrator/campaign/pipeline.py:1821,1836` | `verify_configs` は production が書く → 表は commit 側だけ実在 |
| abort 側 3 field の producer | `orchestrator/campaign/` 全走査 | 0 件。`witnesses` も 0 件 |
| 事実上の producer 境界 | `orchestrator/campaign/p3_autonomous_workload_trial.py:429,1664` | `OriginProducerInputs.result_record_bytes` は外部注入。repo 内の構築は test 1 箇所のみ |
| verifier policy 成果物 | `reflux_source_closure.py:377` / `reflux_origin_fixture_builder.py:167` | `candidate_attributable_rejected = "single-normalized-witness-class"`、`witness_class_cardinality = 1`。production の実 file は不在 (fixture のみ) |
| `truncated` の既存判定 | `orchestrator/campaign/mocc_g2_discriminator.py:503` | `total_cycles != len(anomalies)` を `verifier-anomaly-list-truncated` と呼ぶ |

## (P1) 親の provisional 裁定 — 攻撃対象

**consumer を実在 field へ合わせる。producer に 3 field を新設しない。**

根拠 (実測):
1. `candidate_attributable: true` / `truncated: false` を producer が書く boolean にすると、
   producer が書けば必ず真になる**恒真な保証**になる。規律 6 の監査発火条件が名指しする型そのもの。
2. 同じ述語は production が既に書いている値から**反証可能に**導ける —
   attributability は `reason == verify.verdict` (infra 起因の `build-error` /
   `trace-timeout` / `admission-error` と字面で分かれる)、truncation は
   `verify.total_cycles != verify.anomaly_count` (既存の判定が `mocc_g2_discriminator.py:503` にある)。
3. witness class を consumer が `verify.anomalies` から導けば、record 側 `constraint_sha256` とは
   独立入力になる。producer が digest を書いて consumer が受け取る形より束縛が強い。
4. record 層の producer は repo 内に 1 件も無い (`OriginProducerInputs` 構築は test のみ)。
   producer を書く方向は record 層 producer の新設まで連鎖し、「不整合の解消だけ」を超える。

**規律 2 の向き:** 本裁定は受理集合を**狭める**方向でなければならない。今 FC07 で止まっている
rejected 側が通るようになるが、通る条件は「実 verifier 証拠が単一 witness class を示し、
anomaly 列が truncate されていない」で、緩めた箇所は無い。**恒真になる述語を 1 つも作らない**ことを
段 3・段 6 の攻撃面に明示する。

## 不変条件

- `_wal_field()` の root→payload fallback、FC07 以外の判定式、reason code、他 gate は変えない。
- D338 のとおり consumer は全検査通過後も `P6Unavailable` を返す — certified 選択集合は変わらない
  (DW-G05: 変わるのは report の reason と receipt / evidence-root 参照)。
- D1715 の決定 (terminal は `stage` を読む、外枠は閉じない) を巻き戻さない。
- pin: 対象 file 自身の blob/sha256 pin は repo 全走査で 0 件。ただし fixture builder の**出力**を
  固定する `orchestrator/tests/reflux_origin_fixture_baseline.json` と
  `orchestrator/tests/test_reflux_result_evidence.py` の golden literal 4 個は生きている (F864 の型)。
  値は実装子が変更後の実物から再計算する。段 2/段 3 が提示した値をコピーしない。
- normalization 規則を新設する場合、それは gate の新設ではなく既存述語の実装であることを示す
  (DW-O13: 要求する値が実環境で到達可能かを実測してから採用する)。

## 成果物

- `orchestrator/campaign/reflux_formal_consumer.py` の FC07 rejected 枝。
- `orchestrator/campaign/reflux_source_closure.py` の token 表 1 行 + 対応する fixture 成果物。
- `orchestrator/tests/reflux_origin_fixture_builder.py` と再計算した pin 2 件。
- 焦点走 (変更 production module を参照する consumer test を参照関係で引く、DW-O26)、変異 matrix、
  受入全走、worklog / decisions fragment、本 insight。

## 分割方針

変更面が 3 file + fixture + pin で、判定式が 1 箇所に集中するため実装子は 1 本。
段 2 プラン 1 本、段 3 敵対 2 レンズ、段 6 敵対レビュー 2 レンズ。
正しさ防壁 (FC07) に触り受理集合が変わるので、軽量版にはしない (DW-C00)。
