単独段 dispatch: stage=focus; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 段 6 レビュー A・B: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s6-review-a.md、/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s6-review-b.md
- 所見の裁定と fix1 の内容: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s6-fix1-ruling.md
- fix1 実装子の報告: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s6-fix1-a.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。

対象 (read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra の `git diff cb3d129ae 4f7512e31` (docs fix1 4af3c92b2 と fix1 統合 4f7512e31)、
および全体 `git diff 2094e8862 4f7512e31`。

## 前置き

読み取り専用 sandbox で書込可能な tmp が無いので静的検査でよい。テストは親が走らせる。予算が尽きそうなら途中結論を出力形式どおり書いて終わること。
**sub-agent を spawn しない (spawn_agent 等の collaboration tool を使わない)。この起動器は委任した attempt を拒否する。**

# 依頼 — fix 後の焦点再レビュー (DW-O16)

1. 所見ごとの closed / partial / regressed 対応表: RB-1、RA-1、RB-2、RA-2 (不採用 nit)。
2. 親が書いた派生値の再計算: L1.5 footprint が 9,696 bytes 以内に収まること (docs/dev-wave 3 file と check_docs の層分類から数え直す)、
   `.claude/commands/rulings.md` が 5,623 bytes 以内であること。数えた値を書く。
3. 縮約 3 文 (DW-O01 の完了判定文、DW-O05、DW-S05-B) と rulings.md 13・58 行が、旧文と意味等価か (義務の脱落・主体の移動が無いか)。
4. fix1 の 6 箇所が base 3cb51f201 の値へ厳密に戻り、段 5 の他の変更 (ultra・astra・委任拒否) を壊していないか。

# 出力形式

markdown。「## 対応表」「## 再計算」「## 意味等価の検査」「## 新たな所見」「## 総括」。
