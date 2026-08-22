---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-22
wave: dev-wave-t1472-provider-init-indeterminate
seq: 1
title: '[T-1472] C04 (docs/phase3-8c-preregistration.md §6条件4) のcrash時の扱いにprovider-init/transport-admission失敗を含めた (コード+テスト、branch worktree-dev-wave-t1472-provider-init-indeterminate、変異matrix = baseline PASSED・MUT-1〜4 4/4 KILLED・SURVIVED0・MISMATCH0)'
---

## 本文

- 裁定根拠 D657。決定文は実装・受入を別waveの責務とし記録のみでは完了扱いしないと明記しており、
  本waveがその実装waveに当たる。実装の詳細設計は {{D:c04-provider-init-indeterminate-implementation}}
  を参照。
- 段1 brief で根本原因を特定: `orchestrator/campaign/p3_autonomous_workload_trial.py::
  _finish_trial()` の pre-loop 初期化 (3106行) が、同じ関数内の mid-loop supervisor-error 分岐
  (3178-3183行) と非対称で、provider-init/transport-admission 失敗時に
  `experiment_indeterminate` を立てないまま報告を組み立てていた。安全性は
  `autonomous_trial_completeness.py` の `_check_terminal_projection`/`_check_workload_coverage`
  を事前に読み、zero-cells の provider-init-error/transport-admission-error を既に妥当と
  扱っていることを確認してから着手した。
- 段2 codex plan (rc=0) が brief の (P1) を独立検証し、file:line 粒度の具体案を起草した。
- 段3 敵対相談2レンズ (sol=正しさ境界、luna=整合・実効性・所有範囲)。**罠**: sol/luna を同じ
  `--job-id consult1` で並列起動したため衝突し、sol が即死 (rc=2、実質未起動)。sol は別 job-id
  (`consult2`) で再投入し正常完了、luna は `attempt-0001.output.md` から recover した
  (どちらも実害なし、memory `dev-wave-consult-lanes-need-distinct-job-ids` に記録)。
  sol 所見1 (C04 の再走許可意味論と `trial_registry.py` の retryable-failure 要件との不整合、
  real だが pre-existing・scope外) と luna 所見6+sol 所見2 (test coverage gap 2件) を段4裁定で
  real として採用し plan v2 へ反映した。luna 所見4 (DW-G05 の現在形表現が過大、real) も採用し
  brief の影響記述を未来条件へ訂正した。
- 段5 実装子 (Codex role=author、独立 worktree `dev-wave-t1472-provider-init-indeterminate-author1`)
  が production 1箇所・test 4箇所を実装。子の環境では `qstat -Q preflight rc=1` で pytest 実走
  不能 (既知の子 sandbox 制約) のため「実装済み・未実走」と正しく報告。
- **親が実測して赤1件を発見** (`test_registered_transport_admission_failure_is_indeterminate`
  が `[campaign-binding] producer campaign_id differs from the manifest` で red)。段6敵対
  レビュー2本 (job-id: reviewA/reviewB、段3の教訓を反映し最初から分離) が独立に同じ根本原因
  (fixture が site=OTHER で manifest campaign_id を事前計算・登録済みなのに test が
  `_current_site` を PEGASUS_COMPUTE へ monkeypatch したことによる不一致) を特定し、
  production 側は無欠陥と確認した。reviewA は追加で real 所見2件 (MUT-4 の kill 精度不足
  =`match=`が部分一致、C06 test が例外発生しか見ておらず attempt/lifecycle 永続化未検証) を
  発見。
- fix1 (Codex role=author、author1 worktree 再利用) が3件すべて修正。親は `diff` (git不使用、
  隔離session はauthor1 worktreeへの`git -C`/`cd`が不可) で差分確認し Edit ツールで自分の
  wave worktree へ逐語転記、byte-identical を確認した (T-1314 と同型の手順)。焦点再レビュー
  1本 (job-id: focus1) で3件とも closed・回帰なしを確認した (DW-O16、1巡で完了)。
- production差分 (8行) をcommit (`74b3854f`) し `check_ai_provenance.py` full-history監査
  (4970件、新規違反なし) を確認した。
- **変異matrix (DW-M01、MUT-1〜4) は試行錯誤の末に完了。詳細な罠は failures fragment
  ({{F:mutation-worktree-local-mode-and-resume-file-preconditions}}、F461再発)参照。** 要旨:
  DW-M07 (段6条件dispatch15「fix後に変異を走らせる直前」) を読まずに `--runner-mode local` へ
  切り替えた結果、DW-M07が明記する「runnerが自壊しrc=16になる」を実際に再現し、加えて
  `--resume`/`--attempt-out`/`--out`/`--wrapper-attempt`の未文書な相互依存制約に連続して
  遭遇した。最終的にDW-M07の指示どおり`--runner-mode dispatch`+`--force-dispatch`へ戻して
  クリーンな結果を得た: **baseline PASSED (rc=0)・MUT-1〜4 4/4 KILLED・SURVIVED0・MISMATCH0**
  (`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1472-provider-init-indeterminate/
  mutation-out-final.json`)。途中で得た暫定結果 (`mutation-out-v6-erratum.json`、MUT-3が
  自分のexpected_nodes過大登録によりMISMATCH — 実際は登録した4件中3件が明確なKeyErrorで
  KILLEDしており、除外した1件は当該変異でも論理的に通る) はerratumとして保全しspecを
  訂正した。
- **D662発見と対応**: 段6作業中、複数の並行セッションから「受入lease廃止・merge後再テスト
  省略可」という通達を受けたが、当初 (main HEAD 92e8878e時点) は正本 (docs/dev-wave/
  operations.md DW-O23/DW-O25、decisions.md) にこの内容が反映されておらず、独立検証の結果
  従わないと回答した。その後main HEAD b3fe27cf以降で`docs/decisions.md`のD662として正式landした
  ことを`git show main:docs/decisions.md`で自分でも確認した。D662はユーザー裁定として
  受入lease待ち行列の廃止・自ブランチでの受入全走・merge後再テスト省略・known-violation
  registration による scope外問題の切り離しを定める。本waveの段9 landはD662に従う
  (`docs/dev-wave/operations.md`のDW-O23/DW-O25自体はまだ未改訂、D662が運用として優先)。
- **本fragmentの時点では受入全走・landは未実施** (D662に従い自ブランチでの受入投入を準備中、
  `preclaim-history-provenance`の固定300秒timeoutが現在の計算ノード混雑に対して短すぎるという
  別の既知課題が解消され次第投入する)。記録 (本fragment) をtested tipへ含めるため、受入投入前に
  この記録commitを先に作る (memory `acceptance-runs-on-final-tip-with-records`)。受入・land結果は
  後続fragmentまたはworklog本体の追記で記録する。T-1472は本fragmentでは触れず carry する。

## 次の一手差分
