## 所見

以下の略記を使う。

- `G` = `tools/update_acceptance_duration_ledger.py`
- `T` = `orchestrator/tests/test_update_acceptance_duration_ledger.py`
- `L` = `orchestrator/tests/acceptance_duration_ledger.json`
- `V` = `/home/SFC/tanab/.claude/jobs/897c9a22/tmp/wave-t2236/refs/verify_after.py`

指定資料はすべて読取り済み。pytest・変異走・受入走は本レビューでは未実測。実台帳の canonical bytes、件数、8 suite identity、12値、removed 5件は、テストを呼び出さずデータとして独立照合した。

1. **refuted — 凍結 entry の欠落・上書き。must-fix なし。**
   根拠: `G:466` は既存 map の凍結部分を入力 JUnit と無関係に抽出し、`G:475` は JUnit 側の凍結部分を除外する。`G:477` の二つの map は key が非交差なので、凍結値は上書きされない。`T:780` は凍結 key の一部だけを JUnit に置き、`T:787` が不在分を含む凍結 map 全体を比較する。prefix は `G:21` の全8件が `.py::` まで含み、`T:768` の `_extra.py::` は一致しない。
   **成果物影響:** 現実装では凍結集合・値を保持し、兄弟 file の値は JUnit 値へ更新される。

2. **refuted — refresh による値の合成・再量子化。must-fix なし。**
   根拠: JUnit 値の量子化は `G:267`。refresh はその JSON を `G:463` で読み、`G:473` で値をそのまま採用する。凍結値も `G:467` で直接採用し、再量子化する呼出しはない。最後は `G:492` の canonical JSON 描画だけである。非 canonical な数値表記の変更は `T:852` が明示的に許容している。
   **成果物影響:** 凍結値は既存台帳由来、非凍結値は量子化済み JUnit 由来のまま保持される。

3. **real — 親検算の「all values」の行は、凍結値の出所を単独では検査しない。nit。**
   根拠: `V:19` の `fz` は検査対象の出力自身から作るため、`V:52` の `k in fz` は凍結 key について値にかかわらず真になる。また `V:37` の「12 values」は実際には5.89の1値だけで、直前の0.19と合わせても2値である。
   ただし全体では `V:18` の旧凍結行照合が値の保持を検査し、`V:51` は非凍結 map の完全一致を検査する。今回の426/426という親報告と、本レビューでの12/12値一致に反する所見ではない。`V:18` 自体は参照行数・一意性を assert しておらず、空の参照でもその行だけは真になる。
   **成果物影響:** 現在の検算一式を維持する限り変更なし。「all values」の行だけを独立した証明として再利用すると、凍結値の改変を見逃す。

4. **real — 凍結行の comma 検査は末尾 entry 配置を覆わない。nit。**
   根拠: `T:790` は必ず `,\n` を付けて比較する。現在は入力の最後が `pkg/...::test_after`（`T:775`）、出力でも `pkg/...` が凍結 `orchestrator/...` より後に並ぶため成立する。実台帳の最後も非凍結の `test_wave_land_window.py`（`L:24381`）であり、今回の検査が偽赤になる配置ではない。
   凍結 entry が最後になる fixture に同じ assertion を流用すると、正しい JSON でも偽赤になる。現在の凍結 map 等値検査 `T:787` があるので、comma の条件によって欠落・値変更が偽緑になるわけではない。
   **成果物影響:** 現台帳の値・集合・pin に影響なし。末尾配置の正常出力を将来テストが誤拒否する余地がある。

5. **refuted — D1152／F902 の正しさ境界を緩める変更。must-fix なし。**
   根拠: 提供差分は生成器の mode 追加、追加テスト、台帳更新の3 file。`G:21`、`G:31`、`G:40` の `_ADD_ONLY_FROZEN_*` は変更なし。既存 T-1574 の期待値・identity 検査（`T:321`、`T:364`）も変更なし。0.90閾値と consumer は変更対象にない。今回の refresh と、F902 の add-only 和集合合成を区別する契約は `ruling-v2.md` の段4裁定に明記されている。手編集なしはユーザー提示の作業事実と author 報告に基づく。
   **成果物影響:** 非凍結の所要値・登録集合は更新するが、凍結 pin と受理条件は緩めない。

6. **refuted — stdout 順序の不定性／既存 add-only stdout の変更。must-fix なし。**
   根拠: `G:478` の dict literal が順序を決め、途中で並べ替えず `G:596` で列挙する。Python の dict 挿入順により固定され、`T:754` と `T:968` が全文を pin する。既存 add-only の出力処理は差分で変更されておらず、`T:582` の既存全文 assertion も不変。なお `--help` の表示は option 追加によって変わるため、「全 CLI 呼出しの stdout 不変」とまでは言わない。
   **成果物影響:** 通常の add-only 結果と件数表示は不変。refresh の件数行は規定順で出力される。

7. **refuted — 指定した異常入力で書込みまで進む。must-fix なし。**
   根拠: 排他違反は `G:82` と `G:530` の解析時に拒否。重複・空・全失敗は `G:257`、`G:268` から例外となり、`G:538` より先へ進まない。既存台帳の不在・列挙された不正形は `G:338` の検証で拒否され、refresh 呼出し `G:549` に到達しない。coverage 検証も書込み前。`--check` は refresh 後の `rendered` を `G:559` で比較し、`G:565` の書込み分岐へ入らない。
   **成果物影響:** 指定異常入力は既存台帳を保持し、不在出力を作成しない。実際の負例走は未実測。

## fixture と実物の照合結果

| 対象 | 照合結果 |
|---|---|
| JSON の字下げ・ASCII・末尾 LF | `T:712` は `indent=2, ensure_ascii=True` と末尾LF。実台帳は独立再描画で `sort_keys=True` を含む canonical bytes と完全一致した。 |
| key の並び | fixture helper は意図的に `sort_keys` を指定しない。`T:826` の凍結 key を逆順にした入力は M6 用であり、出力期待値 `T:843` は sort 済み。入力全体が実台帳と同一順という主張はできないが、裁定どおりの検査である。 |
| entry 行 | `    "<nodeid>": <value>,` の空白・引用符・区切りが対応する。最後の entry は comma なし。上記所見4の制約がある。 |
| `.py::` | `_refresh_frozen_modules` は `::` だけを除いて `.py` を残す（`T:723`）。`_refresh_case` は file と test 名を `::` で分離する（`T:729`）。凍結 key に `.py::` 欠落なし。 |
| `@real-repo` | `T:767` の既存 key は `L:20599` の実 key と同形・同値0.19。JUnit 経由では `G:198` により suffix が除去されるので、既存 suffix 付き key を保持しつつ base key を追加しない構造になっている。 |
| removed 5件 | `G:33` の定数群と `T:328` の独立した既存 pin が文字列として対応する。`T:801` はその5件を JUnit fixture に入れる。実台帳との集合交差は独立照合で0件。 |
| `全` などの escape | removed 定数の `r"...\u5168..."` は生の「全」ではなく、文字としての backslash と `u5168`。`_refresh_case`／XML 往復でこれを Unicode decode せず、JSON 化時は `\\u5168` となる。実台帳でも同じ二重 escape の形を確認した（例 `L:4518`）。removed 自身は不在なので、その entry 行が実台帳にあるわけではない。 |
| 生の日本語 fixture | `T:831` の `日本語` は非凍結の追加 serializer case。pytest の escape 済み parameter ID の完全再現ではないが、凍結 fixture の文字不一致ではない。 |
| 実台帳 pin | データとして独立照合した結果、8 suite の件数＋SHA-256は全一致、12値は12/12一致、removedは0件、entry数24379。変更前426行との比較とJUnit全値の再照合は親報告に依存し、本レビューでは再実測していない。 |

## 変異 M0〜M9 の帰属表

node の共通接頭辞は `orchestrator/tests/test_update_acceptance_duration_ledger.py::`。以下は静的な赤予測であり、変異走はすべて未実測。

`P8` は次の8個の parameter ID をそれぞれ指す。

```text
[orchestrator/tests/test_critic.py::]
[orchestrator/tests/test_p3_exploration_namespace.py::]
[orchestrator/tests/test_p3_s4_loop_sort.py::]
[orchestrator/tests/test_real_repo_serialization.py::]
[orchestrator/tests/test_s1_direct_comparison.py::]
[orchestrator/tests/test_s8b_materialization.py::]
[orchestrator/tests/test_s8b_sort_swo_receipt.py::]
[orchestrator/tests/test_sort_swo_oracle.py::]
```

| 変異 | 変異位置・具体形 | 赤になる node／根拠 | 冗長 gate |
|---|---|---|---|
| M0 | `G:457` の docstring を同義に変更 | なし。等価で SURVIVED 期待。 | なし |
| M1 | `G:475` の prefix 除外条件を削除 | `test_refresh_excludes_all_frozen_junit_nodes`。13件が入り `T:811` の map 等値が赤。 | 新設の `test_refresh_preserves_frozen_entry_bytes_and_values`＋P8、coverage test等も赤。既存 add-only はこの関数を通らない。実台帳再生成を伴えば既存 T-1574 identity が**冗長 gate**となる。 |
| M2 | `G:467` を `generated_durations.get(nodeid, duration)` に変更し、共通 key だけ上書き | `test_refresh_preserves_frozen_entry_bytes_and_values`＋P8。JUnit に存在する凍結 key が5.89→9.9となり `T:787` で赤。欠落 key の KeyError に依存しない。 | コード変更だけでは既存 T-1574 は台帳を再生成しないため赤にならない。実台帳再生成後、12 pin のどれかが異値なら**冗長 gate**。実入力での帰属は未実測。 |
| M3 | `G:477` を `{**existing_durations, **new_nonfrozen}` に変更 | `test_refresh_replaces_nonfrozen_entries_and_removes_old_names[9.9]`、同`[0.5]`。旧名が残り `T:748` で赤。 | 新設 `test_refresh_drops_failed_and_error_nonfrozen_entries` も赤。既存 gate の直接検出なし。 |
| M4 | `G:473` を `existing_durations.get(nodeid, duration)` に変更 | `test_refresh_replaces_nonfrozen_entries_and_removes_old_names[9.9]`。旧0.5が残る。 | 同`[0.5]` は等値なので生存するが、変異全体は非等価。兄弟値0.7→0.25を要求する保持test＋P8も赤。既存 gate の直接検出なし。 |
| M5 | `G:467` を `_quantize_seconds(Decimal(str(duration)))` に変更 | `test_refresh_preserves_frozen_entry_bytes_and_values`＋P8。5.89→5.9で赤。 | canonical描画・数値表記・failed/error保持の新設testも赤。実台帳再生成後は12値 pin の既存 T-1574 が**冗長 gate**。 |
| M6 | `G:492` の `sort_keys=True` を `False` に変更 | `test_refresh_renders_canonical_bytes`。`T:846` の完全bytes比較で赤。 | 既存 gate の直接検出なし。トップレベルkey順も変わるので、赤は凍結map順だけに帰属しない。payload側を別途sortしても、逆順の凍結fixtureが残る。 |
| M7 | `G:82` を `mode = parser` に変更して独立optionへ戻す | `test_refresh_and_add_only_are_mutually_exclusive`。`T:873` の `SystemExit` が起きず赤。現分岐なら add-only が実行される。 | 既存 add-only正常系は併用を渡さないため直接検出なし。 |
| M8 | `G:548` で、output不在時だけ既存mapを `{}` とする | `test_refresh_requires_existing_ledger`。期待rc=2に対して生成成功し `T:886` で赤。 | 既存 gate の直接検出なし。不正既存台帳まで空map扱いにする変異は、M8より広い別変異。 |
| M9 | `G:549` で refresh 戻り値のnode集合を別変数へ受け、`ledger_nodeids` をJUnit集合のままにする | `test_refresh_check_and_coverage_use_refreshed_nodeids`。`T:935` が期待する1/3に対し2/3を表示して赤。 | 既存coverage testはrefreshを使わず直接検出なし。台帳bytes自体は正しいためT-1574も検出しない。 |

M9 の fixture は裁定中の例示「1/2→2/2」から分母が3に増えているが、除外される凍結新規nodeを含む条件は満たす。検出差は **1/3→2/3** であり、等価変異にはなっていない。

M0以外に、指定した具体形で全対象testを生存する等価変異は静的には見当たらない。既存 add-only testを、refresh限定変異の冗長 gate と数えるのは誤りである。

## 総括

**GO — must-fix 0件、nit 2件。**

凍結集合・値、既裁定の境界、非凍結値の出所を緩める実装変更は認めなかった。親検算の単独行の過大な検査名と、末尾凍結entryの未被覆は残るが、今回の成果物を誤って受理する根拠にはならない。

これは静的レビューのGOである。変異の赤、焦点走、受入走は本レビューでは未実測。