## 所見

指定射影の静的レビュー。pytest・変異 harness・JUnit round-trip は未実測。以下では `G`＝`tools/update_acceptance_duration_ledger.py`、`T`＝`orchestrator/tests/test_update_acceptance_duration_ledger.py` と略記する。

1. **parametrize id の区切り文字 — refuted／一部未実測、nit。**
   根拠：`T:760`、`G:50`、`G:171`、`G:198`。
   - (a) 提示された `_canonical_item` の `nodeid.partition("::")` という処理なら、最初の区切りで module と残りを分けるため、parameter 内の `/`・`::` は module に混入しない。ただし `_canonical_item` 本体は指定された閲覧範囲外であり、その前後処理は未確認。
   - (b) `_module_join` は module を `classname` から決め、`name` は分割せず連結する。今回の parameter には `@` がなく、末尾は `]` なので `_strip_group_suffix` も壊さない。外側に付いた `@group` は除去される。
   - (c) `FAILED <nodeid>` の**完全な文字列を抽出して比較するなら**問題ない。ただし harness 本体は射影に含まれず、区切り文字で切り詰めないことは未実測。M2/M5 の期待 node は parameter 部分まで必要。
   - (d) `/`・`::` は XML 属性値として問題なく、提示された writer は `name` をそのまま属性へ渡す（`T:66`）。実際の pytest JUnit writer による round-trip は未実測。

   防御的な簡素化として、`ids=lambda prefix: Path(prefix.removesuffix("::")).stem` を付ける案は妥当。ただし現時点で誤解釈を実証した修正ではない。
   **放置時の成果物影響：確認した生成器経路では値・割付・受理集合は変わらない。harness が切り詰める場合の変異帰属だけが未確認。**

2. **M6 が等価になる懸念 — refuted、nit（修正不要）。**
   根拠：`T:826`、`T:843`、`G:466`、`G:477`、`G:492`。
   fixture の凍結 map は `sort_swo_oracle → critic` の順。その順が `frozen` に残り、結果は `sort_swo_oracle → critic → pkg/test_a → pkg/test_z` となる。`sort_keys=False` では期待する `critic → sort_swo_oracle → …` と一致しない。さらにトップレベルも挿入順が canonical 順と異なる。M6 は静的に非等価で、`T:846` が赤になる見込み。
   **放置時の成果物影響：現行実装には問題なし。M6 を入れると JSON bytes・hash は変わるが、値・割付・受理集合は変わらない。**

3. **複数 assert と変異の単一理由性 — real、nit。**
   根拠：`T:748`、`T:754`、`T:787`、`T:791`、`T:811`、`T:814`、`T:963`、`T:968`。
   map・件数・stdout、または数値・bytes を同時に検査しており、同じ test が複数の不具合を検出する構造である。ただし、それだけでは DW-M01 の単一理由性違反ではない。
   - M1 の指定 test はまず `T:811` の map 不一致で失敗する。stdout 件数の相違に依存しない。
   - M2/M5 はまず `T:787` の凍結値不一致で失敗する。bytes assert より先である。
   - M3/M4 は `T:748` で、それぞれ余分な旧名／異なる値として区別できる。
   - M6 のトップレベル順・内側順の二つの差は、同じ sort 無効化の帰結である。

   親の変異実測では、expected node 一致に加えて**最初に失敗した assert と差分内容**を記録すること。M2 は共通 key に限定し、M5 は `Decimal` を渡す正しい変異にして、`KeyError`・型不整合による別理由の赤を避ける。
   **放置時の成果物影響：現行台帳・割付・受理集合は変わらないが、赤の件数だけでは変異検出の帰属を過大評価しうる。**

4. **`excluded_frozen_suite` の意味が mode 間で異なる — real、nit。**
   根拠：`G:437`、`G:483`、`G:95`、`G:457`、`T:814`、`T:968`。
   refresh は「failed/error 除外後の generated map のうち凍結 prefix に一致する全件」。add-only は既存登録済み・writer base・removed を先に別分類し、その残りの凍結件数である。したがって add-only 側も、厳密には単なる「未登録かつ凍結の全件」ではない。

   help/docstring は除外順を説明しているが、この mode 間の差までは明記しない。test は removed/writer を含めた `13` と failed/error を除いた `1` を固定する一方、既存凍結と JUnit の共通 key が除外件数に入る点を直接 assert していない（`T:793` は保持件数のみ）。refresh 側だけ `excluded_frozen_junit_nodes` 等へ改名し、分母と既存登録の有無に依存しないことを説明すると明確になる。
   **放置時の成果物影響：値・割付・受理集合は不変。stdout の mode 横断比較で除外件数を誤読する余地が残る。**

5. **coverage test の出力消費 — refuted、nit（修正不要）。**
   根拠：`T:933`、`T:935`、`T:936`、`T:938`、`T:940`、`G:598`。
   1 回目の `readouterr()` が最初の `--check` 出力を消費し、最後の count は書込み走と一致確認走の二つを対象にする。意図と実装は一致する。現 fixture の M9 は `1/3` を `2/3` に変えるため、最初の `T:935` で検出される。
   合算 assert だけなら「片方が二重出力、他方が無出力」を区別しないが、M9 の検出を損なうものではない。
   **放置時の成果物影響：値・割付・受理集合は変わらない。二走それぞれの出力回数を独立には保証しない。**

6. **`@real-repo` entry が今後も当たらない、という説明 — refuted／実際の未使用理由は未実測、nit。**
   根拠：`G:50`、`G:198`、`T:341`、`T:348`、`T:357`、`tools/acceptance_shards.py:397`、`refs/parent-verify-after.txt:4`、`refs/parent-measurements-v2-before.md:2`。
   4 走すべてで `group_fallback_hits=0` は確認できる。しかし「producer が suffix を剥がすため canonical lookup が成功する」という説明は、この entry には成立しない。**その canonical base key 自体が removed として不在を pin され、親検算も不在を確認している。**

   `record.nodeid == base` かつ `record.group == "real-repo"` なら、第 1 lookup は miss し、第 2 lookup が保存された `0.19` を取得する。producer の suffix 除去は consumer の第 2 lookup を無効にしない。

   記録には「before 4 走で group fallback の利用は観測されなかった。将来も利用されないとは未確認」と書くべきで、恒久的な死蔵 entry と断定しない。D1152 の凍結 entry の変更は提案しない。
   **放置時の成果物影響：記述だけなら成果物は不変。誤って削除すると、該当 record が現れた場合の重みが `0.19 → 1.0` となり割付が変わりうる。**

## test と変異の対応表

表の test 名はすべて `T` 内の `test_refresh_` 接頭辞を省略。検出結果は静的予測であり、変異実測は未実測。

| test（行） | 検出する M1〜M9 |
|---|---|
| `replaces_nonfrozen_entries_and_removes_old_names`（734） | M3：両 parameter。M4：`[9.9]` のみ |
| `preserves_frozen_entry_bytes_and_values`（761） | M1・M2・M4・M5：8 parameter とも |
| `excludes_all_frozen_junit_nodes`（796） | M1 |
| `frozen_prefixes_cover_removed_nodes_and_writer_base_key`（817） | なし。定数間の包含関係を検査 |
| `renders_canonical_bytes`（824） | M5・M6 |
| `canonicalizes_noncanonical_frozen_number_spelling`（852） | M5 |
| `and_add_only_are_mutually_exclusive`（866） | M7 |
| `requires_existing_ledger`（881） | M8 |
| `rejects_invalid_existing_ledger_without_writing`（896） | なし。既存台帳不正の拒否を検査 |
| `check_and_coverage_use_refreshed_nodeids`（917） | M1・M9 |
| `drops_failed_and_error_nonfrozen_entries`（943） | M1・M3・M5 |
| `rejects_unusable_junit_without_writing`（975） | なし。JUnit 不正の拒否と非書込みを検査 |

M8 は事前登録どおり「不在だけを空 map にする」変異を前提とする。不正台帳まで握り潰す変異なら、896 の test も赤になるが、別の変更範囲である。

| 変異 | 実装 anchor | 事前登録に対応する赤 node／最初の失敗箇所 |
|---|---|---|
| M0 | `G:457` docstring | なし。等価、SURVIVED 期待 |
| M1 | `G:475` の除外条件 | `excludes_all_frozen_junit_nodes` → `T:811` |
| M2 | `G:466` の凍結 map 作成後、共通 key の値だけ上書き | `preserves_frozen_entry_bytes_and_values[<prefix>]` → `T:787` |
| M3 | `G:477` の `frozen` を既存全 map に置換 | `replaces_nonfrozen_entries_and_removes_old_names[9.9]`、`[0.5]` → `T:748` |
| M4 | `G:473` の採用値を共通 key では旧値に変更 | 同 test の `[9.9]` → `T:748` |
| M5 | `G:467` の凍結値を再量子化 | `preserves_frozen_entry_bytes_and_values[<prefix>]` → `T:787` |
| M6 | **`G:492`** の `sort_keys` | `renders_canonical_bytes` → `T:846` |
| M7 | `G:82` の排他 group と option 登録 | `and_add_only_are_mutually_exclusive` → `T:873`、期待した例外が出ない |
| M8 | `G:549` の不在時処理 | `requires_existing_ledger` → `T:886` |
| M9 | `G:555` に渡す集合を変更 | `check_and_coverage_use_refreshed_nodeids` → `T:935` |

M6 は共通生成処理の `G:286` ではなく、refresh 描画の `G:492` を変異させる必要がある。前者だけを変えると最終 refresh が再 sort するため、意図した変異にならない。

M1〜M9 に、静的に検出先のない変異はない。M4 の `[0.5]` は入力値と旧値が同じなのでその case に限って等価だが、`[9.9]` が検出する。

817・896・975 の test は**この変異集合に対して追加の kill を持たない**。ただし、それぞれ包含関係、不正既存台帳、不正 JUnit という別契約を検査しており、削除可能な冗長 test とは断定しない。また、同じ変異を検出する test 同士も、number spelling や sibling module 境界など、M1〜M9 が表現していない契約を持つ。

## consumer 波及の判定

- **実際の割付は変わりうる。** `tools/acceptance_shards.py:397` で新しい値を取り、`:406` で component の数値和、`:434` で LPT 順序、`:438` で投入先に反映する。台帳更新は割付・予測負荷を変えるが、このコードには値によって node を受理集合から除外する処理はない。

- **指定された consumer test は合成 record を使う。** `test_run_tests_shards.py:65` の `test_a.py`〜`test_d.py`、`:764` の `test_e.py` は fixture 用 nodeid。未登録ならすべて `1.0` fallback となり、実在 test の値更新には依存しない。ただし `:757` の `baseline.loads == node 数` は、明確にその未登録状態へ依存する assert である。「実台帳に依存する assert がない」とは言えない。射影に台帳本体が含まれないため、合成 key の実台帳不在の直接照合は未実測。

- **`:84` の helper は引数に依存する。** 引数省略時は上記合成 record。`records` を渡した場合はその集合で割付するため、指定範囲だけから全呼出し元まで無影響とは断定しない。`:744` と `:766` の明示的な呼出しについては、合成 key が未登録である限り結果は不変。

- **loader の上限・schema には抵触しない。** `conftest.py:1004` の上限は 16 MiB で、提示された約 3.0 MB は十分小さい。`G:485` は schema 1、seconds、map 件数を維持し、`conftest.py:1520` の検査に適合する。親検算の `refs/parent-verify-after.txt:7`・`:11`・`:16` も件数・値の由来・canonical bytes の一致を報告している。値更新そのものは schema 拒否の理由にならない。

## 総括

**GO（静的レビューとして）。must-fix：0 件。**

M1〜M9 はすべて検出先を持ち、M6・M9 の fixture は意図した差を作る。残る nit は stdout 名称、変異の失敗箇所の記録、parameter id の簡素化、および `@real-repo` の未使用理由を断定しないこと。

変異 harness の完全一致抽出、実際の JUnit round-trip、consumer 焦点走・受入走は未実測であり、この GO はそれらの成功を主張しない。