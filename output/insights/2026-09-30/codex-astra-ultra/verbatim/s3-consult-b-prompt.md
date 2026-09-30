単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 依頼の逐語: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/request-md_1.txt
- 親 brief (段 1、攻撃対象): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s1-brief.md
- 段 2 plan (攻撃対象): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s2-plan.md
- 段 2 plan の未確定点への親の追加実測 (攻撃対象): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s2-parent-measurements.md
- 親の実測の生データ: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/liveness/ (token-summary.txt ほか)

この「読めなければ即停止」は上の射影 file にだけ掛かる。自分で組み立てた path が不在でも停止せず、1 行書いて実在 file を探し直し、最後まで続けること。

参照してよい repo (read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra/ 配下 (HEAD 241f0c960)。
特に `docs/decisions.md` の D2229 (前回の model 移行の型)、`docs/dev-wave/core.md` の DW-C00・DW-G02〜G05、`docs/failures.md` の型タグ。

## 前置き

対象は研究用 repo の開発道具 (Codex 子の起動器と docs の pin) の設定変更である。読み取り専用 sandbox で書込可能な tmp が無いので静的検査でよい。
テストは走らせない。予算が尽きそうなら途中結論を出力形式どおり書いて終わること。**sub-agent を spawn しない (collaboration tool を使わない)。**
成果物はアカデミアのプロトタイプであり、仮想リスクだけの gate・検査・台帳・framework は足さない。ただし絶対規律と実測された欠陥の修正はこの制限の外。

# 依頼 — レンズ B「過剰・削除」: 研究前進と実測欠陥への対応として、plan が大きすぎないか・小さすぎないか

brief と plan を守らず、両方を攻撃対象として検査せよ。

1. **P1 と対案 P1'・P1'' の比較。** 委任先会計を起動器へ足す差分量・新しい受領証 field・consumer 追随の総量と、委任を検出して拒否する案、権威段だけ effort を下げる案、
   prompt で委任を禁じるだけの案を、依頼 (「検査が落ちても黙って緩めない。何が記録されたかを読んでから受理規則を明文化して直す」) と実測 (L5: 検査は落ちずに素通り、
   L6: 設定で委任を止められない) に照らして比べ、最小で依頼を満たす案を推奨せよ。拒否案では ultra の token を無駄にする頻度も見積もれ。
2. **削れるもの。** plan の変更のうち、DW-G05 の成果物影響 1 行を示せないもの、既存 test の期待値の付け替えだけで意味の無いもの、D2229 決定 5 と同じく
   変えない方がよいもの (例示値・過去記録) を挙げよ。逆に、依頼が求めるのに plan が落としたもの (rulings・next-tasks の値、週枠の実測記録、生死確認の項目) を挙げよ。
3. **段構成の過剰。** 全 9 段・2 単位分割・変異 matrix・受入全走のうち、この wave で省けるもの・省けないものを DW-C00・DW-S04 で判定せよ。
4. **brief の実測値の一般化。** L6 の 3 probe・L7 の sandbox 継承・L8 の guard の主張が、測った範囲を超えて一般化されていないか。
5. **週枠。** ultra の token 実測 (token-summary.txt) から、dev-wave 1 本 (plan 1・consult 2・author 2・review 2・fix・focus) の消費を粗く見積もり、
   `LLM 週上限 429` で系列 job が欠測した前例 (memory ではなく repo の worklog・failures を grep) に照らした注意点を 3 行以内で。

# 出力形式

markdown。各所見を「### B-n 題」+ 重大度 (must-fix / should / nit) + 根拠 + 放置時の成果物影響 1 行 + 推奨。
最後に「## 推奨する最小 plan」(単位ごとの変更 file と行数見積もり) と「## 総括」。
