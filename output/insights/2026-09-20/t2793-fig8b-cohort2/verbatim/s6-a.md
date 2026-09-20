## must-fix

0 件。指定された実装範囲で、成果物の誤りを生む欠陥は確認できませんでした。

## should

0 件。fig8b の生成・README 収録・着地検査は親の未了作業であり、author 所有 2 file の欠陥とは扱いません。

## nit

**N1：v2 の fixture provenance が、override なしでは production pin に拒否されることも直接検査するとよい。**

- 根拠：test 354–363 行の v1 CLI test は、override なしの拒否と override ありの受理を両方検査しています。v2 の 604–605 行は後者だけです。生成器 550–555 行の実装自体は正しいため、任意の補強です。
- 放置時の影響：現行の図・caption・provenance は変わりません。test が v2 closure の既定 pin 経路の退行を直接検出する機会が不足します。DW-G05 に従い nit とします。
- 既存行：
  ```python
  PLOT.validate_external_sources(prov, root)
  PLOT.validate_repo_closure(prov, REPO, expected_hashes=hashes)
  ```
- 修正案：
  ```python
  PLOT.validate_external_sources(prov, root)
  _reject(lambda: PLOT.validate_repo_closure(prov, REPO), "external pins")
  PLOT.validate_repo_closure(prov, REPO, expected_hashes=hashes)
  ```

以下、行番号の「生成器」は `tools/plotting/plot_b10_static_tail_formal.py`、「test」は `orchestrator/tests/test_plot_b10_static_tail_formal.py` を指します。

## 正しさ境界・役割・非プール

**cohort 2 の拒否条件は cohort 1 と同じ実装を通ります。**

- pin：生成器 186–202 行で cohort ごとの固定 path 集合・実 bytes の SHA-256・completion 内の束縛を検査。
- verdict：205 行で `== EXPECTED_VERDICT`。
- 性能未認証：206 行で `is False`。数値の `0` は代用できません。
- 正しさ：共通 `_cell` の 144–145 行で `certified is True`、整数型の `anomalies == 0`。真偽値を整数として通すこともありません。
- cohort 2 の負例は test 460–474 行で再 seal してから検査するため、verdict・認証の欠陥が先行する hash 不一致に隠れません。

`expected_hashes` は、明示的に Python API へ渡せば production pin を置換できる seam です。「API からも迂回不能」ではありません。一方、CLI parser に hash 引数はなく、`__main__` は引数なしの `main()` を呼び、v2 は両 loader に `None` を渡します（649–684 行）。したがって、今回の変更で **production CLI から pin を迂回する経路は増えていません**。

役割と順序は `COHORTS`、CLI の `(1, 2)`、closure の literal `[(1, "primary"), (2, "reproduction")]` で固定されています（40–51、545–546、664–665 行）。provenance を入れ替えて artist と caption まで再投影しても、位置検査が拒否します。

v2 closure は top-level key 集合を固定し、境界辞書の一致とは別に `cohorts_pooled is False` を検査します（542–543、558–559 行）。図・caption・provenance の数値処理に、cohort 間の差・比・プール推定・一致度・統合 verdict はありません。凡例の共通化は統計の合成ではありません。

## caption と再現欄

`_caption_v2` 全文（315–346 行）を確認しました。要求された要素があります。

- 固定表現は各 cohort に独立適用する前置きの直後に **1 回**。
- `performance_certified: false`、`NOT_POOLED_WORDING`、`NO_REREAD_WORDING`。
- 「Within each block」による上下行の説明。
- cohort ごとの区間分類・L 範囲・throughput 比・120 正しさ記録。240 という合計への置換なし。
- cohort-local y、workload 間・block 間の形と傾きの比較禁止。
- 機序・採用判断を主張しない限定、fig2c と探索標本の除外。

“same aggregate verdict” は出力された分類の併記であり、数値の一致度評価ではありません。続く限定も含め、D2157・追記項 7 の「飽和しない」への読み替えはありません。

追記項 2 の必須情報の配置は次のとおりです。

| 必須情報 | caption | provenance の各 `cohorts[]` |
|---|---|---|
| 主結果／独立再現 | 冒頭・block 説明 | `cohort`、`role` |
| group id・verdict | 両 cohort を明記 | `group_id`、`report.verdict` |
| 事前登録束縛 | commit の先頭 9 桁 | 完全な commit、blob SHA-256 |
| spec 束縛 | 同一である旨 | `report.spec_sha256` |
| 一次成果物参照 | hash 全文は詰めない裁定 | `external_inputs` の path・kind・SHA-256 |
| job・results 稿 | job を明記 | `campaigns`、`results_document` |

これは段 4 A5 の配置方針に整合します。README の再現表への収録は親側の確認事項です。

## v1 不変と layout

base `b7f970dfa` と現物を、テストを実行せず source 比較しました。

- `_caption`、`_artist_series`、`build_provenance`：関数 source が完全一致。
- v1 closure：追加された v2 dispatch の 2 行を除けば完全一致。
- 既存 25 test と `_run()`：関数 source が完全一致。着地 fig8 test の期待値変更もありません。
- `_figure_number`：既定の正規表現は従来の `fig([0-9]+)_`。v1 の suffix 受理集合は拡張していません。
- v1 展開 argv：従来の 5 要素を維持。
- fixture：cohort 1 では `shift=0`、従来の path・job・事前登録値を使う変更です。

さらに、凍結 fig8 の PNG・PDF・provenance は **base と bytes 同一**で、SHA-256 も author 報告の 3 値と一致しました。

layout は 12 axes を明示して検査し、`block-title` と panel bbox の交差面積が 1 を超える場合に拒否します（473–504 行）。負例は短い `"intrusion"` を panel 中央へ置いており、他の文字との重なりに頼らず侵入条件を検査する構成です。

B1 も是正されています。CLI から `_caption_v2` と `build_provenance_v2` が `_publish_outputs` に渡り、caption 設定・layout 検査を **mkdir・一時ファイル作成・保存より前**に実施します（615–628、668 行）。v2 CLI test はこの実経路を通ります。

## author 報告と証拠の範囲

v1 不変・既存 25 test 不変・凍結 3 file 不変は、今回の静的比較でも裏付けられました。

焦点走ログは request `11883.nqsv`、child rc=0、**39 passed / 1 skipped** を記録しています。ただし、次の区別が必要です。

- ログ自身が「受入形でない走行」と明記しており、受入全走の証拠にはできません。
- このログには author が報告した自走 harness の node 別出力や、実 root の v1/v2 CLI 実走記録はありません。それらは指定資料の範囲では author 報告に留まります。
- 39 件の内訳はこのログから特定できません。対象ファイルの 37 test と直ちに同一視できません。
- author の「pytest 未実走」と、後続の親による pytest 成功は時点が異なるため矛盾しません。
- 現物に fig8b の 3 成果物はまだなく、着地 test の成功は未証明です。

本レビューでは pytest、自走 harness、作図を実行していません。

## 総括

**must-fix 0 件、should 0 件、nit 1 件。段 5 実装の静的レビューは GO。**  
wave 全体の受入完了を意味する判定ではありません。親の成果物統合と変異 probe / final は残っています。

変異の期待 node 集合は以下です。逐語 anchor 未確定のため、M8 は `_caption_v2` の `letter_suffix=True` を外す変異、M9 は下 block の描画入力を cohort 1 に置換する変異として予測します。M0 を除き、すべてに独立した kill 根拠があります。

| 変異 | 期待 | 期待 node 集合・失敗理由 |
|---|---|---|
| M0 docstring 追記 | SURVIVED | ∅。現行 generator hash との一致を closure は要求しない |
| M1 cohort 2 DAT pin 改変 | KILLED | `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_cohort2_pinned_hashes_match_cohort2_results_document`：凍結稿との digest 不一致。root がある場合は `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_real_root_loads_cohort2_and_matches_results_document_when_present`：SHA-256 不一致 |
| M2 role → primary | KILLED | `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_cohort_roles_are_fixed_literals`：固定 literal 不一致。`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_cli_cohort2_writes_three_outputs_and_v2_closure`：生成 provenance の役割対不一致 |
| M3 alternate verdict 受理 | KILLED | `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_cohort2_rejects_alternate_verdict_and_certification_failures`：指定 verdict の負例が受理される。既存の `"fixture-invalid"` 負例はこの変異を kill しない |
| M4 非プール文削除 | KILLED | `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_v2_caption_contains_independent_fixed_wording`：固定 literal の出現数が 0 |
| M5 禁止表現へ置換 | KILLED | `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_caption_contains_fixed_expression_and_certification_literal`：固定表現欠落。`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_caption_avoids_forbidden_saturation_claims`：禁止語。`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_v2_caption_contains_independent_fixed_wording`：固定表現欠落。`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_landed_fig8_repo_closure_and_caption_when_present`：凍結 caption と再投影の不一致 |
| M6 layout 先頭 return | KILLED | `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_bbox_overlap_is_a_failure`、`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_layout_failure_publishes_nothing`、`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_v2_block_title_intrusion_publishes_nothing`、`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_v2_text_overlap_publishes_nothing`：それぞれ不正 layout を拒否しない |
| M7 block-title 侵入検査削除 | KILLED | `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_v2_block_title_intrusion_publishes_nothing`：panel 内の見出しを拒否しない |
| M8 v2 caption を数字のみへ | KILLED | `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_figure_number_suffix_is_v2_only`、`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_v2_caption_contains_independent_fixed_wording`、`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_two_cohort_artists_match_raw_repetitions_and_intervals`、`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_v2_block_title_intrusion_publishes_nothing`、`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_v2_text_overlap_publishes_nothing`、`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_cli_cohort2_writes_three_outputs_and_v2_closure`：`fig8b_` を caption 生成時に拒否。後半の node は巻き添えであり、layout 欠陥への帰属ではない |
| M9 下 block 取り違え | KILLED | `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_two_cohort_artists_match_raw_repetitions_and_intervals`：cohort 2 の生 reps から計算した期待 y と描画 line が不一致 |
| M10 pooled → True | KILLED | `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_cohort_roles_are_fixed_literals`、`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_cli_cohort2_writes_three_outputs_and_v2_closure`：独立した `is False` assertion |
| M11 位置・役割対検査削除 | KILLED | `orchestrator/tests/test_plot_b10_static_tail_formal.py::test_cli_cohort2_writes_three_outputs_and_v2_closure`：入替後に artist・caption を再投影した provenance が受理される |

fig8b 着地後は、**M1・M4・M5・M8・M10** の集合へ  
`orchestrator/tests/test_plot_b10_static_tail_formal.py::test_landed_fig8b_repo_closure_and_both_captions_when_present`  
が加わる予測です。現在は未着地のため集合に算入しません。

M9 は生成器の射影から期待値を取らず、M11 は他の射影不一致を除去して位置検査だけを残しています。したがって、指定変異について producer と検査側の同時追随で全 test が緑になる構成は見当たりません。最終的な完全集合は、裁定 §3 どおり probe の実測で確定する必要があります。