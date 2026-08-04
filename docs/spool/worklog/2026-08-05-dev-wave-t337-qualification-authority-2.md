---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-05
wave: dev-wave-t337-qualification-authority
seq: 2
title: 段 8 の dev-wave 改善候補 1 件は byte 予算に阻まれた — 統合を試して実測し、上限は上げずに戻した (docs のみ、branch worktree-dev-wave-t337-qualification-authority)
---

## 本文

- **段 8 の候補は 1 件、実測付き。** 本 wave の親 brief は「適格性 field を読む consumer は 0 件」と
  書いたが、敵対 2 レンズが独立に反証した — 定数を exact 照合するだけの参照も、不一致なら計測を
  止める authoritative な consumer である。正しくは「**昇格**権威として読む consumer が 0 件」だった。
  `DW-S01` へ「consumer 不在を前提にするときは、どの種類 (昇格・拒否・表示) が不在かまで書く。
  定数照合だけの参照も authoritative な consumer である」を統合する案。
- **実際に統合してみて、byte 予算で入らないことを実測した。** 追加は 186 bytes、`docs/dev-wave/**` の
  合計は 25,196 / 25,200 bytes で**余裕は 4 bytes** しかなく、`check_docs.py` が hard ceiling 違反で
  赤になった。編集は戻し、検査の緑を回復済み。**上限の引き上げは提案しない。** 意味等価な縮約で
  186 bytes を回収する案も、安全義務の文言を削る方向にしか届かないため採らなかった。
- **もう 1 件は実測が無いので候補にしない。** 段 3 の子へ前段の成果物を読ませる際、job 用
  subdirectory は子の sandbox root の外にあるため、親は逐語を repo 内へ複製してから絶対 path で
  渡した。ただし「複製しなければ読めなかった」ことは測っていない (先回りで複製した)。
  仮想的懸念だけで reference を変更しない契約に従い、記録だけに留める。

## 次の一手差分

### 更新

- [T-341] **P3・候補 1 件と予算実測を追加**: 本 wave の段 8 候補も同じ byte 予算に阻まれた。
  (e) **`DW-S01` に consumer 不在の粒度規律を足す** — 「◯◯ を読む consumer は 0 件」と書くときに、
  どの種類 (昇格・拒否・表示) が不在かまで書かせる。定数照合だけの参照も authoritative な
  consumer であり、これを見落として親 brief が誤った前提を立て、敵対 2 レンズが独立に訂正した。
  **必要 186 bytes に対し `docs/dev-wave/**` 合計の余裕は 4 bytes** (25,196 / 25,200) で、
  実際に統合して `check_docs.py` の hard ceiling 赤を実測してから戻した。
  意味等価な縮約は安全義務の文言を削る方向にしか届かないため採らない。
  **上限引き上げは提案しない。** 既存の裁定どおり [T-328] の外出し枠へ相乗りさせる
  base: d074a7fe9a2fd61d6dd920afc245429da8ffb47fe51d407305fd7adbcd431a87
