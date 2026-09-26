# [T-2851] 残り (2) 未知条件への転移の実行器と解析器 — 実装の記録

authority: none / default_effect: no-state-change (記録。可変状態の正本は worklog 末尾と現行 phase doc)

## 0. 何をしたか

事前登録 v1 (`docs/unseen-condition-transfer-preregistration.md`) §11「既存機構で欠ける部品」の表のうち、MOCC の参照の選定を除く 7 行と、
TPC-C 版 (`docs/tpcc-unseen-condition-transfer-preregistration.md`) §5 の置換表を、新しい 2 module に実装した (Codex author、D95)。
`orchestrator/campaign/pipeline.py` と `orchestrator/calibrator/runner.py` は呼ぶだけで編集していない。事前登録 2 本の本文 bytes も変えていない。

| §11 の行 / §5 の置換 | 実装 (`orchestrator/campaign/`) |
|---|---|
| 26 cell の展開・1 走単位の実行 | `t2851_transfer_runner.cells` (YCSB 26、TPC-C 段 s1・s2 各 12)、`run_job` (`calibrator.runner.run_once` を 1 回ずつ、`use_perf=False`) |
| 全候補の block と §5 の順序 | `order_identities` (identity 辞書順 → SHA-256 による Fisher–Yates、鍵は YCSB `t2851-order-v1|…`、TPC-C `t2851-tpcc-order-v1|<段>|…`、block は 1..32) |
| (課題, 手法, 独立探索) → identity・重複除去・凍結記録 | `freeze_candidates` (全系列の網羅と排他、学習 cell ⊆ 登録錨、binary 対応、M の算出、正規化 JSON と sha256) |
| cohort 2 の別日判定・hostname 比較・再投入 | `cohort2_admission` と `run_job` (cohort 1 の全 job 記録から最後の終了時刻と同 cell の hostname を導出、同 hostname の棄却 2 回まで・3 回目は測定して別割当て不成立、単独性違反・job 失敗は丸ごと 1 回) |
| 留保 cell の引数での検証・3 値 | `verify_candidate` (YCSB は `pipeline._run_trace` + `verifier.core.verify_trace_dir`、certified / disqualified / indeterminate、再検証は別 hostname で 1 回) |
| §9 の欠測分類と n_eff | `run_job` の使えない走 (rc≠0・例外・timeout・tps 欠落・0・非有限) と `t2851_transfer_analysis` の n_eff |
| §6 の同時区間・分類・主要表 | `t2851_transfer_analysis.analyze` (Bonferroni `t(1−0.025/M, 31)`、δ = ln(1.03) の厳密不等号 4 分類、記述区間、両 cohort 一致、勝者交代、Welch の転移差、因子別・手法別の記述、失格の全 cell・両 cohort 除外) |

測定の発効 (T-2851 残り (1)) は別の決定であり、本実装は対象探索群・候補凍結・MOCC の参照・R* を**入力として受け取るだけ**で、選定をしない。
留保 cell の `run-job` / `verify` は、発効の記録 (decision_id と凍結記録の sha256、TPC-C は段と認定経路) を受けたときだけ走り、欠ければ測定前に拒否する。
発効前なので、計算ノードで留保 cell は 1 走もしていない (smoke を含む)。

## 1. 登録文に明記が無く実装で選んだこと (発効束で確認する項目)

- block 番号の始点は 1 (1..32)。順序の鍵の `<b>` はこの値。
- 検証 status の語彙は `certified` / `disqualified` / `indeterminate` (v1 §8 の certified / 失格 / 未確定)。
- 凍結入力に `environment` (`env_tag`・`clocks_per_us`・`numactl`) と、各 identity の `trace_ccbench_root` (trace-enabled binary を compile した CCBench source の絶対 path) を必須にした。
  runner は `trace_ccbench_root` が実際の compile 元と一致することを保証しない (発効束 §13.1 の CCBench pin・patch・configure の固定で担う)。
- 実行前に凍結記録を入力 field から再生成し、派生 field (jobs・comparisons・m_by_family・sha256) を含めて完全一致を要求する。
- binary 内容の sha256 を実行時に照合する (v1 §5 の「両 cohort で同じ identity の build」の束縛。段 6 review B の削除提案は不採用)。
- M は族ごとに、cell 内で重複除去した (候補 identity, 強い参照 identity) の数 (同 identity の組を除く)。系列との対応は comparisons の `series` に保持。

## 2. 段の経過

- 段 1 brief、段 2 plan (codex)、段 3 相談 2 本 (正しさ・整合 / 過剰・削除)、段 4 裁定 (プラン v2、変異 M1〜M12 の事前登録、規模上限)。逐語は `verbatim/`。
- 段 5: 実装子 2 本 (単位 A 実行器 / 単位 B 解析器、所有 path 素集合)。
- 段 6: 敵対 review 2 本 (両 NO-GO: A/B の JSON 契約の不一致、M の系列重複、参照どうしの比較の欠落、凍結 hash の範囲、再検証回数、24 時間の導出ほか) → fix 1 巡目 →
  焦点 1 巡目 NO-GO (派生 field の保護、cohort 1 全件性、attempt 付番) + 親の所見 (clocks_per_us の暗黙依存) → fix 2 巡目 → 焦点 2 巡目 GO →
  計算ノードの生死確認で検証が certified に到達しない欠陥 (G-1) を発見 → fix 3 巡目 → 焦点 3 巡目 GO。
- fix 1 巡目の子は、本 wave 新設の test の旧期待 (拒否記録を再検証回数に数える) と R-A5 裁定の衝突で停止し、親が test の書き直しを許可して再投入した。
- 受入全走 1 回目 (tested tip dc41d40ce、main 856cdbcda 取り込み済み) の赤 3 件は本 wave に帰属: 新 module の process launch site 2 つが review 済み inventory に未分類
  (`test_ccbench_spawn_sites.py` の 2 node と `test_s8b_floor_campaign.py::test_materializer_registry_covers_all_python_build_launches`)。裁定は `verbatim/s6-ruling-4.md`。
  理由 comment 付きの追加だけで分類し (Codex author)、焦点走 (3 node + 新 test 2 本) 52 passed の後に受入を再投入した。
- 不採用: TPC-C の認定経路への接続 (F-3)。裁定時点で経路は未着地だった。2026-09-26 時点の main では `pipeline._run_trace` が TPC-C 段 1 (57:43) の trace を許すようになっている (T-2854 の着地)。
  実行器の TPC-C 検証は `indeterminate` (認定経路なし) を記録し続ける。これは certified を誤って出さない側である。接続は発効時に経路を固定する別単位とした (worklog の新規 T)。

## 3. 計算ノードでの生死確認 (錨 wh-base だけ、留保 cell なし)

使い捨て driver (repo 外、Codex author) で、YCSB Silo の R0 (上流既定 BACK_OFF=1) と R1 (B0-L-W0) を trace 無し・有りで build し、cohort 1 の 1 job (32 block) と R1 の検証 1 本、解析までを通した。

| 回 | request | wave commit | 結果 | 原因 / 所見 |
|---|---|---|---|---|
| 1 | 21333.nqsv | 16f654141 | rc=1、Elapse 13 秒 | `buildcache.build` の configure が gflags 不在。計算ノードに system の gflags/glog が無い → driver を `s3_mocc_lock_coverage._prepare_dependencies` の既存経路へ |
| 2 | 21357.nqsv | 16f654141 | rc=1、Elapse 5 秒 | driver の `ROOT = Path(__file__).parent` が repo 外退避で job dir を指した → `orchestrator` package の位置から求める形へ |
| 3 | 29210.nqsv | 16f654141 | rc=0、Elapse 351 秒 | job は成立 (下表)。**検証が indeterminate** (serializable・anomaly 0・違反件数 0 なのに clean=false) → G-1 |
| 4 | 29237.nqsv (driver sha256 `cf1ea5d0…`) | a635a8872 | rc=0、Elapse 350 秒 | 検証 certified (serializable、anomaly 0、clean) |

4 回目の job (bnode096、CCBench e9e477ca、clocks_per_us 2100): completed_blocks 32、使えない走 0、単独性は開始・終了とも成立、平均 tps R0 1,368,603.7 / R1 2,448,161.6。
3 回目の job (同 node): 32 block、使えない走 0、ln(R1/R0) の平均 0.5780 (無補正 95% [0.5693, 0.5866]、記述)、順序は R0 先 15 / R1 先 17 block。
smoke は R1 自身を選択候補にしたので R1 比は同 identity で除外され、M = 0 (設計どおり)。この値は動作確認であり、事前登録の測定ではない。

**G-1:** 実行器が `verify_trace_dir` を `ccbench_root` なしで呼んでいたため、`assess_protocol_proof_surfaces` が X/P/I 三面を unavailable にし、
`Integrity.clean()` の `certification_gate_satisfied()` が常に偽で、YCSB の検証が certified に到達できなかった。放置すれば主要表は全て判定不能になる。
review 2 本・焦点 2 巡と fixture test はいずれも検出しなかった。親が実装子 prompt で「verifier の外部呼び出しを fixture 化してよい」と許していたため、
test が認定の到達性そのもの (検査対象の機構) を通っていなかった (F649 の再発、failures fragment)。fix 3 巡目で、凍結した source root を verifier へ渡し、
実 verifier のまま最小 trace で certified / indeterminate を切り替える正例・負例 test を足した。

所要: 4 回の job Elapse 合計 719 秒 (13 + 5 + 351 + 350 秒、約 0.2 node 時間)。D2212 項 4 の確認ライン (2 node 時間) 未満。

## 4. 変異 matrix

`tools/mutation_worktree.py` (独立 clone、`--runner-mode dispatch`、対象 test = `orchestrator/tests/test_t2851_transfer_runner.py` と `test_t2851_transfer_analysis.py`) で 2 回走らせた。
期待 node は変異ごとの login self-run (注入 → 2 本を自走 → `git checkout` で復元、sha256 と `--porcelain` 空を照合) で集めた。spec と結果は job dir
`/work/1/SFC/tanab/dev-wave-jobs/t2851-transfer-runner/` の `mutation-spec-final{,-2}.json` と `mutation-final{,2}-results.json`。

| 回 | 対象 commit | spec sha256 | baseline | 結果 |
|---|---|---|---|---|
| 1 | 16f654141 (fix 2 巡目後) | `4c3ddf23b3e53aaddd39bb0535b23bbeccaf02d71d46ed22f08ab1ef7fdc2c88` | PASSED | M1〜M12 すべて KILLED、期待 node と一致 12/12 |
| 2 | a635a8872 (fix 3 巡目後) | `4eae1e2b1d658e75fae0c7f0040a7843202807716926f041c1061260c05a42c4` | PASSED | M1〜M13 すべて KILLED、期待 node と一致 13/13 |

| ID | 変異 | 検出する test |
|---|---|---|
| M1 | Fisher–Yates の `% (i + 1)` → `% (i)` | `test_order_hand_calculated_and_prefix` |
| M2 | 順序の鍵の版 v1 → v2 | 同上 |
| M3 | 既知別枠が protocol を見ない | `test_cells_and_known_separate` |
| M4 | 留保 cell の解禁検査を素通し | `test_activation_rejects_before_measurement` |
| M5 | 同 hostname の棄却上限 2 → 3 | `test_cohort_two_boundary_and_rejections` |
| M6 | 別日の閾値 24 → 23 時間 | 同上と `test_cohort_one_complete_keys_and_mixed_utc_max` |
| M7 | indeterminate を certified に写す | `test_verification_mapping` ほか 2 |
| M8 | 優越の不等号を非厳密に | `test_quantiles_and_strict_classification_boundaries` |
| M9 | Bonferroni を外す | 同上と `test_bonferroni_m_is_frozen_and_changes_interval` |
| M10 | 資格 n_eff == 32 → ≥ 24 | `test_effective_block_boundaries[31]` |
| M11 | 失格を当該 cell だけに限る | `test_disqualification_excludes_all_cells_both_cohorts_and_preserves_m` ほか 1 |
| M12 | 同 identity の組を比較に含める | `test_same_identity_excluded_even_if_frozen_as_primary` |
| M13 | verify で `ccbench_root` を渡さない | `test_verify_candidate_real_verifier_source_root_controls_certification` |

M1〜M12 はどれも G-1 (§3) の経路を対象にしておらず、1 回目が全 KILLED でも G-1 は残っていた。M13 は G-1 の fix の前に追加登録した。

## 5. 記録前の機械走査

`python3 -m orchestrator.campaign.s8b_holdout_freeze search` は rc=1。hit は rr80・rr20 とも
`output/env/pegasus/calibration/s8b-floor-official/20260916T111925Z-2c8cf9be/` の既存 3 file (journal.jsonl・manifest.json・result.json) だけで、
v1 §2.3 が「8b の floor 較正で既に測定がある」と書く既存の記録である。本 wave の file (本書・verbatim・spool fragment・新 module・test) は hit に含まれない。

## 6. 残るもの

- 測定の発効 (T-2851 残り (1)) と実施 (残り (3))。発効束には §1 の実装上の選択の確認を含める。
- TPC-C の検証を段 1 の認定経路へ接続する単位 (新規 T)。TPC-C の build 経路 (buildcache は YCSB target 固定) と単独性確認の TPC-C 版の実機確認も同じ単位。
- MOCC の参照・R* の選定は本実装の対象外 (入力として受け取る)。
