単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-b7-limited

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、
それを理由に検査全体を打ち切ってはならない (その path は「不在」と記録して先へ進め)。

W = /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-b7-limited (投入先 worktree、HEAD `947fd160a` = local main、**docs の変更は未 commit で working tree にある**)。
以下の path は W 配下の絶対 path で書く。

**レビュー対象 (親が書いた docs の差分 2 file、未 commit。差分だけを見るなら下の patch file を読め):**

- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-b7-limited/verbatim/diff-docs.patch (2 file の unified diff、60 行。**これが本レビューの対象の全文**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-b7-limited/docs/paper-story/README.md の **行 58〜70** (stale 注記の節。追記は行 64 の件数文と行 67 の新項目。file は 228 行 — `sed -n` で読め) と **行 202** (results 系列表の 2026-09-19 稿の行。行末に追補注記を足した。1 行が長い — `sed -n 202p | cut -c1-3000`)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-b7-limited/docs/paper-story/figures/README.md の **行 27** (一覧の fig10 行、行末に追補注記) と **行 1184〜1324** (fig10 節の全体。追記は行 1308〜1324 の `## 追補 — B-7 の限定付き充足`。file は 1,324 行 — `sed -n` で読め)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-b7-limited/verbatim/rulings-body.md (既裁定の逐語 44 行: D2044 項 3 (行 1〜10)、D2162 の決定文 (行 11〜22)、D2174 の前文 (行 23〜34)、**D2174 項 3 (行 35〜44) = 本 wave が写す裁定の正本**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-b7-limited/output/insights/2026-09-20/t2610-b7-limited-satisfaction/README.md (段 1 brief。scope・不変条件・(P1)(P2) の正本)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2610-b7-limited/HANDOFF.md (親の段 1 前実測の要約)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-b7-limited/docs/spool/worklog/2026-09-20-dev-wave-t2610-b7-limited-1.md (worklog fragment。`〔REVIEW〕` 等の仮置きは親が後で実値へ置換する — 仮置きは所見にしない)

**一次資料・凍結物 (照合に使う。次の範囲だけ `sed -n` で読め。全文 `cat` しない):**

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-b7-limited/docs/paper-story/results/2026-09-19-b7-fixed5-three-workload-regression.md: 行 1〜22 (冒頭の位置づけと「本稿が判定しないこと」)、行 245〜271 (§4 限定)。337 行の凍結稿。**本 wave はこの file を 1 byte も変えていない** — `git -C W status --short -- docs/paper-story/results/` が空であることを確認せよ
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-b7-limited/docs/paper-story/2026-09-20.md: 行 3156〜3162 (§8 B-7)、行 2252〜2256 (§6 「言えないこと」の B-7 項)。3,000 行超の凍結版。**本 wave は変えていない**
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-b7-limited/docs/paper-story/README.md: 行 101〜125 (erratum・追補の先例 = fig2 / fig5 / 旧 fig5 用途制限)、行 148〜152 (T-1998 単独稿の読解上の追補の先例)、行 181〜187 と 208〜223 (results 系列の規則 = append-only、1 file = 1 結果)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-b7-limited/orchestrator/tests/test_plot_b7_fixed5_regression.py: 行 550〜567 (`test_landed_fig10_repo_closure_and_caption_when_present` — README の節切りと SHA 行の照合、caption 逐語)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2610-b7-limited/docs/paper-story/figures/fig10_b7_fixed5_three_workload_regression.provenance.json: `grep -n "caption_source" -A 3` で `caption_source` の sha256 を確認 (稿の現 SHA-256 は `sha256sum` で取れ)

**巨大 file の扱い (必ず守れ):** `docs/decisions.md` は約 5.6 MB、`docs/failures.md` は約 2.8 MB、`docs/worklog.md` は 3,000 行超。
**全文 `cat` してはならない。** `grep -n "^## D<番号>"` で位置を出し `sed -n` で 60 行以内ずつ読め。`wc -c` / `wc -l` は許す。
既裁定の逐語は上の verbatim file にある。検算に要る D 番号は D2174 項 3・D2044 項 3・D2162 だけで、3 つとも verbatim にある。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す
(read-only sandbox では `-o` の file を書けない。**出力は最終メッセージ本文に全文**)。
pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い。静的検査でよい。テスト実測は親が行う —
親は `tools/check_docs.py` rc=0、`git diff --check` 緑、`spool_fold --dry-run` rc=0 を実測済み。fig10 着地 test と check_docs 系の焦点走は親が計算ノードで行う)。
予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 役割分担

親 (Claude) が docs 2 file (paper-story README の stale 注記 + results 行、figures README の fig10 行 + fig10 節末尾の追補) を直接編集した (docs のみ、実装面ゼロ)。
この wave は軽量版で段 2 plan と段 3 敵対相談は省いた。**お前は「一次資料 (裁定文) から限定文言を再抽出する docs-only wave の段 6 read-only 独立レビュー 1 本」であり、
下の 2 レンズを 1 本で担う。** 裁定 D2174 項 3 の当否は攻撃対象ではない (ユーザー裁定済み)。攻撃対象は「写した文言が裁定文と一致するか (盛っていないか・削っていないか)」
「凍結物と pin を壊していないか」「scope 外へはみ出していないか」「過剰・冗長・置き場違い」である。

## レンズ A — 裁定文との照合と正しさ境界 (盛り・削りの検出)

1. **限定 4 語の逐語性。** D2174 項 3 の限定「単一 attempt・descriptive・非認証・反復間安定性は未判定」が、追記 4 か所 (README 行 67・行 202、figures README 行 27・行 1308〜1324) の
   すべてで逐語に写されているか。語の欠落・言い換え・順序の違いを挙げよ。
2. **supersede の範囲。** 「D2044 項 3 を supersede」が、D2044 項 3 の**全体** (昇格させない + 記述的な報告は利用してよい) を消すと読めないか。D2174 項 3 が supersede したのは
   「要件充足へ昇格させない」の部分であり、「記述的な報告は利用してよい」は生きている — 追記の書き方はこれと整合するか。
3. **「充足」の射程が広がっていないか。** 追記のどこかが、充足を「候補の採用根拠」「certified」「性能主張」「有意差」「反復で安定」と読める書き方になっていないか。
   逆に、限定を盛りすぎて D2174 項 3 が言っていない制限 (例: 「論文で使えない」) を足していないか。
   figures README 追補の「論文でこの図を B-7 の報告として使うときに付く限定は上の 4 語である (D2174 項 3)」は裁定文から導けるか、それとも親の追加規則か。
4. **凍結物の扱い。** (a) 稿・図・caption・provenance・ストーリー版・claim-evidence 稿を変えていないこと (`git -C W status --short`、`git -C W diff --stat`)。
   (b) fig10 節の追補が着地 test の節切り (行 550〜567: `# \`fig10…\` — ` 〜 次の `\n# `、`## 着地 bytes の SHA-256\n` 〜 次の `\n## `) を壊さないか —
   追補を `## 着地 bytes の SHA-256` の**後**に H2 で置いたので、hash 抽出部は `provenance が caption_source …` の段落までで切れる。SHA 3 行と caption 逐語 (`prov['caption'] in readme`) は残っているか。
   (c) 稿の現 SHA-256 が provenance の `caption_source.sha256` と一致するか (`sha256sum` で実測)。
5. **caption の読み替えの妥当性。** 凍結 caption "This is B-7 material, not a B-7 satisfaction decision (D2044 item 3)." を「着地時点の記録として真のまま残す」「充足の裁定は図の外で D2174 項 3 が行った」と
   書いたが、これは fig5 の erratum (README 行 105〜125) と同じ「凍結物を直さず入口で読み替える」形か。矛盾 (図は「判定しない」と言い、README は「充足」と言う) が読者に誤解を与えない書き方か。
6. **stale 注記の型。** README 行 64〜67 の「執筆時点では真で、後続の裁定で古くなった型」という分類は正しいか。ストーリー版 2026-09-20 版 (行 3156〜3162、2252〜2256) の文は
   執筆時点 (導出起点 `b7f970dfa`、07:04 JST) で真だったか — D2174 は同日 13:03 の記録 (verbatim 行 23〜34 の前文で提示時点の main `4a87d566b` を確認)。
   件数文「2 件」は箇条書きの個数と一致するか。

## レンズ B — 裁定境界・scope・過剰と削除 (DW-S03 の固定レンズ)

1. **scope 外への逸脱。** 追記のどれかが「新規測定・反復 attempt・certified 昇格・有意差判定」を示唆・要求・予告していないか。「次版の再導出で拾う」は新しい版を作る要求になっていないか
   (README 行 101〜103 の D1858: 項目が積まれること自体は新版の要求にならない)。
2. **(P1) の当否 — 「稿の追補」の置き場。** 依頼は「稿の追補」と言ったが、親は稿本文 (凍結 + SHA 束縛) へ書かず README 側へ置いた。results 系列の規則 (行 208〜223) と先例 (行 148〜152) に照らして、
   この置き場は正しいか。新しい results file (例: `results/2026-09-20-b7-limited-satisfaction.md`) を作るべきだったか — 「1 file = 1 結果」の規則と照らして判定せよ。**(P1) への判定を必ず 1 件立てよ。**
3. **(P2) の当否 — worklog の T-2610 を `完了` に置く。** fragment の `完了` 項 (remaining: none) は、D2174 項 3 の AI 手番 (稿・図の説明・ストーリー版の地図に写す) を本 wave が全て済ませたと
   言えるか。「ストーリー版の地図」= paper-story README の stale 注記という読みは妥当か。残件 (次版での取り込み) を T として残すべきか、版系列の規則が拾うので不要か。**(P2) への判定を必ず 1 件立てよ。**
4. **過剰・冗長・置き場違い。** 4 か所の追記について、削るべき文・移すべき文・重複を具体的に挙げよ。特に (a) README 行 67 の新項目は既存項目 (行 66) と重複する説明 (図 10 の内容) を繰り返していないか、
   (b) figures README の追補 (行 1308〜1324) の 5 bullet のうち、fig10 節の「何を示す図か」(行 1186〜1201) と重複するものはどれか、(c) 一覧行 (行 27) と results 行 (行 202) の注記は
   節/項目への参照 1 文で足りるか、(d) 「F428 型の回避」等の内部語が読者向け docs に漏れていないか (fragment は worklog なので内部語可、README 2 本は執筆者向け)。
5. **既存文との整合。** README 行 67 の新項目の書式 (太字の見出し文 + 執筆時点の真偽 + 変わらないこと + 一次資料) は行 66 の既存項目と揃っているか。figures README 追補の見出し書式は
   同 file の既存追補 (`grep -n "^## 追補\|^### 追補\|^## Erratum" docs/paper-story/figures/README.md`) と揃っているか。
6. **worklog fragment の形式。** `docs/spool/worklog/README.md` の規則 (H2 は `## 本文` と `## 次の一手差分` の 2 つ、`完了` には `remaining: none` と `base:` の連続 field 行) を満たすか。
   `title:` の `[T-2610]` は同エントリで `完了` に置く既存 active item なので許されるか (同 README の `title:` 規則)。

## 出力形式

最終メッセージ本文に、次の順で、**H2 見出し (`## `) をこの 3 つだけ**使って書け。

## 所見

番号付きで、1 所見につき: **real / refuted** と **must-fix / nit** の 2 判定、対象 (file と行または節)、一次資料 (path と行または節)、
対案 (置換後の文面か削除)、**放置の影響 1 行** (成果物 = 論文執筆者が README を読んで B-7 をどう書くかがどう変わるか、または着地 test / fold がどう赤になるか。
示せない must-fix は nit にせよ)。所見ゼロなら「所見ゼロ」と書き、その根拠 (何を検算して一致したか) を列挙せよ。
(P1) と (P2) への判定は所見の中で必ず各 1 件立てよ (real / refuted のどちらでも)。

## 検算の記録

読んだ path と行範囲、実行した command とその出力の要点、一致した項目の一覧。

## 総括

must-fix 件数、nit 件数、レンズ A / B の結論を各 2 文以内。**`## 総括` の見出し (H2、行頭から `## 総括`) は必須である**
(親の受理検査 `tools/check_codex_output.py` が `^## 総括` を要求する)。
