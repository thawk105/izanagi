---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-09
wave: dev-wave-t648-fallback-ledger
seq: 1
title: [T-648] 受入免除判定の証拠記録義務を fallback (台帳 + memory) で発効させた — 契約本文は 1 byte も変えず、本文昇格は再訪条件付きで見送り台帳へ (docs のみ、実装差分なし、branch worktree-dev-wave-t648-fallback-ledger)
---

## 本文

- **ユーザー裁定 2 件に基づく fallback 実施 wave。** (1) 2026-08-08 /rulings: [T-648] = (b) +
  遡及なし — 「実 repo を読むテストがあるか」の判定証拠 (該当 nodeid か「不存在」の判定手順) の
  worklog 記録を dev-wave 契約へ 1 文足す。**予算内に収まらなければ [T-641] (c) と同型に台帳記録へ
  落とす** (rulings branch `worktree-rulings-20260806-a` の fragment seq 25、本 wave 時点で未 land)。
  (2) 2026-08-09 本セッション、ユーザー逐語「(B') 再訪条件付き fallback で進めて」。
- **発効させた義務 (正本 = 本エントリ + memory `record-acceptance-exemption-evidence`):**
  docs-only / 実装差分ゼロの wave が受入全走の要否を判定するときは、「実 repo を読むテストが
  あるか」の判定証拠 — 該当テストの nodeid、無ければ「不存在」と判定した検索手順 — を
  worklog (fragment) へ記録する。
- **契約本文は変えていない。** `docs/dev-wave/**` の aggregate は 25,199 / 25,200 bytes
  (空き 1 byte)、dispatcher は 9,457 / 9,500 bytes (空き 43 bytes) を本 wave で実測し、
  裁定 (b) の 1 文はどこにも入らない。[T-664] は未 land のうえ branch 側の結論が
  「依頼 2 経路で解放 0 bytes」のため、予算待ちをやめ fallback 条項を発動した。
  memory への固定は repo 予算を使わない (t664 wave 段 8 の memory 固定と同型)。
- **canonical decisions の旧射程記載 (D72 ほか) は遡及改変していない** (裁定どおり
  前向き supersession のみ)。
- **義務の初回適用は本 wave 自身。** 実 repo を読むテストは存在する — 判定証拠 =
  `orchestrator/tests/test_check_docs.py` / `orchestrator/tests/test_spool_fold.py`
  (いずれも実 checkout の docs/ と spool を読む) — したがって docs-only だが受入全走を実施する。
  受入結果はこの commit 時点では未実施 (投入前に fragment を先に commit する順序のため)。
  実測後に本行を再走値で更新する。
- 実装差分ゼロのため変異 matrix は免除 (`DW-S04` の免除条項)。子エージェントは起動していない
  (docs-only は子ゼロ、`DW-C00`)。

## 次の一手差分

### 見送り

#### プロセス文書系

- [T-648] 受入免除判定の証拠記録義務の契約本文への明文化 — 理由: 義務は fallback
  (本エントリ + memory) で発効済みで、契約 1 文の追加は dev-wave docs 予算 (空き 1 byte) に
  入らない ([T-641] (c) 同型)。再訪 = [T-313] 実装などで `docs/dev-wave/**` 予算に空きが
  出たとき、本文 1 文への昇格を再検討する (2026-08-09 ユーザー裁定 (B') による再訪条件)。
  base: 054c83f5793e127d0adfaedab4d5b321d5fde9c1af920ce433a1f37c46a1c8ee
