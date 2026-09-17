単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/brief.md` — 親の段 1 brief (**親自身も検査対象**)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/s4-adjudication.md` — 親の段 4 裁定 (**検査対象**。§2.2 の load 手順、§3 test 仕様、§4 変異 matrix、§5 受理集合)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/artifacts/dev-wave-t2647-b10-tail-fig8/s5-author.md` — 実装子の完了報告 (説明と実装の食い違い、「変異 matrix の anchor」表の予想 node を疑う)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/focus-post-s5.log` — 親の焦点走 log (計算ノード dispatch、27 passed 1 skipped)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/tools/plotting/plot_b10_static_tail_formal.py` — 生成器 (519 行、全文読む)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/orchestrator/tests/test_plot_b10_static_tail_formal.py` — test (441 行、全文読む)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/paper-story/figures/fig8_b10_static_tail_not_observed.provenance.json` — 着地 provenance (336 KB。**全文 cat しない**。`python3 -c` か `jq` で構造・`workloads[].cells[]` の値・`artist_series`・`outputs` を見る)
- `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/t2500-backoff-static-tail-formal.json` — 実データ (359 KB、読むだけ。**全文 cat しない**。`python3 -c` / `jq` で構造を見る)
- `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/t2500-backoff-static-tail-formal.dat` — 実データ (121 行)
- `/work/1/SFC/tanab/b10-backoff-grid-t2500-formal/group-report-20260915/t2500-backoff-static-tail-formal-complete.json` — 実データ
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/paper-story/results/2026-09-16-b10-static-tail-not-observed.md` — results 稿 §2.2〜§2.3 (176〜284 行) の表と §4.1 (392〜420 行)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/tools/plotting/FIGURE_CONVENTIONS.md` — 作図規約 (§1・§2・§9・§10)
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/tools/plotting/plot_a2_certification.py` — 雛形 (fig6)。比較用に `check_figure_layout` 757〜793、`validate_repo_closure` 865〜889 だけ読む
- `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8/docs/dev-wave/mutation.md` — 変異契約 (DW-M01・M03・M04・M08)

repo root は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8` (commit 4636181a9) とする。上記以外も repo 内を読んでよい。

**大きい file を全文 `cat` しないこと。** `grep -n <語> <file>` で位置を出し、`sed -n '<開始>,<終了>p' <file>` で 200 行以内ずつ読む。sandbox は read-only なので pytest や生成器の実走は要求しない。静的検査でよい (実データを `python3 -c` で読んで値を検算することはしてよい)。

## レンズ B — 数値の忠実性、pin と fail-closed、fixture の実寸、test の質、変異の単一理由性

plan を守らせるのではなく攻撃せよ。次を最優先で疑う:

1. **数値の忠実性 (§1・§2)**: provenance の `workloads[].cells[]` の平均・CI・abort 率・変動係数を、実データ `.dat` / JSON reps から独立に再計算して照合する (24 cell、少なくとも各 workload 2 cell)。`T95_DF4` の値、`ddof=1`、`abort = aborts / (aborts + commits)` の全精度。caption の比 0.444 / 0.481 / 0.400 と L の範囲 0.2738 / 0.3704 を JSON から再計算。results 稿 §2.3 の表と不一致があれば名指しで書く。
2. **コピーと再計算の境界**: verdict・state・interval state・qhat・L・U が本当にコピーされているか (再計算・上書き・並べ替えの経路が無いか)。`sorted(campaign["points"], key=backoff_us)` による並べ替えが `workloads[].statistics` との対応を壊さないか。`zip(report["campaigns"], report["workloads"], sorted(RRATIOS))` の対応付けが workload 名で束縛されているか (名前でなく位置だけで対応させていないか)。
3. **pin と fail-closed**: `_load_measurements` の検査順序で、SHA-256 不一致より前に JSON を parse していないか (parse 例外が SHA 不一致を隠す経路)。`expected_hashes` seam が production の CLI から到達可能でないか (`main` の argv で渡せないこと)。`validate_repo_closure(expected_hashes=)` seam の追加が着地 test の意味を弱めていないか (着地 test は None = pin 表で呼んでいるか)。`_publish_outputs` の tmp → rename と「失敗時に成果物を出さない」が本当に成立するか (layout check の位置、`previous` 復元の意味)。
4. **fixture の実寸 (§10)**: fixture が production 入力の形 (3 × 8 × 5、`.dat` 120 行、区間 6 × 3、statistics の field、correctness 5 件、`identity.grid`) を本当に持つか。fixture が生成器の定数から組み立てられているか。**fixture が過剰決定で、負例の赤理由が 1 つに絞れない箇所** (DW-M03) を探す。`test_malformed_fields_and_counterpart_mismatches_are_rejected` の 11 変異のどれが「単一理由」でないか。
5. **恒真・inert な検査**: 生成器の中に「自分の出力を自分で検査する」だけの gate や、fixture に対して必ず通る検査が無いか。`test_caption_avoids_forbidden_saturation_claims` が生成器の source に対しても検査する設計の是非 (source に "saturated" (state 名) があるのに "saturates" 検査が通る理由を確認)。`_require(len(plot_axes) != 6 ...)` の意味。
6. **変異 matrix (裁定 §4、author の anchor 表)**: M0〜M12 の各 anchor (逐語) が生成器に**一意**に存在するか (`grep -c`)。各変異を単独で殺す test が予想どおりか、別の test も同時に赤になるか (期待 node の完全集合、DW-M08)。M11 (SHA 比較除去) が M1 (pin 値変更) や `test_pinned_hashes_are_used_when_no_override` と同じ層で mask されないか。M9 (`check_figure_layout` 先頭 return) を殺すのが `test_bbox_overlap_is_a_failure` だけか、`test_layout_failure_publishes_nothing` も赤になるか。等価対照 M0 が本当に等価か。
7. **実データ test と着地 test の射程**: `test_real_root_loads_and_matches_results_document_when_present` が root 不在で skip する設計は計算ノード受入で緑を偽装しないか (今回の焦点走では計算ノードから root が読めて passed)。`test_landed_fig8_repo_closure_and_caption_when_present` の skip 条件 (3 file と README 記載がともに無い場合) が「部分着地」を見逃さないか。
8. **自走 harness**: `_run()` が全 test を拾うか (`sorted(globals())` の走査)、`tmp_path` 注入、Skip の扱い。`test_plain_runner_coverage` の allowlist 契約との整合。
9. **親 brief・裁定自身の誤り**: 親が実測せずに書いた前提 (「statistics に median がある」「group id は JSON に無い」「`.dat` の列順」等) と実装のズレ。

所見は real / refuted の判定材料 (根拠の file:line、再計算した値) を付け、must-fix は「放置したとき成果物 (図・provenance・受理集合・test の検出力) がどう変わるか」を 1 行で示す。示せないものは nit にする。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2) で書き、最後の節は必ず `## 総括` とする。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ (無出力が最悪)。

節の順:

## 数値の再計算結果 (cell ごとの照合表、不一致の有無)
## must-fix (番号、file:line、放置時の影響 1 行、根拠、修正案)
## nit
## 変異 matrix の検査 (M0〜M12 の anchor 一意性・予想 node・mask の可能性)
## 親 brief・裁定への所見
## 総括
