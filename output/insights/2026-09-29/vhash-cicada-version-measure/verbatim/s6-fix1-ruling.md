# 段 6 fix 1 巡目の裁定 (2026-09-29 04:5x JST)

入力: codex/out/s6-review.md (NO-GO、must-fix 6)、親の焦点走 focus-1.log (5 file、388 passed・2 skipped・rc=0)、親の観察。
統合 snapshot: integration-snapshot-7a4f9a592.patch。fix は 1 単位 (patch・driver・test・作図が raw JSON schema で結合し、所有を割ると契約が壊れるため)。

| # | 所見 | 判定 | fix の内容 |
|---|---|---|---|
| F1 | patch の `#line N "file"` が既定 build の `__FILE__` を変える (debug.hh NNN) | real (親も同観察) | 全 `#line` をファイル名なしの `#line N` にする |
| F2 | 前処理 test が include とファイル名を捨て F1 を検出できない。driver の objdump 比較は `.rodata` を見ない | real | test は行マーカーのファイル名も比較対象に含める (stdin 入力なら stock・patch とも `<stdin>` のはず、ファイル名付き `#line` が残れば赤)。driver の witness に `.rodata` の内容比較 (`objdump -s -j .rodata` 等) を足す。正規化は address だけに限る |
| F3 | `VLIFE_VISIT` が pending 版を記録せず、待機後に committed になっても再評価しない | real | stock の pending 待機が終わった直後に、その版の確定 status で記録する (追加の鎖走査はしない、二重計数しない) |
| F4 | `read_zero` が深い read に限らず最初の read を全部数える | real | K ごとに「既読 0 件の深い read 数」と「そのうち候補あり数」を別 field (`deep_read_zero[5]`、`candidate_read_zero[5]`) にし、旧 `read_zero` は削除 |
| F5 | readcheck 等 validation site の位置は `later_ver_` 起点 | 定義の明示 (追加走査なしでは latest 起点にできない) | validation site の position は「その走査の開始点からの位置」と JSON の site 定義 (`position_origin` 等) と作図 caption に明記し、K の図は read site (read_update / read_ronly) だけで描く |
| F6 | measure の `--records` が smoke の選定に束縛されない | real | measure は `--smoke-json <path>` を必須にし、その `calibration.selected_records` を N に使う。smoke JSON の `ccbench_commit`・`patch_sha256` が現在と一致しなければ拒否。`--records` は削除 |
| F7 | 図 1 に版の位置が無い、図 3 に回収時年齢が無い | real | 図 1 = site 別 hop 分布 + read site の位置分布。図 3 = gc_inter_us ごとの境界年齢・公開間隔・回収時年齢 (生成基準・上書き基準)・論理生存版数 (パネル分け) |
| F8 | 図・caption に測定条件が無い | real (should) | 図に条件 (workload・長い tx・gc_inter_us・N・反復数) を caption/注記で出す |
| F9 | 較正 probe の前に単独性確認が無い | real (should) | 各 probe 起動前に `_assert_single_tenant()` |
| B1 | measure の stock build は不要 | refuted | 依存物準備 (masstree の生成物) のための build で前例どおり。残す (理由をコメントで 1 行) |
| B2 | 図が bucket 番号の加重平均を描く | real | bucket の上界値で中央値・p90 (または bucket 割合) を描き、平均 bucket 番号は描かない |
| P1 | 親所見: 時間系ヒストグラムの上限 2048 µs では gc_inter_us=100000 の値が全部 overflow | real | µs 系 (gc_boundary_us, gc_publish_us, age_create_us, age_overwrite_us) は別の bucket 列 (log2、2^0〜2^40 µs + overflow) にし、JSON に `time_bucket_bounds` を出す。hop/位置の bucket は現行のまま |

変異の事前登録 (DW-M01) の追加:
- MUT-6 (F1/F2): patch の `#line N` を 1 箇所だけ `#line N "cc/cicada/transaction.cc"` に戻す → 前処理一致 test が KILLED
- MUT-7 (F6): measure で smoke JSON の patch_sha256 照合を外す → 照合拒否 test が KILLED
