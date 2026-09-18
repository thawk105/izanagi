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
- 初回受入は25109 passed / 69 skipped / 28 errorsで失敗。T1259の共通setupのGit走査30秒timeout
  （status 10件、ls-files 18件）だった。該当test/probeのsourceは未変更で、同じtipのfile単独再走は
  51 passed / 12.12秒。I/O根因は未分離とし、timeout・期待値・除外を変えず全走を再試行する。
  待機中のmain前進56be58448（T-2674、docsのみ）は固定SHAで競合なく取り込んだ。
- 2回目も同じsetup timeoutが1件残ったため、再投入だけで閉じず隔離Codex authorで配置を局所修復した。
  D1936項43の既存module snapshotを同一workerで共有できるよう、T1259の30関数を既存memo集合へ
  明示追加した。全51ケース・実snapshot・deepcopy・timeout・lock/shard閉包は不変。独立レビューmust-fix0。
  焦点走はcollection時に既存site_policy初期化が確立する集合で261 passed/1 skipped。
- 配置変異でchildの4条件は期待どおりだったが共有木事後検査が赤になった試行を保持した。
  D1009の独立cloneへsourceを固定してwrapperを再走し、DW-M07から同規律への導線を補った。
  再走job6654はwrapper rc0・共有木一致・復元完了、4条件とも期待一致。M10は新helperで検出し
  旧helper対照では生存、M9は冗長な登録検査として区別する。verifier correctness killへ加算しない。
- 元author/fix authorの履歴はmain第1親の一括mergeで保全した。旧回収枝も保全し、rebase/forceは使わない。
- 全job-stagingをrepo外へ複製し全ファイル一致を確認した。レビュー逐語・receipt・変異台帳と限界は
  `output/insights/2026-09-18/t2780-mocc-pilot-discriminator/`。清掃はland・保全・非稼働を条件に許可済み。
  本題外のgate・台帳機構・一般化・次waveは追加しない。追加承認された自己改善は上記の運用文書だけ。

## 次の一手差分

### 完了

- [T-2780] HYDRATE_PY、build前X/P patch・verifier source配線・receipt束縛を実装し、独立監査・job5905のfinalization到達・正式変異job6360・焦点検査で確認した。
  remaining: none
  base: e2f21f233b4c5a3d9789bfb2d5b7412b3d2be19811809b7278409961b8541759
- [T-2504] D1936項43のmodule snapshotと各testへの独立copyを維持し、T1259の全consumerを既存memo配置へ接続した。timeout延長・検査除外をせず、実装着地済みだった追跡項を終端する。
  remaining: none
  base: c3b73b01c864b1e22c2bec7b8e2fc3038c7329c5bc8d8478bb27977ad067b30a
