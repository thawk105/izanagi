# 段 4 追補 2 — R1 の確定、段 6 レビューの裁定、確認 job の縮小 (2026-09-30 13:5x JST、親)

## R1 (巡回の修理 F1) — 採用確定

根拠: 診断 2 回目 (request 37912.nqsv、m1 木、Elapse 280 秒) の evidence/diag-2/result.json。事前登録 (追補 1) の確定条件「Y0 の巡回 witness のうち event の tx を含むものが 1 件以上、Y1 は全走行で巡回 0」を満たした。

| build | cell・反復 | 判定器 rc | 巡回 (SCC) | 代表 witness | event の tx を含む witness | event の key の rw 辺を持つ witness | event 数 |
|---|---|---|---|---|---|---|---|
| Y0 (修理前) | K r1 | 1 | 7 | 7 | 7 | 7 | 11 |
| Y0 | K r2 | 1 | 5 | 5 | 5 | 5 | 7 |
| Y0 | R r1 | 1 | 372 | 20 | 20 | 20 | 1,979 |
| Y0 | R r2 | 1 | 379 | 20 | 20 | 20 | 1,981 |
| Y1 (読み取り専用 promotion 無効) | K r1・r2、R r1・r2 | 3 | 0 | 0 | — | — | 0 |

照合は代表 witness (判定器の報告は最大 20 件) に限る。R の 372・379 件の SCC 全部を照合したのではない。診断 1 回目 (request 37853.nqsv) も同じ向き (Y0 の 3/4 走行が non-serializable、Y1 は 4/4 で巡回 0)。

## 段 6 レビュー (out/s6-review-A.md・s6-review-B.md) の裁定

| # | 所見 | 裁定 | 扱い |
|---|---|---|---|
| A-1 | F2 の目印を `update()` 後の再探索で立てるので、要素を積まなかったときに既存要素へ誤って立ちうる | real (静的に発火経路は未確認)・採用 | fix: `write_set_` が 1 増え status が aborted でないときだけ末尾要素に立てる (B の再探索削減と同じ直し) |
| A-2 | F3 の退避配列の確保 | real・nit | 限界として記録。writeSetClean が write_set_ を clear するので退避は必要 (fix3.msg に理由) |
| A-3 | 壊し patch の event が tx 単位の真偽値で、promotion した key に限らない | real・採用 | fix: promotion した key の read 要素だけを event にする |
| A-4 / B-4 | 確認 job が M1〜M3 の期待を合否に結んでいない (0 件でも observed) | real・must-fix | fix: M1 = non-serializable ∧ witness の同じ巡回の辺に event tx と event key、M2 = 指定 frame (writeSetClean ← abort) の heap-use-after-free、M3 = update_skip > 0 (kill に数えない感度 pin、patch 不適用は未達) |
| A-5 | 異常終了した走行の `#FLAGS` 照合で止まる | real・must-fix | fix: 単位 D の D2・D3 と同じ扱い (異常終了は「未出力」、表示されない flag は argv で束縛、共通 flag の表示は必須) |
| A-6 | D297 の tip 検査が「期待した拒否」かを判定しない | real・採用 | fix: rc と stderr の未知 macro の文言で拒否を確認。probe 側の受理条件は緩めない |
| B-1 | 修理前 8 genome の YCSB 再走・走らせない非 trace build・D と重なる修理前 TPC-C/ASan を削る | real・採用 | 修理前の対照は単位 D の同 SHA・同設定の走行を再使用 (YCSB は diag-2 の Y0、TPC-C・ASan は diag-3)。確認 job の土台側は代表 genome の YCSB K・R と TPC-C M・R2 を各 1 回だけ同じ job 内に置く (同時刻の対照、R7) |
| B-2 | 削ってはいけない核 | 採用 | 修理後 8 genome × YCSB K・W・R・P、修理後 8 genome × TPC-C M・R2 (trace + 判定器)、代表 genome の TPC-C 反復 3 回、ASan 前後、M1〜M3、上流 CI、D297 |
| B-3 | 記録量 (全 verifier の sha・全 cicada patch の適用表) | nit・採用 | 適用検査は計装 2 本 + 壊し patch に絞る |
| B-5 | F4 を足すときの最小追加 | 採用 (F4 の採否は追補 3) | OPT=1・PROMO=0 の代表 genome の TPC-C M・R2 (trace + 判定器) を修理後 tip で |

## 確認 job の条件表 (修理後 tip = 土台 + fix1〜fix4 の 4 commit を前提。F4 不採用なら追補 3 で直す)

| part | build | 走行 |
|---|---|---|
| ycsb | 修理後 trace 8 (promotion 8 genome)・土台 trace 1 (代表)・M1 (修理後 + 壊し) 1 | 8 × K・W・R・P = 32、土台 K・R = 2、M1 は R から始め成立まで最大 K・R 各 2 |
| tpcc | 修理後 trace 8 (promotion 8 genome)・修理後 trace 1 (OPT=1・PROMO=0 代表)・修理後 Release 1 (代表)・土台 Release 1 (代表)・ASan 修理後 1 (代表)・M2 1・M3 1 | trace 9 × M・R2 = 18、Release 修理後 M・R2 × 3 = 6、土台 M・R2 × 1 = 2、ASan 修理後 M × 2、M2 M × 1、M3 (YCSB K、計器) × 1 |
| ci | CI image 全 protocol build 1、format 1、D297 2 面 | — |
