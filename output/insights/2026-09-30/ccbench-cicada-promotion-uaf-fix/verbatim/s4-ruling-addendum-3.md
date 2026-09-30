# 段 4 追補 3 — F4 の採用、M3 の erratum (2026-09-30 14:1x JST、親)

## F4 (INLINE_VERSION_OPT=1 の Tuple::init) — 採用

根拠: 診断 4 回目 (m1 木、Elapse 151 秒、job rc=0、status observed) の evidence/diag-4/result.json。TPC-C Release TRACE=0、thread 4、extime 1、warehouse 1、build 交互、M・R2 × 各 2 反復。

| build (土台 = aa8e36f1) | genome | M r1・r2 | R2 r1・r2 |
|---|---|---|---|
| T0 = 土台 | OPT=1・PROMO=1 | SIGABRT・SIGABRT | SIGABRT・SIGABRT |
| T1 = + v-uaf-reorder | 同 | SIGABRT・SIGABRT | SIGABRT・SIGABRT |
| T2 = + v-update-keep | 同 | SIGABRT・SIGABRT | SIGABRT・SIGABRT |
| T3 = + v-ronly-nopromo | 同 | SIGABRT・SIGABRT | SIGABRT・SIGABRT |
| T4 = + v-init-ver | 同 | 完走・完走 | 完走・完走 |
| T5 = + v-init-ver + v-uaf-reorder | 同 | 完走・完走 | 完走・完走 |
| T6 = + v-init-ver + v-uaf-reorder + v-update-keep | 同 | 完走・完走 | 完走・完走 |
| T0p = 土台 | OPT=1・PROMO=0 | SIGABRT・SIGABRT | SIGABRT・SIGABRT |
| T4p = + v-init-ver | OPT=1・PROMO=0 | 完走・完走 | 完走・完走 |

SIGABRT の stderr は `std::bad_alloc` の terminate (一部は複数 thread の `terminate called recursively` だけが先頭に出て bad_alloc の文字列が先頭 3 行に入らない)。事前登録 (追補 1) の条件 (i) T0 と T0p がともに落ち、(ii) T4・T4p・T5 が全反復で完走、を満たす。予測 (T1〜T3 は落ちる、T4・T5 は完走) も当たった。

**帰結:** TPC-C の異常終了の原因は promotion ではなく INLINE_VERSION_OPT=1 の insert (`Tuple::init` が渡された版を無視する) で、promotion 無効の OPT=1 genome でも起きる。T-2922 の「TPC-C M・R2 × thread 4 が bad_alloc」は INLINE_VERSION_OPT=1 の 16 genome の欠陥として記録し直す。既定 genome (OPT=0) は影響しない。前 wave §5 の「promotion の失格」のうち TPC-C の部分の帰属は訂正になる (追記で訂正する)。

## ASan (UAF)

ASAN (土台、代表 promotion genome) は M で `heap-use-after-free` 1 件で rc=1 終了 (診断 1・2・4 回目とも同じ frame: writeSetClean ← abort、解放は abort)。ASAN-T5 (init-ver + uaf) と ASAN-T6 (+ update-keep) は報告 0 件で完走。F4 が無いと bad_alloc が先に起きうるので、F3 の確認は F4 と組で行う。

## F2 の効果 (TPC-C の観測値)

stdout の `insert order failed` 行数 / 走行:

| build | M r1・r2 | R2 r1・r2 |
|---|---|---|
| T4 (F2 相当なし) | 313,180・298,560 | 28,175・30,980 |
| T5 (F2 相当なし) | 299,312・320,051 | 29,289・30,736 |
| T6 (F2 相当あり) | 18,802・18,511 | 1,007・1,078 |
| T4p (promotion 無効) | 19,260・19,076 | 1,383・1,385 |

F2 相当なしでは promotion 無効の約 16 倍 (M)・約 22 倍 (R2)、F2 相当ありで promotion 無効と同じ水準。親の読み (promotion の書き込みが district の次の注文番号の加算を握りつぶす) と整合するが、どの表のどの行かは計数していない。promotion 無効でも出る約 1.9 万件 (M) は並行 NewOrder どうしの注文番号の衝突の水準と見る (既定 genome OPT=0 の水準は測っていない)。

## M3 の erratum (事前登録の差し替え、初回の登録は消さない)

初回登録: 「修理後 tip から fix2 を逆適用した版に単位 D の diag-counters.patch を当て update_skip > 0」。X の login 検査で diag-counters.patch は fix2 を戻した木に fuzz なしで当たらない (preimage が土台 + 診断変種 + TPC-C 計装) ことが分かった。
差し替え: M3 = 修理後 tip から fix2 だけを逆適用した Release TRACE=0 build (代表 promotion genome) と修理後 tip の Release build を同じ job で交互に TPC-C M × 1 ずつ走らせ、`insert order failed` 行数が 逆適用版 > 5 × 修理後 tip であること (診断 4 回目の比 約 16 倍から、結果を見る前に 5 倍を閾値に置く)。kill に数えない感度 pin (判定器は値を見ない)。
