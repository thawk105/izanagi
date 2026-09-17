---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t1912-prereg-erratum
seq: 1
title: [T-1912] B-4 事前登録 §7.2 / §10 の「4 者の束縛を強制しない」記述を追補で訂正し、publication 間の選別が閉じていないことを文面へ出した (docs のみ、branch worktree-dev-wave-t1912-prereg-erratum、codex 子 0 本)
---

## 本文

- ユーザー依頼は「[T-1912] (D1986 項 3 → 記録手番) B-4 事前登録 §7.2 / §10 で事実と違ってしまった『強制しない』記述
  (block id・precursor・proposal・on/off receipt の 4 者束縛を強制しないと書いたまま。実装は 227ec6892 で着地済み) を
  追補で訂正し、残る publication 間の選別は閉じないことを成果物の文面へ出す (D1884 / D1896 と同じ形)。docs のみ、
  §5 の値セル・凍結 bytes は変えない。本題の追補だけ。仮想リスク向けの gate・検査・台帳の追加は scope 外」。
- **閉じた (追補は着地、残件は裁定どおり据え置き)。** 一次資料は `output/insights/2026-09-17/t1912-prereg-erratum/README.md`。
  前 wave の裁定パッケージは `output/insights/2026-09-14/t1912-pair-completeness/README.md`。新しい設計判断はない
  (D1986 項 3 の実施)。
- 追記 2 箇所 (§7.2「pair の完全性と receipt shopping」項の直後、§10 の同名項の直後、挿入のみ 41 行・削除 0)。
  閉じたと書いた範囲は「1 つの publication の内側での 4 者の束縛」に限定し、束縛が転記の一貫性までであること、
  publication をまたぐ選別が残ること、model/prompt は対象外であることを併記した。§5.1.1 の凍結 bytes・§6 の
  publication root 宣言行 (issuer が「ちょうど 1 行」を検査) は不変。
- **段 1 で新事実 1 件。** 一次資料 (09-14) の「issuer は呼び出しごとに新しい publication root を発行」は 09-16 の
  [T-2545] (D1881、`7b0b43d04`) で変わり、issuer は §6 が名指す 1 root だけへ create-only で発行する。ただし loader と
  材料レポート生成は呼び手の root をそのまま読むので、別 checkout・root 退避後の再発行で複数 publication を作り
  有利な方だけを渡す経路は残る。段 4 で real と裁定し、追記は現行形で書いた。D1986 項 3 の結論は不変。
- 軽量版 (docs-only、codex 子 0 本、段 2・3・6 の子を省略)。変異 matrix は実装面差分ゼロで免除。
- 実走: 焦点走 (事前登録 doc を直接・間接に読む test 10 file、計算ノード dispatch、request 3981.nqsv) 826 passed /
  154.8 秒、赤ゼロ。`check_docs` 違反なし、`spool_fold --dry-run` rc=0、`s8b_holdout_freeze search` rc=0、
  `git diff --check` 0。受入全走は docs commit 後の最終 tip に land 前に 1 回 (結果は land の受領証)。
- 工数: codex 子 0 本。親の実測: 焦点走 1 (計算ノード)、check_docs 1、受入 1。

## 次の一手差分

### 更新

- [T-1912] **P3・裁定済み据え置き (D1986 項 3)**: 4 者 (block id・precursor・proposal・on/off receipt) の束縛は
  1 つの publication の内側で着地済み (`227ec6892`)、事前登録 §7.2 / §10 の追補は 2026-09-17 に着地。残るのは
  publication 間の選別で、D1986 項 3 により閉じない (閉じるには publication をまたぐ追記専用の権威が要り、D1936
  前文・項 8 と衝突)。AI の手番なし。再開条件はこの 2 決定を改める新裁定。
  base: 42c6152f469a9a81b9e92f2901171ca262af9ab9cc27c92f16527a2c5ae93619
