現状は受理不可です。上限 1.0% と 12-cell 判定は保たれていますが、must-fix が 2 件あります。pytest は指示どおり実行していません。

## must-fix

1. `real` — `physical_residual.provenance` は key 集合だけ閉じており、文書値と完全一致しません。[driver:1059](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1059) は schema、抽出規則、18 cell だけを exact にし、SHA、commit、request ID、nonce、host、時刻は形式だけ、clocks/calls は正整数だけを検査しています。文書の正本値は [doc:477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/docs/b10-backoff-shape-preregistration.md:477) です。数値文字列は `_positive_int()` により拒否されますが、例えば `probe_clocks_per_us=2101` は通ります。影響: 別 probe や架空の identity を記した v4 文書を formal driver が受理し、その偽 provenance を束縛・報告できます。

2. `real` — resume 済み block record から `binary` / code 2 が report へ再流入できます。[driver:2323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:2323) は `point` と block order を照合しますが、`shape`、`mean_us`、`encoded`、`genome` を point の正規 metadata と照合していません。その record は [driver:2585](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:2585) と [driver:2624](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:2624) から成果物へ出力されます。影響: current-v4 binding と自己 hash を持つ `point=none, shape=binary, encoded=2002` の prior recordが受理され、campaign が complete のまま「binary を測った」reportを生成できます。

必須修正は、provenance 全 field の文書値との完全一致と各 field の変異 test、ならびに prior record の pointに対する `(shape, mean_us, encoded, genome)` 完全一致と code-2 負例 testです。

## refuted

- `refuted` — 1.0% 上限は緩んでいません。parser は direct `!= 1.0`、runtime は `>=` のままです。[driver:1051](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1051) [driver:1277](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1277) 影響: 1.0%以上の cell は引き続き本走前に拒否されます。
- `refuted` — parser と runtime は 12 cell の順序・件数を閉じ、全件を走査してから最大値を判定します。[driver:1109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1109) [driver:1247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1247) runtime gate は例外捕捉の外側で呼ばれます。[driver:2793](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:2793) 影響: cell免除、警告化、環境変数、途中 returnによる迂回はありません。
- `refuted` — `registration_rules` は全 key と全 value の dict 完全一致です。[driver:831](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:831) 2つの重要値と residual 欠落を変異する test もあり、比較を stub 化すると落ちます。[test:812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:812) 影響: 観測値による shape/cell 除外を spec へ混入できません。
- `refuted` — fresh-run の shape consumer は2形に閉じています。`SHAPES`、encode/decode、named genomes、block order、spec、Holm、residual、probe、name parserはいずれも `constant` / `symmetric-modulo` のみです。[driver:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:91) [driver:863](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:863) [driver:2488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:2488) 影響: must-fix 2 の resume 経路を除けば code 2 は発行されません。
- `refuted` — dormant code 2 test は「登録 shape」と誤読しにくい名前・コメントへ改められています。[test:667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:667) [test:1085](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:1085) 影響: code 2 の検査は byte-pinned C++ 互換性に限定されています。
- `refuted` — 実文書を読む正例 test が存在し、actual v4を parseして2形、3族、12 residual、1.0、rules、参考幅、runtime最大偏差まで検査します。[test:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:743) 影響: canonical v4 の過剰拒否を検出できます。
- `refuted` — 境界 test は parser を通過した後で runtimeへ到達します。[test:848](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:848) `4242/4200` から exact 1.0% を構成しているため、`>=` を `>` にすると例外が消えて test が失敗します。影響: exclusive境界の変異を実際に殺せます。
- `refuted` — 既存 test の skip、xfail、削除、期待反転はありません。M11 は3族でも `raw_p < alpha < holm_p` を維持するため入力数を7から6へ調整しただけで、期待結果は維持されています。[test:625](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:625)
- `refuted` — `pairs_per_family=18`、`all-2^18`、`construct-all-18-...` は維持されています。[driver:980](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:980) [driver:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1027) MEANS、workload、threads、extime、reps、alpha、等価域にも差分はありません。
- `refuted` — 禁止面には未commit差分がありません。`EXPECTED_PATCH_PATHS`、`MEANS_US`、`EXPECTED_HOLE_LINE`、`FORMULA_SHA256`、`MIXER` は [driver:89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:89) 以降で不変、`exact_model()` の code 2 枝も不変です。[driver:566](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:566) `docs/` と `acceptance_duration_ledger.json` に未commit差分はありません。
- `refuted` — v3との `external_floor_reference_widths` JSON subtree比較は完全一致でした。現在値は [doc:579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/docs/b10-backoff-shape-preregistration.md:579)、driverの値検査は [driver:1153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1153) です。影響: 初版v4の flat-list化は残っていません。

## 定数の全文走査

- `21`: 実行コード・testには残存なし。文書 [doc:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/docs/b10-backoff-shape-preregistration.md:29) と [doc:239](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/docs/b10-backoff-shape-preregistration.md:239) の改訂履歴だけです。
- `54`: 残存なし。
- `18`: permutationの18対と、転記元probeの18 cellだけです。[driver:983](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:983) [driver:1106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/campaign/b10_backoff_shape_sweep.py:1106) residual受理表は直後で2形 x 6 meanの12 cellに生成されています。
- `6 families` / `all-six`: 実行コード・testには残存なし。文書の `6 -> 3` 改訂履歴だけです。testの `shape_differences_from_constant == 6` は1つの非constant形 x 6 meanなので正当です。[test:958](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1905-b10-shape-prereg-v2/orchestrator/tests/test_b10_backoff_shape_sweep.py:958)

## nit

- `real` — 実装子報告の差分件数が現物と不一致です。[author.md:6](/home/SFC/tanab/.claude/jobs/11513787/tmp/t1905-b10-prereg-v2/artifacts/t1905-b10-prereg-v2/author.md:6) は `+377/-138` としますが、最終現物は2 fileで `+336/-73` です。影響: 成果物の受理集合には影響せず、fix子追随後に報告が古くなったものです。

scope外の real 所見はありません。

## 総括

- real所見数: 3件
- must-fix: 2件
- nit: 1件
- 最重要3件: provenance全値のexact検査欠落、prior block recordからのbinary再流入、1.0%境界と12-cell全件判定は正しく維持
- pytest: 未実行。テスト結果を緑とは判定していません。