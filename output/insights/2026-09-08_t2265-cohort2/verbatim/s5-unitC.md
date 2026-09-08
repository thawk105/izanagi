## 実装内容

指定された unit C の4ファイルだけを編集しました。

- [cohort 2 解析器](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-c/orchestrator/campaign/backoff_counterfactual_cohort2_analysis.py)
  - schema v4、extime 6、exact 3-cell、12 seed、事前登録SHAを固定。
  - assignment-integrity checkを実装。
  - `seq = 0` の先行除外、terminalをfollowing専用化。
  - terminalを割当率、層、block、LCGから除外。
  - terminal非閉鎖とterminalの0 commitを全体の`inconclusive`へ反映。
  - TOST、実用優越、12 cluster等重み、主層はcohort 1と同一。
- [cohort 2 解析テスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-c/orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py)
  - 自走harnessを含む13 test function、17 collected caseを追加。
- [plot実装](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-c/tools/plotting/plot_dynamic_backoff.py)
  - legacy、cohort 1、cohort 2を別のexact gridとして扱うよう変更。
  - v3 policy fieldとv4 terminal field、summary、row、gridを検査。
  - extimeは旧grid/cohort 1が3、cohort 2が6の閉じた契約。
  - diagnostic値生成とfigure loopを成果物のcell orderへ追随。
  - 中間terminal、複数terminal、54-row誤認を拒否。
- [plotテスト](/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-c/orchestrator/tests/test_plot_dynamic_backoff.py)
  - cohort 1、cohort 2、figure loop、near-miss検査を追加。
  - 既存legacy A+B/A+B+Cの期待値は維持。

commit、`git add`、branch操作、pushは行っていません。

## pin

patch Cの実bytesから得たSHA-256:

```text
b5649becded2ad62d015d94263b3e4b3e32f8c271892647e6567772c234dad5f
```

取得元:

```text
/work/1/SFC/tanab/izanagi/.codex/worktrees/t2265c2-unit-c/patches/cicada-adaptive-counterfactual.patch
```

事前登録文書の実SHAも指定値`8b4127f4be895da0d25da88b0837f679ecf06d43ab656b16d2944146b9f7a9e9`と一致しました。

## 実走結果

- `python3 tools/run_tests.py orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py orchestrator/tests/test_plot_dynamic_backoff.py -q`
  - rc=16、`qstat -Q` preflight失敗。
  - `child_started=false`のためtest本体は未実走。
- `PYTHONPATH=. python3 orchestrator/tests/test_backoff_counterfactual_cohort2_analysis.py`
  - ファイル全体、17 passed。
- `PYTHONPATH=. python3 orchestrator/tests/test_plot_dynamic_backoff.py`
  - ファイル全体、30 passed。
- `PYTHONPATH=. python3 orchestrator/tests/test_backoff_counterfactual_analysis.py`
  - 変更禁止のcohort 1 test全体、25 passed。
- `PYTHONPATH=. python3 orchestrator/tests/test_plain_runner_coverage.py`
  - 3 passed。
  - 制約meta-test `test_every_test_file_is_self_runnable_or_allowlisted`が新規test fileを列挙して通過。
  - stale allowlist検査とmeta-test自己適用も通過。
- `python3 tools/check_codex_agents.py`: passed。
- `python3 tools/check_docs.py`: passed。
- `git diff --check`: passed。
- 所有4ファイルの末尾空白、U+0300からU+036F: 検出なし。

build、benchmark、性能計測、unit A/B統合後producer-consumer走行は実装済み・未実走です。

## 殺す変異

解析テストの主要な1行変異:

| test | 赤になる変異 |
|---|---|
| `test_assignment_lcg_accepts_exact_positive_sequence_and_rejects_one_bit_flip` | LCG乗数・加数・bit比較を変更、rowからLCG呼出しを削除、terminal前にLCGを進める |
| `test_seq_zero_is_excluded_before_pairing_under_cohort2` | `events[1:]`を`events`へ変更 |
| `test_terminal_flush_is_following_only_and_does_not_consume_lcg` | terminalをcurrent、割当率、membershipへ含める |
| `test_terminal_zero_commit_makes_whole_primary_inconclusive` | 0 commit走査からterminalを除外 |
| `test_missing_terminal_makes_whole_primary_inconclusive_without_replacement` | terminal欠落を拒否、run除外、または最後の通常eventで代替 |
| `test_nonterminal_events_require_count_trigger_and_count_window` | 通常eventの`time` triggerまたは1から9999 commitを受理 |
| `test_terminal_requires_one_position_at_the_end_when_present` | terminal件数または末尾検査を削除 |
| `test_exact_cohort2_cells_extime_patch_and_preregistration_are_bound` | cell、extime、patch C、top/row事前登録のexact比較を緩和 |
| `test_cohort2_literal_pins_are_independent_of_fixture_helpers` | schema、cell、patch、事前登録のliteralを変更 |
| `test_final_normal_assignment_changes_estimate_through_terminal_following_window` | 最後の通常割当とterminalの対を落とす |
| `test_tost_and_practical_superiority_constants_match_v2` | margin、t値、strict境界を変更 |
| `test_public_cohort2_analysis_uses_exact_twelve_equal_clusters` | event等重みに変更、seed集合・version・SHAを変更 |
| `test_analysis_preregistration_file_is_bound_to_literal_cohort2_sha` | 文書bytesのSHA検査を削除 |

plot追加テスト:

| test | 赤になる変異 |
|---|---|
| `test_plot_accepts_exact_cohort1_policy_grid_at_extime_three` | v3をlegacy gridだけへ戻す、policy fieldを読まない、extime 3を拒否 |
| `test_plot_accepts_exact_cohort2_grid_and_uses_artifact_cells_in_figure_loop` | global `TRACE_CELLS`で18 rowを54 row扱い、figure loopを旧cell固定、v4 fieldを捨てる |
| `test_plot_policy_grid_literals_and_field_counts_are_exact` | schema、cap、cell literal、11/12 field数を変更 |
| `test_cohort2_plot_contract_rejects_near_misses_and_nonfinal_terminal` | 中間・複数terminal、非count trigger、field欠落、policy/cap/extime/cell near-missを受理 |

既存の`test_plot_accepts_both_ab_and_abc_stacks`と`test_plot_still_accepts_existing_ab_artifacts`も全走で通過しています。

## cohort 1保持根拠

- `backoff_counterfactual_analysis.py`と`test_backoff_counterfactual_analysis.py`に対する`git diff --quiet`はrc=0。
- cohort 1 test全25件がpassed。
- plotの`TRACE_CELLS`互換alias、11-field設定、extime 3のdefault pinを保持。
- plot全30件で既存A+B、既存A+B+C、明示的cohort 1 policy gridの正例がすべてpassed。
- v4の追加は独立したschema/grid契約で、既存18-row artifactへcellを合算していません。

## 所有外への波及

静的に確認した波及候補:

- Unit B producer/PBS:
  - `tools/pegasus/probes/t2187_adaptive_const_probe.py`
  - `tools/pegasus/probes/t2187_adaptive_const_probe.pbs`
  - 実v4成果物との統合走行が必要。
- Unit A/B結合:
  - `test_dynamic_backoff_transitions.py::test_emitter_stdout_parses_with_the_real_parser`
- 共有meta-test:
  - `test_plain_runner_coverage.py`
- plotの外部consumer:
  - `tools/plotting/README.md`
  - `docs/dynamic-backoff-preregistration.md`
- 新規cohort 2解析器を直接呼ぶproduction callerは現行tree内に見つかりませんでした。

## 所有外なので触らなかったもの

- unit A所有の`patches/`と`test_dynamic_backoff_transitions.py`。
- unit B所有のproducer、PBS、各test。
- `condition_meaning_gate.py`、`screening_driver.py`と各test。新terminal define登録の波及候補ですがunit C所有外です。
- `tools/plotting/README.md`および`docs/`。文書更新は禁止かつ段6担当です。
- cohort 1解析器・test。歴史的受理集合保持のため変更禁止です。
- handoff、worklog、phase文書。単独unitの所有外です。

## 総括

実装: cohort 2専用解析、assignment-integrity、terminal following、schema別plot gridを所有4ファイルへ実装。  
実走結果: unit C解析17件、plot 30件、cohort 1回帰25件、meta-test 3件がpassed。  
残っている赤: unit C内は0件。unit A/B統合testと所有外condition registry追随は実装済み・未実走です。