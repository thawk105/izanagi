# failures fragment

`docs/failures.md` へ追記する失敗・near miss・規律違反。共通規則は `docs/spool/README.md` を正本とする。

本文の H2 は `## 新規`、`## 再発`、`## supersede 追記` のうち使うものだけを、この順で置く。
どれか 1 つだけでもよい (`supersede 追記` 単独の fragment も有効)。

```markdown
---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-02
wave: dev-wave-parallel-docs-spool
seq: 3
---

## 新規

### {{F:partial-fold}}. fold の一部だけが反映された [恒真ゲート] [手順漏れ]

- 事象: canonical の一部だけが after hash になった。
- 根本原因: 複数ファイル更新に resume journal が無かった。
- 恒久対応: {{D:parallel-doc-spool}} の transaction state と before/after hash 照合。
- 再発検知: crash resume の positive control テスト。

## 再発

### F58

- **再発: 2026-08-02** — 別内容への ID 再利用を fold 前検査で拒否した。

## supersede 追記

- F196 **supersede: 2026-08-10** — 恒久対応末尾の「改訂は scope 外」は F197 で実施済み。
```

## 規則

- **新規**は `### {{F:slug}}. <題> [型タグ]` で宣言する。F 番号は fold が付ける。
  型タグは `docs/failures.md` の運用規則にある語から選ぶ。
- **恒久対応は実体へのポインタ必須**。宣言だけの対応 (恒真) は対応と認めない
  — 規律番号 / memory / hook / lint / スクリプトの fails-closed 検査のいずれかを指す。
- **再発**は既存の `### Fnn` を見出しに書き、`- **再発: 日付** — ...` を追記する。
  **新しい F 番号を採らない。** 同じ型の再発を新規エントリにしてはならない
  (再発を顕在化させるのがこの台帳の目的)。
- **supersede 追記**は、既存エントリの**記述が後続の事実で古くなった**ときに使う
  (同型の新たな発生ではない — その区別は `docs/failures.md` の運用規則が正本)。
  - item は `- F<n> **supersede: YYYY-MM-DD** — <本文>` の **1 物理行**だけ。
    H3・`base:`・継続行は付けない。空節は拒否される。
  - **target は literal の `F<n>` だけ**で、`{{F:slug}}` は使えない
    (同じ fold で採番した新規 F を supersede しても意味がない)。本文中の placeholder は解決される。
  - 日付は実在する暦日、区切りは `** — ` (半角空白 + U+2014 + 半角空白)、
    本文は空白以外を 1 文字以上含む。行区切り・段落区切り文字 (`\r`, VT, FF, U+0085,
    U+2028, U+2029) は拒否される。**日付とラベルは書き手が書く。fold は補わない。**
  - fold は**対象 F エントリの最後の非空行の直後**へ、行頭の `- ` を自分で付けて 1 行挿入する。
    同じ F に `再発` と supersede があるときは **再発 → supersede** の順になる。
  - `再発` 節に `- **supersede: ...` で始まる行を置くことはできない (誤分類の防止)。
- 参照先の F が存在しない、または重複していれば fold は停止する。
  supersede の対象エントリに同一行が既にある場合、同じ fold 内で同一の
  (target, 本文) が重複する場合も停止する。
