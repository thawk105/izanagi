---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2780-codex-recovery
seq: 1
title: [T-2780] mocc pilot discriminator修正を回収・独立監査し、計算ノードのfinalization到達と変異検出を確認した (コード+docs、branch worktree-dev-wave-t2780-codex-recovery)
---

## 本文

- 旧wave f93281e55 / author f75ca703c を引継ぎ、着手時local main b2037abfaから専用Codex木へ回収した。
  独立read-only監査はmust-fix 0。実装bytesを変えずmain第1親でmergeしphaseチェックを同時記録した。
- job5905のsubmit成功や旧待ち手のsuccessだけでは完走とせず、終了時刻入りaccountingと
  receipt/patch/source/discriminatorの束縛を回収した。no-g2、各gate rc0、Elapse127秒。
  正式認証・G2再現・rc1実機被覆は主張しない。schema判断は{{D:mocc-pilot-patch-binding}}、F1027へ追補。
- 正式変異job6360はbaseline149件通過、等価M0生存、M1〜M8は期待node完全集合一致、MISMATCH 0。
  挙動検出6件とsensitivity2件を分離。M8はjob-result writerの先行拒否で、後段field assertionの検出とはしない。
- 旧local probeとauthorのpytest.main直接呼出はrun_tests経由規律からの逸脱として保持し、正式検査に代用しない。
  回収後の変異は正規mutation taskで計算ノードへ投入した。試行1/2の入力形式拒否は投入前でchild_started=false。
- 旧焦点走はlocal上限到達後のjob5893で1591 passed / 3 skipped、114.92秒。追加job6365は239 passed、5.29秒。
  contract単独149件とpegasus_tools単独72件も正規経路で通過。実装者の非正規実走との合算はしない。
- check_codex_agents/check_docsはrc0。統合全史provenanceは11460件・新規違反なし、既知違反56件を区別する。
  記録後のjob6378はqueue-wait-timeoutで未実行。再投入job6403を親がQUE中にqdelし、
  compute-marker-not-observedのF47ラッチを武装させた。親の取消し判断が原因で、解除は人間手番。
  この時点では自動投入を止め、最終受入とlandを未実施のまま保存した。
- 上記停止後、取消し起因と解除境界を説明したうえでユーザーからmain landまでの再開・自己改善指示を受けた。
  6403の不在と保存ラッチのhash一致を再確認し、この既知取消しだけを復旧した。通常のF47契約は変更しない。
  自己改善はDW-C00の停止前runbook読了導線とmutation taskの入力形明示に限定する。
  最終受入は全記録commit後に共通待ち手で行い、結果を受領証へ固定して共通landで取り込む。
- 全job-stagingをrepo外へ複製し全ファイル一致を確認した。レビュー逐語・receipt・変異台帳と限界は
  `output/insights/2026-09-18/t2780-mocc-pilot-discriminator/`。清掃はland・保全・非稼働を条件に許可済み。
  本題外のgate・台帳機構・一般化・次waveは追加しない。追加承認された自己改善は上記の運用文書だけ。

## 次の一手差分

### 完了

- [T-2780] HYDRATE_PY、build前X/P patch・verifier source配線・receipt束縛を実装し、独立監査・job5905のfinalization到達・正式変異job6360・焦点検査で確認した。
  remaining: none
  base: e2f21f233b4c5a3d9789bfb2d5b7412b3d2be19811809b7278409961b8541759
