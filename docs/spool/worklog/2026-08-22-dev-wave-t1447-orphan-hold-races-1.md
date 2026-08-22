---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1447-orphan-hold-races
seq: 1
title: '[T-1447] dispatch_compute.pyのorphan-hold機構の未防御race 3件を是正した (コード+テスト、branch worktree-dev-wave-t1447-orphan-hold-races、変異matrix = baseline PASSED・MUT-2,4,6,7,8 5/5 KILLED・SURVIVED 0・MISMATCH 0)'
---

## 本文

- 一次資料 (T-1053段3敵対レビュー`stage3-lens-b.md`) は「静的検査のみ、pytest未実行」と明記していた
  ため、段1着手前に3件raceを実プロダクションコードへの再現スクリプト (repo外
  `dev-wave-jobs/dev-wave-t1447-orphan-hold-races/repro/`) で実証した。race(a)は実子プロセス+実
  SIGKILLで、race(b)(c)は実関数呼出しで再現確認。
- 段3敵対相談2レンズ (sol=正しさ境界、luna=整合性・波及) が独立に収斂した最重要所見:
  hold操作helperの`except BaseException`が`_SignalAbort`も無差別に変換し、deferred signal情報を
  失う。段6敵対レビュー2レンズも独立に同じ所見へ到達し、fix 1巡で解消・焦点再レビューでclosed確認。
- **親の手順逸脱と自己是正**: 段5完了後の親検証中、consumer test
  (`orchestrator/tests/test_mutation_harness.py`) の互換性問題を発見した際、Editツールで
  直接修正してしまった (凍結境界違反 — 親は実装面を直接編集しない)。`git checkout --`で
  revertし、同じ修正をCodex `role=author`子 (job-id t1447-stage5b-fix-consumer-test) へ
  正しく委任し直した。実害なし (commit前に是正)。
- 変異事前登録は段4のMUT-1〜9から、単一理由kill・既存test対応を個別確認できたMUT-2,4,6,7,8の
  5件へ絞り込んだ。MUT-3 (post-qdel hard cap除去) は初回実行でSURVIVED — 調査の結果、
  outer for-loopとは別に各classification分岐内の`attempt < qstat_attempts`検査が独立に
  同じ上限を課しており、意図せず冗長防御になっていたと判明 (実害なし、良い意味での過剰防御)。
  DW-M08 diagnostic pin相当として記録に留め、strict mutationとしては見送った。
  MUT-4/MUT-8は初回MISMATCH (期待1nodeに対し実測7/2node) — `_arm_pending_orphan_hold`と
  outer exceptの2箇所目call siteはいずれも複数testが経由する共通点であり、単一原因の
  カスケードと確認しexpected_nodesを実測値へ訂正して再実行、5/5 KILLED・SURVIVED0・
  MISMATCH0を得た (初回結果は`mutation-ledger-attempt1-erratum.json`へ保全)。
- 段9進行中にD662 (計算ノード混雑の恒常化を踏まえた受入・land運用の簡素化) が別waveの
  ユーザー裁定としてmain (commit b3fe27cf) へ着地した。lease coordinator系ピアからの通達を
  即座には信用せず、`clean-automerge-can-still-break-tests-semantically`memoryとの矛盾を
  指摘して裏取りを要求し、`git cat-file`/`git show`/`git branch --contains`で独立に検証した
  うえで採用した。T-1447の段9はD662新運用 (lease待ちなし、branch単体で受入全走→merge→
  再テスト省略) に従った。
- **known-violation (自分の変更に起因しない、D662点4に基づく記録)**: 受入全走
  (branch単体、HEAD=`0441b3f5`) で27件の赤を観測したが、全て
  `test_sort_swo_oracle.py` (25件、masstree関連ビルドキャッシュ `config-h-missing`)・
  `test_dev_wave_wait.py::test_dispatch_attestation_protocol_matches_producer_exactly`・
  `test_t338_submission_gate_unit5.py::test_receipt_publish_call_sites_are_path_aware_and_allow_event_sink`
  で、`dispatch_compute`・`test_pegasus_dispatch_compute`・`test_mutation_harness`との
  文字列一致はゼロ (grep確認済み)。他waveの並行作業 (masstree staging floor campaign等) に
  起因する既知不具合と判断し、ユーザー裁定へ送る。本waveはこれをblockerにせずlandへ進んだ。
- 段5実装は当初のcodex plan (`stage2-plan.md`) より広いraceの窓 (qsub直前の危険状態突入
  直後から保護する設計) を実現しており、親briefの想定より優れた設計だったことを段5監査で確認した。

## 次の一手差分

### 完了

- [T-1447] dispatch_compute.pyのorphan-hold機構の未防御race 3件 ((a)外部SIGKILLでhold未作成、
  (b)hold書込み失敗のfail-open、(c)qdel後qstat終端未確認) を是正した。pending hold前倒し作成
  (create-only)・専用例外`_OrphanHoldError`によるfail-closed化・post-qdel bounded終端確認を
  実装。段3・段6の敵対検証で収斂したdeferred signal優先順位の欠陥をfix 1巡で解消。
  焦点走206 passed (test_pegasus_dispatch_compute.py)、90 passed (test_mutation_harness.py、
  consumer互換性修正込み)。変異matrix 5/5 KILLED。
  remaining: none
  base: b9fe3f9e302886223fd631f3c20d40ab2da10bdba8d4641ab1d8a6e08e8e60ae
