## 現行の受理・拒否挙動

候補 commit の freeze は valid、g4 は schema v2 かつ現行 `DECIDER_VERSION` と一致します。一方、§5 と12条件が未充足なので `effective=False` のまま拒否されます。テストのみの変更で受理集合は変えていません。

## scope

編集したのは [test_s8c_preregistration_invariant.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1250-decider-version-generation/orchestrator/tests/test_s8c_preregistration_invariant.py:165) だけです。production、docs、output は編集せず、commit も作成していません。親所有の docs 差分と g4 は維持しています。

## 実装内容

追加した関数は次の2つです。

- `test_repository_tip_binds_current_decider_version_without_activation`
  - `repository_candidate_commit` と `@CANDIDATE_XDIST_GROUP` を使用
  - freeze valid、schema、record/report の判定器版一致、reason code、未発効を固定
  - `"HEAD"` は直接渡していません

- `test_generation_4_changes_revision_procedure_without_changing_condition_contract`
  - 作業ツリーの世代3・4を固定して比較
  - 4種類の条件契約 hash と12個の条件 hash の継続性を固定
  - normative/protected hash の変更、g3実bytesとの supersedes 関係、D458、schema、判定器版を固定

64桁の literal hash は追加していません。legacy parametrize は `(1, 2, 3)` のままです。

## 静的確認

- `git diff --check`: 成功
- `py_compile`: 成功
- g3/g4診断比較:
  - 継続対象4項目: すべて同一
  - 条件 hash: 両世代とも12件
  - normative/protected hash: いずれも相異
  - g4 supersedes: g3実bytesのSHA-256と一致
  - g4: D458、schema v2、`s8c-decider/v1`
- 制約 meta-test:
  - 既存ファイルなのでテストファイル集合への追加不要
  - pytest-only allowlistへ登録済み
  - `WAVE_REQUIRED_PATHS`へ登録済み
  - `REAL_REPO_SERIAL_NODES`追加不要
  - xdist group名は既存golden登録済みで、新規groupなし
  - fixture consumerは既存candidate group内に閉じています

期待赤の事前集合は空です。両テストとも未commitの親成果物をcandidateまたは作業ツリー経由で観測します。

## 実走

pytestは未実走です。次の2新設nodeと2種類のmeta-testを `tools/run_tests.py` 経由で投入しましたが、Pegasusの `qstat -Q` が認証エラーとなり、dispatch infrastructure failure `rc=16` で停止しました。テストnodeは1件も実行されておらず、緑またはclosedとは扱いません。

runnerが生成した一時dispatch receipt一式は削除し、残存させていません。

## 波及可能性

- `repository_candidate_commit` のconsumerが1件増え、同じcandidate xdist groupの実行時間に影響します。
- `activation_report_at` 経由でfreeze履歴、core/evaluator/projectionのblob一致、判定器版を消費します。
- `_load_freeze_record` とg3/g4作業ツリー成果物へ依存します。
- 既存candidate連鎖テスト、未発効テスト、holdout scan、plain-runner coverage、xdist collection auditが関連consumerです。

## 残る懸念

親による焦点pytest、collection meta-test、変異M01〜M05、受入全走が未実施です。キュー認証または実行環境の復旧後にrunner経由で確認が必要です。

## 総括

指定された2関数を対象テストファイルだけに実装済みです。静的検査は整合していますが、pytestはPegasus dispatch障害のため未実走です。