# docs/archive/ — 凍結アーカイブ

**凍結 = 追記しない (訂正注記のみ可)** の記録族の置き場 (2026-07-05 新設)。現役の文書と
パスで区別し、「古い記録を現役と誤認して読む」事故を防ぐ。

## 規約

- **ファイル名は移動前と不変で入れる。** 凍結文書 (decisions・worklog 過去エントリ・insights 等) 内の
  旧パス参照は改竄禁止ゆえ直せないが、ファイル名が不変なら `grep -r <ファイル名>` で必ず辿れる
  (docs 間参照は節名 + ファイル名が正であり、パスは補助 — check_docs.py の行番号参照禁止と同系の発想)
- 入るもの: 監査記録 (`audit-*`)、worklog のローテーションアーカイブ (`worklog-<範囲>.md`)、
  その他「書いた時点で凍結」の記録
- 入らないもの: 現役文書 (roadmap / 現行 phase doc / glossary 等)、可変状態の正本 (worklog.md 現行)、
  roadmap の版凍結 (専用の `docs/roadmap-history/` が既にある)、セッション引き継ぎ (`docs/handoff/`)
- **git-history-only 化 (2026-07-15 新設):** 正本性がなく現役参照も要らない収容物は、working tree から
  削除して git 履歴にだけ残せる。削除時は本 README の収容物リストの当該行を**墓標行**に置き換える —
  様式 = `` `<ファイル名>` — (git-history-only、削除 <日付>) <一行の内容説明と削除理由>。正本/経緯 =
  <ポインタ>。復元 = `git log --follow -- docs/archive/<ファイル名>` ``。凍結文書内の旧参照は
  ファイル名 grep で本 README の墓標行に到達できる (到達性 lint = check_docs.py が墓標様式を認識する)

## 現在の収容物

- `audit-2026-06-30.md` — リポジトリ全体監査の台帳 (残項目の正本は現行 phase doc の must 表)
- `audit-2026-07-04-docs-consistency.json` — docs 横断監査 (real 39/refuted 4) の一次資料
- `audit-2026-07-12-docs-maintenance.json` — docs 保守監査 (2026-07-12) の一次資料 (07-15 の読書量
  診断が参照)
- `worklog-phase1-2.md` — worklog の Phase 1〜2 分 (2026-06-17〜06-30) ローテーションアーカイブ
- `phase3-kickoff-stages1-5.md` — phase3.md の完了済み記録 (kickoff タスク詳細 + 後続段 1〜5) の
  分離アーカイブ (2026-07-10)。チェックリスト正本・must 表・残存リスクは現行 phase3.md のまま
- `token-management-strategy.md` — (git-history-only、削除 2026-07-15) AI 生成の token 管理解説
  (2026-07-07 Haiku 生成)。2026-07-11 監査で定量記述の捏造を確認し注記付き凍結、正本性がないため
  working tree から削除。経緯 = failures.md F8・worklog 2026-07-11。復元 =
  `git log --follow -- docs/archive/token-management-strategy.md`
- `phase3-s4-design-foundation.md` — (git-history-only、削除 2026-07-15) 後続段 4 の設計基盤
  (2026-07-06 焦点調査の写像)。段 4 完了で D39 + phase3.md に畳む約束どおり 2026-07-12 に凍結移動
  済みで、設計判断の正本は D39 (decisions.md)。文書自体の正本性がないため working tree から削除。
  復元 = `git log --follow -- docs/archive/phase3-s4-design-foundation.md`
- `worklog-phase3-0702-0713.md` — worklog の Phase 3 前半分 (2026-07-02〜07-13) ローテーション
  アーカイブ (2026-07-15、肥大 224KB 対応。境界 = 07-14 (1)「全体方針の根本評価」以降を現行に
  保持 — 07-14 の戦略再定義セッション群の起点)
- `phase3-s6-s8a-completed-details.md` — phase3.md の完了済み記録第 2 弾 (段 6 (h)〜(j)・段 8a・
  must 表解消済み 3 行の詳細) の分離アーカイブ (2026-07-15)。チェックリスト正本・must 表・現役の裁定
  サマリは現行 phase3.md のまま
- `worklog-phase3-0714-0716.md` — worklog の Phase 3 中盤分 (2026-07-14〜07-16) ローテーション
- `worklog-phase3-0717-0718.md` — worklog の Phase 3 中盤分 (2026-07-17〜07-18) ローテーション
  アーカイブ (2026-07-17、肥大 97KB — 閾値 100KB 目前の先回り対応。境界 = 07-17 (1)「wave 2 前半」
  以降を現行に保持 — floor protocol 凍結案のユーザー裁定待ちという現行未決の起点)
