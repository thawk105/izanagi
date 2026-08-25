## 現状の読み取り

- `tools/check_docs.py:1003-1009` は carry を新形式の完全一致と legacy 形式の検索で認識する。どちらも task ID と target entry 番号を抽出する。

- `tools/check_docs.py:1881-1930` の `_validate_next_action_items` は `### 次の一手` のトップレベル項目だけを検査するが、carry は `dict[int, _CarryReference]` へ `target` を key に `setdefault` する。このため同じ target を指す約 404,326 件が実質 957 target に collapse し、後続 occurrence の task ID と source entry を失う。

- `tools/check_docs.py:2049-2077` の `_validate_entry_universe` は全域 entry 番号の重複を検出し、`numbered_archive_input_complete` が偽なら finding を出して停止する。入力が完全な場合も確認するのは target 番号の実在だけで、target の `### 次の一手` の ID 集合は参照しない。

- `tools/check_docs.py:2567-2600` は現行 worklog の entry location、`next_actions`、`sources` を構築する。`sources` は entry ごとの次の一手 ID 集合だが、entry 番号から引く索引にはなっていない。

- `tools/check_docs.py:2683-2736` は番号付き archive の entry location と `archive_sources` を作る。ID 導入前の非末尾 entry は `section=None` になりうるが、この「索引不能」と「ID 集合が空」が区別可能な形で全域索引へ保存されていない。

- `tools/check_docs.py:2800-2805` で上記の collapsed dict を `_validate_entry_universe` に渡す。ここが同一 ID 検査を統合する終端である。

- `orchestrator/tests/test_check_docs.py:10778-10813` は新形式・legacy 形式の実在／宙吊りを固定している。ただし `test_backlog_guard_carry_reference_existing_in_current_is_clean` は `[T-002]` から entry 1 を参照し、entry 1 の次の一手が `[T-001]` でも緑を期待している。期待を赤へ反転せず、正例 fixture の target 側を `[T-002]` に直す必要がある。

- `orchestrator/tests/test_check_docs.py:10831-10845` の番号付き archive 正例も target の次の一手が空のまま緑を期待する。これも期待値は維持し、target に同じ ID を置く fixture 補正が必要である。

## 変更プラン

1. `tools/check_docs.py:203-249` — 台帳と母数 pin の追加

   - 変更前: placeholder 用の既知違反台帳と固定総数だけがある。
   - 変更後: 次を追加する。

     - `KNOWN_CARRY_ID_MISMATCHES`
     - `EXPECTED_KNOWN_CARRY_ID_MISMATCHES = 4`
     - `MIN_EXPECTED_CARRY_REFERENCE_COUNT = 404_326`

   - `KNOWN_CARRY_ID_MISMATCHES` は `dict[tuple[int, str, int], int]` とし、key は `(carry_source_entry, task_id, target_entry)`、value は期待観測数とする。
   - コメントで D837 による固定台帳であること、追加はユーザーの明示裁定に限ることを明記する。
   - 理由: path・行番号を同一性から外し、archive ローテーションに耐えつつ、台帳総数と母集合を独立に pin するため。

2. `tools/check_docs.py:1031-1045` — occurrence を失わないデータ型への変更

   - 変更前: `_CarryReference` は `path`, `line`, `task_id` だけを持ち、target は外側 dict の key にある。
   - 変更後: `_CarryReference` に `source_entry: int`, `target_entry: int` を追加する。
   - 新設する `_CarrySource` は `path`, `whole_text`, `source_entry`, `section_body`, `section_offset` を持つ。
   - 理由: 台帳 key の source entry と、同一 ID 判定の target/task ID を occurrence ごとに保持するため。404,326 個の `_CarryReference` は materialize せず、約 957 entry 分の `_CarrySource` だけを保持する。

3. `tools/check_docs.py:1881-1930` — carry 抽出を streaming traversal へ分離

   - 変更前: `_validate_next_action_items` が項目構造検査と collapsed carry 収集を同時に行う。
   - 変更後: `carry_references` 引数と `setdefault` 部分を削除し、同関数を項目構造検査だけに戻す。
   - 同じ近傍へ `_iter_carry_references(sources: Sequence[_CarrySource]) -> Iterator[_CarryReference]` を新設する。
   - `_iter_carry_references` は各 section の `_top_level_items` を一度だけ走査し、現行と同じ二つの regex で認識した occurrence を逐次 yield する。
   - 理由: `(target, task_id)` より粗い collapse をなくし、source entry の異なる同一 `(target, task_id)` を別 occurrence として検査しながら、404,326 record の常駐を避けるため。この走査が追加 traversal の唯一の 1 回となる。

4. `tools/check_docs.py:2049-2077` — `_validate_entry_universe` の強化

   - 変更前: `dict[int, _CarryReference]` を受け、target 実在だけを調べる。
   - 変更後: 次を受ける形に変更する。

     - `next_action_ids_by_entry: Mapping[int, set[str] | None]`
     - `carry_references: Iterator[_CarryReference]`

   - 内部処理は次の順序にする。

     1. 全域 entry 番号の重複検査を現状どおり実施する。
     2. `numbered_archive_input_complete` が偽なら、現行の finding 文言を維持して return する。iterator は消費しない。
     3. `KNOWN_CARRY_ID_MISMATCHES` の登録 occurrence 総数が `EXPECTED_KNOWN_CARRY_ID_MISMATCHES` と一致するか調べる。
     4. carry stream を一度だけ消費し、全 occurrence 数を数える。
     5. target が universe に無ければ `missing_by_target.setdefault(target, carry)` に保存し、最後に target 順で現行と同じ宙吊り finding を出す。これにより既存の「target ごとに 1 finding」という挙動を保つ。
     6. target が重複 entry なら同一 ID 判定を行わない。既に重複 finding が赤を保証し、任意の片方を選ばない。
     7. target は実在するが索引値が `None` または索引自体が無い場合、「参照先 entry の次の一手 ID 集合を索引できない」という専用 finding を target ごとに 1 件出す。
     8. target の ID 集合に同じ task ID があれば受理する。
     9. 同じ ID が無ければ `(source_entry, task_id, target_entry)` を台帳と照合する。未登録なら source path/line を含む新規違反 finding、登録済みなら観測数を加算する。
     10. 各登録 key の観測数が期待値と一致するか検査する。
     11. carry occurrence 総数が `MIN_EXPECTED_CARRY_REFERENCE_COUNT` 未満なら母数縮退 finding を出す。

   - 理由: 実在検査を後方互換に保ちつつ、同一 ID、既知違反、索引不能、母数縮退を一つの fail-closed 終端で扱うため。

5. `tools/check_docs.py:2567-2600` — 現行 worklog の索引と carry source 登録

   - 変更前: `entry_locations`, `next_actions`, `sources`, collapsed `carry_references` を別々に作る。
   - 変更後: `next_action_ids_by_entry: dict[int, set[str] | None]` と `carry_sources: list[_CarrySource]` を初期化する。
   - current entry ごとに `number -> sources[i]` を登録する。section 抽出失敗時は `number -> None` とする。
   - 現行と同じ `_validate_next_action_items` 適用条件を満たす section だけ `_CarrySource` に登録する。
   - `sources[i]` の同じ set object を索引値として再利用し、412,401 ID を別 set へ複製しない。
   - 理由: 既存 traversal 中に O(957) の索引参照だけを足し、追加メモリを抑えるため。

6. `tools/check_docs.py:2683-2736` — 番号付き archive の索引と索引不能状態

   - 変更前: `archive_sources` は遷移検査にだけ使用され、carry は `_validate_next_action_items` 内で収集される。
   - 変更後: 番号付き archive の entry 番号ごとに、section が抽出できれば既存 `source_ids` set、ID 導入前などで抽出対象外なら `None` を `next_action_ids_by_entry` に登録する。
   - 番号付きかつ ID-bearing で section がある entry だけ `_CarrySource` に加える。番号を持たない H2 は既存 finding を出したまま source 登録しない。
   - 非番号付き archive の carry は現行どおり検査対象外に保つ。
   - 理由: 「ID が無い」と「索引できない」を区別し、P4 の専用 finding を実現するため。

7. `tools/check_docs.py:2800-2805` — streaming validator の接続

   - 変更前: collapsed dict を渡す。
   - 変更後: `next_action_ids_by_entry` と `_iter_carry_references(carry_sources)` を `_validate_entry_universe` に渡す。
   - 理由: 追加 traversal をこの 1 箇所に限定し、全 entry の索引完成後に carry を判定するため。

8. `orchestrator/tests/test_check_docs.py:420-457,686-741,1083-1174` — synthetic baseline の補強

   - 変更前: synthetic repo には D837 の既知 4 件も 404,326 件の母数もない。
   - 変更後: `_KNOWN_CARRY_ID_MISMATCH_ARCHIVE_NAME` と `_KNOWN_CARRY_ID_MISMATCH_ARCHIVE` を追加し、entry 73〜78 の最小 archive に確定 4 件を再現する。entry 75 は filename range を連続にし、隣接遷移を成立させる bridge とする。
   - `_archive_readme` と `_write_archive_index` はこの番号付き synthetic archive の正規 range 行を常に含める。次 archive の先頭には entry 78 の source ID を消費する項目を置き、既存遷移検査を満たす。
   - copied checker の `MIN_EXPECTED_CARRY_REFERENCE_COUNT` だけを exact 1 回の置換で `4` に specialize し、置換数が 1 でなければ test setup 自体を失敗させる。台帳本体と期待上限 4 は production と同一に保つ。
   - 理由: production に test bypass を作らず、synthetic baseline でも「既知 4 件を観測した上で緑」という実際の契約を通すため。

9. `orchestrator/tests/test_check_docs.py:10778-10845` — 既存正例 fixture の補正

   - 変更前: target 実在だけを満たす正例がある。
   - 変更後: current target 正例では target entry の次の一手を carry と同じ ID にする。番号付き archive 正例では target の次の一手へ同じ ID を置き、archive 境界遷移も同じ ID で成立させる。
   - assertion、期待 rc、skip 状態は一切変更しない。
   - 理由: D837 後も「正しい carry は緑」という既存テストの意味を維持するため。

## 既知違反台帳の設計

key は `(carry_source_entry, task_id, target_entry)` とし、path と行番号は診断表示にだけ使う。登録内容は次の 4 件で、各期待観測数は 1 とする。

| source entry | task ID | target entry | 期待観測数 | 現在の所在 |
|---:|---|---:|---:|---|
| 74 | `[T-209]` | 73 | 1 | `docs/archive/worklog-phase3-0731-77.md` |
| 76 | `[T-208]` | 73 | 1 | `docs/archive/worklog-phase3-0731-77.md` |
| 77 | `[T-210]` | 73 | 1 | `docs/archive/worklog-phase3-0731-77.md` |
| 78 | `[T-211]` | 73 | 1 | `docs/archive/worklog-phase3-0731-77.md` |

緑の条件式は次の論理積にする。

```text
registered_total =
    sum(KNOWN_CARRY_ID_MISMATCHES.values())
registered_total == EXPECTED_KNOWN_CARRY_ID_MISMATCHES == 4

checked_carry_reference_count >= MIN_EXPECTED_CARRY_REFERENCE_COUNT == 404326

全 registered key k について:
    observed_known_mismatches[k] == KNOWN_CARRY_ID_MISMATCHES[k] == 1

全 observed mismatch r について:
    key(r) in KNOWN_CARRY_ID_MISMATCHES
```

したがって緑なら、観測された mismatch は登録済み 4 occurrence だけとなる。新規 mismatch、台帳への無裁定追加、登録済み occurrence の消失・複製、母数の 404,326 未満への縮退は、それぞれ独立に赤になる。

`MIN_EXPECTED_CARRY_REFERENCE_COUNT` は exact count ではなく現在の実測値を下限として固定する。carry は追記・archive ローテーションで減らない量であり、exact pin にすると正常な carry 追加のたびに checker 本体の更新が必要になるためである。

## テストプラン

追加先は `orchestrator/tests/test_check_docs.py:10777-10912` の carry 検査群を基本とし、台帳の静的 pin は既存 placeholder 台帳テストに近い `orchestrator/tests/test_check_docs.py:5159-5235` の近傍へ置く。

1. `test_backlog_guard_carry_same_id_mismatch_is_positive_control`

   - target entry 1 は実在するが次の一手は `[T-001]`、source entry 2 は `[T-002] (1)` とする。
   - rc=1、source path/line、`[T-002]`、target `(1)`、同じ ID が無い旨を固定する。
   - 旧実在検査だけなら緑になる fixture なので、これを主要な positive control と明示する。

2. `test_backlog_guard_known_carry_id_mismatches_are_clean`

   - synthetic entry 73〜78 に確定 4 件を置き、台帳と母数下限 4を満たす。
   - rc=0 と同一 ID finding 不在を固定する。
   - P5(ii) の「登録済み 4 件は緑」に対応する。

3. `test_backlog_guard_carry_mismatch_ledger_entries_are_pinned_exactly`

   - production module の `KNOWN_CARRY_ID_MISMATCHES` を上記 4 key と value 1 の dict と exact 比較する。
   - path や行番号が key に混入していないことも固定する。

4. `test_backlog_guard_carry_mismatch_ledger_total_is_enforced`

   - fixture module の台帳へ未裁定の 5 件目を monkeypatch し、期待総数は 4 のまま validator を呼ぶ。
   - 「台帳 occurrence 総数 expected=4, actual=5」が赤になることを固定する。

5. `test_backlog_guard_registered_carry_mismatch_removal_is_violation`

   - 登録 4 key のうち 1 occurrence だけを carry stream から除く。
   - 当該 key の `expected=1, actual=0` finding を固定する。
   - 台帳登録済みなら実体が消えても緑、という恒真化を防ぐ。

6. `test_backlog_guard_same_target_and_id_from_new_source_is_violation`

   - 台帳登録済み `(74, [T-209], 73)` と、未登録 `(75, [T-209], 73)` を同時に渡す。
   - source 74 は受理され、source 75 は新規違反になることを固定する。
   - `(target, task_id)` collapse に戻って source 75 が隠れる退行を防ぐ。

7. `test_backlog_guard_carry_reference_population_floor_rejects_shrink`

   - 台帳を空、期待上限を 0、母数下限を 2 にした direct fixture へ、同一 ID が成立する carry を 1 件だけ渡す。
   - mismatch が 0 件でも母数 `actual=1, minimum=2` だけで finding が出ることを固定する。
   - P5(iii) の母集合空・縮退 positive control に対応する。

8. `test_backlog_guard_unindexable_carry_target_is_distinct_violation`

   - target は `locations` に実在させるが、`next_action_ids_by_entry[target] = None` とする。
   - 「同じ ID が無い」ではなく「次の一手 ID 集合を索引できない」という専用 finding を固定する。
   - ID 導入前 archive を既知 mismatch と誤分類したり黙って通したりしないことを固定する。

9. `test_backlog_guard_incomplete_numbered_archive_stops_carry_validation`

   - proper README claim を持つ番号付き archive を invalid UTF-8 にし、`numbered_archive_input_complete=False` に到達させる。
   - rc=1 と既存の「番号付き archive 入力が不完全」「carry 参照先の実在検査を停止」を固定する。
   - carry iterator を消費しない direct control も入れ、部分集合の母数や台帳観測を完全入力として扱わないことを確認する。

10. `test_backlog_guard_carry_references_are_streamed`

    - `_iter_carry_references` の返値が iterator 自身を返すことを確認し、全 occurrence の list 化を禁止する。
    - 二つの source section から順次 yield され、source entry、task ID、target、line が保持されることを固定する。

11. 既存 `test_backlog_guard_carry_reference_existing_in_current_is_clean` (`orchestrator/tests/test_check_docs.py:10778-10794`)

    - assertion は変えず、target の次の一手に同じ ID がある正例へ fixture だけを補正する。
    - 新形式と二つの legacy 表記の被覆を維持する。

12. 既存 `test_backlog_guard_dangling_carry_reference_is_violation` (`orchestrator/tests/test_check_docs.py:10797-10813`)

    - 変更せず、実在検査の挙動が残ることを固定する。

13. 既存 `test_backlog_guard_new_carry_syntax_in_prose_is_not_a_reference` (`orchestrator/tests/test_check_docs.py:10816-10828`)

    - 変更せず、regex が prose 内の類似形へ広がらない negative control とする。

14. 既存 `test_real_repo_clean` (`orchestrator/tests/test_check_docs.py:11145-11153`)

    - assertion は変更せず、実 repo で既知 4 件と母数 404,326 を観測して rc=0 になる回帰とする。
    - 本段では実走せず、親の実測対象とする。

## 恒真化しない根拠

- 台帳上限: `sum(ledger.values()) == 4` なので、5 件目を台帳へ足すだけでは緑にならない。
- 台帳実体: 各 key の `actual == expected == 1` なので、登録済み occurrence の消失・複製も赤になる。
- 新規違反: mismatch の key が台帳に無ければ件数に関係なく即 finding になる。
- 母集合: `checked_carry_reference_count >= 404326` なので、regex が carry を 0 件または現状未満しか認識しなくなれば赤になる。
- 入力不完全: `numbered_archive_input_complete=False` は現行 finding を出して return するため、部分入力を空の正常集合として扱わない。
- target 索引不能: `next_action_ids_by_entry[target] is None` は専用 finding になり、空集合扱いにも無条件受理にもならない。
- target 重複: 全域番号重複 finding が先に赤を保証し、どちらか一方の ID 集合を恣意的に採用しない。
- regex 過剰一致: 既存 prose negative control と新形式・legacy の正負テストが、母数下限だけでは捕捉しにくい過剰一致を固定する。
- occurrence collapse: source entry の異なる同一 `(target, task_id)` を別 yield とする positive control により、既知 1 件で後続新規違反を隠せない。

## 残る危険

- 実測は行っていない。追加 traversal は section body の streaming 1 回だけで、親の probe 値では約 1.69 秒の増分が見込まれるが、総所要が 21.04 秒未満かは親が段 5 以降で測る必要がある。

- `MIN_EXPECTED_CARRY_REFERENCE_COUNT = 404_326` は現在値未満への縮退を止めるが、将来 404,326 より増えた後の部分消失がなお下限以上なら検出しない。carry が単調増加するという P3 を採用し、節目ごとに下限を ratchet する運用が必要である。exact pin は通常追加のたび checker 更新を要求するため推奨しない。

- regex の過剰一致は下限検査だけでは赤にならない。既存 prose negative control と形式別テストで閉じるが、regex 文法を大幅に変える変更には追加 mutation が必要である。

- 索引不能 finding は target ごとに 1 件へ集約する案である。全 carry occurrence を列挙するより出力を制御できるが、どの source を代表表示するかは最初の occurrence になる。

- P1、P3、P4、P5 に反対しない。P2 は意味上採用するが、404,326 occurrence の保持は行わず streaming へ精緻化する。検査粒度は `(target, task_id)` より細かい `(source_entry, task_id, target)` なので、P2 の検出力を弱めない。

- synthetic repo の母数 pin を 4 に置換する helper は production escape ではないが、置換対象が 1 件であることを assert しないと checker 定数の改名時にテスト設定だけ黙って壊れる。

## 総括

`carry_references` の target 単位 collapse を occurrence stream に置き換え、完成済みの entry 番号・次の一手 ID 索引へ照合する。  
確定 4 件は `(source entry, task ID, target entry)` 台帳でのみ受理し、台帳総数 4、各観測数 1、母数下限 404,326 を対で検査する。  
ID 導入前の索引不能、番号付き archive の入力不完全、target 重複はいずれも fail-closed の別 finding とする。  
404,326 record は常駐させず、追加 traversal は streaming 1 回に限定する。  
本段ではファイル変更もテスト実走もしておらず、緑は主張しない。  
親が段 4 で裁定すべき残余は、母数下限の将来 ratchet 方針と、索引不能 finding を target 単位で集約する粒度である。