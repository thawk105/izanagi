## G1〜G3 の対応

- **G1: closed（実装）** — WAL の `reason` を閉じた code に正規化し、`outcome` と `verifier_digest.reason` に自由文を写さないようにしました。[driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/p3_s4_loop_policy.py:47)
- **G2: closed（実装）** — anomaly を決定的な順序で先頭 8 件に絞り、全件数を `anomaly_count` に記録します。[driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/p3_s4_loop_policy.py:244)
- **G3: closed（実装）** — `--record-reject` を追加しました。preview と同じ coder 専用入力・gate を使い、拒否だけを WAL と履歴に記録して iteration を進めます。通過候補は書込み前に `ValueError` となり、build は起動しません。入口の予算停止判定は run と同じです。[driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/p3_s4_loop_policy.py:373)

## reason の閉じた code 集合

集合は [driver](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/p3_s4_loop_policy.py:48) に定義しました。出所は次の実コードです。

- `identity-error`、`eval-exception` 接頭辞: [loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/loop.py:852)、[loop.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/loop.py:985)
- admission・build・trace・verify・bench・screen・stale-baseline の固定 reason: [pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/pipeline.py:540)、[pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/pipeline.py:1422)、[pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/pipeline.py:1882)、[pipeline.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/campaign/pipeline.py:2378)
- `non-serializable`・`indeterminate`: [verifier model](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/verifier/model.py:555)
- `diff-quarantine`: [digest.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/critic/digest.py:203)

集合外は `eval-exception: ` 接頭辞なら `eval-exception`、それ以外は `other` に写します。

## 変更した既存 test

既存 test の期待値は変更していません。[test_p3_s4_loop_policy.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2865-unit-core/orchestrator/tests/test_p3_s4_loop_policy.py:246) に G1〜G3 の test を追加しました。

## 確認の実走

`py_compile` と `git diff --check` は成功しました。追加した次の nodeid 相当の関数を**直接呼出し**で確認しました: `test_exception_reason_is_closed_before_coder_input`、`test_anomaly_digest_has_stable_first_eight_and_full_count`、`test_record_reject_records_only_real_gate_failure`、`test_record_reject_honors_budget_before_gate`、`test_record_reject_cli_uses_coder_only_input_without_build_opt_in`。**pytest は未実走**です。実装済み・未実走として親の計算ノードでの検査を待ちます。

## 変異 M-E15〜M-E17 に使える fixture と単一理由性の見立て

- **M-E15:** `eval-exception: ValueError: arbitrary private exception text` が coder 入力へ出ない test。reason 正規化だけを対象にします。
- **M-E16:** 11 件の G2 anomaly を逆順でも同じ先頭 8 件・全件数 11 と確認する test。件数上限を対象にします。
- **M-E17:** 実 `policy_gate` の通過候補で `ValueError` と無書込みを、拒否候補で実 WAL・履歴追記を確認する test。通過候補の記録禁止を対象にします。

## 所有外への波及

namespace の AST layout 呼出し数と `run_campaign` 呼出し数、caller inventory、coder entrypoint、spawn site は変わらず、追加登録は不要でした。driver は 494 行で規模上限内です。変更前の run・preview の受理／拒否条件は変えず、新 CLI の入力だけ preview と同じ閉じた形にしました。所有外のファイル、docs、output は編集していません。作業木の runbook §1(c) は現時点では旧説明のため、親が持つ docs 更新との整合確認が必要です。

## 総括

G1〜G3 を所有 2 ファイル内で実装しました。直接呼出し確認は成功、pytest は未実走です。commit は作成していません。