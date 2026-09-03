## 総括

指定された 3 source と独立 prereg data file のみを変更し、commit は作成していません。

主な修正:

- scratch は実行時の source `HEAD` を解決し、独立した `.git` と disk bytes を同じ commit へ固定。
- baseline/prototype の双方が実 issuer → attempt 発行 → assembly → consumer 経路を通る構成へ変更。
- 認証拒否、既存 gate 拒否、受理、ABORTED を区別。
- 39 組の完全性、期待一致、非後退結果が揃わない限り decision を生成しない。
- 独立した [mutation-prereg.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/output/insights/2026-09-03_t2103-producer-auth-layer/mutation-prereg.json) を追加。
- 実 route 診断では raw POS-1、R-P baseline、D-P frozen prototype が期待どおり動作。

変更ファイル:

- [p3_b4_producer_auth_experiment.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/campaign/p3_b4_producer_auth_experiment.py)
- [p3_b4_rogue_producer_support.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/tests/p3_b4_rogue_producer_support.py)
- [test_p3_b4_producer_auth_experiment.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/orchestrator/tests/test_p3_b4_producer_auth_experiment.py)
- [mutation-prereg.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2103-fix1/output/insights/2026-09-03_t2103-producer-auth-layer/mutation-prereg.json)

## 所見ごとの対応表

| 所見 | 状態 | 根拠 |
|---|---|---|
| F0 | closed | 固定 `BASE_COMMIT` を廃止。source HEAD を実行時解決し、scratch の HEAD、index、object store、archive bytes を同一 commit へ固定。report に commit を記録。現 HEAD `3e6fe8d97ec104e2bfa86125b3af33a319bf5bd1` で `core.py` の HEAD blob と disk bytes の一致を診断確認。 |
| F1 | partial | `run_isolated_cases` は全 13×3 組で baseline と prototype を必ず呼ぶ。失敗時は既定観測値で埋めず ABORTED。ただし全 78 走は pytest dispatch 障害により未実走。 |
| F2 | closed | probe が実 attempt artifact 201 件を発行してから assembly するよう変更。raw POS-1 実 route は認証拒否・既存拒否とも false を確認。非認証拒否を受理へ潰さない。 |
| F3 | closed | `existing_gate_rejected` の case 名による合成を削除。実 R-P baseline が `evidence_binding:source_rederivation` を返すことを確認。 |
| F4 | closed | R は separate-path rogue producer が planned attempt artifact を置換。D は assembly 後の raw analysis bytes のみを書き換える。R-P と D-P を別経路で実診断。 |
| F5 | closed | harness は固定 repo-relative prereg file を必須入力とし、欠落時は `PreregistrationError`。trust anchor、13 case の exact bytes、投入位置、matrix、採否規則を完全比較。 |
| F6 | closed | 欠測、重複、ABORTED、期待不一致、base commit 不整合、非後退欠測を先に検査。該当時は `decision_available=false`、leader 空。直接診断で各条件を確認。 |
| F7 | partial | 候補別非後退結果を decision/report に束縛し、赤候補を除外する実装と test を追加。候補別 29-node 実走は dispatch 障害により未実走。 |
| F8 | closed | scratch 不可時の `pytest.skip` を全廃し、assertion failure に変更。測定ゼロの成功は不可。 |
| F9 | closed | baseline/prototype 各 phase の subprocess、assertion、I/O、scratch 例外を case-local ABORTED に変換し、残りを継続。 |
| F10 | closed | production file 数を issuer/raw/frozen=`2/2/4` に修正。共有 runtime experiment module の加算理由も report に記録。 |
| F11 | closed | R/D を contextual judgment projection の exact old/new bytes として登録。rogue producer が各実対象で出現数 1 と変更対象 field の単一性を検査。P/T/C の直接診断済み。 |
| F12 | partial | W01-W08 の適用可能な exact mutant、対象 node、8-node failing-set calibration test を追加。W09 は mutant なしの正例。exact anchor 一意性は診断済みだが、8 mutant の pytest calibration は未実走。 |
| F13 | closed | 裁定 §2.12 の 7 非保証を明示的な文章として report に収録。指定された一般化不能条件と frozen の射程を名指し。 |
| F14 | closed | ABORTED reason は phase と例外型だけに正規化し、例外文字列や絶対 path を report に入れない。 |

## 実走した node と結果

正式な pytest node は実走できませんでした。`tools/run_tests.py` を通した以下の 2 走はいずれも `qstat -Q preflight rc=1`、rc=16、`child_started=false` で、collection/test child が起動していません。

- `orchestrator/tests/test_p3_b4_producer_auth_experiment.py --collect-only`
- 次の軽量 5 node:
  - `test_expected_matrix_has_twelve_negative_cases_and_pos_1`
  - `test_comparison_report_is_canonical_and_has_no_volatile_payload`
  - `test_wave_mutation_node_mapping_is_complete_and_one_to_one`
  - `test_w06_only_c1_and_r_are_decision_inputs`
  - `test_non_regression_failure_excludes_candidate_from_decision`

実装済み・未実走:

- `test_full_baseline_and_prototype_comparison_in_external_scratch`: 78 phase 走、39 result。
- `test_candidate_enabled_producer_29_node_non_regression[...]`: 3 candidate。
- W01-W08 mutant calibration: 8 mutant × 8 登録 node。
- 親が赤を観測した 4 node 全て。

pytest 外の実 route 診断:

- raw POS-1 prototype: 216.0 秒、受理。
- raw R-P baseline: 84.5 秒、既存 `evidence_binding:source_rederivation` 拒否。
- frozen D-P prototype: 135.6 秒、認証拒否・既存拒否ともなし。
- prereg、decision fail-closed、report、exact replacement などの軽量直接診断は通過。
- `git diff --check` 通過。

## 赤の内訳

現在のコードに対する pytest assertion failure は観測していません。pytest child 自体が起動していないため、緑とも報告しません。

- infrastructure failure: 2 走
- return code: 16
- 原因: `qstat -Q preflight rc=1`
- test child: 未起動
- queue_state: ENA/STS/待ち数/実行数が観測不能

親が記録した既存の 4 赤は、F0 の固定 commit 問題を修正済みですが正式再走はできていません。

## 受理・拒否挙動の変更点

- raw POS-1 は attempt artifact が揃い、assembly が実際に成功した場合だけ受理扱いになります。
- `producer_auth_mismatch` 以外の拒否を受理へ変換しません。
- R は全 candidate の実 route で既存 source rederivation 拒否として観測され、候補の増分 KILL に数えません。
- D は assembly 後の raw judgment だけを変更し、R と同じ投入位置にはしません。
- scratch 不可、欠測、例外、期待不一致は成功やゼロ KILLではなく、赤または ABORTED になります。
- 非後退が赤の candidate は leader になりません。

## 修正できなかった所見

既知の実装上の未修正はありません。

ただし、次の検証は infrastructure failure により未完了です。

- F1: 13×3 の全 baseline/prototype 実走。
- F7: 3 candidate の 29-node 非後退実走と report 束縛の実測。
- F12: W01-W08 各 mutant の failing node 集合が厳密に 1 件であることの pytest calibration。
- 親の 4 failed node の正式再走。