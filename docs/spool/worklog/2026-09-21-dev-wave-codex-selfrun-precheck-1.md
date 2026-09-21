---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-21
wave: dev-wave-codex-selfrun-precheck
seq: 1
title: Codex 実装子の login self-run precheck — 自走 harness は hook に拒否されず子が rc=0 で実走できるが、大半は admission 外の in-process pytest なので「prompt に self-run を足す」は名指しの 1 file・1 回に限る条件付き許可の裁定パッケージで返す (insight のみ、実装・docs 変更なし、branch worktree-dev-wave-codex-selfrun-precheck)
---

## 本文

- ユーザー直接起動の precheck (依頼逐語は insight `verbatim/origin.md`)。T-2792 / T-2796 の「実装済み・未実走 → 親が焦点走を dispatch → fix 巡」の往復を減らせるか、新 test file の自走 harness (`PYTHONPATH=. python3 orchestrator/tests/<test>.py`) を Codex author / fix 子が login sandbox で実行できるか (hook 拒否対象か・rc・所要) を実装差分ゼロの probe で実測した。一次資料は `output/insights/2026-09-21/codex-selfrun-precheck/README.md` (静的 hook 判定 10 綴り、live gate、親の対照走 4 本、probe 子の報告、段 3 相談・段 4 裁定・段 6 レビューの逐語)。数値はここに再掲しない。
- 起点 local main `5efd69367` (fresh worktree、07:44 JST 開始 gate rc 0)。段構成: 軽量版 + 診断 wave の型 (段 1 → 段 3 相談 1 本 → 段 4 → 段 5 probe (Codex author 1 本、unit worktree、編集ゼロ) + 親の `check_codex_hooks.py` live gate → README → 段 6 read-only review 1 本 (must-fix 4) + 焦点再レビュー 2 巡 (2 巡目 GO) → 7 → 8 → 9)。段 2 は省いた。実装・docs の変更なし。
- 依頼文の「D289 / rc=16」は D103 (login 重量処理の三層強制) と `run_tests.py` の dispatch rc で読んだ (D289 は並行投入の裁定)。guard の pytest 拒否・admission はいずれも動かしていない。
- **段 3 (read-only、所見 11 / 高 5、NO-GO) を全件 real 採用して probe を縮小した:** 「hook が拒否しない」と「login で走らせてよい」は別 (全 test file 369 本中 232 本の自走 harness は `pytest.main([__file__])` 委譲の in-process pytest で admission を通らない)、「1 file・数秒」は一般化不可、子に `run_tests.py` / `-m pytest` を試させるコマンドは削除 (前者は local scope / dispatch へ進みうる、後者は不発火時に実走)、「契約上保証」「往復 1 巡削減」は言い過ぎ、fix 子 probe は不要 (author と argv 同一)。
- **裁定パッケージ (ユーザー裁定待ち、insight §4):** 案 A (親が名指しした新設・変更 test file だけを自走 harness で 1 回、資源除外文つき、計測でも受入でもない) と案 B (足さない = 現状) の択一。親の推奨は裁定までは B を既定、A は「名指しの 1 file・1 回・子の自己検証に限り、admission 外の in-process pytest を含む自走 harness を子に許す」狭い条件付き許可をユーザーが明示裁定した場合だけ適用する候補 (`DW-M08` の一般境界は定義しない。D2195 は親の変異観測のコマンド形の先例で、子への許可根拠にならない)。案 C (`python3 -c "…pytest.main…"`、T-2810 / T-2814 の author prompt が実際に使った形) は不採用推奨 — A / B どちらでもこの形の指示は止める。案 D (`run_tests.py` の sandbox 対応) は scope 外で記録のみ。
- 落とし穴: 段 3 で指摘されるまで、親は「自走 harness = 契約された形だから許される」と書いていた。`test_plain_runner_coverage.py` は `__main__` 以後の文字列 signal を見る構造検査で、実行成功・login 許可を保証しない。
- 受入全走は 1 回目で child-green (26,739 passed / 69 skipped、赤 0・flake 0、tested main `21641fee7` / tested tip `8f6ecb264`)。門番は他 wave の受入 leader 2〜4 本で 24 分待った。取り込んだ main 4 commit には別 wave の `DW-M08` 改訂 (親の変異 self-run 手順の詰め書き) が含まれるが、本 wave の結論は変わらない。
- 工数: codex 5 本 (consult 1、author 1、review 1、焦点再レビュー 2、gpt-6-astra / medium、probe 子は 10 call / 128.9 秒)、live gate 1 回 (47 秒)、親の login 対照走 4 本 (合計 7 秒)。計算ノード job は受入全走のみ。

## 次の一手差分

### 新規

- {{T:codex-selfrun-prompt-ruling}} **P2・新規 (ユーザー裁定待ち)**: Codex author / fix prompt に「親が名指しした新設・変更 test file だけを自走 harness で 1 回走らせて報告する」(案 A、名指しの 1 file・1 回・子の自己検証に限る狭い条件付き許可で、admission 外の in-process pytest を含む) を足すか、現状 (案 B) を維持するかの択一。`output/insights/2026-09-21/codex-selfrun-precheck/README.md` §4。どちらでも `python3 -c "…pytest.main…"` の prompt 指示 (案 C) は止める。採用時の `DW-S05-C` 収容は予算の裁定が別に要る。
