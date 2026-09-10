# 逐語保存の正規化

authority: none
default_effect: no-state-change

git diff --checkで末尾空白が検出された3fileだけ、各行末の半角空白2字を除いた。可視文字は不変。以下の行へ半角空白2字を戻し、保存時に付けた最終LFを除くと原文bytesを復元できる（原文3fileはいずれも最終LFなし）。

- consult-a.md: 原文SHA/bytes = a0dcd9b093309a490bc5b0b76882f2a8bfd8b153e8952730dd9b056dd080b6dc  /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/output/insights/2026-09-10_t2581-k2-pin/reviews/consult-a.md / 4614 /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/output/insights/2026-09-10_t2581-k2-pin/reviews/consult-a.md。復元対象行: 3, 4, 5, 8, 9, 10, 11, 14, 15, 16, 17, 20, 21, 22, 25, 26, 27, 28。
- consult-b.md: 原文SHA/bytes = d93fe9ef51b662d2f003fc96bc4a1f1147bfb1703b639225b0905b34e2d78917  /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/output/insights/2026-09-10_t2581-k2-pin/reviews/consult-b.md / 3766 /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/output/insights/2026-09-10_t2581-k2-pin/reviews/consult-b.md。復元対象行: 3, 6, 9, 12, 15。
- review-a.md: 原文SHA/bytes = 71d25ebc52f75fd392fbe0d61fdff4e62f1db4cb022abaa1374f8fd618a7f75f  /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/output/insights/2026-09-10_t2581-k2-pin/reviews/review-a.md / 3112 /work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t2581-k2-pin/output/insights/2026-09-10_t2581-k2-pin/reviews/review-a.md。復元対象行: 3, 4, 7, 8, 11, 12, 13, 16, 17。

planの「4ファイル」表現は原文のまま保存した。親裁定の最終scopeは5file、7桁互換案は不採用で40桁限定。原文はrepo外の各worker artifactにも保持している。
