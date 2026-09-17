## 設計 (refresh mode)

`--refresh` を追加する。既存の `_ledger_bytes` で JUnit を検証・量子化した後、既存台帳の凍結部分と合成する。

以下、行番号は変更前のファイルを指す。新設関数は挿入位置と処理名で指定する。

**集合と値の規則**

既存台帳を `E`、`_ledger_bytes` が生成した成功・skip testcase の map を `J`、凍結 prefix 判定を `F(k) = k.startswith(_ADD_ONLY_FROZEN_SUITE_PREFIXES)` とする。

```python
frozen = {k: v for k, v in E.items() if F(k)}
old_nonfrozen = {k: v for k, v in E.items() if not F(k)}
new_nonfrozen = {k: v for k, v in J.items() if not F(k)}
result = {**frozen, **new_nonfrozen}
```

- 凍結 entry は JUnit に無くても保持し、値を再量子化しない。`@real-repo` を含む既存 key もそのまま保持する。
- 非凍結 entry は JUnit の値で置換する。JUnit に無い旧名は削除、新名は追加する。
- 凍結 prefix 内の JUnit entry は、既存・新規を問わず採用しない。
- removed 5 件と writer base key がすべて凍結 prefix 内であることを独立した test で検証する。writer base key は removed 集合にも含まれるため、fixture へ二重投入しない。
- 入力重複、join、量子化、failed/error 除外は既存 `_ledger_bytes` のままとする。凍結 testcase も、この検証を通った後に refresh の採用対象から除外する。

**CLI と戻り値**

`_parser` の L82〜89 を `add_mutually_exclusive_group()` に移し、同じ group に `--refresh` を追加する。双方省略時は現在の全再生成、`--add-only` の動作・stdout は維持する。

| 組合せ | 動作 |
|---|---|
| `--refresh` | 出力先の既存台帳を読み、refresh 結果を atomic write |
| `--refresh --output PATH` | `PATH` を既存台帳の入力兼出力先にする。別ファイルへの出力なら、事前に既存台帳をそこへ複製する必要がある |
| `--refresh --check` | refresh 結果と既存 bytes が一致なら rc=0、不一致なら rc=1。書き込まない |
| `--refresh --coverage-against FILE` | refresh **後の集合**について被覆を表示する。閾値判定は追加しない |
| 上記3 option の併用 | 同じ意味で併用可能 |
| `--refresh --add-only` | argparse による rc=2。`main()` 直接呼出しでは `SystemExit(2)` |
| 既存台帳が不在・不正 | `_existing_ledger(output)` の拒否で rc=2。書込みなし |
| 不正 JUnit・重複 nodeid | 現行どおり rc=2。書込みなし |

**新設関数と stdout**

L441 の後へ、次の形で追加する。

```python
def _refresh_result(
    generated: bytes,
    existing_durations: Mapping[str, float],
) -> tuple[bytes, set[str], dict[str, int]]:
    ...
```

戻り値は `_add_only_result` と同型にする。count は次の集合演算で定義し、値が偶然同じでも JUnit から再採用した既存 key は `replaced` に数える。

```text
excluded_failure_or_error=<既存の除外数>
mode=refresh
preserved_frozen=<len(frozen)>
replaced=<len(old_nonfrozen.keys() & new_nonfrozen.keys())>
added=<len(new_nonfrozen.keys() - old_nonfrozen.keys())>
removed=<len(old_nonfrozen.keys() - new_nonfrozen.keys())>
excluded_frozen_suite=<J のうち凍結 prefix に一致する件数>
covered=... total=... ratio=...    # coverage 指定時だけ
```

`excluded_frozen_suite` は **failed/error 除外後**の testcase 数とする。failed/error は先頭の既存 count にのみ計上し、二重計上しない。重複 nodeid は先に拒否するので、この段階では entry 数と testcase 数が一致する。この優先順位を help/docstring と混合 outcome test に明記する。

`main` L485〜493 に `elif args.refresh` 分岐を追加し、`_existing_ledger` と `_refresh_result` を呼ぶ。L535 の coverage 表示前に refresh count を表示する。coverage、`_check`、`_atomic_write` の既存経路を共用する。

**canonical 描画と凍結 bytes**

payload は現在と同じ4 field とし、L266〜282 と同じ設定で描画する。

```python
json.dumps(
    payload,
    sort_keys=True,
    indent=2,
    ensure_ascii=True,
    allow_nan=False,
) + "\n"
```

凍結値は `_existing_ledger` が返した数値をそのまま持ち回る。特に `5.89` を `_quantize_seconds` に通して `5.9` にしない。

同じ Python JSON 描画系で生成された有限 float の数値 token は、parse で同じ float に戻り、再度 dumps すれば同じ表記になる。一方、任意の JSON に対する byte 不変ではない。例えば `5.890` は `5.89`、`1e0` は `1.0` になり、key の escape・空白・順序・末尾 comma の位置も変わりうる。なお `_existing_ledger` は int も許すため、不必要な `float()` 変換もしない。

したがって、mode の一般契約は「凍結 key・数値保持と canonical 出力」とする。本 wave の厳密な byte 不変条件は、親が再生成前後の **実台帳の全凍結 entry 行**を key ごとに比較して検証する。差があれば本 wave の成果物として採用せず停止する。T-1574 の数値比較だけで byte 不変を証明したことにはしない。

**failed/error の既存 entry をどう扱うか**

非凍結なら削除する案を推奨する。

- 削除案は「非凍結部分を入力 JUnit から全再生成」と一致し、旧値を実測更新済みと誤認させない。`allocate` L396〜403 では未登録の 1.0 秒扱いになる。
- 保持案は直前値を利用できるが、非凍結部分にも旧値の例外が残り、完全再生成・stale 解消の契約が曖昧になる。

この 1.0 秒は consumer の既存 fallback であり、生成器が台帳へ合成して書く値ではない。全 testcase が failed/error の場合は `_ledger_bytes` L259〜265 が先に rc=2 で拒否し、台帳全消去には進まない。

## 変更一覧 (file:line、関数名、追加 / 変更の別)

| file:line | 関数・対象 | 種別・内容 |
|---|---|---|
| `tools/update_acceptance_duration_ledger.py:57`、特に L82〜89 | `_parser` | 変更：mode の排他 group と `--refresh`、help を追加 |
| 同 `:441` の後、`:444` の前 | `_refresh_result` | 追加：凍結保持、非凍結再生成、集合 count、canonical 描画 |
| 同 `:476`、特に L485〜493 | `main` | 変更：refresh 分岐、既存台帳の読込み、新関数への接続 |
| 同 `:509`〜535 | `main` | 変更：既存 stdout を維持したまま refresh count 行を追加 |
| `orchestrator/tests/test_update_acceptance_duration_ledger.py:605` の後 | 下記の新 test 群 | 追加：L515 の既存 add-only test を型にする |
| `orchestrator/tests/acceptance_duration_ledger.json:1` | JSON 全体 | producer 出力による再生成のみ。手編集しない |

`_existing_ledger` L329〜359、`_ledger_bytes` L235〜282、add-only 実装、既存 test 全件は維持する。consumer、0.90 閾値、凍結定数、除外集合は変更しない。

## test 一覧

すべて `orchestrator/tests/test_update_acceptance_duration_ledger.py` に追加する。fixture は既存 `join_repo`、`_case`、`_write_junit`、`_run` を利用する。

1. **`test_refresh_replaces_nonfrozen_entries_and_removes_old_names`**
   既存に `test_existing=0.5`、`test_old=0.7`。JUnit に `test_existing=9.9`、`test_new=0.25`。結果を2 key の literal map と比較し、旧名不在、`replaced=1 / added=1 / removed=1`、`nodeid_count=2` を assert。同値の既存 key を含めた parameter case で `replaced` の定義も固定する。

2. **`test_refresh_preserves_frozen_entry_bytes_and_values`**
   8 suite の module fixture を L520〜523 と同様に作る。各 prefix に凍結既存 entry を置き、一部は JUnit 不在、一部は JUnit に異なる値で登場させる。`5.89` と writer の `@real-repo` key を含める。既存 JSON は同じ dumps 設定による entry 表記とし、非凍結の末尾 entry を前後とも置く。凍結 map の完全一致、各 entry 行の bytes 一致、`preserved_frozen` を assert。位置変更は許すが entry 自体の差は許さない。

3. **`test_refresh_excludes_all_frozen_junit_nodes`**
   各 prefix に未登録 testcase を1個ずつ、removed 5件、writer の group suffix 付き testcaseを別 parameter case として投入する。writer は suffix 除去後に base key になるため、同じ入力へ base と重複投入しない。非凍結の対照 testcase は残ること、凍結新規 key・removed・base key が不在であること、除外 count を assert。

4. **`test_refresh_frozen_prefixes_cover_removed_nodes_and_writer_base_key`**
   removed 全件と writer base key に対して `startswith(prefixes)` を assert。writer が removed 集合内であることも assert。refresh に別の除外規則を足さなくてよい根拠を固定する。

5. **`test_refresh_renders_canonical_bytes`**
   既存 map を非 sort 順に書き、JUnit も逆順にする。Unicode を含む key を用意し、literal expected payload を `sort_keys=True, indent=2, ensure_ascii=True, allow_nan=False` で描画した bytes と完全比較する。末尾 LF、再実行の bytes 一致も assert。

6. **`test_refresh_canonicalizes_noncanonical_frozen_number_spelling`**
   凍結値 token が `5.890` の有効 JSON を入力する。出力数値は `5.89`、token は canonical 化されることを assert。一般の入力で raw bytes 保持までは保証しない境界を明示する。本 wave の実台帳にこの差が出た場合は親の採用前検算で停止する。

7. **`test_refresh_and_add_only_are_mutually_exclusive`**
   有効な既存台帳・JUnit に両 flag を付け、`pytest.raises(SystemExit)` の code が2、stderr に両 option、出力 bytes 不変を assert。

8. **`test_refresh_requires_existing_ledger`**
   有効 JUnit と不在 output。rc=2、`_REJECTION_PREFIX`、`cannot read existing ledger`、ファイル未作成を assert。

9. **`test_refresh_rejects_invalid_existing_ledger_without_writing`**
   壊れた JSON、schema/unit 不正、件数不一致、bool・負値・非有限 duration を parameter 化。rc=2、固定拒否 prefix、元 bytes 不変を assert。

10. **`test_refresh_check_and_coverage_use_refreshed_nodeids`**
    既存に旧名、JUnit に新名、coverage に新名と未登録名を置く。最初の `--check` は rc=1・書込みなしでも、coverage は生成後集合の `covered=1 total=2 ratio=0.500`。通常 refresh 後の `--check` は rc=0。既存集合や全 JUnit 集合を coverage に誤使用しないよう、凍結新規 testcase も含める。

11. **`test_refresh_drops_failed_and_error_nonfrozen_entries`**
    既存の非凍結2 key を failure/error にし、正常・skip・凍結 failure を混在させる。非凍結2 key は消え、skip は量子化値で残り、凍結既存値は残る。failed/error count と frozen exclusion count の二重計上なしを assert。

12. **`test_refresh_rejects_unusable_junit_without_writing`**
    有効な既存台帳に対して空 JUnit、全失敗、shard 間重複を parameter 化。rc=2、元 bytes 不変。全失敗時に凍結だけの台帳へ縮退しないことを確認する。

既存 `test_t1574_changed_suite_ledger_node_delta_is_exact`、add-only test、schema test は削除・改名・期待値変更をしない。

## 台帳再生成の手順と親の検算項目

1. 親が入力3 shard、基準 collection、再生成前台帳の識別情報を記録する。入力間の重複なし、failed/error=0、基準 collection と入力集合の差0を再確認する。`collect-main.nodeids` は marker 行除去済みを使う。
2. 再生成前の凍結426 entry の key・数値・元 entry bytes、T-1574 の8 suite hash・12値・removed 5件不在を保存する。
3. author が既存生成器に実装を加え、次を実行する。これは親・author 用の手順であり、この plan 段では実行しない。

```bash
python3 tools/update_acceptance_duration_ledger.py \
  /work/1/SFC/tanab/.izanagi-acceptance-shards/d3ebafc08d3d12c86081dcd356ebb80c/shard-0/junit.xml \
  /work/1/SFC/tanab/.izanagi-acceptance-shards/d3ebafc08d3d12c86081dcd356ebb80c/shard-1/junit.xml \
  /work/1/SFC/tanab/.izanagi-acceptance-shards/d3ebafc08d3d12c86081dcd356ebb80c/shard-2/junit.xml \
  --repo /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2236-ledger-refresh \
  --refresh \
  --coverage-against /home/SFC/tanab/.claude/jobs/897c9a22/tmp/collect-main.nodeids
```

4. 同じ command に `--check` を追加して再実行し、rc=0 と bytes 一致を確認する。
5. 親が次を独立検算する。

| 検算対象 | 期待 |
|---|---|
| 凍結既存 entry | 426件、key・全値・entry bytes 不変 |
| T-1574 suite identity | L364〜388 の8組の件数・SHA-256 と一致 |
| T-1574 exact 値 | L343〜355 の12値と一致 |
| removed と writer base | removed 5件不在、base key 不在、既存 `@real-repo` は保持 |
| 非凍結結果 | JUnit 由来の非凍結 map と完全一致 |
| 旧名 | 親の一覧126件がすべて消失。非凍結 stale 0 |
| 値の出所 | 非凍結は既存量子化関数による入力値、凍結は旧台帳値。その他なし |
| 件数 | `426 + 23953 = 24379`、`nodeid_count == len(map)` |
| 初回 count | `preserved_frozen=426 / replaced=22593 / added=1360 / removed=126` |
| 残存差分 | stale 18、未登録207、いずれも凍結内 |
| 被覆 | **24361 / 24568 = 約99.16%** |
| 描画 | canonical bytes と末尾 LF。再実行で差なし |

**24,379 は台帳総数であり、被覆の分子ではない。** stale 18件を除く24,361件が被覆数になる。既存 stdout は小数3桁なので `ratio=0.992` と表示される。99.16% の検算は整数分子・分母から行う。

新 test 追加後の collection は24,568件より増える。上表は指定された基準 collection に対する期待であり、実際の被覆 gate の分母とは区別する。追加 test の未測定値は合成しない。

6. 生成器・test・台帳を commit してから、親が既定の実行経路で `test_update_acceptance_duration_ledger.py`、`test_acceptance_schedule_order.py`、`test_paper_story_a1_headline.py` を焦点検査する。未実行を緑と扱わない。
7. 親が受入 after を1走取り、before の shard wall `350.994 / 238.476 / 202.659` 秒と並べて観測値を記録する。改善・退行・300秒達成の一般的主張には使わない。

## 変異 matrix 候補

新設関数の行番号はまだ存在しないため、変更前の挿入アンカーと対象式で指定する。親は実装後の exact 行番号を段4の登録へ転記する。以下の test node は、特記がなければすべて `orchestrator/tests/test_update_acceptance_duration_ledger.py::<関数名>`。

| # | 生成器の変更箇所・変異 | 赤になる test node |
|---|---|---|
| 1 | L441後 `_refresh_result` の `new_nonfrozen` から prefix 除外条件を外す | `test_refresh_excludes_all_frozen_junit_nodes`。変異 producer で実台帳を再生成した場合は `test_t1574_changed_suite_ledger_node_delta_is_exact` も赤 |
| 2 | 同、凍結 map の値を JUnit の対応値で上書きする | `test_refresh_preserves_frozen_entry_bytes_and_values`。実台帳再生成後は T-1574 の12値 pin も赤 |
| 3 | 同、結果の初期値を `frozen` から `dict(existing_durations)` へ変え、旧非凍結 key を残す | `test_refresh_replaces_nonfrozen_entries_and_removes_old_names` |
| 4 | 同、共通する非凍結 key の値に旧台帳値を採用する | `test_refresh_replaces_nonfrozen_entries_and_removes_old_names` |
| 5 | 同、凍結値に `_quantize_seconds(Decimal(str(v)))` を適用する | `test_refresh_preserves_frozen_entry_bytes_and_values` の `5.89` が赤 |
| 6 | 同、描画の `sort_keys=True` を `False` にする | `test_refresh_renders_canonical_bytes` |
| 7 | L82付近、mode group を通常の独立 option 登録に戻す | `test_refresh_and_add_only_are_mutually_exclusive` |
| 8 | L493後の refresh 分岐で、不在台帳を空 map として扱う | `test_refresh_requires_existing_ledger` |
| 9 | L494〜499へ渡す `ledger_nodeids` を refresh 前の JUnit 集合に戻す | `test_refresh_check_and_coverage_use_refreshed_nodeids` |
| 10 | L441後 `_refresh_result` の docstring のみ同義に書き換える | 等価変異。赤になる test なしを期待 |

T-1574 は checked-in 台帳を読む test であり、生成器だけを変異させても直接は赤にならない。#1・#2の T-1574 検証には、隔離した変異実行先での台帳再生成を組み込む。

## 所見 (P1〜P5 への反証・懸念)

- **P1：mode 追加の必要性は確認できるが、F902 の一般運用とは区別が必要。**
  既存全再生成は凍結を破壊し、add-only は旧値を保持するため、今回の要件には新 mode が必要。ただし F902 の逐語は producer の `--add-only` と merge 時の全 entry 和集合照合まで指定している。今回の明示依頼に従って refresh を実装するが、通常の merge 解消へ適用する手順には広げない。refresh は他 wave が追加した、入力 JUnit に無い非凍結 entry も削除しうる。

- **P2：集合一致は基準 main に対する事実であり、実装後 HEAD にはそのまま適用できない。**
  新 test が増えるため、after collection と古い JUnit の差0は成立しない。基準 collection に対する再生成検算と、変更後 HEAD の被覆 gate を分ける。また、入力重複拒否は failed testcase にも働く。複数走をそのまま結合しない判断は実装と整合する。

- **P3：被覆分数に訂正が必要。**
  brief の `24379 / 24568 = 99.16%` は分子が誤り。集合差資料の stale 18・missing 207 から、正しくは `24361 / 24568`。凍結18 stale と207未登録を据え置く設計自体は整合する。ここでの「非凍結 stale 0」は旧名集合についてであり、将来の実行時間予測が正確になる保証ではない。

- **P4：1走では律速の原因断定や改善主張まで進めない。**
  D357 は node 秒を仕事量そのものと扱わない。親の file 表にも `2661 - 676 != 2126` など、列名だけでは delta の算式が説明できない行がある。未登録 fallback を含む差である可能性はあるが、今回の射影だけでは確定しない。計画は実測値への更新に留め、after の均等化や wall 改善を保証しない。

- **P5：数値保持と byte 保持は別の検証が必要。**
  T-1574 は12値を数値比較しており、数値 token の byte 一致までは検査しない。canonical 出力と任意入力の raw byte 保持は両立しない。実台帳の凍結426 entry が既に同じ描画であることを、親の採用前検算で確認する必要がある。全体 sort による位置変更は想定どおりだが、凍結 entry 自体の byte 差は見逃さない。

## 総括

`--refresh` で凍結既存値を保持し、非凍結部分だけを指定 JUnit から再生成する。既存 mode・test・consumer・閾値は維持する。

親が特に確認すべき点は、凍結 entry の byte 不変、正しい被覆分数 **24,361 / 24,568**、追加 test による分母増加、変異 producer と T-1574 検査の接続である。指定資料を静的に確認した計画であり、ファイル変更・台帳生成・pytest 実行は行っていない。