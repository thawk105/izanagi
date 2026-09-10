# 段 2 実装プラン — T-352 / T-358

指定資料・対象コード・見送り台帳・5 fragment はすべて読めた。以下は静的調査だけに基づくプランであり、`pegasus02` 上では pytest を実行していない。緑は主張しない。

結論は次のとおり。

- T-352 は `### 完了` item に exact-one の `  remaining: none` を必須化する。`base:` とは別 helper で除去し、canonical には残さない案を推奨する。
- 既存の「残件あり」「一部完了」検査は残す。削除すると、従来の拒否入力を新たに受理する非承認の受理集合拡大になる。
- T-358 は `### 見送り追記` を action 順序の末尾へ追加する。ただし active 遷移用 `_Operation` へ混ぜず、専用 `_DeferredAppend` と専用挿入経路を設ける。
- 見送り追記は fold 開始時点ですでに見送り台帳にある ID だけを対象とする。新規見送りと同じ fold で初めて現れる ID への追記は拒否する。
- failures の `## 再発` と同様、内容重複ではなく transaction state と `FOLDED.md` receipt で冪等性を担保する。

## 現行挙動

### `### 完了` の検査と canonical 反映

現行の処理順は次のとおり。

1. [`tools/spool_fold.py:358–470`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:358) で worklog fragment の H2 を `本文` → `次の一手差分` に限定する。
2. action H3 は [`tools/spool_fold.py:374–381`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:374) の  
   `carry`, `完了`, `更新`, `新規`, `見送り` に限定し、この順序を強制する。
3. `完了` item は、item 継続行の 2-space indent、先頭の既存 T ID を検査した後、[`_strip_base` at tools/spool_fold.py:342–355`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:342) で exact-one の  
   `  base: <64 hex>` を要求し、その行を出力 block から除去する。
4. [`tools/spool_fold.py:467–468`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:467) で、base 除去後の全文に  
   `残件(?:[はが:]|：|[ \t])*あり|一部完了`  
   があれば `completion-remaining` を出す。それ以外は、残件の有無を示す構造 field がなくても受理する。
5. plan 時に [`tools/spool_fold.py:1137–1152`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1137) で対象が現在 active か、`base` が carry を解決した実本文 digest と一致するかを検査する。
6. `完了` の出力 block は [`tools/spool_fold.py:1160–1162`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1160) で active 出力から外れ、`completions` へ移る。
7. [`tools/spool_fold.py:1199–1209`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1199) で、新 worklog entry の「本文」と「次の一手」の間に完了 block が書かれる。`base:` は canonical へ出ない。
8. active 集合は [`tools/spool_fold.py:1093–1115`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1093) の保存則  
   `入力 active − 完了 − 見送り + 新規`  
   と実出力を突き合わせる。

したがって現在は、例えば「初期処置だけ終了。後続作業は明日行う。」も、正しい `base:` さえあれば terminal として受理され、worklog 本文へ移った後に active から消える。

### `_insert_deferred` の現行動作

[`_deferred_region` at tools/spool_fold.py:992–1006`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:992) は、`## 見送り台帳` から `### 裁定・完了記録` の直前までを切り出し、各 H3 category の範囲を得る。

[`_insert_deferred` at tools/spool_fold.py:1212–1227`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1212) は、

- `見送り` action から得た新規 item を category ごとにまとめる
- category 名を辞書順に処理する
- 各 H3 region の末尾、すなわち次の H3 または `裁定・完了記録` の直前へ payload を挿入する
- offset の大きい順に挿入して位置ずれを防ぐ

という処理だけを行う。既存 `[T-NNN]` item の特定・本文末尾への追記は行わない。

## T-352 の設計

### field 契約

推奨契約は以下。

```markdown
- [T-352] 実装と受入を完了した。
  remaining: none
  base: <sha256>
```

- field 名: `remaining`
- exact 書式: `^  remaining: (?P<value>[^\n]+)$`
- cardinality: `### 完了` item ごとにちょうど 1 件
- 閉じた値語彙: ASCII lowercase の `none` のみ
- `None`, `なし`, `0`, `false`, `some`, trailing comment は拒否
- `base:` との行順は検査しない。README の例は `remaining` → `base` とするが、逆順も正例として残す
- `完了` 以外の `更新` / `見送り` に field を要求しない
- schema 名 `izanagi-spool-v1` は変えない。全 fragment の migration を発生させないためである

`terminal: true` より `remaining: none` を推奨する。`完了` H3 自体が terminal を表しているため、追加 field は「残件がない」という不足していた事実を直接表す方がよい。

### `_strip_base` との関係

P4 の「同じ機械可読行の枠」は支持するが、`_strip_base` 自体へ remaining の意味を混ぜる案は採らない。

[`tools/spool_fold.py:342`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:342) の直後に、例えば `_strip_completion_remaining` を追加する。

- `_strip_base` の既存 cardinality・error ID・出力を変更しない
- `完了` のときだけ `_strip_completion_remaining` を呼ぶ
- exact-one かつ値が `none` なら、その行を output block から除く
- 欠落・重複・未知値・不正書式はすべて `completion-remaining-field`
- finding の位置は item 先頭。message は「`完了` item には `  remaining: none` が 1 件必要」とする
- 除去後に既存の禁制語検査を行う

専用 helper に分けることで、既存 `base` gate を不用意に一般化せず、field の適用範囲も `完了` だけに固定できる。

### canonical への反映

推奨は `remaining:` を `base:` と同じ authoring/control metadata として canonical worklog から除去すること。

理由は次のとおり。

- canonical の完了 block と既存テスト出力を変えない
- `base:` と同じく fold 時の受理判定に使う field である
- field を含んだ元 fragment は fold commit の親履歴と receipt の content hash で追跡できる
- canonical に残す場合、後続の worklog 書式へ新しい機械 field を持ち込む別契約が必要になる

ただし「明示的な残件なし宣言を canonical にも可視化したい」という要件を親が優先するなら残す案も可能であり、これは親裁定点とする。

### 禁制語検査

[`tools/spool_fold.py:467–468`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:467) は残す。error ID も `completion-remaining` のままにする。

- 構造 field 欠落・値不正: `completion-remaining-field`
- `remaining: none` と本文の「残件あり」「一部完了」が矛盾: `completion-remaining`

削除すると、現在拒否している「一部完了だが `remaining: none` と書いた」入力が通る。これは T-352 の裁定に含まれない受理集合拡大である。

## T-358 の設計

### fragment 形式

action 順序を次へ拡張する。

```text
carry → 完了 → 更新 → 新規 → 見送り → 見送り追記
```

`見送り追記` は任意。使う場合は 1 item 以上必要とする。

```markdown
### 見送り追記

- [T-058] 2026-08-03 に D125 / D127 / D128 により再発火した。追加裁定なし、記録のみ。
- [T-059] 2026-08-03 に D125 / D127 / D128 により再発火した。真時 action の履行状況は各 worklog 参照。
```

item 契約は以下。

- exact 形: `- [T-NNN] <追記 suffix>`
- `[T-NNN]` は既存の canonical T ID。placeholder は不可
- payload は空不可、1 physical line 限定
- `base:` と category H4 は付けない
- payload 内の通常 placeholder 参照は許し、plan 時に `_replace_placeholders` する
- fold は日付、発火回数、「発火記録:」という語を自動生成・意味検査しない。見送り台帳の慣行を変えないためである

section 名は P5 の `見送り追記` を支持する。`見送り発火記録` は用途を狭く表せるが、fold が発火の意味を検査しない以上、機械操作を正確に表す現名称の方がよい。

### active 遷移からの分離

[`_WorklogDelta` at tools/spool_fold.py:211–215`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:211) を次の概念へ分ける。

- `operations`: `carry`, `完了`, `更新`, `新規`, `見送り`
- `deferred_appends`: `_DeferredAppend(task_id, suffix)`

`見送り追記` を `_Operation` へ入れてはならない。入れると [`_render_next_actions`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1118) の active target 検査や完了・見送り集合へ紛れ、保存則を壊す。

### 既存項目の特定と追記位置

[`_deferred_region`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:992) を使い、`裁定・完了記録` より前の各 H3 region だけを走査する。

- top-level item の先頭だけを `TASK_HEAD_RE` で読む
- `task_id -> item block の末尾改行直前 offset` を作る
- 取り消し線項目、本文中の参照、`裁定・完了記録` 内の ID は対象にしない
- 同一 valid ID が複数 item にあれば `deferred-append-duplicate`
- target がなければ `deferred-append-missing`
- 新しい item を暗黙作成したり、通常の `見送り` に読み替えたりしない

payload は対象 item block の末尾改行直前へ、fragment item の ID を除いた suffix として挿入する。T-058/T-059 のような 1 行 item では行末追記になる。複数行 item なら最後の継続行の末尾となる。新しい継続行は作らない。

新 helper は [`_insert_deferred` at tools/spool_fold.py:1212`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1212) の隣に `_insert_deferred_appends` として置き、既存の新規見送り挿入処理とは分ける。

### 適用順序

[`plan_fold` at tools/spool_fold.py:1484–1496`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1484) は次の順にする。

1. 全 worklog fragment から、決定的 fragment 順・item 順で `deferred_appends` を収集する。
2. placeholder を解決する。
3. fold 開始時点の `phase` に `_insert_deferred_appends` を適用する。
4. その後、既存ループで active 遷移と `_insert_deferred` による新規見送りを処理する。

これにより、追記対象は fold 前から存在する項目に限定される。これは failures が [`tools/spool_fold.py:1502–1512`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1502) で再発を既存 F へ挿入してから新規 F を末尾追加する順序と同じである。

### error ID

- section があるが item 0 件: `deferred-append-empty`
- item が一行の `- [T-NNN] <非空 suffix>` でない: `deferred-append-shape`
- canonical 見送り台帳で target ID が重複: `deferred-append-duplicate`
- fold 開始時点の見送り台帳に target がない: `deferred-append-missing`
- section の重複・未知 H3: 既存 `worklog-actions`
- section 順序違反: 既存 `worklog-action-order`

### failures `## 再発` との対応

既存 failures 経路は、

- [`_failure_symbols` at tools/spool_fold.py:491–551`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:491) で target heading を検査
- [`_failure_parts` at tools/spool_fold.py:1240–1261`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1240) で `(F number, payload)` を抽出
- [`_insert_failure_recurrences` at tools/spool_fold.py:1264–1284`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1264) で既存 F entry の末尾へ挿入
- target 不在・重複を拒否
- `base:` や本文重複検査は持たず、receipt と transaction で exact replay を防止

という構造である。

見送り追記も同じ枠へ載せられる。ただし F は H3 entry 境界、見送りは H3 内の top-level item 境界なので、同じ関数の流用ではなく同型の専用 helper とする。

## fold 不変条件との整合

### 決定性

- fragment 順は [`Fragment.key` at tools/spool_fold.py:89–92`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:89) の `(wave, seq, ledger rank, path)`。
- 同じ target への複数追記は、この fragment 順と item 出現順を保持して連結する。
- target offset への実挿入は offset 降順。
- payload を set 化したり内容順に sort しない。
- fold date 以外に時刻・mtime・directory 列挙順を使わない。

### 冪等性・replay

- 同じ plan を resume した場合、phase が after hash なら再挿入せず skip される。
- 成功後に同じ fragment bytes を戻すと [`receipt-replay` at tools/spool_fold.py:1435–1461`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1435) で拒否される。
- payload が同じでも fragment bytes を意図的に変えたものは新しい記録として扱う。内容 dedup は failures 再発にもなく、fold の冪等性とは別問題である。

### 「既存 bytes 不変」

見送り既存 item への追記は、概念上も実装上も `docs/phase3.md` の既存 entry を書き換える操作である。README の「追記と挿入だけ」という例外列挙へ明記する必要がある。

実装は既存 bytes の削除・並べ替えをせず、item 末尾への suffix 挿入だけに限定するが、これを「canonical は append-only」と報告してはならない。`docs/phase3.md` 全体は transaction target として atomic replace される。

### transaction / resume

[`tools/spool_fold.py:1542–1558`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1542) で、追記後 phase bytes が既存の `docs/phase3.md` target に入る。

- transaction ID は fragment hash と各 target の before/after hash を含む
- state は after bytes 自体も保持する
- [`apply_fold` at tools/spool_fold.py:1702–1789`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1702) が全 target を書く前に before/after/第三状態を先に分類する
- phase だけ書けた中断でも resume は after と認識し、suffix を二重挿入しない
- fragment GC は全 target の after hash 確認後だけ

したがって新しい journal schema や transaction path は不要である。

### active 保存則

`deferred_appends` を `_render_next_actions` へ渡さないため、completed/deferred/new ID 集合は変わらない。見送り追記だけの fragment は全 active itemを暗黙 carry し、出力 active 集合は入力と一致する。

## 5 fragment の実測

`git show worktree-rulings-2026-08-02-e:...-<n>.md` を 5 件すべて読み、action H3 を機械抽出した。

| seq | action H3 |
|---:|---|
| 1 | `更新` |
| 2 | `新規` |
| 3 | `更新` |
| 4 | `更新`, `新規` |
| 5 | `更新` |

5 件すべてに `### 完了` はない。したがって `remaining: none` 必須化では壊れない。`見送り追記` も任意 section なので既存 fragment に追加を要求しない。

ただし、これは新 field に対する互換性の確認であって、各 `base:` が land 時の active 本文と一致することまで保証するものではない。

### 同時 fold の順序前提

追加の重要な静的所見がある。

- `worktree-rulings-2026-08-02-e` の seq 2 が T-357、seq 4 が T-358 を新規作成する。
- T-352 は seq 3 で更新される。
- 本 wave の記録で T-352/T-358 を `完了` にするなら、その fragment は 5 件より後に処理されなければならない。
- `Fragment.key` は `wave` を seq より先に比較するため、本 wave の frontmatter が `dev-wave-fold-rotation-copy` なら `rulings-...` より前となり、T-352 は後続更新が non-active target、T-358 は未作成 target になって fold が失敗する。
- job 名由来の `wave-fold-rotation-copy` なら `rulings-...` より後になる。

コードの sort 規則は変更しない。親は stage 7 fragment の provenance と両立する wave slug を確定し、dry-run で「rulings 5 件 → 本 wave fragment」の順を検査する必要がある。後順を正当に作れない場合、同じ fold で T-352/T-358 を完了扱いにせず、記録方法を再裁定する。

後順が成立する場合、T-352 の `base` は seq 3 の更新後 item、T-358 の `base` は seq 4 で `[T-358]` に解決された新規 item の digest にする。

## file:line 実装手順

1. [`tools/spool_fold.py:201–215`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:201)
   - `_DeferredAppend` を追加。
   - `_WorklogDelta` に `deferred_appends` を追加。
   - active `_Operation` とは分離する。

2. [`tools/spool_fold.py:342–355`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:342)
   - `_strip_completion_remaining` を追加。
   - exact-one、値 `none`、field 除去、`completion-remaining-field` を実装。
   - `_strip_base` の既存契約は変更しない。

3. [`tools/spool_fold.py:374–470`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:374)
   - allowed action の末尾へ `見送り追記`。
   - `完了` item だけ remaining helper を通し、その後に既存禁制語検査。
   - `見送り追記` は専用 branch で exact item 形を検査し、`deferred_appends` へ格納。
   - empty/prefix/multiline を fail-closed にする。

4. [`tools/spool_fold.py:992–1006`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:992) と [`tools/spool_fold.py:1212–1227`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1212)
   - 見送り台帳内の valid top-level T item と末尾 offset を一意に索引する helper。
   - `_insert_deferred_appends` を追加。
   - target 不在・重複、対象範囲、行末挿入、複数 payload 順序を固定。
   - `_insert_deferred` は既存の新規 item 専用のまま残す。

5. [`tools/spool_fold.py:1484–1496`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/spool_fold.py:1484)
   - 全 append を収集・placeholder 解決。
   - original phase への append を先に実施。
   - その後に既存 worklog render と新規見送り挿入。
   - `changes`、transaction、receipt schema は変更しない。

6. [`orchestrator/tests/test_spool_fold.py:118–153`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:118)
   - `_worklog_body` の valid completion に `remaining: none` を自動追加。既存 call site と期待値は変えない。
   - `deferred_appends=()` を追加し、`見送り追記` を末尾生成する。
   - 既存 `test_n18_completion_with_remaining_work_is_rejected` の期待値 `["completion-remaining"]` は維持する。

7. docs は親所有。
   - [`docs/spool/worklog/README.md:29–64`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/docs/spool/worklog/README.md:29): field、action 順序、append item、base 不要、existing-only を追記。
   - [`docs/spool/README.md:75–103`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/docs/spool/README.md:75): fold の操作列挙、不変条件の例外、意味保証の記述を更新。
   - 本 wave fragment の `見送り追記` で T-058/T-059 の D125/D127/D128 発火を自己適用する。`docs/phase3.md` は直接編集しない。

## テスト計画

### 既存被覆

現状の主要被覆は以下。

- base 必須・stale: [`test_spool_fold.py:511–526`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:511)
- placeholder の全 mutation sink 解決: 529–545
- 既存 bytes と新規見送り挿入: 584–598
- second fold no-op / receipt replay: 601–624
- transaction 第三状態 / resume: 665–703
- 決定性と明示 fold date: 706–733
- 禁制語による部分完了拒否: 747–755
- 完了・更新・見送りの sink: 820–839
- active 保存則: 443–454

不足しているのは、構造的完了 field、既存見送り item への追記、対象境界、追記固有の replay/resume である。

### 純増テスト

すべて [`orchestrator/tests/test_spool_fold.py`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/orchestrator/tests/test_spool_fold.py:747) へ追加し、既存 assertion の期待値は変更しない。

| 新テスト | これがないと見逃すこと |
|---|---|
| `test_completion_requires_remaining_none_field` | 禁制語がないだけの完了を従来どおり受理する退行 |
| `test_completion_rejects_non_none_remaining_value` | field を必須にしても語彙を任意文字列へ開く退行 |
| `test_completion_rejects_duplicate_remaining_field` | first/last-wins で矛盾 field を受理する退行 |
| `test_completion_remaining_none_is_stripped_and_order_independent` | metadata の canonical 漏出、または base との不要な順序制約 |
| `test_remaining_field_is_not_required_for_update_or_defer` | 承認外に全 mutation action の受理集合を縮小する退行 |
| `test_deferred_append_updates_exact_item_and_preserves_active` | append を active 遷移に混ぜる、または category 末尾へ新規 item として出す退行 |
| `test_deferred_append_empty_section_is_rejected` | 空 section が receipt だけ残す恒真操作になる退行 |
| `test_deferred_append_multiline_item_is_rejected` | payload から別 item/H3 を注入できる退行 |
| `test_deferred_append_missing_target_is_rejected` | typo ID を黙って捨てる、または暗黙作成する退行 |
| `test_deferred_append_does_not_target_completion_record` | `裁定・完了記録` まで検索範囲を広げる退行 |
| `test_deferred_append_duplicate_canonical_id_is_rejected` | 同じ ID の任意一件を last-wins で選ぶ退行 |
| `test_deferred_append_must_follow_defer_action` | action 順序を未固定にする退行 |
| `test_deferred_append_is_at_item_end_not_category_end` | 対象 item でなく次 item/category 全体の末尾へ追記する退行 |
| `test_deferred_append_resolves_cross_ledger_placeholder` | resolved symbol を raw `{{D:...}}` のまま phase へ漏らす退行 |
| `test_deferred_append_fragment_order_is_deterministic` | filesystem 作成順や payload sort で追記順が変わる退行 |
| `test_deferred_append_cannot_target_new_defer_in_same_fold` | 「既存項目だけ」の境界を外し、操作順依存の受理集合を増やす退行 |
| `test_deferred_append_exact_replay_does_not_duplicate_suffix` | exact fragment 再投入で発火記録が二重化する退行 |
| `test_deferred_append_resume_after_phase_write_is_single_insert` | phase 書込み後の中断 resume で suffix が二重化する退行 |

後段の受入では、親が計算ノードへ dispatch して対象テスト、関連 `test_check_docs.py` / `test_dev_wave_land.py`、受入全走を実行する。さらに、5 fragment と本 wave fragment を含む実 land で rotation が起きることを positive control とし、次を確認する。

- `rotation_path` が計画にある
- fragment 順が rulings 5 件 → 本 wave 記録
- T-058/T-059 の suffix が各 1 回
- T-352/T-358 completion に `remaining: none`
- active 保存則成立
- archive と index 更新
- fragment GC と receipt 追記
- resume/replay 後も二重追記なし

T-347 の plan/blob 照合は加えない。

## 変異候補と単独 kill

### T-352

| gate | 変異 → 赤くなるテスト | 単独性 |
|---|---|---|
| field 必須 | exact-one 検査を削除 → `test_completion_requires_remaining_none_field` | valid ID・indent・base、禁制語なしなので手前の拒否なし |
| 閉語彙 | `none` 比較を任意非空値へ緩和 → `test_completion_rejects_non_none_remaining_value` | `some` は禁制語 regex に一致しない |
| cardinality | `len == 1` を `len >= 1` に緩和 → duplicate test | base は 1 件、remaining だけ 2 件 |
| metadata 除去 | remaining 行の除去を省略 → stripped/order positive | plan 自体は valid、canonical exact assertion だけが赤 |
| 既存語矛盾 | 禁制語 regex を削除 → 既存 `test_n18_completion_with_remaining_work_is_rejected` | helper が valid `remaining: none` と valid base を供給するため、この gate だけが発火点 |
| 適用範囲 | remaining を更新/見送りにも要求 → non-completion positive | valid base・active target だけの単一 operation |

欠落 field と「一部完了」を同じ入力にした候補は、2 gate が同時に赤になるため除外する。invalid base を使う候補も `_strip_base` / `base-mismatch` が先に発火するため除外する。

### T-358

| gate | 変異 → 赤くなるテスト | 単独性 |
|---|---|---|
| action allowlist | `見送り追記` を allowed へ加えない → valid append positive | H2・item・target はすべて valid |
| action order | rank を `見送り` より前へ置く → order test | append と見送りの各 item は単独では valid |
| 非空 section | empty 検査削除 → empty-section test | section は既知で prefix payload もない |
| 一行 shape | continuation を許可 → multiline test | continuation は 2-space indent 済みなので generic indent gate は発火しない |
| target 実在 | missing を `continue` にする → missing-target test | `[T-999]` は canonical 形式の valid ID、placeholder なし |
| ledger 境界 | `裁定・完了記録` まで検索 → completion-record test | T-052 はそこだけに実在し、parse gate はすべて通る |
| target 一意性 | duplicate を last-wins → duplicate-canonical test | `plan_fold` は `check_docs.py` を先に呼ばないため、新 gate だけが拒否理由 |
| item-end offset | category end を使う → exact-position test | 同 category に sibling item を置き、対象を先頭にする |
| existing-only | 新規見送り挿入後に target 解決 → same-fold target test | item は active かつ base valid。拒否理由は fold 前 target 不在だけ |
| placeholder 解決 | `_replace_placeholders` を省略 → cross-ledger test | symbol は同 wave で定義済みなので `symbol-undefined` は発火しない |
| fragment 順 | append を set/sorted/列挙順へ変える → deterministic-order test | 各 fragment は単独 valid、payload 順だけを exact 比較 |
| 保存則分離 | append を `_Operation` へ混ぜる → active-preservation positive | target は見送り T-050 で active operation target ではない。正常案では active 集合が不変 |
| receipt replay | content-sha replay を素通し → replay test | 初回 fold 完了後の exact raw 再投入だけを使う |
| resume | after target を再 render/write → resume single-insert test | state・他 target は正規 before/after、第三状態なし |

一行 shape の変異入力に unindented continuation は使わない。現行の `item-continuation` が先に拒否し、偽 kill になるためである。missing target に malformed/undefined placeholder も使わない。

## 静的波及

- [`tools/check_docs.py:616–667`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/check_docs.py:616) は `validate_spool_tree` を動的 import するため、コード変更なしで新 error ID を main finding へ伝播する。
- 同 checker の [`見送り台帳 ID 検査 at tools/check_docs.py:1380–1456`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/check_docs.py:1380) は top-level item 先頭 ID だけを見る。行末 suffix は ID 集合を変えないため変更不要。
- [`tools/dev_wave_land.py:1196–1219`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1196) は fold engine を動的 importし、[`1439–1455`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1439) で generic target path を apply/stage する。`docs/phase3.md` は既存 target なので変更不要。
- land の rollback は [`tools/dev_wave_land.py:1250–1360`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_wave_land.py:1250) で対象 bytes を snapshot/restore する。suffix 追記も既存枠に入る。
- [`tools/dev_waves/git_state.py:47–50`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-fold-rotation-copy/tools/dev_waves/git_state.py:47) は fold commit の modified path として `docs/phase3.md` をすでに許可する。変更不要。
- `hooks/` には spool grammar や `見送り追記` を読む consumer がない。hook 変更・新 allowlist は不要。
- `orchestrator/tests/test_check_docs.py` の pending worklog fixture は completion を持たず、`test_dev_wave_land.py:1678–1689` の実 fold fixtureも carry のみ。新 field で壊れない。
- `orchestrator/tests/test_dev_waves_fake.py` と git-state 系は fragment path・raw content hash・receipt だけを扱い、action grammar を複製していない。
- rulings command / Skill は fragment producer だが形式を `docs/spool/README.md` へ委譲している。docs 更新以外のコード変更は不要。
- `FOLDED.md` record schema、frontmatter schema、T/D/F allocation、rotation、凍結ソース閉包は変更しない。

## 総括

- 推奨案は `remaining: none` の exact-one 必須化、field の canonical 除去、既存禁制語 gate 維持。
- `見送り追記` は action 末尾、一行 `- [T-NNN] <suffix>`、base/category なし、active 遷移から完全分離する。
- 追記対象は fold 開始時点の見送り台帳にある一意な IDだけ。item 末尾へ挿入し、missing/duplicate は fail-closed。
- failures 再発と同じく、semantic dedup はせず before/after transaction・resume・receipt replay で冪等性を担保する。
- 5 fragment は実測上 `更新` / `新規` だけで、新 field では壊れない。
- 親が裁定すべき細部:
  - field を canonical から除去するか残すか。推奨は除去。
  - 同じ fold で新規見送りになった ID への追記を許すか。推奨は拒否し、既存-only。
  - 行末追記か新しい continuation 行か。T-058/T-059 の慣行に合わせ行末を推奨。
  - stage 7 fragment の wave slug を `rulings-2026-08-02-e` より後に並ぶ provenance-valid 値にできるか。できなければ T-352/T-358 を同時 fold で完了にする記録案は停止・再裁定が必要。