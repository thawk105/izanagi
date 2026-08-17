# 既知赤の機序確定と evidence grace 起点の裁定パッケージ (2026-08-17)

wave: `worktree-dev-wave-known-reds` / 依頼「既知赤のテストがあれば適切に直す。リワードハック禁止」
実装差分ゼロ (段 4 で「実装しない」と裁定)。

## 何が確定したか

F57 族 (`test_codex_worker_launch.py` が 48-worker 全走でだけ rc=1 / 出力空で落ちる) は
2026-07-30 から 20 回以上再発し、原因未確定が続いていた。2026-08-17 の [T-190] 計装が
「retry の attempt 2 で preflight が 3.6 倍になり evidence grace 1.0 秒を食い切る」まで確定させ、
本 wave がその先を静的解析で詰めた。

1. **容疑者の片方を構造的に除外した。** codex executable の再 hash は
   `tools/codex_worker_launch.py:1670`、sidecar の計時起点 `attempt_started_ns` は `:1698`。
   `phase_duration_s.attempt_preflight` は起点以降しか測らないので、実測された 1.04〜1.11 秒に
   再 hash は含まれない。計測区間の中身は `_require_attempt_hook_installation` (`:1764`) だけ。

2. **本当の欠陥は 3.6 倍ではなく evidence grace の起点だった。**
   `evidence_deadline_ns = state.started_ns + evidence_grace_s` (`:1797-1800`) の起点は
   preflight の前、子の spawn は preflight の後 (`:1778`)。強制停止条件 (`:1882-1891`) は
   spawn 直後の最初の poll で必ず成立する。よって preflight が grace を超えた瞬間、
   子は生まれた直後に必ず殺される。[T-190] の 3 bundle は preflight 完了と SIGTERM が
   1 ミリ秒差 (1.053/1.054、1.042/1.043、1.105/1.106) で、これと完全に一致する。
   preflight が正常な 0.29 秒でも子の実効猶予は 0.71 秒であり、この gate の閾値は最初から負荷依存。

## なぜ直さなかったか

唯一の修理経路 (起点を spawn 後へ移す) は、現行で強制停止されていた attempt を
accepted の 7 条件へ到達させる = 受理集合の拡張である。`--evidence-grace-s` の意味を定義した
decision も help 文も repo に無い (実測) ため、意図が未確定の契約を親が一方的に決めることになる。
DW-S04 に従い裁定パッケージへ返した。

他の経路はすべてリワードハックとして不採用: 予算引き上げ (台帳 [T-1298] 自身の警告)、
hook / guard 再検証の頻度削減 (attempt 間 drift の門)、sleep、tmp mirror への退避、
受入での xdist 直列化、再 hash 削除。

## 逐語

- `verbatim/s1-brief.md` — 親 brief (provisional 裁定 P1/P2/P3 を含む。3 つとも子に否定された)
- `verbatim/s2-plan.md` — 段 2 プラン (codex `reasoning=max`、read-only)
- `verbatim/s3-lensA.md` — 段 3 敵対レンズ A (正しさ境界・受理集合)。起点変更を
  「高速化ではなく受理集合の拡張」と判定した本文を含む
- `verbatim/s3-lensB.md` — 段 3 敵対レンズ B (実効性・到達可能性)
- `verbatim/s4-ruling.md` — 段 4 裁定
