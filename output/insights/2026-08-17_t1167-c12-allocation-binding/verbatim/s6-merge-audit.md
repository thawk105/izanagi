## 総括

競合は main 側の 2 テストを残し、HEAD 側だけが持っていた検査を統合して解消しました。

- `test_repository_candidate_tip_binds_current_decider_version_without_activation` は削除しました。main 側テストが freeze validity、commit、reason、`effective is False` まで包含していたためです。
- ただし HEAD 固有だった `_load_freeze_record(..., expected_generation=...)` と型付き record の `schema_version` / `decider_version` 検査は落とさず、`test_repository_tip_binds_current_decider_version_without_activation` へ統合しました。[test_s8c_preregistration_invariant.py:165](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:165)
- 落とした assert は 0 件です。
- `@CANDIDATE_XDIST_GROUP` は tip テストだけに付き、g4 履歴テストには付かないことを AST でも確認しました。[test_s8c_preregistration_invariant.py:164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:164) [test_s8c_preregistration_invariant.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:197)

自動 merge 面の監査結果です。

- `rg -n --fixed-strings 's8c-decider/v1' orchestrator` を全件取得した結果は 2 件でした。現行 tip を v1 と仮定する誤った箇所は 0 件です。
  - g4 の歴史事実を固定する正当な literal。[test_s8c_preregistration_invariant.py:237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:237)
  - 拒否対象 `s8c-decider/v1/extra` の不正形式 fixture。[test_s8c_preregistration_core.py:1497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_core.py:1497)
- 現行 `DECIDER_VERSION` は v2 のままです。[s8c_preregistration.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration.py:50)
- C12 は allocation binding を先に判定し、不合格なら `allocation-enforcement-consumer-absent` を返してから environment gate へ進みます。[s8c_preregistration_evidence.py:564](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration_evidence.py:564) [s8c_preregistration_evidence.py:582](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration_evidence.py:582)
- activation の判定器版 reason は C12 reason と別フィールドで計算され、`effective` は freeze、版一致、全条件の conjunction です。[s8c_preregistration.py:1733](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration.py:1733) したがって g5 後は `decider-version-match` と C12 の allocation 不成立が同時に成立し、main 側の `effective is False` と矛盾しません。[test_s8c_preregistration_invariant.py:191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:191)
- 縮小後の evidence contract hash は、core テストの固定値 `6944…f29` と一致しました。[test_s8c_preregistration_core.py:1153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_core.py:1153)
- predicates の gap 台帳も C12 を allocation reason として固定しており、縮小後契約と一致しています。[test_s8c_preregistration_predicates.py:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_predicates.py:109)

M3 の reason precedence を production snapshot に依存させないため、allocation と environment が同時に欠ける fixture を追加しました。allocation reason が先に返ることを直接固定します。[test_s8c_preregistration_predicates.py:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_predicates.py:486)

世代 literal は次の分類です。

- 本体コードに「現行 tip は g4」と仮定する literal はありません。freeze namespace を列挙し、`validation.generation_number + 1` で次世代を求めています。[s8c_preregistration.py:1849](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/campaign/s8c_preregistration.py:1849)
- 実 repository 向け literal は、g1 の歴史 pin、g3→g4 の歴史的性質、legacy g1〜g3 の可読性検査です。[test_s8c_preregistration_core.py:1159](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_core.py:1159) [test_s8c_preregistration_invariant.py:197](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:197) [test_s8c_preregistration_invariant.py:240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:240) いずれも g5 発行後も真です。
- core 内のほかの g1〜g3 literal は一時 repository に履歴形状を作る fixture です。現行世代の前提ではありません。
- candidate tip テストは `report.freeze_generation` を使うため g5 を自動追随します。[test_s8c_preregistration_invariant.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:173)
- よって実装子が直す世代 literal はありません。親へ返す作業は指定どおり g5 の生成・`output/` 反映だけです。

4 変異の検出根拠は次のとおりです。

- M1 `read_binding` を必須集合から削除: `check_reservation` だけ残した fixture で helper が `None` を返すため、期待する UNSATISFIED tuple の assert が発火します。[test_s8c_preregistration_predicates.py:464](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_predicates.py:464) [test_s8c_preregistration_predicates.py:480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_predicates.py:480)
- M2 `check_reservation` を必須集合から削除: reservation check を bypass した C12 negative control が terminal undefined へ進み、`UNSATISFIED` と allocation reason の両 assert が発火します。[test_s8c_preregistration_predicates.py:590](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_predicates.py:590) [test_s8c_preregistration_predicates.py:650](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_predicates.py:650)
- M3 allocation gate を environment gate の後ろへ移動: 追加した両欠落 fixture が environment reason を先に受けるため、allocation reason の assert が発火します。[test_s8c_preregistration_predicates.py:499](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_predicates.py:499)
- M4 `DECIDER_VERSION` を v1 へ戻す: g5 の v2 record と current constant の一致 assert、続く `decider_version_matches is True` が発火します。[test_s8c_preregistration_invariant.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_invariant.py:187) 加えて、core の生成 record を v2 と固定する assert も v1 退行を検出します。[test_s8c_preregistration_core.py:2057](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1167-c12-allocation-binding/orchestrator/tests/test_s8c_preregistration_core.py:2057)

弱める必要がある箇所はなく、assert の削除・緩和・skip・xfail は行っていません。pytest と git 操作は指示どおり未実施です。静的確認として、`orchestrator/` 全 Python の AST parse 成功、Python/JSON 内の競合 marker 0 件、g3/g4 の指定 3 hash 同一と g4 の schema v2・decider v1 を確認しました。