# [T-434] 段 1 brief — cap-lift 受領証と全 consumer 結線

基準: main `08a17b3b3` / branch `worktree-dev-wave-t434-cap-lift-receipt`。
設計正本 (2026-08-04 起草・択一 1〜10 は同日 /rulings で推奨どおり裁定済み):
`output/insights/2026-08-04_t434-cap-lift-receipt/design-v2.md`。

## scope

D841 (択 (a)) に従い、上限引き上げの受領証 (schema + 検証器 + 発効 topology 検査) と、
それを読む consumer の結線を**同じ変更単位**で実装する。受領証だけ先に作る形は不採用。
仮想リスク向けの gate・検査・台帳・一般化は scope 外 (DW-G05)。

## 段 1 前提実測 — 承認済み裁定を覆す新事実 3 件 (段 4 で再裁定する)

- **N1. `MAX_APPROVED_GENERATIONS` は 1 ではなく 2** (`p3_autonomous_workload_trial.py:144`)。
  D410 (2026-08-15) が D114 の上限 1 を 2 へ引き上げた。design-v2 §2 の「receipt 無しの
  実効 cap = literal 1」をそのまま実装すると、現行の受理集合を**狭める**方向の未裁定変更になる。
- **N2. 層 3 の版上げは D828 (2026-08-25) が禁じている** — `layer3_schema.json` の
  `runs.items.properties` へ optional property を足す変更では `schema_version` を上げない。
  design-v2 択一 5 の「v4 top-level envelope」はこの後発裁定と衝突する。
- **N3. 6 面に無い第 7 の consumer が実在する** — `s8c_preregistration_evidence.py:2529` の C11
  評価器が AST で `MAX_APPROVED_GENERATIONS` を読み `cap < 2` を `GENERATION_CAP_NOT_LIFTED` で
  UNSATISFIED にする。契約 `s8c_preregistration_evidence_contract.v1.json` の C11 `field_paths` が
  同定数と 3 入口を pin する。`docs/phase3-8c-preregistration.md` §4 は全 cell を厳密に `G=2` と定める。

## 不変条件

- 規律 2: anomaly を検出した variant の即 reject を緩めない。既存テストの期待値を変えない。
- 現行の受理集合 (`generations` 1..2 が receipt 無しで通る) を狭めない。C11 を UNSATISFIED にしない。
- `REPORT_SCHEMA_VERSION` / `layer3_schema.json` の `schema_version` は据え置く (N2、D828)。
- 実装面は Codex `role=author` が書く。親は docs 本文のみ編集する。

## provisional 裁定 (割れうる前提 — 段 3 の攻撃対象)

- **(P1) 受領証が支配するのは「現行の承認済み定数を超える引き上げ」**とし、receipt 無しの実効 cap は
  `MAX_APPROVED_GENERATIONS` (現行 2)、receipt 検証済みなら `min(receipt 値, MAX_GENERATIONS)` とする。
  design-v2 §2 の literal 1 は N1 により採らない。
- **(P2) 層 3 は版を上げず**、`runs.items.properties` へ optional な受領証 envelope を足し、
  campaign identity への束縛だけ design-v2 択一 5 から継承する。
- **(P3) 第 7 面 (C11 / 事前登録 evidence 契約) を結線対象に含める。** C11 の述語を
  「定数が 2 以上」から「実効 cap の導出が受領証経路を通る」へ広げるかは段 4 で決める。
- **(P4) DW-O13 の到達可能性**: P1〜P9 の独立評価器は repo に 1 件も実在せず (実測: `D121` を
  参照する評価器 0 件)、`SATISFIED` は現環境で到達不能である。したがって受領証の受理枝は
  現状 fail-closed のまま開かない。正例をどう置くか (実体を stub せずに受理枝を発火させられるか、
  できないなら受理枝を採用してよいか) は段 3 の主要攻撃点とし、段 4 で裁定する。

## 成果物の形

- 受領証 schema + 純関数 validator (副作用前に 3 入口が同じ検証を呼ぶ)。
- 結線 7 面: runbook / 事前登録 evidence (C11) / journal `run-start` / report / 層 3 /
  producer 3 入口 / completeness の独立再検証。
- 変異事前登録 (DW-M01): 欠落・偽 hash・別 revision 流用・wrong parent・witness drift の負例と、
  受理枝の正例 (段 4 の (P4) 裁定に従う)。

## 分割方針

編集 path 所有が素集合になる 3 単位に分ける — (A) 受領証 core (schema + validator + 発効 topology)、
(B) producer 側結線 (3 入口 / journal / report) + completeness、(C) 層 3 + 事前登録 evidence (C11) + runbook。
依存は A → B, C。
