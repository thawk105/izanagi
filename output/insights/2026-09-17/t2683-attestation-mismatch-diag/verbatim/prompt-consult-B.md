単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/parent-brief.md — 親 brief (scope・実アンカー表・provisional 裁定 P1〜P4・不変条件)。**親 brief 自身も検査対象。** 読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/plan-out.md — 段 2 plan (検査対象)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/ruling-items-14-15.md — ユーザー裁定 (第 20 回 /rulings 項 14・15) の逐語。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/t2683-archive-item.md — T-2683 の起票原文。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/D474.md — D474。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/D2056.md — D2056。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/t126_driver.py — 変更対象。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/tests/test_t126_qualification_driver.py — 既存 test。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/tools/pegasus/t126_qualification.sh — T126 の実走 wrapper (attempt dir の扱い、rc 表 L205-215、driver 起動 L830-840)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/artifacts.py — write capability / layout。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/campaign/execution_guard.py — `attest_and_build_receipt` L576-640 (P1 の対象)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/campaign/loop.py — L170-200 (execution_guard の呼び手の 1 つ)。読めなければ即停止。

## 依頼 — レンズ B: 整合と実効性

plan と親 brief を**守らず攻撃**せよ。あなたは read-only で pytest 実走は不要 (静的検査でよい)。テスト実測は親が行う。レンズ A (別の子) が正しさ境界と受理集合を見るので、あなたは**成果物が実際に効くか・親の前提が実測に耐えるか**を見る。

攻撃観点 (各観点で「所見 / real か refuted か / 根拠 file:line / 是正案」を書く):

1. **sidecar は読み手に届くか:** T126 の実走は `tools/pegasus/t126_qualification.sh` が driver を起動し attempt dir を扱う。失敗 attempt の attempt dir と sidecar は、job 終了後に誰が・どこで読めるか (退避・保全・rc 表との対応)。読み手が存在しない/到達しないなら、この修正は「書いただけ」になる — その場合の最小の追加 (scope 内) と裁定パッケージ候補を分けて示せ。
2. **親 brief P1 の実測の一般化:** 親は execution_guard の呼び手 4 本 (`loop.py:187`、`s8b_oracle_driver.py:968/1147`、`screening_driver.py:336`、`s8b_floor_campaign.py:7379`) が `str(exc)` を伝播すると述べた。各呼び手の実コードで、message が最終的に**どこに記録されるか** (WAL・stderr・台帳・捨てられる) を辿り、「捨てられる」経路が 1 つでもあれば P1 は一般化しすぎである。real なら是正案を「本 wave の局所修正」と「裁定パッケージ候補」に分けて示せ。
3. **抽出 helper の実効性:** plan の module-level helper は fork 経路の実挙動 (`os._exit`、capability の継承、`create_json` の fsync) を代表するか。helper 直呼び test が緑でも fork 経路が壊れている形 (例: 例外型が `except BaseException` に飲まれて sidecar が書かれない) を具体的に構成できるか。
4. **親側 message の変更 (P3 相当):** `AttestationError` の message に sidecar 相対 path と failed field 名を含める案は、`fsm.reject` の evidence (canonical JSON) に入る。台帳 replay・`verify()`・既存 test (`test_attestation_failure_is_terminal_reject_with_exact_rc`) に影響しないか。message が長くなること (21 field 全部 fail の場合) の実害はあるか。
5. **所有範囲・並行 wave:** 変更 file は `orchestrator/qualification/t126_driver.py` と `orchestrator/tests/test_t126_qualification_driver.py` の 2 つ。同 file を参照する他 test (`test_t126_pegasus_tools.py`、`test_campaign.py:5526`、`test_official_perf_closure.py`、`test_artifact_admission.py`) の構造 pin が今回の hunk で赤になる形はあるか。焦点走に含めるべき consumer test file を列挙せよ。
6. **変異 matrix の帰属:** plan の変異候補について、「期待 killer が実際に赤になるか」を静的に追い、赤にならない候補 (恒真) を指摘せよ。既存 test だけで殺せる変異 (新 test 不要) も区別せよ。
7. **scope 逸脱:** plan が依頼 (局所修正、新 gate なし、台帳・検査の追加なし) を超えている箇所、逆に依頼を満たさない箇所 (例: 「呼び手が捨てずに」の主語が execution_guard も含むのに変更しない件の説明責任)。

各所見に「放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか」を 1 行で付けよ。示せない所見は nit とし must-fix にしない。scope 外の層は「実装したふり」をせず裁定パッケージ候補として返せ。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: real 所見数 / refuted 数 / must-fix 数 / 親 brief への異議)。続けて観点 1〜7 の見出しで所見を書き、最後に `## 裁定パッケージ候補` (無ければ「なし」) と `## 焦点走に含める test file` (path 列挙)。
