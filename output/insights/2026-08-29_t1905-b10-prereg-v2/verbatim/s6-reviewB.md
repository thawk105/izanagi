pytest は実行していない。以下は静的検査結果であり、「緑」の申告ではない。

## 変異表

- M1 — killed by `test_schema_v3_document_is_rejected_after_v4_positive_control`:845
- M2 — killed by `test_v4_spec_including_binary_shape_is_rejected`:801
- M3 — killed by `test_physical_residual_limit_other_than_exact_one_is_rejected`:809
- M4 — killed by `test_physical_residual_deviation_exactly_at_the_limit_is_rejected`:856
- M5 — killed by `test_registration_rules_values_are_checked_exactly`:819
- M6 — killed by `test_registration_rules_values_are_checked_exactly`:828
- M7 — unkilled
- M8 — killed by `test_p06_canonical_v4_machine_spec_and_runtime_residual_are_accepted`:754
- M9 — killed by `test_probe_output_schema_and_create_only`:948
- M10 — killed by `test_p04_three_reference_points_and_full_grid_are_accepted`:1081
- M11 — killed by `test_p06_canonical_v4_machine_spec_and_runtime_residual_are_accepted`:744

根拠:

- M1: fixture の `/v4` と変異後の `/v3` はともに literal である。[test:150](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:150)、[test:844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:844)
- M4: parser は上限が exact 1.0 かと deviation の再計算一致だけを検査し、cell の 1.0 境界は拒否しない。[driver:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1051)、[driver:1142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1142)。したがって test の入力は [test:855](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:855) で runtime まで届き、`>=` は [driver:1279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1279) で直接検査される。
- M5/M6: 変異入力は key を変えないため、`_exact_object` の key 検査を通過する。[driver:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:831)。値を拒否する実体は辞書全体の exact 比較 [driver:860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:860) であり、帰属は成立する。
- M9: 正例 `/v2`、assertion `/v2`、負例 `/v1` はすべて literal で、`B.PROBE_SCHEMA` を参照していない。[test:333](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:333)、[test:948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:948)、[test:951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:951)。
- M11: 合成 fixture ではなく、`ROOT / B.PREREG_REL` から実 file を読む。[test:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:743)、[driver:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:87)。

## must-fix

- real — M7 は殺せていない。[test:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:833) は先頭行を削除するため、件数 guard [driver:1114](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1114) を除去しても、直後の順序検査 [driver:1127](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1127) が同じ `prereg-spec` を返す。runtime closure [driver:1253](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1253) には到達しない。影響: 件数 guard を消して末尾の余分な residual 行を受理する変異が、現行 suite を通過して受理集合を広げられる。
  - 代案: `physical_residual.values` の末尾へ有効な 13 行目を追加し、実体 `B.parse_preregistration()` が `prereg-spec` で拒否することを要求する。件数 guard を除去した mutant は先頭 12 行だけを parse して成功し、runtime に渡る値も 12 行になるため、前後の閉包に横取りされない。

## 恒真性と nit

- real / nit — `test_exact_finite_models_distinguish_registered_shapes_and_dormant_code2` は `B.exact_model()` を一度も呼ばず、test 内で候補列と式を再構成している。[test:1085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:1085)。奇数 multiplier の assertion [test:1090](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:1090) の後では平均 equality [test:1106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:1106) は候補集合の構成に含意される。影響: production の `exact_model()` が壊れてもこの test は通るが、formal 成果物生成では同関数を使っていないため成果物値への直接影響はなく nit。
  - 代案: inverse から作った high-bit 対を、実体 `B.exact_model()` に `B.encode(...)` および dormant literal `2000 + mean_us` とともに渡して pair sum を検査する。

- refuted — 新設した5負例、M14改名 test、dormant code 2 の C++ test は production parser、validator、または実際に compile した `EXPECTED_HOLE_LINE` を呼んでおり、上と同種の恒真性は確認しなかった。[test:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:794)、[test:667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:667)、[test:680](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:680)。影響: これらの test は対応する production 実体の変化に反応する。

- real / nit — 改名前 nodeid が `acceptance_duration_ledger.json` に残る件は、親裁定でも「赤にならない」と確定済みである。[ruling:66](/home/SFC/tanab/.claude/jobs/11513787/tmp/t1905-b10-prereg-v2/ruling.md:66)。影響: test 結果は変わらず、duration 台帳に到達不能な旧参照が残るだけである。

## 波及と既存 test

- refuted — projected test file では新規 test file はなく、5件とも既存の `test_b10_backoff_shape_sweep.py` 内に追加されている。[test:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:794)。影響: file glob の集合はこの単位では変わらず、関数名や nodeid を列挙する inventory だけが値を変えうる。
- refuted —主要な期待値は 3 Holm族、12 encoding、15 points、36 factorial cells の literal assertion として残り、期待値の反転や緩和は見つからない。[test:754](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:754)、[test:1054](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:1054)、[test:1081](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:1081)、[test:1256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:1256)。影響: projected file 内で旧21/54/6族の意味を維持する合格 test は確認しなかった。
- refuted —共有 fixture 4種は `B.SHAPES`、`B.block_run_order()`、`B.encode()` へ追随している。[test:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:86)、[test:111](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:111)、[test:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:147)、[test:305](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:305)。影響: 2形への縮小は同 file の judge、cell-effect、probe consumer に伝播する。
- refuted — `EXPECTED_HOLE_LINE` の consumer は fixture、validator変異、probe harness、patch、C++ oracle に残っている。[test:42](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:42)、[test:940](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:940)、[test:1273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:1273)。影響: hole line の変更は複数の実体 consumer に伝播する。
- refuted —この test file を直接起動しても `pytest.main([__file__])` で当該 file だけを走らせ、pytest 全体を入れ子起動しない。[test:1447](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:1447)。影響: suite 全体の意図しない再帰起動はない。ただし同 file 内には C++ compile、`git archive`、shell script 検査があり、焦点走自体は軽量ではない。

単独段 dispatch の射影境界により、非射影の `orchestrator/tests/`、`acceptance_duration_ledger.json`、`tools/check_docs.py`、inventory test 本体は読んでいない。このため、実装子が候補として挙げた `test_condition_meaning_gate.py`、ledger coverage、certified-writer/process-launch/coder-authority/official-perf inventory の参照関係と赤否は独立確認できない。author の列挙だけを根拠に合格または波及なしとは判定しない。

## 実装子報告の裏取り

- refuted —実走 nodeid は「なし」と報告されており、存在しない nodeid を成功扱いしていない。[author:12](/home/SFC/tanab/.claude/jobs/11513787/tmp/t1905-b10-prereg-v2/artifacts/t1905-b10-prereg-v2/author.md:12)。5件の新設 test 名は現物にすべて存在する。[test:794](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:794)
- refuted —対象 file と meta-test は明示的に未実走と書かれている。[author:14](/home/SFC/tanab/.claude/jobs/11513787/tmp/t1905-b10-prereg-v2/artifacts/t1905-b10-prereg-v2/author.md:14)。影響: 「実装済み・未実走」を「緑」とした虚偽はない。
- real —報告の「residual 欠落を拒否」は現行挙動として正しいが、M7の件数 guardを殺す証拠にはならない。[author:4](/home/SFC/tanab/.claude/jobs/11513787/tmp/t1905-b10-prereg-v2/artifacts/t1905-b10-prereg-v2/author.md:4)、[test:833](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:833)。影響: 完了報告と受理挙動は一致するが、変異事前登録の達成度だけが過大になる。
- refuted —その他の projected code と報告の literal な食い違いは見つからなかった。非pytest直接診断の実行証跡は射影資料に無いため、成功自体は追認していない。[author:13](/home/SFC/tanab/.claude/jobs/11513787/tmp/t1905-b10-prereg-v2/artifacts/t1905-b10-prereg-v2/author.md:13)

## 総括

- real 所見数: 3
- must-fix 件数: 1
- unkilled 変異数: 1（M7）
- 焦点走の静的に確認済み file 集合: `orchestrator/tests/test_b10_backoff_shape_sweep.py`
- 追加候補だが射影外で未確認: `orchestrator/tests/test_condition_meaning_gate.py`、ledger coverage と4種の inventory test の所在 file、`tools/check_docs.py` の dispatch 契約 consumer
- nested pytest 全体起動: なし。当該 file 自身だけを起動する
- pytest 実走結果: なし。緑の申告なし