静的レビュー結論: must-fix 7 件、should-fix 3 件です。pytest は未実走です。

1. [severity: must-fix] [攻撃シナリオ: `verify_floor_bytes` を呼ばずに `judge` → `publish_result_table` を実行できる。検証例外を無視しても publish 用 token が無い] [根拠 `orchestrator/campaign/s8c_result_judge.py:901`, `orchestrator/campaign/s8c_result_judge.py:1013`, `orchestrator/campaign/s8c_result_judge.py:1187`] [提案: 床値を含まない検証 receipt/token を `publish_result_table` が必須入力として要求し、失敗時は publish 不可にする。mutable な共有 state は使わない。]  
成果物影響: 未検証 floor のまま `official_status` 表・selection 表が生成され、後続で certified 選択の受理集合へ混入する。

2. [severity: must-fix] [攻撃シナリオ: observation の値を任意に改変し、`correctness_gate_passed=True`、`certified=True`、`trace_enabled=False` を付けると gate 通過として採用される] [根拠 `orchestrator/campaign/s8c_result_judge.py:349`, `orchestrator/campaign/s8c_result_judge.py:359`, `orchestrator/campaign/s8c_result_judge.py:427`] [提案: 真偽値の自己申告ではなく、raw observation bytes に束縛された信頼側の gate attestation を必須にする。]  
成果物影響: 任意の raw 値から対差・`official_status`・結論を成立側へ動かせる。

3. [severity: must-fix] [攻撃シナリオ: `manifest["source_binding"]` を省略し、caller が作った frozen params に小さい `delta_min` と大きい `sd_max` を入れる。source binding 不在が一致扱いになり、観測後の閾値差し替えが通る] [根拠 `orchestrator/campaign/s8c_result_judge.py:67`, `orchestrator/campaign/s8c_result_judge.py:198`, `orchestrator/campaign/s8c_result_judge.py:841`, `orchestrator/campaign/s8c_result_judge.py:927`] [提案: manifest の binding 欠落を必ず判定不能にし、params は ratified manifest 由来の provenance token だけ受理する。commit 束縛を bundle 送りにする間は C07 を発効させない。]  
成果物影響: 対比の `official_status` と全体結論が UNSATISFIED から SATISFIED へ反転する。

4. [severity: must-fix] [攻撃シナリオ: on/off cell の `configuration_id` を同じ値にし、prediction では異なる `cell_id` を渡す。`same_prediction` は文字列比較なので、同一構成でも C3 が成立する] [根拠 `orchestrator/campaign/s8c_result_judge.py:245`, `orchestrator/campaign/s8c_result_judge.py:263`, `orchestrator/campaign/s8c_result_judge.py:659`, `orchestrator/campaign/s8c_result_judge.py:760`] [提案: holdout 内の canonical configuration ID を一意にし、prediction は canonical ID に正規化してから同一性を判定する。]  
成果物影響: 同じ構成の比較でも C1/C3 と結論が SATISFIED になり、公式性能表の受理集合が広がる。

5. [severity: must-fix] [攻撃シナリオ: cells が不正で holdout 集合が空のとき、空の mapping を渡すと C1 は UNSATISFIED、C2 は空ループの初期値 `True` から SATISFIED になる] [根拠 `orchestrator/campaign/s8c_result_judge.py:503`, `orchestrator/campaign/s8c_result_judge.py:571`, `orchestrator/campaign/s8c_result_judge.py:611`, `orchestrator/campaign/s8c_result_judge.py:925`] [提案: holdout が空、または完全 cell block が無い場合は三条件すべてを INDETERMINATE に固定する。空集合に `any` や空ループの真値を適用しない。]  
成果物影響: 判定不能な入力から条件別の SATISFIED 証拠が生成される。現状の結論は C3 により INDETERMINATE だが、条件別 consumer の受理値が汚染される。

6. [severity: must-fix] [攻撃シナリオ: `_evaluate_c07` は validator の戻り値を未使用の変数へ代入しても消費済みと認定し、条件・cell set・table bytes との実 data flow を検証しない。floor field も literal を置くだけでよく、`load_ratified_freeze` の呼出しや verify→judge→publish の連結を要求しない] [根拠 `orchestrator/campaign/s8c_preregistration_evidence.py:1866`, `orchestrator/campaign/s8c_preregistration_evidence.py:1972`, `orchestrator/campaign/s8c_preregistration_evidence.py:2015`, `orchestrator/campaign/s8c_preregistration_evidence.py:2083`, `orchestrator/campaign/s8c_preregistration_evidence.py:2137`] [提案: 戻り値が実際の condition map / staged bytes に到達する SSA 相当の検査、exact helper と引数の検査、ratified loader と entrypoint chain の検査を追加する。]  
成果物影響: C07 を将来発効する際、謳うだけの validator でも readiness を通り、未検証の result table が正式系列の受理集合へ入る。

7. [severity: must-fix] [攻撃シナリオ: 3 表目の書込み中に二つ目の write が失敗する、または process が中断する。rollback の unlink 失敗は握り潰され、先に作った表だけが残る] [根拠 `orchestrator/campaign/s8c_result_judge.py:1205`, `orchestrator/campaign/s8c_result_judge.py:1215`] [提案: 単一 transaction directory と atomic completion marker で公開し、rollback 失敗を成功扱いにしない。]  
成果物影響: descriptive/official/selection の部分表だけが残り、レポートと台帳の参照集合が 6 cell 完全集合でなくなる。

8. [severity: should-fix] [攻撃シナリオ: 正常な swapped prediction は swap 元 holdout の configuration ID だが、selection table は対象 holdout だけを検索するため `predicted_rank=None`、`prediction_matches_rank=False` になる] [根拠 `orchestrator/campaign/s8c_result_judge.py:854`, `orchestrator/campaign/s8c_result_judge.py:866`, `orchestrator/campaign/s8c_result_judge.py:870`, `docs/phase3-8b-descriptor-design.md:494`] [提案: swapped mapping の source holdout を selection row 生成へ渡し、source 側の順位と照合する。]  
成果物影響: 結論は変わらなくても、独立 selection evaluation 表の swapped 行の順位・整合性値が誤る。

9. [severity: should-fix] [攻撃シナリオ: `test_c2_boundary_list_is_documented` と `test_c3_and_c4_boundary_catalogues_are_present` は実装を呼ばず、`test_floor_bytes_or_floor_value_cannot_change_judge_result` は floor を judge へ渡さず、`test_publish_cell_missing_extra_duplicate_leaves_no_table` は書込み前に失敗する。C07 の dead assignment、loader 非呼出し、decoy 誤読も検出しない] [根拠 `orchestrator/tests/test_s8c_result_judge.py:209`, `orchestrator/tests/test_s8c_result_judge.py:546`, `orchestrator/tests/test_s8c_result_judge.py:587`, `orchestrator/tests/test_s8c_result_judge.py:655`, `orchestrator/tests/test_s8c_preregistration_predicates.py:882`, `orchestrator/tests/test_s8c_preregistration_predicates.py:918`, `orchestrator/tests/test_s8c_preregistration_predicates.py:928`, `orchestrator/tests/test_s8c_preregistration_predicates.py:944`] [提案: 実装 mutant、publish 二段目失敗、dead assignment、loader 呼出し除去、宣言 path に存在する decoy を追加する。]  
成果物影響: 受入が緑のまま false gate を land し、後続 wave の正式 result table 受理を誤って許す。

10. [severity: should-fix] [攻撃シナリオ: 親報告の「C3 が INDETERMINATE でも結論は UNSATISFIED」という期待値] [根拠 `docs/phase3-8b-descriptor-design.md:444`, `orchestrator/campaign/s8c_result_judge.py:892`, `orchestrator/tests/test_s8c_result_judge.py:448`] [提案: 期待値を INDETERMINATE に固定する。現在読んだ worktree の同テストは `:451` ですでに INDETERMINATE を期待しており、親の赤は別 snapshot の期待値ずれに見える。]  
成果物影響: certified 選択・レポート・台帳の値は変わらず、受入テストだけが誤って赤になる。

## 総括

- 床 bytes 検証そのものは ratified freeze 由来で、床値は現在 `judge` の結論へ再流入していない。
- ただし検証を publish の必須前提にする防壁が無い。
- gate、params、source binding、configuration identity は caller 側で偽装可能。
- 空入力では三値優先順位にも穴がある。
- `_evaluate_c07` は syntactic witness に留まり、実 data flow を保証しない。
- cell set の通常経路は厳格だが、公開の全件 atomicity は不十分。
- C07 未登録は段 4 の P1 どおりで、現時点の certified 件数は増えない。
- read-only 静的レビューのため pytest は未実走。