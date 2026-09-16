単独段 dispatch: stage=consult; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/parent-brief.md — 親 brief (scope・実アンカー表・provisional 裁定 P1〜P4・不変条件)。**親 brief 自身も検査対象。** 読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/plan-out.md — 段 2 plan (検査対象)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/ruling-items-14-15.md — ユーザー裁定 (第 20 回 /rulings 項 14・15) の逐語。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/t2683-archive-item.md — T-2683 の起票原文。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/D474.md — D474。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/D2056.md — D2056。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/D2052-excerpt.md — D2052 抜粋。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/t126_driver.py — 変更対象。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/tests/test_t126_qualification_driver.py — 既存 test。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/artifacts.py — create-only 書込みの契約。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/campaign/execution_guard.py — `attest_and_build_receipt` L576-640 (P1 の対象)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/tests/test_s8b_floor_campaign.py — L9127-9145 `test_required_attestation_comparison_failure_has_zero_side_effects` (P1 の根拠)。読めなければ即停止。

## 依頼 — レンズ A: 正しさ境界と受理集合

plan と親 brief を**守らず攻撃**せよ。あなたは read-only で pytest 実走は不要 (静的検査でよい)。テスト実測は親が行う。

攻撃観点 (各観点で「所見 / real か refuted か / 根拠 file:line / 是正案」を書く):

1. **受理集合の不変性:** plan の変更で、attestation の受理・拒否の境界が 1 bit でも動く経路はあるか。typed 例外への差し替えで `except Exception` の包み方・rc (RC_ATTESTATION=31)・`fsm.reject` の payload key 集合が変わらないか。sidecar 書込みが成功経路 (一致時) に混入しないか。書込み失敗が rc を変えないか (D474)。
2. **規律 2・3・7 との整合:** sidecar が「診断」に留まり、checker authority や gate 入力にならないか (D474)。成功時に何も残さないことが項 15 と整合するか。sidecar の内容 (P2: 全行 + failed_fields) が過剰・不足でないか — 規律 3 の「なぜ壊れたか」に対し、expected/observed の値をそのまま載せて問題ないか (秘匿・サイズ)。
3. **create-only 経路の衝突:** `create_json` は create-only。sidecar の相対 path が accepted payload と衝突しないか。同じ stage/round で再試行が起きる経路は無いか (`run()` の attest closure、`run_series` の呼び順)。`_bound_path` の相対 path 検査に `.mismatch.json` が通るか。
4. **親 brief の provisional 裁定 P1 (execution_guard は変更なし):** 親は「非 pass 行は既に例外 message に JSON で載っている」「floor campaign は失敗時副作用ゼロを pin」を根拠に変更なしと裁定した。この根拠は正しいか。`json.dumps(failures)` が TypeError を起こしうる値 (非 JSON 型) は `expected_comparison_values` / `observed_comparison_values` の戻り値に含まれるか — 含まれるなら不一致が別例外に化ける経路であり P1 の根拠が崩れる。反証できるなら real と書け。
5. **P4 (空 comparisons でも sidecar):** 空の比較行で sidecar を書くことに意味があるか、逆に有害か。
6. **変異の帰属:** plan の変異候補は各 test を専属で殺すか。等価対照が本当に等価か。「sidecar 書込み削除」を殺す test が fork を経由せず helper 直呼びで成立するか。fork 経路 (`os._exit`) 自体の未検査を隠さないか。
7. **親 brief の実測の一般化:** 親は pin 閉包 (DW-O09) を「歴史 snapshot のみ、live 比較なし」と結論した。t126_driver.py が identity file (`orchestrator/qualification/contract.py:51` の集合、`tools/pegasus/t126_qualification.sh:799/835`) であることが、変更後の T126 実走・`verify()`・過去 attempt の再検証に与える影響を親が過小評価していないか。

各所見に「放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか」を 1 行で付けよ。示せない所見は nit とし must-fix にしない。scope 外と判断した層は「実装したふり」をせず裁定パッケージ候補として返せ。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: real 所見数 / refuted 数 / must-fix 数 / 親 brief への異議)。続けて観点 1〜7 の見出しで所見を書き、最後に `## 裁定パッケージ候補` (無ければ「なし」)。
