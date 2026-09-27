### 現行挙動

変更前は、marker のある source について BEGIN〜END の block と END 直後の epilogue を照合し、BEGIN より前の bytes は読んでいませんでした。そのため、提示された R4/R5/R7 差分は受理されました。source 不在と marker・skeleton token のない source も受理していました。

### 変更

`abort()` 宣言から BEGIN 行頭直前までを、骨格のみ、または宣言行直後に tally を挿入した形の2形で照合するようにしました。定数は pin 原文・骨格 patch・tally patch の bytes から作成しました。既存の三分岐、block・epilogue 照合、呼出し元、テスト期待値は変更していません。commit は作成していません。

| ファイル | 追加 / 削除行 |
|---|---:|
| [axis_trigger_gating.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/campaign/axis_trigger_gating.py:28) | 57 / 0 |
| [build_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/campaign/build_admission.py:91) | 27 / 11 |
| [test_build_admission.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/tests/test_build_admission.py:741) | 110 / 1 |
| [test_buildcache_v2.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/tests/test_buildcache_v2.py:5698) | 4 / 1 |
| [test_campaign.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/tests/test_campaign.py:6245) | 3 / 1 |
| [test_reflux_campaign_issuer.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/tests/test_reflux_campaign_issuer.py:174) | 22 / 4 |

合計 **241変更行**で、上限450行以内です。

### テスト

追加した関数は `test_trigger_axis_rejects_mutated_abort_prefix`（`R4-gate-pass-type`、`R4-reason-reset`、`R5-return`、`R7-flags-shadow`、`R7-backoff-shadow`、各移設版4件、`tally-slot-return`）、`test_trigger_axis_accepts_tally_abort_prefix`、`test_trigger_axis_accepts_bytes_before_abort_declaration`、および prologue・tally・pin 原文の独立照合3本です。

関数を直接呼ぶ smoke 確認では、独立照合3件、正例2件、負例10件、既存 admission 正例4件が通りました。これは pytest 実走の代わりには数えていません。

### 検査

- `python3 -m py_compile`：所有6ファイルで成功。
- `g++ -std=c++17 -fsyntax-only`：合成 fixture が `BACK_OFF=1`、`BACKOFF_TRIGGER_GATING=1`、`TRACE=0/1` の両方で成功。
- `git diff --check`：問題なし。
- `python3 tools/run_tests.py -n 1 orchestrator/tests/test_build_admission.py`：qstat preflight で `rc=16`、子テストは未起動。**実装済み・pytest 未実走**です。

### 波及

所有外の production caller は `pipeline.py`、`buildcache.py`、`p3_s4_loop.py`、S8a/S8b 系など、`derive_build_admission`・`require_build_admission` を使う箇所です。新定数の所有外での直接参照は見つかりませんでした。制約メタテストでは `test_acceptance_schedule_order.py::test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` が新 nodeid により coverage を下げますが、閾値への到達は未実走です。`test_growth_test_holds_contract.py` の collection 固定と `test_check_docs.py` の inventory 検査も確認し、今回の追加名を直接要求する箇所は見つかりませんでした。

### 変異の位置

| 変異 | 位置 | 落ちる見込みのテスト |
|---|---|---|
| M1 検査削除 | [build_admission.py:216](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/campaign/build_admission.py:216) | R4/R5/R7・tally slot の負例 |
| M2 prologue のみ照合 | 同上 | 移設版4件・`tally-slot-return` |
| M3 tally 形削除 | [build_admission.py:96](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/campaign/build_admission.py:96) | `test_trigger_axis_accepts_tally_abort_prefix` |
| M4 宣言前まで比較 | [build_admission.py:216](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/campaign/build_admission.py:216) | `test_trigger_axis_accepts_bytes_before_abort_declaration` |
| M5 tally slot を任意 bytes 化 | [build_admission.py:98](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/campaign/build_admission.py:98) | `tally-slot-return` |
| M6 prologue コメント変更 | [axis_trigger_gating.py:76](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/campaign/axis_trigger_gating.py:76) | prologue ↔ patch 独立照合 |
| M7 head コメント変更 | [axis_trigger_gating.py:28](/work/1/SFC/tanab/izanagi/.codex/worktrees/t1068-author/orchestrator/campaign/axis_trigger_gating.py:28) | head ↔ pin 原文独立照合 |

## 総括

指定された6ファイルに plan v2 を実装しました。  
受理形は骨格のみと骨格＋tally の2形です。  
R4/R5/R7 の提示形・移設形と tally slot の負例を追加しました。  
独立照合と合成 C++ fixture の構文検査は通過しました。  
pytest は dispatch 前に失敗したため、受入結果は未確認です。  
変更は未 commit のままです。