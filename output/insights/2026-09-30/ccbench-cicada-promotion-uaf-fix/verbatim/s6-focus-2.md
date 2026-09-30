## 1 回目の partial の対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| M2 の呼出し順 | **closed** | 最初の UAF 報告で連続する frame 番号を読み、`writeSetClean` の次の frame が `abort` であることを要求する。実測も `#1` → `#2` の順。[判定コード](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/confirm/launch_promo_confirm.py:302) |
| ASan の回数・4 組合せ | **closed** | 土台／既定 1 回は UAF 1 件、tip／既定 1 回と tip／代表 promotion 2 回は各 0 件。土台／代表 promotion 1 回は diag-4 を同土台 SHA・genome・argv の対照として取り込む。[確認結果](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/evidence/confirm-tpcc-2/result.json)、[対照条件](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/confirm/launch_promo_confirm.py:405) |
| D2 対照の限定表現 | **closed** | 前回指摘した「同一実行物」という無限定な表現は確認 job の説明にない。土台 SHA・genome・argv の対応と、計装の違いを区別する必要は引き続きある。[README](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/confirm/README.md) |
| commit message 3 件 | **closed** | fix1 は「報告された代表 witness 52 件」に限定され、fix2 は観測された失敗行数の倍率に限定された。fix4 の「promotion 無効でも」は該当する失敗走行がある。各主張の実測範囲は下記のとおり。 |

## X3〜X5 の fix の検査

- `INLINE_VERSION_OPT` は CMake に `CCBENCH_INLINE_VERSION_OPT_CICADA` として渡し、compile 時は `INLINE_VERSION_OPT` マクロを照合している。確認結果は YCSB 10 build、TPC-C 16 build を記録しており、最初の `-D` 不一致による停止は解消した。[設定と照合](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/confirm/launch_promo_confirm.py:179)
- M3 の thread 接頭辞正規化は妥当。`confirm-tpcc-2` の原データから、逆適用版は `76,018 + 76,351 + 76,380 + 76,586 = 305,335`、tip は `4,549 + 4,547 + 4,614 + 4,596 = 18,306`。**305,335 > 5 × 18,306 = 91,530** なので、修正後の式では `reached`。保存済み結果の `0/0・not_reached` は修正前の集計であり、この走行を再判定した値ではない。[原データ](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/evidence/confirm-tpcc-2/result.json)、[修正後の集計](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/confirm/launch_promo_confirm.py:269)
- [format-tip.log](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/format-tip.log) には tip `16ad3eb8…`、checker SHA-256 `61e2df…`、213 file、login／`:latest` image の両方で rc=0、clang-format 14.0.0／14.0.6 が記録されている。ログ自体の SHA-256 も報告値 `cfa32f…` と一致する。**このログを根拠とする「format を通した」は支持されるが、確認 job の合格条件としては partial。** `--format-evidence` はファイルの存在を要求して要約を保存するだけで、tip・checker hash・件数・rc を検証せず、CI の合否にも含めない。任意の既存ファイルでも format 条件を通過し得る。[証跡処理](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/confirm/launch_promo_confirm.py:108)、[CI 合否](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/confirm/launch_promo_confirm.py:578)。指定資料には checker 本体がないため、その SHA-256 と実体の一致までは検証していない。

## commit message の照合（再計算を含む）

| commit | 判定 |
|---|---|
| fix1 | D2 の Y0 は K/R 各 2 回で巡回 **7・5・372・379**、報告 witness は **7＋5＋20＋20＝52**。52 件すべてで event tx・key の照合欄が成立し、Y1 の同じ 4 走行は巡回 0。「all 52 representative witnesses」は原データの報告上限内を正しく限定している。R の全 751 巡回を調べたという主張ではない。なお D2 全体の status は後続 ASan の flag 不一致による `identity-error`。[D2](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/evidence/diag-2/result.json) |
| fix2 | D4 の T5／promotion 無効 T4p の `insert order failed` 比は、M が **15.54・16.78 倍**、R2 が **21.18・22.19 倍**。修理相当 T6／T4p は **0.976・0.970・0.728・0.778 倍**。「about 16 to 22 times」「at or below that level」は丸めを含む観測表現として妥当。確認 job の M3 は別走行で **305,335／18,306 ≈ 16.68 倍**。[D4](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/evidence/diag-4/result.json)、[M3 原データ](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/evidence/confirm-tpcc-2/result.json) |
| fix3 | D4 の土台 ASan は UAF 1 件・rc=1。確認 job の fix3 逆適用 M2 も UAF 1 件で `writeSetClean` → `abort`、tip の ASan 3 走行は 0 件。message の解放順の説明と矛盾しない。[M2 と ASan 行列](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/evidence/confirm-tpcc-2/result.json) |
| fix4 | D4 の T0・T0p は M/R2 各 2 回とも SIGABRT。T0p は promotion 無効なので “also with promotion disabled” を支持する。修理相当 T4・T4p・T5 の同範囲は rc=0。`bad_alloc` の発生箇所や「最初の insert」という時点は指定された結果欄だけからは独立に確定できず、message のコード経路説明に依存する。[D4](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/evidence/diag-4/result.json) |

## 確認結果の恒真性

`fixed_tip_failures=[]` は恒真ではない。[`cell()`](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/confirm/launch_promo_confirm.py:391) は tip の trace、Release、ASan 走行について、非 0 rc、trace 判定不受理、ASan 報告を追加し、[最終判定](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/confirm/launch_promo_confirm.py:625) は 1 件でも fail にする。原データでも対象の **YCSB 32 走行、TPC-C 27 走行**について、非 0 rc・ASan 報告は 0、trace **32＋18 走行**の不受理も 0。一方、土台 TPC-C の SIGABRT、土台 ASan と M2 の UAF、土台／壊し YCSB の巡回は実際に記録され、tip 失敗欄には入っていない。

走行数は [条件表](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/confirm/README.md) どおり **YCSB 35、TPC-C 32、計 67**。YCSB の M1 は最初の R で成立して停止したため、許容範囲 35～38 の下限になった。build も **10＋16＝26**。M1・M2 はともに成立している。[YCSB 結果](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/evidence/confirm-ycsb-2/result.json)、[TPC-C 結果](/work/SFC/tanab/tmp/cicada-promotion-uaf-fix-2026-09-30/evidence/confirm-tpcc-2/result.json)

## 総括

修理後 tip の YCSB／TPC-C 確認結果に、恒真の 0 件判定や走行数不足は見つからない。M3 は保存済みの `not_reached` を原データに基づき **`reached` 相当**へ訂正して読む必要がある。残る実質的な限定は format で、ログは合格を記録しているが、確認 job はその内容を合否判定していない。指定資料に CI part の実走結果は含まれないため、CI 全体の合格は判定できない。