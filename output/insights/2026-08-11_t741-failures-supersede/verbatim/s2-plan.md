## 変更箇所

行番号は現行 checkout の値であり、実装後は後続行がずれる。

- `tools/spool_fold.py:56` の `FAILURE_ID_RE` 直後に、fragment item 専用の regex を追加する。raw fragment 上で `- F[1-9][0-9]* <本文>` の完全一致、本文中の非空白 1 文字以上、1 物理行を強制する。target placeholder、`F01`、H3、`base:`、継続行は一致させない。
- `tools/spool_fold.py:82-97` の `Fragment` は変更しない。これは ledger 非依存の provenance・raw bytes・決定順キーを持つ型であり、failures 固有 payload を載せると責務が崩れる。
- `tools/spool_fold.py:216-220` の `_DeferredAppend` の隣に、新規 frozen dataclass `_FailureSupersede` を置く。field は `target_number: int` と `line: str` とする。
  - `_DeferredAppend` は `[T-NNN]` の先頭行末へ suffix を連結する型。
  - `_FailureSupersede` は F エントリ末尾へ独立した 1 物理行を挿入する型。
  - target 型、挿入位置、重複判定が異なるため `_DeferredAppend` は再利用しない。
- `tools/spool_fold.py:503-655` の `_parse_worklog_delta` と `1487-1534` の `_insert_deferred_appends` は変更しない。物理行 parser、空節、同一追記拒否の設計見本としてだけ使う。

**fragment parse**

- `tools/spool_fold.py:676-736` の `_failure_symbols` を拡張する。
  - canonical 順を `("新規", "再発", "supersede 追記")` とし、現行式と同じく次で完全な部分列を検査する。

    ```python
    names != [name for name in canonical_names if name in names]
    ```

  - `not names` は引き続き拒否するが、`["supersede 追記"]` は有効にする。
  - `supersede 追記` region は空行を飛ばし、各非空行を専用 regex で検査する。非空行がゼロなら empty、1 行でも不一致なら shape issue とする。
  - raw fragment 上で target を検査するため、`{{F:slug}}` は後段の placeholder 解決前に shape 違反となる。一方、本文内 placeholder は許可する。
- `tools/spool_fold.py:900-903` では failures fragment が必ず `_failure_symbols` を通る。したがって parser issue は `validate_spool_tree` (`934-938`) にそのまま返り、`tools/check_docs.py:724-775`、特に `757` の呼び出しから `spool <code>` finding として見える。`check_docs.py` 自体の変更は不要。
- target 不存在、canonical 重複、既存同一行は canonical を必要とする semantic 検査なので、既存の recurrence と同様に `validate_spool_tree` ではなく `plan_fold`／`--dry-run` で拒否する。

**fold parse と適用**

- `tools/spool_fold.py:1273-1283` の `_replace_placeholders` は変更しない。
  - `_failure_parts` 内で従来どおり body を解決してから `_FailureSupersede.line` を作る。
  - これにより本文 placeholder は解決され、解決後に同一 bytes となる 2 item も重複として扱える。
  - target placeholder は raw parser が先に拒否済みである。
- `tools/spool_fold.py:1547-1568` の `_failure_parts` を変更する。
  - H2 regex に `supersede 追記` を追加する。
  - 戻り値を `new_entries, recurrences, supersedes` の 3 要素にする。
  - `新規` と `再発` の既存 branch は変えない。
  - `supersede 追記` は H3 ではなく物理行 item を読み、selector `- Fnn ` を除いた本文だけを `_FailureSupersede.line` に保持する。
- `tools/spool_fold.py:1571-1591` の `_insert_failure_recurrences` は変更しない。既存 fragment の bytes を守るため、supersede をこの関数へ混在させない。
- 現行 `1591` の直後に `_insert_failure_supersedes(failures, supersedes)` を追加する。
  - `FAILURE_ID_RE` で各 F の開始と次の F heading を索引し、挿入位置を対象エントリ末尾にする。
  - canonical ID 重複を防御的に `failure-duplicate` で拒否する。
  - target 不存在を拒否する。
  - 対象エントリの `splitlines()` に payload と byte-exact な行があれば拒否する。substring や `endswith` では判定しない。
  - fold 内では `(target_number, resolved_line)` の集合を持ち、同一組を拒否する。
  - target ごとの payload は入力順を保存し、複数 target への splice は canonical offset の降順で行う。
- `plan_fold` の現行 `1837-1847` を次の順にする。
  1. `supersede_entries` accumulator を `new_failure_entries`、`recurrence_entries` と並べて作る。
  2. fragment は既存の `Fragment.key` 順で `_failure_parts` し、各リストへ extend する。
  3. 現行 `1844` で `_insert_failure_recurrences`。
  4. **現行 `1844` と `1845` の間**で `_insert_failure_supersedes`。
  5. 現行 `1845` で encode。
  6. 現行 `1846-1847` で新規 F を末尾追加。
- この順により、同一 F 競合は常に `再発` 全件 → `supersede 追記` 全件となる。新規 F の追加前に supersede を適用するため、同 fold で採番される新規 F は target にできない。
- canonical F ID 重複は現行 `plan_fold:1790-1795` でも先に `failure-duplicate` となる。

## issue code 設計

repo 全体で `failure-supersede-` は未使用だった。新設する code は次の 4 個とする。

| issue code | 拒否対象 |
|---|---|
| `failure-supersede-empty` | 使用した節に非空 item がない |
| `failure-supersede-shape` | 複数行、空／空白本文、H3、`base:`、継続行、不正／placeholder target |
| `failure-supersede-missing` | literal target が canonical に存在しない |
| `failure-supersede-duplicate-line` | 同一行が対象エントリに既存、または同一 fold に同一 `(target, resolved line)` が重複 |

canonical F ID 重複には既存の ledger-wide `failure-duplicate`、H2 の未知・重複・順序違反には既存の `failure-sections` を再利用する。これは名称衝突ではなく既存 invariant の同じ発火である。

以下は共通 frontmatter の直後に置く body の逐語である。

1. 空節 → `failure-supersede-empty`

```markdown
## supersede 追記
```

2. 複数行 item → `failure-supersede-shape`

```markdown
## supersede 追記

- F1 - **supersede: 2026-08-10** — 一行目
  継続行
```

3. 空白のみ本文 → `failure-supersede-shape`。`F1` 後の本文は ASCII spaces 4 個。

```markdown
## supersede 追記

- F1    
```

4. target 不存在 → `failure-supersede-missing`

```markdown
## supersede 追記

- F999 - **supersede: 2026-08-10** — 不存在 target。
```

5. canonical F 重複 → `failure-duplicate`。次の fragment と、canonical 内の `### F1.` 2 個を組み合わせる。

```markdown
## supersede 追記

- F1 - **supersede: 2026-08-10** — target 一意性検査。
```

6. 対象エントリに同一行が既存 → `failure-supersede-duplicate-line`。F1 本文に同じ payload 行を事前配置する。

```markdown
## supersede 追記

- F1 - **supersede: 2026-08-10** — 既存と同一。
```

7. 同一 fold 内の同一組 → `failure-supersede-duplicate-line`

```markdown
## supersede 追記

- F1 - **supersede: 2026-08-10** — fold 内重複。
- F1 - **supersede: 2026-08-10** — fold 内重複。
```

P5 の target placeholder も `failure-supersede-shape` とする。新規 symbol を同じ fragment で正しく定義して `symbol-undefined` を避けた上で、次を拒否する。

```markdown
## supersede 追記

- {{F:future}} - **supersede: 2026-08-10** — placeholder target。
```

## テスト計画

**helper**

- `orchestrator/tests/test_spool_fold.py:60-95` の現行 fixture 名は `_repo` であり、依頼文にある `_seed_repo` は実ファイルに存在しない。架空の名称を使わず `_repo` をそのまま使う。既定 fixture は変更しない。
- `_fragment` (`98-121`) は arbitrary failures body を既に受け取れるため signature を変更しない。
- `_worklog_body` (`124-168`) は変更しない。既存 `test_deferred_append_*` の生成 bytes に影響させない。
- 現行 `168` と `_active_block` (`171`) の間に `_failure_body(new=..., recurrences=..., supersedes=...)` を追加し、H2 を `新規` → `再発` → `supersede 追記` の順で生成する。invalid shape／順序テストだけは raw string を `_fragment` へ直接渡す。
- `_raises` (`187-193`) は単一 code の fold-time rejection に再利用し、変更しない。
- `_target` (`196-197`) と `_splice_exact` (`212-216`) を byte-exact 検査に再利用する。必要なら `_phase_after` (`200-204`) と同型の `_failures_after` を直後に純増する。

追加先は既存 failures テスト `test_failure_section_payload_without_valid_h3_is_rejected` (`1048-1055`) の直後とする。

| 追加する関数名 | 固定する性質 | 期待値 |
|---|---|---|
| `test_failure_supersede_only_fragment_inserts_at_entry_end_byte_exact` | `新規`／`再発` がない supersede 単独を受理し、F1 と F2 の境界へ 1 行だけ splice | `before[:offset] + ("\n" + line + "\n").encode() + before[offset:]` |
| `test_failure_recurrence_precedes_supersede_for_same_target_byte_exact` | 同一 F の競合順 | 挿入 block が `"\n<再発行>\n\n<supersede行>\n"` と byte 一致 |
| `test_failure_supersede_order_is_deterministic_by_fragment_key_and_item_index` | 作成順や directory 順でなく wave/seq/item 順 | plan 2 回の `as_dict()` が一致し、行順が `A2-first, A2-second, A10, B1` |
| `test_failure_supersede_body_resolves_cross_ledger_placeholder` | target は literal のまま、本文 placeholder だけ解決 | F1 末尾が `- **supersede: 2026-08-10** — 根拠 D2\n`、`{{`/`}}` なし |
| `test_failure_supersede_target_placeholder_is_rejected` | 同 fold の新規 F を selector にできない | `failure-supersede-shape` |
| `test_failure_supersede_section_order_and_uniqueness_are_rejected` | supersede→再発の逆順、および H2 重複 | `validate_spool_tree` に `failure-sections` |
| `test_empty_failure_supersede_section_is_rejected` | P6 の空節と check_docs 経路 | `validate_spool_tree` の code が `failure-supersede-empty` |
| `test_multiline_h3_and_base_failure_supersede_shapes_are_rejected` | 継続行、H3、`base:` の各独立 subcase | 各 fixture で `failure-supersede-shape` |
| `test_empty_failure_supersede_body_is_rejected` | `- F1` だけ | `failure-supersede-shape` |
| `test_whitespace_only_failure_supersede_body_is_rejected` | `- F1` 後が空白だけ | `failure-supersede-shape` |
| `test_failure_supersede_missing_target_is_rejected` | canonical 不存在 | `failure-supersede-missing` |
| `test_failure_supersede_rejects_duplicate_canonical_target_ids` | canonical `### F1.` が 2 個 | 既存 `failure-duplicate` |
| `test_failure_supersede_rejects_existing_identical_line` | target entry に exact line が既存 | `failure-supersede-duplicate-line` |
| `test_failure_supersede_rejects_duplicate_line_within_same_fold` | 同一 fragment、別 fragment双方を跨げる fold-global guard | `failure-supersede-duplicate-line` |
| `test_failure_supersede_replay_guards_exact_and_changed_fragments` | exact raw replay と、frontmatter/seq を変えた同一出力行の replay | 前者 `receipt-replay`、後者 `failure-supersede-duplicate-line` |
| `test_failure_new_and_recurrence_only_output_remains_byte_exact` | 新 H2 を使わない既存受理集合・描画 bytes | F1 再発 splice と F2 新規末尾追加の既存 bytes を完全一致 |

既存テストの期待値・nodeid は一切変更しない。現時点で「要裁定」とする既存 nodeid はない。

## 冪等性と決定性

- fragment は現行 `Fragment.key = (wave, seq, ledger rank, path)` (`tools/spool_fold.py:94-97`) で並び、supersede item は fragment 内の物理行順を保つ。target ごとの grouping には入力順を使い、canonical への splice だけ offset 降順にする。
- 同一 target で `再発` と supersede が共存するときは、`plan_fold` が recurrence 全件を適用した結果へ supersede 全件を適用する。この順は fragment の作成順に左右されない。
- 1 回目の成功適用では canonical と `FOLDED.md` が after bytes になり、fragment は GC される。通常の 2 回目 `plan_fold` は fragment 0 件なので `noop`。
- GC 後に同一 raw fragment を戻せば、現行 `plan_fold:1780-1788` の content SHA receipt により `receipt-replay`。
- raw bytesを変えて receipt replay を避けても、resolved payload が同じなら `failure-supersede-duplicate-line`。同じ fold 内の重複も plan 作成前に同 code で止まる。
- supersede-only fragment は symbol を定義しないので receipt の `allocations` は空だが、現行 `1849-1866` の `content_sha256`、wave、seq は従来どおり記録される。receipt schema は変わらない。
- 新しい failures after bytes は現行 `1877-1893` で通常の `TargetChange` になり、before/after SHA-256 と transaction ID に含まれる。中断時は `apply_fold:2058-2106` が同じ after hash を認識して resume するため、新しい dataclass を transaction state に保存する必要はない。

## 回帰リスク

- `新規`／`再発` のみの fragment:
  - H2 の許可列へ末尾要素を足すだけで、既存の 3 有効形 `新規`、`再発`、`新規→再発` を保持する。
  - `_insert_failure_recurrences` は変更せず、supersede 空列なら新 helper は入力をそのまま返す。
  - `_failure_parts` の既存 2 branch の strip／newline 処理を変更しない。
- 順序検査:
  - 現行 `names != [name for name in ("新規","再発") if name in names]` は、tuple へ末尾要素を加える形でのみ拡張する。
  - `set(names)` や `sorted(names)` に置き換えると重複・原順序を失う。
  - 3 節すべてとの完全一致にすると既存 fragment と supersede 単独が拒否される。
  - 未知名を先に filter すると未知 H2 が黙って落ちる。左辺 `names` は無加工のまま比較する。
- supersede 単独:
  - `names == ["supersede 追記"]` の期待列も同じ 1 要素になるため有効。
  - worklog delta や active T 保存則には入らず、failures と receipt だけを変更する。
- placeholder:
  - selector は raw parser で literal を強制する。
  - 本文は allocation 後に解決し、重複判定も解決後の exact line で行う。
- F entry 境界:
  - target は現行正本 `FAILURE_ID_RE` (`56`) の `### F<n>.` だけとする。
  - 最終 F は EOF、それ以外は次の F heading 直前を末尾とする。H4、fence、本文中の `Fnn` を境界に使わない。
- `FOLDED.md`:
  - receipt field、allocation identity、replay 検査に変更なし。supersede は新 F symbol ではないため allocation を増やさない。
  - after bytes と transaction hash は通常どおり変わるが、receipt format／replay 解釈は変わらない。
- 本作業では pytest を実行していない。上記は静的読解に基づくテスト計画であり、緑は主張しない。

## docs 更新箇所 (親向け)

- `docs/spool/failures/README.md:5`
  - H2 の許可順を `新規` → `再発` → `supersede 追記` に更新し、使う節だけ置けること、supersede 単独が有効であることを書く。
- `docs/spool/failures/README.md:7-30`
  - 例へ `## supersede 追記` と `- F196 - **supersede: 2026-08-10** — ...` を追加する。
- `docs/spool/failures/README.md:38-41`
  - literal `Fnn` selector、1 物理行、本文非空白、H3／`base:`／継続行禁止を追加する。
  - 挿入位置は対象 F 末尾、同一 F では再発→supersede、日付・prefix は書き手、本文 placeholder のみ解決、と明記する。
  - target 不存在、canonical 重複、既存同一行、fold 内同一組を拒否することを書く。
- `docs/spool/README.md:91-92`
  - 「既存 bytes を書き換える」許可集合へ、既存 F エントリ末尾への supersede 1 行挿入を追加する。
- `docs/spool/README.md:101-105`
  - 不変条件の挿入列挙を、F 再発、F supersede 1 行、見送り新規 item、見送り item 先頭行末 suffix に分けて曖昧さをなくす。
- `docs/spool/worklog/README.md` は見送り追記の比較対象として読んだが、文法変更対象ではないため更新不要。
- wave の実 fragment は `docs/failures.md` を直接編集せず、F196 target の failures fragment として作る。現行 stale bytes は `docs/failures.md:4839`、挿入位置は F197 heading (`4843`) の直前。親が `--dry-run` で実 canonical に対する splice を確認する。

## (Pn) への異議

なし。

## 総括

実装は failures parser に第三の任意 H2 と専用 `_FailureSupersede` を加え、既存 recurrence 適用の直後、新規 F 追加の直前に独立した 1 行挿入を置く。既存 `新規`／`再発`、worklog の見送り追記、receipt、transaction は変更せず、P6 の全 7 条件を parser／fold semantic issue に割り当てる。作業ツリーは未変更で、テストは未実走。