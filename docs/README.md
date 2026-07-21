# docs/ — 文書の地図

リポジトリの文書がどこにあるかの地図 (CLAUDE.md「主要ドキュメント」節から委譲、2026-07-11)。
毎セッション必読ではない — 文書の所在を引くときに読む。毎セッション使う正本 (worklog 末尾・
現行 phase doc) は CLAUDE.md「現在地」が指す。

## 大きい文書の引き方 (D35)

`decisions.md` は `grep -n "^## D"`、`glossary.md` は用語検索を索引にし、該当見出しから次の見出しまで
だけを読む。worklog 過去分、監査、insight、生ログも検索・tail・offset/limit で絞る。全文が必要な解析は
独立コンテキストまたは digest に委ね、メインコンテキストには構造化された結論だけを戻す。

## docs/

- `roadmap.md` — 設計の全体像と理由 (戦略)。全文必読は Phase 初回セッションと改訂時のみ、日常は節名で引く (冒頭「読み方」、D35)
- `decisions.md` — 設計判断と却下案 (D 番号)。`grep -n "^## D"` が目次 (引き方は直上の節)
- `phase1.md` / `phase2.md` — タスク分解 (完了・凍結)
- `phase3.md` — 現行 phase doc。チェックリストと must 表 = タスク粒度の完了状況の正本
- `phase3-main-experiment.md` — 主実験の事前登録
- `worklog.md` — 日誌。末尾エントリ = 可変状態の正本。書式とローテーションは同ファイル冒頭
- `ai-provenance.md` — commit ごとの AI 製品・モデル・推論深度・役割を記録する `AI-Agent` trailer 規約
- `failures.md` — 失敗台帳。起こした問題の型別索引と恒久対応の実体ポインタ (2026-07-13 新設。
  問題発生時は worklog と同時に追記、再発は既存エントリに「再発:」追記)
- `handoff/` — セッションの WAL (中断引き継ぎ + 並行セッションの宣言板。運用は同 README)
- `archive/` — 凍結記録 (監査台帳・worklog 過去分・凍結文書)。ファイル名は移動前と不変、規約は同 README
- `agent-architecture.md` — サブエージェント構成・製品別 adapter・権限・規律の正本
- `orchestrator-design.md` — orchestrator の ACID/WAL/排他、環境タグ
- `pegasus-runbook.md` — Pegasus の qlogin / PBS バッチ / module / 並列実行 / ストレージ運用手順
- `ccbench-anatomy.md` — CCBench 構造調査
- `axis-onboarding.md` — 変異軸オンボーディングの手順書
- `isolation-phenomena.md` — verifier が判定する serializability 異常 (G0/G1/G2) の分類
- `glossary.md` — 用語集 (用語を grep して該当項目だけ読む)
- `related-work/` — 関連研究 (README.md が本体 + shinka-deepdive.md 付録 + literature-map/ 文献マップ + notes/ 調査ノート)
- `paper-story/` — 論文ストーリーの横断合成 (日付付き凍結スナップショットを束ねる、詳細は同 README)
- `roadmap-history/` — roadmap の版凍結置き場 (改訂セレモニーの正本 = 同 README)
- `phase3-s*.md`・`phase3-8b-*.md` — 現行 phase doc の従属文書 (段の設計書・手順書)。段ごとの内訳は phase3.md から辿る (段番号をここに列挙しない — 段の追加で腐るため)
- `freeze-permanent-design.md` — freeze 族の恒久設計の正本 ([T-080]、R1..R16 承認済み 2026-07-22。次 = 第 2 設計段 §13)

## docs/ の外

- `AGENTS.md` — Codex 用の薄い作業入口。共有規律の正本 `CLAUDE.md` と現行正本へのポインタ
- `orchestrator/` — 探索・評価・campaign 駆動の Python 実装 (構成と安定核は `orchestrator/README.md` が正本)
- `patches/` — CCBench への意図的 patch (positive control・合成 variant・診断計器)。来歴は `patches/README.md` が正本
- `src/` — coder 向け仕様 (`coder-spec.md` §1-2 が現役、`coder-leakproof-context.md` = リーク遮断入力の正本)
- `output/` — 成果物 (campaigns/<id>/ と env/<tag>/ の二軸、D13 — 詳細 output/README.md)。insight は `output/insights/`。
  AI 開発作業の統計記録 (task-run 台帳、開発プロセス観測 — D66) は `output/task-runs/README.md` が詳細正本
- `tools/` — 運用スクリプト (`check_docs.py` = 文書 lint / `check_codex_agents.py` = Claude role と
  Codex adapter の本文・metadata・schema・policy parity、実行可否・発見可能性の fail-closed 検査 /
  `check_ai_provenance.py` = commit trailer 監査 / `plotting/` = campaign の論文品質作図、規約は
  `tools/plotting/FIGURE_CONVENTIONS.md`)
- `hooks/` — 正しさの最小第二防壁 (guard_write / guard_bash) + 別系統のコンテキスト衛生
  (guard_read)。詳細は同 README
- `.claude/agents/` — role 本文と Claude Code 固有の model/tools 契約 (現有一覧は ls が正本)
- `.codex/agents/` — Codex role adapter の現行状態・再開条件の正本 (D54〜D56、F16/F17)
- `.codex/role-adapters/` — 非自動発見の Codex adapter 定義 (稼働可否は `.codex/agents/README.md` が正本)
