# 段 6 fix 4 巡目の裁定 — smoke2 で露見した実機 blocker (2026-09-29 07:0x JST)

入力: smoke2 (request 33926.nqsv、wave worktree @09fdf57f1、Elapse 60 s、rc=1)、raw /work/1/SFC/tanab/tmp/vhash-cicada-version-measure-2026-09-29/raw/smoke2.json。
DW-O16 の「親の実機 blocker は別枠」。

## smoke2 で確かめた事実

- 依存物準備・stock build・既定 patch build は成功。**stock と既定 patch の正規化 `objdump -d` (.text) と `.rodata` は一致** (sha256 be7575a2… / 0ce135be…)。
- `nm -C` に izanagi 文字列は無いが、`strings -a` は **stock 自身も** izanagi / IZANAGI_ を含む (stock_absence.strings=false、default も false)。「0 件」基準は stock で成立しない。
- stock の `WORKER1_INSERT_DELAY_RPHASE=1` は compile error 3 件 (transaction.cc:924 `thid` 未宣言、`WORKER1_INSERT_DELAY_RPHASE_US` 未宣言、:925 `clock_delay` 未宣言)。これは記録すべき事実で、smoke の不合格条件ではない。
- 較正: L3 = 105 MiB (110100480 B)、N=1M で maxrss > 4×L3 → selected_records=1000000。
- 有効 build は condition gate の meaning 検査で拒否: owner TU transaction.cc の前処理で観測 `requested=(38,38),default=(0,38)`、宣言 44 (transaction.cc 31 + transaction.hh 8 + util.cc 1 + ycsb_cicada.cc 4)。gate は owner TU の前処理だけを見るので別 TU (util.cc・ycsb_cicada.cc) の分岐は観測できず、さらに transaction.cc の 1 箇所が `#if SINGLE_EXEC` (既定 0) の内側 (patch の read_internal、`ver = &tuple->inline_ver_;` の直後) にある。前例 BACKOFF_REQUESTED_US も companion は owner TU が include する header だけ。

## fix の内容

| # | 内容 |
|---|---|
| J1 | **計器・長い tx の `#if IZANAGI_CICADA_VLIFE` / `#if IZANAGI_CICADA_LONGTX` 分岐を、owner TU `cc/cicada/transaction.cc` と、それが include する `cc/cicada/include/transaction.hh` だけに置く。util.cc と ycsb_cicada.cc は stock のまま (patch から外す)。** 置き換え: (a) MinRts 公開の計測は `TxExecutor::leaderWork()` (transaction.cc) で `cicadaLeaderWork()` の前後の `MinRts` を比べて行う。(b) thread 別統計は動的 resize をやめ、thid (uint8) で引ける固定長配列にする (実際の worker 数は `TotalThreadNum`)。(c) 終了時の 1 行 JSON は transaction.cc 内の静的オブジェクトの destructor 等、ycsb_cicada.cc を触らずに 1 回だけ出す形 (出力順は runner の結果表示の後でよい。出力されることを smoke の短い走で確かめる)。(d) batch worker (thid >= FLAGS_thread_num) の操作数は、`TxExecutor::begin()` で `pro_set_` を `FLAGS_batch_max_ope` 個まで同じ分布 (zipf、FLAGS_ycsb_zipf_skew・FLAGS_ycsb_tuple_num・FLAGS_ycsb_rratio・FLAGS_ycsb_rmw) で伸ばす。retry の begin() では伸ばし直さない (同じ手続きで再試行する stock の意味を保つ)。伸ばした後に `is_ronly_` と `pro_set_.front().ronly_/wonly_` を全操作から再計算する。YCSB の `run()` は begin() の後に `pro_set_.size()` で配列を確保するので、この順序で成立することを file:line で確認する |
| J2 | `#if SINGLE_EXEC` の内側の計器分岐を削除する (SINGLE_EXEC=1 は D1419 で探索外。計器の対象外と patch 冒頭 comment に書く) |
| J3 | LONGTX の待機は `clock_delay` を使わず、既存 include だけで書ける `rdtscp()` の spin (`FLAGS_worker1_insert_delay_rphase_us * FLAGS_clocks_per_us` cycle) にする (transaction.cc は delay.hh を include していない) |
| J4 | smoke の witness の izanagi 文字列検査は「既定 patch の binary が stock に無い izanagi / IZANAGI_ 文字列を増やさない (集合一致)」に改める。`nm` は従来どおり 0 件も要求してよい (stock が 0 件なので) |
| J5 | smoke の delay compile 段は「compile を実行し rc と診断を記録できたこと」を成功とし、rc≠0 を smoke の不合格にしない (結果は raw に残す) |
| J6 | condition_meaning_gate の宣言 (`_CONDITIONAL_BRANCH_SITE_COUNTS`、`_CONDITIONAL_BRANCH_COMPANION_SITES`) と在庫 test の件数・docstring を、新しい分岐配置に合わせて更新する (companion は transaction.hh だけ)。既存 macro の宣言・期待値は変えない |

test: J1 の既定前処理一致 (touched TU は transaction.hh と transaction.cc の 2 つになる)、J4・J5 の smoke 判定、J1(d) の手続き延長 (純関数として切り出せない部分は既定前処理 test と smoke に任せ、その旨を報告)。
変異の事前登録の見直し: MUT-3 / MUT-6 の置換文字列は patch 変更で無効になりうるので、実装後に親が現物から取り直す (意図は同じ: 計器文を #if の外へ / `#line N` にファイル名)。
