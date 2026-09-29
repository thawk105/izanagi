## 1. 所見

1. **must-fix — trace の patch 適用順が保存時に壊れる。** [driver:74](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:74) は manifest のキーをソートし、[driver:324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:324) は patch の順序を辞書キーにしている。[driver:828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:828) で再読込すると、trace は裁定の `instr → variant` でなく `variant → instr`、壊しは `broken → instr → variant` の順に厳密適用される。放置すると trace 19 走が開始できず、正しさの受入と性能図が作れない。**修正案:** 順序付きの patch 名配列を manifest に別途保存し、hash 辞書は照合専用にする。

2. **must-fix — 正常な trace 判定を集計が拒否する。** [driver:673–678](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:673) は巡回 0 の verdict に `indeterminate` だけを許すが、verifier は非空・非巡回・integrity clean を `serializable` と返す（[model.py:554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/verifier/model.py:554)）。放置すると正常な trace を含む aggregate が失敗し、数値と図を生成できない。**修正案:** rc・巡回数・integrity を直接確認し、巡回 0 の正常 verdict を受け入れる。判定の上限を一次資料では裁定どおり表現する。

3. **must-fix — COUNT の実行時間だけ 1 秒になる。** [driver:374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:374) は裁定 §2.3 の共通 `extime=3` に反する。放置すると探索長、snapshot 遅れ、書込み費用、実現 ro 比率が性能走行と異なる時間窓の値になり、一次資料の対比が歪む。**修正案:** COUNT も 3 秒に揃える。

4. **must-fix — 共有に失敗すると各実行 job が17 binary を再 build する。** [driver:805–813](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:805) は裁定の「build 1 回」を破り、その時間を事前の [estimate:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:181) に含めない。放置すると 2 node 時間の上限を超えても投入されうる。**修正案:** 共有できなければ投入を止めるか、各 job の再 build を smoke で実測してから上限を再判定する。

5. **should — smoke の build 時間を二重計上する。** [driver:833–840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:833) の `smoke_seconds` は build を含むが、[estimate:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:181) はさらに `build` を加える。放置すると 12 cell・6 round が不要に縮小され、成果物の範囲が変わりうる。**修正案:** smoke を実際の投入単位として一度だけ数える。

6. **should — 図の誤差表示が裁定の集計と異なる。** [plot:63–78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/tools/plotting/plot_vhash_cicada_hot_block.py:63) は平均と95% t 区間を描き、[plot:59](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/tools/plotting/plot_vhash_cicada_hot_block.py:59) にもそう記す。裁定 §2.3 は全点・中央値・最小〜最大で、有意性を述べない。放置すると図の中心と範囲が一次資料の指定値と違う。**修正案:** 全点、中央値、最小〜最大を描く。

7. **nit — README の既存「壊し3本」の重ね方は新規2本を含まない。** [patches/README.md:930](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/patches/README.md:930)。放置すると手順の読み違いを招くが、直前の新設節には正しい順序がある。**修正案:** 既存文の対象を旧3本と明記する。

**不成立:** `wait4` の `ru_maxrss` は [driver:557–591](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-hot-block-cicada/orchestrator/campaign/vhash_cicada_hot_block.py:557) で対象 child ごとに取得している。cell の ro・GC・rr 引数、腕の巡回、round の node 割付、`sizeof(Tuple)` の実行時 probe にも、静的検査で別の欠陥は確認しなかった。禁止された所有外 patch、`external/ccbench` gitlink の変更も差分にない。

## 2. 裁定 §2〜§5 への適合表

| 項目 | 判定 | 根拠 |
|---|---|---|
| §2.1 hot 配置・atomic 記述子・reader/writer/GC | 未検査 | patch は設計形に沿うが、実行時の競合と寿命は静的検査では確定できない |
| §2.1 COUNT の計数・WL・inert | 未検査 | schema と分岐はある。前処理一致・実現比率の実走は未確認 |
| §2.2 B1/B2 事象と帰属 | 未検査 | 記録・帰属コードはあるが、発火と witness は未実走 |
| §2.3 17 binary と build 共有 | **不適合** | patch 順序の破損、共有失敗時の全再 build |
| §2.3 360 perf・20 COUNT・19 trace の計画 | 適合 | plan の件数と round 割付は一致 |
| §2.3 共通 argv・図3枚 | **不適合** | COUNT の `extime`、図の中心・範囲 |
| §3 正しさの門・aggregate | **不適合** | 正常 verdict を aggregate が拒否 |
| §4 smoke 見積り・2 node 時間 | **不適合** | build 二重計上と再 build 時間の欠落 |
| §5 M1〜M6 の単一理由性 | 未検査 | 合成 test はあるが、変異を実際に適用した赤確認はない |

## 3. 実装子報告の主張の検算

- **成立:** U1 の報告どおり、variant と壊し patch は指定の新規 file にあり、所有禁止 file の変更は差分にない。U2/U2f の 17 build、360/20/19 run の計画件数と COUNT schema の接続も静的には一致する。
- **不成立:** U2 の「build を共有し、各 job は manifest を読む」という主張は、共有失敗時の全再 build により無条件には成立しない。U2f の「実物形式の照合」は aggregate の正常 verdict 拒否と、manifest 再読込時の patch 順序を検出できていない。
- **未検査:** U1 の厳密適用・構文確認、U3 の site 数、各報告の `py_compile` 成功は報告上の結果として扱う。指定どおりテスト・build を再実行していない。報告自身も pytest と実計測は未実走としている。

## 総括

静的レビューで、trace 実行を止める patch 順序と、正常 trace の集計拒否を確認した。これらを直すまで正しさの受入と3図は生成できない。COUNT の時間窓と計算上限の扱いも、計測開始前に修正が必要。テスト・build は実行していない。