## 所見

**RA1 — nit — `tools/check_branch_landed.py:1356`、`s4-adjudication.md:68`**
成果物への影響：M6 の主担当登録が実際の到達経路と一致せず、そのままでは変異 matrix が検出能力を過大表示する。
修正案：段 4 の留保どおり M6 単独を登録から外し、理由を「any-path は matched / not-matched を返すか例外を伝播するため」と記録する。

author の判断は正しい。`_find_object_any_path` の timeout は `_regular_decision` 到達前に最上位へ伝播する。**M5 を併用しても当該分岐には到達しない**。再照準するなら、同関数内で timeout を `SearchResult("truncated", …)` に変換する変異と、`any_path.incomplete` を負判定へ落とす変異の組合せは到達可能。ただし新規 test は前者単独でも decision の reason／proof phase の違いで赤になるため、後者の検出実績とは区別する必要がある。

**RA2 — nit — `orchestrator/tests/test_check_branch_landed.py:1086`**
成果物への影響：`remaining() > 1.0` 単独では、実際に subprocess に渡された timeout が 0.05 秒だったことまでは検証できない。
修正案：捕捉した `TimeoutExpired.timeout` が `pytest.approx(0.05)` であることも確認する。

現実装では直後に `min(command_timeout, remaining)` を通り、実例外も確認するので十分に強い試験である。ただし wrapper の検査と内部の残余取得は別時点であり、厳密な上限帰属には上記 assertion が適する。must-fix ではない。

**RA3 — backlog — `tools/check_branch_landed.py:1920`、`:1940`**
成果物への影響：観測待機の延長で終端 ref 確認が予算切れになる逆向きを未集計のままでは、上限変更による確定率改善を評価できない。
修正案：段 4 が指定した親の実測報告で observations／ref_snapshot の timeout 件数を区別し、逆向きの回帰試験追加は別途扱う。

この経路は理論上成立する。今回の定数だけの変更に、その再現 test を必須追加する必要はない。親の実測件数を提出する義務は残るが、射影資料にはその結果がなく、未実施とは断定できない。

その他の検査結果：

- 全ハンクを確認。製品変更は **定数 1 行＋コメント 2 行**。指定された受理述語、最上位 except、`min(command_timeout, remaining)` は byte 単位で変更なし。CLI・retry・基盤・全体予算・探索・gate・台帳の変更もない。
- 偽 git は例外注入ではなく、本物の `subprocess.TimeoutExpired` を起こす。`delayed=False` も同じ selector／委譲経路を通り、履歴の exact-state 証拠と closed-world 負証拠をそれぞれ確認する。
- selector は現在の固定 fixture では正しい。`-c VALUE` の読み飛ばしは subshell 内なので元の引数を保存する。一般化すると `--` より後のファイル名が `--find-object=` で始まる場合を誤分類し得るが、今回の `f`／`unique.txt` では発生しない。
- `exec sleep 2` は shell を置換するため、timeout 時に sleep 自体が kill・回収される。通常経路で 2 秒の終了待ちは残らない。
- `_assert_exact_unit` は witness・mode・type・OID・決定的証拠まで照合しており再利用は妥当。既存 test の削除・期待値緩和はない。
- delayed=True は proof 中に脱出するため `negative_paths` は初期値 `[]` のまま。`branch_delete_authorized` も初期値 `False` から変更されず、両 assertion は成立する。

## 変異帰属の検算

以下は**静的な赤予測**であり、変異実走結果ではない。略号：

- **U**：`test_git_run_real_command_timeout_is_truncated`
- **B**：`test_command_timeout_default_is_bounded_and_bound`
- **A[p]**：`test_assess_real_log_timeout_is_indeterminate_not_a_verdict[p]`

| id | 変更後 test で赤になる node | 段 4 の主担当との一致 |
|---|---|---|
| M0 | なし。コメントのみなので SURVIVED 期待 | 一致 |
| M1 | U、A[True-proof-path-log]、A[True-any-path-find-object]。U は例外不発、A は `timeout_causes` 不一致で赤 | 一致 |
| M2 | U、A[True-proof-path-log]、A[True-any-path-find-object]。それぞれ outcome／proof phase が不一致 | 一致 |
| M3 | B。既定値 5.0 と定数 30.0 が不一致 | 一致 |
| M4 | B。61.0 が全体予算 60 を超える | 一致 |
| M5 | A の delayed=True 2 node、および下記既存 node 群 | 一致 |
| M6 | なし。新規・既存とも当該 incomplete 値の生成経路なし | **不一致。登録撤回条件に該当** |
| M7 | `test_history_scan_limit_is_indeterminate_and_measured` | 一致 |

M5 の既存検出先：

- `test_global_timeout_is_indeterminate_json`
- `test_global_exception_marks_the_active_phase`
- `test_batch_validates_all_rows_before_accepting_match`
- `test_batch_failure_never_becomes_negative[command-timeout-False]`、`[deadline-False]`、`[parse-False]`
- `test_batch_invalid_stdout_is_indeterminate` の全 10 parameter node
- `test_missing_branch_or_commitish_has_dedicated_indeterminate_issue`
- `test_branch_named_like_abbreviated_sha_is_fail_closed`
- `test_closure_limit_preserves_observed_measurements`
- `test_max_files_makes_changed_files_unknown`
- `test_shallow_repository_is_indeterminate`
- `test_replace_ref_is_indeterminate`
- `test_nonempty_grafts_file_is_indeterminate`
- `test_custom_replace_namespace_is_indeterminate`

段 4 の M6 parameter 表記は順序も逆で、実際の node suffix は `[True-any-path-find-object]`。

## GO / NO-GO

**GO（レビュー対象差分）** — must-fix はなく、timeout から偽 verdict を作る変更もない。M6 の登録整理と親の実測による値の確定は残る。

## 総括

受理述語と scope は維持されている。
実 timeout と証拠による verdict の対は成立する。
M6 単独の検出不能という author の判断は正しい。
親ログの `102 passed in 5.18s` を確認したが、受入全走・変異実走の証拠とは扱わない。
レビュー側で pytest は実行していない。