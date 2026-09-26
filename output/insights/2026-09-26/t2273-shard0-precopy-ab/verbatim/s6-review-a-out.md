## 所見

- **RA1 — must-fix** — [runner:650–654](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_runner.py:650)、[analyzer:895–896](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:895)。P の実行環境には `T2273_PRECOPY=1` を渡すが、`run.json` には記録しない。`intervention_env` は全対で偽になり、効果があっても有効な対にならない。実際の child 環境値を記録すること。加えて `T2273_LOCAL_OUTPUT_SOURCE` に入れた文字列 `"T2273_PRECOPY"` は既存 `--pair-dir` の A2 判定も壊すため、未設定時は `None` に戻すこと。

- **RA2 — must-fix** — [plugin:465–501](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_plugin.py:465)。P は最初の `pytest_configure_node` で対象 module を main thread に同期 import してから写し thread を起動する。import の所要が P の worker 起動と早期 memo 開始を遅らせ、P の pre と Δ に片側だけ加算される。import と写し作成を thread 内へ移し、hook では identity と thread の起動だけを行うこと。

- **RA3 — must-fix** — [plugin:38–47](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_plugin.py:38)、[元関数:895–899](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/orchestrator/tests/test_s8b_oracle_driver.py:895)。stat digest は directory の `st_size` も含む。A の ignore 付き copytree と P の二段 copytree で directory size の一致は保証されず、内容が同じでも対が無効になり得る。file の path・size・mode・mtime_ns を比較し、directory は path 集合を別に比較すること。file の mtime・mode は現行 digest に入っており、相違を通す経路は見当たらない。digest span は両条件とも builder 内の複製直後に置かれている。

- **RA4 — should** — [analyzer:839–920](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:839)。`valid` は `analyze()` の `missing` を見ない。test span の欠落、selected/finished 不一致などが残っても有効と判定し得て、W の解釈を誤る。P で構造上生じる `copy.list` 欠測だけを明示的に扱い、それ以外の必須観測欠落を無効条件に入れること。

- **RA5 — should** — [analyzer:933–978](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:933)。早期 memo 超過で外した対も、条件別中央値・順序別対差・phase 集計に混入する。また有効 3 対未満でも「(b) の候補」を推奨する。集計は有効対に限定し、3 対不足は判定保留にすること。Δ の符号、r の分母、3 対基準式自体は裁定どおり。

- **RA6 — should** — [analyzer:897–900](/work/1/SFC/tanab/izanagi/.claude/worktrees/author-t2273pc-probe/tools/t2273_replica_analyze.py:897)。早期 memo 超過を pytest log の語句だけで数えるため、実際の待ち超過が別表現なら条件別件数から漏れる。待ち結果を構造化して記録し、その値で除外・集計すること。

## 総括

**修正後 GO。** 現状は RA1 により正常な A/P 本走も有効対にならない。RA2 は P の pre と効果値に片側だけ費用を加える。発行 child の AST 変換では、指定された文の順序・`sys.argv` 添字・stdout JSON を変える明白な箇所は見つからなかった。実装報告は smoke と本走を「未実走」と明記しており、実測済みとの誤記はない。