# 親の追加実測 (段 2 投入後、login pegasus、load ≈ 21〜27) — 段 3・4 の入力

probe script (repo 外): /home/SFC/tanab/.claude/jobs/45167654/tmp/probe_batch.py, probe_batch2.py, probe_lstree_full.py, probe_gitcost.py
対象: worktree HEAD 34af5a571、`CONTRACT_LOADER_RELATIVE_PATHS` 62 path (全件 mode 100644 / type blob)。
harden 引数・env は `contract_loader_binding._run_git` と同じもの (`--no-pager -c core.useReplaceRefs=false -c core.commitGraph=false -c core.fsmonitor=false --no-replace-objects`、GIT_CONFIG_GLOBAL=/dev/null 等)。

| 形 | 1 回分 (62 path) の所要 | 備考 |
|---|---|---|
| 現行: 逐次 62 process (`cat-file blob <commit>:<path>`) | 5.37 / 6.80 / 6.02 秒 | 1 process ≈ 0.04 秒 + 起動 |
| 1 process `cat-file --batch`、stdin に `<commit>:<path>` 62 行 | 1.566 / 1.289 / 0.904 秒 (別回: 0.647 / 0.618 / 0.940 / 0.751) | spec ごとに commit → tree を辿り直すため 1 process でも遅い |
| `ls-tree -r -z <commit> -- :(literal)<path> x62` (0.03〜0.06 秒) + oid 指定 `cat-file --batch` | **0.081 / 0.089 / 0.071 / 0.091 秒** | 2 process |
| 参考: full `ls-tree -r -z <commit>` (pathspec 無し、22,081 entry) を Python で filter | 0.172 / 0.106 / 0.078 秒 | pathspec magic を構造的に避ける代替 |
| 参考: 単発 `rev-parse --verify HEAD^{commit}` / `cat-file blob` 1 件 / `--batch` 1 件 | 0.036〜0.047 / 0.035〜0.046 / 0.035〜0.069 秒 | |

- 3 形 (逐次 / batch by path / ls-tree + batch by oid) の sha256 62 件は完全一致 (4 回とも `equal=True`)。
- 単体 profile (段 1 brief): `test_m10_empty_red_section_...` 47.5 秒のうち `_run_git` 704 回で 36.4 秒。
  内訳: `capture_contract_loader_binding` 5 回 (18.9 秒)、`verify_committed_contract_loader_binding` 4 回 (14.9 秒)、
  `verify_live_contract_loader_binding` 1 回 (4.9 秒)。`_read_regular_file_no_follow` 372 回で 4.3 秒 (posix.open 3.6 秒)。
- 親の推定: capture 1 回 = rev-parse + ls-tree + cat-file --batch の 3 process ≈ 0.15 秒 + disk 読取 62 件 ≈ 0.7 秒。
  同 test は 47 秒 → 約 12〜15 秒になる見込み (残りは fsync・tmp copy・disk 読取)。**この推定は login の値であり、
  計算ノードの 48 worker 同時 fork 条件では未測定。受入 A/B で確かめる。**
- ls-tree の pathspec は `:(literal)` を付けないと glob magic (`*` `?` `[`) が効く。現行 62 path に該当文字は無いが、
  fail-closed の観点で literal 指定か full listing のどちらかを採ること。
- `ls-tree` の出力に無い path (commit に存在しない) は fail-closed で `contract-loader-git-error` 相当にする。
  逐次版では `cat-file blob` が rc 128 で同じ error 種になっていた。
