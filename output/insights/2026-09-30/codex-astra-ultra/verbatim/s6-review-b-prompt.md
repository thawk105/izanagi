単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra

必読事項の射影 (各 path を読めなければ即停止して、その旨だけを `## 総括` に書いて終わること):
- 依頼の逐語: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/request-md_1.txt
- 段 4 裁定 (正本): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s4-ruling.md
- 段 3 のレンズ B 相談 (過剰・削除の基準): /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s3-consult-b.md
- 実装子の報告: /work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s5-author-a.md、/work/1/SFC/tanab/dev-wave-jobs/codex-astra-ultra/s5-author-b.md

この「読めなければ即停止」は上の射影 file にだけ掛かる。

レビュー対象 (read-only): /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-codex-astra-ultra の `git diff 2094e8862 cb3d129ae`。
特に `docs/decisions.md` の D2229・D782、`docs/skill-self-improvement.md`「command 入口の編集条件」。

## 前置き

読み取り専用 sandbox で書込可能な tmp が無いので静的検査でよい。テストは親が走らせる。予算が尽きそうなら途中結論を出力形式どおり書いて終わること。
**sub-agent を spawn しない (spawn_agent 等の collaboration tool を使わない)。この起動器は委任した attempt を拒否する。**
成果物はアカデミアのプロトタイプであり、仮想リスクだけの gate・検査・台帳は足さない。ただし絶対規律と実測された欠陥の修正はこの制限の外。

# 依頼 — レンズ B「過剰・削除」(DW-S03 の過剰・削除レンズ)

1. 差分のうち、裁定 (s4-ruling.md) と依頼に対して過剰なもの (要らない test・定数・docs 文、DW-G05 の成果物影響 1 行を示せないもの) と、逆に足りないもの
   (依頼の生死確認・記録項目で実装側に要るのに落ちたもの) を挙げよ。
2. docs 予算: `DEV_WAVE_L1_5_BYTES_MAX` を 9_696 → 9_788 に上げた判断 (D782: 既存記述の削減を試してから最小増分) が妥当か。DW-O01 の追加 1 文を
   既存記述の削減で収容できる余地が実際に無いか (具体的に削れる文を示せるなら示す)。`.claude/commands/rulings.md` の空白詰め 3 行が
   「既存命令の意味を変えず縮約」に当たるか。
3. `tools/dev_waves/effort_levels.py` の docstring 追記が実態 (依頼の指定) を超えて主張していないか。
4. 規律 7: 過去記録の sol/medium、`test_s8b_ratified_freeze.py` の例示値、role adapter、`tools/codex_reasoning_ab.py`・`tools/t189_*` を触っていないか。

# 出力形式

markdown。各所見を「### RB-n 題」+ 重大度 (must-fix / should / nit) + 根拠 + 放置時の成果物影響 1 行 + 推奨。最後に「## 総括」。
