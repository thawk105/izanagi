---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1447-orphan-hold-races
seq: 1
title: [T-1447] dispatch_compute.pyのorphan-hold race 3件を現行shard dispatchへ統合した (コード+テスト、branch worktree-dev-wave-t1447-orphan-hold-races、変異matrix = dispatch 5/5 KILLED + bounded local 1/1 KILLED)
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
- 中断後のCodex再開では、旧 `acceptance-red-check` (rc=70) と `signal-15` (rc=143)、および
  HEAD=`0441b3f5` の27件赤をすべて不受理の一次artifactとして保全し、成功証拠へ流用しなかった。
  旧変異artifactも「6件KILLED」ではなく、初回6登録=3 KILLED/2 MISMATCH/1 SURVIVED、
  訂正後5/5 KILLEDであると独立監査した。
- 現mainのshard dispatchが同じ3実装面を変更していたため、read-only Codex監査は単純mergeを
  NO-GOとした。D95に従うCodex authorへ3巡戻し、artifact/control root分離・control lock・
  per-request ledger・intent recovery・deadline共有を保ったまま、T-1447防壁を意味統合した
  (`65cd1769`、docs-only main追随=`8cee8fe1`)。release途中失敗、fresh target-bound END、
  ledger-only destructive consumer閉包も同じauthor成果へ含む。最終refocusはCodex利用上限で
  output 0/not_acceptedだったため緑に数えず、3巡上限後の静的照合と実測へ送った。
- 現tipの焦点走は対象4 fileで465 passed/1 skipped。変異はMUT-2/6/7/8と新しいconsumer閉包を
  dispatchで5/5 KILLED、runner自己変異となるMUT-4を`run_tests.py -n 8`のbounded localで
  1/1 KILLEDとした。旧MUT-3はdiagnostic TIMEOUTとして別枠に残し、KILLEDへ偽装していない。
  TIMEOUT時にRUN jobが残ったため自然walltime終端までsource/holdを保全し、qstat不在確認後に
  HEAD復元・該当hold/sidecarだけを削除した。
- 段5実装は当初のcodex plan (`stage2-plan.md`) より広いraceの窓 (qsub直前の危険状態突入
  直後から保護する設計) を実現しており、親briefの想定より優れた設計だったことを段5監査で確認した。

## 次の一手差分

### 完了

- [T-1447] dispatch_compute.pyのorphan-hold機構の未防御race 3件 ((a)外部SIGKILLでhold未作成、
  (b)hold書込み失敗のfail-open、(c)qdel後qstat終端未確認) を是正した。pending hold前倒し作成
  (create-only)・専用例外`_OrphanHoldError`によるfail-closed化・post-qdel bounded終端確認を
  実装。段3・段6の敵対検証で収斂したdeferred signal優先順位の欠陥をfix 1巡で解消。
  現mainのshard/control/intent設計へ統合し、release failure-atomic化とledger-only consumer閉包を
  追加した。焦点走465 passed/1 skipped。変異matrixはdispatch 5/5 KILLED + bounded local
  MUT-4 1/1 KILLEDで、SURVIVED 0・MISMATCH 0。MUT-3 diagnostic TIMEOUTは別枠記録。
  remaining: none
  base: b9fe3f9e302886223fd631f3c20d40ab2da10bdba8d4641ab1d8a6e08e8e60ae
