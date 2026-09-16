## 変更した file と差分の要約

変更は指定の4 file のみ、173行追加・3行削除です。

- `orchestrator/campaign/condition_meaning_gate.py`: registry に2 entry 追加のみ。
- `orchestrator/campaign/s2_verify_calibration.py`: `declaration=None` の1箇所を factory 呼出しへ変更。
- `orchestrator/tests/test_condition_meaning_gate.py`: 対象 macro 追加、未登録例の差替え、正例2件追加。
- `orchestrator/tests/test_s5_permutation_coverage.py`: S2 の静的配線検査と consumer test 4件追加。

`git diff --check` は成功。commit・禁止された Git 操作は実行していません。

## 単位 A: registry と TG

NOREAD、HIGHKEY の順で registry と `_COMPILE_TIME_BRANCH_MACROS` に追加しました。未登録例は TRIGGER_MISATTR に差し替え、期待値は維持しました。

新正例は ADD_ANALYSIS 未定義の toy TU で、実 patch の前処理構造を再現しています。実 supply・meaning・family により、以下を確認しました。

- supply と meaning が指定 reason code で green。
- requested は `("1", 1, 1)`、default は `("0", 0, 1)`。
- admission は True、未確立一覧は空。

domain test、一意性・非識別・完了 marker・factory 条件は変更していません。

## 単位 B: S2 と T5

S2 の factory 宣言を meaning evaluator へ配線しました。capture の configure 引数、supply、signature、`raw-measurement` は維持し、`configured_commands` は追加していません。

consumer test は実 request と実 factory を使い、同じ captured/request/declaration の伝達、TRACE 設定、family 引数、受理時の返却 dict、拒否時の RuntimeError を検査します。compiler 呼出しはありません。

## 実走結果 (nodeid と結果、未実走の列挙)

指定の `PYTHONPATH=. python3 -c "...pytest.main(...)"` で実行しました。skip はありません。

| 範囲 | 結果 |
|---|---|
| TG、指定の `-k 'compile_time_branch or registry_macro or domain_and_claim or unregistered_macro or nonpaired'` | **32 passed、92 deselected、10.71秒** |
| T5 全体 | **12 passed、2.47秒** |

主要 nodeid（TG/T5 は上記 test file の略記）:

- `TG::test_compile_time_branch_selection_accepts_each_registry_macro[...]`: registry 全14 macro が成功。
- `TG::test_compile_time_branch_selection_accepts_else_with_nested_analysis[IZANAGI_BREAK_NOREAD_VALIDATION]`: 成功。
- `TG::test_compile_time_branch_selection_accepts_else_with_nested_analysis[IZANAGI_BREAK_HIGHKEY_VALIDATION]`: 成功。
- `TG::test_compile_time_branch_registry_and_fixtures_are_bound_to_real_patches`: 成功。
- `TG::test_compile_time_factory_keeps_unregistered_macro_unestablished`: 成功。
- `TG::test_compile_time_factory_rejects_nonpaired_values[...]`: 全4件成功。
- `TG::test_v1_domain_and_claim_boundaries_are_exact`: 成功。
- `T5::test_s2_condition_gate_passes_factory_declaration_to_meaning_evaluator[True-IZANAGI_BREAK_NOREAD_VALIDATION]`: 成功。
- 同 `[True-IZANAGI_BREAK_HIGHKEY_VALIDATION]`、`[False-IZANAGI_BREAK_NOREAD_VALIDATION]`、`[False-IZANAGI_BREAK_HIGHKEY_VALIDATION]`: 成功。

TG の重複指令・非識別・完了 marker 等の既存負例も指定範囲で成功しました。

未実走は TG 残り92件、所有外 consumer 回帰、受入全走、§5 の変異 matrix、実機 S2 走行です。

## 波及可能性の静的列挙

repository 内の Python 参照を検索しました。

- **`CONDITIONAL_BRANCH_WITNESSES`**: 宣言型の検証、factory、供給の共有 build root 選択・整合検査、meaning record の宣言照合、公開 export。test consumer は TG の fixture helper・registry 束縛・非識別負例と `test_mocc_proof_surface.py`。
- **`MEANING_SUPPORTED_MACROS`**: meaning record の対応集合検査、公開 export、TG の domain 境界検査。対応集合は13→15、未対応は25→23。
- **`_COMPILE_TIME_BRANCH_MACROS`**: TG の registry 順序一致・patch 束縛 loop・各 macro 正例の parametrize・domain 期待集合。
- **`s2._require_condition_gate`**: production caller は `_preflight_condition_gates` と `_broken_build_and_verify`。直接 test consumer は T5 の静的配線検査と新 consumer test。S2 module を参照する `test_build_site_gate.py`、`test_ccbench_spawn_sites.py`、CLI 登録を検査する `test_p3_build_authority_cli.py` も回帰対象。
- **所有外 caller**: gate CLI は既存 factory 配線から自動追随。S3、S5、MOCC、write-intent、S1、paper-story A2 の既存 factory caller は既存 macro の条件を維持。screening は対象2 macro の route 不一致による拒否を維持。
- **共有 fixture**: `condition_gate_test_support.py` は未変更。TG の新 macro も既存 fixture を利用します。共有 fixture を使う build-site、探索 namespace、screening、S8b、A2、sort oracle 等への波及は、親の回帰・受入全走で確認する範囲です。

registry 登録により、2 macro の供給内部は既存の共有 build root 分岐へ移ります。供給・意味間で compile command を共有する保証は追加していません。

## 未完・懸念

実装と指定焦点走は完了しています。§5 の M0〜M7 の SURVIVED/KILLED 判定は未実走で、親の後続検証へ引き継ぎます。

実 patch 適用後の CCBench TU、masstree `config.h` の供給、実機 S2 JSON の未確立一覧縮小は未検証です。toy の成功は動的到達性や positive control の実行時発火を証明しません。

## 総括

変更前は2 macro の factory が None を返し、meaning は unestablished のため、supply が green なら admit するコード上の状態でした。変更後は factory 宣言によって枝選択を検査し、成立時は green で admit、枝が選ばれなければ red で reject します。

指定4 file の実装を完了し、焦点44件が成功しました。差分は未commitで残しています。