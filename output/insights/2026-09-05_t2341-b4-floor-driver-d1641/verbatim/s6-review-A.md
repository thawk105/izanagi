## blocker

[実測] なし。

## must-fix

### 所見 1 — role-aware 完備性が median を検査せず、有限 rep から非有限 median を作る

- (a) [実測] `_measurement_payload_complete` は各 rep の有限性と role 条件だけを確認し、plan v2 3 が要求する median の有限非負または有限正を確認しません。さらに偶数個の median を `(low + high) / 2` で計算するため、`[1e308, 1e308]` は両 rep が有限でも median が `inf` になります。読取専用診断でも `_median([1e308, 1e308]) == inf` を確認しました。
- (b) [実測] `orchestrator/campaign/floor_pair_driver.py:1628-1674`、`:2411-2417`、`:2561-2569`、`:2644-2653`。既存境界 test は `orchestrator/tests/test_floor_pair_driver.py:2217-2297` ですが、大値 median は未観測です。
- (c) [実測] 放置すると、本来 complete にできる標本を含む window が terminal `complete` のまま記録された後、finalize だけが `not_generated_missing_samples` になり、床値と受理集合が消えます。
- (d) [推測] 偶数 median をオーバーフローしない式で計算し、`_measurement_payload_complete` でも median を生成して candidate は `_finite_nonnegative`、reference は `_finite_positive` で検査してください。全 role が `(1e308, 1e308)` の正例を追加すべきです。
- (e) [実測] plan v2 3、5、6、8、12(j)(k)。M16/M17 は 0 の境界だけで、この median 経路に直接対応する事前登録変異はありません。

### 所見 2 — exact int の一部で status 導出が total でなく、未処理 `OverflowError` になる

- (a) [実測] exact `int` は型検査を通りますが、`float(value)` が無防護です。`10**400` では `_finite_nonnegative` と `_throughput_protocol_violation` の双方が `OverflowError` になりました。run 側では session record と terminal を閉じる前、finalize 側では `FloorPairBindingError` や summary status に変換する前に例外が漏れます。
- (b) [実測] `orchestrator/campaign/floor_pair_driver.py:1328-1334`、`:1592-1603`、`:1630-1635`、`:1841-1854`、`:2190-2198`。
- (c) [実測] 放置すると、該当 payload で raw artifact が途中まで残るか summary が発行されず、床値は生成されず受理集合から campaign 全体が消えます。
- (d) [推測] float 変換を共通 helper で total 化し、変換不能な正の巨大 int は少なくとも `measure_incomplete`、負の巨大 int は符号を変換前に検出して `protocol_violation` としてください。run と artifact 再導出の対称 test が必要です。
- (e) [実測] plan v2 3、5。M1〜M20 にこの exact-int 境界を直接観測する変異はありません。

## nit

[実測] なし。

## 必須検査結果

### 1. 値依存除外

[実測] drop 集合は固定された `DROPPABLE_STATUSES` だけから作られます。集合は probe competing/indeterminate、`measure_failed`、`measure_incomplete` の6種で、binary、window、protocol は含みません。`_dropped_sample_keys` も status membership しか参照せず、D、median、順位、有限正値の大小を参照しません。現物は `floor_pair_driver.py:102-114`、`:2445-2452` です。

[実測] payload からの状態導出は次の順です。

- pre probe competing/indeterminateは droppable。
- 負値または reference 0 は `protocol_violation`。
- post probe competing/indeterminateは droppable。
- 測定結果なし、空 throughputs、測定例外は `measure_failed`。
- rep数、型、有限性、returncode、observation、timestamp の不完備は `measure_incomplete`。
- 完備なら `complete`。

[実測] 対応箇所は `floor_pair_driver.py:1822-1902` と `:2142-2243` です。正の有限 throughput の大小、D、median、HMAC順位はこの分岐に入りません。ただし所見1のとおり、median 完備性そのものが未実装です。

[実測] 数値境界は次のとおりです。

|入力|`_finite_nonnegative`|candidate protocol|reference protocol|
|---|---|---|---|
|`0`、`0.0`、`-0.0`|受理|違反なし|0 として fatal|
|有限負値|拒否|fatal|fatal|
|`NaN`、`+inf`|拒否|ここでは違反なし。後段で incomplete|同左|
|`-inf`|拒否|負値として fatal|負値として fatal|
|`bool`|exact 型違反|ここでは無視。後段で incomplete|同左|
|通常範囲の `int` / `float`|role 条件内なら受理|有限非負なら完備候補|有限正なら完備候補|
|その他の型|exact 型違反|ここでは無視。後段で incomplete|同左|
|float 化不能な巨大 `int`|未処理 `OverflowError`|未処理 `OverflowError`|未処理 `OverflowError`|

### 2. status の再導出

[実測] `_audit_session_causality` は全 record について `_derived_record_status` を呼び、記録 status との exact 一致を要求します。complete record の status だけを `measure_incomplete` にした旧 mutation_07 は `FloorPairBindingError` になります。`floor_pair_driver.py:2255-2260`、`test_floor_pair_driver.py:1945-1963`。

[実測] 一方、probeの status、`competitors`、record status/error、後続 skip、terminal countまで整合して改変した artifact は防ぎません。`_probe_payload_status` は stdout/stderr から classifier を再実行しないためです。これは `NOT_PROVEN` の「成果物の削除・改名・改変を防がない」によって正しく限定されています。`floor_pair_driver.py:70`、`:2113-2139`。

### 3. 因果整合

[実測] `not_run_sample_dropped` は同一 sample の先行 droppable と、その `session_id` に一致する `dropped_by_session_id` が必須です。先行原因なしは拒否されます。`floor_pair_driver.py:2269-2279`。

[実測] `not_run_after_fail_closed` は先行 fatal が必須で、fatal 後の droppable、complete、別 fatal はすべて拒否されます。droppable が先にあり、後続 sample で fatal になる実 artifact は許されますが、terminal `incomplete` が優先されます。`:2263-2268`、`:2280-2281`。

[実測] HMAC 順は sample を並べた後、その sample 内の3 roleを並べる構造です。したがって第1 role失敗なら後続2 roleが skip、第2 role失敗なら先行1 roleが complete、後続1 roleが skipになります。auditor は plan 内の sample role 順で cause index を求め、この両形を検査します。`:1240-1267`、`:2287-2305`。第2 role失敗の summary test は `test_floor_pair_driver.py:2058-2104` です。

### 4. 5% 判定

[実測] 分母は windowごとに `sample_count × len(pair_ids)`、分子は unique sample keyです。`Fraction(dropped, planned) <= Fraction(1, 20)` なので、拒否条件は exact に `dropped * 20 > planned` と同値で、exact 5% は受理します。`floor_pair_driver.py:2464-2471`。

[実測] windowごとに独立判定し、全window合算はしません。fatal terminalによる `not_generated_missing_samples`、threshold超過、empty stratum の順で優先されます。`:2425-2426`、`:2630-2642`。59/2、59/3、40/2、177/8、177/9、2-window局所性、empty優先順の静的 node は `test_floor_pair_driver.py:1966-2055`、`:2107-2139` にあります。

### 5. fatal の維持

[実測] `binary_binding_failed`、`outside_window`、`protocol_violation` は `FATAL_STATUSES` のままで、発生後は全 session が `not_run_after_fail_closed`、terminal は `incomplete`、finalize は `not_generated_missing_samples` です。`floor_pair_driver.py:112-114`、`:1991-2044`、`:2425-2426`。

[実測] fatal 後に droppable recordを混ぜた改変 artifact は `fatal session 後に planned session が実行された` として拒否されます。`:2263-2266`。

### 6. regression 面

[実測] diff の全 hunkを確認し、要求された regression 面の緩和はありません。

- create-only: `floor_pair_driver.py:1501-1518`
- HEAD/blob/source三者束縛: `:511-550`、`:1099-1185`、`:1953-1961`
- 固定 probe argv: `:64`、`:1546-1559`
- upper 1以上の非丸め: `:2655-2662`
- live site/env: `:1482-1498`
- production adapter非差込: `:1937-1942`
- plan exact、session ID/count/order exact: `:1308-1316`、`:2359-2368`
- `measure_point`: `:1406-1424` は位置引数4個、既存 keyword集合のままです。

[実測] 変更ファイルは所有2 fileだけで、`git diff --check` と両ファイルの AST parse は成功しました。pytest は指定どおり未実走です。

### 7. NOT_PROVEN、docstring、status集合

[実測] plan v2 10 の新2文は module docstringと `NOT_PROVEN` に同一文字列で入っています。`floor_pair_driver.py:17-18`、`:74-75`。

[実測] `SESSION_STATUSES` には `protocol_violation` と `not_run_sample_dropped` が入り、`environment_mismatch` は入っていません。`:85-100`。対応 assert は `test_floor_pair_driver.py:454-466` です。

### 8. summary v2

[実測] `campaigns` は window/campaign、planned、dropped、既約 `Fraction`、threshold、admissible、stratum別 planned/dropped/retainedを持ちます。`floor_pair_driver.py:2455-2505`。

[実測] top-level の `dropped_sample_count` は unique sample数、`dropped_record_count` は該当 sample の全record数、`dropped` は指定7 fieldです。sample keyで全recordを選ぶため、失敗より前に完了した roleも含みます。`:2508-2526`、`:2663-2679`。第2 role失敗の正例は `test_floor_pair_driver.py:2058-2104` です。

## 変異観測 node

[実測] 静的には M1〜M20 の全てに観測 nodeがあります。主な対応は M1〜M2=`:554-572`、M3〜M5=`:1514-1569`、M6〜M8/M10/M11=`:1966-2033`、M9=`:2036-2055`、M12=`:2107-2125`、M13=`:1893-1926`、M14=`:1945-1963`、M15=`:2142-2175`、M16=`:2217-2241`、M17=`:2244-2297`、M18=`:1573-1627` と `:2300-2320`、M19=`:1842-1884`、M20=`:454-466` です。

[推測] pytest未実走のため、各 node が実際に変異を kill することまでは未確認です。

## 裁定パッケージ候補

[実測] この差分から新たに追加すべき scope 外裁定はありません。所見1、2はいずれも所有2 file内で修正可能です。

## 総括

- [実測] blocker: 0件。
- [実測] must-fix: 2件。
- [実測] nit: 0件。
- [実測] 緩んだ regression 面: なし。
- [実測] plan v2主要契約は median 完備性と数値変換の total 性を除き整合。
- [実測] M1〜M20で観測 nodeなしと判断した番号: なし。
- [実測] pytest: 未実走。
- [実測] 静的検査: AST parse成功、`git diff --check`成功。