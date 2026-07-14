# docs/ — 文書の地図

リポジトリの文書がどこにあるかの地図 (CLAUDE.md「主要ドキュメント」節から委譲、2026-07-11)。
毎セッション必読ではない — 文書の所在を引くときに読む。毎セッション使う正本 (worklog 末尾・
現行 phase doc) は CLAUDE.md「現在地」が指す。

## docs/

- `roadmap.md` — 設計の全体像と理由 (戦略)。全文必読は Phase 初回セッションと改訂時のみ、日常は節名で引く (冒頭「読み方」、D35)
- `decisions.md` — 設計判断と却下案 (D 番号)。`grep -n "^## D"` が目次 (引き方は CLAUDE.md「主要ドキュメント」節)
- `phase1.md` / `phase2.md` — タスク分解 (完了・凍結)
- `phase3.md` — 現行 phase doc。チェックリストと must 表 = タスク粒度の完了状況の正本
- `phase3-main-experiment.md` — 主実験の事前登録
- `worklog.md` — 日誌。末尾エントリ = 可変状態の正本 (書式は CLAUDE.md 作業の進め方 7)
- `ai-provenance.md` — commit ごとの AI 製品・モデル・推論深度・役割を記録する `AI-Agent` trailer 規約
- `failures.md` — 失敗台帳。起こした問題の型別索引と恒久対応の実体ポインタ (2026-07-13 新設。
  問題発生時は worklog と同時に追記、再発は既存エントリに「再発:」追記)
- `handoff/` — セッションの WAL (中断引き継ぎ + 並行セッションの宣言板。運用は同 README)
- `archive/` — 凍結記録 (監査台帳・worklog 過去分・凍結文書)。ファイル名は移動前と不変、規約は同 README
- `agent-architecture.md` — サブエージェント構成・権限・規律の正本 (ロール定義本体は `.claude/agents/`)
- `orchestrator-design.md` — orchestrator の ACID/WAL/排他、環境タグ
- `ccbench-anatomy.md` — CCBench 構造調査
- `axis-onboarding.md` — 変異軸オンボーディングの手順書
- `isolation-phenomena.md` — verifier が判定する serializability 異常 (G0/G1/G2) の分類
- `glossary.md` — 用語集 (用語を grep して該当項目だけ読む)
- `related-work/` — 関連研究 (README.md が本体 + shinka-deepdive.md 付録 + literature-map/ 文献マップ)
- `paper-story/` — 論文ストーリーの横断合成 (日付付き凍結スナップショットを束ねる、詳細は同 README)
- `roadmap-history/` — roadmap の版凍結置き場 (改訂セレモニーの正本 = 同 README)
- `phase3-s*.md` — 現行 phase doc の従属文書 (段の設計書・手順書)。段ごとの内訳は phase3.md から辿る (段番号をここに列挙しない — 段の追加で腐るため)

## docs/ の外

- `AGENTS.md` — Codex 用の薄い作業入口。共有規律の正本 `CLAUDE.md` と現行正本へのポインタ
- `output/` — 成果物 (campaigns/<id>/ と env/<tag>/ の二軸、D13 — 詳細 output/README.md)。insight は `output/insights/`
- `tools/` — 運用スクリプト (`check_docs.py` = 文書 lint / `check_ai_provenance.py` = commit trailer 監査 /
  `plotting/` = campaign の論文品質作図、規約は `tools/plotting/FIGURE_CONVENTIONS.md`)
- `hooks/` — 方針 A の最小第二防壁 (guard_write / guard_bash、詳細は同 README)
- `.claude/agents/` — サブエージェントのロール定義 (現有一覧は ls が正本)
