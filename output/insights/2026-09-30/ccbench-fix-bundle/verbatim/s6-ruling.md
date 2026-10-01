# 段 6 裁定 (review-a・review-b、親、2026-09-30 23 時台 JST)

退避済み snapshot: 検査器 = wave/author-a.patch (sha256 b6e51336…)、script = ../scripts-v1/ (9 file)。

| ID | 裁定 | 担当 |
|---|---|---|
| R1 = B-02 | real・採用。run_judge.sh は検査器の rc で終了し、合格は rc=0 かつ report の `result == "pass"` | fix-b |
| R2 = B-01 | real・採用。erratum E1 (F の cicada transaction.cc 末尾に新しい `#if TRACE` 枝 `static int izanagi_trace_probe = 0;`) を実装 | fix-b |
| R3 = B-08 | real・採用 (最小)。既存 key `expected_context_count_per_file` の意味は変えず、report 上位に path 別の期待数 `expected_context_count_by_path` を足す。file 別の `expected_context_count` は残し、`actual_context_count` は `contexts` の長さと一致するので残してよい | fix-a |
| R4 | real・採用。cicada の値組合せ (4 macro=値) を context タグと不一致・include 活性の例外文に含める。cicada 以外の path のタグ・文言は変えない | fix-a |
| R5 | real・採用。run_judge.sh の job 内でも A の修正対象 blob が F→各修正 tip の blob と一致し、他 path は F と一致することを照合 | fix-b |
| B-03 | real・採用。`.done` は trap で必ず rc と終了時刻を書く。失敗 job は新しい tag で再投入できる手順 (submit_one) を持つ。成功 `.done` の上書きは拒否 | fix-b |
| B-04 | 採用 (記録のみ)。各 job の dispatch log から request ID・実行ノード・Elapse を抜き出して receipt に残す。別ノード配置の保証は主張しない | fix-b |
| B-05・B-06 | 採用。各段 (clone・build・run・verify・登録検査) の所要秒を result.json に構造化記録し、timeout は段名・上限・経過秒・専用 rc で記録。MOCC cell は変えない (1 秒走) | fix-b |
| B-07 | 採用。login 用の索引生成 script (bundle・synth・manifest・各 report・検査器の sha256 を 1 つの JSON/Markdown 表に) | fix-b |
| B-09 | nit・不採用 (DW-G05: 成果物の値・受理集合を変えない。backlog にも起票しない) | — |
| B-10 | nit・不採用 (同上) | — |

共通: 既存テストの期待値を変更しない (反転・緩和・skip・削除の禁止)。赤なら実装側が誤り、期待値が誤りと考えるなら実装を変えず報告して止める。受理集合を変えない (R3・R4 は report と文言だけ)。

## 変異 (DW-M01 の登録を維持、fix 後に spec 化)

M1〜M6 は s4-ruling.md のとおり。R4 の文言追加は受理集合を変えないので変異対象にしない。
