## 実装

- [producer](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-unit-b/orchestrator/campaign/p3_autonomous_workload_trial.py:429)
  - 論理 cfg、attempt capability digest、q のみから 33 個の物理 cfg・preimage・identity を決定的に導出。
  - preimage、identity、不整合、重複を envelope 構築前に拒否。
  - caller から完成済み run plan / planned identity を受ける型面を削除。
  - 順序を slot 予約 → classification → ledger snapshot → 33 identity → envelope create-only → lifecycle start → observation に変更。
  - 実 envelope bytes の SHA-256 を `origin_run_plan_sha256` として lifecycle start に渡す。
  - envelope 失敗を preflight、lifecycle 後の失敗を report を持つ typed partial として分類。
  - originless では新引数を渡さない。
- [producer tests](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2293-unit-b/orchestrator/tests/test_p3_autonomous_workload_trial.py:10280)
  - 決定性、33 相異、slot digest 分離、q exact int、既存 key 上書き拒否、不整合・重複拒否を追加。
  - registry が物理 identity を拒否する負例、issuer が論理 cfg のみを受ける検査を追加。
  - create-only 失敗境界、確定順序、digest 一致、originless 引数不在を追加。

sealed executor、origin report、completion、`p3_s4_loop_trigger_gating.py` は変更していません。commit も作成していません。

## 検査

実走を試みた範囲:

- identity 関連の追加 nodeid 群
- `test_p3_autonomous_workload_trial.py --collect-only`

どちらも `tools/run_tests.py` を通しましたが、`pegasus02` からの dispatch が `qstat -Q` の socket 作成失敗で `rc=16` となり、子 pytest は未起動です。したがって実装済み・未実走であり、緑とは申告しません。

静的検査では、対象 2 file の AST parse、module import、`git diff --check` が成功し、禁止された U+0300〜U+036F は検出されませんでした。

## 残る赤と波及

- 単位 A の signature 未着地中は、実 `record_trial_start_once` を使う origin 正例 2 nodeidが `origin_run_plan_sha256` の unexpected keyword で赤になる見込みです。
- 単位 A の provenance v2 fixture 統合時は、`_align_origin_result_records` が producer 導出 identity を使うよう調整が必要になる可能性があります。
- 単位 C の `evaluate_formal_origin` 新 signature と canonical layout 検査には、既存 `_complete_origin_runtime` caller の統合確認が必要です。
- `OriginProducerInputs` 共有 fixture は materially 変更しました。tracked Python 内の他 caller はありませんでした。
- finalizer 回数・status 順序を固定する AST test と `_finish_trial` の構造は未変更ですが、行番号は移動したため再実走対象です。
- 所有外の originless compatibility、trial registry、formal consumer tests は親の統合後に回帰確認が必要です。

## 総括

- 要件 9〜11 と R1 producer 側を所有 2 file に実装しました。
- 物理 identity は構造化 `origin_campaign_run` key だけで導出します。
- caller に planned identity を自己申告させる API は削除しました。
- lifecycle start は envelope の durable write と digest 計算後です。
- originless 経路では新しい digest 引数を渡しません。
- sealed executor、要件 18、R2 は未実装です。
- pytest は dispatch infrastructure failure のため未実走です。
- 単位 A 未着地による正例 2 件の赤見込みがあります。
- 単位 A/C と共有 fixture、formal-consumer caller の統合確認が残ります。