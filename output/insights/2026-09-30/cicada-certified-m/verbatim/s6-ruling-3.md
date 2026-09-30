# 段 6 裁定 3 — md_33 (wave dev-wave-cicada-certified-m、2026-09-30)

入力: focus2.md (焦点再レビュー 2 巡目、NO-GO = 実測確認待ち + N1)、親の SMOKE 2 回目 (request 39032.nqsv、Elapse 145 s、`runs/smoke-2/result-SMOKE.json`)。対象 = 5c968c978 と job dir の起動器・変異 patch。fix 前の snapshot は `snapshot-pre-fix3/`。

**smoke-2 の実測 (親が result から読んだ値):** stock・E-max の 5 run (default K t4、best R t4、best E-max A10 t8、壊し B の専用 cell の stock 対照 default BD t8・best BB t8) はすべて `pass` (巡回 0、integrity 数値項目 0、C 行 = commit 数、READ_WTS_MISMATCH 0、M の違反 0、等式 7 本成立、照合件数 > 0)。BEST と E-max で inline 版の事象 (`ev_gc_inline`・`ev_reuse_inline`) が 2,345〜371,641 件。run 1.0 s、判定器 4.4〜22.4 s、build 4.7〜5.2 s、trace 76〜402 MB。壊し 4 本と旧壊し 1 本の build は失敗 (下の D1・D2)。

| ID | 裁定 | 処置 |
|---|---|---|
| F1 | closed (静的、focus2)。stock 5 run で偽の B 違反 0 (実測) | なし |
| F2 | closed。stock・E-max 5 run で `b_registered = b_elements_checked`・`api_checked + read_not_found + read_other_status = read_calls` が成立 (実測)。照合分岐を壊したときの検出は壊し API と変異 MV-API で見る | なし |
| F3 | closed。U1 の関数対応表 (fix2-u1.md) と、E-max A10 の run で B・U・API の等式と照合件数が成立したこと (実測) | なし |
| S2 | closed。smoke-2 で configure と stock 系の build が成功 (実測) | なし |
| D1 (親) 壊し B が compile できない (`transaction.cc:1156` で `clock_delay` 未宣言) | real (must-fix) | U1: 壊し B の待機を `transaction.cc` で使える既存の時刻 API (例: `rdtscp()` と `FLAGS_clocks_per_us`) で書き直す。`pin C → instr → M → 壊し B` と `… → mv-b → 壊し B` の適用に加え、TRACE=1 の compile が通る形であることを、同じ TU で既に使われている識別子だけで書くことで担保し、報告に使った識別子の宣言元 file:line を書く |
| D2 (親) build 失敗後に同じ build dir を使い回し連鎖失敗 | real (must-fix) | U2: build ごとに一意な build dir を使い、configure・build の失敗後はその dir を再利用しない。失敗した build に依存する run だけを失敗扱いにし、他の build は続ける |
| N1 失敗ログに byte 上限が無い | real (should) | U2: 末尾 200 行に加えて各 64 KiB の byte 上限を設ける。秘密の伏せ字は、この起動器が扱う出力 (cmake・compiler・ベンチ・判定器) に秘密が載る経路が無いので実装しない |

焦点再レビューは fix 3 の後に 3 巡目 (上限) を行う。
