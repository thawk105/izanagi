## 変更点

- **F1:** 比較前に予定集合を固定し、比較結果の evidence と各集約鍵に属する configure から実行済み集合を作って厳密照合するよう修正しました。[検査器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/tools/check_trace0_preprocess_identity.py:1004)
- **F2:** volatile builtin の probe に限り `-Wno-builtin-macro-redefined` を追加しました。[検査器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/tools/check_trace0_preprocess_identity.py:830)
- **F3:** discovery の依存列挙を当該 protocol の production target に絞り、consumer を見つけた時点で止めます。[検査器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/tools/check_trace0_preprocess_identity.py:940)
- **F4:** header 用引数がすべて無い起動では、macro 不在検査を ancestor・diff 検査より前に戻しました。[検査器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/tools/check_trace0_preprocess_identity.py:1068)
- **F5:** 裁定どおりコード変更なし。
- **F6:** 判定 script が裁定済み C・C2′ の OID と引数を照合し、不一致なら exit 2 にしました。[判定 script](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/output/runs/t2854-hv2/judge/run_judge.sh:13)
- **F7:** 正例 fixture に `-Werror` と、TRACE token を持たず変更 header も読まない target を加えました。[test](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/orchestrator/tests/test_check_trace0_header_rule.py:70)
- **F8:** 未使用の `discovered` を削除し、production target の形式検査と正規化 root の重複をそれぞれ一箇所に整理しました。[検査器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2854-hv2-impl/tools/check_trace0_preprocess_identity.py:732)

## 自走した確認と変異の赤化確認

`orchestrator/tests/test_check_trace0_header_rule.py` の `test_discovery_only_checks_production_target`、`test_v1`、`test_v2`、`test_v3_v4_v9`、`test_v5`〜`test_v8`、`test_v10`〜`test_v12`、`test_volatile_builtin_in_expansion_is_rejected` を test 関数として直接実行し、**全12件通過、合計14.43秒**でした。F3 test は未選定 beta の discovery が production target だけを旧新 × TRACE 0/1 で調べた **8呼び出し**を確認しました。

既存の `orchestrator/tests/test_check_trace0_preprocess_identity.py` は、`test_known_absent_validation_receives_both_comparison_oids_once`、`test_modified_header_is_rejected_as_outside_checker_guarantee[.hh]`、`test_add_delete_and_rename_are_rejected_as_unsupported_status[add]`、`test_mode_change_is_rejected`、`test_non_cpp_changed_path_is_rejected`、`test_nonancestor_commit_relation_is_rejected` の6件を直接実行して通過しました。

一時変異では、**F1/V9** の最後の比較省略が予定・実行集合の不一致で赤化し、**F2/F7** の probe オプション除去が `-Werror=builtin-macro-redefined` で赤化し、**F3** の全 entry discovery 復帰が呼び出し回数の assertion で赤化しました。いずれも復元を確認済みです。`bash -n`、誤った OID に対する exit 2、`git diff --check` も通過しました。

## 未実走・懸念

実 CCBench の判定 job、計算ノード実行、CCBench 本体 build は未実走です。したがって実構成での判定は**実装済み・未実走**です。pytest は起動せず、指定された test 関数の直接実行で確認しました。

## 波及の静的列挙

所有外の caller・consumer test として、`tools/pegasus/mocc_trace_pilot.sh`、`orchestrator/tests/test_mocc_trace_pair.py`、`orchestrator/tests/test_mocc_trace_job_contract.py`、既存の `orchestrator/tests/test_check_trace0_preprocess_identity.py` に参照があります。これらは編集していません。

## 総括

F1〜F4・F6〜F8 を実装し、指定の直接実行と変異赤化を確認しました。F5 は変更せず、F9・F10 は実装していません。