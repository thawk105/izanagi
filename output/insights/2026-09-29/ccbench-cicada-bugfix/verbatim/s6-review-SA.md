## 所見

1. **must-fix — R4/R5(a) の起動位置が固定されている。** [build_genomes.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/build_genomes.py:24) の `parents[4]` は、レビュー対象の配置では `/work/SFC` になり、意図した repo root ではありません。import または policy 読み込みが失敗し、24 genome と W5 の数値を取得できません。repo root を明示引数で受け、存在と内容を検査してください。

2. **must-fix — 空の小走行が合格し得る。** [launch_cicada_run_g.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:672) は `indeterminate`、cycle 0、C 行 0、commit 数 0 を合格にします。判定器も空 trace を `indeterminate` とします（[model.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-ccbench-cicada-bugfix/orchestrator/verifier/model.py:554)）。放置すると R6 の未実行 cell が緑になります。`expected_commits > 0` と判定器の `stats.txns > 0` を要求し、`indeterminate` の CLI rc は 3 と照合してください。

3. **must-fix — R6/W5 の実効 flag と compile 定義を照合していない。** 起動器は CMake cache を確認しますが（[launch_cicada_run_g.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:943)）、対象 TU の `compile_commands.json` の `-D` と走行 stdout の `#FLAGS_*` を確認しません（[同ファイル](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/launch_cicada_run_g.py:798)）。放置すると誤った promotion／待機 build、または flag 0 の走行を G の結果として記録できます。各 target の Cicada TU と各 run の flag を期待値に照合してください。

4. **must-fix — CI の合格条件が rc だけになっている。** [run_ci_build.sh](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/run_ci_build.sh:132) は実行 file 数を数えますが、34 本か確認せず、CCBench の warning／error 数も判定しません。放置すると R7 の「34 本、警告・error 0」と異なる report でも rc 0 になります。対象を限定して数え、両条件を合格判定に入れてください。

5. **should — R4 の正準集合の件数が固定条件として検査されない。** [build_genomes.py](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/build_genomes.py:237) は `model.genomes()` の返値をそのまま使い、最後も生成した `specs` の件数と成功数を比べるだけです（[同ファイル](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/build_genomes.py:292)）。集合が変わると 24/24 でない成功を緑にできます。正準 24 点の件数・一意性・集合、および追加 2 点を事前登録値と照合してください。

6. **should — D297 の bundle head が G と照合されない。** [run_judge.sh](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/run_judge.sh:53) の照合は正しい一方、[run_ci_build.sh](/work/SFC/tanab/tmp/ccbench-cicada-bugfix-20260929/scripts/run_ci_build.sh:35) には同等の確認がありません。G を checkout するので D297 の測定対象は保たれますが、R7 の「G が head の complete-history bundle」という一次資料の束縛を証明できません。CI 側にも単一 head = G の確認を加えてください。

## 判定 (GO / NO-GO)

**NO-GO。** 特に空 trace の偽の緑と R6/W5 の flag 未照合を修正してから投入すべきです。

## 総括

静的検査のみで、編集・実走はしていません。診断 patch の差分は指定の `#error` 1 行削除と hunk 行数修正だけでした。計装の C 行は `C txid thid …`、W 行は `W …` なので、現行の thid 別 C 行数と P の W 行数の数え方は形式に合っています。F／C の OID と expected path の値も裁定に一致します。