# 依頼

次の親 brief を攻撃可能な前提として読み、Izanagi の dev-wave を Claude / Codex 両方で並行
session 対応にする実装計画を作ってください。

- brief:
  `/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/parent-brief.md`
- repository:
  `/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill`

brief を読めなければ即停止してください。read-only 作業です。ファイルは編集せず、pytest の緑も
要求しません。静的検査で、既存の共通 dispatcher/reference、Codex adapter、startup/supervisor
checker とテストを確認してください。

計画は file:line 粒度にし、次を必ず扱ってください。

1. 他 session の active handoff と専用 worktree コンテナだけを main cleanliness の例外にする exact 条件。
2. accepted-main SHA、wave tip、ff-only をどう束縛し、main が競合 session により前進した race を
   stale 受入結果のまま通さないか。
3. main 前進後に audit、merge、競合解決、受入再走、bounded retry をどの順で行うか。
4. Claude command と Codex Skill が同じ契約を実行し、文章 drift を起こさない正本配置。
5. helper の CLI / exit code / allowlisted Git argv / symlink・path・worktree identity 境界。
6. 正例・負例・race・mutation のテスト計画と、既存 checker との責務分離。
7. brief の P1〜P3 を棄却すべきなら、その理由と代案。

最後に fence 外の `## 総括` で、推奨 plan、blocker、変更対象を簡潔にまとめてください。
