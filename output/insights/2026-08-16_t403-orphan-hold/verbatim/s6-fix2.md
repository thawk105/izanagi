## 1. must-fix A / B 対応表

| must-fix | 判定 | 根拠 |
|---|---|---|
| A — sidecar 起動ゲート | `partial` | fresh / resume 共通ゲートを [mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2596) に追加。判定不能も停止し、path・`reason.hold_error`・復旧順序を [mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2411) で表示する。production 経路テストも追加したが `rc=16` で未実走。 |
| B — wrapper の sidecar 分類 | `partial` | hold または sidecar の fail-closed 判定を [mutation_worktree.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:616) に実装。通常経路は同 file:1173、fallback は同 file:1239 から使用。production 経路テストは追加済みだが未実走。 |

`regressed` と判定した項目はない。ただし pytest 未実走のため `closed` とは申告しない。

## 2. 変更した file と関数、実装内容

- [tools/mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2407)

  - `_orphan_stop_gate_message` を追加。
  - `main` に `<out>.orphan-stop.json` の fresh / resume 共通起動ゲートを追加。
  - `_orphan_recovery` を hold と sidecar の両方を手動削除する案内へ更新。
  - sidecar・hold の自動削除や自動解除は追加していない。

- [tools/mutation_worktree.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:616)

  - `_path_present_fail_closed` を追加。
  - `_orphan_hold_present` を container 内 hold または外部 sidecar の OR 判定へ拡張。
  - `_print_preserved_resume` の復旧案内に sidecar の手動削除を追加。
  - `_should_teardown` の署名・実装は変更していない。

- [test_mutation_harness.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_mutation_harness.py:635)

  - resume、fresh、sidecar `lstat` 判定不能の3負例を追加。
  - runner 呼出し数、hold 不在、sidecar 非改変、復旧順序を production `main` 経路で固定。

- [test_mutation_worktree.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_mutation_worktree.py:662)

  - sidecar-only の通常経路と plan-only fallback を追加。
  - container 保全、`failure="orphan-hold"`、teardown 未試行、復旧案内順序を固定。
  - hold / sidecar 不在時の正常 teardown 正例を同 file:740 に追加。

## 3. 触った各関数の変更前後の受理・拒否挙動

| 関数 | 変更前 | 変更後 |
|---|---|---|
| `mutation_harness.main` | sidecar 単独の fresh / resume を受理し、runner 起動へ進み得た | sidecar が存在、または `lstat` 判定不能なら runner 前に拒否。sidecar 不在時は従来どおり |
| `_orphan_stop_gate_message` | 新規 | sidecar path、読めた場合の `reason.hold_error`、指定された復旧順序を返す |
| `_orphan_recovery` | hold の手動削除まで案内 | hold と sidecar の両方の手動削除まで案内 |
| `mutation_worktree._path_present_fail_closed` | 新規 | `FileNotFoundError` だけ False、その他の `OSError` は True |
| `_orphan_hold_present` | container 内 hold のみ成立 | container 内 hold または `<out>.orphan-stop.json` で成立 |
| `_print_preserved_resume` | hold の削除だけ案内 | 復旧順序の最後に hold と sidecar の手動削除を案内 |

`_should_teardown` は未変更であり、`orphan_hold=True` なら常に拒否、False なら従来の plan-only または terminal `{0,1}` を受理する。

## 4. 実走した test node と rc

実走した pytest node はない。次の8 selectorを `tools/run_tests.py` 経由、`--force-dispatch` なしで投入したが、runner が自動 dispatch を選択後、`qstat -Q preflight rc=1` により全体が `rc=16` で終了した。

- `test_resume_rejects_orphan_stop_sidecar_before_runner_without_hold`
- `test_fresh_rejects_orphan_stop_sidecar_before_runner_without_hold`
- `test_orphan_stop_sidecar_lstat_error_rejects_before_runner`
- `test_normal_run_uses_cumulative_replacements_and_full_failed_line`
- `test_orphan_stop_sidecar_preserves_container_and_receipt_without_hold`
- `test_plan_only_exception_fallback_preserves_sidecar_only_container`
- `test_dispatch_without_hold_or_sidecar_tears_down_as_before`
- `test_orphan_hold_preserves_container_and_wrapper_receipt_between_observation_points`

したがってすべて「実装済み・未実走」。

その他の検査結果:

- `git diff --check`: `rc=0`
- 4 file の AST / NFC 検査: `rc=0`
- `python3 tools/check_codex_agents.py`: `rc=0`
- `python3 tools/check_docs.py`: `rc=0`

## 5. 波及可能性の静的列挙

- harness のゲートは runner mode や plan-only に依存しないため、sidecar が残る限り fresh / resume の全起動を拒否する。
- wrapper の共有分類関数を拡張したため、通常経路と fallback に加え signal 時の復旧案内にも sidecar が反映される。
- sidecar の判定不能も保全側へ倒れるため、storage 障害時は teardown より container 保全を優先する。
- 通常 ledger v4、wrapper receipt v1、dispatch receipt v2、`job_may_remain is True`、F47、qdel 経路は変更していない。
- 既存 hold file 単独の停止条件と `_should_teardown` の契約は維持している。

## 6. 実装できなかった項目と理由

- pytest 実測は Pegasus dispatch preflight の `rc=16` により未実走。raw pytest や `--force-dispatch` では迂回していない。
- M13 / M14 の変異 matrix 実走・事前登録更新は親の担当かつ許可4 fileの外なので実施していない。
- 指定 HEAD は `2f6e1af9` だったが、実環境はその直上の docs commit `f7be0346`。許可4 fileが両 commit間で不変であることを確認して作業した。
- docs 編集および commit は行っていない。差分は指定された4 fileだけ。

## 総括

must-fix A/B と対応する production 経路テストは実装済みです。  
sidecar-only 状態は fresh / resume と wrapper の通常・fallback の全対象経路で fail-closed になります。  
既存 schema、F47、qdel、`_should_teardown` は変更していません。  
pytest は dispatch infrastructure の `rc=16` により未実走のため、判定は A/B とも `partial` です。