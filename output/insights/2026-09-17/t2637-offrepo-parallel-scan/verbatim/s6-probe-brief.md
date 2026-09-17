# 親の依頼の背景 — 並列走だけに出る「確認不能」の帰属

実根 `/work/1/SFC/tanab/dev-wave-jobs` (約 185 万 file、直下 1,252 entry) を fixture repo
(`/work/1/SFC/tanab/t2637-audit-fixture/repo`、到達不能 commit 1 本・候補 4 file) から走査した結果:

| 走 | tool | workers | 列挙 (秒) | 確認不能 (scan_failures) | load |
|---|---|---|---|---|---|
| old-1 | 変更前 | 1 | 935 | 0 | 21→36 |
| new16-1 | 新 | 16 | 188 | 11 | 36→14 |
| old-2 | 変更前 | 1 | 1297 | 0 | 36→65 |
| new16-w | 新 | 16 | 226 | 2 | 65→82 |
| new16-2 | 新 | 16 | 238 | **149** | 82→78 |
| old-3 | 変更前 | 1 | 1113 | 0 | 78→14 |
| new16-3 | 新 | 16 | 119 | 0 | 14→10 |
| new1-1 | 新 | 1 | 551 | 0 | 10→77 |

同じ時間帯に他 wave の mutation harness が `dev-wave-jobs/<x>/scratch` や `.izanagi-mutation-worktree`
(1 本 26,000 file) を生成・削除している (探索根の churn)。走査中に消えた directory は逐次版でも
`os.walk` の `onerror` で数えられるはずだが、逐次版は 4 走とも 0 で、並列版だけ高負荷の窓で 2〜149 が出る。
帰属候補: (a) churn (並列版は 1 秒あたりの scandir 数が 10 倍で、削除中の tree に当たりやすい)、
(b) Lustre が高負荷で返す一時 errno (EINTR / ESTALE 等) を `os.scandir` が OSError にして
`onerror` が数える、(c) 並列版固有の欠陥 (存在する directory を失敗と数える)。
path と errno と走査後の存在有無が分かれば (a)(b)(c) を分けられる。
