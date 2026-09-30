---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-30
wave: dev-wave-vhash-hot-block-v2
seq: 2
---

## {{D:vhash-hot-block-post}}. VHash の hot block の書き込み側の排他を挿入の CAS の外へ出す設計 B-post は、CAS 後の短い書き区間で hot へ wts 順に書き足し、読み手の隣接確認で遅れた hot の安全を担保する overlay patch として入れる

**決定:**
1. **書き込み:** 版の挿入 (位置探索と先頭 / 途中の CAS) は stock のまま key ごとの書き区間の外で行い、CAS が成功した後にだけ短い書き区間を取って (wts, ptr) を hot の wts 降順の位置へ書き足す (列を辿らない。満杯で最小より古ければ落とす、同じ ptr は入れない)。書き足しは validation の中 (commit / abort の確定と次の begin より前) で終える。GC は D2311 のまま (gc_lock_ → 書き区間 → trim → 切り離し → 閉じてから再利用)。
2. **読み:** seqlock の copy から wts ≤ trts の最初の記述子 X = ptr[i] を選んだら、i = 0 なら `latest_ == X`、i ≥ 1 なら `ptr[i-1]->next_ == X` を acquire で確かめ、成り立つときだけ X と later_ver = ptr[i-1] を採る。外れたら latest からの stock の走査へ落ちる。cold (全件 > trts) は D2311 のまま最後の記述子から stock のループを続ける。
3. **hot の意味は「物理列の先頭の正確な写し」から「列の中の版を wts 降順に並べた K 件以下の手がかり」に弱める。** 正しさは隣接確認と pointer の生存 (書き手が自版を自 tx の中で hot に入れる、GC が再利用前に trim する) だけに依存させる。
4. **実装の形:** md_23 の variant patch の bytes を変えず、その上に重ねる overlay `patches/cicada-vhash-hot-block-post.patch` にする (新 macro なし)。条件 gate が数える exact な `#if CICADA_VHASH_*` 行の数を変えないことを overlay の契約とし、gate の登録は変えない。snapshot の遅れの計器の修正は別の overlay `patches/cicada-vhash-hot-block-count-v2.patch` に分けて全腕の計器 build に重ねる。
5. **計測と正しさの構成:** 性能は stock・md_23 の B・B-post を K ∈ {1, 8} で同じ job・round・cell・node に並べる。壊しは B-post の上に post 用 B1・B2 と、書き足しを省き隣接確認を外す stale-gap を置く。壊しの走の 180 s 打ち切りは判定なし (hung) として集計を止めず、正例の打ち切りは集計を止める。

**理由:**
- 実測 (一次資料 `output/insights/2026-09-30/vhash-hot-block-cicada-v2/README.md`): 書き区間の待ち / update commit は B の約 11 万サイクルから B-post K=1 の約 550 サイクルへ下がり、更新中心の cell の同時刻の stock 比の中央値は B の 0.224〜0.694 に対し B-post K=1 で 0.938〜0.991 だった。5 腕 × 3 trace cell で巡回なし (上限 indeterminate)、壊し 4 本は 2 cell ずつ検出・帰属した。
- 隣接確認があると、確認の瞬間の列で stock の第 1 段と同じ版・同じ later_ver を選ぶことに帰着でき、遅れた hot の隙間の版 (PENDING を含む) は stock の走査が見つけて待つ。隣接確認を外した壊し stale-gap は判定器に巡回として検出された。
- REUSE_VERSION の再利用による pointer の等値の誤り (ABA) は、「切り離し点の書き手は読み手の begin より前に終わり、その版は書き足し済みなので copy に居る」ことから起きないと論じた (stock と共通の寿命前提つき、段 6 レビューで反例不成立)。
- overlay にすると md_23 の B を同じ patch bytes で同時刻対照に置け、md_23 の記録の再現性を保てる。

**却下した選択肢:**
- 隣接確認なしで遅れを許す (ro は MinWts の性質、update は validation (a) が止めるという論証だけに頼る) — 疎な hot の hit が隙間を越えると ro の古い読みがそのまま commit する。md_23 の壊し B2 が結果前の予測に反して commit したことも、この論証の前提を疑わせた。
- 疎な hot の cold を latest から走査し直す — 段 2 plan の反例は hit の場合で、cold は末尾から続けても最初の wts ≤ trts を飛ばさない (段 3 相談 A)。
- variant patch に新 macro (`CICADA_VHASH_POST` 等) を足す — 条件 gate・在庫 test の登録を増やし、md_23 の B の patch bytes も変わる。
- K=1 の最新版だけを CAS 後に更新する単純な代案 (段 3 相談 B) — 依頼が 1 設計を指定しており、B-post の K=1 腕が近い問いに答える。
