---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-10
wave: dev-wave-t2273-current-cost
seq: 1
title: [T-2273] 現行受入の最大占有と非重複tailを分け、局所コピー費用を診断して実装不採用とした (docs・実測、branch worktree-dev-wave-t2273-current-cost)
---

## 本文

- D1936項35/D104に従い、旧t080床仮説を固定せず既存受入を再集計した。起動時6走と相談中の追加完了1走は全てshard-0が最遅。最大占有233.707〜272.355秒に対し最後1workerだけのtailは2.610〜7.666秒だった。
- planの「候補なしで終了」は相談Bが早計と指摘した。親は上書き前sourceコピー1件の費用診断を先に行い、終端判断を延期した。検証反復の削除は相談Aの根拠を採り不採用とした。
- 新規実装を作らず既存phase pluginを再利用。計算ノードbnode022、request990044.nqsv、HEAD98a3d7c9eで5passed/rc0。pytest210.48秒、JUnit210.328秒、会計216秒。base構築2回73.279/81.125秒に対し、orchestrator全量copyは0.822/0.986秒だった。
- 上書き対象のコピーはその一部で、追加機構を採用する根拠にならなかった。実装差分0で診断終了。D104のA-B/B-Aは未実施であり、効果ゼロの統制実験や恒常的短縮を主張しない。prewarm Pは未測定のまま先行実装しなかった。
- nodeの読取sshはhost key verificationで失敗し、同居processの直接確認は未充足。計装値は候補の費用診断だけに使い、正式な効果採否の証拠にはしない。独自probe・cache・gate・検査・台帳は追加していない。
- 起動時に所有重複を確認し、T-2515のt1259/conftest・較正変更は編集しなかった。親の実装直接編集なし。診断のrawと独立相談、限界は `output/insights/2026-09-10/t2273-current-cost/README.md`。
- 実装差分0で段5/6・変異を省略し、実repoの焦点5nodeを段7前に実走。check_codex_agents/check_docsはrc0。記録後の受入・landは別の最終receiptで閉じる。
- dev-wave 改善候補: なし。今回のRUN表記を実行開始と読んだ途中報告は親の誤読で、既存の完了証拠契約の欠落ではない。Started Request Timeと実artifactで訂正した。自己改善実装と次wave起動は行わない。
- 受入初回は共有phase文書のowned-path-overlapで実走前拒否。所有検査を外さず固定mainを通常mergeした。次の実走は22473passed/68skipped/2error、t1259共通setupのgit ls-filesが30秒timeout。対象test/probe/conftestはmainとbyte同一で文書assertion前の赤だが、repo走査の間接費用の影響まで否定しない。同tipのfile単独再走は51passed/rc0（484.16秒）、DW-O18に従い編集・除外なしで受入を再走する。
- その再受入は22464passed/68skipped/6failed/5error。t1259のtimeoutが再発し、親はscope外処置と解釈して停止した。2026-09-11のユーザー「main landまでよろしく」で停止を撤回し同waveを再開。mainにe28a62d26のt1259 snapshot修正が着地済みであることを確認し、固定main d85bbb211を通常mergeした。今回の独自実装・hold追加はなし。

## 次の一手差分

### 更新

- [T-2273] **P1・今回の診断完了、300秒目標は未達**: 2026-09-10の7走はshard-0が最遅320.826〜397.021秒、最大worker占有233.707〜272.355秒、最後1workerのtail2.610〜7.666秒。計算ノードの局所コピー診断で採用根拠を得られず実装0。次も最新律速を選び、検出力維持とD104の効果実証が成立する候補だけ採る。
  base: 88dee648b7847f2c243428333b9533f8ea90689c683664ce688cfa88325b6aa9
- [T-2559] **P1・今回の局所費用診断完了、prewarmは未実装**: base構築73〜81秒に対し候補を含むorchestrator全量copyは0.82〜0.99秒で、局所実装は採用しなかった。観測worker tailと未実装prewarmの非重複tail Pを区別し、Pと同一allocation A-B/B-Aは未測定。未検証のprewarm/共有cacheは先行実装しない。
  base: 959ce3735bf3f9e6adc6ec76c4b8970772490e79574c187167247d4e9d7e0f06
