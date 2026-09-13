---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-14
wave: dev-wave-license-polyform-nc
seq: 1
title: izanagi 本体のライセンスを PolyForm Noncommercial 1.0.0 に確定した (docs のみ、branch worktree-dev-wave-license-polyform-nc)
---

## 本文

- ユーザー裁定: 「PolyForm Noncommercial 1.0.0 のライセンスを izanagi/ に追加してくれる?
  非商用の研究・検証・改変を認めながら、商用利用には許可を求める方針です」。README の
  「未定 (Phase 進行中は private 想定)」を置き換える確定裁定として扱った。設計判断は
  {{D:license-polyform-noncommercial}}。
- 子を起動していない。`docs/ai-provenance.md` の実装面定義に root の `LICENSE.md` と `README.md` は
  当たらないため、Codex author を要さない docs-only の軽量版と裁定した。実装面の差分がゼロなので
  変異 matrix は免除し、受入全走は免除しなかった。
- 本文の逐語性は実測で担保した。配布元の公式 plain text (4563 bytes、sha256
  ffcca38841adb694b6f380647e15f17c446a4d1656fed51a1e2041d064c94cc8) をそのまま置き、先頭の
  `Required Notice:` 行と空行を除いた残りが原本と byte 一致することを diff rc=0 で確認した。
- 親が裁定した割れうる前提 4 件。(P1) ファイル名は `LICENSE.md` — 配布物が markdown で、無保証条項の
  強調が「目立つ表示」として意味を持つため、plain text 化して強調を落とさない。(P2) `Required Notice:`
  の著作権者は git author identity の `thawk105` — 実名・所属の一次資料が repo 内に無いので推測しない。
  (P3) 商用利用の窓口は README に書き、メールアドレスは新たに載せない。(P4) 著作権年は 2026 単年 —
  最初の commit が 2026-06-04、最新が 2026-09-14。
- pin 閉包 (`DW-O09`) は 0 件だった。`LICENSE` の path 検索で当たるのは masstree の fixture だけで、
  root の `README.md` を bytes で束縛する台帳・test も無い。`README.md` は `tools/check_docs.py` の
  LIVING_DOCS なので lint 対象であり、緑を実測した。
- 検査の実測: `check_docs.py` 違反なし / `git diff --cached --check` rc=0 / 三軸語走査
  (`s8b_holdout_freeze search`) rc=0 / provenance full 監査 9752 件で新規違反なし。
- 受入全走 attempt 1 は `child-green` (23310 passed, 68 skipped)。claimed_main
  30efab0c48fd9b1a0ec9716e8468e3f42961ce2f を取り込んだ後の tip で走らせた。

## 次の一手差分

### 新規

- {{T:license-copyright-holder-naming}} **P3・新規**: `LICENSE.md` の `Required Notice:` 行と README の
  商用窓口が指す著作権者表記を、実名・所属・連絡先へ差し替えるかユーザーへ確認する。現状は repo 内に
  一次資料のある git author identity を使っている。差し替えは 1 行で済む。
