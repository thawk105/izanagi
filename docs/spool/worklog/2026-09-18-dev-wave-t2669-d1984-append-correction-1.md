---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-18
wave: dev-wave-t2669-d1984-append-correction
seq: 1
title: [T-2669] D1984 の却下欄「二読 fallback の択一は未裁定」を D1872 裁定済み (実装 entry 1594) の追記で訂正する D を起草した — 決定の効力は維持、新たな択一は起こさない (docs のみ、branch worktree-dev-wave-t2669-d1984-append-correction、変異 matrix 免除 = 実装面差分ゼロ)
---

## 本文

- ユーザー依頼は「[T-2669] (P2、entry 1596、D2104 項 18 で裁定済み) docs/decisions.md D1984 の却下欄にある『二読 fallback
  の択一は未裁定』を、D1872 で裁定済み (実装は entry 1594 で着地) である旨の追記で訂正する。canonical は直接編集せず
  docs/spool/README.md の形式で decisions fragment (追補) を書く。既存裁定の訂正記録に限り、新たな択一の再審議へ広げない。
  docs のみ、実装面差分ゼロ。着手直前の local main から fresh worktree。本題の追記だけ。仮想リスク向けの gate・検査・台帳・
  一般化の追加は scope 外」。
- **閉じた (D 1 本 = {{D:d1984-rejection-reason-superseded-by-d1872}})。** canonical 3 台帳は 1 byte も触っていない
  (fold が末尾へ追記する)。実装面ゼロ、insight は作らず (実測値なし)。
- 一次資料の鎖を親が現物で確認した: D1872 (2026-09-09、択 (ii) = v2 fallback 廃止・exact 必須) → D1984 (2026-09-14、
  却下欄 3 項目目「二読 fallback の択一は未裁定」) → entry 1594 (2026-09-17、T-2067 実装着地、D2102 が同じ不整合を認識し
  D1872 を裁定済みとして扱った) → entry 1596 (第 20 回 /rulings、起点) → D2104 項 18 (a)。訂正対象は却下欄の逐語 1 項目に
  限り、D1984 の決定文 (「未配線 2 群の扱いも変えない」は 09-14 時点で偽ではない) と D1872 の決定内容には触れない。
  却下欄当該項の結論は主決定 (メタテスト不新設) に含意されるため効力を維持する、と D に明記した。
- 軽量版 (docs-only)。段 2・3 省略 (択は D2104 項 18 で尽き、残るのは既裁定の転記)。実装子なし。段 6 相当として
  read-only codex レビュー 1 本 (`gpt-6-astra`、一次資料照合 + 過剰・削除の 2 レンズを 1 本で担う) を回した — REVIEW_RESULT。
  dev-wave 改善候補 0 (段 8 は無言通過)。
- 検査: `tools/check_docs.py`、`spool_fold.py --dry-run`、`git diff --check`、provenance 監査。受入全走は land 前に 1 回
  (結果は land の受領証)。

## 次の一手差分

### 完了

- [T-2669] D1984 の却下欄の誤記を {{D:d1984-rejection-reason-superseded-by-d1872}} の追記で訂正した (決定の効力は維持)。
  remaining: none
  base: e3cdc52d04f331c0a42d6b3d91b7e92b7d6237835e50313b03025db05e5b99e2
