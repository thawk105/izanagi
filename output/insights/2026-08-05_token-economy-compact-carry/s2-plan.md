## 総括

- 採用案は P1′ `- [T-NNN] (N)`。P1 は regex を全て通るが、既存の ID 単独実体項目との衝突と直前関係の再構成が危険。
- 末尾 237 carry 行は 9,006 → 3,792 bytes、今後の新規エントリごとに 5,214 bytes 削減。
- P1 の削減は 6,399 でなく 6,636 bytes。P1′の親見積 5,214 bytes は正しい。
- 最大の危険は、新 carry の認識漏れが stub 自身の digest へ fail-open し、`base-mismatch` を意味的に恒真化する経路。

## 1. P1 / P1′の判定

ID 単独行は、指定された全抽出面を現行のまま通る。

`check_docs.py` の regex は次のとおり。

```python
TOP_LEVEL_ITEM_RE = re.compile(
    r"^(?:[1-9][0-9]*\.|-)[ \t]+(?P<text>[^\n]*)$", re.MULTILINE
)
TASK_ID_AT_HEAD_RE = re.compile(
    rf"^(?P<id>{TASK_ID_PATTERN})(?=$|[ \t])"
)
```

- list marker を除いた `item_text == "[T-NNN]"` に対し、末尾の `(?=$|[ \t])` は `$` で成功する。[tools/check_docs.py:518-526](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:518)
- source は `### 次の一手` に対する `_top_level_ids()` で抽出される。[tools/check_docs.py:1464-1469](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:1464)
- sink も後続 entry 全体に同じ `_top_level_ids()` を使う。[tools/check_docs.py:1489-1498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:1489)
- 最新 entry の ID 完備性検査も同じ regex なので通る。[tools/check_docs.py:1034-1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/check_docs.py:1034)

`spool_fold.py` も通る。

```python
TASK_HEAD_RE = re.compile(
    r"^(?:- |[1-9][0-9]*\. )(?P<id>...)(?=$|[ \t])"
)
```

- `_split_top_items()` の `r"^(?:- |[1-9][0-9]*\. ).+$"` は ID 部分があるため ID 単独行を抽出する。[tools/spool_fold.py:312-319](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:312)
- block は末尾 LF 付きだが、Python の `$` は終端 LF の直前でも成立するため `TASK_HEAD_RE.match()` が成功する。[tools/spool_fold.py:34-38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:34)
- `_entry_active_items()` はその match 結果をそのまま `_TaskItem` にする。[tools/spool_fold.py:1004-1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1004)

したがって「regex を通らないため P1 却下」という条件は成立しない。それでも総合判断では P1′を採る。

理由は、現行では ID 単独 item は `carry_re` に一致せず、実体 item として digest されるからである。[tools/spool_fold.py:1151-1164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1151) P1 はこの既存受理形を carry に再分類する。P1′が予約するのは「ID + 正整数括弧だけ」という狭い形で、衝突面が小さい。

さらに `_global_ordinal_entries()` は欠番・最大 ordinal・ordinal 単調性を固定していない。[tools/spool_fold.py:1110-1112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1110) P1 では archive/current を跨ぐ「直前」を新たに再構成する必要があるが、P1′は生成時の実 `prior_ordinal` を保持する。P1より 1,422 bytes/entry 削減が減るものの、品質優先では妥当な交換である。

## 2. 実装プラン

### carry の生成

[tools/spool_fold.py:1338-1341](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1338) を次の意味へ変更する。

```python
block = f"- {item.task_id} ({prior_ordinal})\n"
```

`prior_ordinal` の引数・更新方法は維持する。`check_docs.py` の本体は変更しない。

### 新旧 carry の認識

[tools/spool_fold.py:1151-1155](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1151) の `carry_re` を、旧形と compact 形の完全一致二択にする。

```python
carry_re = re.compile(
    r"^- (?P<id>\[T-(?:0(?:0[1-9]|[1-9][0-9])|[1-9][0-9]{2,})\]) "
    r"(?:変わらず \(\((?P<legacy_ordinal>[1-9][0-9]*)\) 参照\)"
    r"|\((?P<compact_ordinal>[1-9][0-9]*)\))\n$"
)
```

旧書式側の受理形は一字も狭めない。既存 worklog/archive は書き換えず、そのまま再帰解決可能にする。

### substantive digest

[tools/spool_fold.py:1156-1168](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1156) は次の順序を固定する。

1. `carry_re.fullmatch(item.block)` が `None` の場合だけ実体 item として `_task_item_digest(item.block)` を返す。
2. carry の場合は `legacy_ordinal` / `compact_ordinal` のちょうど一方を選ぶ。両方または両方なしは例外にし、既定 ordinal を補わない。
3. `items_for()` の missing entry、参照先での missing task、循環、現在・未来参照の例外をそのまま伝播する。
4. 再帰中の例外を捕捉して stub digest へ戻す処理は置かない。

`_extract_latest_active()` が全 active item に解決済み digest を付ける [tools/spool_fold.py:1170-1173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1170) 契約と、連続 fragment 間でその digest を渡す [tools/spool_fold.py:1338-1363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1338) 契約は維持する。

## 3. fail-open 検査点

- **認識漏れ:** compact 行が `carry_re` に一致しないと、[tools/spool_fold.py:1162-1164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1162) から stub digest を返してしまう。生成→再読の round-trip と混在 chain を byte-exact に固定する。
- **entry 不在:** [tools/spool_fold.py:1142-1145](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1142) の `carry-reference` を捕捉・救済しない。
- **task 不在:** [tools/spool_fold.py:1159-1161](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1159) を stub digest へ退避させない。
- **循環・未来参照:** [tools/spool_fold.py:1157-1158](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1157) と [tools/spool_fold.py:1165-1167](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1165) を新旧双方へ共通適用する。
- **base-mismatch:** [tools/spool_fold.py:1335-1337](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1335) 自体は恒真ではない。だが resolver が stub digest を返すと、stub から作った `base:` が自己一致して意味的に恒真化する。実体 digest は受理、compact stub digest は `base-mismatch`、未解決参照はそれ以前に `carry-reference`、の三点を独立に固定する。

## 4. rotation・ordinal・複数 fragment

- **archive 跨ぎ:** archive 群は resolver より先に読み込まれ [tools/spool_fold.py:1723-1741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1723)、明示 ordinal で辞書検索される。rotation は全 entry 描画後に行われるため [tools/spool_fold.py:1849-1856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1849)、参照先が archive へ移っても P1′の値は変わらない。
- **ordinal 非連続:** `prior_ordinal` は現行末尾の実 ordinal、次の entry 番号は全履歴の最大値 + 1 で別々に計算される。[tools/spool_fold.py:1792-1796](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1792) P1′は前者を行内へ書くため、`ordinal - 1` を仮定しない。
- **同一 fold 内の連続 entry:** 各 worklog fragment の描画後に `prior_ordinal = ordinal` となる。[tools/spool_fold.py:1797-1812](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1797) よって第1 entry は fold 前末尾、第2 entry は第1 entryを指す。active の substantive digest も in-memory で次 fragmentへ渡る。
- **rotation が同一 fold の2 entry間を分断する場合:** 第1 entry が archive、第2 entry が current に残っても、明示 ordinal と archive 全読みにより次回 fold で解決できる。専用回帰を追加する。

## 5. テスト計画

既存期待値を compact の完全一致へ更新・強化する nodeid:

- `orchestrator/tests/test_spool_fold.py::test_n08_all_carries_preserve_order_and_count`
- `orchestrator/tests/test_spool_fold.py::test_implicit_and_explicit_carry_render_identically`
- `orchestrator/tests/test_spool_fold.py::test_parallel_fold_implicitly_carries_task_added_by_earlier_wave`
- `orchestrator/tests/test_spool_fold.py::test_deferred_append_only_fragment_preserves_all_active_tasks`
- `orchestrator/tests/test_spool_fold.py::test_real_worklog_105_to_106_next_action_is_byte_exact_golden`

最後の real-data golden は比較を緩めない。凍結された (106) の旧 carry 行だけをテスト側の独立 regex で compact 化し、置換件数を固定したうえで全 section の byte equality を維持する。

旧書式入力を持つ以下は書き換えず、後方互換性の防壁として残す。

- `::test_global_carry_resolves_global_entry_not_legacy_collision`
- `::test_global_carry_cannot_fall_back_to_legacy_only_target`
- `::test_n37_real_repo_canonical_family_requires_archive_active_history`

新設する回帰 nodeid:

- `::test_id_only_item_remains_substantive_under_compact_carry_format`
- `::test_compact_and_legacy_carry_chain_resolves_substantive_base`
- `::test_compact_carry_missing_entry_rejects_before_stub_digest`
- `::test_compact_carry_missing_task_rejects_before_stub_digest`
- `::test_compact_carry_future_or_self_reference_is_rejected`
- `::test_compact_stub_digest_cannot_satisfy_mutating_base`
- `::test_compact_carry_crosses_rotation_archive_boundary`
- `::test_compact_carry_uses_explicit_prior_across_ordinal_gap`
- `::test_two_worklog_fragments_use_immediate_prior_ordinals`
- `::test_rotation_between_two_new_entries_preserves_compact_chain`
- `orchestrator/tests/test_check_docs.py::test_backlog_guard_id_only_item_is_source_and_sink`

変異では「compact 分岐削除」「旧分岐削除」「再帰例外を stub digest へ変換」「`ordinal - 1` 使用」「[tools/spool_fold.py:1811](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/tools/spool_fold.py:1811) の更新削除」「旧 producer 書式へ戻す」を個別に kill する。

## 6. docs 追随

[docs/worklog.md:12-27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:12) は、有効 ID literal を使わず次の文面へ変更する。

```markdown
エントリ番号・日付・carry 行 `- [T-NNN] (N)` の N・ローテーションはすべて fold が付ける。
```

```markdown
- 論文素材になる段落は行頭に「素材:」を付ける。持ち越しは逐語再掲せず
  `- [T-NNN] (N)` とする。N は fold 時点の直前エントリの ordinal である。
  過去の `- [T-NNN] 変わらず ((N) 参照)` は凍結した旧書式として引き続き解決する
```

併せて、現役の形式正本も同期する。

- [docs/spool/README.md:84-89](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/spool/README.md:84): fold の生成形を compact へ変更。
- [docs/spool/worklog/README.md:81-88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/spool/worklog/README.md:81): stub例、substantive digest説明、Nの所有者を新旧混在契約へ変更。
- `docs/decisions.md` と `docs/failures.md` に残る旧書式の事故・決定記録は歴史記録なので変更しない。

## 7. 削減量の再実測

`docs/worklog.md` は 98,391 bytes。完全一致する旧 carry 行は実際には **1,671 行 / 63,498 bytes**で、全行が38 bytesだった。

brief の **1,673行 / 63,764 bytes** は、旧 carry 行に加えて書式説明の [docs/worklog.md:18](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:18) 121 bytes と [docs/worklog.md:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-token-economy/docs/worklog.md:26) 145 bytesも「変わらず」の部分一致で数えた値である。差は正確に2行 / 266 bytes。

末尾 entry は exact carry **237行 / 9,006 bytes**で、ここは親実測どおり。

- 旧: `- [T-316] 変わらず ((181) 参照)\n` = 38 bytes
- P1: `- [T-316]\n` = 10 bytes、28 × 237 = **6,636 bytes削減**
- P1′: `- [T-316] (181)\n` = 16 bytes、22 × 237 = **5,214 bytes削減**

採用する P1′では carry 部が 9,006 → 3,792 bytesになる。過去 entry は凍結するため既存ファイルの即時削減は0で、今後、同程度の active 件数を持つ各新規 entryで5,214 bytesずつ増分を抑える。

read-only のため実装・pytest・`check_docs.py` 実走は行っておらず、テスト緑は主張しない。