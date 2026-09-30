## 総括

**NO-GO。** 実読した差分に、計測後の作図を止める schema 不一致と、事前登録した投入判定を満たさない smoke 手順がある。計器入り build の実走と inert witness は未確認であり、この結論は静的レビューによる。

## 所見

1. **must-fix — measure raw を作図器が拒否する。** driver は raw の `schema_version` を常に `1` とする一方、作図器は `3` のみ受理する（[driver:932](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:932)、[作図器:166](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/tools/plotting/plot_vhash_workload_space.py:166)）。**影響:** 504 走の raw が揃っても全点表・候補領域を生成できない。**推奨:** raw と計器内 JSON の schema を区別して契約を一致させ、driver 出力を作図器へ渡す結合検査を加える。

2. **must-fix — 登録した smoke と予算判定が実装されていない。** README §1.6 は全 build キーと極端な W 条件の実測を要求するが、`_smoke` は旧 A/T の短い走だけを測り、見積りも `258 ×` 旧走時間で計算する（[README:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/output/insights/2026-09-30/vhash-workload-space/README.md:153)、[driver:804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:804)、[driver:868](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:868)、[driver:897](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:897)）。**影響:** 1000 操作・1000 B・長い tx の時間と maxrss を見ずに、計測可否と縮小判断が変わる。**推奨:** R11 の極端条件と全 build キーを smoke で測り、その時間・maxrss から 504 走と縮小後の見積りを計算する。

3. **should — abort 理由の公開名が driver と作図器で食い違う。** 同じ配列位置を driver は `latest`／`scan_node_set`、作図器は `rmw_delete_latest`／`node_insert` と呼ぶ（[driver:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:64)、[作図器:36](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/tools/plotting/plot_vhash_workload_space.py:36)）。**影響:** abort 件数は保たれても、一次資料へ載せる理由別の値が別の失敗箇所として読まれる。**推奨:** 理由名と順序を一つの定義に統一する。

4. **should — H4 候補の中央値は lag 側を評価しない。** H4 は lag または live で通過する仕様だが、領域の順位付けには常に `live_ratio` の中央値を使う（[作図器:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/tools/plotting/plot_vhash_workload_space.py:323)、[README:148](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/output/insights/2026-09-30/vhash-workload-space/README.md:148)）。**影響:** 同じ通過率の lag／停止領域の順位が版数で決まり、第 2 段の候補領域が変わり得る。**推奨:** H4 の順位指標を事前登録文に明記し、lag・停止・live の別判定に沿って実装する。

## 確認して問題なかった点

- W 条件の生成ループは S 72 点、O1/O2 各 27 点を各 2 genome で登録する形で、README §1.2 の件数と一致する（実読）。
- W の argv は records・全 worker の操作数・通常／batch thread 数・batch 1000 操作を条件から設定し、best100 の定義も登録値と一致する（実読）。
- 子 process の maxrss は `wait4` の `ru_maxrss`、走行 timeout は 180 秒（実読）。
- 鎖長走査は最後の `TxExecutor` 破棄時に起動する。CCBench の worker は executor をローカルに保持してループ終了後に破棄し、runner が全 worker を join するため、通常終了経路では並行する worker の install・GC は残らない（[patch:281](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/patches/instr-cicada-version-lifetime.patch:281)、[runner:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/external/ccbench/common/runner.hh:183)、[runner:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/external/ccbench/common/runner.hh:299)、実読）。
- R3 の read 分母下限、H2 の候補・commit 下限、2 反復の境界、公開 0 回の「停止」はコード上で確認した。計器 patch の既定 build のバイナリ同一性と condition gate の実効発火は、親の未実走項目なので確認済みとは扱わない。