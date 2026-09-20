単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja

必読事項の射影: 下記の絶対パスを読む。**読めなければ即停止し、読めなかった path を報告せよ。**
この停止規則は下記に列挙した射影 file にだけ掛かる。お前が自分で探した path が不在でも、それを理由に検査全体を打ち切っては
ならない (その path は「不在」と記録して先へ進め)。

- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/output/insights/2026-09-20/paper-intro-ja/intro.md
  (**レビュー対象 1: 序論草稿**、約 15 KB)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/output/insights/2026-09-20/paper-intro-ja/contributions.md
  (**レビュー対象 2: 貢献節草稿**、約 20 KB)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/output/insights/2026-09-20/paper-intro-ja/limitations.md
  (**レビュー対象 3: 限界節草稿**、約 32 KB)
- /work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-intro-ja/brief-s1.md
  (親の段 1 brief。依頼の逐語、scope、不変条件、provisional 裁定 (P1)〜(P3)。**依頼文の「古い版の誤記を継承しない」「3 節を同じ主張の
  強さで揃える」「個々の実験の留保は results 稿側」が成立しているかを、この brief を基準に判定せよ**)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/docs/paper-story/2026-09-20.md
  (論文ストーリー最新版、3,866 行 / 489 KB。**全文 cat 禁止。** `grep -n "^## "` で節の位置を出し、入力節 §1 (238〜353 行)、§3 (1326〜1492 行)、
  §6 (2021〜2361 行)、§7 (2362〜2716 行) を `sed -n` で 80 行以内ずつ読め。§2 (354〜1325 行) は序論の第 3 節が要約している箇所
  (第 1 幕の冒頭 4 段落、第 2 幕の 2 結果と結論、第 3 幕 (a)(b)(c) の冒頭と (f) の「3 つを合わせて言えること、言えないこと」) だけ読め)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/docs/paper-story/claim-evidence/2026-09-20.md
  (claim-evidence 最新稿、706 行 / 210 KB。**全文 cat 禁止。** §1.1 (読み違い防止の 8 条、38〜67 行)、§1.2 (拒否文、68〜83 行)、
  §2.4 (書けない主張、202〜240 行)、§3 (限定レジストリ L01〜L53、241〜333 行、表なので `cut -c1-400` で先頭だけ読んでよい)、
  §5 (limitations 統制稿、401〜644 行) を読め。§2.1〜§2.3 の表は行 ID (C1〜C37) の (a) 欄を必要な行だけ `grep -n "^| C<番号> "` で引け)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-intro-ja/docs/paper-story/README.md
  (「最新スナップショット以後に確定したこと (stale 注記)」節 = `grep -n "stale 注記"` で位置を出し、その節の 3 項目 (fig10 / B-7 の限定付き充足
  D2174 項 3 / fig12) を読め。他は読まなくてよい)

新稿が「出所」で指す一次資料 (`docs/decisions.md` の D 本文、`output/insights/**/certification.json`、`output/reports/s1_direct_comparison/report.json`、
`output/campaigns/p2-5-summary.json`、`output/env/pegasus/calibration/between_run_noise_*.json`、`docs/paper-story/results/*.md`、
`docs/paper-story/figures/README.md`) は、お前が新稿の path から自分で開け。**`docs/decisions.md` は 5.7 MB / 69,000 行超 — 全文 `cat` して
はならない。** `grep -n "^## D<番号>\. "` で位置を出し `sed -n` で 60 行以内ずつ読め。D2172 (全 13 項) と D2174 (全 7 項) は `grep -n "^### 項"`
で項の位置を出してから該当項だけ読め。`jq` / `grep` / `sed -n` / `wc` / `git -C <worktree> log` / `git -C <worktree> diff --stat` は使ってよい。

この段では commit・push・file の書き込みを行わない。成果は最終メッセージの本文だけで返す (read-only sandbox では `-o` の
file を書けない。**出力は最終メッセージ本文に全文**)。pytest・build・測定は走らせない (sandbox に書込可能 tmp が無い。静的検査でよい。
テスト実測は親が行う)。予算が尽きそうなら、途中までの結論を下記の出力形式どおりに書いて終われ。無出力が最悪である。

## 役割分担

親 (Claude) が 3 稿を書いた。この wave は軽量版 (docs-only、実装面ゼロ) で、段 2 plan と段 3 敵対相談は省いた。
**お前は「一次資料から事実を再抽出する docs-only wave の段 6 read-only 独立レビュー 1 本」(D2148 項 11) であり、下の 2 レンズを 1 本で担う。**

親が実走した検査 (結果を信用せず、疑わしければ自分で再実行せよ): 3 稿の markdown 相対リンク 68 本の実在 (不達 0)、backtick の repo 内 path の実在、
A-2 / A-6 / B-7 fixed5 の `certification.json` の `effects` / `status` (0.63548… / 0.14421… observed-positive、−0.057841… reject、
0.67896… / 0.12671… / −0.11378… reject)、S-1 report の `families.s1a.p_family` 1.0 と `s1b` 0.000204…、P2-5 集計の exact p 0.0002521… と A 0.2304…、
`between_run_noise_*.json` の `between_run.cv` (0.009536… / 0.007250… / 0.002228…)、P2-4 単独稿の未丸め 3 値。

**親が論文ストーリー版・claim-evidence 稿より後の裁定 (D2172〜D2183) を読んで状態語を更新した箇所 (これが本 wave の要点であり、最も攻撃すべき面):**

| 項目 | 版・稿の記述 (執筆時点では真) | 新稿が採った現在地 | 親が根拠にした D |
|---|---|---|---|
| B-7 | 要件充足へは昇格しない (D2044 項 3、D2162 維持) | 限定付きで充足 (単一 attempt・descriptive・非認証・反復間安定性は未判定) | D2174 項 3 (D2044 項 3 を supersede)、README stale 注記 |
| 床値 g1 (A-4) | 未発効。承認 A と active pointer X は人間手番 | AI 委任の批准で発効 (A / X は main に着地)。oracle の gate-check は既存の不整合 2 件で `allowed: false` のまま。「科学的に十分な床」は主張しない | D2180 (D2120 項 2 (b) と D2174 項 4 を supersede)、`output/insights/2026-09-20/t2724-ax-delegated/README.md`、worklog の [T-2810] 起票文 |
| A-1 attempt-0002 | gate で拒否、投入経路は [T-2792] 裁定待ち | 1 attempt 限定で認可され、gate 解除は実装済み、**未投入で値は無い** | D2172 項 2、D2178、worklog archive entry 1736 |
| K2 同 job stock 対照 | 未達、[T-2795] 裁定待ち | pair launcher は実装済み、**未投入** | D2172 項 3、D2183、worklog entry 1746 |
| B-5 | 事前登録 v1 未発効、[T-2797] 裁定待ち | 部品の段階実装と上限付き試走は認可、本走は未認可、対照未取得 | D2172 項 4 |
| B-8 | 未取得 (検証相の仕分けは要裁定) | 事前登録 v1 が作られた (未発効、試走・本走は未認可)。検証相は別の追加検証 | D2175 |
| B-10 第 2 cohort の図 | 図は無い (再現欄は未着地) | 再現欄付きの後継図 fig8b がある。合成しない | D2173、figures README の fig8b 節 |
| mocc 追加実験 | (記述なし) | 費用対効果で見送り | D2172 項 7 |
| 仮説層 v3 | 前版の見出し「仮説層は未実装」は同版で訂正済み | 実装・適用済み、非 certifying の二次 view | D2143 |

## レンズ A — 事実照合 (状態語・数値・参照)

1. **上の表の 9 行を D 本文で検証せよ。** 各 D の決定文を読み、新稿の状態語が D 本文より強くも弱くもないことを確かめよ。特に:
   D2180 が「発効」と言えるか (承認 A / active pointer X の record が `output/s8b-freeze/approvals/` と `active/` に実在するか `ls` で確かめよ) と、
   新稿が「oracle 実走には至っていない」「科学的に十分な床は主張しない」を落としていないか。D2174 項 3 の限定 4 語 (単一 attempt・descriptive・非認証・
   反復間安定性は未判定) が新稿に揃っているか。D2172 項 2 / 項 3 / 項 4 で「認可」と「実装済み」と「投入済み」を新稿が混同していないか
   (attempt-0002 と K2 pair はいずれも**未投入**であることを、insight / worklog の現物で確かめよ: `grep -n "投入" ` で `output/insights/2026-09-20/t2792-a1-sized-rerun-authorization/README.md` と
   `output/insights/2026-09-20/t2795-pair-launcher/README.md` の該当行を読め)。
2. **数値。** 3 稿の数値 (利得 3 値、A-2 / A-6 / T-1998 / fixed5 の効果、S' の p 値と 9 対の範囲、P2-5 の A と p、verifier の G2 件数 1,310 / 3,576、
   mocc 5/42、floor 案 rr20 / rr80、between-run CV 3 値、A-1 attempt-0001 の対差平均 3 値、abort 0.815 → 0.494、commit −44% / 56%) を、新稿の
   「出所」が指す一次資料で検算せよ。版 (2026-09-20.md) を数値の出所にしていないか (版は「何を語るか」の入力であり値の権威ではない)。
3. **D 番号の帰属。** 3 稿が引く D 番号 (D12 / D15 / D18 / D20 / D21 / D29 / D30 / D36 / D47 / D48 / D106 / D387 / D496 / D824 / D906 / D920 / D955 / D959 /
   D960 / D1067 / D1100 / D1163 / D1198 / D1257 / D1261 / D1360 / D1363 / D1409 / D1505 / D1506 / D1525 / D1598 / D1637 / D1645 / D1678 / D1718 / D1724 / D1760 /
   D1829 / D1857 / D1931 / D1936 項 39 / D1986 項 4 / D1993 / D2016 / D2027 / D2044 (項 3・項 8・項 14) / D2083 / D2095 / D2108 / D2114 / D2120 (項 2・項 3・項 7・
   項 14) / D2127 / D2134 / D2138 / D2143 / D2145 / D2146 / D2147 / D2148 (項 11・項 13) / D2150 (項 1・項 4) / D2155 / D2156 / D2157 / D2158 / D2159 / D2160 / D2162 /
   D2172 (項 2・3・4・7・8) / D2173 / D2174 (項 3) / D2175 / D2178 / D2180 / D2183) について、実在と、新稿がその D に帰している内容が D 本文と合うことを
   **少なくとも 20 件**抜き取りで確かめよ (状態語を更新した 9 行に関わる D は全件)。
4. **§7 チェックリストと L レジストリ。** 版 §7 の 87 項と claim-evidence の L01〜L53 のうち、3 稿の記述に直接掛かるものを列挙し、違反があれば所見にせよ。
   特に: 「certified」に保証範囲を添えているか (L01)、3 workload の符号を併記しているか (L22)、`observed-positive` を「効いた」へ滑らせていないか (L29)、
   3 走行を横断実験として書いていないか (L31)、「A-1 の値がある」と書いていないか (L34)、B-10 の固定表現を守っているか (L37 / L38)、
   検証相を確率主張にしていないか (L40)、「説明可能性が核」の短縮形 (L06 / D1598)、「新しい CC」(L20)、優先権 (L06)、mocc「第 2 成功例」(L44)、
   K2「効いた」(L45)、床値の 3 つの量を 1 語で書いていないか (L15 / L43)、2 本目の論文の数値を持ち込んでいないか (L53)。
5. **参照と凍結物。** `git -C <worktree> log --oneline -3` と `git -C <worktree> diff --stat fec4a8187 HEAD` (未 commit なら `git -C <worktree> status --porcelain`)
   で、変更が `output/insights/2026-09-20/paper-intro-ja/` 配下の新規 file だけであること、版・図・`results/`・`claim-evidence/`・README・既存の
   methods / results 稿に差分が**無い**ことを確かめよ。行番号参照が無いこと。

## レンズ B — 主張の強さの整合、過大・過小主張、scope

6. **3 稿の主張の強さが揃っているか。** 序論 §3・§4 で言うこと / 言わないことと、貢献の実証状態、限界の各節が食い違う箇所 (序論で強く言い
   限界で引く、貢献で「実証済み」と書き限界で「未実証」と書く、序論の「言わないこと」が限界に無い、貢献の「書かないもの」が限界と矛盾する) を列挙せよ。
   実証状態の語彙 (claim-evidence の 7 値) が貢献稿で正しく使われているか。
7. **過大主張。** 「再現した」「効いた」「勝った」「新しい CC」「LLM でなければ」「ワークロード特化ができた」「無人で回る」「先行なし」「世界初」
   「一般に直列化可能性を保証」「床値を較正した」「発効したので oracle が動く」「B-7 を満たした (限定なし)」「第 2 cohort で再現されたので飽和しない」に
   相当する肯定文 (短縮形・言い換えを含む) が無いこと。禁止推論として引用しているのは可。
8. **過小主張 (claim-evidence §2.4 と L15 / L16 が禁じる逆向きの誤り)。** 「現行環境の同一 campaign 対はゼロ」「床値はまったく取れていない」
   「8c は何も到達していない」「A-1 の測定が無い」「B-7 は未充足」「g1 は未発効」に相当する文が無いこと。到達点を過小に書いた箇所を列挙せよ。
9. **依頼の 3 条件。** (a) 「限界」が論文全体の適用範囲と未実証の主張を扱い、個々の実験の留保 (各 attempt の限定番号、成果物に無い情報、図の用法) を
   繰り返していないか — 繰り返している箇所があれば results 稿へ委ねる書き方へ直す対案を書け。(b) 古い版の誤記 (「仮説層は未実装」「第 2 cohort は
   fig8 に描かれていない」「B-7 は要件充足でない」「g1 は未発効・人間手番」「A-1 attempt-0002 は裁定待ち」) を継承した箇所が無いこと。
   (c) 関連研究節・英訳・新規実験・gate/検査/台帳の追加が無いこと。序論の位置づけの段落が「関連研究節の代わり」になっていないか
   (1 文 + 3 条件 + 調査状態に留まっているか)。
10. **brief の (P1)〜(P3) を攻撃せよ。** (P1) 限界 §7 の「未実証の主張の地図」(表) は論文の limitations 本文として適切か、作業表 (claim-evidence §4) の
    転記になっていないか。転記なら README 側へ移す対案を書け。(P2) 「資料の採用時点 local main fec4a8187」を冒頭に置き、版・稿より後の裁定で状態語を
    更新する方針は、版の「導出対象は基準 HEAD に着地した正典に限る」規律と整合するか (稼働中・未着地の wave の内容を書いていないか —
    特に「K2 pair launcher は実装済み」は entry 1746 が main に着地済みか `git -C <worktree> log --oneline --all -- orchestrator/campaign/p3_s4_loop.py | head -3`
    で確かめよ)。(P3) 本文に T 番号を書かず D 番号を出所へ寄せる書式は、先例 (09-10 methods / results 稿) と整合するか。
11. **平易さ。** 第三者 (査読者) が読める日本語か。内部用語 (wave / land / handoff / worktree / 段 N / insight / spool) が本文に漏れていないか。
    自作の造語・空語が無いか。あれば置き換えの対案を書け。

## 守らせる不変条件 (これを緩める所見は refuted として扱う)

- 凍結物 (版・図・他の稿・insight・campaign 成果物) は 1 byte も変えない。図の作り直し・再測定は scope 外。
- 論文値は同一 sweep 内の無 backoff 対照との median 比の 3 値のままとし、他の分母の値と混ぜない。+38.5% を headline にしない (D20)。
- 当時の判定を取り消さず、新しい判定器の結果で遡って昇格もさせない (規律 7)。protocol status は成否宣告ではない (D12)。
- 現行環境の 3 走行・A-1・B-7・B-10 と pool しない (D1993 項 6)。旧 3 値の但し書き 1・3 は外れない。
- 仮想リスク向けの gate・検査・台帳・一般化は scope 外。関連研究節・英訳・新規実験も scope 外。版・claim-evidence・results 稿・図・README の改変も scope 外。

## 出力形式 (この見出しをそのまま使う)

## 所見

番号付き。各所見に `real / refuted`、`must-fix / should-fix / nit`、該当箇所 (file 名と §番号)、一次資料の path または D 番号、
対案 (訂正後の文面) を書け。**所見ごとに、放置したときに論文の主張・限定・参照がどう変わるかを 1 行で書け** (書けない所見は nit)。

## 照合して一致を確認した範囲

所見ではなく、消極的な証拠として記録する。状態語 9 行のうち確認できたもの、数値群、D 番号群を列挙せよ。

## GO / NO-GO

3 稿をこのまま凍結してよいか。NO-GO なら must-fix の一覧。

## 総括

10 行以内。
