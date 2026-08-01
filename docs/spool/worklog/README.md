# worklog fragment

`docs/worklog.md` の 1 エントリ分。共通規則は `docs/spool/README.md` を正本とする。

本文の H2 は **`## 本文` と `## 次の一手差分` のちょうど 2 つ**、この順でなければならない。

```markdown
---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-02
wave: dev-wave-parallel-docs-spool
seq: 1
title: 並行 docs 衝突を spool + fold で解消する (コード + docs、branch ...)
---

## 本文

- ユーザー裁定・協議の決着、棄却 finding、セッション異常、エージェント工数など
  **git に入り得ない情報だけ**を書く (`docs/worklog.md` 冒頭の書式契約に従う)。
- 設計判断は {{D:parallel-doc-spool}}、失敗は {{F:partial-fold}} のように参照する。

## 次の一手差分

### carry

- [T-298] 変わらず

### 完了

- [T-288] 単位修正を完了し、受入結果を記録した。
  base: <対象 item の現本文の sha256>

### 更新

- [T-304] **P1・ユーザー裁定待ち**: 二択に第三案を足して再提示する。
  base: <対象 item の現本文の sha256>

### 新規

- {{T:fold-crash-recovery}} **P2・新規**: fold の crash resume を追加監査する。

### 見送り

#### プロセス文書系

- [T-305] live role 文面の整理 — 理由: 多世代開放まで発火しないため別 wave 所有とする。
  base: <対象 item の現本文の sha256>
```

## 規則

- **`carry` 節は任意である。** 触れなかった active な T は fold が自動的に carry する。
  明示 carry と暗黙 carry は同じ出力を生む。
  これは並行 wave のために必要である — 他の wave が新しい T を先に fold しても、
  先に書かれた fragment がそれを知らないまま畳める。
- 脱落は fold の**保存則 postcondition** が塞ぐ。
  「出力 active 集合 == 入力 active 集合 − 完了 − 見送り + 新規」を実際に突き合わせて検査する。
- `完了` は**残件なしの終端**にだけ使う。部分完了は `更新` に書く。
  本文に「残件あり」「一部完了」を含む `完了` は拒否される。
- `完了` / `更新` / `見送り` の item には **`  base: <sha256>`** を 1 行付ける。
  対象 item の現本文の digest であり、これが一致しないと fold は停止する。
  別 wave が先に同じ項を書き換えていた場合に、古い本文から作った更新で上書きするのを防ぐ。
- `見送り` は `docs/phase3.md` の見送り台帳に**実在する H3 名**を H4 として指定し、`理由:` を必ず書く。
- item の継続行は 2 space インデントにする。
- エントリ番号・日付・`変わらず ((N) 参照)` の N は **fold が付ける**。fragment に書かない。
