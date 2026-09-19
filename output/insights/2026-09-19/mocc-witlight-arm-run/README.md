# mocc 軽量 witness の実装と 4 arm 実走 — 軽量 witness on は 0/60・0/60、witness off は 1/60・1/60、discriminator は未発火

作成 2026-09-19 (wave `dev-wave-mocc-witlight-arm-run`、base main `a99425b66`)。一次資料は repo 外の job dir
`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/` (patch 2 種・runner v5・smoke wrapper・走ごとの JSON・G2 走の生 trace / witness・codex 逐語)。
本文は **非 certifying の観測記録** であり、headline・certified 選択・floor・oracle・fitness の根拠に使わない。

## 0. 問いと範囲、認可しないこと

- ユーザー決定 (2026-09-19): 「軽量 witness を hook branch に実装し、4 arm (witness 軽量 on / off × BACK_OFF 0 / 1) × 各 60 走を計算ノードで取ることを認可する。
  非 certifying。certified 昇格・pin 前進・変異探索は認可しない」。問い (i) BACK_OFF=0 で軽量 witness on と off の G2 signal 検出率に差があるか、
  (ii) 検出した各 G2 を payload lineage discriminator (`orchestrator/campaign/mocc_g2_discriminator.py`) で `supported` (実 anomaly と整合) /
  `contradicted` (torn read と整合) / blocker に分類できるか。設計の正本 = T-2779 insight §3 (静的設計)、T-2774 §1 4 (観測者効果の静的根拠)、T-2780 (pilot の配線、本 wave は pilot を使わない)。
- 範囲外: gate・台帳の新設、CCBench 本体の恒久改変 (D16 の trace-hook 分類で hook branch に commit、上流 push は人間)、pin 前進、runner の改版、仮説 cell。
- 認可しないこと: mocc の certified 昇格判定、pin 前進 (D2114 項 3 / D1603)、変異探索の解禁 (D2134)。規律 2 (verifier / discriminator / X/P patch の受理集合は 1 文字も
  変えていない)、規律 7 (T-1892 の 5/42、T-1943 の `no-g2`、T-2774 Q1 / Q2、T-2779 の 5/120・0/120・2/120 は各旧束縛で保持)。**陰性を「G2 が無い」証拠にしない。**
  個別 verifier の `certified=true` と arm 属性 `observational_only=false` は、本 wave・MOCC・軽量 witness の認証を意味しない。

## 1. 結論 (先に上限を書く)

軽量 witness (W) を hook branch に実装し、同一 source の 4 arm × 各 60 走を 4 node の 4 block (各 block に 4 arm、block 内対照) で取った。G2 signal 検出数は
**軽量 witness on = 0/60 (BACK_OFF=0)・0/60 (BACK_OFF=1)、witness off = 1/60・1/60**。片側 Fisher (on < off) は主比較 (BACK_OFF=0) も
副比較 (BACK_OFF=1) も未調整 p=0.500 で、この標本・条件では率差を検出しなかった (設計仮定下の検出力は off 率 0.0417 の完全抑制で 0.105 と低い)。
**on arm に G2 が 1 件も出なかったため discriminator は発火せず、問い (ii) (実 anomaly / torn read の分類) は未到達 (識別対象 0 件)。**
off arm の 2 件は現象名 G2・長さ 2・両辺 rw で T-1892 / T-2774 / T-2779 の形と整合するが、witness off なので識別できない。
0 件は不在証明でなく、非有意は同等性証明でない。軽量 witness が観測者効果を消したかどうかは本結果からは言えない
(on 0/60 は「軽量化しても on で出ない」とも「率 0.017〜0.042 の事象を 60 走で引けなかった」とも両立する)。
W の TRACE=0 identity は OID checker 2 本で `match`、合成 source は TRACE=1 観測専用。certified 昇格・pin 前進・変異探索・規律 2 の即 reject 契約は変えない。

## 2. 実行の束縛

- outer: main `a99425b66` (wave worktree + detached worktree 3 本 `.codex/worktrees/witlight-node{2,3,4}`、いずれも同 base)。CCBench gitlink `511c9538` は動かしていない。
- **hook commit W = `5b02546fcd7b0302c8c92b6e05957541c9660902`** (親 `e9e477ca1b55348ab4530de0b1cf663ce4555290`、branch `izanagi-t1943-mocc-g2-witlight`、
  touch = `cc/mocc/transaction.cc` +26/−6、include 行不変、`#line` 無し。commit は親が wave worktree の submodule に一時 worktree を切って `commit -F` で作成。
  trailer 3 行: `role=author` (codex gpt-6-astra medium)、`role=reviewer` (codex gpt-6-astra medium = 段 3 レンズ A の独立検算と段 6 レビュー A)、`role=manager` (claude-opus-5-1m xhigh)。
  初版 `e0905b3d` (trailer 2 行) を段 6 レビュー A MF2 で message だけ amend した (tree `a41e6c54…` 不変、旧 OID の identity 証拠は job dir `superseded-e0905b3d/`)。
  逐語 = 本 dir `verbatim/W.patch.txt` (job dir では `probe/W.patch`、sha256 `4ef9c387068abf9dcdd123ba87691b4d613cdb36fff9c541448c147367095aff`)。GitHub 未 push (人間手番、D16)。
- **測定用合成 source** = pin `e9e477ca` + patches [X/P `patches/instr-mocc-lock-coverage.patch` (repo、D1686、sha256 `e9e65b7876050865ee1cbc4d3a05516b09a8fe0b18149e0c063632162fd7bb48`、不変),
  `witlight.patch` (job dir、X/P 適用後 source に対する diff、`#line 115 / 1136 / 1201 / 1208` 付き、sha256 `0648e2c6de46319da02056cb516d706ff9f09c3c0ffb2cadb6c94ee069473363`)]。
  W との同内容性 = (e9e477ca + X/P + witlight.patch) と (e9e477ca + W + X/P) から `^#line` 行を除いた bytes が一致 (親が `cmp` で実測、job dir `check-patches.log`)。
  runner v5 の `pin != e9e477ca` では discriminator が `not-run (pin-outside-t1943)` になるため pin は e9e477ca に固定した (T-2779 §3 末尾の注意どおり)。
  **合成 source は TRACE=1 専用の観測 build であり、性能値には使用しない。W 単体の OID identity (下記 2 本) と合成 source の TRACE=0 binary identity は別で、後者は本 wave で検査していない** (段 3 レンズ A MF1)。
- identity (規律 1、`tools/check_trace0_preprocess_identity.py --repo <wave worktree>/external/ccbench --cxx /usr/bin/x86_64-linux-gnu-g++-11`、login で実走。checker は policy を受け取らない):
  `--old 511c9538 --new W` = top-level `result=pass`、`files[0].result=match` (16 context、正規化 preprocess 同一、include 活性同一、trace.hh 1 行の許可追加 `permitted_mocc_trace_include_addition` = e9e477ca 由来)、
  `--old e9e477ca --new W` = `pass` / `match` (全 context `exact_identity`)。負例 = W に `#include <vector>` を `#if TRACE` 内に足した一時 commit は rc=1 (`include 行文字列（順序込み）が不一致`、preprocess 比較の前に include 契約で拒否 = 単一理由)。JSON は job dir `identity-*.json`。
  これとは別の検査として、login の gcc-11 の version body digest を driver の `tool_version_body` で計算し policy の `expected_compiler_version_body_sha256` (`b713e6ab…`) と一致することを確認した (compute の runner が `_resolve_toolchain` で行う検査と同じ方法。identity checker の証拠ではない)。
- runner: `probe/t2779_probe.py` (v5、T-2779 と同一 bytes、sha256 `7907a545b719845d69b36590cc90cff6b28c242d3b7140d9c52b4a838798df99`、無変更、login selftest 21/21)。
  smoke だけ観測 wrapper `probe/smoke_capture.py` (sha256 `65017778972c7dcab6b5bdd0da801da11fb7e923e1075d9755101ff90446bc55`、v5 を import し verifier 起動境界で
  saved_trace / witness を複製してから実物へ委譲。argv・env・返値・分類は不変、runner の `__file__` は v5 本体) 経由。本走は runner 直。
- arm 定義 `probe/arms-witlight-node{1..4}.json` (node k は arm 列を k−1 回転、object は同一 = `jq -S 'sort_by(.name)'` の sha256 `a4af0e8a43855131c408470d35626ff5e95d7c51290f3cd1c37c597932327108`。
  raw sha256: node1 `ba74088785f3ffcaf708166608c04d5f087b00cd28018f50587566022f9bcd30`、node2 `f5e802236d0047125548490553cd34ffc06153f89ef5b85219cb5da94d146245`、
  node3 `8db96f217db2f84af10b7fd3490df01cdd45e7ffc3115d2e851c80af5818b355`、node4 `ab0e84b28b7d9db402ddfbc4d183c362687cd7f6fc9f671d20749a9bcf1fefca`)。
- configure 基底 = T-1943 pilot と同一 (`-DCCBENCH_TRACE=1 -DCCBENCH_BACK_OFF=0 -DCCBENCH_BACKOFF_FIXED=-1 -DCCBENCH_NO_WAIT_LOCKING_IN_VALIDATION=1
  -DCCBENCH_NO_WAIT_OF_TICTOC=0 -DCCBENCH_WAL=0` + `-DCCBENCH_CCACHE=OFF`)。bo1 arm は `-DCCBENCH_BACK_OFF=1` だけ置換。gcc-11、policy `tools/pegasus/mocc_trace_v1_policy.json`。

| arm | pin | X/P | witlight | witness env | BACK_OFF | observational_only |
|---|---|---|---|---|---|---|
| e9-witlight-wit | e9e477ca | 有 | 有 | on | 0 | false |
| e9-witlight-nowit | e9e477ca | 有 | 有 | off | 0 | false |
| e9-witlight-wit-bo1 | e9e477ca | 有 | 有 | on | 1 | false |
| e9-witlight-nowit-bo1 | e9e477ca | 有 | 有 | off | 1 | false |

- 実行 argv: `-ycsb_tuple_num=10000 -thread_num=48 -ycsb_zipf_skew=0.9 -ycsb_rratio=50 -ycsb_rmw=0 -ycsb_max_ope=10 -extime=3`。witness on の走は
  `IZANAGI_MOCC_G2_WITNESS=1` + `IZANAGI_MOCC_G2_WITNESS_DIR`。4 arm は同 source (source file sha 同一)、on/off は実行時 env だけの差。同 source・同 define の on/off も runner は別 build (binary sha は build ごとに異なる)。
- verifier: `python3.10 -m orchestrator.verifier <trace_dir> --json --protocol mocc --ccbench-root <arm の source> --expected-commits N` (outer `a99425b66`、変更なし)。discriminator は witness on かつ cycle 正の走だけ。

## 3. 軽量 witness の実装 (W)

T-2779 §3 の静的設計を、段 2 plan §2 と段 3 レンズ A の検算で修正して実装した。行番号は e9e477ca の `cc/mocc/transaction.cc` (`M:行`)。

- **変更 4 点** (逐語 `verbatim/W.patch.txt`): (1) helper `izanagi_mocc_g2_emit_post_store` (M:100〜110) の signature を `(thid, writer_txid, write, version, stored_producer)` にし、
  共有 body の decode と失敗時の `std::abort()` を呼出側へ移す。S 行の 5 値・書式 (`S txid key epoch tid stored`) は不変。(2) `writePhase()` の `#if TRACE` 内、`izanagi_txid` 取得 (M:1135) 直後で
  `std::vector<std::uint64_t>* izanagi_stored_producers = nullptr;` を置き、`izanagi_mocc_g2_enabled()` の有効分岐内でだけ `thread_local std::vector<std::uint64_t>` を clear /
  `reserve(write_set_.size())` してポインタへ。(3) publish (`__atomic_store_n`、M:1195) 直後の post_store 呼出 (M:1197〜1200) を「ポインタ非 null なら decode + 既存 abort + push」に置換。
  (4) `unlockCLL()` (M:1207) 直後・`RLL_.clear()` 前で `write_set_` を同順に再走査し保存値で S 行を出力、vector を clear。
- **保存されるもの**: S の値・件数・順序・文法、L 行 / stamp / E 行 / validation / publish / CC lock 操作 / `WriteElement`。`stored ≠ txid` の abort は追加しない
  (不一致値を保持して出力し、消費側 `witness-post-store-token-mismatch` の被覆を保つ)。include 行を足さない (`std::vector` は `include/transaction.hh`、`std::uint64_t` は trace.hh の `<cstdint>` 経由)。
  T-2779 §3 案 (6) の `#include <vector>` は identity checker の include 行完全一致契約で拒否されるため撤回した。
- **窓に残るもの**: publish 後・unlock 前には decode (8 byte memcpy + magic 比較) + 失敗 abort + 確保済み vector への push だけが残る。2 要素目以降の stamp・memcpy・X/P の
  `lock-lost-before-publish` 検査・publish、E 行、CLL 順の unlock は不変。**短縮量は未実測** (S の stream 取得・hex 化・書式化・出力が unlock 後へ移る、という処理構成の説明まで)。
  初回・capacity 増大時の `reserve` は publish 前でも write lock 保持中 (残る観測者効果)。
- **off の保証 (限定)**: `izanagi_mocc_g2_enabled()` が false なら TLS vector の構築・clear・reserve・decode・push・S 出力を実行しない。ポインタ初期化と分岐は残る。
  旧 off binary (e9e477ca + X/P、T-2779 通常 arm) との命令列・TLS 領域・cache 挙動の同一性は未実測。
- **生存期間**: validation 失敗は `writePhase()` に入らない (M:1215〜1221)。採取開始時と正常出力後に clear。witness on の INSERT / DELETE と decode 失敗はプロセス abort。
  異常終了時の出力済み prefix は旧版と異なりうる (正常完走時の行対応だけを論証)。
- **保存値の pass-through** (段 3 レンズ B M3): decode → `push_back(stored_producer)` → 再走査で `(*izanagi_stored_producers)[stored_index++]` → helper 引数 → 既存不変行 `<< stored_producer`。
  author の逐語引用と段 6 レビュー A の独立確認による静的確認であり、**runtime の不一致注入では検証していない**。smoke の on arm では全 S で第 5 値 == writer txid を正例として記録 (§5)。
- **測定 patch の `#line`**: `#line 1136` は `#if TRACE` 内、`#line 115 / 1201 / 1208` は `#endif` の直後 (TRACE=0 でも active、X/P の `#line 1158` 等と同じ作法で後続の元位置を復元)。W には置かない。
- **D16 の分類**: `#if TRACE` 内の計器で validation・publish・CC lock 操作を変えない → trace-hook、branch `izanagi-t1943-mocc-g2-witlight` (e9e477ca の子)。主 checkout の submodule git dir へ fetch し bundle を job dir に保全 (§7)。gitlink 不変、push は人間。

## 4. 実走の設計 (事前登録 = job dir `s4-ruling.md` §3〜§4、結果を見る前に確定)

- 4 arm を同一 block で round ごとに開始 arm を回転 (`round_order`)。4 block (W1〜W4) × 15 round × 4 arm = 60 走 / block、各 arm 60 走。node k の arms JSON を k−1 回転させ、4 node 合計で
  各 arm が各位置に 15 回。smoke は別 block (`--rounds 1`、4 走) で本走に合算しない。**rounds は launcher 引数 (15) で固定、結果を見て増減しない。**
- 標本の根拠 (親が計算、段 2 plan と段 3 レンズ B が独立に再計算して丸め精度で一致): 片側 Fisher α=.05、独立・同率 Bernoulli、等標本、完全抑制の設計仮定で、
  off 率 0.0417 (T-2779 通常 arm 5/120) 対 on 0 は **K=60 で 0.105**、0.058 (T-2774 witness off 合算 7/120) 対 0 で 0.268、0.119 (T-1892 5/42) 対 0 で 0.856、部分抑制 0.0417 対 0.014 で 0.050。
  K=60 で on=0 のとき off ≥5 でないと p<.05 にならない (off=4 で 0.059、5 で 0.029)。ユーザー決定の「80% 検出力の根拠 = 各 arm ≥56」は率 0.119 の条件付き計算 (T-2774 段 3 レンズ B) であり、
  観測率では成立しない。**認可枠 60 を超えず、検出力はこの上限として明記する。計算値であり実測ではない。**
- 主表示 = arm 別 k (G2 signal 走数) / m (有効 verdict 数、indeterminate を含み failure を含めない)、k/m (G2 signal 検出率)、Clopper-Pearson 両側 95%、計画数・保存済み N・failure・indeterminate を併記。
  主比較 = BACK_OFF=0 の `e9-witlight-wit` 対 `e9-witlight-nowit` (on 側が低い方向の片側 Fisher、参考値)。副比較 = BACK_OFF=1 の on/off。family 全体の効果をどちらか 1 つの p<.05 で宣言しない。
  block 別件数を併記。CP/Fisher は node 内相関・順序・時間変動をモデル化しない参考値で、固定時間の走あたり検出率 (同じ commit 数への曝露比較ではない)。
- 実用上の到達点 = on arm に G2 ≥1 件が出て discriminator の入力へ到達すること。呼出成功・正常完了 (`supported` / `contradicted` / blocker) ・識別成功を別に数える。到達点は率差の有意性・根因・認証を意味しない。
- T-2779 の通常 arm 5/120 は旧 witness source・別 block・別日の参考値として併記し合算しない。旧 heavyweight on arm (T-2774 instr-wit 0/40) を含まないため軽量化の改善量を因果的に推定しない。
- 問い (ii): on arm の G2 各件に走単位の結論表と comparisons 全件の表。`supported` = 報告された rw reason すべてで reader version の producer と payload 先頭 8 byte の stamp producer が一致 (実 anomaly と整合)、
  `contradicted` = 少なくとも 1 比較で不一致 (torn read と整合)、blocker → `indeterminate`、入力拒否は別記。`witness-post-store-token-mismatch` は S の blocker で `contradicted` に読み替えない。off arm の G2 は `not-run (witness-off)`。
- 欠測規則: block ごとに (a) 保存済み / (b) 開始証拠あり未収載 / (c) 未開始確認済み / (d) 状態不明。主解析は (a)。補充しない。原本は書き換えない。
- smoke の技術的合格集合 (結果前に固定): 4 走 benchmark rc=0、build 4 arm 成功、raw 完全、binding 一致 (runner / wrapper / JSON / patch / source sha、bo1 だけ BACK_OFF=1)、
  verifier rc=0 または整合した G2 の rc=1 (現象名 G2・cycle 正・trace-manifest あり。on arm なら discriminator が正常完了し `supported` / `contradicted` / blocker のいずれかを出す)。
  **on の rc=1 で blocker / 入力拒否なら原因を記録して技術的受入を保留し、再試行しない。** on arm の witness: H = 各 file 先頭に 1 行、S identity Counter = W Counter、各 1 件、C の write 数合計と一致、全 S で第 5 値 == writer txid、L/R 対応、
  空集合どうしの一致は合格にしない (commit・write・witness の実在)。rc=3 / build 失敗 / witness 欠落は不合格。結果を見て smoke を繰り返さない。
- 各走: 別 trace dir (+ witness dir) → verifier (timeout 300 s) → cycle 正の走は trace-manifest (+ witness-manifest) を作り生 trace を退避、witness on なら discriminator → 走ごとに JSON を逐次保存。
- 所要見込み: 60 走 × 約 22 秒 + build 4 + warmup ≈ 26〜29 分 / node (T-2779 の 3 arm 90 走 2222〜2233 秒からの外挿、未実測)。walltime 02:30:00。

## 5. 結果と欠測会計

| block / request | hostname | Created / Started / Ended (JST) | Elapse 秒 | arms JSON | on k/m | off k/m | on-bo1 k/m | off-bo1 k/m |
|---|---|---|---:|---|---:|---:|---:|---:|
| W1 / 10827 | bnode122 | 22:35:18 / 22:35:26 / 22:59:52 | 1471 | node1 (ba740887…) | 0/15 | **1/15** | 0/15 | 0/15 |
| W2 / 10828 | bnode119 | 22:35:37 / 22:35:44 / 23:00:08 | 1468 | node2 (f5e80223…) | 0/15 | 0/15 | 0/15 | 0/15 |
| W3 / 10835 | bnode121 | 22:35:56 / 22:36:13 / 23:00:29 | 1461 | node3 (8db96f21…) | 0/15 | 0/15 | 0/15 | **1/15** |
| W4 / 10837 | bnode109 | 22:36:16 / 22:37:43 / 23:02:04 | 1466 | node4 (ab0e84b2…) | 0/15 | 0/15 | 0/15 | 0/15 |

4 block は `.done=0`、`status=completed`、dispatcher child rc=0、accounting の終端時刻あり。各 block の (a) 保存済み = 60 (result の `runs` と `runs/` dir 集合・ordinal が一致)、
(b) 開始証拠あり未収載 / (c) 未開始 / (d) 状態不明 = 0。全 arm の計画数 = N = m = `decisive_m` = 60、failure = indeterminate = 未開始 = 0、benchmark rc=0 ×240、
verifier rc=0 ×238 / rc=1 ×2 (下記 2 走)。回転は各 arm が各位置 (1〜4) に 15 回ずつ (予定どおり、欠測なし)。
`rounds=15` は launcher 引数で、4 block の result の `rounds` / `planned_runs=60` と一致。smoke と過去 wave は合算していない。本走は runner v5 直 (wrapper 不使用、stdout に wrapper 行なし)。

| arm | k/m | G2 signal 検出率 | Clopper–Pearson 両側 95% | 位置 1/2/3/4 | commit 数 平均 (走あたり) |
|---|---:|---:|---:|---|---:|
| e9-witlight-wit (on, BACK_OFF=0) | 0/60 | 0% | [0%, 5.963%] | 15/15/15/15 | 613,741 |
| e9-witlight-nowit (off, BACK_OFF=0) | 1/60 | 1.667% | [0.042%, 8.940%] | 15/15/15/15 | 710,659 |
| e9-witlight-wit-bo1 (on, BACK_OFF=1) | 0/60 | 0% | [0%, 5.963%] | 15/15/15/15 | 788,886 |
| e9-witlight-nowit-bo1 (off, BACK_OFF=1) | 1/60 | 1.667% | [0.042%, 8.940%] | 15/15/15/15 | 933,622 |

- 片側 Fisher (行 = on / off、列 = G2 / 非 G2、on 側が低い方向): 主比較 BACK_OFF=0 `[[0,60],[1,59]]` → **p = 0.500**、副比較 BACK_OFF=1 `[[0,60],[1,59]]` → p = 0.500。
  独立・同率 Bernoulli の参考値で node 内相関・回転順・時間変動はモデル化していない。区間と母数は `summary.json` (runner v5 `summarize`、sha256 `b1be3ebd…`) と
  親の会計 `parent-accounting.json` (sha256 `20952bb6…`) で独立に計算し一致 (原本 4 本の sha256: W1 `ca8ab3ff…`、W2 `473063aa…`、W3 `f6887660…`、W4 `197a2798…`)。
- 正例 (cycle 正) は 2 走、いずれも witness off: **W1 / ordinal 18 (round 5) `e9-witlight-nowit`** = txid 452883 ↔ 452884、key 0x2 (u_ver (38,62) → v_ver (38,67)) と key 0x0 ((38,65) → (38,66))、
  **W3 / ordinal 5 (round 2) `e9-witlight-nowit-bo1`** = txid 243580 ↔ 243582、一辺 2 reason (key 0x4c (20,2499)→(20,2546)、key 0x1 (20,2544)→(20,2546)) + key 0x0 ((20,2544)→(20,2545))。
  両走とも現象名 G2・長さ 2・両辺 rw (`phenomenon` を保存済み verifier JSON の `results[0].anomalies[]` で照合し `check-phenomenon.log` に保存。親の会計 `parent-accounting.json` の `phenomenon` 欄は runner が縮約した record から取るため null で、現象名の証拠ではない。非 G2 の cycle は 0)。commit 数は 709,237 / 923,923。生 trace は各 48 file
  (261,786,377 / 341,192,067 byte、計 602,978,444 byte) を job dir に保全し、trace-manifest と集合・サイズ・sha256 が一致 (`verify-manifests.log`)。
- discriminator: on arm に G2 が無いため発火 0 件。off arm の 2 件は `not-run (witness-off)`。`comparisons` 0 件。**識別到達点 (呼出成功・正常完了・識別成功) はいずれも 0。**
- commit 数 (走あたり平均、同一 block 内): witness on は off より BACK_OFF=0 で約 14% (613,741 対 710,659)、BACK_OFF=1 で約 15% (788,886 対 933,622) 少ない。
  軽量 witness でも L 行の出力・decode・push・unlock 後の S 出力は残るので曝露量は減る。T-2774 の heavyweight on (instr-wit) 541,601 対 off 711,199 は別日・別 node の
  値であり同時刻対照ではない (性能主張ではなく曝露量の記録)。
- binding: 4 block で runner sha (7907a545…)、policy sha (66ea7135…)、toolchain (gcc-11 `b713e6ab…`)、repo_head `a99425b66`、arm 別 pin / patch sha [e9e65b78…, 0648e2c6…] /
  witness / observational_only / source file sha (`d22b8e43…`、4 arm × 4 block で同一、smoke とも同一) を照合した。bo1 だけ `-DCCBENCH_BACK_OFF=1`。
  binary sha は build ごとに異なる (path 埋込み等、命令列の一致は未確認)。node 専有の実証はしていない (runner の `_assert_single_tenant()` の射程まで)。
- smoke (request `10799.nqsv`、bnode084、22:30:07〜22:32:31 JST、Elapse 148 秒、wrapper 経由、node1 JSON、rounds 1): 4 走 benchmark rc=0・verifier rc=0 (cycle 0)、
  build 4 arm、binding 一致、wrapper 複製 4 run / 288 file (manifest)。on arm 2 走の witness 検算: H は各 file 先頭に 1 行 (48/48)、S の identity Counter = 標準 trace の W Counter
  (3,014,285 / 3,933,687 = C の write 数合計)、各 identity 1 件、L = R = C の read 数合計 (2,968,147 / 3,873,346)、**全 S で第 5 値 (保存 producer) == writer txid (不一致 0)**、
  W の op は全 U、L の producer は `G -` (未書込 genesis) 約 9.9k + `T`。smoke は 1 回だけ (再試行なし)。合算していない。

## 6. 解釈の上限と次の実験

| 結果 | 言える範囲 | 言えないこと |
|---|---|---|
| on 0/60、off 1/60 (両 BACK_OFF) | この標本・条件では on/off の率差を検出できない (p=0.500)。on の CP 上限 5.96%、off の点推定 1.67% | 軽量 witness の観測者効果の有無・大きさ、G2 不在、同等性、計器改善の因果 |
| on の G2 = 0 | 今回の条件・標本では識別対象を得なかった | discriminator の実例での識別性能、実 anomaly / torn read の別 |
| off の G2 2 件 | verifier の G2 signal (T-1892 と同形) が同一 source の off で再現 | payload lineage による識別、根因 |

- 設計仮定下の検出力 (K=60、off 率 0.0417 の完全抑制で 0.105) が低く、今回も率差を検出しなかった。検出不能な設計ではないが、認可枠 60 の上限として検出力を明記する。off の点推定 1.67% (2/120 合算)
  は T-2779 通常 arm 5/120 = 4.17% (旧 witness source・別日・別 block、合算しない) より低い。同一意味 (witness off) の別 source・別日で率が動くことは、率そのものの標本誤差
  (CP 区間は重なる) と node / 日の効果の両方と両立し、本 wave では分離しない。
- 問い (ii) を実際に試すには、witness on で G2 を得る必要がある。次の候補 (本 wave では起動しない、ユーザー確認待ち): (a) 同設計で K を増やす (完全抑制の検出力を 0.5 超にするには
  各 arm 120 以上、off 率 0.017 なら更に多い)、(b) 曝露量を増やす (extime 延長、ただし cell 変更は事前登録の再設計)、(c) 観測者効果の残余 (L 行・reserve・E 行) を更に軽くする設計
  (S 遅延だけでは on の曝露量は off の約 86% に留まる)。いずれも非 certifying の観測として設計し、結果を見て標本を増やさない。
- 規律 2 / 7: verifier・discriminator・X/P・gitlink は不変。T-1892 5/42、T-1943 no-g2、T-2774 Q1/Q2、T-2779 の 5/120・0/120・2/120 は旧束縛で保持。個別 verifier の `certified=true`
  (238 走) と arm 属性 `observational_only=false` は本 wave・MOCC・軽量 witness の認証を意味しない。certified 昇格・pin 前進 (D2114 項 3 / D1603)・変異探索解禁 (D2134) は変えない。
- CCBench 側への扱い: W は D16 の trace-hook 分類で hook branch に置き、上流 push は人間判断。gitlink は 511c9538 のまま。

## 7. 実装・検査・レビュー・回収の記録と再現資料

- 段 2 plan (codex read-only、35 KB): P1/P2/P5/P6 採用、P3 (`#line` 不要、TLS を有効分岐内)・P4 (off の保証の限定) を補正、smoke wrapper を提案。段 3 レンズ A (観測意味論・identity):
  条件付き GO、MF1 (合成 source の TRACE=0 identity は未担保 → TRACE=1 観測専用と明記)、MF2 (brief の「成果物影響なし」撤回)、refuted 4 (S 遅延の意味論・parser・TLS 残留・INSERT/DELETE)。
  レンズ B (実験設計・収集): 条件付き GO、M1 (変異免除を outer repo の差分ゼロ範囲に限定し W / patch / wrapper の挙動検査を登録)、M2 (smoke 合格集合を結果前に固定)、M3 (S 第 5 値の被覆)、
  M4 (4 投入元の開始条件)。検出力・回転は親と一致。全件 real・採用 (`s4-ruling.md`)。
  B-M4 の実施証拠: `check-base-dirs-2.log` (22:27 JST、outer HEAD・index gitlink・submodule HEAD・pin 解決・orphan hold・dirty、base git dir は含まない) と、各 result の
  `bindings.base_dir` / `base_git_dir` の事後照合 (5 request の投入元が相互に異なる)。**投入直前の `ps` 実測 (22:27:13 と 22:35:10 JST に本 wave の dispatch 0 件、W4 投入後に 4 件)
  は親の session 記録にあり保存 log には無い。当時それ以外の同一投入元 dispatch が存在しなかったことは遡及検証できず、未確認の事前条件として扱う** (段 6 レビュー B M1)。
- 段 5 author (codex workspace-write、10 call、受理): `W.patch` / `witlight.patch` / arms JSON ×4 / `smoke_capture.py` を scratch 上で作り、4 系列 `git apply`・同内容性 `cmp`・touch set・include 列・
  JSON・wrapper の最小確認を自走。submodule 非接触、commit は親。
- 親の検査 (login、`check-patches.log` / `check-identity.log` / `mk-W-commit.log` / `amend-W.log`): V1 identity 正例 ×2 `pass` / `match`、V2 負例 rc=1 (include 契約、単一理由)、
  V3 同内容性 MATCH (`#line` 除去後 39,378 byte、レビュー A が独立再構成で一致)、V4 負例 (適用可能な 1 byte 変異 `stored_index++` → `stored_index+1`) MISMATCH、
  4 系列 apply rc=0、touch set 各 1 file、include 列一致、TRACE 外 31,698 byte 一致 (レビュー A)。検査 script の最終 rc は各検査の合否を集約していない (レビュー A S1) ので、
  合否は各 log・JSON の個別証拠で読む。V5 (wrapper の観測義務) は author の最小確認、V6 (smoke の S 件数・identity・第 5 値) は §5、V7 (保存値 pass-through) は author の逐語引用 +
  レビュー A の独立引用 (静的確認、runtime 注入は未実施)。outer repo の実装面差分は 0 (gitlink・patches/・runner 不変、insight + spool のみ) → 製品実装の変異 matrix はその範囲に限って免除。受入全走は land 前に実施 (結果は worklog)。
- 段 6 レビュー A (read-only): W のコード・identity・同内容性に阻害欠陥なし、B-M3 静的確認合格。must-fix 2 = 草稿の identity 説明から policy digest 一致を分離 (§2 に反映)、
  W の trailer に採用判断へ寄与した codex reviewer 行を追加 (W を message だけ amend、`e0905b3d` → `5b02546f`、tree 不変、identity 2 本 + 負例を新 OID で再走し同結果)。
  should 1 (script の rc)、nit 2 (path、`result=pass` / `match` の階層) を反映。段 6 レビュー B (read-only、結果と収集): 240 走 + smoke 4 走の個別 JSON・raw・manifest を
  独立集計し k/m・decisive_m・CP・Fisher・回転・binding・現象名・manifest・smoke の H/S/第 5 値がすべて親と一致 (再走・補充不要)。must-fix 2 = B-M4 の投入直前 `ps` 実測の保存証拠が
  無い (§7 本項に未確認範囲を明記)、草稿の smoke 合格集合から blocker / 入力拒否時の保留条件が脱落 (§4 に復元)。should 3 (`decisive_m=60` 明記、現象名照合の証拠を親会計と分離、
  低検出力を「判定不能」と書かない) と nit 1 (「4 node 同一 block」→ 4 block) を反映。fix 子 0 (docs のみの修正)。
- W の保全: bundle `W.bundle` (自己完結、完全履歴、`git bundle verify` 済、3,215,451 byte、sha256 `874f6dc064bad128c3d310e49d55ea1f63d187cd0a6b9d98e292a84d3c1a4351`) を job dir に保全。
  主 checkout の submodule git dir への branch `izanagi-t1943-mocc-g2-witlight` の fetch (T-1943 の先例) は段 9 の land 後・worktree 撤去前に行う (実施結果は worklog)。gitlink は 511c9538 のまま。
- 再現資料 (job dir `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/`): `probe/` (runner v5、`W.patch`、`witlight.patch`、arms JSON ×4、`smoke_capture.py`、`W-commit-message.txt`)、
  `arm-W/{smoke,W1..W4}/result.json` と `runs/<ordinal>-<arm>/`、`arm-W/smoke-evidence/`、`arm-W/summary.json`、`arm-W/parent-accounting.json`、`dispatch-*.log`、
  `check-*.log`、`identity-*.json`、`superseded-e0905b3d/`、`s1-brief.md`、`s4-ruling.md`、`codex/` (prompt・plan・consult・author・review の全文と launcher)、`HANDOFF.md`。
  投入は `codex/launch-smoke.sh` (smoke) / `codex/launch-block.sh <B> <worktree> 15 <json>` (本走)。
- verbatim (本 dir `verbatim/`): `W.patch.txt`、`witlight.patch.txt`、`arms-witlight-node{1..4}.json`、`smoke_capture.py.txt`、`W-commit-message.txt`、`s1-brief.md`、`s2-plan.md`、`s3-lensA.md`、`s3-lensB.md`、
  `s4-ruling.md`、`s5-author.md`、`s6-reviewA.md`、`s6-reviewB.md`、`prompt-*.md`、`summary.json`、`parent-accounting.json`、`identity-511c-to-W.json`、`identity-e9-to-W.json`、`identity-V2-negative.stderr.txt`、
  `check-*.log`、`W1..W4-result.json`、`smoke-result.json`、`smoke-capture-manifest.json`、`W1-018-e9-witlight-nowit/` と `W3-005-e9-witlight-nowit-bo1/` (run / verifier / trace-manifest / discriminator の JSON)、
  `W.bundle.sha256.txt`、`operational-facts.md`。**逐語 17 file は行末空白の検査のため行末の空白を除去した (可視文字不変)。原本の sha256・byte 数・復元法は `verbatim/NORMALIZATION.md`** (DW-S07 の可逆最小正規化)。
