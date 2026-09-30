# 段 4 裁定 — md_37 B-post (2026-09-30、date 実測 15:18:08 と 15:23:04 の間に起草)

入力: s1-brief.md、plan.md (段 2、受理 rc 0)、consult-a.md (レンズ A、受理 rc 0)、consult-b.md (レンズ B、受理 rc 0)。
裁定 inbox 再走査: 開始後の main 213d411c6..5b7134c5c は台帳の持ち越し行だけで、所有 file・hot block の裁定に変化なし。

## 1. 所見の裁定

| 所見 | real/refuted | 採否 | 裁定 |
|---|---|---|---|
| plan §1 「cold を hot 末尾から続けると B を飛ばす反例」 | refuted (A1) | 不採用 | 反例の hot [A40, C30]・trts 37 は C を選ぶ hit で cold ではない。cold (全記述子 > trts) では hot 末尾より物理的に前の版は全部 wts > 末尾 > trts なので、末尾から stock ループを続けても最初の ≤ trts を飛ばせない。末尾の生存は wts > trts ≥ rts ≥ MinRts > GC anchor で保たれる。**(P1) の cold 継続を維持**。ただし hit の隣接確認は必須 (plan §1 の疎な hot の反例 = hit の i ≥ 1 で成立、A も反例不成立を確認)。 |
| plan §1 隣接確認なし案は不採用 | real | 採用 | (P3) の反対案は採らない。hit で隙間 (列にあって hot に無い版) を越える経路が ro の validation なしの古い読みになる。 |
| A2 B の COUNT は v1、post は v2 で集計が割れる | real | 採用 | snapshot の遅れの計器を post とは別の小 overlay `patches/cicada-vhash-hot-block-count-v2.patch` に分け、**全腕の COUNT build (stock K0・B・post) に当てる**。variant の上にも variant + post の上にも厳密適用できること (U1 が確認)。post 固有の計器は別の JSON 行に出し、VHashReport の行に触れない (§2)。 |
| A3 一致は隣接確認の時点に限る | real | 採用 | 一次資料の論証は「確認の瞬間の列で stock の第 1 段と同じ版・同じ later_ver。その後は stock と同じ並行実行と GC の寿命前提へ帰着」と書き、無条件の同一とは書かない。 |
| A4 B2 の committed は不正な読みの件数ではない | real | 採用 | B2 計器版で read 時と validation 時の P の状態を同じ事象 ID で結ぶ (§3)。一次資料で committed 件数を「不正に飛ばした件数」と書かない。 |
| A5 stale-gap の到達だけでは誤読の証明にならない | real | 採用 | 省略・隙間を越えた hit・返した版が同時点の stock と違う・その読みを含む commit を別計数にする (§3)。誤読 commit > 0 で巡回 0 なら「未検出」。 |
| A6 / B5 見積りが成功 job の和だけ | real | 採用 | 投入前の見積りに全計算 job (smoke・build・perf 3・count・trace 2・変異・焦点走) を列挙して 7,200 s と比べる (§5)。 |
| B1 待ちの解消幅は事前に言えない | real | 採用 (計器のみ) | CAS 失敗の再試行数、CAS 後の区間の待ち・保持を分けて数える。代案「K=1 の最新版だけ」は依頼が 1 設計なので不採用 (B-post の K=1 腕が近い問いに答える)。 |
| B2 隣接 load が ro の利得を消しうる | real | 採用 (計器のみ) | hit・隣接失敗 (先頭 / 途中)・cold を分けて数える。性能の結論は計器なし build の同時刻比だけで書く。 |
| B3 同じ木から並列 dispatch すると rc 16 | real | 採用 | perf 3 job は job ごとに独立の detached 計測木 (同じ tip) から投入する。driver は別の木から同じ manifest の binary を検証して使えること (U2 の契約、§4)。 |
| B4 判定語の限界 | real | 採用 | A/A 腕と主 cell c23 が無いことを明記し、結論は「この格子での回復幅」に限る。node 別の内訳を残す。 |
| B6 B2 の識別規則が無い | real | 採用 | §3 に識別規則と予測を結果前に固定する。 |
| B7 旧図の再生成経路 | real | 採用 | 作図は fig-write に要る field (待ち・保持・update commit) だけ v1 の aggregate からも読む (汎用互換層は作らない)。md_23 の aggregate.json.xz から待ちを足した修正版を**本 wave の一次資料の dir に**生成器付きで置く (md_23 の dir は書き換えない)。driver の aggregate は v1 の raw を読めなくてよい。 |
| B8 所有と sha 検索の一般化 | 一部 real | 採用 (記述) | 作図 `tools/plotting/plot_vhash_cicada_hot_block.py` と `orchestrator/tests/test_plot_vhash_hot_block.py` は依頼の「やること 4. 図の修正」が明示的に求める md_23 の図の生成器なので scope 内と裁定する。条件 gate・在庫は実際に赤になった箇所だけ局所修正 (新 macro は足さない)。sha 検索は「5 file の変更前 sha256 先頭 16 桁、git 追跡範囲で 0 件」とだけ書く。 |

## 2. プラン v2 (確定)

### U1 (C++、所有: patches/cicada-vhash-hot-block-post.patch・patches/cicada-vhash-hot-block-count-v2.patch・patches/broken-cicada-vhash-post-*.patch・patches/broken-cicada-vhash-skip-pending-probe.patch・patches/README.md の該当節)
1. **post overlay** (pin → variant → post、新 macro なし、既存 `#if CICADA_VHASH_K` / `#if CICADA_VHASH_COUNT` の中だけ):
   - tuple.hh: 書き区間の中で (wts, ptr) を wts 降順の位置へ挿入する helper。満杯で最小より古ければ落とす (落とした数を数える)。同じ ptr の重複を入れない。vh_init・vh_trim は維持。
   - read_internal: seqlock の copy と再確認 (variant の順序のまま) の**後**に、hit (i < n) なら i = 0 は `tuple->latest_` の acquire load == ptr[0]、i ≥ 1 は `ptr[i-1]->next_` の acquire load == ptr[i] を確かめる。成功なら ver = ptr[i]・later_ver = (i ? ptr[i-1] : nullptr)。失敗なら ver = latest (stock と同じ)・later_ver = nullptr。cold (全件 > trts) は variant と同じく ptr[n-1] から stock のループ。第 2 段以降は stock。
   - validation: VHashGuard を位置探索と CAS の外へ出し、stock の探索 (`later_ver_` 起点) と先頭 / 途中 CAS を復元する (md_23 の「K>0 は先頭から探索」は外す)。CAS 成功後にだけ guard を取り、hot へ挿入し、guard を閉じてから break。RMW / DELETE / WRITE_LATEST_ONLY の先頭 CAS も同じ。goto FINISH_VALIDATION と CAS 失敗の再試行は guard を持たない。挿入は validation の中で終える。
   - GC: variant のまま (gc_lock_ → guard → trim → 切り離し → 閉じる → 再利用)。
   - 計器 (`#if CICADA_VHASH_COUNT` の中、別の reporter): `CICADA_VHASH_POST_COUNT_JSON {"schema_version":1,"k":K,"workers":[{"thid":t,"hit_adj_ok":…,"adj_fail_head":…,"adj_fail_mid":…,"cold":…,"fallback_odd":…,"fallback_changed":…,"cas_retry":…,"publish_wait_cycles":…,"publish_hold_cycles":…,"publish_count":…,"publish_dropped":…}]}`。variant の VHashStats / VHashReport の行は変えない (count-v2 と衝突させない)。variant の install_* は post では加算されない (0 のまま) ことを README に書く。
   - 各ブロックの後に無条件 #line。macro 未定義で pin と pin + variant + post の `transaction.cc`・`util.cc`・`ycsb_cicada.cc` の前処理が一致すること (行 marker を除く) を U1 が login で確かめる。
2. **count-v2 overlay** (`#if CICADA_VHASH_COUNT` の中だけ): lag を `(wts−rts) >> 8` サイクルにし、bucket 0 と [2^j, 2^(j+1)−1] (j = 0..39) と 2^40+ の 42 個、`snapshot_lag_cycles`・`snapshot_lag_sum_cycles`・`snapshot_lag_count`。`snapshot_lag_ts` は出さない。schema_version 2。variant の上と variant + post の上の両方へ `git apply --check` (fuzz なし) で当たること。
3. **壊し** (post の上、無条件、trace build K ∈ {1, 8} のうち K=8 に重ねる。K=8 を選ぶのは hit で隙間を越える機会が最も多いため):
   - md_23 の B1・B2 が variant + post に厳密適用できればそのまま使い、できなければ `broken-cicada-vhash-post-stale-hot.patch`・`broken-cicada-vhash-post-skip-pending.patch` を新設 (隣接確認の成功後、第 2 段の直前に置き、event の形式は md_23 と同じ)。
   - `broken-cicada-vhash-post-stale-gap.patch`: writer が CAS 後の hot 挿入を thread ごとに決定的に一部 (例: 4 回に 1 回) 省き、reader は隣接確認を外す。事象: reached = 隣接確認なら失敗していた hit (確認の式を評価だけして捨てる)、changed = 返す版が同じ時点で latest から stock の第 1 段を辿った版と違う、committed = changed を含む tx の commit。省略数は `CICADA_BREAK_OMITTED slug=post-stale-gap omitted=<n>` の 1 行。event 行は driver の既存 EVENT_RE / FIRED_RE の形式に合わせる。
4. **B2 計器版** `broken-cicada-vhash-skip-pending-probe.patch` (variant + md_23 の B2 と同じ変更 + 記録、K=4 の trace build、md_23 の B と同じ構成): changed の事象ごとに事象 ID (thid と thread 内の通し番号)、is_ronly_、tx の wts・rts、P の ptr・wts・read 時の status、older の ptr・wts、read_set の index を持つ。validation (a) でその index を処理した時点の P の status・P の wts (再利用の検出)、(a) の開始版と到達版、到達版 == older か、を同じ事象 ID で出す。tx の終わりに commit / abort を出す。1 行 1 事象の `CICADA_B2PROBE stage=<read|validate|end> id=<thid>:<n> ...`。既存の CICADA_BREAK_EVENT / FIRED の行も B2 と同じに出す (帰属の照合を md_23 と同じにする)。

### U2 (Python、所有: orchestrator/campaign/vhash_cicada_hot_block.py・orchestrator/tests/test_vhash_cicada_hot_block.py・tools/plotting/plot_vhash_cicada_hot_block.py・orchestrator/tests/test_plot_vhash_hot_block.py)
1. 腕 `stock` (K0・WL=1、pin + variant)、`B-k1`・`B-k8` (pin + variant)、`post-k1`・`post-k8` (pin + variant + post)。perf は COUNT・TRACE なし。COUNT build は全腕に count-v2 を最後に重ねる。trace は先頭に instr-cicada-trace.patch。
2. perf: 12 cell × 5 腕 × 2 round × 3 job、腕の順は round と cell で回転。比は同じ job・round・cell の B/stock・post/stock・post/B。node 別の内訳を aggregate に残す。
3. count: md_23 の COUNT 4 cell × 5 腕。v2 と POST の JSON を腕ごとに検証 (post 腕だけ POST 行を必須、他の腕は POST 行が無いことを必須)。
4. trace: 正例 T1・T2・T3 × 5 腕 (stock・B の再確認を含む) = 15 走、post の壊し 3 本 × T1・T2 = 6 走、B2 計器版 × T1・T2 = 2 走。巡回が出た正例の腕は aggregate で失格として比から外す。壊しの分類は md_23 の規則 + stale-gap の 4 計数。
5. estimate: trace は 2 job の走数の和。全計算 job (smoke・build・perf・count・trace) の和を 7,200 s と比べ、超えるなら結果前の梯子 (6→4 round → ro 格子を gc {10, 100000} に縮小) を当て、なお超えれば stop。K の段は無い (既に {1, 8})。
6. 計測木: perf job を別の detached 木から同時に投げても、manifest の sha256 と依存 file の照合で同じ binary を使えること (repo root に依存する path を manifest に持たない、または照合で許す)。できなければ報告して止まる。
7. 作図: fig-k・fig-ro を腕で描き分け、fig-write の下段に待ちと保持を横並びで描く (単位 cycles / update commit、分母 0 は欠測)。fig-write は md_23 の aggregate (v1) の待ち・保持 field も読める (fig-write だけ、局所)。provenance JSON は既存の形。
8. 新しい subprocess の spawn site を足さない。materializer・perf closure・spawn site の在庫は変えない (赤になったら報告)。

### 条件 gate の分岐数の契約 (裁定後の親の実測で追加、date 実測 15:23:04 の直前)
build の条件 gate (`orchestrator/campaign/condition_meaning_gate.py` の `_CONDITIONAL_BRANCH_SITE_COUNTS` :624-626 と `_CONDITIONAL_BRANCH_COMPANION_SITES` :633-636、照合 :3728-3749) は、patch 適用後のソースで exact な directive 行を file ごとに数え、宣言と完全一致を要求する。variant の現況 (親が patch の追加行を awk で数えた実測): `cc/cicada/transaction.cc` の `#if CICADA_VHASH_K` 9・`#if CICADA_VHASH_COUNT` 19・`#if CICADA_VHASH_WL` 4、`cc/cicada/include/tuple.hh` の `#if CICADA_VHASH_K` 3、`cc/cicada/include/transaction.hh` の `#if CICADA_VHASH_COUNT` 1・`#if CICADA_VHASH_WL` 1。複合条件 (`#if CICADA_VHASH_K && CICADA_VHASH_COUNT` 等) は数えられていない。
**post・count-v2・壊し・B2 計器の各 overlay は、適用後のこの 6 つの exact 行数を variant と同じに保つ。** 新しい条件付きコードは既存の exact 行の block の中に置くか、複合条件の `#if` にする。既存の exact 行を消さない (中身を空にするのは可)。U1 は pin + variant (+ post) (+ count-v2) (+ 壊し) の各組み合わせで 6 つの行数を数えて報告する。gate の登録 (所有外) は変えない。
U2 の `inert_receipt` は variant だけでなく post・count-v2 を重ねた場合も macro なしの前処理が pin と一致することを確かめる。

### 依存と投入順
U1 と U2 は所有が素集合なので並列に投入する。JSON 名・event 名・patch 名は本節で固定済み。U2 の test は U1 の patch に依存しない fixture で書く (patch の厳密適用の test は U1 完成後に親が統合して走らせる)。

## 3. 結果前の登録

### 3.1 B2 の機序 (T-2927 (1)) の識別規則と予測
各 changed 事象を次の順で 1 つに分類する (上から最初に当たったもの)。
- R: is_ronly_ = 1 (ro の rts 以下に PENDING が来た)。
- A: update、validation 時の P の status = aborted、到達版 == older (P が後で abort し、古い版の読みが結果として正しかった)。
- G: update、P の wts が read 時と validation 時で違う (版の再利用・GC)。
- M: update、validation 時の P の status = committed かつ到達版 == older (validation (a) が P を見なかった)。開始版で下位分類。
- V: update、到達版 != older (validation (a) が止めたはず。commit していれば計器の誤り)。
- U: 上のどれにも当たらない / validation の記録が無い。
予測 (親): committed の過半は A。巡回に帰属した事象 (witness) は A 以外で、R か G のどちらかに入る。どちらかは予測しない。committed が 0 なら「再現せず、機序は未識別」と書く。

### 3.2 壊しの予測
- post-B1 (1 つ古い確定版): T1 で reached > 0・巡回として検出・帰属。
- post-B2 (PENDING を飛ばす): md_23 と同じく到達はある。検出の有無は予測しない (機序が §3.1 で未確定のため)。
- post-stale-gap: omitted > 0、T1 で reached ≥ 1・changed ≥ 1・committed ≥ 1、巡回として検出・帰属を期待。reached = 0 なら「未到達で検出力の証拠にならない」。committed > 0 で巡回 0 なら「未検出」。
- 正例 5 腕 × 3 cell: 巡回 0・integrity 0・C 行数 = commit 数。1 つでも巡回が出た腕は失格。

### 3.3 性能の読み方 (結果前)
- 主問: 更新中心の cell (ro0 × 3、rr5、rr50、ro50-gc10) で post/stock の中央値が B/stock より上がるか、どこまで 1.0 に近づくか。語は md_23 §5.1 と同じ草稿 v1 §5.5 の δ_ex = ln(1.10) で付ける (A/A 腕は無いので「予備的に支持」は出せない、主 cell c23 は欠測)。
- ro95 の 3 cell: post/B の比で隣接確認の費用を見る。|ln 比| ≤ δ_ex なら「差なし」。

## 4. 変異の事前登録 (driver・作図、`tools/mutation_harness.py`、実装後に単一理由性と期待 node を確かめて確定)
- M0: docstring だけの変更 (等価、SURVIVED を期待)。
- M1: estimate の trace を `2 × max` に戻す → estimate の test が kill。
- M2: COUNT の検証が 18 bucket の v1 を受理する → count の test が kill。
- M3: post の比の相手を別 round の stock にする → aggregate の対の test が kill。
- M4: 巡回が出た正例の腕を比に残す → 失格の test が kill。
- M5: plan_trace から stale-gap を落とす → trace の完備性の test が kill。
- M6: perf の回転で post 腕を 1 round 落とす → 回転の test が kill。
- M7: post の build spec から post overlay を落とす (post == B) → build spec の test が kill。
- M8: fig-write の下段から待ちを落とす → 作図の test が kill。
- M9: post 腕に POST の JSON 行が無くても受理する → count の test が kill。
C++ の hot の保守の検出力は壊し 3 本 (§3.2) と判定器で示し、harness の変異に含めない (md_23 と同じ)。

## 5. 計算の見積り (投入前に smoke の実測で再判定)
md_23 §8 の実績: smoke 308 s、build 247 s (17 binary)、perf 518/518/521 s、count 85 s、trace 254 + 32 s、変異 probe + 本走 231 + 233 + 412 s、焦点走・監査 350 s。本 wave: binary は perf 5・count 5・trace 5・壊し 3・probe 1 の 19 (+ smoke) で build 約 300 s、perf 約 1,560 s、count 約 90 s、trace 23 走で約 350 s、smoke 約 310 s、変異約 650 s、焦点走・監査約 350 s。合計約 3,600 s (約 1.0 node 時間)、上限 7,200 s 未満。失敗・再走の余裕を含め、合計が 6,000 s を超えそうになった時点で新しい投入を止めて見積りを書き直す。

## 6. scope 外
- K=1 の最新版だけの設計 (B1 所見の代案) は測らない。
- 構成 D、TPC-C、長い ro tx、主 cell c23・A/A 腕は測らない (md_23 と同じ格子に固定)。
