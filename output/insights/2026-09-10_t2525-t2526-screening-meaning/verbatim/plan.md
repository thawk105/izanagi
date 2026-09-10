## 総括

T2525 は要求元の物理量から作った既存 `MeaningWitnessDeclaration` を screening へ渡す変更、T2526 は T2418 の新走を v2 にして metadata と追補を揃える変更とする。実装は主要 3 ファイルを同一所有単位で扱える。共通 gate、乱択用 framework、凍結 artifact の改訂は不要。

静的確認は完了。主要 6 ファイルの AST parse は成功した。ファイル変更・pytest・性能測定は実施していない。

**1. brief の確認と補正**

- 正本は [D1859](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/docs/decisions.md:56375) と [D1936 項19](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/docs/decisions.md:58246)。brief の引用・物理量独立照合・旧 artifact 不変という理解は一致する。
- [archive T2525/T2526](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/docs/archive/worklog-phase3-0909-1402.md:623) の「別宣言型または別 helper」は当時の設計候補。今回の裁定では新しい型を作る必要はない。
- **通常の backoff screening は既に外側の gate に支配される。** `backoff_sweep.py:425` の D1859 gate が、同 `:449` の `_run_screened_workload` より先に実行される。「汎用 screening 単体は未宣言を admit する」と「通常の backoff sweep が誤った要求を素通しする」を区別する。
- **b10 shape は screening の現行 caller ではない。** [b10_backoff_shape_sweep.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/orchestrator/campaign/b10_backoff_shape_sweep.py:100) の平均値は `(2,5,10,25,50,100)`、`:787` の符号化は `shape_code*1000+mean_us`。`:1253` は `screening=False`、`:4470` は `run_campaign`。乱択設定の保持は必要だが、この driver の新配線は不要。
- 凍結 consumer は存在する。[s1_known_axes_freeze.py:864](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/orchestrator/campaign/s1_known_axes_freeze.py:864) は generator と source を live hash で照合する。現時点でも generator hash は不一致と静的確認した。この既存不一致を本変更の回帰や、凍結再発行の理由にしない。

**2. T2525 の実装計画**

既存呼出鎖は次のとおり。

```text
backoff_sweep.run_workload :425 外側 gate
  → _run_screened_workload :275
    → evaluate_candidate :305 baseline / :344 candidate
      → screening_driver.evaluate_candidate :593
        → _require_condition_gate_before_evaluation :248
          → _run_condition_gate_for_genome :175
            → evaluate_define_runtime_meaning :225
```

| 編集位置 | 実装内容 |
|---|---|
| [backoff_sweep.py:118](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/orchestrator/campaign/backoff_sweep.py:118) | `:118–154` の物理量 mapping 検証と宣言生成を同ファイル内の小さい private helper に抽出する。非負要求の key 完全一致、exact int、非負 physical、有限 binary64 の現行契約を保つ。期待 bits は必ず `float(physical)` から生成する。 |
| 同 `:425` | `SWEEP_US` と実際の選択点から物理量 mapping を一度作り、既存 gate と screened workload に同じ要求を渡す。Genome の観測結果や static decoder から physical を作らない。 |
| 同 `:275` | private `_run_screened_workload` に物理量 mapping の必須 keyword を追加。既存 helper で宣言を作り、`:305` の baseline と `:344` の各候補へ対応する宣言を渡す。`-1` は screening では従来どおり宣言なし。 |
| [screening_driver.py:511](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/orchestrator/campaign/screening_driver.py:511) | optional keyword `backoff_fixed_declaration: MeaningWitnessDeclaration \| None = None` を追加し、`:593` の gate 呼出へ渡す。pipeline の `evaluate` へは渡さない。 |
| 同 `:248` | 宣言を stock checkout あり・なしの両分岐 `:259` / `:266` で転送する。 |
| 同 `:175` / `:225` | `BACKOFF_FIXED` の request にだけ宣言を渡す。他 macro と省略時は `None` を維持する。 |

追加引数を明示した場合、その宣言の型・macro・対象 Genome の値に対応する case を局所検証する。共通 gate は不一致 case を `unestablished` にするため（`condition_meaning_gate.py:3400–3417`）、**渡した intent が配線ミスで未宣言へ落ちる場合は screening 側で拒否する**。これは追加 API の整合検査に限定し、raw 値域による一律拒否は作らない。

受理集合は次のように保つ。

- 未宣言の正値・乱択値は、供給 arm が成立すれば従来どおり `unestablished`。
- 明示した静的 intent は、観測一致で green、不一致で build/measurement 前に拒否。
- backoff 専用 gate の `-1` stock witness、他 macro、sort/trigger caller の意味状態は維持。

**3. 独自宣言経路の棚卸し**

[s1_direct_comparison.py:230](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/orchestrator/campaign/s1_direct_comparison.py:230) は正値を `float(value)` と宣言する。ただし `:856–861` で要求 `backoff_us` と flag の一致を確認しており、現行凍結値は `5 / 10 / 2`。現行要求と一致する。

[paper_story_a2_certification.py:758](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/orchestrator/campaign/paper_story_a2_certification.py:758) も同方式。`:614` の要求元と `paper_story_a2_certification.v2.json:36,42` は `10 / 5`。

両経路は実装変更不要。将来の符号化格子を先取りして decoder を入れない。回帰では現行 literal の意味一致を確認する。

**4. T2526 の実装計画**

| 編集位置 | 実装内容 |
|---|---|
| [backoff_extended_sweep.py:95](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/orchestrator/campaign/backoff_extended_sweep.py:95) | T2418 report schema を `t2418-backoff-static-explore-report/v2` にする。 |
| 同 `:99` | status を例として `driver_declared_static_backoff_physical_us` に変更する。要求側の静的物理量宣言を表し、全 macro の意味確立や性能認証を意味しない値にする。 |
| 同 `:643,675,683` | `scale`・`spec_slug`・`trial` の T2418 identity を v2 に揃える。旧 campaign の再開先から分離する。 |
| 同 `:660,1163,1181,1288` | campaign search config、JSON report、DAT provenance の版と status を整合させる。 |
| 同 `:1023` | loader が新しい `t2418_config_for` の slug を使うことを確認。旧 v1 への fallback を追加しない。 |

意味検査は既に `:1355 → :1426 → :550` で物理格子から宣言され、`:1418` の gate が prebuild・run_campaign に先行する。新しい gate や永続 receipt schema は不要。

`run_kind=t2418-explore`、格子、順序、rep 数、report basename は維持する。新 campaign ディレクトリで分離できるためである。したがって以下は consumer として検証するが、版変更のための編集は不要。

- `backoff_extended_sweep.py:1258,1526` の materializer / CLI。
- `tools/pegasus/b10_backoff_grid.sh:645` の finalizer。
- `tools/pegasus/submit_b10_backoff_grid.sh:37` の run-kind routing。
- `backoff_extended_sweep_report.py` は T2418 v1 schema の直接 consumer ではない。

**5. docs と凍結境界**

[preregistration](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/docs/b10-backoff-static-tail-preregistration.md:623) には少なくとも三つの追補対象がある。

- `:623` の machine-readable spec 内の未確立 status。
- `:1067` の既存系列・report schema 不変条項。
- `:1075` の正値 witness 未確立・裁定待ちという記述。

親が末尾へ日付付き追補を追加し、D1859/D1936 項19、新しい T2418 identity/schema/status、適用開始 commit を記録する。§2 の旧探索結果、既存 JSON spec、旧記述は保存し、追補で新走への適用範囲を明記する。T2500 本格系列の spec 改版や実験規則の変更へ広げない。

旧 `output/insights/2026-09-09_t2418-backoff-static-explore/**`、旧 campaign の lock/WAL/receipt/reports、`output/s1-freeze/**` は編集しない。凍結 manifest と golden hash の再発行も行わない。

**6. 必要な正負検査と変異候補**

以下の node 名は新設案。意味検査では既存 `fixtures/condition_meaning_gate/supplied` の実 CMake・C++ 観測を使い、capture・意味 evaluator・family admission を stub しない。

| 検査 | 必須の観測 | 変異候補 |
|---|---|---|
| `test_screening_declared_literal_intent_is_green` | raw `5` / physical `5` の供給・意味が green | screening 最終呼出を `declaration=None` に戻す |
| `test_screening_declared_encoded_intent_is_green` | raw `3000` / physical `1000` が green | helper の `float(physical)` を `float(raw)` にする |
| `test_screening_literal_1000_intent_is_red` | raw `1000` / physical `1000` は期待 `1000.0`、観測 `0.0` の意味不一致 | expected を観測や decoder から作る |
| `test_screening_undeclared_shape_stays_unestablished` | b10 shape の実 `encode` が返す乱択値を無宣言で渡し、未確立を保持 | 正値全体へ static 宣言を自動生成する |
| `test_screening_declared_case_must_match_genome` | 別 raw 値の宣言を明示すると局所拒否 | 宣言整合検査を除去する |
| `test_backoff_screening_forwards_requested_intent` | 要求元から baseline/candidate、stock checkout 両分岐を経て実 gate へ到達 | 各転送箇所で引数を落とす |
| `test_t2418_v2_identity_and_report_disclosure` | 実 config と materializer が新 identity、JSON/DAT 同一 status を発行 | slug/trial/scale、schema、各出力 status を個別に旧値へ戻す |
| `test_t2418_v2_discovery_does_not_select_v1` | 実 discovery が v1 だけの出力を新走入力にしない | loader を v1 slug に戻す |
| `test_t2418_report_is_create_only` | 再生成を拒否し、既存 bytes を保持 | create-only 検査を除去する |

既存の [test_backoff_extended_sweep.py:660](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2525-t2526/orchestrator/tests/test_backoff_extended_sweep.py:660) は実 materializer を使うが discovery を差し替えている。これだけでは v1/v2 分離の証拠にならないため、実 discovery を通す正負検査を別途置く。

同様に screening の wrapper spy は配線検査に限定する。実 gate の正負検査と合わせ、負例では後段の build/measurement に到達しないことを確認する。性能評価の成功を模擬結果から主張しない。

変異は親が統合 commit の隔離 scratch と既存 harness で実行する。特に「引数を落とす」変異同士は kill 集合が重なり得るため、期待 node 完全一致は probe 後に登録する。

**7. 影響集合と親への引継ぎ**

直接編集するテストは `test_screening_driver.py`、`test_backoff_sweep.py`、`test_backoff_extended_sweep.py`。T2418 の既存 v1 pin は `:504,660,1325` 周辺にあり、今回の新走版変更に対応する期待値だけを更新する。

関連回帰集合は以下。

- `test_screening_opt_in.py`
- `test_t1416_backoff_compiler_binding.py:173`
- `test_p2_2_site_aware.py:376`
- `test_campaign.py` の screening 呼出箇所
- `test_condition_meaning_gate.py`
- `test_backoff_extended_sweep_report.py`
- `test_b10_backoff_shape_sweep.py`
- `test_s1_direct_comparison.py`
- `test_paper_story_a2_certification.py`
- `test_s1_known_axes_freeze.py`、`test_backoff_consumers.py`、`test_backoff_figure_provenance.py`

所有外 caller は `s6_sort_sweep.py:421` と `s8a_trigger_sweep.py:523`。optional 引数の省略互換を確認する。既存 backoff helper の抽出は `backoff_requested_us`、`backoff_profile`、`backoff_repro`、`backoff_overthrottle` にも波及するため、mapping 契約の回帰対象に含める。

親の受入は `tools/run_tests.py` に実行場所を選定させ、関連検査、変異、docs/agents 検査を実施する。commit 後に provenance 監査を行う。本段の静的確認を pytest 緑や実測完了として扱わない。