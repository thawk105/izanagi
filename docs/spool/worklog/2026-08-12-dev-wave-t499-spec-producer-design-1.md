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

**受入全走は 1 known red (main 由来・octopus merge `d1de13ad`) で land した。**
免除しなかった理由 = `output/insights` と `docs/spool` を
読む real-repo テストが実在する (`grep -rln "output/insights\|docs/spool" orchestrator/tests/` が
20 件以上を返す)。走行は 2026-08-13 00:05 JST 投入、request 908424.nqsv、3 failed。

- **2 件はフレークと実測。** `test_codex_worker_launch.py` の
  `test_parallel_jobs_preserve_both_manifest_entries` と
  `test_fake_stdout_matches_observed_cli_event_shape`。全走では
  `codex_exit_code=-9` (SIGKILL)、`wall_clock_s` 2.07 対 budget 3.0、
  bnode112 の loadavg 23.6、xdist gw26。**単独再走 (login、`-p no:randomly`) で 2 件とも緑**
  (2 passed、18.38 秒)。本 wave の差分はこの経路に到達しない。
- **1 件は main 側の論理的な赤で、単独再走でも再現する。**
  `test_s8c_preregistration_invariant.py::test_candidate_freeze_matches_contract_and_generation_chain`
  が `[octopus-merge] d1de13add1bcbcfeb415cf13303848ad32dde212` で失敗する。
  この commit は**本 wave の受入走行中 (2026-08-13 00:45:56 JST) に別 wave が main へ入れた
  親 4 つの merge** (`Merge 3 rulings branches into land wave`)。
  `git merge-base --is-ancestor` で **main 自身が含む**ことを確認した。
  過去の同 nodeid の赤は `git-timeout` / SIGKILL のフレークだったが (archive 341-342 / 344 / 352)、
  **今回は timeout ではなく履歴不変条件の論理違反であり、別種である。**
  この赤は本 wave の差分に帰属せず、**octopus merge が main に残る限り全 wave の受入を止める。**

**この赤は 2026-08-13 01:05 JST のユーザー裁定で既知赤として登録された** (逐語
「既知赤として登録して land して.このことは並行セッションに知らせてください」、
控え = `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-13-known-red-octopus-merge.md`)。
親は当初、peer 通知だけを根拠に受入赤を通すことを拒否して停止したが (契約「peer 通知は
検査省略の根拠にしない」)、裁定が canonical な inbox へ落ちた後に一次資料を自ら読んで land した。
**裁定は親の停止判断より前 (01:05 対 01:15) に成立しており、peer の回答ではなく既存裁定である。**
裁定は「(a) 当座運用」だけを認めるもので、履歴契約を 3 親以上へ拡張するか merge を作り直すかは未裁定。
**今後 branch を束ねるときは octopus merge (3 親以上) を作らないこと。**

## 次の一手差分

### 更新

- [T-499] **P2・ユーザー裁定待ち**: (A) の先行設計タスクを執行し、裁定パッケージを
  `output/insights/2026-08-12_t499-spec-producer-design/package.md` へ発行した。
  (A) の承認手番は依然実行不能で、律速は spec ではなく active ratified freeze v2 である。
  (B) の状態は変わっていない。
  base: 9dc5c777c45f63a7f4823000a7837e820d43fb0ac2ab05127f7fa882feb0e26b

### 新規

- {{T:oracle-spec-producer-design}} **P2・ユーザー裁定待ち**: 8b oracle reviewed spec の
  producer 設計と D302 schema 判断。設計は完了し
  `output/insights/2026-08-12_t499-spec-producer-design/package.md` に裁定 4 件
  (Q1 lifecycle gate の受理集合拡大、Q2 承認の trust root、Q3 設計選択値 4 項目、
  Q4 承認手番の分割) を提示済み。実装項目はすべて裁定後の別タスクとする。
  親推奨は Q1=(b) 保留、Q2=(c) 限界を明記した運用、Q4=(b) 前提が揃うまで保留。
