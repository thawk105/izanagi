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
  主張せず、`hooks/README.md` が定める保護対象と編集面を手動でも守る。Codex への配線を保留した
  理由と再開条件は D54〜D56。
- Codex role adapter の現行状態と再開条件は `.codex/agents/README.md` と
  `tools/check_codex_agents.py` が正本。両正本が安全な実行面として再分類するまでは native profile として
  起動せず、`task_name` を role 名にした通常の Codex 子も role 隔離の代替にしない。通常の Codex 子は
  すべて上の作業開始 1〜5 の対象である。`.claude/agents/` は role 本文と Claude 固有の権限契約であり、
  Codex 子を同等な隔離とは扱わない。
- タスク完了時は関連テスト、`python3 tools/check_codex_agents.py`、`python3 tools/check_docs.py` を
  実行し、phase の完了チェックは実装と同じ commit に含める。commit を作った後は
  `python3 tools/check_ai_provenance.py` で導入時点から `HEAD` までを監査する。
