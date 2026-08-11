# 2026-08-12 [T-139] land 2 session 3 — 着手不能の判定と Q6 (未 land branch の滞留)

wave `dev-wave-t139-manifest-land2-s3` / branch `worktree-dev-wave-t139-manifest-w2`。
**実装面差分ゼロ。land していない** (S6 (a)、本 session は最終ではない)。

## この session が何をしたか

指示は未実装 5 層 (`submit_pilot` + durable submission intent / PBS preflight・実 driver・
collector / `PreregBinding` 必須 receipt writer / iteration 毎の correctness verifier /
certified 適格性判定・選択・材料レポート・試行台帳 consumer) を進めることだった。
**段 1 の実測で 5/5 が session 2 の未裁定 Q1/Q2 の下流と判明し、`DW-STOP`
(ユーザー裁定待ち) で停止した。**

| file | 内容 |
|---|---|
| `verbatim/s1-brief.md` | 段 1 brief — 6 件の実測、S6 (a) の判定、層別の閂表、(P1)(P2) |

裁定の正本は **session 2 の `output/insights/2026-08-11_t139-manifest-land2-s2/package.md`**
(Q1〜Q5) と、本 session が作った repo 外の控え
`/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-12-t139-land2-s2-five-rulings.md`
(Q1〜Q5 の要旨表 + **Q6**) である。

## 層別の閂 (段 1 brief の表)

| 命名された層 | 直接の閂 |
|---|---|
| `submit_pilot` + durable submission intent | **Q1 の B2 そのもの** (intent 母集合 authority / canonical namespace / `O_EXCL` 発行履歴が承認済み文書に無い) + D292 |
| PBS preflight・実 driver・collector | 上記の下流。B1 (`CMakeCache` raw pointer) と B4 (transcript byte grammar) を先取りしないと受理述語が書けない |
| `PreregBinding` 必須 receipt writer | resolver = **Q2** (manifest 表現未裁定) の下流 |
| iteration 毎の correctness verifier | S7 #4。driver と材料 report の下流。`DW-G04` の発火 artifact path が書けない |
| certified 適格性判定・選択・材料レポート・試行台帳 consumer | validator = **Q1** の下流 |

## 先取り実装を却下した理由

承認済み `record-items-v2.md` / `receipt-schema-v1.json` は D282 で exact bytes 承認済みで
bytes を変えられない。この状態で collector や validator を書くと、存在しない入力を producer の
申告値 (`cmake_cache` / `fixed_inputs` / `len(consumed_cluster_slots)`) で代用することになり、
**§8 の否定検査が「受理条件の入力に使ってはならない」と列挙した field で通ってしまう
validator** を作る。session 2 の 2 レンズが独立に最大 risk と名指しした形である (規律 2 の面)。
`orchestrator/preregistration/` を呼ぶ非 test caller は repo 全体で依然 **0 件**であり、
発火 artifact path が書けない休眠コードになる (`DW-G04`)。

## 新しい所見 2 件

1. **裁定待ちが canonical 台帳から見えない** (failures fragment で新規 F を起票、番号は fold が付ける)。
   package も fragment の `更新` も**未 land branch 上にしか無い**ため、
   canonical の `[T-139]` は carry stub のままで 2026-08-12 の /rulings 12 束から落ちた。
   **wave 側の記録は正しく書かれていた** — 落ちたのは収集側の母集合である。
   S6 (a) がこの不可視を構造化する (裁定待ち → land 不能 → 不可視 → 裁定されない)。
   → 控えを inbox へ置いて迂回し、**Q6** として構造の扱いを裁定へ返した。
2. **先行 fragment の `base` が main の前進で stale になっており、fold は本 session 開始時点で
   既に不能だった** (自 fragment を外しても `base-mismatch`)。session 1 の申し送り 1 が
   予告していた形である。現行値へ直して `planned` に戻したが、**land 直前の再算出は依然必須**。

## 走らせた検査

`check_docs.py` rc=0 / `spool_fold.py --dry-run --show-diff` rc=0 (`planned`) /
全史 provenance 監査。**受入全走は走らせていない** — 変更は docs + repo 外のみで実装面差分ゼロ、
land しないため certify する tip が無く、最終 session が記録 commit 込みの最終 tip で
再走する義務がある ([T-836] (c)、[T-648] fallback に従い判定根拠を worklog fragment へ記録)。
