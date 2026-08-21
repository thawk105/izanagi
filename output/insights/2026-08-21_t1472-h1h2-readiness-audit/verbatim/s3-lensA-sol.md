結論: `g10` は「generation 10 / decider v6 の condition-freeze record が存在する」ことまでで、発効済みとは確定できません。

1. `brief.md:18-20` / `s2-plan-output.md:21-31,200-201` / `condition-freeze.v1.g10.json:1` / `docs/phase3-8c-preregistration.md:270-283,347-360` → g10の存在だけで、brief/planの「現行は第8世代 v4」「7条件 dispatch・5条件対象外」を現行事実として扱っている。発効はcommit単位の導出値で、record単体は8b本文も束縛しない → 本文epoch、g10 record、active/effective判定を分離し、active commitを確認するまで条件数を断定しない。

2. `s2-plan-output.md:88-94,123-137` / `docs/phase3-8b-restart-runbook.md:258-268` → 「v2 candidate producer不在」は誤り。`orchestrator/campaign/s8b_holdout_freeze.py:1681-1761,1849-1861,1874-1915` にcandidate生成器とCLIが存在する。ただし承認pin未設定などにより、ratified active freezeの生成・発効は未成立 → 「candidate producerは存在するが、floor/budget/approvalおよびratified発効が未成立」と修正する。

3. `brief.md:12-14` / `s2-plan-output.md:24-25,86-94,207-209` / `docs/decisions.md:22604-22622` → 「judge実装は別wave待ち」を無限定に書くのは不正確。D555は`judge_combined`の旧floor/scale gate撤去済みを記録している。一方、production consumerはゼロである。また`docs/decisions.md:22076-22090`はfloor artifactをjudge入力にしないと定める → `s8b_verdict`の実装追随済み、8cの証拠契約・registry・production受入配線未成立、と分解して記載する。

4. `s2-plan-output.md:88-90,208-210` / `docs/phase3-8b-restart-runbook.md:34-52,55-64` → 「現行oracle gateはfloor-null/budget-null」は、8/10〜8/11の記録を現行状態としている。`holdout_freeze.json:622-624`のnullはv1 artifactの状態であり、現行active oracle gateの証明ではない → 「runbook記録上」と日付を付け、現行active freeze/receiptは未確認とする。

5. `brief.md:38-39` / `s2-plan-output.md:5,12,25,150` / `p3_autonomous_workload_trial.py:1123-1163,4715-4718,4767-4781` → 「H1/H2は起動不可能」はcertifying formal launchとnon-certifying registered routeを混同している。現行productionの正式受入起動は拒否されるが、コードには`registered-formal-non-certifying`経路がある → 「certified formal launchは不可。non-certifying実行は正式実験・証拠に数えない」と限定する。

6. `brief.md:41-44` / `s2-plan-output.md:46-53` / `docs/archive/worklog-phase3-0820-731.md:284-289,509-512` → T972/T1371はworklog上の持越し番号に過ぎず、ListAgentsの稼働状態やT1438/T1458との重複は射影内で検証できない。briefの「全て稼働中または未クローズ」は過剰 → 各タスクのagent、lease、owner、重複対象を個別に「確認済み/未確認」で記録する。

7. `task-requirements.md:3-7` / `brief.md:3-6` / `s2-plan-output.md:55-65,196-213` → Codex roster、worktree、lease、handoff、floor/oracle等の所有者確認がblocker tableにない → これらを起動前確認項目として追加し、未確認なら正式起動不可とする。

8. `s2-plan-output.md:112-137` / `docs/phase3-s8c-autonomous-trial-runbook.md:160-178` → 多数のartifact存在・不在を射影外のinventoryだけで断定している。またp3の既定先は`output/exploration/autonomous-trials/<trial-id>/`であり、正式proof chainとは別物 → artifactごとに「存在確認済み/射影外で未確認/正式受入に不適」と分け、探索pilot pathとformal pathを混同しない。

9. `s2-plan-output.md:152-169` / `docs/phase3-s8c-autonomous-trial-runbook.md:100-101,198-199,221-225` / `docs/phase3-8b-descriptor-design.md:143-151` → 停止条件に、schema違反時のcell停止・再試行禁止、screen reject/timeoutの全件報告、budget不足時の対称的判定不能が抜けている → formal/pilot/oracle別のterminal status表を追加する。

10. `s2-plan-output.md:96-107` / `s8b_holdout_freeze.py:817-820` / `holdout_freeze.json:620-624` / `docs/decisions.md:15567-15573` → `confirmed_by`と`confirmed_at`は非空文字列として記録されるだけで、人間の身元・承認を機械証明しない → 「確認者欄が存在」と「人間lockstepが完了」を分離し、human receiptの有無を未確認として扱う。

11. `task-requirements.md:8-10` / `s2-plan-output.md:139-150,196-213` → planは「single exact submission commandはない」と述べるが、blocker tableに専用行がない → 「正式H1/H2 exact commandは現時点で未成立。既存CLIは部品・pilot用で実行禁止」と明示する。

禁止事項違反（approval bytes生成、正式実験起動、結果推測）は確認できません。コード変更・commit・pytest実走も行っていません。

## 総括

誤り・欠落は11件。  
最重要は、g10を発効済みと扱えないこと、v2 candidate producer不在という誤断定、D555後のjudge/floor状態の未整理。  
加えて、重複確認・所有者確認・artifact実在性・停止条件・exact commandの記録が不足しています。