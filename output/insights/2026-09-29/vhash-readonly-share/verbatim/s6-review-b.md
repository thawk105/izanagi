## must-fix

- **既定 genome の照合値が実際の既定値と違う。** 根拠: [driver:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:96) は `INLINE_VERSION_PROMOTION=0` を要求するが、[Options.cmake:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/external/ccbench/cmake/Options.cmake:31) の既定値は `1`。**影響:** 既定 genome の stock build で smoke が止まり、86 条件を測れない。**推奨:** 既定値を `1` に直し、既定・調整済み双方の compile command fixture を検証する。

- **レコード数が段 4 補遺の 1M 固定になっていない。** 根拠: [driver:560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:560) と [driver:648](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:648) は較正結果から 2M・4M も選び、[driver:818](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:818) がその値で計測する。**影響:** 版の深さ、境界年齢、md_2 との比較条件が変わる。**推奨:** この wave の計測値を 1M に固定し、smoke でも 1M を要求する。

- **ro 深部割合の分子と分母が異なる read 集合を数える。** 根拠: [patch:519](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/patches/instr-cicada-version-lifetime.patch:519) は deleted 判定前に `readonly_deep` を増やし、[patch:542](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/patches/instr-cicada-version-lifetime.patch:542) は選択版を得た後に `readonly_reads` を増やす。**影響:** 図 1 の ro 深部割合が過大になり、場合によって 100% を超える。**推奨:** 両方を選択版取得後の同じ位置で数える。

- **調整済み T 条件が4図の値に使われていない。** 根拠: [作図器:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/tools/plotting/plot_vhash_readonly_share.py:21) は T を入力必須にする一方、描画は [作図器:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/tools/plotting/plot_vhash_readonly_share.py:87) など全て R セルを参照する。**影響:** 補遺で追加した「調整済み Cicada でも ro の深い探索が残るか」を図から判断できない。**推奨:** T と対応する R の深部割合・境界年齢を同じ図で比較する。

## should

- **見積り (a) の名称を裁定の定義に合わせる。** 根拠: [作図器:269](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/tools/plotting/plot_vhash_readonly_share.py:269) は “Optimistic eligibility on observed chains” とだけ記す。**影響:** 先頭 K 版・既読区間に限定した率が、一般的な適格率として読まれる。**推奨:** 題名か凡例に「観測鎖・先頭 K 版・既読区間に限定した楽観的適格率」を明記する。(b) の「公開間隔に対する局所的な機会量」は現行の題名・caption で概ね表現できている。

- **D-F の反復差は対応づけの根拠がない。** 根拠: [作図器:183](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/tools/plotting/plot_vhash_readonly_share.py:183) と [作図器:217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/tools/plotting/plot_vhash_readonly_share.py:217) は条件ごとの `rep` 番号を対にして CI を計算するが、[driver:844](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:844) は条件単位で3連続走を実行する。**影響:** 図 3 の誤差棒が実験上の対応を持たない差の分散になる。**推奨:** 反復のブロック順を事前に固定して実行するか、非対応の条件平均差として不確実性を計算する。

- **smoke の所要見積りは投入判断の保守性を示せない。** 根拠: [driver:770](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:770) は1秒走の最大 wall に2秒を足して258倍し、build は enabled 2種の最大値を12倍する。依存準備と stock/default build の実測値は式に入らない。**影響:** 2 node 時間未満と判定しても実消費が超過しうる。**推奨:** 3秒の代表走を既定・調整済み双方で測り、4 job の全 build・準備時間を足す。8秒/走、180秒/build なら概算は `258×8＋12×180＝4,224秒`、4 job 均等割の壁時計は約18分に準備時間を加えた値となる。

- **各セルの速度値は raw にあるが、作図器の反復集計には入らない。** 根拠: [driver:473](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/orchestrator/campaign/vhash_cicada_vlife.py:473) は update commit/s・install/s を `run.summary` に追加する一方、[作図器:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/tools/plotting/plot_vhash_readonly_share.py:143) は `parsed` から `summarize` し直すため両値を落とす。実現 ro 率と abort 率は残る。**影響:** 図の provenance だけでは裁定が求める各セルの5指標を照合できない。**推奨:** raw の `run.summary` を照合して取り込むか、作図器の集計時に `extime` を使って速度を再計算する。

## nit

- **README の patch entry が旧説明のまま。** 根拠: [patches/README.md:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/patches/README.md:14) と [patches/README.md:845](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-readonly-share/patches/README.md:845)。**影響:** 計器の新しい用途と schema を登録簿から追えない。**推奨:** 裁定で許可された entry を更新する。`ledger.json` を変更しない判断は裁定どおり。

- **実機の build・計測・4図生成は未確認。** 根拠: [実装報告:実走した test](/work/1/SFC/tanab/tmp/vhash-readonly-share-2026-09-29/codex/out/s5-author.md) は `rc=16` で pytest 子が起動していないと明記する。**影響:** ここでの評価は静的検査の範囲に限られる。**推奨:** 親の段 7 で condition gate、compile command、inert witness、実 raw 作図を実走する。

## 削れるもの

- **新規 framework や互換層の追加は見当たらない。** 根拠: [差分](/work/1/SFC/tanab/tmp/vhash-readonly-share-2026-09-29/author-r1.patch) は既存 driver・patch・test、許可された作図器と件数 pin に限る。**影響:** 削除によって主要な測定値を改善する箇所はない。**推奨:** 広い削減より上記の局所修正を優先する。

## 総括

**NO-GO。** 既定 genome 照合で smoke が止まる見込みが強く、1M 固定、ro 深部割合、調整済み T の図示にも成果物へ直接影響する欠陥がある。condition gate の VLIFE 37・LONGTX 3、既存 token 集合、起動関数数については、差分上の新規取りこぼしは確認できなかった。