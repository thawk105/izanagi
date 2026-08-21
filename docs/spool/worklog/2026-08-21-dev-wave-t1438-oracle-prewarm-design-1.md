---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-21
wave: dev-wave-t1438-oracle-prewarm-design
seq: 1
title: [T-1438] oracle_environment controller-only prewarm barrierを実装しREAL_REPO_SERIAL_NODESから24 nodeを分離した (コード+テスト、branch worktree-dev-wave-t1438-oracle-prewarm-design、変異matrix = baseline PASSED・4/4 KILLED・SURVIVED 0・MISMATCH 0、受入 verdict=child-green)
---

## 本文

- D591が候補Cとして見送った「controllerの資源解決がworker実行開始より必ず先行する」という
  hook順序前提を、pytest-xdist 3.8.0の実ソース (dsession.py/remote.py/workermanage.py/
  scheduler/load.py, loadgroup.py) を読んで段2 codex planが証明し、段3敵対相談3レンズ
  (lensA=hook順序反例探索、lensB=correctness/staleness再検証、lensC=規律2適合) が独立に
  検証した。lensCが「fixtureのままprewarm化しても既存closure gateから逃れられない」
  「RECEIPT_MEMO_CONSUMER_NODESには実はAST inventory完全性検査が既にある」という2点を発見し、
  段2 planの当初案 (fixture解除+prewarm配線だけ) では規律2に抵触することが判明した
  ({{F:receipt-memo-completeness-check-assumption}} 参照)。段4裁定でscopeを拡大し、
  独立完全性検査層の新設を必須要件とした ({{D:oracle-environment-controller-prewarm}})。
- 段5 Codex author実装は1回目 (`## 総括` 見出し欠落、親promptの書き忘れ) がformat不備で
  not_accepted、2回目の自己監査+報告修正でrc=0確定した (実装内容自体は1回目から完了していた)。
  段6敵対レビュー2本 (reviewA=real所見2件、reviewB=所見ゼロ) → fix2回 (production writer
  実行検証の強化、oracle prewarm hookのreceipt guardからの分離) → 統合後焦点再レビューで
  reviewA所見2件ともclosed確認。
- 計算ノードのjob queue混雑 (qstat実測: 33〜44 QUE, 117〜127 RUN) により、焦点走・受入・
  変異harnessの投入で複数回`queue-wait-timeout`(rc=16、`IZANAGI_DISPATCH_OVERALL_GRACE_
  OVERRIDE`env varでは延長できず実測901秒付近の非可変上限に達する) に遭遇したが、いずれも
  再投入で解消した (テスト内容の失敗ではなくインフラ層の一時的輻輳)。
- 計算ノード限定A/B: 現行66-node real-repo直列鎖を計算ノードで実測し76.46秒。D591の66-node
  基準値(79.02秒、追加前相当)と3%以内で一致し、90-node基準値(119.34秒、T-1012後)とは
  大きく乖離した。90-node状態の同日再測定は`IZANAGI_RUN_GROWTH_HELD_TESTS`
  (2026-08-12裁定でexplicit-user-command-only指定) を要する既定skip 57件を含むため、
  本waveでは実行せず — 公式性能主張はユーザー明示時に別途行う (command引数の指示どおり)。
- 受入は1回目がqueue-wait-timeoutでインフラ失敗 (lease自動release済み)、2回目で
  verdict=child-green (red_nodeids=[], flake_nodeids=[]) 確定。

## 次の一手差分

### 完了

- [T-1438] real_repo_receipt_memo.py型のcontroller-only prewarm barrier機構を実装し、
  REAL_REPO_SERIAL_NODESから24 nodeを分離した。詳細設計は{{D:oracle-environment-controller-prewarm}}。
  remaining: none
  base: 6155363b2bde8e929ed44e8210e897821ad656803c413edcead7ed2f51275eaa
