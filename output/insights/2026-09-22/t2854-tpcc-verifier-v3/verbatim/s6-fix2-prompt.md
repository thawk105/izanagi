単独段 dispatch: stage=fix; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2854-tpcc-verifier-v3

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 裁定 (採用所見 B1〜B4 と fix2 の制約): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s6-ruling.md
- 段 6 レビュー B (所見 B1〜B4 の根拠 file:line): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s6-review-B.md
- 段 6 レビュー A (参考): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s6-review-A.md
- 段 5 author の prompt (実装子契約。fix はこれを全文継承する): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/codex/s5-author-prompt.md
- 段 4 裁定 (R8 の試験要件、R9 の規模上限): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/s4-ruling.md
- 親の焦点走の実測 log (この worktree の HEAD f80f69cd8 と同内容の wave commit 788657426 で 3,532 passed / 3 skipped / 0 failed): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-tpcc-verifier-v3/review/focus-1.log

## あなたの役割と権限

あなたは Codex の fix 子である。s5-author-prompt.md の「あなたの役割と権限」「検査と報告の義務」をすべて継承する。今回編集してよいのは
`orchestrator/tests/test_verifier.py` の**新規 v3 試験と、その helper (`_v3_` で始まる関数など段 5 で足した部分) だけ**。production
(orchestrator/verifier/*.py) と既存試験 (段 5 より前からある行) は 1 byte も変えない。docs・commit・branch 操作はしない。
試験の期待を緩めない (反転・緩和・skip・削除禁止)。規模は段 4 R9 (test_verifier.py の差分が wave 起点から 800 行以内) を守る。

## 直すこと (段 6 裁定の B1〜B4)

- **B1**: pool 障害から逐次への fallback の試験 (`test_v3_parallel_processes_and_pool_failure_fallback`) で、parse の fallback を確かめる
  PID 等の assertion が、障害を注入した workers=2 の呼出しの**直後**の観測を見るようにする (helper 末尾の `parse_trace_dir(..., workers=1)`
  による上書きを見ない)。parse pool と edge pool の両方について、障害注入 → 逐次への fallback が実際に起きたこと (既存の v2 試験
  `test_capacity_broken_pool_terminates_workers_and_falls_back` / `test_parallel_worker_exit_discards_partial_results_and_rereads_all_files`
  付近の観測方式に倣う) と、fallback 後の v3 の表・取引種別・結果が障害なしの結果と一致することを確かめる。
- **B2**: legacy 経路は workers を使わないので、`_v3_paths` と混在・優先順位の試験で legacy を 1 回だけ走らせ、compact (packed / tuple)
  だけを workers=1 と 2 で走らせる。比較の網羅 (legacy と各 compact 経路の一致) は落とさない。
- **B3**: table の拒否試験の R/W fixture は C の宣言件数を行数に合わせ、拒否理由を table の字句または値域の 1 つにする。
- **B4**: 通常の v3 fixture で、「packed」経路の DSG が実際に packed 表現 (`dsg._PackedVersions`) になっていること、「tuple」経路が
  tuple builder を通ったことを肯定 assertion で確かめる。

## 実走の義務

`PYTHONPATH=. python3 orchestrator/tests/test_verifier.py` (素の自走 runner) を実際に走らせ、結果を逐語で報告する。全件緑になるまで直す。
pytest の直接起動と run_tests.py は sandbox / login の制約で使えない (前段で拒否・rc=16) ので試さなくてよい。

## 出力形式

Markdown。「変更 (file:line と差分行数、R9 の累計)」「B1〜B4 の充足 (項目ごとに file:line)」「実走結果 (逐語)」「未解決」、最後に `## 総括` (5〜10 行)。
