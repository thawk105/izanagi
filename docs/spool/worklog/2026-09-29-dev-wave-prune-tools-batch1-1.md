---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-29
wave: dev-wave-prune-tools-batch1
seq: 1
title: 不要ツールの整理 第 1 束 — 候補 6 束を D1989・D2179 で現物照合し、条件を満たした実施済みの履歴除去 script 1 本だけを削除した。残る 5 束は有効な裁定・凍結事前登録の sha256・docs の再実行手順・live code を検査する test のいずれかに拘束されていた (tool 削除 + runbook 1 行 + insight、branch dev-wave-prune-tools-batch1)
---

## 本文

- 依頼: 並行 wave 共通指示 speedup-2026-09-29 の md_3 (ユーザー依頼「不要なテスト、ツール、ファイルは削除して記録しておき、後でgit参照しやすいように」)。一次資料は `output/insights/2026-09-29/prune-tools-batch1/README.md`。
- 削除は `tools/strip_claude_session_trailers.sh` だけ (2026-07-17 に実行済みの一回限り、専用 test 無し、名前参照は runbook の login `unknown` 経路表 1 行のみ)。runbook の行は「削除済み、`git log --grep='^prune'` で引ける」注記へ置き換えた。test・docs の削除は 0 件なので、墓標・地図・nodeid 台帳は変更なし。
- 残した 5 束: 外部署名の部品 2 本 (D1399 が実装を名指し、D1829 は実効層の保留で撤去指定ではない)、予算承認 preflight (専用 test が live の `s8b_holdout_freeze._load_budget_approval` を直接検査)、環境契約 activation 発行器 (test の大半が live の env_contract 系を検査)、環境偶然一致の走査器 (F641 台帳が「再走査は走査器を当て直す」と要求)、A-1 balanced sizing 2 本 (凍結事前登録が現行 sha256 を名指し)。md の候補一覧は名前参照の件数による機械集計で、test の中身・凍結 hash・docs の手順文は見ていなかった。
- 段構成: 軽量版。段 2 (Codex plan) が予算承認と走査器の 2 件で親の provisional 裁定 (削除) を覆し、親が test 本文と台帳本文で確認した。変更面が「test を持たない script 1 本」に確定した時点で DW-C00 を再評価し段 3 を省いた。変異は kill 型 0 件 (削除 script を読む test・gate が無く単一理由の層を置けない) と記録し、診断 probe 1 本 (runbook 行を残したまま削除した木の `check_docs.py`) を走らせた → rc=0 で生存 (期待どおり。docs に残った削除済み tool path を拾う lint は無い)。
- 実装子 (Codex author) は 2 回投入。1 回目は親 prompt の期待参照集合が狭すぎ (archive worklog 2 行・過去 insight 3 行の歴史的言及を含めていなかった)、子が指示どおり削除せずに停止した。2 回目は削除したが出力に `## 総括` 見出しが無く launcher が不受理とし、待ち手が残差 commit を記録した。不受理のため段 6 で read-only の監査子 1 本に差分全体を点検させた。
- セッション異常: `EnterWorktree` が name 形 (git config 読取) と path 形 2 回 (worktree list の 10 秒 timeout) で失敗し、手動 `git worktree add` (wave 木 10 分超、子木も同程度) の後は絶対 path で作業した。submodule 初期化 tool が `update-no-fetch` と git timeout で 2 回赤になり、同じ git 命令の直接実行 (21 秒) で 3 段とも初期化してから tool の再検査が rc=0 になった (DW-O08 の「1 度再実行」を超えた逸脱、木の中身は SHA で確認)。
- 工数: Codex gpt-6-sol / medium 2 本 (段 2 plan 1・段 5 author 1)。

## 次の一手差分
