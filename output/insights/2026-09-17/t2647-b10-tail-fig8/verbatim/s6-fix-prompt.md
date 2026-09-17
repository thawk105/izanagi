単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2647-b10-tail-fig8

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**する。これは射影 file 限定の停止規則であり、自分が推測して探した path が不在でも停止理由にしない。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/s6-adjudication.md` — **親の段 6 裁定 (確定指示)。R1・R3・R4・R6・R7 が本 fix の対象。** これが他の資料と食い違うときは裁定が勝つ
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/s4-adjudication.md` — 段 4 裁定 (§2 生成器仕様、§3 test 仕様、§5 受理集合。段 6 裁定で変わった点: 注記は `min L =`、caption に Pegasus・非混合文・certified の射程、`measurement_env` の検査)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/artifacts/dev-wave-t2647-b10-tail-fig8/s6-a.md` — レビュー A (must-fix 1、nit 1・2・4 の根拠)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2647-b10-tail-fig8/artifacts/dev-wave-t2647-b10-tail-fig8/s6-b.md` — レビュー B (must-fix 1 の根拠: `test_pinned_hashes_are_used_when_no_override` が G:178 の completion 検査に mask される)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/tools/plotting/plot_b10_static_tail_formal.py` — 生成器 (519 行、commit 4636181a9)。編集対象: `_load_measurements` の campaign 検査 (195〜205 付近)、`_caption` (263〜285)、`_direct_label` (287〜293)
- `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl/orchestrator/tests/test_plot_b10_static_tail_formal.py` — test (441 行)。編集対象: `_fixture` の identity (57〜66 付近)、`test_pinned_hashes_are_used_when_no_override` (255〜257)、caption test (222〜237)、必要なら `test_interval_states_are_copied_not_recomputed` (175〜194) の注記検査

repo root は `/work/1/SFC/tanab/izanagi/.codex/worktrees/t2647-fig8-impl` (branch `impl-dev-wave-t2647-b10-tail-fig8`、HEAD 4636181a9 = wave の統合 commit) とする。上記以外も repo 内を読んでよい。

**大きい file を全文 `cat` しないこと。** `grep -n <語> <file>` で位置を出し、`sed -n '<開始>,<終了>p' <file>` で 200 行以内ずつ読む。

## この段の仕事

段 6 裁定の R1・R3・R4・R6・R7 を実装する。編集してよい file は上記 2 本だけ。

1. **R1 (生成器 `_direct_label`)**: `"6/6 intervals declining\nL >= {min:.3f}"` を `"6/6 intervals declining\nmin L = {min:.3f}"` にする (不等式を使わない。値は JSON コピーの L の最小値、小数 3 桁の四捨五入)。すべて declining でない場合の文は変えない。
2. **R3 (生成器 + fixture)**: `_load_measurements` の campaign 検査に `_require(identity["measurement_env"] == "pegasus", "measurement env mismatch")` を足す (実データは 3 campaign とも `pegasus`)。caption の条件文を `"Conditions: Pegasus compute nodes, 48 threads, 1,000,000 records, …"` にする (先頭に "Pegasus compute nodes, " を足すだけ)。fixture の `identity` に `"measurement_env": "pegasus"` を足す。
3. **R4 (生成器 `_caption`)**: 末尾の "This cohort is a different grid and a different cohort from fig2c and is not a continuation of it." の**直後**に 1 文 `"No samples from the exploratory run t2418-explore or the t2266-tail series are included; 9999 us was newly measured in this cohort."` を足す。
4. **R6 (生成器 `_caption`)**: correctness の文を次に変える (値は data から書式化のまま): `f"Correctness comes from separate trace-enabled runs under the recorded legacy check configuration, not the performance configuration: all {…} records were certified with {…} anomalies; certified means serializability of the observed YCSB point read/write traces under that check configuration and nothing beyond, and this is not a performance certification."`
5. **R7 (test)**: `test_pinned_hashes_are_used_when_no_override` を単一理由にする。fixture を作った後、`-complete.json` の `artifacts` の json / dat の値を **`PLOT.PINNED_SHA256` の production 値** に書き換える (fixture の実 bytes とは一致しないが completion 検査 `complete["artifacts"][name] == hashes[path]` は pin 表に対して通る)。`load_measurements(root)` (override なし) が `"SHA-256 mismatch"` で拒否されることを検査する。これで「SHA-256 比較を除去する変異」に対してこの test は受理 (DID NOT RAISE) で赤になり、completion 検査には mask されない。test の docstring か comment に「completion record は production pin を名乗り、byte 比較だけが拒否する単一理由 fixture」と書く。
6. caption の test (`test_caption_contains_fixed_expression_and_certification_literal`) に "Pegasus compute nodes" と "t2418-explore" と "nothing beyond" の包含を足してよい (足す場合は 3 つとも)。禁止句 test (`test_caption_avoids_forbidden_saturation_claims`) は変えない。
7. **触らない**: 上記以外の file、既存 test の期待値 (R7 の 1 件を除く)。反転・緩和・skip・削除で緑にしない。赤なら実装側が誤り。期待値が誤りなら実装を変えず報告して止める。fixture に現行 hash を差し込んで緑にしない (R7 は completion record 側の値であり、byte 比較を通す目的ではない)。docs 編集・commit・`git add`・図の再生成は親が行う。
8. `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=. python3 orchestrator/tests/test_plot_b10_static_tail_formal.py` を走らせ、結果 (passed / failed / skipped) と nodeid を報告する。着地 test (`test_landed_fig8_repo_closure_and_caption_when_present`) は caption 変更により **赤になるのが正しい** (着地 provenance と README の caption は親が再生成後に更新する)。この 1 件の赤を期待赤として報告し、他の赤は回帰として報告する。`tools/run_tests.py` と pytest は sandbox から走らない。
9. 実データ生成 (`python3 tools/plotting/plot_b10_static_tail_formal.py --measurement-root /work/1/SFC/tanab/b10-backoff-grid-t2500-formal /tmp/<任意>/fig8_b10_static_tail_not_observed`) を試し、rc と caption 全文を報告に載せる。成果物は repo に残さない (削除)。

## 完了報告に必ず含める

- 変更 file:line と関数の一覧、所見ごとの closed / partial / regressed 対応表 (R1・R3・R4・R6・R7)。
- 実走結果 (nodeid、passed / failed / skipped、期待赤 1 件の名指し)。
- 新しい caption 全文 (実データ生成の provenance から逐語)。
- 変異 anchor への影響: 裁定 §4 の M0〜M12 の逐語 anchor (author 報告の表) のうち、本 fix で変わったものと新しい逐語。M11 の kill 証拠が `test_pinned_hashes_are_used_when_no_override` と `test_external_input_hash_drift_is_rejected` の両方になること。
- 受理集合の変化 (`measurement_env == "pegasus"` の要求追加だけであること)。

## 出力形式

**出力は file に書かず、最終メッセージの本文に全文を書け。** 見出しはすべて `##` (H2) で書き、最後の節は必ず `## 総括` とする。予算が尽きそうなら、その時点の結論を出力形式どおりに書いて終われ (無出力が最悪)。

節の順:

## 変更一覧と対応表
## 実走結果
## caption 全文
## 変異 anchor への影響
## 受理集合の変化
## 総括
