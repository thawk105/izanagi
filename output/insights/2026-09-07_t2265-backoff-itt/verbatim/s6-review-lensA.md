## 総括

静的レビューの結論は、解析本体の主推定量、符号、添字、cluster 等重み、分散、CI、欠測分岐、禁止除外、決定性は凍結事前登録と一致しています。現在の計算ロジックに主判定を誤らせる不一致は見つかりませんでした。

ただし、変異事前登録 M13・M14 は独立した oracle を持たず、宣言した変異が緑のまま残ります。これは正しさ境界に触る must-fix です。ほかに、割当比の母集団と親裁定に反するテスト各 1 件を nit としました。

pytest は指示どおり実行していません。

## 所見 1 — M13・M14 の変異検査は自己参照で、誤った TOST 定数と等価域を検出できない

- 主張: M13 の `T90_DF11` を `2.2009852` に変える変異と、M14 の `EQUIVALENCE_MARGIN` を `0.03` に変える変異は、現在の新規テストを通過できます。
- 根拠:
  - 変異事前登録は M13・M14 の赤を要求しています: `output/insights/2026-09-07_t2265-backoff-itt/verbatim/s4-ruling.md:93-94`。
  - 現実装の値自体は正しいです: `orchestrator/campaign/backoff_counterfactual_analysis.py:68-70`。
  - CI 検査は出力を同じ module 定数と比較しています: `orchestrator/tests/test_backoff_counterfactual_analysis.py:181-187`。したがって定数と実装が同時に変わると赤になりません。
  - 境界検査も `margin = analysis.EQUIVALENCE_MARGIN` と自己参照しています: 同 `:314-339`。
  - 合成データの CI は 95% critical valueを使っても等価域の十分内側なので、M13 の定数置換でも `equivalent` のままです: 同 `:163-189`。
  - 射影された全 test file を検索しましたが、`1.7958848`、`2.2009852`、`ln(1.03)` を独立に固定する assertion はありません。
- must-fix か nit か: **must-fix。正しさ境界。**
- 成果物影響 1 行: 90% TOST を誤って 95% CI にしたり等価域を `±0.03` にしたりしてもテストが緑となり、境界付近の確認的判定が変わり得ます。
- 提案: test 側で `T90_DF11 == 1.7958848`、`T95_DF11 == 2.2009852`、`EQUIVALENCE_MARGIN == math.log(1.03)` を module 定数から独立に固定し、90% CI だけが域内、95% CI は域外となる合成 cluster を追加してください。
- 反証されたら何が変わるか: 射影内に独立した数値 oracle が存在する、または上記 2 変異を実際に当てた焦点走で赤になる node が示されれば、この所見は取り下げます。

## 所見 2 — §8 の「実測割当比」が最後の割当を含まず、推定対象の母集団と混同されている

- 主張: `assigned_invert_rate` は run の全割当ではなく、後続窓を持つ `m_r-1` 件だけから計算されています。
- 根拠:
  - 最後の更新を落とす限定は主推定量 `Y[r,i]` に対するものです: `docs/backoff-counterfactual-preregistration.md:114-131`。
  - 一方、無作為化検査は「各 run の実測割当比」を記録するとしています: 同 `:264-265`。seed 表も「先頭 583 割当」の比です: 同 `:242-257`。
  - 実装は `zip(events, events[1:])` の選択集合から腕数と比率を計算するため、最後の割当を数えません: `orchestrator/campaign/backoff_counterfactual_analysis.py:312-329`。
  - テストは最後の割当変更後に run estimate 全体が不変であることを要求し、比率まで変わらない現状を固定しています: `orchestrator/tests/test_backoff_counterfactual_analysis.py:200-215`。
- must-fix か nit か: **nit。報告整合性であり、主判定には影響しません。**
- 成果物影響 1 行: 成果物の割当比が全 `m_r` 件ではなく `m_r-1` 件の比となり、583 event の run では最大 1 件分ずれます。
- 提案: 推定量用の腕数は現状のまま保持し、全 `events` から計算する `assignment_rate_all_events` などを §8 の無作為化診断として別掲してください。
- 反証されたら何が変わるか: §8 の「実測割当比」が明示的に `i=0,...,m_r-2` の推定対象だけを意味すると確認できれば、本所見は取り下げます。

## 所見 3 — 親が禁止した source 全文の `"pending"` 検査が追加されている

- 主張: 新規テストに、親裁定 R12 が明示的に採らなかった source 全文の文字列禁止検査があります。
- 根拠:
  - 裁定は「文字列全禁止でなく、生成された field が exact 64文字小文字 hex」で検査するとしています: `output/insights/2026-09-07_t2265-backoff-itt/verbatim/s4-ruling.md:31`。
  - 実際のテストは `assert "pending" not in DRIVER.read_text(...)` を置いています: `orchestrator/tests/test_t2187_adaptive_const_probe.py:2099`。
  - 生成 field の exact 値と hex 書式は、その直前 `:2094-2098` ですでに検査されています。
- must-fix か nit か: **nit。親裁定との整合・テスト実効性の問題です。**
- 成果物影響 1 行: 生成 field が正しくても、driver 内の無関係な説明や別機能に `"pending"` が入るだけで焦点テストが偽陽性になります。
- 提案: `:2099` の source 全文 assertion だけを外し、生成された metadata の exact hash 検査を維持してください。
- 反証されたら何が変わるか: s4 後に source 全文禁止を採用した新しい親裁定が存在するなら、本所見は取り下げます。

## 事前登録との照合表

| 項目 | 実装 | 判定 |
|---|---|---|
| outcome | `following_rate / current_rate` の log: `backoff_counterfactual_analysis.py:331-335` | §4 と一致 |
| 添字 | `zip(events, events[1:])` で `Z[i]` と窓 `i+1`: 同 `:312-318`。patch は窓統計を記録後、その更新の割当を適用: `patches/cicada-adaptive-counterfactual.patch:407-447,516-586` | 一致。最後の割当だけ不使用 |
| 符号 | `mean(Z=0) - mean(Z=1)`: `backoff_counterfactual_analysis.py:330-345` | 一致 |
| 全 event ITT | 主解析は `include_all`: 同 `:513-518`。clamp、実差分、実現反転、符号、可否、outlier の filter なし | 一致 |
| run 等重み | seed 順の各 `D[r]` を `statistics.fmean`: 同 `:360-385` | 一致 |
| cluster 分散 | `statistics.stdev`、`SE=s_D/sqrt(12)`: 同 `:386-391` | `R-1` 分母と一致 |
| 等価域 | `math.log(1.03)`: 同 `:68` | 現実装は一致 |
| TOST | 90% CI の両端が等価域内: 同 `:406-417,456-460` | 現実装は一致 |
| 実用優越 | 95% CI 下端 `>+Delta` または上端 `<-Delta`: 同 `:394-405,461-469` | 一致 |
| t 値 | `1.7958848`、`2.2009852`: 同 `:69-70` | 現実装は一致 |
| zero commit | run estimate を `None`、理由を保持: 同 `:322-329`。primary decision は初期値 inconclusive のまま: 同 `:531-538` | 一致 |
| 片腕欠落 | run estimate を `None`、run 自体は残す: 同 `:336-343,361-377` | 一致 |
| 12 cluster 未満 | `confirmatory_complete=False`、理由追加、decision inconclusive: 同 `:381-436,531-538` | 一致 |
| 副次層 | 残る5 regime、符号3層、可否2層、時間4 block: 同 `:540-588` | §6 と一致 |
| 決定性 | path を文字列順、run を seed 順に固定: 同 `:493-503,360-361` | 入力順・dict順・加算順の可変経路なし |
| seed | exact 12 seed set、重複拒否: 同 `:50-65,504-508` | 一致 |
| 停止規則 | 明示 path のみ、最大12。再投入と「最初の完走」の選択は解析 API 外 | 解析内の逸脱なし |
| 割当比 | outcome 付き `m_r-1` 件だけ: 同 `:312-329` | 所見2 |

### M1〜M16 の静的変異照合

| 変異 | 赤になる node | 静的結論 |
|---|---|---|
| M1 | `test_step_policy_seed_rejects_non_decimal_or_out_of_uint64[overflow]` | 赤 |
| M2 | 同 `[hex]` | 赤 |
| M3 | `test_genome_for_policy_cell_supplies_real_build_define`、`test_policy_two_nondefault_seed_assignment_matches_independent_lcg` | 赤 |
| M4 | `test_genome_for_policy_cell_supplies_real_build_define` | 赤 |
| M5 | `test_counterfactual_artifacts_record_exact_preregistration_sha_only_on_exact_axes` | 赤 |
| M6 | 同 node の各 axis drift | 赤 |
| M7 | 同 node の row hash assertion | 赤 |
| M8 | 同 node の policy 2 row と journal seed assertion | 赤 |
| M9 | `test_only_final_assignment_is_dropped_and_post_treatment_fields_do_not_filter` | 赤 |
| M10 | `test_missing_arm_and_zero_commit_make_whole_primary_inconclusive` | 赤 |
| M11 | `test_binding_seed_and_input_count_fail_closed_or_become_inconclusive` | 赤 |
| M12 | `test_public_analysis_pairs_next_window_and_uses_equal_run_clusters` | 赤 |
| M13 | 境界関数の CI 引数差し替えは赤。ただし `T90_DF11=2.2009852` は緑 | **事前登録した意味での赤保証なし** |
| M14 | test が module の margin を再利用 | **赤になる node なし** |
| M15 | `test_public_analysis_pairs_next_window_and_uses_equal_run_clusters` の event-weighted 対比 | 赤 |
| M16 | 同 node の reversed-path 完全一致 | 赤 |

## 見つからなかったもの (探したが無かった)

- 符号反転、`Z[i+1]` を使う添字ずれ、最後の更新に架空 outcome を与える経路。
- clamp、実適用差分 0、`inversion_realized`、`recommended_delta_sign`、`both_actions_feasible`、outcome、外れ値による主解析の除外。
- event 数による run 重み付け、母分散、`sqrt(event_count)` を使う cluster SE。
- 現実装での 95% CI による TOST、`±0.03` または非対称 `[ln(0.97),ln(1.03)]`。
- zero commit、片腕欠落の run を `run_estimates` から削除する処理。
- 12 cluster 未満で確認的 decision を発行する分岐。
- 入力 path 順、artifact 内 row 順、dict 反復順により数値加算順が変わる経路。
- `inversion_realized` を副次層として出す処理、または `median_tps` を解析結果へ出す処理。