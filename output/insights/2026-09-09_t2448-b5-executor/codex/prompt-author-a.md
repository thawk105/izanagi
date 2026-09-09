単独段 dispatch: stage=author; sandbox=workspace-write; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-a

**あなたの編集対象 repository は `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-a` である。**
他の worktree の path を書き換えてはならない。

必読事項の射影 (読めなければ即停止):
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/brief.md (親の段 1 brief)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-stage4.md (**親の段 4 裁定。実装契約の正本**)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/parent-measurements.md (親が実測した応答 header の事実)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-a/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md (部分登録。§2.2、§3、§5.1 が入力)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-a/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md (閉包登録 1/2。§2.4)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-a/orchestrator/axis1_search/parsers.py (**写経元として読むだけ。import してはならない**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-a/output/insights/2026-09-08_t2380-b5-closure/probe/ (3 索引の実応答 body と header。fixture の素材)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-unit-a/orchestrator/tests/test_plain_runner_coverage.py (新規 test file の自走 harness 契約)

## 役割

あなたは dev-wave 段 5 の実装子 (単位 A) である。軸 B5 文献調査実行器の **parser と fixture と parser test** を書く。

## 所有 path (これ以外を編集してはならない)

- `orchestrator/axis_b5_search/parsers.py` (新規)
- `orchestrator/tests/fixtures/axis_b5_search/**` (新規)
- `orchestrator/tests/test_axis_b5_search_parsers.py` (新規)

**編集してはならないもの:** docs 配下の全て、`orchestrator/axis_b5_search/catalog.py`、`__init__.py`、
`docs/related-work/claim-survey/*.json`、`orchestrator/axis1_search/**`、`orchestrator/tests/acceptance_duration_ledger.json`、
その他の既存 file。**commit してはならない。** git 操作をしてはならない。外部 network を使ってはならない。

## 実装契約 (親の段 4 裁定より。逐語で守る)

1. **軸 1 の parser を import しない。** 写経元として読むだけ。理由は 2 つあり、どちらも親が現物で確認済みである。
   - 軸 1 は次位置を `start + len(entries)` で作る (`orchestrator/axis1_search/parsers.py:189-191`) が、軸 B5 は固定 step を要求する。
   - 軸 1 の `FROZEN_PREDECESSOR_PATHS` (`orchestrator/axis1_search/validator.py:19-23`) に parser は入っていないので、
     import すると軸 B5 の seal が捕まえられない未束縛依存になる。
2. **parser は次位置を計算しない。** offset 系 (arXiv / DBLP) の次位置は runner が固定 step で決める。
   parser が `position + len(elements)` のような値を作ってはならない。
   OpenAlex だけは応答の `meta.next_cursor` をそのまま `next_cursor` field で運ぶ (加工しない。不在は `None`)。
3. **実要素数 (`actual_count`) は container の要素数だけで数える。**
   arXiv = `feed/entry` の個数、OpenAlex = `results` の個数、DBLP = `result/hits/hit` の個数。
   `itemsPerPage` / `meta.per_page` / `@sent` は `capacity_echo` という**別 field に記録するだけ**で、
   実要素数の代用にしてはならず、判定にも使ってはならない。
4. **重複を消さない。** 索引固有 work ID が page 内・page 間で重複しても occurrence を 1 件も落とさない。
   `occurrences` は順序つきの列で、`page_number` と `ordinal` を持つ。
5. **DBLP の cutoff。** 部分登録 §2.2 に従い、`year` を解釈して次を**別 field**で持つ。
   - `year` が 4 桁で `<= 2026`: 取得集合に採る
   - `year` が 4 桁で `> 2026`: 取得集合の外 (cutoff 外)
   - `year` が欠落または 4 桁でない: **除外せず `要裁定`**
   raw の値は必ず保存する。record を 1 件も消さない。
6. **解釈後クエリ。** 生文字列を `interpreted_query_text` に保存する。
   OpenAlex は加えて `meta.x_query.oqo` の構造を `interpreted_query_ast` として、
   **key の重複・未知の型を落とさずに**運ぶ (同一 object 内に重複 key があればそれを検出できる形で読む)。
   parser は AST の比較をしない (比較は runner の仕事)。
7. **parse error は文字列 code の列** (`parse_errors`) で返し、例外で落とさない。
   code は安定した snake_case とし、test が literal で照合できるようにする。

## fixture の作り方

`orchestrator/tests/fixtures/axis_b5_search/` に置く。次を必ず含める。

- **実応答をそのまま複製したもの** (出所を fixture の file 名か添え書きで示す):
  arXiv の命中応答 (`probe/ax_known.body`)、arXiv の不在応答 (`probe/ax_missing.body`)、
  OpenAlex の命中応答 (`probe/oa_ccbench.body`)、OpenAlex の 404 応答 (`probe/oa_missing.body`)、
  DBLP の anti-bot challenge HTML (`probe/dblp_api_doi.body`)。
- **合成したもの** (小さく作る。索引ごとに必要な形だけ):
  非最終の満杯 page、非最終の短い page、最終 page、page 内重複、page 間重複、
  総件数 field の欠落、DBLP の `year` 欠落、DBLP の `year` が 2027 (cutoff 外)、
  OpenAlex の cursor 連鎖 2 page と `next_cursor` が null の終端。

**合成 fixture の期待値は、fixture を見てから書いてはならない。**
期待件数・期待 ID・期待 code は凍結文の逐語か、あなたが先に決めた設計値から導き、fixture をそれに合わせて作る。
**fixture の `len()` や parser の出力を test の期待値にしてはならない。**
**現行 hash を fixture へ差し込んで緑にしてはならない。**
**揮発する payload (working tree の hash、時刻、host 名) を期待値へ焼き込んではならない。**

## test の作り方

`orchestrator/tests/test_axis_b5_search_parsers.py` に書く。

- 受理の正例と拒否の負例を、上の契約 1〜7 それぞれについて対で置く。
- **規律 2 の負例を必ず置く:** `capacity_echo` を実要素数の代わりに使うと通ってしまう入力が、
  `actual_count` では正しく数えられることを示す test。
- 末尾に自走 harness を置く: `if __name__ == "__main__": raise SystemExit(pytest.main([__file__]))`
- 期待値は凍結文由来の独立 literal で書く。production 関数の出力から期待値を作らない。

## 実走と報告

- **緑を主張するときは実走した nodeid と範囲を必ず併記する。** 実走できなかったものは
  「実装済み・未実走」と書き、`closed` と申告しない。
- 新規 test file を作ったので、`orchestrator/tests/test_plain_runner_coverage.py` の制約 meta-test も
  自分で洗い出して走らせる。他にも新規 file に効く meta-test が無いか自分で探して走らせる。
- test は `python3 -m pytest` ではなく、この repo の作法に従って走らせる。走らせ方が分からない場合は
  `PYTHONPATH=. python3 orchestrator/tests/test_axis_b5_search_parsers.py` の自走 harness を使ってよい。
- 完了報告に、**所有外の caller・共有 fixture・consumer test への波及可能性**を静的に列挙する。
- 指示外の受理集合の変更をしない。変更が要ると判断したら実装せず報告に書く。

## 親へ返すもの (次の単位 B が使う)

完了報告に次を**表で**書く。単位 B はこれを唯一の境界契約として実装する。

1. dataclass の名前と全 field (名前・型・意味)。
2. parse error code の全一覧。
3. 公開関数の signature (`parse_arxiv_page` / `parse_openalex_page` / `parse_dblp_page`)。
4. fixture の path 一覧と、各 fixture が表す形。

## 禁止

- 出力に結合文字 U+0300〜U+036F を使わない。
- 新しい gate・検査・台帳・一般化を、上の所有 path の外へ足さない。
- 検索語彙・ブロック所属・枝・cutoff・完走述語を緩めない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
予算が尽きそうなら途中結論をこの形式で書いて終われ (無出力が最悪)。

## 実装した内容
## 境界契約 (単位 B へ渡す表)
## 実走した test
## 波及可能性
## 未実走・未実装
## 総括
