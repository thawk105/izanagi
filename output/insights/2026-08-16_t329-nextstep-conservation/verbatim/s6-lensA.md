## 総括

段 6 レンズ A の結論は、**このままの land は非推奨**です。read-only 静的レビューと補助 probe の結果、次の 3 点が real です。

- `phase3` の直後から MMDD を外すだけで、採番範囲を主張する破損 archive を `unnumbered` に落とし、新しい filename・README・archive 内 carry 検査をすべて迂回できます。
- 実 corpus に、番号付き archive 内なのに `fullmatch` から漏れる末尾注記付き carry が 3 件あります。
- MU-8 は事前登録された正例テストを落としません。変異は過剰拒否ではなく `unnumbered` 化による検査蒸発になります。

pytest は未実走です。「緑」とは判定していません。補助 probe は実装 helper を直接呼んだ read-only 実行です。

## 所見

### A-1 — real: `unnumbered` 分類で新 gate 全体を迂回できる

具体例を次の形で構成できます。

- filename: `worklog-phase3-106-110.md`
- README: `(106)〜(110)` を主張
- 本文: entry `{106,107}` のみ

処理は次のとおりです。

1. `phase3` は通ります。
2. 第 2 token `106` は MMDD でないため、即座に `unnumbered` になります。
3. `numbered_archive_entries` に登録されません。
4. filename 範囲照合、README 範囲照合、archive 内 carry 収集、全域番号 universe への本文番号追加がすべて止まります。
5. README の既存到達性検査はファイル名が掲載され実在すれば通るため、`(106)〜(110)` という主張自体は検査されません。

補助 probe でも、正規名は `numbered (106,110)`、上記名と `worklog-phaseX-0802-106-110.md` はともに `unnumbered` でした。

根拠: `tools/check_docs.py:1292`, `tools/check_docs.py:1299`, `tools/check_docs.py:1301`, `tools/check_docs.py:1974`, `tools/check_docs.py:2013`, `tools/check_docs.py:2059`, `tools/check_docs.py:1454`

成果物影響: 破損 archive が受理集合へ入り、欠落 entry とその裁定・台帳内容が正規参照から失われたまま certified 作業の根拠に使われ得ます。

### A-2 — refuted（land bypass として）: 入力不完全時の検査停止は作れるが fail-closed

`archive_scan_complete == False` では README 検査が無条件 return し、finding は 0 件です。補助 probe でも確認しました。

また、archive を 1 件 symlink、invalid UTF-8、非 regular file などにすれば `archive_blocked` が立ちます。これは採番 archive に限らず、**読取不能な unnumbered archive 1 件でも** `numbered_archive_input_complete == False` にします。その場合、全 dangling carry の個別診断が止まり、「入力が不完全」1 件だけになります。

ただし、読取不能を作った箇所では placeholder prepass と backlog guard が先に finding を追加し、`_validate_entry_universe()` 自身も停止 finding を追加します。したがって rc=0 への迂回にはなりません。

根拠: `tools/check_docs.py:1446`, `tools/check_docs.py:1697`, `tools/check_docs.py:1706`, `tools/check_docs.py:1951`, `tools/check_docs.py:1956`, `tools/check_docs.py:1958`, `tools/check_docs.py:1400`

成果物影響: 受理集合は広がりませんが、checker レポートから README 不一致と全 dangling carry の場所・件数が消え、修復範囲が「入力不完全」1 件へ縮退します。受理影響がない部分は nit です。

### A-3 — refuted: F79 の正規 filename 形では 3 経路すべて発火する

`worklog-phase3-0802-106-110.md`、README `(106)〜(110)`、実体 `{106,107}` を helper に与えた結果は次のとおりです。

- filename: `numbered (106,110)` になり、`欠番=108〜110`。
- README: 同じく `欠番=108〜110`。
- carry: `(110)` が universe にないため宙吊り finding。

処理経路は、filename 分類 → 本文番号集合 `{106,107}` → filename 照合 → backlog result → README 照合 → universe/carry 照合です。

根拠: `tools/check_docs.py:1304`, `tools/check_docs.py:1320`, `tools/check_docs.py:2009`, `tools/check_docs.py:2016`, `tools/check_docs.py:2126`, `tools/check_docs.py:1462`, `tools/check_docs.py:1477`, `tools/check_docs.py:1406`

成果物影響: 正規名と対象 carry 書式を保った F79 再現は受理集合から除外され、欠落した `(108)〜(110)` を台帳へ固定する再発を防ぎます。

### A-4 — refuted: `_entry_number_from_title()` と現行 worklog の assert は通常入力から到達不能

`_entry_number_from_title()` は不一致時に未捕捉の `ValueError` を投げます。しかし呼出し前に `_extract_archive_entries()` が同じ regex の `fullmatch` を全 title に適用し、不一致があれば finding を追加して `None` を返します。

現行 worklog の `assert match is not None` も、同じ regex で事前検証した `_extract_current_entries()` の戻り値だけに適用されます。通常の異常 Markdown 入力から例外へ到達する経路は確認できません。

内部契約が将来破られた場合は traceback を伴う非 0 終了になり、finding ではありませんが fail-closed です。

根拠: `tools/check_docs.py:997`, `tools/check_docs.py:1003`, `tools/check_docs.py:1032`, `tools/check_docs.py:1041`, `tools/check_docs.py:1326`, `tools/check_docs.py:1895`, `tools/check_docs.py:5408`

成果物影響: 現行受理集合への影響はありません。内部契約違反時に構造化レポートが失われる点だけが nit です。

### A-5 — real: 実 corpus の carry 4 件が `fullmatch` から漏れる

grep による件数は次のとおりです。

| 書式 | `docs/worklog.md` | archive |
|---|---:|---:|
| 新書式の完全一致 | 2,051 | 167,873 |
| 旧書式の完全一致 | 0 | 31,931 |
| 合計 | 2,051 | 199,804 |

完全一致の総数は **201,855** で、プラン記載の 201,856 より 1 件少ないです。広い末尾検索で増える 1 件は `worklog-phase3-0811-399.md:3` の説明文中 `[T-673] (3)` であり、carry の完全一致ではありません。

さらに `((N) 参照)` を含む carry-like 行は archive に 31,935 件あり、次の 4 件が末尾注記のため完全一致しません。

- `docs/archive/worklog-phase3-0721-0722.md:989`
- `docs/archive/worklog-phase3-0801-81-82.md:103`
- `docs/archive/worklog-phase3-0801-91-92.md:278`
- `docs/archive/worklog-phase3-0802-106-110.md:701`

最初の 1 件は unnumbered archive ですが、残り 3 件は numbered archive です。参照先 `(73)`, `(91)`, `(106)` は現在実在するため現状は赤になりませんが、将来消失してもこれら 3 件は gate に拾われません。

根拠: `tools/check_docs.py:780`, `tools/check_docs.py:783`, `tools/check_docs.py:1280`, `tools/check_docs.py:2059`

成果物影響: 対象 entry が消失した際、少なくとも 3 件の numbered archive carry が受理されたままになり、台帳上の継続項目が到達不能でもレポートに現れません。

### A-6 — refuted（受理漏れとして）: 参照先ごとの 1 件保持は診断だけを縮退させる

`setdefault()` により同じ番号を指す carry は最初の 1 件だけ保持されます。しかし「参照先番号が universe に存在するか」という述語は同一 target の全 carry で同じため、1 件だけでも拒否判定は変わりません。

F79 のように同じ `(110)` を数百件が指す場合、checker は最初の task/path しか報告せず、被害件数を表現できません。

根拠: `tools/check_docs.py:1285`, `tools/check_docs.py:1406`, `/home/SFC/tanab/.claude/jobs/6a7dec0f/tmp/t329/adjudication-plan-v2.md:36`

成果物影響: 受理集合は変わりませんが、checker レポートが affected task/path の全量を失い、修復時の台帳監査範囲を過小表示します。これは nit です。

## MU-1〜MU-9 静的照合

| 変異 | 判定 | 落ちる新規テスト／注意 |
|---|---|---|
| MU-1 | real: 落ちる | 新書式側の `test_backlog_guard_dangling_carry_reference_is_violation`。他の finding はありません。`test_check_docs.py:9083`, `:9090` |
| MU-2 | real: 落ちる | 旧書式側の同テスト。新旧 regex は独立です。`test_check_docs.py:9083`, `:9090` |
| MU-3 | real: 落ちる | `test_backlog_guard_carry_reference_existing_in_current_is_clean` の両書式。現行 `(1)` を universe から落とすと正例が宙吊りになります。`test_check_docs.py:9068`, `:9070`, `:9076` |
| MU-4 | real: 落ちる | `test_backlog_guard_numbered_archive_entry_is_carry_target`。archive `(1000)` を universe から落とすと正例が赤になります。`test_check_docs.py:9096`, `:9099`, `:9105`, `:9108` |
| MU-5 | real: 両層同時なら落ちる | 内部欠番 fixture `{10,12}` に対する `test_archive_filename_and_readme_reject_interior_gap`。片層だけなら他層が先取りして gate は赤のままなので、事前登録どおり両層同時が必要です。`test_check_docs.py:9192`, `:9195`, `:9205` |
| MU-6 | realだが一部先取り | `missing` parameter は postcondition を外すと clean になり、真の kill です。`bare` parameter は抽出不能 finding が残り、テストは診断文字列欠落で落ちるだけです。bare は独立した受理集合 kill に数えられません。`test_check_docs.py:9236`, `:9242`, `:9247`, `:9250`; `tools/check_docs.py:1465`, `:1484` |
| MU-7 | real: 落ちる | malformed を unnumbered にすると `test_archive_malformed_filename_is_violation` は他の finding なく通過します。`test_check_docs.py:9255`, `:9258`, `:9267` |
| MU-8 | **real: 落ちない** | `test_archive_claims_accept_single_and_cross_date_ranges` の `1001` と `1003` は MMDD と解釈され、entry token が 0 件となって `unnumbered` 化します。過剰拒否にはならず正例は clean のままです。`1000` は厳密 MMDD ではないため現実装型の変異では entry のままです。「4 桁すべて日付」の変異ならこちらも unnumbered になり、やはり clean です。`test_check_docs.py:9162`, `:9163`, `:9187`; `tools/check_docs.py:1306`, `:1318` |
| MU-9 | real: 落ちる | `(続き)` 以外の実体集合は filename/README と一致しているため、番号なし H2 finding を消すと `test_numbered_archive_rejects_entry_without_global_number` が clean になります。`test_check_docs.py:9272`, `:9281`, `:9288`; `tools/check_docs.py:2022` |

MU-8 は変異表の期待と実テストの決定的な不一致です。MU-6 の bare parameter は別 finding が先取りしており、DW-M03 上の独立 kill 証拠にはできません。