---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-25
wave: dev-wave-t1606-known-violation-entries
seq: 3
title: [T-1606] known-violation 台帳を 1 finding 1 file へ移し、逐語 mirror を append-only 履歴不変条件で置換した (コード + テスト、branch worktree-dev-wave-t1606-known-violation-entries、変異 matrix = baseline PASSED・15/15 KILLED・SURVIVED 0)
---

## 本文

- ユーザー裁定は D743 で確定済み。必須条件は D738 の列挙。段 4 直前に裁定 inbox を再走査し、
  wave 開始後の T-1606 関連の更新が無いことを確認した。
- **裁定の 5 検査だけでは置換が成立しないと判明した。** 段 3 の敵対相談が、filename に本文の
  SHA-256 を入れても書き換える側が digest を再計算できるため**裁定根拠の認証にならない**と
  示した。1 entry を書き換えて rename するだけで、全検査・全史監査・land 受領証が偽造後の値を
  自己追認する。親は append-only 履歴不変条件を必須で加える裁定に変えた ({{D:append-only-replaces-literal-mirror}})。
- **親の段 1 の記述を 2 件撤回した。** (1)「台帳を外へ出すと land 受領証の束縛から外れる」は
  誤りで、`tip_sha` が registry tree を推移的に束縛している。段 3 の 2 レンズも独立に同じ
  結論に達した。よって land 関門は本 wave の編集面から外した。(2)「台帳末尾の競合から生まれた
  違反が 13 件」は数え方が緩く、`note` に「競合」を含む件数にすぎなかった。厳密に
  `KNOWN_PROVENANCE_VIOLATIONS` を競合面として名指しするのは **5 件**、台帳 file に触れつつ
  競合・union に言及するものまで広げて **11 件**である。因果の一般化はしない。
- **移行の同値性は実装前に凍結した digest で閉じた。** 移行後の検査群だけでは、generator の
  誤写も自己整合して全部通ってしまう (段 3 の指摘)。実装前に 53 entry の
  `{sha, kind, value, ruling, note}` を sort_keys 表現して連結した SHA-256
  (`ccc77e27e5d74bab3f06648d14b26131bf5447335a98bb682eb45dbe7aa66001`) を凍結し、
  移行後に親が照合して**完全一致・欠落 0・余分 0・canonical 違反 0** を確認した。
  この照合は一回限りなので repo へは入れない。
- **段 6 の敵対レビュー 2 本が、緑のまま残っていた穴を 6 件見つけた。** 最も重いのは
  append-only 検査が (a) merge を親別に分解せず history simplification と file type 変更を
  見逃すこと、(b) **`main()` から呼ばれておらず land の全史監査でも発火しないこと**である。
  後者は {{F:gate-defined-but-not-wired}}。両レンズが独立に同じ核心へ到達した。
  2 件は不採用にした — 固定 SHA 一覧は新規登録で編集を要求しないため共通編集面ではない。
- **変異検査が、敵対相談もレビュー 2 本も見つけられなかった被覆漏れを 2 件見つけた。**
  `-m` を外す変異が生存し、実測すると既存の merge 負例は side branch 側 commit が改変を持つ
  形なので `--full-history` だけで捕まっていた。**merge commit 自身が改変を持つ evil merge**
  は `-m` 無しで完全に不可視だった (現行 4 行 / `-m` 除去 0 行)。{{F:append-only-blind-to-evil-merge}}。
  もう 1 件は実装の穴ではなく、worktree bytes の照合と filename digest の照合が**互いを
  mask していた**ためで、両層同時変異で初めて forge が受理された。診断文字列を逐語照合する
  負例で単一理由化した。
- **件数 pin を禁じた** ({{D:no-data-derived-count-pins}})。並行 2 wave が両方 `53 -> 54` へ
  直すと、data は union されて 55 entry になる一方 test は 54 を期待し、**競合なしで赤になる**。
- **目的を実測で示した。** 移行前は別 entry を足す 2 branch が 2 file・各 1 hunk で CONFLICT
  (merge rc=1)。移行後は同じ土俵で **conflict 0・merge rc=0**、loader も 55 entry を受理した。
  同一 `(sha, kind, value)` を ruling 違いで足すと git は自動 merge するが **loader が
  duplicate で停止** し、D738 が定めた fail-closed が実際に発火した。同一 bytes は 1 file へ
  収束して受理される。**「競合ゼロ」とは書かない** — 正しい主張は「異なる identity の entry は
  自動 merge され registry も union を受理する。同一 identity の食い違いは fail-closed で止まる」。
- 子は 4 単位とも pytest 実走不能 (`qstat -Q preflight rc=1`、sandbox の構造的制約)。
  **本 wave のテスト結果はすべて親の実測**である。
- 段 3 の lens B は `evidence_status=invalid` で 4 回不採用になり、完成済み成果物 4 本と
  約 70 分を失った。既知 2 原因 (web 検索・非 NFC) を**両方とも反証**した。F217 の再発として記録する。

## 次の一手差分

### 完了

- [T-1606] entry 単位格納へ移行し、逐語 mirror を append-only 履歴不変条件と負例群へ置換した。
  移行の同値性は実装前に凍結した digest との照合で確認した。並行追加の union と
  同一 entry の fail-closed を実測で示した。
  remaining: none
  base: 5595525babd95adee662bc5042b860ef490ed726b7e5ad06a6e4bc3f7304ee79

### 新規

- {{T:codex-evidence-invalid-third-cause}} **P2・新規**: `evidence_status=invalid` の第 3 の原因を
  特定する。web 検索と非 NFC は本 wave で反証済みで、最終 artifact は判定条件を全部満たすため
  tailing 中の sticky flag が疑われる。判定を最終 artifact の再検証で確定させる案を検討する。
