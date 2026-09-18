単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/s6-fix-diff.patch (fix commit 2d953f228 の差分。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/s5-diff.patch (段 5 の commit de7cc6424 の差分。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/out-review-A.md (段 6 レビュー A の所見 RA-1〜RA-3。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/out-review-B.md (段 6 レビュー B の所見 RB-1〜RB-3。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/s4-ruling.md (段 4 裁定。読めなければ即停止)
- /home/SFC/tanab/.claude/jobs/bcf9f618/tmp/codex/dev-wave-t2447-lens-p2-p6/projection/D1893.md (ユーザー裁定の逐語。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/core.md (改訂後、fix commit 済み。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/dev-wave/workers.md (改訂後、commit 済み。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/docs/skill-self-improvement.md (routing の正本、不変。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/.claude/commands/dev-wave.md (入口、不変。読めなければ即停止)
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2447-lens-p2-p6/tools/check_docs.py (pin と予算の実装、不変。読めなければ即停止)

## 目的
これは自分たちの開発手順書 (dev-wave の docs) の docs-only 変更について、段 6 レビュー 2 本の所見に対する fix (commit 2d953f228、`docs/dev-wave/core.md` DW-S04 の 1 行) の焦点再レビューである。

## 親の裁定と fix の内容
- RA-1 / RB-1 (must-fix、同一): 採用。RB-1 の最小是正「scope 外の real 所見は」→「全段の scope 外 real 所見は」(+7 bytes)。
- RB-2 (nit): 採用。「資料/実測で示せる場合だけ」→「示した場合だけ」(0 bytes)。
- RB-3 (nit、E1 の別短縮で E3 を不要にする): 不採用。現案は「明記する」義務を保ち、残 36 bytes と読みやすさを優先。
- RA-2 / RA-3 (記録): 記録のみ。
- 親の実測 (fix 後): `git diff --check` rc=0、`python3 tools/check_docs.py` 違反なし、層予算 L1 10,623 / 10,625、L1.5 9,660 / 9,696、full provenance 監査 11,208 件・新規違反なし。

## 依頼
1. 所見ごとの **closed / partial / regressed 対応表** を作れ (RA-1、RA-2、RA-3、RB-1、RB-2、RB-3)。表なしで閉じたと判定しない。
2. fix 後の DW-S04 の文言「全段の scope 外 real 所見は実装せず、研究前進か実測欠陥を資料/実測で示した場合だけ設計択一・推奨案付き裁定パッケージでユーザーへ返し、他は起票せず insight に記録する。」が、(a) 段 8 の自己改善 routing (`docs/skill-self-improvement.md` routing 2、dev-wave 終端) との競合を実際に閉じるか、(b) 「全段」が段 4 以外で親が裁定する所見 (段 6 レビュー所見、段 8 候補) に届く読みになるか、(c) 「示した」が静的反例 (資料) を排除しないか、を逐語で検証せよ。閉じていなければ最小の是正を bytes 付きで示せ (L1 の残は 2 bytes)。
3. 親が書いた派生値 (+7 bytes、L1 10,623、残 2) を原文から再計算して照合せよ。
4. fix が段 5 の他の編集 (E1〜E4、E6、E7) や pin (`tools/check_docs.py` の reasoning pin、`CODEX_FIRST_REFERENCE_LITERALS`、exact 節 pin) を退行させていないか確認せよ。

## 制約
- 静的検査のみ。pytest を要求しない。テスト実測は親が行う。
- 予算が尽きそうなら途中結論を出力形式どおり書いて終われ (無出力が最悪)。
- 出力は file に書かず、最終メッセージの本文に全文を書け (親の launcher が保存する)。
- 見出しは全部 H2 (`## `) で書く。`###` を使わない。

## 出力形式
## 対応表 (closed / partial / regressed)
## 逐語検証
## 派生値の再計算
## 総括
