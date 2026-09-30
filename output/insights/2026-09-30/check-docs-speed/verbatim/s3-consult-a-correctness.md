1. **重大度: high｜[check_docs.py:3019](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3019)**
   **反例:** O2 で `source_ids`（「次の一手」の本文）を sink の ID として再利用すると、次 entry の本文にだけある ID を見落とす。`check_transition` の sink は `sink_entry[1]`、`entry_has_id` も entry 本文なので、この二者は同じ文字列を解析している。一方、`section[0]` は別の文字列である。
   **修正:** entry 本文の ID を entry ごとに一度保持し、sink と `entry_has_id` に渡す。現行 worklog の先頭は [2989 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:2989)の本文結果を、archive 境界は sort 後の `right.entries[0]`、最終境界は `entries[0]` の結果を使う。entry 番号をキーにすると重複番号で取り違えるため、entry の位置に対応付ける。`archive_worklogs` の sort 後も対応が保たれるよう各 archive と共に保持する。

2. **重大度: medium｜[check_docs.py:1381](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1381)**
   **反例:** O1 で改行位置に `bisect_right` を使うと `text="a\nb", offset=1` など境界の扱いを誤る。`offset=-1`、`offset>len(text)` も単純な索引参照では旧 `str.count` とずれる。CR 単独は行数に算入されない。
   **修正:** `\n` の位置だけを索引化し、`end=max(0,min(len(text), offset if offset>=0 else len(text)+offset))` に対して `bisect_left(positions,end)+1` とする。`offset=0`、`len(text)`、空文字列、末尾改行なし、CRLF を含め旧関数と対照する。同じ内容の別 `str` object は値キーの LRU なら結果が等しい。

3. **重大度: medium｜[check_docs.py:1953](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1953)**
   **反例:** O3 で `splitlines()` や LF 専用の `find` に置き換えると、`body="- [T-002] (1)\r  detail"` の digest 範囲が変わる。`body="\n x", item_offset=0` では旧関数は改行から字下げ行末まで返す。末尾改行なし、空の継続行、CRLF も境界条件になる。
   **修正:** [1956–1980 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1956)の `assert 0 <= item_offset < len(body)` を維持し、次の物理行は `\r` と `\n` の早い方で区切り、CRLF を一つの改行として進める。継続条件は先頭の空白またはタブだけで判定し、改行文字を `raw_end` に含めない。`item_offset=len(body)` と空本文は従来どおり assertion 経路にする。

4. **重大度: medium｜[check_docs.py:2536](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:2536)**
   **反例:** O4 で例外を既定値として cache すると、不正 title の `ValueError` が消える。さらに `ARCHIVE_WORKLOG_ENTRY_TITLE_RE` を monkeypatch して同じ title を再評価する内部 API 利用では、title だけをキーにした cache は旧実装と異なる。ただし通常の入力木では同じ title の解析結果は一定であり、例外を保存しない値 cache は等価。
   **修正:** 正常な返り値だけを memo 化し、[2539–2543 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:2539)の `ValueError` を維持する。cache の寿命を一回の `_check_backlog_guard` に限るか、monkeypatch を使うテストでは cache を消去する。

5. **重大度: low｜[check_docs.py:1513](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1513)**
   **根拠:** O5 の条件 `not in_comment and "<!--" not in line` なら、所有外の `_mask_html_comments` は `line` と `False` を返す。空行、CR/CRLF、末尾改行なしでも同じである。fence opener の先行判定も維持される。ただし `_mask_html_comments` 自体を monkeypatch して副作用や別の返り値を観測するテストとは等価でない。
   **修正:** bypass は現行の [1513 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:1513)だけに置き、fence 判定と offset 更新順を変えない。

6. **重大度: medium｜[check_docs.py:2971](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:2971)**
   **反例:** O2 の計算を前倒しして findings の追加処理や archive の走査順も組み替えると、同じ所見集合でも列順が変わる。特に archive 内遷移の所見は [3170–3178 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3170)、archive 間の順序曖昧所見は sort 後の [3180–3208 行](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:3180)に出る。
   **修正:** ID の値だけを事前計算し、`_extract_next_action`、`_validate_next_action_items`、`check_transition`、`_validate_entry_universe` の実行順と早期 return 条件を保つ。`_iter_carry_references` は generator のままにする。[逐次性テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/orchestrator/tests/test_check_docs.py:12015)は最初の `next()` 前に source と item が未消費であることまで観測している。`Path.open` の回数を観測する[既存テスト](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/orchestrator/tests/test_check_docs.py:4756)があるため、読取 cache には触れない。

7. **重大度: medium｜[profile-base-summary.txt](/home/SFC/tanab/.claude/jobs/c8f1db05/wave/profile-base-summary.txt)**
   **根拠:** 72.1 秒は cProfile 下の時間で、brief の Elapse は 78 秒。`stat` 1.4 秒はこの計算ノード・この時点の観測に限られる。P2 の常駐増 200〜400 MB は peak RSS の計測根拠が示されていない。O2 が直接省ける `check_transition` 由来の `_top_level_ids` は profile 上 2008 回・累積 5.3 秒であり、10 秒削減の見積りは強い。各関数の累積時間は重なっているため、O1〜O5 の推定削減を足して 30 秒と断定できない。
   **修正:** E3 で wall と peak RSS を併記し、各 O の効果を段階的に測る。30 秒は目標値として扱う。

8. **重大度: medium｜[check_docs.py:2057](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-check-docs-speed/tools/check_docs.py:2057)**
   **根拠:** profile には `_validate_next_action_items` 累積 13.4 秒、正規表現 `fullmatch` 2043 万回・内部時間 5.2 秒がある。brief の O1〜O5 はこの反復解析を直接扱わない。carry 走査も 95.9 万件あり、O3 後の律速候補である。ただし累積時間を独立の節約可能時間として数えてはいけない。
   **修正:** 今回の範囲を保つなら E3 の新 profile で残余を確認し、次段の候補にする。

9. **重大度: medium｜[brief.md](/home/SFC/tanab/.claude/jobs/c8f1db05/wave/brief.md)**
   **反例:** E1 の故障注入と E2 の既存 fixture だけでは、O1 の負・範囲外 offset、O3 の `item_offset` が改行位置／`len(body)`／空本文、O4 の `ValueError` と module 属性 monkeypatch、O5 の comment 継続直後の行を網羅したとは言えない。E3 は速度検証であって判定不変の証拠ではない。
   **修正:** 新旧の逐語参照実装との対照にこれらの合成入力を追加する。全体比較では rc に加えて stdout 全文を順序込みで照合し、直呼びの `_validate_entry_universe` と逐次 generator テストも通す。

## 総括

- O1: **条件付き採用**。`str.count` の offset 規則を再現する。
- O2: **条件付き採用**。entry 本文の ID を位置で保持し、section 本文と混同しない。
- O3: **条件付き採用**。CR、CRLF と offset 境界の参照実装対照が必要。
- O4: **条件付き採用**。例外を cache せず、cache 寿命を限定する。
- O5: **採用**。現行 masker の値と状態について等価。
- E1〜E3: E1 に境界入力と例外経路、E2 に内部 API 観測テストの確認、E3 に peak RSS と変更後 profile を追加する。