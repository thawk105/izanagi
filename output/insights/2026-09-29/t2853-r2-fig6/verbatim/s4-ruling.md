# 段 4 裁定 — [T-2853] R2 fig6 (2026-09-29 JST、親)

## 段 2・3 を省いた理由 (DW-C00 の軽量版)

- 設計の択一が割れない: 依頼が経路 (現行 repo の driver・現行 policy 5 node) を名指しし、driver・job body・policy・生成器は変えない。
- 正しさ防壁・受理集合を変えない: 正しさ検査は job 内の既存経路のまま。repo の実装面 (D95 決定 2) の差分はゼロ。
- 生成器の入力束縛 (pin 表) を差し替える点は、生成器が持つ既存の Python seam `main(..., expected_hashes=...)` を使うだけで検査を外さない。wrapper は repo 外の使い捨てで、段 6 で read-only レビュー 2 本を当てる。

## 裁定

| 項 | 裁定 |
|---|---|
| (P1) 投入元 | 採用。現行 main `035fc11fa` の detached checkout `/work/1/SFC/tanab/tmp/t2853-r2-fig6-20260929/submit-tree` (`git worktree lock`)。wave 側の commit が job の `IZANAGI_A2_EXPECTED_HEAD` 検査を壊さないため。先例 b7f5 / t2489 と同じ submit-tree 型 |
| (P2) caption | 採用。生成器の既定文 (attempt ID・request・host・時刻・効果を記録から組む) のまま差し替えない。R2 の地位は insight §0 と出力名 `fig6_r2_…` で示す。生成器を変えずに caption の役割語を変える置換は、fig8b と違い caption に偽になる役割語 (primary 等) が無いので不要 |
| 見積りと確認 | t2489 の (a) Elapse を当てて測定 1.96 node 時間 + 受入 1 回 0.25 (見積り) ≈ 2.21。線を越えるので、投入前検査を済ませた後にユーザーへ確認を取る。確認前に qsub しない |
| trace 保全口 | 使わない。`submit_paper_story_a2_certification.sh` の `qsub -v` は env 固定列挙で渡す口が無い。driver 変更は scope 外 |
| collect の書き先 | repo 外の一時 root `/work/1/SFC/tanab/tmp/t2853-r2-fig6-20260929/collect-root` を `--repo-root` に渡す。collect は submit-tree の module から呼ぶ (submission receipt が policy 絶対 path を束縛するため)。原 attempt の tracked 成果物には書かない |
| attempt ID | `t2853r2-20260929a` (起動時検査で落ちたら `…b`、`…c` と進める) |
| wrapper (段 5) | Codex author 1 本。`.codex/worktrees/` の子 worktree の `scratch/` に書かせ、親が実行後 repo 外 (`/work/1/SFC/tanab/tmp/t2853-r2-fig6-20260929/tools/`、最終的に測定側の置き場) へ退避。repo には入れない。subcommand: `r2` (R2 の図)・`table` (原 attempt と R2 の対照表、生成器の `load_measurements` で読む)・陽性対照 (原 attempt を wrapper の r2 経路で描いた `artist_series` が既存 fig6 provenance と一致) |
| 変異 matrix | 免除 (DW-S04: repo の実装面の差分ゼロ) |
| 受入全走 | 1 回行う (DW-S04) |
| 段 6 | Codex read-only レビュー 2 本 (一次資料との照合・正しさ境界 / 過剰・削除) |
