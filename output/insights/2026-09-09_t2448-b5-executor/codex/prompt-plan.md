単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor

必読事項の射影 (読めなければ即停止):
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/brief.md (親の段 1 brief)
- /home/SFC/tanab/.claude/jobs/33fc4cd7/tmp/dev-wave-t2448-b5-executor/rulings-verbatim.md (D95 と D1895 の逐語)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md (凍結済み部分登録。とくに §2.1〜§2.3、§3.3、§4.1〜§4.5、§5.1、§5.3、§7)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md (後継凍結物 1/2。とくに §2.4 の索引別 member 集合と ID lookup の request 形・3 値、§2.5 の erratum)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-record.md (後継凍結物 2/2。16 anchor の DOI・OpenAlex W-ID・著者 A-ID・補助 stream 61 本)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis_b5_search/catalog.py (凍結済み生成器。bytes を変えてはならない)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-search-catalog.json (凍結 catalog。実行器の入力)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/axis1_search/ の parsers.py・runner.py・validator.py・checkpoint.py (軸 1 の先例)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/schemas/axis1_search_page_evidence.schema.json (schema の先例)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/orchestrator/tests/test_axis1_search_runner.py (test の書式の先例)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2448-b5-executor/output/insights/2026-09-08_t2380-b5-closure/probe/ (3 索引の実応答 body と header。fixture の素材候補)

## 役割

あなたは dev-wave 段 2 のプラン起草者である。read-only sandbox なので書込み可能な tmp は無く、pytest は走らせなくてよい (静的検査でよい)。
brief の scope (S1〜S6)・不変条件 1〜6・(P1)〜(P3) に従い、**file:line 粒度の実装プラン**を書く。
対象は軸 B5 の実行器である。凍結 catalog の bytes を変える提案、事前登録 3 文書の bytes を変える提案は禁止である。

## 書くこと

1. `orchestrator/axis_b5_search/parsers.py` の構成。dataclass の field、`parse_arxiv_page` / `parse_openalex_page` / `parse_dblp_page` の
   入出力と、部分登録 §5.1 条件 2・3・4・6 が要求する値 (位置値、宣言総件数、宣言 page size、実要素数、索引固有 work ID の列と重複、
   解釈後クエリ、DBLP の `year` 欠落) をどの field で運ぶか。軸 1 の `parsers.py` と**どこが同じでどこが違うか**を関数単位で書く。
2. `orchestrator/axis_b5_search/preflight.py` の構成を 2 つに分けて書く。
   - registration preflight (network-zero): 部分登録 §5.3 が列挙する「query catalog、canonical template、parser と fixture、schema、実行器」の
     **どの path の bytes を、どの方法で束縛するか**。軸 1 の `validator.verify_registration` (git blob 照合) と、manifest に sha256 を書き込む形の
     どちらを採るかを、理由つきで 1 つ選ぶ。束縛対象 path の**全列挙**を出す (自己参照の禁止に注意 — 束縛表自身の hash を束縛表へ書かない)。
   - live preflight: 閉包登録 1/2 §2.4 (b) の request 形で、OpenAlex 16 / arXiv 1 / DBLP 13 の member について ID lookup を再実施し、
     `収録` / `非収録` / `不達` の 3 値を判定する。判定の分岐条件を索引ごとに凍結文の逐語から写す。member 集合と anchor の主キーを
     **どこに置くか** (実行器のコード内定数か、別の JSON か) を選び、理由を書く。1 件でも `不達`・`非収録` なら軸全体 `未完走` で
     走行を開始しない fail-closed をどの関数が返すかを書く。
3. `orchestrator/axis_b5_search/runner.py` の構成。凍結 catalog の 1 query / 1 control / 1 stream (leaf) を実行し、
   §5.1 の 6 条件を評価して証拠を書く経路。Transport seam の型、host allowlist、retry 上限 3 と backoff 3→6→12 秒、
   索引ごとの page size (arXiv 200 / OpenAlex 200 / DBLP 100) と位置遷移 (start / cursor / f) の実装、
   **catalog に登録されていない URL を組み立てられないこと**をどう構造で保証するか。
   軸 1 の runner が page size・retry・content type を catalog document から読む一方、軸 B5 の catalog は
   bytes 凍結済みでこれらの field を持たない。この差をどう埋めるか (実行器側の定数として凍結文から転記) を具体的に書く。
4. `orchestrator/schemas/` に足す schema file の名前と、定義する object の一覧 (page evidence、live preflight record、
   registration seal record)。draft-07 で書く。軸 1 の schema と重複する定義をどこまで写すか。
5. `orchestrator/tests/fixtures/axis_b5_search/` に置く fixture の一覧。`output/insights/2026-09-08_t2380-b5-closure/probe/` の
   実応答のうちどれをどう使えるか、足りない形 (複数ページ、cursor 連鎖、総件数不一致、実要素数と宣言 page size の食い違い) を
   どう合成するかを書く。**合成 fixture の期待値は凍結文の逐語から独立に導き、fixture を見てから期待値を書かない**こと。
6. `orchestrator/tests/test_axis_b5_search_executor.py` の test 関数一覧 (名前・検査内容・期待値の出所となる凍結文の節)。
   受理の正例と拒否の負例を条件ごとに対で置く。とくに規律 2 に当たる負例 (`meta.per_page` や `@sent` を実要素数の代わりに使うと
   通ってしまう形を拒否する test) を明示する。
7. 凍結文の規則に**曖昧・不足・矛盾**があり、実行器が決定的に振る舞いを決められない箇所を全部列挙する。
   各項目に「凍結文から一意に読める / 読めないので親の erratum 裁定が要る」を付け、読めない項目には推奨の読みを 1 つ添える。
8. 変異 matrix の候補 (実装後に親が事前登録する): 変異位置 (関数・行の目安)、期待する赤 test、単一理由性の懸念。8〜12 件。
9. リスク: `tools/check_docs.py`、`tools/check_ai_provenance.py`、`orchestrator/tests/acceptance_duration_ledger.json`、
   受入の自走 harness 要求に、本 wave の新規 file がどう当たるかを実際に読んで書く。新規 test file が受入で要求するもの
   (自走 harness と所要時間台帳の行) を、既存の作り方を読んで具体的な手順で書く。
10. 段 5 の 2 単位 (A = S1 + S5、B = S2 + S3 + S4) の所有 path を重複なく割る。境界の型を先に固定して書く。

## 禁止

- ファイルを 1 つも書かない・変更しない。git 操作をしない。外部 network を使わない (名前解決も request も禁止)。
- 凍結済み文書 (2026-09-05 / 2026-09-07 / 2026-09-08 の 3 文書) と `catalog.py`、catalog JSON の変更を提案しない。
- 検索語彙・ブロック所属・枝・cutoff・control anchor・補助探索範囲・完走述語を緩める提案をしない (D1895)。
- 本 wave で live preflight を実行する提案をしない (実行は人間の認可事項)。
- 新しい gate・検査・台帳・一般化を、依頼された実行器の外へ足さない。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。
予算が尽きそうなら途中結論をこの形式で書いて終われ (無出力が最悪)。

## parser
## preflight
## runner
## schema
## fixture
## test 一覧
## 曖昧・不足・矛盾
## 変異候補
## リスク
## 所有分割
## 総括
