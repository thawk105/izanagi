---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-20
wave: dev-wave-t2610-b7-limited
seq: 1
title: [T-2610] B-7 (全 workload の退行込み報告) の限定付き充足 (D2174 項 3) を腐らない入口 3 か所へ写し、T-2610 を裁定済みで閉じる (docs のみ、branch worktree-dev-wave-t2610-b7-limited)
---

## 本文

- ユーザー依頼 (2026-09-20、dev-wave 引数、D2174 項 3 択 (a)) の範囲で 1 wave: B-7 が**単一 attempt・descriptive・非認証・反復間安定性は未判定**の限定付きで
  充足と裁定され D2044 項 3 が supersede された事実を、`docs/paper-story/README.md` (stale 注記 1 → 2 件、results 系列表の 2026-09-19 稿の行の末尾注記) と
  `docs/paper-story/figures/README.md` (一覧の fig10 行の注記、fig10 節末尾の「追補 — B-7 の限定付き充足」) に写した。新規測定・certified 昇格・有意差判定・
  反復 attempt の認可は含まない。**実装面の差分はゼロ** (変異 matrix 免除、DW-S04)。
- **段 1 で判明した新事実 2 件 (親が段 4 で自己裁定):** (1) 依頼が「稿の追補」と呼ぶ稿 `results/2026-09-19-b7-fixed5-three-workload-regression.md` は results 系列の
  append-only 凍結物で、かつ fig10 の provenance が `caption_source` として稿の SHA-256 `6585d446…` を束縛し着地 test (`validate_repo_closure`) が現 SHA-256 を検査する。
  稿本文へは 1 byte も書けないので、追補は稿の外 (paper-story README の stale 注記 + results 行、figures README の fig10 節) へ置いた
  (先例 = T-1998 単独稿の読解上の追補、旧 fig5 の用途制限の追補)。新しい results file は作らない (1 file = 1 結果の規則、裁定は結果ではない)。
  (2) fig10 節は着地 test が第一レベル見出しで節を切るため、追補は同節内の H2 小節として足した (caption 逐語・SHA 3 行・稿 SHA は不変)。
- fig10 の凍結 caption "This is B-7 material, not a B-7 satisfaction decision (D2044 item 3)." と稿冒頭の「本稿が判定しないこと」は着地時点の記録として保持し、
  追補で「充足の裁定は稿・図の外で D2174 項 3 が行った」と読み替えを示した (fig5 erratum と同じ形)。凍結版 (ストーリー版 2026-09-20 版、claim-evidence 2026-09-20 稿) は
  編集せず、次版の全面再導出で拾う (系列規則、D1858)。
- T-2610 の状態語は entry 1729 の「P2・未裁定」から「裁定済み (D2174 項 3)・反映済み」へ更新し、残件なしで閉じる。凍結版への反映は版系列の規則が拾うので
  active に残さない (手番の無い永久 carry を作らない、F428 型の回避)。
- 軽量版 (段 2・3 省略)。段 5 は親が docs 4 か所を直接編集。段 6 は read-only レビュー 1 本 (gpt-6-astra、13:46〜13:49 JST、`check_codex_output` OK): must-fix 1 (fig10 追補の「区間推定」の除外範囲が既存説明より広い) / nit 2 (一覧 2 行の supersede 対象を「要件充足へ昇格させない」に限定、重複説明の短縮) / (P1)(P2) は refuted = 親の判断維持。3 所見とも real 採用、親が docs を直した (fig10 追補の第 2 bullet を「何を示す図か」への参照へ、第 4 bullet を stale 注記への参照 1 文へ、「論文で使うときに付く限定」→「B-7 の充足裁定に付く限定」)。焦点再レビューは、fix が reviewer の対案の文面をそのまま採り派生値を含まないので省略し、親が逐語 4 か所・caption・SHA 3 行を再検算して closed 3 / partial 0 / regressed 0 とした。焦点走 1 走 (計算ノード request `12603.nqsv`、5 file = fig10 着地 test・figures README を読む a2 / s1 の provenance test・check_docs・spool_fold): **904 passed / 3 skipped (check_docs の成長 hold) / 0 failed、rc=0**。受入全走は記録後に投入し、結果は land の receipt が束縛する (`docs/spool/FOLDED.md` の tested_tip)。
  一次資料は `output/insights/2026-09-20/t2610-b7-limited-satisfaction/README.md`。
- 工数: codex 子 1 本 (review)。計算ノード job = 焦点走 1 + 受入 1 (変異は免除)。

## 次の一手差分

### 完了

- [T-2610] **裁定済み (D2174 項 3、択 (a))・反映済み**: B-7 (全 workload の退行込み報告) は、同一候補 fixed 5 µs の 3 workload 同時期測定と床値判定
  (D2162、稿 `results/2026-09-19-b7-fixed5-three-workload-regression.md`) と図 10 により、単一 attempt・descriptive・非認証・反復間安定性は未判定の
  限定付きで充足と扱う。D2044 項 3 は supersede。反復 attempt は認可しない。限定文言は paper-story README (stale 注記・results 行) と figures README
  (fig10 行・fig10 節の追補) に写した。稿・図・ストーリー版・claim-evidence 稿は凍結のまま (次版の再導出で拾う)。
  remaining: none
  base: a7b142f9ce3a0dddaa191269f8b28eea6c5ab83432ae70f483bff34f6c446cc6
