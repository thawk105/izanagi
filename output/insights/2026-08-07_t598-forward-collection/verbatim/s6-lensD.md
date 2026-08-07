# 段 6 敵対レビュー — レンズ D

read-only の静的レビューのみ実施した。pytest、`tools/check_docs.py` は実行しておらず、緑・赤は判定しない。

## 1. 実装子の権限境界 — refuted

実装子の報告は docs・commit・index 非接触を明記している（[s5-impl-out.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s5-impl-out.md:1)）。実装 prompt も docs 編集と commit/add を明示的に禁止していた（[prompt-s5-impl.txt](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/prompt-s5-impl.txt:4)）。

実測した状態：

- staged 差分なし
- docs 2 件は unstaged
- 実装面 2 件が unstaged、新規コード・テスト各 1 件が untracked
- 直近 commit は `bb824d8b`、`5d0d76ab`、`6ff44afe` で、本 wave の実装 commit はない

docs 差分は段 4 が親へ指示した内容に対応する（[s4-ruling.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s4-ruling.md:51)）。利用可能な証拠上、実装子による docs 編集・commit は認められない。

成果物影響: なし。

## 2. dev-wave byte 予算 — refuted

`wc -c` の静的実測：

| file | 実測 | 個別 cap |
|---|---:|---:|
| `core.md` | 8,646 | 9,600 |
| `workers.md` | 4,575 | 5,000 |
| `mutation.md` | 3,674 | 3,750 |
| `operations.md` | 8,301 | 8,400 |
| 合計 | 25,196 | 25,200 |

個別 cap は [check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:176)、合計 ceiling は同ファイルの[254 行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:254)にある。cap 総和は 26,750 bytes、1.10 倍上限は 27,720 bytes で、構成検査も範囲内。実装は [3361 行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:3361)と[3557 行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:3557)。

成果物影響: なし。

## 3. `docs/README.md` への規範 detail 逃がし — real

段 4 は、手順本体を `docs/README.md` へ移さず、README は inventory 更新だけに限定していた（[s4-ruling.md](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s4-ruling.md:53)、[同 62–66 相当](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/s4-ruling.md:62)）。

しかし実差分は inventory を越えて、次の規範 detail を README に置いている。

- 非 gate 契約
- operand・受理条件の正本指定
- 未分類時の login-node 停止と `blocked` 記録

根拠は [docs/README.md:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/README.md:69)。これは D110 却下案 (b) の「予算外 reference への規範 detail 逃がし」に該当する。`check_docs.py` の `docs/dev-wave/**` 閉包検査は README 本文へのこの逃がしを検出しない。

成果物影響: 規約違反が land する。

## 4. Pegasus site fail-closed — real

通常の `PEGASUS_LOGIN` は collector 呼出前に `blocked` になる（[collect_wave_usage.py:187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:187)）。明示的な site override 用環境変数・CLI 引数も新 tool にはない。

ただし分岐が `is_pegasus_login(site)` のみなので、`PEGASUS_SUSPECT` は `else` に入り collector を実行する（[collect_wave_usage.py:198](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:198)）。既存 site policy は重い処理の拒否対象を login と suspect の両方としている（[site_policy.py:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/campaign/site_policy.py:83)）。

これは、実測のない実行体を `unknown` に倒して止める §7.0 の契約（[pegasus-runbook.md:491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/pegasus-runbook.md:491)）に対する fail-open。テストも exact `PEGASUS_LOGIN` だけで、suspect を扱っていない（[test_collect_wave_usage.py:238](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:238)）。

最小修正は `site_policy.refuses_heavy_work(site)` を使い、`PEGASUS_SUSPECT` の collector 非呼出テストを追加すること。

成果物影響: 規約違反が land する。

## 5. U-2 — 限定付き

追加・変更行に実在の project slug、実時間窓、機体固有絶対 path、保存先識別子は見つからなかった。fixture は `synthetic-wave`、`synthetic-project`、`/synthetic/izanagi`（[test_collect_wave_usage.py:34](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:34)）、時刻も synthetic fixture（[同 359 行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:359)）。

予定 commit message file はまだ存在しないため、最終文面だけは commit 前に再走査が必要。新 privacy lint は段 4 の明示的 scope 外であり、追加してはならない。

成果物影響: 現差分にはなし。

## 6. scope 逸脱・既存受理集合 — refuted

task-run 台帳 v2、定期実行、A/B、admission registry、privacy lint の導入はない。helper は collector を import 呼出し、`--strict` を渡していない（[collect_wave_usage.py:94](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:94)）。テストもその不在を pin する（[test_collect_wave_usage.py:123](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:123)）。

collector の既存 `--cwd-contains`、`--strict` は維持され、承認された `--cwd-under` だけが追加されている（[claude_session_ledger.py:116](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/claude_session_ledger.py:116)）。

成果物影響: なし。

## 7. meta-test・dispatch・DW-S09 pin — refuted

新 test file は自走 harness を持つ（[test_collect_wave_usage.py:408](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:408)）。README allowlist への逃がしはない。既存 meta-test は `pytest.main` を harness signal として認識する（[test_plain_runner_coverage.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_plain_runner_coverage.py:25)）。

dispatch 集合一致検査は保存されている（[check_docs.py:2248](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:2248)）。runbook の `{tests, provenance}`（[pegasus-runbook.md:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/pegasus-runbook.md:527)）と source の `TASKS`（[dispatch_compute.py:54](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/pegasus/dispatch_compute.py:54)）は静的に一致する。

`DW-S09` の acceptance-order literal と唯一 land 経路もそのまま残る（[core.md:109](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/dev-wave/core.md:109)）。逐語検査本体は [check_docs.py:3802](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/check_docs.py:3802)。

成果物影響: なし。検査は未実走なので実行結果の主張はしない。

## 8. provenance — 限定付き

まだ commit がないため、現時点で trailer 違反は成立していない。ただし tools・テストを含む統合 commit には Codex `role=author` が必須（[ai-provenance.md:44](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/ai-provenance.md:44)）。

実装子は `gpt-5.6-sol`、`reasoning=high` で起動されている（[launch-s5.sh:14](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t598-forward-collection/launch-s5.sh:14)）。親が最低限含めるべき物理 1 行は：

```text
AI-Agent: product=codex; model=gpt-5.6-sol; reasoning=high; role=author
```

親自身が統合・docs 執筆へ実質関与した構成も、実表示値を使って別行の `manager` / `integrator` / docs `author` として記録する。値は推測しない（[ai-provenance.md:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/ai-provenance.md:20)）。

成果物影響: trailer を欠けば規約違反が land する。

## 9. D206 / D205 — refuted

helper は既存 collector の `collect_report` を直接 import し（[collect_wave_usage.py:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:22)）、1 回呼ぶ（[同 109 行目](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/tools/collect_wave_usage.py:109)）。subprocess や第 2 JSON parser による実質 fork ではない。AST ベースの防壁もある（[test_collect_wave_usage.py:157](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/orchestrator/tests/test_collect_wave_usage.py:157)）。

規模は：

- production: helper 229 行、collector `+69/-14`
- tests: 新規 409 行、既存 test `+39`

D205 が禁じる production 級 hardening（[decisions.md:9840](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/decisions.md:9840)）に対し、production 追加は 298 行で、task-run v2 の却下見積り 645–816 行（[decisions.md:10371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t598-forward-collection/docs/decisions.md:10371)）より小さい。要求外の多層機構もない。行数だけを理由に追加 hardening を要求しない。

成果物影響: なし。

## 総括

(a) **NO-GO**

(b) must-fix：

1. `docs/README.md` を inventory のみに戻し、非 gate・受理条件・login-node 停止という規範 detail を除く。
2. `PEGASUS_SUSPECT` でも collector を呼ばず `blocked` にし、その静的テストを追加する。
3. 統合 commit 前に Codex `role=author` trailer を必ず入れる。

(c) 見送り可：

- privacy lint、task-run v2、定期実行、A/B、admission registry 追加。
- D205 に反する追加の一般 hardening。
- U-2 は現差分では問題なし。最終 commit message の実値走査だけ親の commit 前手番として残す。