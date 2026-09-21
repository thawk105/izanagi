単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、その旨だけを `## 総括` に書いて終わる (射影 file 限定の停止規則で、自分が推測して探した path の不在は停止理由にしない)。

- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s1-brief.md` — 親の段 1 brief。**これ自体も攻撃対象**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s1-pin-closure.md` — 親がまとめた pin 閉包 (**攻撃対象**)
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/plan.md` — 段 2 の codex plan。**攻撃対象**
- `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/verbatim/` 配下の全 file (依頼文の逐語 `origin.md`、裁定の逐語、両 results 稿の該当節、README 2 本の現行節、先行 wave の終端記録)
- repo 内 (worktree の path、read-only): `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures/` の
  `tools/plotting/plot_a1_sized_paired.py` (全文)、`orchestrator/tests/test_plot_a1_sized_paired.py` (全文)、`tools/plotting/FIGURE_CONVENTIONS.md` (全文)、
  `tools/plotting/plot_b10_waiting_grid_forest.py` と `orchestrator/tests/test_plot_b10_waiting_grid_forest.py` (部分読み)、`docs/dev-wave/core.md` の `DW-G02`〜`DW-G05` 節
- repo 外 (read-only): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/arm-W/summary.json`、`W1/result.json`〜`W4/result.json` (全文 cat しない。`python3 -c` / `jq` で見る)

**大きい file を全文 `cat` しない。** sandbox は read-only で書込可能 tmp は無い。静的検査でよい (テスト実測は親が行う)。予算が尽きそうなら途中結論を下の出力形式で書いて終わる。
**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。

## 前置き — この依頼の性質

対象は研究用 repo の論文図の生成器 (matplotlib) の拡張・新設と、その図・provenance・test の**計画の敵対レビュー**である。セキュリティでも攻撃でもない。
あなたの仕事は plan と brief を守ることではなく、**欠陥を見つけること**である。所見は real と判断した根拠 (file:line・実測値・一次資料の逐語) を付ける。

## レンズ B — 過剰・削除 (研究前進・実測欠陥への対応、削除・局所修正の可否)

依頼は「本題の作図だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」と明記している (`verbatim/origin.md`)。次を探せ。
見つからなければ「探した場所と方法」を書いて「所見なし」とする。

1. **過剰:** plan の生成器・test・docs のうち、依頼 (図 2 枚の作成、attempt ごとの exact pin 表、fig9 と稿の bytes 不変、breach の表示、4 block の束縛、逐語の値、禁止する描き方) と
   FIGURE_CONVENTIONS の必須項目 (§1〜§10) のどれにも対応しない追加 — 汎用 attempt loader・N attempt 対応・verbatim 写しへの fallback・新しい台帳・新しい gate・
   既存図の検査の一般化・互換層・過剰な負例 test。各所見に「削っても成果物 (図・caption・provenance・README) の値・受理集合・参照がどう変わらないか」を 1 行で添える (DW-G05)
2. **不足 (研究前進に必要なのに欠けているもの):** 図が論文の結果節で使える形になっているか — fig14 が fig9 と同形で並べて読めるか (軸・尺度・panel 順・凡例)、
   `variance_plan_breach` が読者に見える形か、fig15 が 4 arm の G2 signal 検出率と区間・曝露量を 1 図で読めるか、caption が稿の限定 (非有意 ≠ 同等性、検出力 0.105 は計算値、
   非 certifying、TRACE=1、smoke 除外、4 block) を落としていないか
3. **より小さい実装:** 既存生成器の拡張の差分を小さくできる箇所 (例: attempt-0001 の定数を残したまま attempt-0002 の表を足すだけで済むか)、fig15 の生成器を fig13 より小さく書けるか、
   test の本数と所要 (test 全体 5 分の上限、matplotlib の実描画は数を絞る)。削除・局所修正で済むものは推奨として出す
4. **分割と所有:** 段 5 の実装子 2 本 (A = A-1 の 2 file、B = mocc の新規 2 file) の分割が producer / consumer の契約を壊さないか。親の docs (README 2 本) と実装子の test が
   README の節の文字列を照合する場合、どちらが先に書くかで test が赤になる順序問題がないか
5. **brief の P1〜P8 の要否:** 各 P が本当に要る決定か、より単純な択で同じ成果が得られないか (特に P2 の CLI 既定値、P3 の図番号、P7 の panel 数、P8 の着地閉包の 2 層)
6. **親 brief 自身の誤り:** brief の研究前進・完了判定・成果物影響の記述が過大・過小でないか

## 出力形式

```
## 所見
| # | 種別 (過剰 / 不足 / 縮小可 / 順序) | 重大度 (must-fix / should / nit) | 対象 (plan §x / brief / 既存 file:line) | 内容 | 根拠 | 推奨 (削る / 足す / 置き換える) |
## P1〜P8 の判定
(P ごとに 同意 / 反対 / 根拠不足 と 1〜2 行)
## 探したが所見なしの項目
## 総括
```

`## 総括` は 5〜10 行。must-fix の件数と、plan を実装へ進めてよいか (GO / 条件付き GO / NO-GO) を書く。
