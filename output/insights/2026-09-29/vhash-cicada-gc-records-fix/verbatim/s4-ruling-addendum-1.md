# 段 4 追補裁定 1 — V1・V2 と段 6 レビューを受けて (2026-09-29 23:4x JST、親)

入力: v1-result-summary.md、runs/v2/result-CUSTOM.json、review-a.md、review-b.md (どちらも受理済み)。

## 確定した事実 (事前登録どおりの判定)

- V1: 無修理 F_T0 は t4 10/10・t8 10/10 が gc_records の ERR、修理版 FIX_F_T0 は 20/20 完走、pin C + 修理 3/3 完走、M2 (1 段だけ読み飛ばす変異) は t4 10/10・t8 3/10 が ERR で KILLED。
- V2: delete を含まない M・R2 は修理版・無修理版とも各 2/2 が合格 (巡回 0・integrity 数値項目 0・存在履歴違反 0・C 行 = commit 数) で判定不変。identity (F + fix) 対 (F + instr + instr-tpcc + fix) の TRACE=0 は tpcc の 3 TU で compile command・命令列・前処理とも一致、nm・strings も一致。
- V2 の F cell 修理版 3 run は完走 (rc=0)、W op D 1,510〜1,636 件を 4 thread 全部が出し、計数 patch の読み飛ばし回収は 246〜315 回/run (修理分岐は同じ run で発火)。**しかし判定器は parse error (rc=2)** で判定できていない。M3 (SKIPRC) も同じ parse error。

## 新事実 S (real、scope 内に取り込む)

`TxExecutor::scan()` は結果の tuple の key を最新版の body から取る (transaction.cc:430-432、上流の TODO コメント付き)。削除版は body を持たない (`new Version(wts)`、transaction.cc:400)。最上段に削除版 (abort して残ったもの、または pending の削除) がある NewOrder 行を scan すると key が空になり、read set の要素と trace の R 行の key が空になる (V2: `R 558 5  1 0`、1 file あたり約 90 行)。
影響: (i) trace が判定器に掛からない (完了判定の trace 項目が取れない)。(ii) CC 自体でも、空 key の read set 要素は `searchReadSet(s, key)` / `searchWriteSet` の key 照合で別の tuple の空 key 要素と一致しうる (read-own-reads が別の行の body を返す)。
修理前は同じ状態に達する前に gc_records の ERR で落ちていたので見えなかった (D1 の走行は 0 秒台で止まる)。md_17 の F t1 は abort が無いので起きない。

裁定: 依頼の完了判定 (修理版 trace が判定器を通る) に必要なので、本 wave で直す。修理 S = scan の key を `Tuple::body_` (tuple.hh:34、作成時に最初の版の body を深く複写し以後変えない。初期 load は tuple.hh:84-91、insert は tuple.hh:99-106 で、insert の版は newVersionGeneration が body 付きで作る) から取る 1 行の変更。受理集合: key が空でない通常の場合は同じ key なので挙動不変。空 key の場合だけ正しい key に変わる (誤った read-own-reads の一致が無くなる)。
置き場: 上流の「1 issue = 1 context」(CCBench docs/contributing_ja.md) に合わせ、別 patch `patches/fix-cicada-gc-records-scan-key.patch` (所有の glob `fix-cicada-gc-records*.patch` 内) と、CCBench branch の 2 つ目の commit にする。2 本は行が離れていて (432 と 849) 独立に当たる。適用順は gc-records → scan-key。

## 新事実 U (real、scope 外として記録)

ASan (V1 FIX_F_ASAN 3/3) の heap-use-after-free は修理と無関係の既存欠陥: `abort()` が INSERT した tuple を `delete` した (transaction.cc:750) 直後、`writeSetClean()` が同じ要素の `rcdptr_->continuing_commit_` に書く (transaction.hh:345)。insert を含む tx が abort すれば delete の有無に依らず起きる。Release では解放直後の同じ thread の書き込みで、実害は小さいと見込む (推測) が未定義動作。**本 wave では直さず**、一次資料と worklog の次の一手に新 item として記録する (直し方の候補: writeSetClean で INSERT 要素の tuple に触れない、または abort の削除を writeSetClean の後に回す)。
A1 (回収の寿命) の ASan 検査は、U を避ける使い捨ての回避 patch (repo 外、Codex author、CCBench にも patches/ にも入れない) を重ねた ASan build で取り直す。

## 段 6 レビュー所見の裁定

| 所見 | 判定 | 処置 |
|---|---|---|
| A-1 identity 判定が compile command 一致を要求しない | real (今回の測定値は compile command も一致していたので結論は不変) | 起動器を既存 L0 系と同じ条件 (compile command 一致 + 命令列一致) に揃える (fix)。 |
| B-1 M2 の分類が起動器に無い | real | 親が集計して記録 (V1: KILLED)。起動器は変えない。 |
| B-2 V1 の見積り 76 run は実際 66 run | real (nit) | 一次資料に実施数 66 を書く。 |

## 追加の事前登録 (V3、結果を見る前に固定)

計測木 2 本から 2 job を同時投入。fix2 = fix-cicada-gc-records.patch → fix-cicada-gc-records-scan-key.patch。
**V3a (TRACE=0・ASan、gcfix-m1):**
| build | run | 期待 |
|---|---|---|
| F_T0 (無修理、同時刻対照) | F×t4×5、F×t8×5 | thread ごとに既知 ERR ≥ 1 |
| FIX2_F_T0 (F + fix2) | F×t4×10、F×t8×10 | 20/20 rc=0 |
| C_FIX2_T0 (pin C + fix2) | F×t4×3 | 3/3 rc=0 |
| ASAN_F_M (F 無 patch、ASan) | M×t4×2 | record-only (U が修理と無関係に stock で起きることの帰属) |
| ASAN_FIX2_WA_F (F + fix2 + U 回避、ASan) | F×t4×3 | 3/3 rc=0 かつ ASan 報告 0 (gc_records の回収の寿命) |
**V3b (TRACE=1、gcfix-m2):**
| build | run | 期待 |
|---|---|---|
| FIX2_F_TRACE (F + instr + instr-tpcc + fix2 + count) | F×t4×3、M×t4×2、R2×t4×2 | trace-pass (巡回 0・integrity 数値 0・存在履歴違反 0・C = commit 数・READ_WTS_MISMATCH 0、F では W op D > 0・D の thread ≥ 2・読み飛ばし回収 > 0) |
| SKIPRC_FIX2_F_TRACE (F + instr + instr-tpcc + broken-skip-read-recheck + fix2) | F×t4×1 | trace-cycles (non-serializable・巡回 > 0) |
| identity | (F + fix2) 対 (F + instr + instr-tpcc + fix2)、TRACE=0、tpcc 3 TU | compile command・命令列が一致 |
M4 (scan-key 修理を外した変異) = V2 の FIX_F_TRACE (fix だけ) が parse error で trace-pass を満たさなかったこと (既測、KILLED)。
見積り: V3a 5 build・38 run (当初 48 と誤記、焦点再レビューで訂正)、V3b 2 build + identity・8 trace run。合計 < 0.3 node 時間。
