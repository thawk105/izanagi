---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-19
wave: dev-wave-t2489-nodes5-local-lock
seq: 1
title: [T-2489] A-2の5ノード化を整合し、node-local lockの局所候補を計算ノードで実測して不採用とした (コード＋docs、branch dev-wave-t2489-nodes5-local-lock)
---

## 本文

- D2148項5と第23回裁定控えに従い、A-2のscheduler.nodes=5をpolicy一キー・literal pin・host/nodefile/qsub fixtureと同時整合した。
  着手時local main `7975385b55a2e3451f6c80d584a9312f44d5199d` からfresh worktreeを作成。最終3fileの所有重複は219木を照合し、完了済み旧probeのpolicy以外になかった。
- A-2/A-6共通job bodyの固定scratch_base/bench.lock候補を試作し、計算ノード2台で実bench_lockを測った。
  request9137.nqsv、bnode082/083、2026-09-19 07:38:45〜07:38:47 JST、NQSV Elapse6秒。
  candidate同士は同nodeでBenchBusy/別node取得成功、default同士は両方BenchBusy、mixed pathは同nodeで両方向取得成功、全4case解放後取得成功。
  **候補は不採用**。既存default consumerとの同一ノード排他を失うため、候補exportと専用試作testを撤回した。共通job bodyは基準bytesへ戻し、同一ノード内の既存排他を維持。
  他launcher/workerの一般改修・新gate・総timeout追加へ広げず、付随性能値を論文採用値へ昇格させない。
- 実測は同一予約内の別process/別scratchであり、独立scheduler job間のnamespace共有、全bencher排他、CC性能改善を主張しない。
  実source代入由来pathのflockと、stubbed job-body inheritance harnessの4caseは別の証拠。過去attemptの待ち時間全体の原因や約8分の静的見積りを確定しない。
  一次資料は `output/insights/2026-09-19/t2489-a2-nodes5-local-lock/README.md`。原本と運転記録は `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2489-nodes5-local-lock/`。
- 独立plan、相談2レンズ、D95 author、レビュー2レンズ、候補撤回fix、焦点レビューを実施。
  author試作 `c5bfe9e8249634236ac267e4114044433a64490c`、fix `3e2a8327ab7678fe7258cbf6701d81b4158e5759`。親は実装面を直接編集せず所有path patchだけを統合した。
  レビューBの候補出荷拒否を実測採否へ反映。両rank/会計照合と候補撤回はclosed。消滅確認の一次出力不足だけpartialだったためqstat不在出力を追補した。
- 試作時の関連5fileは442 passed/1 skipped（既存growth hold1件）、最終file単独走はcertification215 passed、job-contract72 passed。
  変異は固定 `eda92f10774b297c0abe292a3bd757bb3e861802` の独立cloneでbaseline5件PASS、登録2/記録2/KILLED2/期待一致2。
  nodes1への回帰はpolicy pin1件だけ、host count拒否無効化はA2/A6不足・過剰4件だけで検出。wrapper rc0で復元確認を完了した。skip・期待緩和・正しさgate変更はない。
- 親の単独test先行投入はprovenance dispatch中の既存holdでrc16/child_started=false、新job0。監査終端後に別log/doneで再投入し上記単独緑を得た。
  read-onlyレビューの初回detachはpid未生成で待ち手が拒否。対象process/成果物不在を確認し、親launcherの起動待ち後に再投入して受領した。新しい防壁は追加しない。

- 段6の正規受入は **25,231 passed / 69 skipped、child-green**。tested main `57485e280f2b13efc48e145a41462b2760e7e68b`、tested tip `73d4a16c5dcc3a7aa65437c1ad0ebf874c7c8724`。
  3shardのうち9331は07:59:33投入後08:15:14までPre-runningで、実テスト開始前の待ちだった。他2本の成功を全体成功へ先取りせず、全受領証の確定を待った。
  受入leaseは明示releaseしてreleased。正規受入中のsource変更・除外・期待緩和はしない。
- check_docs/check_codex_agents、freeze search（holdout conjunction hit0）、commit前後provenanceを実施。履歴監査は既知56件を維持し新規違反なし。
  dev-wave改善候補は専用handoffで「なし」。親の先行投入・pid準備の確認不足は既存DW-O26/C01に規律があり、改善実装や次waveを追加しない。

## 次の一手差分

### 完了

- [T-2489] D2148項5のA-2 nodes=5・policy pin・波及閉包を整合し、node-local局所候補を計算ノードで実測した。既存default consumerとの同一ノード排他を失う候補は不採用として採否材料を保存し、共通job bodyを維持。追加総timeoutの保留と性能値非昇格を維持した。
  remaining: none
  base: 55e11c2ef49d8b24c8635dabed61eb4b0c4c5679d0b385791aafce8eb6ea5b5e
