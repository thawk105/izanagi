# failures fragment

`docs/failures.md` へ追記する失敗・near miss・規律違反。共通規則は `docs/spool/README.md` を正本とする。

本文の H2 は `## 新規` と `## 再発` のうち使うものだけを、この順で置く。

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
```

## 規則

- **新規**は `### {{F:slug}}. <題> [型タグ]` で宣言する。F 番号は fold が付ける。
  型タグは `docs/failures.md` の運用規則にある語から選ぶ。
- **恒久対応は実体へのポインタ必須**。宣言だけの対応 (恒真) は対応と認めない
  — 規律番号 / memory / hook / lint / スクリプトの fails-closed 検査のいずれかを指す。
- **再発**は既存の `### Fnn` を見出しに書き、`- **再発: 日付** — ...` を追記する。
  **新しい F 番号を採らない。** 同じ型の再発を新規エントリにしてはならない
  (再発を顕在化させるのがこの台帳の目的)。
- 参照先の F が存在しない、または重複していれば fold は停止する。
