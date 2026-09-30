## 所見 — 削れるもの

- **should｜8 genome 分の修理前 YCSB build・16 走行を削る。** 現行 job は土台の trace build を 8 本作り、K/R を各 genome で走らせる（`launch_promo_confirm.py:301–318`）。裁定 R7 が求める土台の対照は代表 genome であり、同 SHA・同設定なら単位 D の Y0 K/R を再使用できる（`s4-ruling.md:36`、`s4-ruling-addendum-1.md:7–15`）。放置すると、帰属を増やさない build と走行に node 時間を使う。D2 の witness と event の照合が成立した結果を代表対照として引用し、他の土台 genome は走らせない。

- **should｜YCSB の非 trace build 8 本を削る。** これらは build するだけで走行も判定も行わない（`launch_promo_confirm.py:307–309,313–321`）。修理後 8 genome の build と小走行は各 trace build で確認でき、上流の通常 Release build は CI が担う（`s4-ruling.md:36`）。放置すると同じ genome の build を重ねる。trace 8 本を残す。

- **should｜代表土台の TPC-C Release 2 走行、土台 ASan の再走を D2 と照合して削る。** 現行の再走箇所は `launch_promo_confirm.py:330–360`。D2 は T0/T0p の M・R2 と土台 ASan M を予定している（`diag/launch_promo_diag.py:436–446`）。放置すると同じ SHA・genome・flag の対照を重複採取する。D2 が完走し設定も一致した分だけ結果を再使用する。D1 は YCSB 8 走行と gdb まで記録されたが、ASan は結果に登録される前に停止したため、D1 の `result.json` だけを ASan 対照 1 回と数えない（`s4-ruling-addendum-1.md:17`、`evidence/diag-1/result.json`）。

- **should｜M1 の K/R 各 2 回を、帰属が成立する最初の cell から始める。** 現行は 4 走行固定（`launch_promo_confirm.py:319–321`）。必要なのは non-serializable と、壊し event の commit tx・key が witness の辺に入る正例 1 件（`s4-ruling.md:37,46`）。放置すると正例成立後も走行する。D2 で巡回が強く出た R を先に走らせ、不成立なら K と追加反復へ進む。

**最小条件表。** D2 の予定結果が得られ、土台との SHA・設定一致を確認できた場合の X 側の条件である。これは上限 2 node 時間を保証する実測値ではない。D1 の使用済み 250 秒と D2 見込み 400～800 秒を先に計上し、X の実測経過を合算する（`md_32.txt:37`、`diag/README.md:20–27`）。

| 条件 | X 側の最小 build | X 側の最小走行 |
|---|---:|---:|
| 修理後 YCSB、promotion 8 genome | trace 8 | K/W/R/P ×各 1＝32 |
| 修理後 TPC-C、promotion 8 genome | trace 8 | M/R2 ×各 1＝16 |
| TPC-C 反復完走、代表 genome | 通常 Release 1 | M/R2 ×各 3＝6 |
| UAF、代表 genome | 修理後 ASan 1 | M ×2。修理前の必要回数は D2 と照合して補う |
| M1・M2・M3 | 各 1 | M1 は成立まで最低 1、M2・M3 は各 1 |
| 上流 CI・D297 | 全 protocol CI build 1 | 0 |
| 修理前の帰属対照 | X では 0 | D2 の Y0/Y1、T0/T0p、ASan を再使用 |

この核は **22 build、最低 59 走行**（M1 が 1 回で成立する場合）。裁定の「4 組合せの結果」に未取得の組合せがあれば、その記録に必要な ASan build・走行を加える（`s4-ruling.md:14,36`）。現行の default/promotion ×修理前後を一律各 2 回とする 8 走行は、既取得結果を差し引いて数える（`launch_promo_confirm.py:334–360`）。残り予算は概ね **6,150～6,550 秒**だが、X の見積り 0.8～1.3 node 時間には build cache 等が含まれないため、投入前に実数で再計算する（`confirm/README.md:5–10`）。

## 所見 — 削ってはいけないもの

- **must-fix｜修理後 YCSB の 8 genome × K/W/R/P。** 削ると、指定空間の小走行と巡回 0（上限 indeterminate）を言えない（`s4-ruling.md:36,38`）。各 trace build の判定を残す。
- **must-fix｜修理後 TPC-C の 8 genome × M/R2 と代表 genome の各 3 回完走。** 削ると異常終了の解消範囲または反復完走を言えない（`md_32.txt:20`、`s4-ruling.md:36`）。F4 採否後の tip で行う。
- **must-fix｜同設定の修理前対照と D2 の witness・event 帰属。** 削ると F1 の原因帰属と修理前後の対が言えない（`s4-ruling-addendum-1.md:20–24`）。D2 を再使用できる条件を明記する。
- **must-fix｜修理前後 ASan と M2。** 削ると報告された abort／`writeSetClean` UAF の消失、または F3 単独の検出感度を言えない（`s4-ruling.md:36,47`）。対象 genome・回数・frame を残す。
- **must-fix｜M1 の witness 辺との照合、M3 の `update_skip > 0`。** 前者を削ると壊し正例の帰属が、後者を削ると F2 対象経路の感度が言えない（`s4-ruling.md:46,48`）。M3 を単なる省略可能項目にしない。
- **must-fix｜上流 format・全 protocol build と R5 の D297 2 面。** 削ると D2277 または D297 の完了判定を満たさない（`md_32.txt:10,22`、`s4-ruling.md:34,36`）。最終 tip で各 1 回残す。

## 所見 — 修理差分の過剰

- **nit｜F1 は裁定の条件追加に沿う。** `fix1-promotion-ronly.patch:7–20` のコメント移動と `later_ver` の未使用指定は条件を外へ移したことに伴う整理で、別経路の変更は見えない。放置しても成果物の動作は変わらない。追加削減は不要。
- **should｜F2 の目印設定は再探索を省ける。** `fix2-promotion-update-body.patch:19–24` は `update()` の直後に `searchWriteSet()` をもう一度呼ぶ。放置すると promotion ごとに余分な探索が入る。`update()` が作った要素を直接受け取れる最小の局所手段があるかを確認し、なければ現行のままにする。`from_promotion_` を OPT・PROMO の内側に置き、既存 write の二重 update を変えない点は R2 に合う（同 patch:9–11,35–42、`s4-ruling.md:31`）。
- **should｜F3 の `std::vector` は必要性を説明する。** `fix3-abort-insert-uaf.patch:9–19` は全 genome の abort に空 vector を作る。放置すると既定経路にも追加のオブジェクト生成が入る。`writeSetClean()` 後に `write_set_` から INSERT pointer を安全に再走査できるなら退避を省く。clean が集合を消すなら vector は順序修理に必要であり、その根拠を記録する。索引除去→clean→delete 自体は R3 どおり（`s4-ruling.md:32`）。

## 所見 — 壊し patch と job の過剰

- **should｜壊し patch の発火診断は先例の書式内。** event の tx・key・版と `FIRED` の 3 計数は R8 と既存 4 本の書式に一致する（`broken-cicada-promotion-ronly-stale-recheck.patch:8–35,44–57`、`patches/README.md:980–984,1007–1008`）。放置しても過剰な台帳は増えない。追加の計数・gate は要らない。
- **must-fix｜job は M1 の検出と帰属を合格条件にしていない。** `launch_promo_confirm.py:258–285,319–321,455–457` は一致数を記録するが、0 件でも `observed` になり得る。さらに key が witness のどれかの辺にあるだけでは、その event tx が当該辺の端点か確かめられない。放置すると壊し正例が検出されなくても完了扱いになる。少なくとも non-serializable、event commit tx、同じ巡回辺の key・tx の一致を受理条件にする（`s4-ruling.md:37,46`）。
- **must-fix｜M2 と M3 も期待結果を合格条件にしていない。** M2 は ASan 件数・frame を記録するだけ、M3 は patch 適用失敗時に `skipped` として続行し、計数の正値も判定しない（`launch_promo_confirm.py:338–346,361–366,455–457`）。放置すると M2 の UAF 再現と M3 の感度 pin が欠けた成果物を成功扱いする。M2 の指定 frame と M3 の `update_skip > 0` を評価し、patch 不適用は未達として報告する（`s4-ruling.md:47–50`）。
- **nit｜記録量を絞る余地がある。** 全 verifier Python の SHA、全 `*cicada*.patch` の適用表、全 run の stdout/stderr SHA は、指定された CI・D297・計装 2 本の適用確認や M1〜M3 の判定には使われていない（`launch_promo_confirm.py:136–140,232–233,410–416`）。放置すると結果 JSON と確認作業だけが増える。必須の tip・patch・設定の束縛と必要な生ログを残し、適用検査は裁定の計装 2 本に絞る（`s4-ruling.md:36`）。

## 所見 — F4 を足すときの最小追加

- **must-fix｜F4 の採否を D2 の T0/T0p と T4/T4p/T5 で先に決める。** 追補 1 は promotion 無効の OPT=1 対照を明示している（`s4-ruling-addendum-1.md:16,22–25`）。放置すると F1～F3 の tip で TPC-C が `bad_alloc` のままでも、確認 job が想定外失敗として終わる（`confirm/README.md:12`）。採用時は F4 を別差分として tip と同一性確認に加え、最終 tip の TPC-C 8 genome を再 build・実走する。
- **should｜X に足す独立対照は OPT=1・PROMO=0 の TPC-C 代表 build 1 本、M/R2 各 1 走行で足りる。** 修理前 T0p と F4 単独 T4p の M/R2 反復は D2 が予定している（`diag/launch_promo_diag.py:441–446`、`s4-ruling-addendum-1.md:23`）。放置すると最終 tip でも F4 が promotion と独立に効くか言えない。D2 と同設定で最終 tip の PROMO=0 を 1 組加え、既定 OPT=0 の分岐を変えない F4 差分も確認する。

## 総括

現行 job の 42 build・86 走行には、土台全 8 genome の再走と、走らせない YCSB build が含まれる。D2 の同一条件の対照を再使用すれば、核は 22 build・最低 59 走行まで絞れる。一方、現行 job は M1〜M3 の期待結果を成功条件に結び付けていない。削減と同時にこの判定を直し、F4 の裁定後の最終 tip で確認する必要がある。