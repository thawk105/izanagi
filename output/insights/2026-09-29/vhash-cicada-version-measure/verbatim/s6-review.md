## レンズ A の所見

1. **must-fix** — [patch:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:25) などの `#line N "cc/cicada/…"` は、行番号に加えて `__FILE__` も変更する。stock の `ERR` は [debug.hh:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/external/ccbench/include/debug.hh:54) の `NNN` を通じて `__FILE__` を出すため、**既定 patch の前処理結果と `.rodata` は stock と一致しない**。`.text` への波及は未 compile なので未確定だが、inert witness は現状成立しない。`#line N` としてファイル名を保つ必要がある。

2. **must-fix** — [test_vhash_cicada_vlife.py:142](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:142) は include を削除し、[同:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:153) はファイル名を捨てて行番号だけ比較するため、所見 1 を検出できない。[driver:278](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:278) の `objdump -d` 比較も `.text` の生バイト比較ではなく、`.rodata` を検査しない。放置すると、実際には不一致の既定 build を inert として一次資料に載せうる。行番号の戻し先はテスト上の数値比較では一致しているが、実 compile command と include を通した証拠はまだない。

3. **must-fix** — [patch:154](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:154) の `VLIFE_VISIT` は、pending 版を最初に見たとき記録せず、stock が待機して committed に変わった後も再評価しない（stock [transaction.cc:108](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/external/ccbench/cc/cicada/transaction.cc:108)）。放置すると、先頭 K の committed 候補や選択版の直上 wts を落とし、候補率を誤る。

4. **must-fix** — [patch:232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:232) の `read_zero` は深い read に限らず「最初の成功 read」すべてを数える。放置すると、裁定の「既読 0 件」の深部候補を raw から分離・照合できない。

5. **must-fix** — [patch:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:363) と [同:372](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:372) の readcheck 位置は `later_ver_` から数えるが、裁定の位置は latest からの物理位置である。放置すると、site 間の位置ヒストグラムを同じ物理位置として比較した図・結論が誤る。追加の鎖走査なしで直せる範囲を明示する必要がある。

6. **must-fix** — [driver:399](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:399) の `--records` は任意の正整数を受け、smoke の選定結果との照合がない。放置すると、条件表以外の N による measure raw を正式データとして生成でき、一次資料の較正根拠が切れる。

7. **must-fix** — [plot:110](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:110) の図 1 は hops だけで選択版の位置を描かず、[同:145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:145) の図 3 は採取した生成基準・上書き基準の回収時年齢を描かない。放置すると、要求された版位置・保持時間の結論を図 3 枚から確認できない。

8. **should** — [plot:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:98) の provenance は入力 SHA と条件表を持ち、95% CI は [同:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:25) で t 分布を使う。一方、図・caption に測定条件を表示しておらず、FIGURE_CONVENTIONS §6 の要件を満たさない。放置すると図単体で条件を読めない。

9. **should** — [driver:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:329) の較正 probe は、[同:229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:229) の本走と違って各起動直前の単一テナント確認をしない。放置すると競合中の maxrss を N 選定に使いうる。

長短別の試行・commit・abort・操作数・cycles、worker 0 の GC 公開計数、worker join 後の JSON 出力、24 条件の値、登録件数 63／46、`NON_ADMISSIBLE` は、読んだ範囲では裁定と整合する。`CicadaYcsbWorkload::run` の RETRY、abort、commit 計数、leaderWork、quit、read-only 判定も stock と対応する。C++ は未 compile であり、これらは静的判定に限る。

## レンズ B の所見

1. **should** — [driver:421](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/campaign/vhash_cicada_vlife.py:421) は measure ごとに使わない stock binary を build する。削れば条件付き gate や enabled build の証拠は維持したまま、計算ノードの所要と最初の失敗点を減らせる。

2. **should** — [plot:147](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/tools/plotting/plot_vhash_cicada_vlife.py:147) は時間値そのものではなく bucket 番号の加重平均を描く。削って分位点または各 bucket の割合を raw から描けば、失うのは擬似的な「平均 bucket」だけで、GC の時間解釈が明確になる。

3. **nit** — [patch:579](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/patches/instr-cicada-version-lifetime.patch:579) は stock の `run` 本体をほぼ複製している。将来の stock 修正との乖離点が増えるため、局所化できるのは batch 手続き生成と操作数計数の部分。ただし共有 `include/ycsb.hh` を触らない裁定を優先するなら、この複製には理由がある。

## 変異 MUT-1〜5 の被覆

- **MUT-1: KILLED 見込み。** [test:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:54) が重複 JSON 行を拒否する。変異実走は未確認。
- **MUT-2: KILLED 見込み。** [test:97](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:97) が patch の `>=` 行を文字列で固定する。ただし実際の C++ 境界動作を検査する test ではない。
- **MUT-3: KILLED 見込み。** [test:158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:158) は既定時に露出した計器文を検出する。ただし include とファイル名を除くため、inert witness 全体の証明にはならない。
- **MUT-4: KILLED 見込み。** [test:105](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:105) が重複条件 ID を拒否する。
- **MUT-5: KILLED 見込み。** [test:78](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-cicada-version-measure/orchestrator/tests/test_vhash_cicada_vlife.py:78) が read-only 深部 100 件を候補分母から分離して確認する。

これはテスト構造からの判定であり、変異体を実走して得た KILLED 記録ではない。

## 総括

**NO-GO。** must-fix は、① `#line` による `__FILE__` 変更と不十分な inert witness、② pending 確定後の候補記録、③既読 0 件の深部計数、④ site の物理位置定義、⑤ measure の N と smoke の束縛、⑥版位置・保持時間を欠く図。親が並行している焦点テストと計算ノード smoke の結果は、この静的レビューには含めていない。