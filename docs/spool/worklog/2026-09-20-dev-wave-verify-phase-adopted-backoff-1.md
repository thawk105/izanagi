---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-verify-phase-adopted-backoff
seq: 1
title: 採用候補 fixed-5 / fixed-10 の検証相 (独立 8 反復 × 3 workload、trace-enabled、extime 3 s) を Pegasus で通し、両候補とも 24 枠すべて serializable・certified・anomaly 0 (S-1 (iv 付属) 規則の準用、docs + insight、runner は job dir、branch worktree-dev-wave-verify-phase-adopted-backoff、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー裁定 (2026-09-19、逐語は `rulings-inbox/2026-09-19-verify-phase-adopted-backoff-authorization.md`): 対象 = T-1998 事前登録の採用 arm と
  A-2 observed-positive の固定 backoff 値、各候補 N_verify = 8 独立反復 × 3 workload、total 予算 ≤ 4 時間/候補 (超過見込みなら extime を下げ N は削らない)、
  24 verify すべて anomaly ゼロで pass・1 件でも anomaly なら失格、長 extime は {3, 6, 10} s の校正で 1 verify ≤ 10 分の最大値、規律 1 の build 分離、
  verifier は `python3 -m orchestrator.verifier`、seed identity と trace の保全先を記録、1−εⁿ は主張しない、複数ノードへ同時投入。scope 外 = 新 protocol・追加 gate・certification の昇格。
- **結果:** 候補 2 genome (fixed-5 = `BACK_OFF=1, BACKOFF_FIXED=5` = T-1998 v1 target = A-2 rr50 採用値、fixed-10 = A-2 rr5 採用値) について、校正 (段 A、6 job) で
  extime を両候補とも **3 s** に確定し (適格集合 write-heavy {3, 6}・balanced {3, 6}・read-heavy {3} の共通部分)、本走 (段 B、12 job × 4 反復) の 24 枠が
  両候補とも全件 `serializable`・certified・anomaly 0。runner の `summarize` が段 4 裁定 §4.1 を機械適用して **fixed-5 = pass、fixed-10 = pass**
  (判定集合 30 verify / 候補 = 本走 24 + 校正完走 6、anomaly 0)。校正 10 s の未完走 (balanced = SIGKILL `killed_unknown` ×2 node、write-heavy = hard timeout 3600 s)
  は候補あたり 2 件で verdict を持たず開示のみ (trace 保全済み)。本走の実消費 (dispatch Elapse 和) = fixed-5 6316 S、fixed-10 6134 S (≤ 14400 S)。
  校正の実消費は別欄 6462 / 6339 S。一次資料 `output/insights/2026-09-20/verify-phase-adopted-backoff/README.md`、単独 results 稿
  `docs/paper-story/results/2026-09-20-verify-phase-adopted-backoff.md` (paper-story README の results 表と stale 注記 (B-8) に 1 項ずつ)。
- **位置づけ:** S-1 事前登録 (iv 付属) の充足ではなく、裁定で対象を変え同節の規則を**準用**した追加検証 ({{D:verify-phase-adopted-backoff-authorization}})。
  操作的事実であって確率主張ではない。性能値は含まない (規律 1)。A-2 / T-1998 / A-6 の certified 記録は昇格も降格もしない (規律 7)。
- **裁定時の未見事実 2 点 (段 1 で実測、段 4 で処置):** (1) `docs/phase3-main-experiment.md` は `output/s1-freeze/known_axes_freeze.json` の source sha256 として
  凍結され、1 行追記の模擬で `verify_document` が `FreezeError: source sha256 不一致` → 「確定値は本節へ日付付き追記」は本 wave では**未履行の繰延べ**とし、
  D fragment・insight・results 稿に日付付きで記録 (凍結再発行・`IZANAGI_FREEZE_HOLD` の解除は行わない)。(2) A-2 attempt `t2364-20260907b` の `src_token` は
  patch 改訂 `91a5bfca3` (999→9999 µs 拡張、5/10 µs の分岐は不変) 前の値で、現行 source の identity (fixed-5 `678b7203…` = T-1998 v1 と一致、fixed-10 `16c29935…`) と
  不一致 → 期待値は現行実測値に固定し、A-2 の旧 token は履歴併記、A-2 当時の source での建て直しは不採用。
- **07-16 校正器からの意図的変更:** 校正 verifier の未完走を「校正全体の失敗」でなく `indeterminate` として開示付きで記録し、完走 prefix から extime を決めた。
  理由は Pegasus gen_S の DRAM 上限が資源事実で正しさシグナルでないこと (旧規則では balanced 10 s の kill (`killed_unknown`、原因未確定) で今回の校正が未確定になり本走へ進めない)。規律 2・3 は緩めない。
- 進め方: 段 2 plan 1 + 段 3 敵対相談 2 (A = 正しさ境界・事前登録整合、B = 実効性・資源) → 段 4 裁定 (`s4-ruling.md`、全規則を段 A 前に書面固定、§7 は段 A 後の計算結果の追補のみ)
  → 段 5 Codex `role=author` 1 本 (runner 1301 行、sha256 `91bbf85d…`、login selftest 42/42) → 段 A 校正 6 job (request 10868〜10873、投入 2026-09-19 22:46、最後の job 終了 00:01:24、集計 00:02:02 JST、記録 18 = 実走 16 + 未実走 2) →
  段 B 本走 12 job (11268〜11279、00:04〜00:43 JST、submit-tree 12 本、node-local build) → 段 6 fix 1 (Codex): 裁定文書が規則と追補を 1 file に持つため
  段 A / 段 B の記録で `ruling_sha256` が異なり `summarize` の混入検査が `undetermined` を返した → 段 A 版を復元して差分が §7 だけであることを実測し、
  `--accept-ruling-sha` (許可集合の明示、段別 sha の開示、無指定時の挙動不変、selftest 42→49) を足した v2 (1384 行、`c960093d…`) で最終集計。判定を親が手で書き換えていない。
  → 段 6 独立レビュー 2 本 (A: NO-GO must-fix 1 = 段 3 B2 の walltime 上限式は hard timeout 3600 s に更新されず「処置済み」と書けない → 上限保証は未実装・実測最大 (dispatch Elapse 4063 S / runner job wall 4057.9 s) は予約内・B2 は会計範囲のみ処置と記録、should 2。
  B: NO-GO must-fix 3 = CPU 時間の転記 822→816.7 s、時刻の精度と時系列 (extime 決定 = summary-A 00:02:02、§7 見出しの 00:05 は誤りで erratum)、18/66 は記録件数で実走 16/64、should 2 = 合計消費 12,778 / 12,473 S の追記)
  + 焦点 1。全所見 real、観測値・判定の変更なし。所見と対応は insight §10。
- 検証相の保全: 64 走 × 48 file = 3072 trace file、原本 213.3 GB → zstd 48.9 GB、job dir `run/` に保全。binary は job (node) ごとに別 build (`binary_sha256` が異なる、
  source identity は候補ごとの 9 job で一致、toolchain は 18 job で同一)。
- 受入全走は記録 commit 後・land 前に 1 回投入する (land 調停役 [58b769] の PREP / GO 直列化に従う)。結果は land の受領証と job dir `HANDOFF.md` に残し、本 fragment は
  受入前に書いたので件数は書かない。phase の実装完了項に対応しないためチェックを新設しない。dev-wave 改善候補は専用 handoff に記録し、改善実装や次 wave は行わない。

## 次の一手差分
