単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/brief.md (親の段 1 brief。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/9218ced6/tmp/t2380/artifacts/dev-wave-t2380-b5-successor-freeze/plan.md (段 2 の plan。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-08-backoff-axis-b5-closure-preregistration.md (親が起草中の後継凍結物 1/2 の草稿。未 commit。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/docs/related-work/claim-survey/2026-09-07-backoff-axis-b5-search-preregistration.md (凍結済み部分登録。§3、§4.1、§4.5、§5.1 が生成器と 3 経路の入力。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/orchestrator/axis1_search/catalog.py (先例。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2380-b5-successor-freeze/tools/check_docs.py と tools/check_ai_provenance.py (docs / JSON 追加が引っかかる lint と実装面判定。該当箇所を grep で引く。読めなければ即停止)

## 役割 — レンズ B: 整合と実効性

あなたは dev-wave 段 3 の敵対相談者である。**plan と親 brief と草稿を守らず、攻撃する。** 親 brief 自身も検査対象である。
read-only sandbox なので pytest は走らせなくてよい (静的検査でよい)。外部 network は使わない。

攻撃すること (各所見に real か refuted かの自己判定と、根拠の file:line または節番号を付ける):

1. **plan の生成器設計が部分登録 §3.1〜§3.5・§4.1・§4.5 の規則と 1 箇所でも食い違う点** を、規則の逐語と plan の該当行を並べて挙げよ。
   特に: 語順 (§3.1 の列挙順、辞書順でない)、block 順 (§3.2 の論理式の順)、percent encoding の safe 集合 (`A-Z a-z 0-9 - _ . ~` だけ、`,` は filter の区切りなので符号化しない)、
   DBLP の `q=` の扱い (規則 5 の出力に `q=` を含めない、語内空白は `%20`、ハイフンはそのまま)、`{POS}` / `{CUR}` の literal、初回 `cursor=*`、
   `B5-CTL-AND2023@dblp` の同一 bytes、venue template の `venue%3A<venue>%3A%20year%3A<year>%3A`、ID 規約 (規則 7、`B5-CTL-<役割>@<索引>`、`B5-AUX-VENUE@dblp/<venue>-<year>`)。
2. **plan が「曖昧・不足・矛盾」として挙げた項目を検証せよ。** 本当に凍結文から一意に読めないのか、それとも読めるのに plan が読み落としたのか。
   plan が挙げていない曖昧点があれば足せ (例: 単一 block の control を規則 3・4 でどう括るか、`X OR Y` の control を「1 block に 2 語」と読むか「2 block」と読むか、
   §4.1 の `B5-OP-3` の arXiv 日付節の下限、OpenAlex で複数語 term を引用符なしで置いたときの意味)。
3. **test 設計の実効性:** plan の test 一覧が、規則の各項目に対して「その規則を壊す変異で赤になる」構造か。期待値が生成器自身の出力から写した恒真 (自己参照) になっていないか。
   §3.3 の照合例 `B5-Q10@dblp/T01-O01` のような凍結文由来の literal を期待値に使う test が十分にあるか。plan の変異候補について、単一理由性 (同じ入力を拒否する層が他に無い) が成り立つかを検査せよ。
4. **草稿 §3.2 の catalog field 集合 (期待 AST・期待 echo を置かない) の帰結:** 実行 wave が凍結文の規則から期待 AST を導出するとき、catalog に `blocks` / `branches` / `term_ids` があれば一意に導出できるか。足りない field があれば挙げよ。
5. **草稿 §4 の 3 経路の template の実効性:** OpenAlex の `filter=cites:<W-ID>`、`filter=author.id:<A-ID>`、`works/<W-ID>?select=id,referenced_works` は公知の API 形か。
   `authorships[0]` / `authorships[-1]` を第一著者・最終著者とする読みの穴 (著者順の保証、`author_position` field の存在) を挙げよ。網羅は要らないが、断定でなく「検証すべき点」として書け。
6. **lint と provenance:** `docs/related-work/claim-survey/*.json` を tracked に足すことと、`docs/related-work/claim-survey/*.md` 2 本 + README 一覧行 3 行を足すことが、`tools/check_docs.py` (byte 予算・最長行・dispatch 表・凍結族の扱い) と `tools/check_ai_provenance.py` (実装面判定: `docs/` 配下の `.json` は実装面か) でどう扱われるかを、コードを読んで書け。
   `orchestrator/tests/` に新規 test file を足すことで発火する既存のメタテスト (file 集合列挙、受入所要時間台帳の被覆 gate 等) を grep で探し、名指しせよ。
7. **草稿の内部整合:** 後継凍結物 1/2 の草稿の中で、§1 の表・§2.4 の 3 値・§2.5 の E-1・§4 の表・§5・§7 の間に矛盾や自己言及の陳腐化 (「本 wave では〜」型で凍結後に古くなる文) があれば挙げよ。

## 禁止

- ファイルを書かない・変更しない。git 操作をしない。外部 network を使わない。
- 凍結済み 2026-09-07 / 2026-09-05 文書の変更を提案しない。
- 新しい gate・検査・台帳・一般化の追加を推奨しない。scope 外の real 所見は「裁定パッケージ候補」として分けて書け。
- 出力に結合文字 U+0300〜U+036F を使わない。

## 出力形式

見出しは全部 H2 (`## `) で書く。所見ごとに `B-<番号>`、`real` / `refuted` の自己判定、根拠 (file:line または節)、推奨対応 (1〜3 行)、scope 内/外。
最後の節は必ず `## 総括` (`#` を 2 個) とする。`### 総括` と書いてはならない。予算が尽きそうなら途中結論をこの形式で書いて終われ。

## 所見
## 裁定パッケージ候補 (scope 外)
## 総括
