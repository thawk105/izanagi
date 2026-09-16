単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials

## 必読事項の射影

次の絶対パスだけを読む。**この射影に挙げた file が読めなければ即停止し、その旨を出力に書く。**
停止規則の射程はこの射影 file に限る — 自分で探した path が不在でも、それは停止理由にしない。

1. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/brief.md` (親の段 1 brief)
2. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/plan-out.md` (段 2 の plan)
3. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1631.md`
4. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1993.md`
5. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1986-1to5.md`
6. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-d1874.md`
7. `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2670-b7-three-run-materials/verbatim-b7-item.md` (版 §8 の B-7 項の逐語)
8. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/README.md`
9. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-14-b7-all-workload-regression.md`
10. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/results/2026-09-07-a2-certification-observed-positive.md`
11. `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2670-b7-three-run-materials/docs/paper-story/figures/README.md`

必要なら次も読んでよい (任意、読めなくても停止しない)。

- 同 worktree の `docs/decisions.md` (`D1631` / `D1993` / `D1986` / `D1013` / `D1858` / `D12` を見出しで検索)
- 同 worktree の `docs/paper-story/2026-09-14.md` の §8
- 同 worktree の `docs/phase3-main-experiment.md` の「失敗条件」節
- 同 worktree の `docs/paper-story/results/` の他の稿

## レンズ

**配置・単位・系列規則・凍結境界。** 「この成果物をここへ、この単位で作ってよいのか」だけを攻める。
数値の転記の正しさは別の相談子が担当するので、そちらへは踏み込まなくてよい。

**親 brief 自身も検査対象である。** plan を守らない。plan と親 brief の両方を攻撃する。

## 攻めどころ (これに限らない)

1. **そもそも新稿を足すのが正しいか。** 親 brief の対抗案 (b)「2026-09-14 稿 + 版 §8 で材料化済みと
   結論し、新稿を作らない」は本当に退けられるか。既存稿の §0.1 と §4.4 が何をどこまで書いているかを
   現物で読み、「[T-1998] の材料が results 系列に無い」という親の純増主張が成立するかを判定する。
2. **D1631 と README の系列規則への適合。** append-only、1 file = 1 結果、一次資料全体からの作り直し、
   「一項目だけを直した差分改訂を新しい日付として置かない」。新稿はこれらのどれかに抵触しないか。
   **抵触するなら、どの規則の逐語のどの語に当たるかを名指しする。**
3. **単位の妥当性。** 3 走行 (A-2 / A-6 / [T-1998]) を 1 file の単位にしてよいか。plan が提案した
   単位の言い換えは既存契約の適用にとどまるか、それとも新しい一般則を作っているか。
   対抗案 (a) [T-1998] 単独稿だけを足す案の方が規則に素直ではないか。
4. **凍結境界。** 新稿が既存の凍結物 (2026-09-14 稿、版 `2026-09-14.md`、figures、事前登録) の
   bytes・意味・用途制限を変えてしまう経路が無いか。**旧 fig5 の用途制限 (期限なし)** を新稿が
   緩めないか。既存稿を「誤りを直した」と読ませる書き方になっていないか。
5. **入口の表。** plan が提案した README の 1 行は、既存 5 行の書式・列の意味と整合するか。
   既存稿の行と並べたとき、読者が「新稿が旧稿を置き換えた」と誤読しないか。
6. **裁定の射程。** D1986 項 5 は何を据え置いたのか。plan と brief はそれを正しく帰属させているか。
   D1993 の各項を、この稿が引いてよい範囲を超えて使っていないか。
   **[T-2610] (B-7 の要件充足の扱い) は未裁定である。新稿が事実上その裁定を先取りしていないか。**
7. **親 brief の誤り。** brief の記述・前提・アンカー表・一次資料表に現物と食い違うものがあれば
   名指しで挙げる。plan が既に挙げた 7 件については、**同意するか反対するかを 1 件ずつ書く**
   (同意の追認だけで終わらせない)。

## 禁止

- file を書かない・編集しない・commit しない。read-only である。
- 新しい測定を提案しない。既存の凍結物の bytes を変える案を出さない。
- B-7 の充足・不充足を宣告する案を出さない。
- plan の案を守る方向の補強だけを返さない。所見が無いなら「無い」と根拠つきで書く。
- 書込み可能な tmp は無い。pytest の緑を求めない。静的検査でよい。テストの実測は親が行う。

予算が尽きそうなら、途中結論を下の出力形式どおりに書いて終える。無出力が最悪である。

## 出力形式

次の H2 見出しをこの順で使う。各所見には `重大度: must-fix | should-fix | nit` と、
**放置したとき成果物 (統制稿・入口の表・下流の執筆) の値・受理集合・参照がどう変わるか**を 1 行で書く。

## 新稿を足すことの当否
## 系列規則への適合
## 単位の妥当性
## 凍結境界への影響
## 入口の表と裁定の射程
## 親 brief と plan の誤り
## 総括
