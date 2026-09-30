---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-30
wave: dev-wave-prune-orchestrator-batch2
seq: 1
title: 不要コードの整理 第 2 束 — 使われていない提出 gate と一回限りの分析の候補 9 群 (19 file) を D1989・D2179 で現物照合し、削除 0 と判定した (insight のみ、branch worktree-dev-wave-prune-orchestrator-batch2)
---

## 本文

- 依頼: 並行 wave 共通指示 speedup-2026-09-29 の md_4 (ユーザー依頼「不要なテスト、ツール、ファイルは削除して記録しておき、後でgit参照しやすいように」)。md_3 (prune-tools-batch1) の land 後に着手。候補別の判定と根拠は一次資料 `output/insights/2026-09-30/prune-orchestrator-batch2/README.md` §2。
- 結果: 削除 0。台帳・allowlist・spawn 表・地図・墓標・所要台帳は変更なし。依頼の「submission_gate 系 test 約 790 秒」は所要台帳で 222 node・788.8 worker 秒と一致したが縮まない。md の候補一覧 (「tests 以外から import 0」の機械集計) は 2026-09-20 の T-2800 の判定、事前登録の契約、live test の照合先、runbook 手順を反映していなかった。
- 棄却・訂正: 段 1 brief の件数「12 module」は段 2 の指摘で 9 群・19 file に訂正。記録レビュー (NO-GO) の must-fix 2 件を commit 前に直した — nonmonotonicity は D1989 上は歴史的言及しか持たず D2179 条件 1 の不成立で残す、sweep_report の根拠は `docs/orchestrator-design.md` §材料レポート (本 module を名指ししない) ではなく共有 test の import と `docs/phase2.md:184`。
- 段構成: 軽量版。段 2 Codex (read-only、「残しすぎ」「消しすぎ」の両方向) が親の見立て (削除 0) を支持。段 4 で「実装しない」と裁定し 4→7→8→9。段 3 は実装面ゼロ・受理集合不変で DW-C00 の必須条件が不成立のため省略。事実を再抽出した docs-only なので記録に独立 read-only レビュー 1 本。変異 matrix は実装差分ゼロで免除。受入は D2316 の縮小受入を予定したが、`tools/scoped_acceptance.py plan` (tested main 4f412c67b、記録 commit 7f51d0e91) が不適格と判定したので受入全走にした。不適格の理由は 8 件とも `production-reference:<insight の verbatim/ 配下の file>:orchestrator/campaign/condition_meaning_gate.py` で、同 file `:22` の docstring の英単語 "verbatim" が dir 名の鍵 `verbatim` と部分一致したもの。D2316 決定 3 の鍵は汎用名 README.md・index.md だけを除くので、`verbatim/` を持つ insight (tracked で 1,112 file) を書く wave は、production code にこの語がある限り縮小受入に入れない。安全側の過大除外で正しさの問題ではないが、縮小受入の効果が大きく減る。
- 受入 attempt 1 の赤の判定 (DW-O18): 記録 commit fb571fe95 に local main 51765ae6c を post-claim merge した木 49e071812 で 28,403 passed / 74 skipped / 赤 1 件 —
  `orchestrator/tests/test_codex_worker_launch.py::test_t2620_orphan_zombie_is_rejected` (`residual_observation` が期待 `final_count: 1` に対し `final_count: None`・`final_unknown_source: proc_stat_read_error`、`process_group_residual` が期待 1 に対し None。launcher の /proc 走査が一時的な読み取り失敗に当たった)。
  **非帰属**: 本 wave の変更は insight と spool fragment だけで、test も対象 `tools/codex_worker_launch.py` もこれらを読まない。同じ木で当該 node を計算ノードで単独再走して 1 passed (6.47 s) で非再現。受入を投げ直す。
- 受入 attempt 2 の赤の判定 (DW-O18): 474693d67 に local main fb02637e4 を post-claim merge した木 41475e5dd で 28,401 passed / 赤 3 件 —
  `orchestrator/tests/test_env_contract_activation.py` の `test_historical_calibration_is_verified_only_when_resolved_in_source_stage[missing]`・`[modified]` と
  `test_import_performs_no_open_or_stat_io_in_worktree_or_archive_source_stage`。3 件とも test 本体の `git archive --format=tar ... HEAD` が 30 秒で `TimeoutExpired`
  (既知の非帰属型、2026-09-14・09-21 に同 test で記録あり)。同じ木の単独再走 (計算ノード) でも 3 件とも同じ timeout で再現した。
  **非帰属**: 同じ worktree で main の木 fb02637e4 と wave の木 41475e5dd を login で交互に 2 回ずつ tar 化すると、どちらも 1.16 GB (差 82 KB) で
  main 8.6 s / 18.1 s、wave 5.8 s / 12.0 s と同程度。本 wave の追加 (insight・fragment) は archive の所要を変えず、30 秒上限を超えるのは計算ノード側の I/O 負荷による。
  同一 tip の受入は 1 回だけなので、この記録 commit (9dc43ce25) を新しい tip として当該 3 node を単独再走したが、再び 3 件とも同じ timeout (34.16 s)。
  余裕の実測: 通った回でもこの 2 test は 30 秒上限の直下で走っている — 直前の別 wave の受入 (shard session 6e27b0781、13:40 JST 前後) で
  `[modified]` 25.3 s・`test_import_performs_no_open…` 28.1 s、本 wave の attempt 1 (49e071812) で 26.5 s・24.6 s (各 junit.xml の time)。
  repo 全体の tar (1.16 GB) を 30 秒で作る前提の余裕が 2〜5 秒しか無く、計算ノードの I/O の揺れで落ちる。本 wave の差分とは独立。
  受入はこの追記 commit を tip として投げ直す。
- セッション異常: submodule 初期化 tool の 1 回目が `update-no-fetch` (既知の tool 内 30 秒上限型)、同じ引数の再走で rc=0。候補 hash の検索を needle ごとの `git grep` 76 回で始めて 1 回 30 秒前後かかり、`-e` を並べた 1 回走査へ切り替えた。記録レビューの待ち手を誤って 2 本張り、後の 1 本を止めた。
- 工数: Codex gpt-6-sol / medium 2 本 (段 2 plan 1・記録レビュー 1)。

## 次の一手差分

### 新規

- {{T:scoped-acceptance-verbatim-key}} **P2・新規**: 縮小受入 (D2316) の分類で、insight の `verbatim/` dir 名が production code の英単語 "verbatim" (`orchestrator/campaign/condition_meaning_gate.py:22` の docstring) と部分一致し、`verbatim/` を持つ insight を書く wave がすべて不適格になる (2026-09-30 prune-orchestrator-batch2 で実測、理由 8 件とも同型)。`verbatim` を README.md・index.md と同じ汎用名に加えるかを、D2316 決定 3 (受理集合の変更) として諮る。材料 = 本エントリと `output/insights/2026-09-30/prune-orchestrator-batch2/verbatim/scoped-plan.json` (`tools/scoped_acceptance.py plan` の出力)。
