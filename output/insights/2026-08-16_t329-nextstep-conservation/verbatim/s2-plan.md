## 総括

実装対象は指定どおり 2 ファイルだけとする。設計の軸は、既存 archive 本文走査から得た entry 集合を `_check_backlog_guard()` の戻り値で README pass へ渡し、ファイル再読・追加 `glob`・追加 `iterdir` を一切行わないこと。

provisional 裁定は次のように扱う。

- P1 は撤回を推奨する。「4 桁は日付、それ以外は entry」では `worklog-phase1-2.md` を entry 2 と誤認し、将来の entry 1000 以上を日付と誤認する。
- P2 は条件付き採用。正規の単数・範囲行を受理する一方、番号付き archive の README 行が書式外なら免除せず赤にする。免除するのは audit、墓標、番号を名乗らない archive だけ。
- P3 は採用する。全域番号 universe を実体から作り、同一番号が複数箇所にあれば、参照の有無とは別の違反にする。

静的調査では現存 423 archive のうち、後述の位置文法に合う番号付き archive は 414 件、番号を名乗らないものは 9 件だった。pytest、`check_docs.py` は実走していない。ファイル変更もない。

## `tools/check_docs.py` の変更計画

| 現在位置 | 変更 |
|---|---|
| [tools/check_docs.py:757-795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:757) | entry 番号、carry 2 書式、番号付き archive 名、README 範囲行の正規表現を追加する。`WORKLOG_ENTRY_TITLE_RE` の番号を named group にする。 |
| [tools/check_docs.py:788-795](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:788) | `_CarryReference` と `_BacklogCheckResult` を追加する。後者は `numbered_archive_entries: dict[str, frozenset[int] | None]` を持つ。`None` は名前は番号を名乗るが本文入力が利用不能という意味に固定する。 |
| [tools/check_docs.py:1202-1240](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1202) | `_validate_next_action_items()` の戻り値を `list[_CarryReference]` に変える。既存のトップレベル項目ループ内で新旧 carry を抽出し、追加の本文走査を作らない。 |
| [tools/check_docs.py:1242](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1242) | `_archive_filename_entry_range()`、`_entry_number_from_title()`、`_entry_range_delta()`、`_validate_claimed_entry_range()`、`_validate_entry_universe()`、`_validate_archive_readme_claim()` を `_archive_entry_point()` の直前に定義する。 |
| [tools/check_docs.py:1555-1561](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1555) | `_check_backlog_guard()` の戻り値を `_BacklogCheckResult` に変更する。早期終了箇所も空の結果を返し、`None` と空 universe を二義化しない。 |
| [tools/check_docs.py:1643-1666](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1643) | 現行 worklog の既存 entry ループで entry 番号と所在を登録し、変更後の `_validate_next_action_items()` が返す carry を収集する。 |
| [tools/check_docs.py:1689-1761](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1689) | 既存 archive loop の各 path について、読取前に名前の番号主張を純粋関数で解釈する。本文読取後は既存 entry ループ内で実体番号、所在、carry を収集し、ループ末尾で filename 主張と実体を照合する。 |
| [tools/check_docs.py:1761-1771](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1761) | 全 archive 走査後、`_validate_entry_universe()` を一度呼ぶ。重複番号を先に報告し、入力が完全な場合だけ宙吊り carry を報告する。 |
| [tools/check_docs.py:1815](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:1815) | `_BacklogCheckResult` を返す。README へ渡すのは、既に読んだ番号付き archive の実体集合だけ。 |
| [tools/check_docs.py:4971-4976](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:4971) | `backlog_result = _check_backlog_guard(...)` として戻り値を保持する。 |
| [tools/check_docs.py:5009-5027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/tools/check_docs.py:5009) | 既存「現在の収容物」行ループへ `_validate_archive_readme_claim()` を挿入する。`splitlines(keepends=True)` と節の開始 offset から README の正確な行番号を出す。既存到達性検査も同じループで維持する。 |

### Filename の解釈

`_archive_filename_entry_range()` は次の位置文法だけを番号主張とする。

`worklog-phase3-<開始 MMDD>-<lo>[-<hi>].md`

または

`worklog-phase3-<開始 MMDD>-<lo>-<終了 MMDD>-<hi>.md`

entry token は `[1-9][0-9]*` とし、先頭の MMDD slot より後では 4 桁でも entry を優先する。これにより `worklog-phase3-0730-1000.md` は entry 1000 と解釈できる。

次の現存 9 ファイルは正規表現に合わず、構文上「entry 番号を名乗らない」ため除外される。

- `worklog-phase1-2.md`
- `worklog-phase3-0702-0713.md`
- `worklog-phase3-0714-0716.md`
- `worklog-phase3-0717-0718.md`
- `worklog-phase3-0719.md`
- `worklog-phase3-0720.md`
- `worklog-phase3-0721-0722.md`
- `worklog-phase3-0722-0724.md`
- `worklog-phase3-0725.md`

ファイル名 allowlist は持たない。番号を名乗らない archive は実体番号を universe に入れず、その内部の carry も検査対象にしない。したがって、旧 archive のローカル `(1)` が全域 entry 1 の実在証明になることもない。

番号付き archive 内に番号なし、または `(続き)` の H2 があれば別 finding にする。実体集合から黙って捨てると、番号付き本文に余分な entry を挿入できるためである。

### Carry 参照と universe

`_validate_next_action_items()` の既存トップレベル項目ループで、次の full-match だけを carry とする。

- 新書式: `[T-NNN] (N)`
- 旧書式: `[T-NNN] 変わらず ((N) 参照)`

収集値は path、行番号、task ID、参照先番号。universe の所在表は `dict[int, list[str]]` とし、次を登録する。

- 現行 worklog の全 entry 番号
- 番号を名乗る archive の全実体 entry 番号

同じ番号の所在が 2 件以上なら、集合化して隠さず次の別種の赤にする。

`docs/worklog.md / docs/archive: 全域 entry 番号 (115) が複数箇所に実在 — <path:line>, <path:line>`

重複番号は universe 上「存在」はしているため、その番号を指す carry に宙吊り finding は重ねない。

参照先がない場合の文言は次で固定する。

`<path>:<line>: [T-NNN] の carry 参照先 entry (N) が全域番号 universe に実在しない — 宙吊り参照`

番号付き archive の読取・構造抽出が一つでも失敗した場合、存在しないとは断定しない。既存の入力エラーに加え、

`docs/archive: 番号付き archive 入力が不完全 — carry 参照先の実在検査を停止`

を一度だけ出す。番号を名乗らない archive の読取失敗は universe の完全性には影響させない。

### Archive の主張と実体

実体集合は entry title の数字 group から作る。filename と README はそれぞれ独立に同じ実体集合と比較する。

README は次を受理する。

- 単数: ``- `<name>` — worklog の YYYY-MM-DD (N) 分``
- 範囲: ``- `<name>` — worklog の YYYY-MM-DD (lo) 〜 (hi) 分``
- 範囲: ``- `<name>` — worklog の YYYY-MM-DD (lo)〜YYYY-MM-DD (hi) 分``

`〜` 前後の空白、同日での第 2 日付省略、`分` 後の注記を許容する。番号付き filename が掲載されているのにこの full-match に失敗した場合は、

`docs/archive/README.md:<line>: 番号付き archive <name> の「現在の収容物」行から entry 範囲を抽出できない`

とする。audit、`git-history-only` 墓標、番号を名乗らない worklog は対象外。

比較は巨大な `set(range(lo, hi + 1))` を作らない。実体番号の sort から欠番区間を走査し、範囲外番号も抽出する。成功条件は次の全て。

- `lo <= hi`
- 範囲外番号がない
- 範囲内実体数が `hi - lo + 1`
- 隣接差から得た欠番区間がない

文言は主張元を区別する。

- `<archive path>: filename が名乗る entry 範囲 (10)〜(12) と実体 entry 集合が不一致 — 欠番=11, 範囲外=なし`
- `docs/archive/README.md:<line>: <name> が名乗る entry 範囲 (10)〜(12) と実体 entry 集合が不一致 — 欠番=11, 範囲外=なし`

これにより実体 `{10, 12}` は、min/max が一致しても必ず赤になる。

### I/O と計算量

新しい I/O 呼び出しは追加しない。

- archive filename と本文の検査は既存 `ARCHIVE_DIR.glob("worklog-*.md")` と `_safe_read_text()` の loop 内。
- entry 番号と carry は既存 entry loop 内で収集。
- README は既存 `_safe_read_text(ARCHIVE_README)` と「現在の収容物」行 loop 内。
- 2 pass 間は `_BacklogCheckResult` のメモリ値で接続。
- 新しい `glob`、`iterdir`、`read_text`、`open`、`stat` は禁止。
- 欠番検出は実体 entry 数に比例させ、filename の誤った巨大上限に比例させない。

## `orchestrator/tests/test_check_docs.py` の変更計画

### Fixture

[orchestrator/tests/test_check_docs.py:565-570](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:565) の `_archive_readme()` は既存非採番 fixture 用として維持する。その直後に、日付、lo、hi、任意の終了日を受けて canonical README 行を作る `_numbered_archive_claim_line()` を追加する。

[orchestrator/tests/test_check_docs.py:875-943](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:875) の baseline は変更しない。`_PLACEHOLDER_ARCHIVE_NAME` は日付だけの名前なので、内部のローカル番号や README の bare 行は新検査対象外になる。

### 既存 synthetic archive への波及

`grep` で得た `_archive_readme()` 呼び出しは次のとおり。期待値緩和や skip は行わない。

| 既存箇所 | 処置 |
|---|---|
| `_build_min_repo` 911 | `worklog-phase3-0722-0724.md` は番号を名乗らないため構文除外。変更なし。 |
| `test_placeholder_guard_entry_rotation_keeps_ledger_green` 4386、4404 | `worklog-rotation-prelude.md`、`worklog-rotation-new.md` は番号主張なし。変更なし。 |
| `test_safe_reader_dependency_failures_do_not_emit_derived_findings` 4800、4833、4867 | `worklog-archive-*.md` は番号主張なし。読取不能な旧 archive も universe を不完全にしない。変更なし。 |
| `test_backlog_guard_checks_latest_archive_rotation_boundary` 8722 | `worklog-synthetic-latest.md` は番号主張なし。変更なし。 |
| `test_backlog_guard_checks_archive_internal_transitions` 8761 | `worklog-synthetic.md` は番号主張なし。変更なし。 |
| `test_backlog_guard_id_bearing_archive_entry_requires_ids_on_all_items` 8800 | 同上。変更なし。 |
| `test_backlog_guard_checks_boundaries_between_all_archives` 8848 | `worklog-first.md`、`worklog-second.md` は番号主張なし。変更なし。 |
| `test_backlog_guard_latest_archive_is_selected_by_entry_date` 8889 | `worklog-zz-older.md`、`worklog-aa-newer.md` は番号主張なし。変更なし。 |
| `test_backlog_guard_same_day_archives_use_entry_ordinal_not_filename` 8935 | `worklog-z-early.md`、`worklog-a-late.md` は番号主張なし。変更なし。 |
| `test_backlog_guard_ambiguous_same_day_archive_order_is_violation` 8972 | `worklog-a.md`、`worklog-z.md` は番号主張なし。変更なし。 |
| `test_backlog_guard_latest_archive_structure_is_fail_closed` 9010 | `worklog-synthetic-latest.md` は番号主張なし。既存構造エラーだけを維持。 |

直接 archive を作る placeholder 系も、`worklog-new.md`、`worklog-h2-collision.md`、`worklog-tab-scope-replay.md` または日付だけの placeholder なので構文除外する。これには 4550〜4590 行付近のテストも含まれるが、その本文は表示・変更しない。symlink / FIFO 系も同じく fixture 修正不要で、派生した範囲不一致を追加しない。

### 新規テスト

配置は carry 系を [test_check_docs.py:8441-8560](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:8441)、archive 範囲系を [test_check_docs.py:8984-9016](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:8984) の直後とする。

1. `test_backlog_guard_carry_reference_existing_in_current_is_clean`

   新旧 2 書式を parameterize し、current entry 1 を参照させる。両方 rc=0。

2. `test_backlog_guard_numbered_archive_entry_is_carry_target`

   `worklog-phase3-0730-1000.md`、実体 `(1000)`、README `(1000) 分` を作り、current の新書式 carry から 1000 を参照する。4 桁 entry を日付扱いしない正例にもする。

3. `test_backlog_guard_dangling_carry_reference_is_violation`

   新旧 2 書式で存在しない 999 を参照し、path、task ID、`(999)`、`宙吊り参照` を assert する。

4. `test_backlog_guard_unnumbered_archive_carry_is_out_of_scope`

   日付だけの archive 内に存在しない参照を置き、既存 D70 境界 sink は満たす。carry finding が出ないことを正例として固定する。

5. `test_backlog_guard_duplicate_global_entry_number_is_violation`

   current entry 1 と番号付き archive entry 1 を併存させ、重複診断が両方の `path:line` を含むことを assert する。carry の宙吊り診断は期待しない。

6. `test_archive_claims_accept_single_and_cross_date_ranges`

   単数形と、`0730-1001-0731-1003` の連続 `{1001,1002,1003}` を同時に置く。README は空白あり・なしと第 2 日付ありを使い、rc=0。

7. `test_archive_filename_and_readme_reject_interior_gap`

   filename と README がともに 10〜12、実体が `{10,12}` の fixture。両主張元の finding と `欠番=11` を assert し、min/max だけの実装を殺す。

8. `test_archive_readme_range_must_match_actual_set`

   filename と実体は `{10,11,12}` で一致、README だけ 10〜11 とする。README finding の `範囲外=12` を assert し、filename finding が出ないことも確認する。

9. `test_numbered_archive_readme_requires_range_syntax`

   番号付き archive を bare ``- `<name>` `` 行で掲載し、「範囲を抽出できない」が出ることを確認する。P2 を無条件除外として実装する逃げ道を塞ぐ。

10. `test_numbered_archive_rejects_entry_without_global_number`

    範囲が正しい数字 entry に加えて `(続き)` H2 を入れ、番号付き archive 内の無番号 entry 診断を確認する。

[既存 N21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t329-nextstep-conservation/orchestrator/tests/test_check_docs.py:1923) は変更しない。既存 D70 の暗黙脱落と、新しい carry / archive 主張検査は別理由なので一つのテストへ束ねない。

## 変異で固定すべき失敗面

段 4 の事前登録候補は少なくとも次の独立変異に分ける。

- 新書式または旧書式の片方だけ抽出しない。
- universe から current または archive を落とす。
- 番号重複を set 化して黙殺する。
- 4 桁 entry を日付として除外する。
- 番号を名乗らない archive の carry を誤って検査する。
- filename を min/max だけで照合し、内部欠番を見逃す。
- README を min/max だけで照合する。
- 番号付き archive の malformed README 行を対象外にする。
- README pass で archive 本文を再読する。

受入時は直接 pytest を起動せず、リポジトリ規律どおり `tools/run_tests.py` 経由で対象テストを実走し、その後 `tools/check_codex_agents.py` と `tools/check_docs.py` を確認する。現段階ではいずれも未実走である。