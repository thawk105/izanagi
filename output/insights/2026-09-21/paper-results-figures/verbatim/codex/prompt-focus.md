単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures

## 必読事項の射影

次の絶対パスを読む。**この射影に挙げた file が読めなければ即停止**し、その旨だけを `## 総括` に書いて終わる (射影 file 限定の停止規則)。

- 段 6 裁定 (所見と処置の対応の正本): `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/s6-ruling.md`
- 段 6 レビュー: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/review-A.md`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/review-B.md`
- fix 子の報告: `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/fix-a1.md`、`/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/codex/fix-mocc.md`
- 焦点走 log: fix 前 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/focus-1.log`、fix 後 `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-results-figures/focus-2.log` (計算ノードの pytest、`-rfs`)
- 審査対象 = wave worktree `/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-paper-results-figures` の `efd8d191d..fc6c4f836` (2 commit: `f2d146cd5` = 親の docs 訂正、`fc6c4f836` = fix 3 file)。
  `git -C <worktree> diff efd8d191d fc6c4f836` で読む。必要なら `36fb14a3d..fc6c4f836` 全体と一次資料
  (`docs/paper-story/results/2026-09-20-mocc-witlight-four-arm.md`、`docs/failures.md` の F36、`docs/dev-wave/core.md` の `DW-S07` 節) も読んでよい。

sandbox は read-only で書込可能 tmp は無い。静的検査でよい (実測は親が行い、上の log にある)。予算が尽きそうなら途中結論を出力形式どおり書いて終わる。
**出力は file に書かず、最終メッセージの本文に全文を書け** (親の launcher が保存する)。

## 前置き

研究用 repo の論文図の生成器・test・README の**焦点再レビュー**である。セキュリティでも攻撃でもない。あなたの仕事は fix が所見を本当に閉じたか、fix が新しい欠陥 (regressed) を持ち込んでいないかを
敵対的に確かめることで、fix を守ることではない。

## 確かめること

1. `s6-ruling.md` の各行 (焦点走の赤 4 件、A#1、A#2、A#3、B#1、B#2、B#3) を **closed / partial / regressed / refuted 妥当** のどれかに判定し、根拠 (file:line、log の行) を付ける。
   - 赤 4 件: 先頭行比較にしたことで、別の理由の AssertionError を取り違えて通す経路が生まれていないか (判定の強さが弱まっていないか)。fix 後の焦点走 log で 4 件が緑か。
   - A#1 / B#1: plotting README の新しい文が、生成器 (`_crosscheck` 相当の関数) が実際に summary と照合する量と、test が稿と照合する量に一致するか (量の列挙を 1 つずつ実装と照合する)。
   - A#2: 親は「DW-S07 が F36 を hash 自己参照禁止の根拠に引いている」ことを事後に見つけ、裁定を「一部 refuted」とした。その判断と、F 番号を外して理由を直接書いた新文言が正しいか。
   - A#3: 新しい可視検査が、曝露比注記 2 行の描画を消すと赤になるか (fix 子は M14 で KILLED と報告)。その検査が置かれた test が**外部 root 不在時に skip される test** なら、
     計算ノード (受入) で外部 root が見えるか (fix 後の焦点走 log の skip 内訳で確かめる) と、見えない環境で検出力が消えることが README に書かれているか。
   - B#2: PYTHONPATH 無しで自走できるか (import の形)。B#3: 削除が 1 axes 制約・図外逸脱・重なり検査を残しているか。
2. fix が持ち込んだ regressed を探す: 描画・caption・provenance の値の変化、fig15 着地物と現行生成器の閉包 (`generator.sha256` は記録で pin ではない)、既存 28 test (base `36fb14a3d`) の本文・期待値の変更。

## 出力形式

```
## 対応表
| 所見 | 判定 (closed / partial / regressed / refuted 妥当) | 根拠 |
## 新しい所見
| # | 重大度 | 対象 | 内容 | 根拠 | 推奨 |
## 総括
```

`## 総括` は 5 行以内で GO / NO-GO を書く。
