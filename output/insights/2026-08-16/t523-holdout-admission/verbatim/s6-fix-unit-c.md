# fix Unit C 報告

## 1. 赤ごとの対応表

| 赤 | 状態 | 対応 |
|---|---|---|
| F-C1 | partial | `rr79` / `rr23` へ全置換を復元。元 assert を逐語復元し、実 holdout literal は元と同じ各3件だけ。正式 pytest 未実走。 |
| F-C2 | partial | private core 専用の中立表解決 seam を追加。exact 一致、authority、claim、ledger、ticket、identity は維持。正式 pytest 未実走。 |
| F-C3 | partial | test authority が既に正規化済みの test protocol を使用するよう修正。rank 14 用に test durable-root policy 配線も補完。正式 pytest 未実走。 |
| F-C4 | partial | `_run()` / `__main__` harness を追加。正式 pytest 未実走。 |

`regressed` はありません。正式 pytest が infrastructure rc=16 で collection 前停止したため、`closed` は主張しません。

## 2. 変更した file と要点

- [holdout_observation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/holdout_observation.py:152)
  - production 公開 leaf と private な中立表差替え leaf を分離。
  - production 既定値は現行 `_NEUTRAL_PROTECTED_SIGNATURES` のまま。
- [s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_holdout_admission.py:595)
  - 公開 reservation API と private core を分離。
  - 解決済み中立表を reservation、cell、ticket 発行まで保持。
- [s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_floor_campaign.py:4217)
  - `_run_campaign_core` に private `_holdout_signature_source` を追加。
  - public `run_campaign` からは到達不能。
- [test_s8b_floor_campaign.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_s8b_floor_campaign.py:385)
  - 合成 fixture を `rr79` / `rr23` へ復元。
  - test authority の historical registry 誤使用を除去。
  - public 到達不能 meta-testと実 proof-chain testを追加。
- [test_s8b_holdout_admission.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_s8b_holdout_admission.py:562)
  - 自走 harness を追加。
- [test_holdout_observation.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/tests/test_holdout_observation.py:425)
  - 差替え表でも exact signature 一致が必須である負例を追加。

## 3. F-C2 の解決 seam

`_run_campaign_core(..., _holdout_signature_source=...)` が差し替えるのは、中立な保護 signature 表だけです。

必ず実行されるもの:

- freeze 由来集合と与えた表の exact 一致検査
- Git HEAD の canonical protocol／freeze authority 検査
- `O_EXCL` cell claim
- admission ledger
- attempt ticket marker／attempt ledger
- token identity capability 検査

公開 `run_campaign`、公開 `reserve_floor_holdout_observations`、公開 `protected_signatures_from_verified_freeze` のいずれにも差替え引数が無いことを meta-test で固定しました。

## 4. 実走したテスト / 実走できなかったもの

正式 pytest は次の2範囲を `tools/run_tests.py` 経由で投入しました。

- `--force-dispatch`:
  - `test_s8b_floor_campaign.py`
  - `test_s8b_holdout_admission.py`
  - `test_holdout_observation.py`
  - `test_plain_runner_coverage.py`
- 焦点6 nodeid:
  - 元 schedule assert
  - seam 到達不能
  - synthetic proof chain
  - rank 1 resolver 赤
  - exact signature 負例
  - plain runner coverage

両方とも `qstat -Q preflight rc=1`、runner rc=16で collection 前停止しました。正式に実走した pytest nodeid は0件です。

限定 direct 診断では以下を確認しました。

- 一次ログの floor campaign 赤15関数: 全件 `DIRECT_OK`
- synthetic seam: claim 12件、admission ledger 12行、ticket marker 96件、attempt ledger 96行
- canonical authorityから `run_once` までの実 proof chain: `DIRECT_CANONICAL_E2E_OK`
- schedule、public 到達不能、exact 負例、plain runner coverage
- AST、NFC、結合文字不在、`git diff --check`
- `check_codex_agents.py`: 成功
- `check_docs.py`: 違反なし

direct 診断は pytest 緑には数えていません。

## 5. 事前登録変異の位置

- M4: [s8b_holdout_admission.py:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/campaign/s8b_holdout_admission.py:384)
  - old: `flags = os.O_WRONLY | os.O_CREAT | os.O_EXCL`
- M6: [holdout_observation.py:176](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/holdout_observation.py:176)
  - old: `if derived != _NEUTRAL_PROTECTED_SIGNATURES:`
- M7: [holdout_observation.py:371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t523-holdout-admission/orchestrator/holdout_observation.py:371)
  - old:
    ```python
    _consume_holdout_observation_run_once(
        admission,
        expected_signature=signature,
    )
    ```
- M1 / M2 / M3 / M5 / P1: 不変。

## 6. 所有外への波及可能性

- `test_s8b_freeze_io.py` と `test_s8b_ratified_freeze.py` は private core の consumer。seam 未指定時はproduction 中立表を使うため既存経路を維持。
- `test_s8b_holdout_admission.py` の各 fixture は公開 reservation APIを使用し、公開 signature は不変。
- `calibrator/runner.py` の `run_once` 分類はproduction 中立表のままで、合成 seam の影響外。
- `test_plain_runner_coverage.py` は新 harness を検出する consumer。
- Unit A/B 由来の所有外変更 `runner.py`、`backoff_profile.py`、`test_ccbench_spawn_sites.py`、`test_s8b_freeze_io.py` は保持し、本巡では編集していません。

## 7. 未完・申し送り

- Pegasus dispatch infrastructure rc=16のため正式 pytest は未実走です。
- 親で同じ4 file範囲を `--force-dispatch` 再走してください。
- docs、所有外 file、commitには触れていません。
- [T-524] / [T-525] は実装していません。

## 総括

F-C1〜F-C4の修正は所有範囲内へ実装済みです。  
合成 fixture は `rr79` / `rr23` へ戻り、元 assert も復元しました。  
private seam は中立表だけを差し替え、全 admission proof chain を維持します。  
一次ログの16赤は限定 direct 診断で再現範囲すべて通過しました。  
正式 pytest はdispatch rc=16のため未実走であり、全項目をpartialと報告します。