# AGENTS.md — Izanagi Codex 作業入口

このファイルはリポジトリ全体に適用する Codex 用の入口である。名称が Claude 向けであっても、
`CLAUDE.md` が全 AI 作業者に共通する規律の正本である。可変状態や絶対規律をこのファイルへ
複製しない。

## 作業開始

1. 作業前に `CLAUDE.md` を全文読み、絶対規律・現在地の引き方・作業手順に従う。
2. `CLAUDE.md`「現在地」が指定する `docs/worklog.md` の末尾エントリと、現行 phase doc の
   必要箇所だけを読む。phase doc 自身の「読み方」を優先し、完了済みの長い経緯を常時ロード
   しない。
3. `docs/handoff/` を列挙し、README 以外の残ファイルがあれば読む。作業セッションでは自分専用の
   handoff を作り、節目ごとに更新し、正常終了時に worklog へ吸収して削除する。
4. `docs/roadmap.md` は現行タスクが参照する節だけを読む。`docs/decisions.md` と
   `docs/glossary.md` は検索して該当項目だけを読む。
5. `git status` を確認し、他セッションまたはユーザーの変更を上書きしない。

## 共通規律と Codex 固有の注意

- `CLAUDE.md` の絶対規律、信頼境界、文書運用、計測規律、push は人間が行うという境界をすべて守る。
- `.claude/settings.json` の PreToolUse hooks は Codex には自動適用されない。hook が発火したと
  主張せず、`hooks/README.md` が定める保護対象と編集面を手動でも守る。
- `.claude/agents/` は実験ロールのモデル・ツール・情報遮断を含む契約である。Codex のサブエージェントは
  同じツール権限を持つため、機械的に同等な隔離を作れないロールを安易に置き換えない。置換が必要なら
  `docs/agent-architecture.md` と対象ロールを読み、弱くなる境界を明示して独立検証を追加する。
- ドキュメントは日本語、orchestrator・hooks・verifier は Python、CCBench と variant は C++ を基本とする。
- タスク完了時は関連テストと `python3 tools/check_docs.py` を実行し、phase の完了チェックは実装と
  同じ commit に含める。commit を作った後は `python3 tools/check_ai_provenance.py` で導入時点から
  `HEAD` までを監査する。

## commit provenance

commit を作るときは `docs/ai-provenance.md` を正本として、AI 製品・モデル・推論深度・役割を
反復可能な `AI-Agent:` trailer に必ず記録する。値が不明な場合は正本が定める
`not-exposed` / `unknown` を区別し、推測しない。複数の AI 構成が実質的に寄与した場合は
構成ごとに trailer を分ける。
`Co-Authored-By` やセッション URL はこの記録の代用にならない。
