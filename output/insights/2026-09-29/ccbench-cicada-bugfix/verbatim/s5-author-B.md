## 変更内容

作成・編集したものはすべて `R/scripts/` 配下です。tracked file、`R/ccbench`、流用元は編集せず、commit もしていません。

| script | 引数・出力・流用元との差分 |
|---|---|
| [build_genomes.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/build_genomes.py) | 指定の `--bundle`、G/F OID、依存 cache、scratch、out、並列数を受けます。F→G の親・2 path を build 前に照合し、24 正準 genome、ADD_ANALYSIS の 2 点、W5 を build します。build の rc・時間・`-D` 照合・binary SHA256 と、W5 の各 run・予測比較を `report.json` に記録します。較正 driver の設定と workload を流用し、待機量は runtime flag に移しました。 |
| [launch_cicada_run_g.py](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/launch_cicada_run_g.py) | md_17 起動器を G 専用の 5 build・指定 cell に限定しました。`--new-oid` と `--bundle` を検査し、`--dry-run` で patch 適用を確認できます。結果 JSON に source OID、CMake cache、patch SHA256、判定器値、thid 別 C 行数、P の W 行数、W5 の直接証拠を残します。判定器は変更していません。 |
| [run_ci_build.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/run_ci_build.sh) | T-2854 版を複製し、直親 F と F→G の 2 path 照合に更新しました。image 実行、依存 clean clone、report 形式は流用元どおりです。 |
| [run_judge.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/run_judge.sh) | T-2854 版を複製し、直親 F、C→G の辞書順 5 path に更新しました。old=C、bundle head=G、GCC 11/12 並行判定は維持しています。 |
| [check_format_ci.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/check_format_ci.sh) | T-2854 版を複製し、冒頭に引数・出力・rc の説明を追加しました。 |
| [check_patch_apply.sh](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/check_patch_apply.sh) | clean detached checkout と patches dir を受け、Cicada を触る patch の単独検査と既定順の重ね適用を一時 clone で確認します。各段の rc と offset 表示を JSON に記録します。 |
| [診断 patch](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/instr-cicada-trace-promotion-diag.patch) | 元の計装 patch から指定の `#error` 一行だけを除き、該当 hunk の行数を修正しました。差分の機械照合は一致しました。 |

## 実走した command と rc

- `bash -n`（shell 4 本）、`python3 -m py_compile`（Python 2 本）: **rc=0**。
- `check_format_ci.sh R/ccbench /usr/bin/clang-format`: **rc=0、213 file**。image 版は通常起動 **rc=1**、`--userns` 付きでも sandbox の socket permission で **rc=255** となり、format 判定に至りませんでした。
- `check_patch_apply.sh R/ccbench patches …/patch-apply-F.json`: 修正版で **rc=0**。F では単独 10 本中 3 本が適用可、重ね順 7 系列は各段を適用できました。offset の有無と個別結果は [patch-apply-F.json](/work/1/SFC/tanab/izanagi/.codex/worktrees/md19-cicada-fix-b/output/runs/md19-cicada-fix/scripts/patch-apply-F.json) にあります。初回実行も rc=0 でしたが、相対 patch path の不備で全件を誤判定したため破棄し、絶対 path に直して再実走しました。
- 診断 patch の F への `git apply --check`: **rc=0**。F clone の終了時 `git status --porcelain --ignored` は空です。
- 計算ノード用 script のログインノード自己確認: `build_genomes.py` **rc=2**（bnode 制限）、起動器の F を指定した `--dry-run` **rc=2**（G の親・path 条件不一致）、CI build／judge の引数不足 **各 rc=2**。

## 未実走・残る懸念

G の OID と bundle はまだ渡されていないため、G 上の `--dry-run`、build、benchmark、CI build、D297、patch 適用は**未実走**です。F の patch 結果を G の結果とは扱いません。image format も上記の起動制約により未判定です。

## 総括

R4〜R9 の job body と診断 patch を `R/scripts/` に実装しました。ログインノードで可能な構文確認と F の format・patch 検査は済みました。G を使う受入判定は親の計算ノード投入後に必要です。