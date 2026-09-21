単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、その旨だけを `## 総括` に書いて終わる (射影 file 限定の停止規則で、自分が推測して探した path の不在は停止理由にしない)。

- 設計の正本: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s4-ruling.md` (段 4 裁定)、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s1-brief.md` (brief)、
  `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/verbatim/origin.md` (依頼文の逐語。「本題の作図だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」)
- 実装子の最終報告: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/author-a1.md`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/author-mocc.md`
- 親の実走 log: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/focus-1.log` (焦点走 + consumer 回帰)
- 審査対象 = wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures` の commit 範囲 `36fb14a3d..efd8d191d`
  (`git -C <worktree> diff 36fb14a3d efd8d191d -- <path>` で読む): `tools/plotting/plot_a1_sized_paired.py`、`orchestrator/tests/test_plot_a1_sized_paired.py`、
  `tools/plotting/plot_mocc_witlight_four_arm.py` (新規)、`orchestrator/tests/test_plot_mocc_witlight_four_arm.py` (新規)、`docs/paper-story/figures/README.md` (一覧 2 行と末尾 2 節)、`tools/plotting/README.md` (2 節)
- 作図規約: `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures/tools/plotting/FIGURE_CONVENTIONS.md`、`docs/dev-wave/core.md` の `DW-G05` 節

**大きい file を全文 `cat` しない。** sandbox は read-only で書込可能 tmp は無い。静的検査でよい (テスト実測は親が行う)。予算が尽きそうなら途中結論を下の出力形式で書いて終わる。
**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。

## 前置き — この依頼の性質

対象は研究用 repo の論文図の生成器 (matplotlib) の拡張・新設と、その test・README の**敵対レビュー**である。セキュリティでも攻撃でもない。
あなたの仕事は実装を守ることではなく、**過剰と不足 (所見) を見つけること**である。各所見に根拠 (file:line) と重大度 must-fix / should / nit を付ける。

## 親の実測

login で A-1 test 44 passed (3.0 s)、mocc test 27 passed (3.6 s)。両図を login で実走 (rc=0)。fig9 の bytes 不変。docs 検査違反なし。焦点走 + consumer 回帰は `focus-1.log`
(計算ノードの pytest で 800 passed / 4 failed。4 件は `str(exc) == msg` の完全一致比較が pytest の assert 書き換えで崩れる既知の原因で、段 6 の fix で直す予定。所見に重複して書かなくてよい)。

## レンズ B — 過剰・削除 (研究前進・実測欠陥への対応、削除・局所修正の可否)

1. **過剰:** 依頼 (図 2 枚、attempt ごとの exact pin 表、fig9 と稿の bytes 不変、breach の表示、4 block の束縛、稿 §2 の逐語の値、禁止する描き方) と段 4 裁定と FIGURE_CONVENTIONS の必須項目の
   どれにも対応しないコード・test・README 記述 — 汎用化 (N attempt、任意 block、任意 arm)、互換層、使われない field・関数、同じ入力を拒否する重複した検査、`summary.json` に無い量を summary と照合したことにする記述、
   本数の多すぎる負例、実描画の多すぎる test。各所見に「削っても成果物 (図・caption・provenance・README) の値・受理集合・参照が変わらない」ことを 1 行で添える (DW-G05)。
2. **不足:** 論文の結果節の図素材として使えない点 (fig14 が fig9 と並べて読めるか、breach が読者に見えるか、fig15 の 4 arm の率・区間・曝露量が 1 図で読めるか、図中注記・caption が稿の限定を落としていないか、
   測定条件が caption に出ているか)。README の再現コマンドが実際にその図を再現するか。
3. **test 所要と構造:** 全体 5 分の上限に対して追加 test の所要 (親の実測 3〜4 秒/file) と、実描画の本数。plain runner の起動形 (`PYTHONPATH` の要否) が repo の既存 test と揃っているか。
4. **縮小可:** より小さい実装で同じ成果になる箇所 (削除・局所修正の推奨)。

## 出力形式

```
## 所見
| # | 種別 (過剰 / 不足 / 縮小可) | 重大度 | 対象 (file:line / README 節) | 内容 | 根拠 | 推奨 (削る / 足す / 置き換える) と成果物影響 1 行 |
## 探したが所見なしの項目
## 総括
```

`## 総括` は 5〜10 行。must-fix の件数と、GO / 条件付き GO / NO-GO を書く。
