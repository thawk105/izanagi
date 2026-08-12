---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-12
wave: dev-wave-t499-spec-producer-design
seq: 1
title: 8b oracle reviewed spec の producer 設計と D302 schema 判断 (docs + insights のみ、branch worktree-dev-wave-t499-spec-producer-design)
---

## 本文

2026-08-12 第 6 束ユーザー裁定 [T-499] Q1 = (b) の先行設計タスクを執行した。
**docs + insights のみで実装差分ゼロ。** durable artifact 0 件、`APPROVED_SPEC_SHA256` は
`None` のまま、contract test も `SCHEMA_VERSION` も変更していない。

- 成果物 = `output/insights/2026-08-12_t499-spec-producer-design/`
  (`package.md` = 裁定パッケージ、`producer-design.md`、`d302-schema-choice.md`、
  `preregistration-approval-package-draft.md`、`verbatim/` に子出力 4 本)。
- 設計判断は {{D:oracle-spec-durable-is-lifecycle-not-schema}} と
  {{D:oracle-approval-not-machine-enforced}}。

**裁定控えの前提 1 件が取り違えだった。** `2026-08-12-t499-approval-turns-blocked.md` は
「`_assert_user_commit` の要求を満たす形で spec bytes を配置する」としていたが、
oracle spec の承認経路にその要求は存在しない (`_assert_user_commit` の呼び手 4 か所は
すべて freeze v2 の record)。spec 側に同等の provenance を課すかは新規の設計判断である。

**親の brief 前実測のうち 3 件を段 3 が訂正し、親が一次資料で確認して撤回・限定した。**

- M7 (T-810 を承認機構の先例とする) を**撤回**。T-810 の artifact 自身が
  trust root 不在と `run_authorized = False` を宣言し、launch に正例が構造的に無い。
- M9 を限定。`contract_sha256` / `clocks` の実 equality は manifest 層ではなく driver 層。
  manifest 層は 64hex の書式検査だけ。
- M10 を限定。`holdout_ids` / `configuration_ids` は v1→g1 の transition 許可 pointer 集合に
  `/holdouts` が無いため**有効な v2 では機械的に v1 から継承される**。導出不能なのは
  `binding_identity` だけであり、その authority は `LaunchValidatedFreeze.binaries_by_cell`。

**段 2 プラン子の推奨 (協調 v2 再発行) を不採用とした。** 「選択肢 A は受理集合を広げるから
規律 2 と両立しない」という却下論法が、同じプランの「B でも zero-file assertion は落ちる」と
両立しない。段 3 敵対 2 本と親の独立見解 (子出力を読む前に固定、
`verbatim/s1-parent-independent-view.md`) が独立に一致して refuted と判定した。

**段 3 がより上位の欠陥を 4 件発見した** (schema version をどちらにしても残る)。
(1) 人間承認が機械強制されていない、(2) lifecycle の状態機械が閉じていない、
(3) pin 設定後から本走までの同時 drift が閉じていない、
(4) spec の binding と `LaunchValidatedFreeze` の交差照合が one-shot marker 作成より後にあり、
誤 binding が初回 run を消費しうる (`s8b_oracle_driver.py` の marker 作成が binding 照合より先)。

**現在の先行 blocker は `no-approved-spec` ではなく `no-active-ratified-freeze` である。**
`build_approved_manifest` は spec より先に active freeze を読むため、spec を承認しても止まる。

工数: codex 3 本 (plan sol/max、consult sol/max、consult luna/max)、いずれも受理検査 rc=0。
親は段 2 の出力を読む前に独立見解を固定し、子と突き合わせた。

## 次の一手差分

### 更新

- [T-499] **P2・ユーザー裁定待ち**: (A) の先行設計タスクを執行し、裁定パッケージを
  `output/insights/2026-08-12_t499-spec-producer-design/package.md` へ発行した。
  (A) の承認手番は依然実行不能で、律速は spec ではなく active ratified freeze v2 である。
  (B) の状態は変わっていない。
  base: c0192f6ddc57e303dfb8dbc6c5038b896e456080f36a5efe5576fe041a33126a

### 新規

- {{T:oracle-spec-producer-design}} **P2・ユーザー裁定待ち**: 8b oracle reviewed spec の
  producer 設計と D302 schema 判断。設計は完了し
  `output/insights/2026-08-12_t499-spec-producer-design/package.md` に裁定 4 件
  (Q1 lifecycle gate の受理集合拡大、Q2 承認の trust root、Q3 設計選択値 4 項目、
  Q4 承認手番の分割) を提示済み。実装項目はすべて裁定後の別タスクとする。
  親推奨は Q1=(b) 保留、Q2=(c) 限界を明記した運用、Q4=(b) 前提が揃うまで保留。
