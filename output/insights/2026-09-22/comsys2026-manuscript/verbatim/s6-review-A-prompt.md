単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-comsys2026-manuscript

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 依頼文の逐語: /work/1/SFC/tanab/dev-wave-jobs/dev-wave-comsys2026-manuscript/verbatim-request.md
- 親 brief (P1〜P6 は親の provisional 裁定で攻撃対象): /work/1/SFC/tanab/dev-wave-jobs/dev-wave-comsys2026-manuscript/s1-brief.md
- レビュー対象 (投入先 worktree の path、read-only): `docs/paper-story/2026-09-22.md` (commit `d18b073abe2d8957c26827cd062d2e4a5e6cbcec`)。前版は `docs/paper-story/2026-09-21c.md`。
  差分は `git diff 8fd2a2f5c775954d6a32cee019ac7ce276298e4d d18b073ab -- docs/paper-story/` ではなく **前版との比較** `git diff --no-index docs/paper-story/2026-09-21c.md docs/paper-story/2026-09-22.md` で読める。
- 版の作り方の記録 (親の手順と修正、job dir): `story/r0_timewords.py` (時点語の機械置換)、`story/story-drafter-rules.md` (下書き役の規則)、`story/edits-R1.json`〜`edits-R7.json` と `edits-P*.json` (当てた置換案)、
  `story/parent-fixes.log` (親が置換案を直した記録)、`story/new-header.md`・`new-s0.md`・`new-s10.md` (親が書いた区間)。いずれも `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-comsys2026-manuscript/` の下。
- 索引 (正本ではない。一次資料で確かめること): 同 job dir の `digest-decisions.md`・`digest-entries.md`。
- 一次資料: 投入先 worktree の `docs/decisions.md` (D2206〜D2218、`grep -n "^## D22[01][0-9]" docs/decisions.md`)、`docs/worklog.md` (entry 1814〜1818) と `docs/archive/worklog-phase3-0921-1796.md`〜`-1813.md`、
  `docs/paper-story/README.md` の stale 注記、`docs/paper-story/figures/README.md` (fig14・fig15 節)、`docs/paper-story/figures/arc_status_story_2026-09-21c.json`、
  `output/insights/2026-09-21/` の各 README (vldb-direction・tpcc-trace-certification-design・silo-function-synthesis-space・t2632-b4-evidence-carrier・t2797-tier0・t2844-mocc-xp-hook-branch・paper-results-figures)。

## 前置き — これは自分たちの研究文書のレビューである

研究用 repo (トランザクションの並行性制御を LLM で合成する研究) の「論文ストーリー」文書の次版を、書いた後に敵対的に点検してもらう。セキュリティ製品でも攻撃ツールでもない。
あなたは read-only のレビュー役で、書込可能な tmp は無いので静的な読解と grep でよい。テストや build は走らせない。**親の brief・親が書いた区間・親の実測 (時点語の置換件数、置換案の監査) も点検対象である。**
攻撃が成立しなかった項目は正直に「不成立」と書け。全項目を無理に成立させるな。

## レンズ A — 状態語と時点語の正しさ (正しさ境界・整合)

所見ごとに real / refuted の見込み・重大度 (must-fix / should / nit)・根拠 (版の行番号と一次資料の file と見出し)・放置時に論文の主張・状態語・原稿がどう誤るかを 1 行で書く。

1. **状態語:** この版が「動いた」と書く事実 (冒頭の第 1〜3、§0 の 8 点、§2 第 3 幕・§6・§7・§8・§9 の「この版の起点までに」の各文) が、一次資料 (D 本文 = 認可・保留・却下・条件付き採用・設計のみ、entry / insight = 実施・件数・結果) と一致するか。
   特に「認可」と「実施」、「段階認可」と「認可」、「条件付き採用」と「採用・実装」、「設計のみ」と「実装」、「pair 再投入 1 job の認可」と「pair 成立 / 4 巡目の認可」、「候補 commit C」と「pin 前進」、「保留」と「却下」を取り違えていないか。
2. **時点語:** 機械置換 (前版→2026-09-21b 版、この版→前版) の後に、(a) 前版 (21c) の時点の記述なのに現在形のまま起点 `8fd2a2f5c` で偽になっている文、(b)「前版でも」で止まった継続の主張でこの版の起点でも真なのに延ばしていないもの / 延ばしたが偽のもの、
   (c) 修飾の無い「基準 HEAD」「この wave」「同日」が別の版の時点を指している文、(d) 版の自己言及 (「この版で…した」) が別の版・日付の出来事と取り違えられている文、が残っていないか。
3. **前版の執筆時点の誤り (brief の P6):** 冒頭と §10 (P2) の「訂正 0 件」は妥当か。前版の起点 `d99c556df` (2026-09-21 13:35 JST) までに正典に入っていたのに前版が反映していなかった事実があれば、それは「後続が古くした」型ではなく執筆時点の誤りである。
   `git merge-base --is-ancestor <着地 commit> d99c556df` の祖先性で判定し、該当があれば列挙せよ。
4. **§4 の図:** fig14 / fig15 の行・fig3c の副ラベルとの不一致の記述 (A-4 と B-4 の副ラベルが偽、B-5 / B-6 は真) が状態 JSON と一致するか。着地 bytes の SHA-256 の先頭 8 桁が figures README と一致するか。

## レンズ B — 過剰・削除 (研究前進に要らない追加、落とした限定)

5. **過剰:** この版が一次資料に無い新しい主張・評価語・一般化を足していないか (例: D2212 の理由欄を超えた新規性の否定 / 肯定、ADRS と位置づけの 1 文の関係を判定したように読める文、TPC-C・関数単位の軸を実施済みに読める文)。
   依頼が scope 外とした gate・検査・台帳・一般化の追加が紛れていないか。
6. **削除:** 前版の限定・禁止句・「言えないこと」を、置換や区間の差し替えで落としていないか (冒頭・§0・§10 は親が書き直したので、前版の冒頭・§0 が持っていた限定のうち今も要るものが残っているか)。
   §7 が「前半 122 項 + 後半 11 項の計 133 項」「落とした項目は無い」と書く主張が本文の `- [ ]` の数と合うか。
7. **重複・冗長:** 同じ新事実 (K2 の認可、g1 の保留、B-4 の carrier、mocc の候補 C) が多数の節に繰り返されて、どこかで食い違っていないか (食い違いは must-fix、単なる重複は nit)。

## 出力形式

- 見出しは `#` 1 段だけを使い、`##` は最後の `## 総括` のみ。`### 総括` と書いてはならない。
- 実行できない検査は「未実走・静的読解」と明記する。予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- **出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。
- 末尾に `## 総括`: GO / NO-GO、must-fix / should / nit の一覧 (各 1 行、根拠は版の行番号と一次資料)、各 must-fix の最小修正案 (置き換え後の文面を 1 つ添える)。
