## 総括

最大所見は、`p3_s4_loop._resolve_duplicate()` が未結線で、閉包は 21 module / 29 site ではなく少なくとも 21 module / 30 site です。  
次に、`test_bench_first_real_wal.py` に新 gate と両立しない旧期待値が残っています。  
さらに `test_critic.py` の改名が acceptance duration ledger に追随していません。  
以上 3 件と段 7 の docs 更新を直すまで land 不可です。私は pytest を実走していません。

## 所見

- B-01 / real / scope 内 / `orchestrator/campaign/p3_s4_loop.py:1048-1062,1573-1579`, `p3_s4_loop_sort.py:308,371,544-549`, `p3_s4_loop_trigger_gating.py:600,791-796,1083-1091` / 成果物影響: receipt が無効な既存 COMMITでも whiteboard と checkpoint に success が永続化し、後段 gate の拒否後も次 iteration の停止・選択状態を汚染できます。

- B-02 / real / scope 内 / `orchestrator/tests/test_bench_first_real_wal.py:438-440`, fixture `:68-81`, helper `orchestrator/campaign/artifact_admission.py:665-667` / 成果物影響: `build_attempt_id` も receipt もない旧実 WAL に対し `_bench_tps()` が値を返すという期待は成立せず、この node は静的には `TypeError` になります。

- B-03 / real / scope 内 / `orchestrator/tests/test_critic.py:748`, `acceptance_duration_ledger.json:4911`, `test_update_acceptance_duration_ledger.py:360-404` / 成果物影響: ledger は削除済み旧 node 名を保持し、新 node の実測時間と critic suite の exact node-set commitment が更新されていません。

- B-04 / refuted / scope 内 / `artifact_admission.py:652-735,1262-1269`, `pipeline.py:1169-1177,1453-1462`, `test_artifact_admission.py:1296-1372` / 成果物影響: 承認外の一般的過剰拒否は確認できません。no-COMMIT、非零 abort、赤 attempt 共存は受理され、現 producer は receipt を発行します。

- B-05 / refuted / scope 内 / `test_s8b_oracle_manifest.py:61-99` / 成果物影響: `s8b_oracle_report.py` の現 SHA `f7ef6259...69c93b` と、それを含む spec SHA の 2 箇所は追随済みです。他 6 file を含む旧・新 SHA の追加 literal pin は見つかりませんでした。

- B-06 / refuted / scope 内 / `t080_freeze_migration.py:874-880,1365-1381` / 成果物影響: `_KNOWN_REPIN_ROWS` は live file ではなく `migration_basis_commit` の blob を読むため、S6/S8A の今回の bytes 変更による再 pin は不要です。

- B-07 / refuted / scope 内 / `test_plain_runner_coverage.py:44-68`, `test_campaign_import_invariant.py:31-39`, `test_ccbench_spawn_sites.py:25-30,80-84` / 成果物影響: 新 test file、process spawn、絶対 sibling import は増えておらず、plain-runner、spawn、import gate への追加登録は不要です。例外は B-03 の duration ledger です。

- B-08 / refuted / scope 外 / `artifact_admission.py:42-45,652-735` と 2 commit の 19 file 差分 / 成果物影響: 新台帳、新署名主体、新 receipt schema、将来 consumer 登録、汎用 proof framework は入っていません。既存 receipt validator の再利用だけです。

- B-09 / real / scope 内 / `docs/decisions.md:40872-40880`, `docs/phase3.md:19-53`, `docs/roadmap.md:400` / 成果物影響: D1246 の実装閉包、Phase 3 の現行 checkpoint、proof-chain の persisted admission 契約が文書から追跡できません。段 7 で更新が必要です。

- B-10 / refuted / scope 内 / `test_paper_story_a2_certification.py:536-611,1405-1429` / 成果物影響: A2 fix は性能 verify 1 件を欠く COMMITを残りの evidence で再発行し、権威ある cell 2 件を保持したまま `inconclusive` と effects 空を検査しています。骨抜きではありません。

- B-11 / refuted / scope 内 / `test_s8b_oracle_report.py:650-746,3037-3048,3115-3126` / 成果物影響: `without_crashing` 系は引き続き malformed abort reason を検査し、該当経路に COMMIT はありません。receipt fixture 更新は検査対象を避けていません。

## 自分で再導出した consumer 閉包と、結線漏れ

再導出できた既結線集合は次のとおりです。

- 中央 chokepoint: 16 module / 22 site  
  `critic/digest.py:1586`、`p3_b4_closed_critic.py:740,1779`、`p3_autonomous_workload_trial.py:3088`、`s6_sort_sweep.py:520`、`backoff_extended_sweep_report.py:459`、`backoff_sweep_report.py:57`、`backoff_overthrottle.py:145`、`p3_b4_wiring_probe.py:1475`、`p3_s4_loop_sort.py:546,743`、`autonomous_trial_completeness.py:4423,4912,4959`、`p3_s4_loop_trigger_gating.py:1088`、`p3_s4_loop.py:1240,1576,1791`、`s8a_trigger_sweep.py:622`、`replay.py:184`、`layer3_report.py:685`、`p3_s4_red.py:191`。

- lock-only: 3 site  
  `backoff_requested_us.py:484-490`、`s1_report.py:352-355`、`s8b_oracle_report.py:1641-1645`。いずれも lock bytes の前後 SHA 照合があります。

- raw WAL: 4 site  
  `s6_sort_sweep.py:402-448`、`s8a_trigger_sweep.py:501-547`、`backoff_repro.py:82-118`、`paper_story_a2_certification.py:2574-2699`。

したがって裁定どおりなら 21 module / 29 site ですが、次が漏れています。

- `p3_s4_loop.py:1031-1062` の `_resolve_duplicate()`。`records_by_stage()` の COMMITだけで success、TPS、verdict を復元します。`p3_s4_loop_sort.py:308` と `p3_s4_loop_trigger_gating.py:600` が同じ関数を re-export しています。
- 中央 gate は各 driver が state を保存した後に発火するため、この raw consumer を代替できません。

よって閉包は少なくとも 21 module / 30 source-level site です。修正は共有 `_resolve_duplicate()` 1 箇所へ同一 snapshot 契約と helper を結線すれば 3 driver に届きます。

`tools/` 側では、`plot_backoff.py:269` と `plot_s1_9pair.py:562` は明示的な `HISTORICAL_RAW`、`plot_b10_extended_backoff.py:133-152` は exact frozen historical bytes の consumer です。current certified acceptance の追加漏れとは数えません。

## 既存 consumer の回帰

中央経路の Layer3、critic digest、replay、autonomous completeness、P3 各 loop は `require_admitted_campaign(...CERTIFIED_ACCEPTANCE)` を通り、現 producer の receipt 形式とも一致しています。helper の述語も D1246 の最小集合で、`commits > 0`、batch、workload exact keys などへの過剰拡張はありません。

回帰として残るのは次の 2 点です。

1. P3 duplicate resume は B-01 のとおり、中央 gate より前に状態を書き換えます。
2. `test_real_wal_backoff_repro_bench_tps_requires_commit` は旧 receiptless fixture の受理を期待したままです。親の集計結果とは静的に矛盾するため、この exact node が現 HEAD で実行されたか再確認が必要です。

## pin の追随漏れ

追随漏れは確認できませんでした。

- `s8b_oracle_report.py`: source SHA と、それを内包する `PIN_GATE_SPEC_SHA256` を更新済み。
- `s1_report.py`、`backoff_repro.py`、`backoff_requested_us.py`、`paper_story_a2_certification.py`: literal SHA pin なし。
- `s6_sort_sweep.py`、`s8a_trigger_sweep.py`: live bytes の literal pin なし。S1 golden は editable source の SHA を形だけ検査し、campaign bytes だけを literal pin しています。
- T-080 は basis commit blob を読むため追随不要です。

## fix がテストの意図を保っているかの判定

A2 は意図を保っています。対象 cell は COMMITのまま、性能 verify の反復だけが 1 件不足し、receipt は残存 evidence と一致するよう再発行されています。その結果、authority と cell は有効なまま、科学判定だけが `authoritative-workload-inconclusive:rr50` になります。

S8B の `without_crashing` 系も意図を保っています。不正な abort payload 自体は残っており、COMMITのない失敗経路なので、新 persisted-COMMIT gate を通らないことは検査の弱体化ではありません。

## must-fix と nit の切り分け

Must-fix:

1. `_resolve_duplicate()` を共通 helper へ結線し、receipt 不正時に whiteboard/checkpoint を更新しない回帰テストを追加する。
2. `test_bench_first_real_wal.py:438-440` を receipt 付き fixture に移すか、D1246 に沿った拒否期待へ変更する。
3. critic test の改名前後を duration ledger に実測値で反映し、exact suite hash を更新する。
4. 段 7 で D1246 周辺、Phase 3 checkpoint、roadmap §6 の proof-chain 契約へ実装結果と修正後の閉包数を記録する。

Nit: なし。現時点の残件はいずれも閉包、回帰、凍結台帳、正本文書に関わるため nit へ落とせません。