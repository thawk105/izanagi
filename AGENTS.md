# AGENTS.md — Izanagi Codex 作業入口

このファイルはリポジトリ全体に適用する Codex 用の入口である。名称が Claude 向けであっても、
`CLAUDE.md` が全 AI 作業者に共通する規律の正本である。可変状態や絶対規律をこのファイルへ
複製しない。

## 作業開始

まず `CLAUDE.md` を全文読み、「現在地」の作業種別ゲート (task-class gate) で依頼を分類し、クラスに
応じた導線に従う。クラス 1 では、ゲート定義と回答に必要なファイルだけを読み、起動確認・handoff・
worklog 追記・完了検査を省く。クラス 2 / 3 では `CLAUDE.md`「現在地」の起動順をそのまま実行する
(worklog・phase doc・handoff・roadmap / decisions の引き方と `git status` 確認を含む)。phase doc は
その冒頭の「読み方」に従い、完了済みの長い経緯を常時ロードしない。

## 共通規律と Codex 固有の注意

- `CLAUDE.md` の絶対規律、信頼境界、文書運用、計測規律、push は人間が行うという境界をすべて守る。
- `.claude/settings.json` の PreToolUse hooks は Codex には自動適用されない。hook が発火したと
  主張せず、`hooks/README.md` が定める保護対象と編集面を手動でも守る。Codex への配線を保留した
  理由と再開条件は D54〜D56。
- Codex role adapter の現行状態と再開条件は `.codex/agents/README.md` と
  `tools/check_codex_agents.py` が正本。両正本が安全な実行面として再分類するまでは native profile として
  起動せず、`task_name` を role 名にした通常の Codex 子も role 隔離の代替にしない。通常の Codex 子は
  `CLAUDE.md`「現在地」のゲートに従い、クラス 1 相当の小さい作業では起動しない。`.claude/agents/` は
  role 本文と Claude 固有の権限契約であり、Codex 子を同等な隔離とは扱わない。
- クラス 2 / 3 のタスク完了時は関連テスト、`python3 tools/check_codex_agents.py`、
  `python3 tools/check_docs.py` を実行し、phase の完了チェックは実装と同じ commit に含める。
  commit を作った後は `python3 tools/check_ai_provenance.py` で導入時点から `HEAD` までを監査する。
  Pegasus ログインノードでは同 checker が計算ノードへ自動 dispatch するので、この行を打つこと自体は
  禁止されない (`rc=16` は dispatch の失敗であって監査結果ではない)。
- **`hostname` が Pegasus ログインノード (`pegasus0N`) のときは、重い処理を自分で走らせない。**
  テスト (pytest の全走・部分走)・ビルド (`cmake --build` / `make -j` / `ninja`)・ベンチ・計測・
  provenance 履歴監査は計算ノードで行う規律であり (`docs/pegasus-runbook.md` §7)、**Codex には
  hook が未配線なので機械的に止まらない**。許されるのは静的読み取りと `python3 -m py_compile` まで
  (`check_ai_provenance.py` の履歴監査は git subprocess 約 3000 本であり静的読み取りではない) で、
  **pytest はログインノードで一切走らせない (単一ファイル・単一 nodeid も含む)**。
  テスト実測は親が `tools/run_tests.py` 経由で計算ノードへ dispatch する。
  走らせていないものを緑と報告しない。
  **上の列挙は閉じた一覧ではない — 判定は場所でなく量で行う。** 同時に生きる全子孫を含む cgroup
  charged memory のピークが規範値以上、または未計測・入力依存で分からないなら、
  ログインノードで走らせない。基準と分類は `tools/README.md` と `docs/pegasus-runbook.md` §7.0。
