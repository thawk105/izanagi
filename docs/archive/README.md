# docs/archive/ — 凍結アーカイブ

**凍結 = 追記しない (訂正注記のみ可)** の記録族の置き場 (2026-07-05 新設)。現役の living 文書と
パスで区別し、「古い記録を現役と誤認して読む」事故を防ぐ。

## 規約

- **ファイル名は移動前と不変で入れる。** 凍結文書 (decisions・worklog 過去エントリ・insights 等) 内の
  旧パス参照は改竄禁止ゆえ直せないが、ファイル名が不変なら `grep -r <ファイル名>` で必ず辿れる
  (docs 間参照は節名 + ファイル名が正であり、パスは補助 — check_docs.py の行番号参照禁止と同系の発想)
- 入るもの: 監査記録 (`audit-*`)、worklog のローテーションアーカイブ (`worklog-<範囲>.md`)、
  その他「書いた時点で凍結」の記録
- 入らないもの: living 文書 (roadmap / 現行 phase doc / glossary 等)、可変状態の正本 (worklog.md 現行)、
  roadmap の版凍結 (専用の `docs/roadmap-history/` が既にある)、セッション引き継ぎ (`docs/handoff/`)

## 現在の収容物

- `audit-2026-06-30.md` — リポジトリ全体監査の台帳 (残項目の正本は現行 phase doc の must 表)
- `audit-2026-07-04-docs-consistency.json` — docs 横断監査 (real 39/refuted 4) の一次資料
- `worklog-phase1-2.md` — worklog の Phase 1〜2 分 (2026-06-17〜06-30) ローテーションアーカイブ
