## 所見ごとの対応表

採用された実装項目はすべて **closed** です。参照略号：

- L＝[p3_s4_loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-fix2/orchestrator/campaign/p3_s4_loop.py)
- G＝[b5_generator_contrast.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-fix2/orchestrator/campaign/b5_generator_contrast.py)
- R＝[b5_generator_contrast_report.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-fix2/orchestrator/campaign/b5_generator_contrast_report.py)
- J＝[b5_contrast_launch.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2797-unit-fix2/tools/pegasus/b5_contrast_launch.py)

| 所見 | 状態 | 対応・file:line |
|---|---|---|
| A1 | closed | 候補拒否 sidecar、rc 3、whiteboard 非投影、A-only 継続。L:1945、G:297 |
| A2 | closed | verify 環境故障の retry、上限後は score=None・fallback 無し。G:55、G:776 |
| A3 | closed | 起動前の durable attempt 記録と未終端 sidecar 集計。G:586、R:308 |
| A4 | closed | 2 評価目以降の両入力に診断必須。G:449 |
| A5／B03 | closed | 全 handshake 終了枝の待機記録、opportunity 単位の集計。G:639、R:353 |
| A6／B02 | closed | certified fitness と bench median の一致検査。R:244 |
| A7／A8／A9／A10 | closed | 裁定どおり変更不要。既存契約を維持 |
| A11 | closed | 登録 1000 重み表・独立固定 vector。`test_b5_generator_contrast.py:706` |
| A12 | closed | 探索品質欠測の件数表示、score 品質欠測との対照。R:398、R:414 |
| B01 | closed | 終端 B と評価件数・連番を照合。R:294 |
| B04 | closed | 投入済み論理数・試行論理数・物理数・前処理拒否数を分離。R:393 |
| B05 | 未対応 | 裁定で親担当の文書修正。J:78 の Git 読取りは維持 |
| B06 | closed | 投入対象 checkout の PIN 行を読む。J:99 |
| B07 | closed | LLM CLI の K2 3 引数を必須化。G:859 |
| B08／B09／B10／B11 | closed | 裁定どおり変更不要 |
| B12 | closed | WAL 計時重複、未使用 baseline、env 二重構築を除去。G:369、R:117、J:203 |
| B13 | 未対応 | 裁定で親担当の README 修正 |

変更不要・親担当の根拠は [s6-adjudication.md:21](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2797-b5-contrast/s6-adjudication.md:21) 以降です。

## 変更の要約

指定 **8 ファイルだけ**に未 commit の差分を残しました。

候補拒否と機械故障を分離し、中断時の投入済み予算を report に反映しました。retry 中の allocation 枯渇でも、消費済み B に対応する評価記録を保持します。台帳の件数・数値検査を追加し、許可された TR fixture を 10 評価へ是正しました。

既存の検査意図と M0〜M19 対応テストを維持しています。新契約に合わせた診断入力・対象 PIN fixture・イベント参照位置の追従も行いました。

## 新 test 一覧

| 変異 | 独立した kill test |
|---|---|
| M20 | `test_b5_candidate_rejection_sidecar_rc3_m20` |
| M21 | `test_rejected_sidecar_advances_without_retry_m21` |
| M22 | `test_verify_machine_retry_and_exhaustion_m22` |
| M23 | `test_attempt_start_durable_before_runner_exception_m23` |
| M24 | `test_incomplete_attempt_sidecar_consumes_budget_m24` |
| M25 | `test_one_evaluation_cannot_claim_B10_m25` |
| M26 | `test_fitness_median_mismatch_invalid_m26` |
| M27 | `test_both_critic_diagnoses_required_m27` |
| M28 | `test_target_checkout_pin_m28`／`test_validate_submit_tree_rejects_ccbench_pin` |

**M20〜M28 の全 9 変異をメモリ上に注入し、対応テストによる kill を実走確認しました。**

追加で、固定生成 vector、handshake 全 5 出口、K2 部分指定拒否、retry の B 重複防止、A-only の session 除外、探索／score 品質欠測の対照を検証しています。

## 実走結果

指定コマンドで実行しました。`::*` は当該ファイルの全収集 nodeid です。

| 対象 | 最終結果 | rc |
|---|---:|---:|
| `test_b5_generator_contrast.py::*` | **107 passed** | 0 |
| `test_b5_generator_contrast_report.py::*` | **67 passed** | 0 |
| `test_b5_contrast_launch.py::*` | **38 passed** | 0 |
| `test_p3_s4_loop.py::*`（指定 pytest 全件） | **585 passed** | 0 |
| `test_official_perf_closure.py`（plain harness 全件） | **7 passed** | 0 |
| `git diff --check` | 通過 | 0 |

合計 **804 件通過**。初回に検出した新規 fixture 不整合と非文字列 preflight 拒否の問題は修正し、再実走済みです。

## 未了・懸念

- B05／B13 の文書対応は親担当として残しています。
- 実機 qsub・build・bench、実際の親との handshake は未実施です。
- M0〜M19 対応の既存テストは維持・実走しましたが、全変異の再注入は今回行っていません。

## 総括

fix2 の採用実装、追加変異検証、指定 5 系統の実走を完了しました。差分は指定 8 ファイルのみ。commit・staging・job dir への書込みは行っていません。