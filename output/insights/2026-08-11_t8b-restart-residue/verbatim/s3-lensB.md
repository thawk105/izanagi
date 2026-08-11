## 総括

静的検査のみ。R-4(B) の verified calibration loader 利用と `build_v2` manifest 比較方針は整合するが、T-747 の attempt 実測値が比較対象から抜け、現時点で実際に発火する本番経路も示されていない。A-1 の変更範囲なら legacy cache は変わらないが、実装前に以下を解消すべきである。

1. [severity: blocker] [攻撃シナリオ: shell が記録した attempt の compiler/cmake 値 A と、`build_v2` が観測した manifest B が異なっても、計画は B しか検査しない。A は job-result や floor campaign に渡らず、T-747 の照合が成立しない]
   [根拠 brief.md:8-10, brief.md:44-52, tools/pegasus/floor_campaign.sh:769-778, tools/pegasus/floor_campaign.sh:970-1005, out-plan.md:17-22] [提案: attempt artifact の正確なパス・IDを campaign に渡し、calibration authority・attempt 実測値・`build_v2` manifest の三者を比較して run/job に束縛する。範囲外なら実装ではなく裁定パッケージへ戻す]

2. [severity: blocker] [攻撃シナリオ: official 経路は W-1 の無条件拒否と shell の `--mode official` 固定で `build_cells()` に到達せず、既存の floor attempt path / measurement ID もないため、追加 gate が本番で一度も発火しない]
   [根拠 brief.md:20-26, brief.md:44-47, orchestrator/campaign/s8b_floor_campaign.py:213-217, orchestrator/campaign/s8b_floor_campaign.py:3562-3579, tools/pegasus/floor_campaign.sh:961-964, out-plan.md:17-22] [提案: W-1/W-2 まで A-2 を設計メモに留めるか、既存の pilot artifact path・measurement IDを具体的に指定して「最初に発火する呼出し」を明記する]

3. [severity: must-fix] [攻撃シナリオ: 実装者が指定された package.md を裁定材料として読むと T-747=(a) の contract field 追加を選び、brief/plan の T-747=(B) と異なる contract hash・受理集合を生成する]
   [根拠 brief.md:8-10, output/insights/2026-08-11_t8b-restart-integration/package.md:18-24, docs/phase3-8b-restart-runbook.md:193-197, out-plan.md:124-142] [提案: package.md に「旧裁定・superseded」と明記し、T-747(B) を正本とするリンク・日付を追加する。成果物影響は contract hash と certified selection 境界の相違]

4. [severity: must-fix] [攻撃シナリオ: consultation の full-pipeline pilot は既知 workload の試し測りだが、実装上の `pilot` は freeze の全 cell を列挙する floor pilot であり、別 toolchain を試す pilot を同じ gate で拒否する。さらに pilot の `build_fn` は caller 注入可能である]
   [根拠 output/insights/2026-07-16_s8b-floor-protocol-consultations.md:173-182, output/insights/2026-07-16_s8b-floor-protocol-consultations.md:228, orchestrator/campaign/s8b_floor_campaign.py:2763-2802, orchestrator/campaign/s8b_floor_campaign.py:3514-3579, out-plan.md:124-129] [提案: floor pilot と operational/full-pipeline pilot を別モード・別成果物に分け、binding gate の適用対象を明示する。成果物影響は pilot の B_total 測定を過剰拒否し、floor の certified selection を増やせない]

5. [severity: must-fix] [攻撃シナリオ: gate は通過しても `build_cells()` が toolchain manifest を built record・portable manifest・journal・result に保存しないため、後続の report/ledger はどの authority と照合して受理された binary か再検証できない]
   [根拠 orchestrator/campaign/s8b_floor_campaign.py:172-176, orchestrator/campaign/s8b_floor_campaign.py:1121-1135, orchestrator/campaign/s8b_floor_campaign.py:1292-1315, orchestrator/campaign/s8b_floor_campaign.py:2440-2546, out-plan.md:131-139] [提案: 少なくとも cell ごとの manifest SHA と authority/calibration_ref SHA を durable artifact に保存し、consumer schema も同時更新する。成果物影響は certified binary の受理理由が材料レポート・試行台帳に残らない]

6. [severity: must-fix] [攻撃シナリオ: runbook を「既定は gcc/g++ 11.4.0」と無条件訂正すると、登録済み2 calibration の標本を Pegasus 全 compute node の現在値と誤認する。別の正本は compute に g++-12 があると記述しており、次回実測で gate が正しく拒否しても運用者が誤った期待値を持つ]
   [根拠 docs/phase3-8b-restart-runbook.md:50-59, docs/pegasus-runbook.md:619-625, output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:29-61, output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:29-61] [提案: 「登録済み g1/g2 calibration では 11.4.0 を記録」と限定し、現在の node default は実測値で確定すると書く。成果物影響は floor の実行可否と calibration authority の選択を誤る]

7. [severity: should] [攻撃シナリオ: manifest は configure/build 前に取得されるため、同一 realpath の compiler が build 中に差し替わっても、authority に一致した古い manifest のまま binary が受理される]
   [根拠 orchestrator/campaign/buildcache.py:648-662, orchestrator/campaign/buildcache.py:701-779, out-plan.md:5-7, out-plan.md:77-88] [提案: post-build の compiler identity/hash を取得するか、少なくともこの時間窓を運用上の前提として明記する。成果物影響は manifest と実際の floor binary の対応を保証できない]

8. [severity: should] [攻撃シナリオ: `silo_ladder_rung1` が既に calibration の compiler path/version を独自比較しており、新 module と抽出・version 正規化規則がずれると、silo artifact と s8b floor artifact が異なる toolchain を受理する]
   [根拠 orchestrator/campaign/silo_ladder_rung1.py:3518-3589, orchestrator/campaign/calibration_verify.py:81-159, orchestrator/campaign/pegasus_floor_scoping.py:77-104, orchestrator/campaign/buildcache.py:246-266] [提案: 共通 pure helper または cross-consistency test を追加する。既存 scoping/attestation は別責務なので単純再利用はしない]

A-1 は、`s8b_floor_campaign.py` の call site に限定する限り `buildcache.cache_key` と legacy caller を変更しないため、既存期待値は原則維持できる。`test_build_site_gate.py:302-309`、`test_campaign.py:8323` 付近、slow canary の `test_s8b_floor_campaign.py:2574,2617` は変更対象にしない。

NO-GO — blocker 1, 2。