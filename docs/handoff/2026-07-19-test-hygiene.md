# テストスイート衛生 — 確定所見 3 種の後始末 + 調査結果の正本化

- 目的: 2026-07-19 のテストスイート調査 (read-only) で確定した所見の反映。1 セッション規模
- 状態: 中断
- 最終更新: 2026-07-19
- 基準コミット: d4cbf91 (調査時点の HEAD。着手時に HEAD を再確認し、並行セッションの変更で行番号がずれていたら関数名で再特定する)

## 着手条件 (満たすまで拾わないこと)

- 並行開発セッションの終了 (このプラン 3 ファイル以外の handoff が空 + git status クリーン)
- ユーザーの着手 GO (実行順は A=本ファイル → B=backlog-triage → C=backlog-guard-mechanism の提案。裁定待ち)

## 完了した中間成果

- 調査は完了済み・編集ゼロ。要旨: スイートは健全 (1573 収集 / 66 秒 / 重複疑い・恒真・skip 常態化はほぼ白)。
  確定所見のみ以下に列挙。急増の機序分析は本タスクの正本化 (下記 1) に含めて記録する

## 未完の作業と次の一手 (具体的に)

1. **調査報告の正本化**: 調査結果 (増加機序: 7/14-18 の 5 日で +23,000 行、84% が feat 同梱、テスト/実装比 0.74 一定
   / 所見一覧 / 施策 9 件うち棄却 2 件 = 比率目標化・フル CI 化) を `output/insights/2026-07-19_test-suite-hygiene-survey.md`
   に保存する。worklog にはポインタのみ
2. **確定重複 1 組の統合**: `orchestrator/tests/test_s8b_selector_freeze.py` の
   `test_selector_basis_ignores_floor_budget_but_binds_variant_entries` (調査時 :468) を削除する。
   直後の `test_selector_basis_preimage_is_versioned_and_backward_compatible` (:484) が逐語上位集合
   (floor/budget 除外 + binding 束縛の同一アサートを含む) であることは調査セッションが検算済み。
   吸収先 docstring に統合の旨を 1 行明記
3. **弱テスト 10 件の強化** (「妥当入力で例外なし」だけの型。戻り値の内容アサートを 1〜2 個ずつ追加し、
   各アサートは一度わざと壊して赤を確認してから戻す — 恒真でないことの実証):
   - test_between_run_floor.py `test_between_run_floor_admission_passes_when_no_competitor`
   - test_execution_guard.py `test_assert_machine_pin_accepts_matching_env_tag`
   - test_p3_s4_loop.py `test_value_literal_consistency_accepts_match`
   - test_s8b_ratified_verify.py `test_transition_gn_to_gn1_allows_floor_change_unit`
   - test_s8b_ratified_verify.py `test_manifest_mode_100755_accepted_when_g_h_worktree_match` (isinstance のみ)
   - test_s8b_verdict.py `test_off_stock_check_accepts_valid_static_default`
   - test_s8b_oracle_manifest.py の `_snapshot(...)` / `_validate_run_contract(...)` 呼びのみ 4 件 (調査時 :359,363,374,508)
4. **契約 pin テストの明記**: test_s8b_oracle_driver.py
   `test_layer3_strict_consumer_accepts_optional_bench_wall_s` の docstring に「schema JSON の契約 pin であり
   実装コードは通らない」旨を追記 (削除はしない — 唯一の optionality pin)
5. 完了検査: `python3 tools/run_tests.py` 全緑 (1549+ passed / 0 failed 維持) + `python3 tools/check_docs.py`。
   worklog 1 エントリに吸収して本ファイルを削除

## 落とし穴・気づき

- 発火条件付き施策 (ratified_verify の git fixture 共有化はスイート 3 分超で発火 / カバレッジ観測のみ導入 /
  差分 mutation の監査標準化) は**ここではやらない** — 2026-07-19-backlog-triage.md の台帳更新で
  「忘れない」側に登載する
- commit まで。push/PR はユーザー引き渡し (Pegasus 規約)
- 3 の強化は「テストを弱める方向でない」ことをレビューしやすいよう、追加アサートのみ・既存アサートは触らない
