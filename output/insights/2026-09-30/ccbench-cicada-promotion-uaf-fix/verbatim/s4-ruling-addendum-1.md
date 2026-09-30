# 段 4 追補 1 — 診断 1 回目の結果と事前登録 (2026-09-30 13:3x JST、親、D2 の再走結果を見る前)

## 診断 1 回目 (request 37853.nqsv、m1 木、Elapse 250 秒、job rc=2) で分かったこと

根拠: job dir evidence/diag-1/result.json・logs/ (Codex author の launch_promo_diag.py、D1 版)。

1. **YCSB (巡回) — (P1) を支持。** 同じ job 内で build 交互、genome OPT=1・PROMO=1・BACK_OFF=0・REUSE=1・WLO=0、thread 4、1 秒。
   | build | cell・反復 | 判定器 | 再検査起点差で通った commit の event 数 | 読み取り専用での promotion 成功 |
   |---|---|---|---|---|
   | Y0 (土台 + 診断変種 + TPC-C 計装 + 計器) | K r1 | rc=3、巡回 0 | 8 | 308 |
   | Y0 | K r2 | rc=1 (non-serializable) | 11 | 299 |
   | Y0 | R r1 | rc=1、巡回 344 (代表 witness 20) | 1,972 | 241,069 |
   | Y0 | R r2 | rc=1 | 1,967 | 238,328 |
   | Y1 (Y0 + 読み取り専用 promotion 無効) | K r1・r2、R r1・r2 | 4 走行とも rc=3、巡回 0、integrity 数値項目 0、C 行 = commit 数 | 0 | 0 |
   event の `later_status` はすべて 2 (= aborted、VersionStatus の列挙順)。相談 A の「`later_ver_` が aborted で、その手前に wts 未満の確定版が入る」と一致。witness と event の tx 照合は、job が判定器 JSON (stdout の後ろに stderr が連結) を読めず未取得 → D2 で取り直す。
2. **TPC-C (異常終了) — 原因は promotion ではない見込み。** gdb の catch throw (DBG-M-r1) で `std::bad_alloc` の送出点は `HeapObject::allocate(size=0, align=0)` ← `TupleBody::operator=` ← `Tuple::init(thid, ver, initial_wts)` (tuple.hh:103) ← `TxExecutor::insert` (transaction.cc:315) ← Payment の insert_history。静的な読み: `Version()` は status を pending にするので新しい Tuple の inline 版は取れず insert の版は別確保になるが、INLINE_VERSION_OPT=1 の `Tuple::init(…, ver, …)` は ver を無視して空の inline 版を latest_ にし、その空 body を複写して align 0 の new が失敗する。**(P2) の候補 (a)〜(c) のどれでもない新しい候補 (d)。** これが正しければ INLINE_VERSION_OPT=1 の 16 genome (promotion 無効の 8 を含む) すべてで insert のある workload が落ちる。既定 genome は OPT=0 (cmake/Options.cmake:53) なので影響しない。
3. **UAF — 実在を ASan で確認。** ASAN-M-r1: `heap-use-after-free` WRITE size 8 at writeSetClean (transaction.hh:345、`continuing_commit_` の store) ← abort (transaction.cc:756)、解放は abort (transaction.cc:752)。job は halt_on_error=1 と `#FLAGS` 照合で止まり後続 T0〜T3 は未走行 → D2 で直した版で取り直す。
4. **値の欠落 (F2 の対象) — 発火を確認。** Y0 の `update_skip` (promotion が積んだ要素への後続 update の素通り) は K で 5,709・5,800、R で 904・854 件 / 走行。

## 事前登録 (D2 の再走の結果を見る前)

- **R1 の確定条件:** D2 の再走で、Y0 の巡回 witness のうち event の tx (再検査起点差で通った commit) を含むものが 1 件以上あり、Y1 は全走行で巡回 0 なら F1 を採る。Y0 の witness に event の tx が 1 件も無ければ F1 を保留し追補 2 で再裁定する。
- **新しい修理 F4 (候補):** INLINE_VERSION_OPT=1 の `Tuple::init(thid, ver, initial_wts)` が渡された ver を latest_ にし body_ を ver->body_ から取る (`#if INLINE_VERSION_OPT` の内側だけ、OPT=0 の分岐と同じ意味)。採る条件 = D2 の TPC-C で (i) 土台 (T0) と promotion 無効の OPT=1 genome の土台 (T0p) がともに bad_alloc で落ち、(ii) v-init-ver を当てた T4・T4p・T5 が M・R2 の全反復で完走する。(i) の T0p が落ちなければ「promotion との相互作用」を疑い追補 2 で再裁定。F4 を採るなら T-2922 の対象は「promotion 8 genome」から「INLINE_VERSION_OPT=1 の 16 genome の TPC-C」へ広がることを一次資料と fragment に書く。
- **F3 (UAF) の確認:** D2 の ASan で土台は `ERROR: AddressSanitizer` ≥ 1、T5 相当 (v-init-ver + v-uaf-reorder) は 0 件。
- **予測 (外れても記録する):** T1 (UAF 修理のみ)・T2 (素通り修理のみ)・T3 (読み取り専用 promotion 無効のみ) は T0 と同様に落ちる。T4・T5 は完走する。
