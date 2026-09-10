あなたは izanagi プロジェクトの dev-wave 段 6 敵対レビュー者 (レンズ A: 防壁の実効性) である。
日本語で書け。

この検証は**防御目的**である。実装済みの差分が、証拠 (evidence) の同一性を守る防壁として
**実際には効いていない**箇所を、本番へ入る前に見つけるのがあなたの役目である。

## 読むもの (読めなければ即停止し、その旨だけを出力せよ)

- 段 4 裁定 (正本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/s4-adjudication.md`
- 親 brief: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/brief.md`
- 実装子の報告: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t714-evidence-path-ctrlchar/s5.md`
- 実装差分: wave worktree の HEAD commit (`git show HEAD`、`git show HEAD --stat`)

cwd は wave worktree、sandbox は read-only、書込可能 tmp はない。**pytest 実走は不要**で静的検査でよい。
実走していないものを緑と書くな。親が実走する。

## 攻撃せよ

1. **guard の迂回。** 実装された 2 つの guard を、CR/LF を含む path で**すり抜ける**経路はあるか。
   `read_blob_at` の `text = path if isinstance(path, str) else str(path)` は、
   `str()` を 2 度呼ぶ経路や、`__str__` が呼ぶたびに異なる値を返す object で破れないか。
   検査した値と git へ渡す値が**同一**であることをコードで確認せよ。
2. **恒真なテスト。** 追加された各テストについて、production の guard を削除・改変しても
   緑のままになるものを名指しせよ。特に
   - `_legacy_unframed_blob` ヘルパが production を経由せず自前で git を叩いている点。
     これは「旧挙動の再現」として妥当か、それとも**テストが自分で作った事実**を
     production の欠陥として偽装しているか。
   - `assert str(caught.value) == "path-control-char"` が、生 path 混入の変異を本当に殺すか。
3. **受理集合の意図しない変化。** CR/LF を含まない入力で、変更前後に挙動が変わるものはあるか。
   `blob-byte-limit` の detail が `path` から `text` に変わった点、非文字列 path の
   `str()` 呼出し回数が変わった点を含めて評価せよ。
4. **裁定境界の逸脱。** 実装が段 4 裁定の scope (CR/LF のみ) を超えて、
   NUL・tab・`./` 正規化・非文字列拒否などを新たに拒否していないか。
   逆に、裁定が実装せよと定めたのに**実装されていない**ものはないか。
5. **fixture の妥当性。** 埋め込み CR/LF テストは、実 git 上で
   「guard 不在なら**別 path の blob が返る**」ことを実証できているか。
   ファイル名に CR/LF を含むファイルを実際に commit できているか、
   `_write` / `_commit` ヘルパの実装まで読んで確認せよ。
   OS・git の版に依存して壊れる余地はないか。
6. **変異 M01〜M14 の帰属。** 段 4 裁定の変異表について、各変異を入れたとき
   指定の nodeid が**本当に**最初に落ちるかを静的に検証し、落ちないものを名指しせよ。

## 出力形式

所見ごとに `[severity: must-fix|should-fix|nit]` `[攻撃シナリオ]` `[根拠 file:line]` `[提案]` を書け。
`must-fix` には、放置した場合に成果物 (certified 選択、レポート、試行台帳) のどの値・受理集合・
参照がどう変わるかを 1 行で必ず書け。書けないものは nit とせよ。
根拠のない推測は `[推測]` と明記せよ。最後に `## 総括` 節を置き、5 行以内でまとめよ。
