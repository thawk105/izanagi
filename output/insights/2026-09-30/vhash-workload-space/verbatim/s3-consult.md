## 総括

**条件付き GO。** L27 の列割付は二因子について直交する。計測前に、md_28 の格子の欠落、H4 の判定不能条件、候補領域の選択規則を直す必要がある。以下は指定資料とコードの静的な実読に基づく。実走結果は確認していない。

## 所見

1. **must-fix — md_28 の長い read 条件が格子から抜ける。** 根拠: md_28「skew 0.9, 0.95, 0.97, 0.99 × rr5/50/95 × 通常／操作数が多い長い tx」、[brief P1](/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/brief.md) と[親メモ N1](/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/stage3/parent-notes.md)。S 層の長い tx は batch1000U だけで、batch1000R は疎な O 層にしかない。**放置すると**高 skew で長い read が鎖長・GC に及ぼす変化を軸ごとに結論できない。**推奨:** md_28 の「長い tx」が U・R のどちらを指すか登録時に明記し、両方を結論に使うなら該当する skew×rr の格子を確保する。

2. **must-fix — H4 の AND 述語は GC 停止を見落とす。** 根拠: [brief P4](/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/brief.md)、[plan:49](/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/stage2/plan.md:49)、[driver:323](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:323)。境界 p50 は公開が 0 回なら算出不能で、read が支配的なら生存版数も 1.1N に届きにくい。**放置すると**親メモ N2 が重要視する GC 公開停止を H4「小」と扱いうる。**推奨:** 公開 0 回を右打ち切りの別状態にし、境界遅延と版の蓄積を別々に判定する。

3. **must-fix — 候補領域の支持点数だけでは安定性を示せない。** 根拠: [親メモ N5](/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/stage3/parent-notes.md)、[plan:46](/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/stage2/plan.md:46)。L27 では二水準の組の支持は各表でちょうど 3 点であり、「支持点 ≥3・過半通過」は 2/3 点で成立する。S 層の集中点も全域の通過率を偏らせる。**放置すると**偶然の通過や層の配分が第 2 段の候補領域を決める。**推奨:** S/O を分けた支持数と通過率、各反復の値を公開し、領域選択には両表または隣接水準での再現を要求する。3 件未満なら不足と報告する。

4. **should — H2 の abort 条件が極端な失敗負荷を優先する。** 根拠: [brief P4](/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/brief.md)、候補計数の[patch:515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/patches/instr-cicada-version-lifetime.patch:515)、[driver:332](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:332)。abort 率 ≥5% には上端がなく、少数の成功 read でも候補率が閾値を越えうる。**放置すると**ほぼ進行しない負荷が「前進の有望領域」になる。**推奨:** 分母・候補の実件数と commit 数の下限を事前登録し、abort 100% は別扱いにする。「上限」は観測時点の候補頻度に限ると記す。

5. **should — bytes の見積りが payload の実寸を過小評価しうる。** 根拠: [plan:31](/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/stage2/plan.md:31)、[ycsb.hh:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/external/ccbench/include/ycsb.hh:40)、[heap_object.hh:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/external/ccbench/include/heap_object.hh:95)。値は `YCSB` オブジェクトとして確保され、`VAL_SIZE` 以外に id と alignment がある。**放置すると**値サイズ別の生存 bytes の差を小さく報告する。**推奨:** `sizeof(YCSB)` も echo して版本体と確保 payload の概算を示し、共有・再利用待ちと RSS との差を明記する。

6. **should — 5 秒／走は今回の予算根拠にならない。** 根拠: [plan:63](/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/stage2/plan.md:63) は短い既存条件の job 平均であり、[driver:448](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:448) は 180 秒 timeout。**放置すると**1000 操作・高 skew・大値の反復や timeout で 2 node 時間を超える。**推奨:** 親メモ N6 の極端条件 smoke を先に実走し、build 重複・失敗走・追加検査を含む実測上限で投入を判定する。1 万・10 万 record の「L3 に収まる」も値サイズと build ごとの footprint を見るまで断定しない。

7. **should — md_28 の図と現実性の節が作図計画に明記されていない。** 根拠: md_28「位置 ≥1 / ≥8、前進候補率、abort 率の skew 図」「現実性を 1 節」、[plan:39](/work/SFC/tanab/tmp/vhash-workload-space-2026-09-30/stage2/plan.md:39)。**放置すると**H 別の地図はあっても、依頼された skew の連続した読み方と用途上の限界が欠ける。**推奨:** skew 別の三つの図、熱いキー数と鎖長の表、出典を確認した現実性の節を成果物の要件に固定する。

8. **nit — 終了後の鎖走査は走行中の計器値を汚さない設計だが、driver の壁時計には入る。** 根拠: worker の join は[runner.hh:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/external/ccbench/common/runner.hh:299)、現行 JSON は[patch:304](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/patches/instr-cicada-version-lifetime.patch:304)で終了時出力、`wall_s` は[driver:481](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-vhash-workload-space/orchestrator/campaign/vhash_cicada_vlife.py:481)で記録する。**放置すると**鎖走査時間を負荷の走行時間や性能差と読み違える。**推奨:** 走査時間を別記し、診断 build の `wall_s` と throughput を性能値に使わない。明示出力と schema 3 は旧 schema 2 の parser・consumer を残したまま、既定 build の inert witness で確認する。

## 削れるもの

- abort 理由の全失敗箇所への細分類は重い。第 2 段のふるい分けには既存の `aborts/attempts` があり、理由が必要ならまず early／validation／other 程度に絞れる。ただし md_28 の「理由」自体は残す。
- 2 本目の L27 と細かな負例 fixture は、極端条件 smoke 後の予算が厳しければ縮小候補。ただし削る前に候補領域の支持点不足を再計算する。
- PDF と PNG の二重生成より、全点表・反復点・生成器を優先できる。

## 足りないもの

- 公開 0 回、分母 0、少数観測、timeout、abort 100% をそれぞれどう表示し候補選択からどう扱うかの登録規則。
- 鎖長の走査失敗・循環・未発見 key の扱いと、`key=0..7` が**実現した**熱さを示す値ではなく Zipf 上の順位であるという区別。
- 二反復で閾値近傍を判定する規則。二反復は地図の探索には使えても、境界付近を安定した領域と断定する根拠には足りない。