単独段 dispatch: stage=review; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/parent-brief.md — 親 brief。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/stage4-ruling.md — 段 4 裁定・plan v2・変異事前登録。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/author-snapshot.patch — 段 5 author の統合差分 (レビュー対象の正本)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/author-out.md — author の最終報告 (未実走の申告を含む)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/focus1-driver.log — 親が走らせた変更 test file の単独焦点走 log。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/consultB-out.md — 段 3 レンズ B の所見 (B1 配線・B2 staging 残留・読み手の経路)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/t126_driver.py — 変更後の実体。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/tests/test_t126_qualification_driver.py — 変更後の test。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/collector.py — `_manifest` L228-246・failure receipt 経路。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/series.py — `SeriesFSM.reject` / replay。読めなければ即停止。

## 依頼 — レビュー B: 配線・実効性・波及・報告と実体の一致

段 5 の差分を**敵対的に**レビューせよ。あなたは read-only で pytest 実走は不要 (静的検査でよい)。実走結果は focus1-driver.log を一次資料とし、log に無い緑を主張しない。レビュー A (別の子) が受理集合と規律を見るので、あなたは**production 配線・consumer・波及・報告の正確さ**を見る。

観点:
1. **production 配線 (段 3 B1 の解消):** closure の子分岐 `os._exit(_run_attestation_child(...))` と親分岐 `raise AttestationError(_attestation_rejection_message(...))` が、引数 (`source_root` vs `repo_root`、`capability`、`relative`、`layout.attempt_dir`) を旧 closure と同じ実体で渡しているか。AST 配線 test `test_t2683_run_attest_closure_wires_child_helper_and_rejection_message` が M10・M11 を確実に赤にするか、逆に無関係な将来変更で偽赤になる過剰決定か。
2. **fork 経路:** `test_t2683_forked_child_writes_sidecar_visible_to_parent` が親の pytest process を汚さないか (子の例外・出力・fixture teardown)。fork 後の子で monkeypatch 済み `probe` / `load_verified_calibration` が有効か。
3. **台帳契約 test:** `test_t2683_diagnostic_rejection_preserves_ledger_contract` の post-series ケースが実際に終端 (lower_boundary) に到達して post-series attestation を呼ぶか (bits・monotonic・sleep の stub が既存 positive control と整合するか)。`events[-1]["payload"]` の exact 比較が `SeriesFSM._append` の実際の payload 形と一致するか。
4. **consumer (collector):** T5 `_manifest` test の妥当性。failure receipt 発行経路 (`collector.py` L1310-1380) で sidecar が `closure_manifest` に入る以外の影響 (exclusion 集合・`verify_manifest_closure`・schema の exact keys) が無いか。
5. **波及:** 差分が `test_t126_pegasus_tools.py` (変異 anchor registry `test_fr3_mutation_node_registry_is_exact_and_complete`、verify/receipt closure)、`test_campaign.py:5526` (evaluate 1 call)、`test_official_perf_closure.py`、`test_artifact_admission.py`、`test_t126_qualification_artifacts.py`、`test_env_contract.py` (env literal 禁止) の構造 pin を赤にする形はあるか。**新規 test 名や新規 module-level 関数名が何かの registry / allowlist / lineno pin に当たるか** を grep で確かめよ (`orchestrator/tests/` 配下)。
6. **報告と実体の一致:** author-out.md の hunk 数・test 数・anchor 表・「未実走」の申告が差分と一致するか。closed と申告していない点は妥当か。
7. **scope:** 依頼 (局所修正、新 gate なし、台帳・検査・schema 登録の追加なし、`execution_guard.py` 無変更) を超えた箇所、または満たさない箇所。

各所見に「放置時に成果物 (certified 選択・レポート・台帳) の値・受理集合・参照がどう変わるか」を 1 行で付け、示せない所見は nit とし must-fix にしない。既存テストの期待値変更を是正案にしない。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: must-fix 数 / nit 数 / GO or NO-GO)。続けて観点 1〜7 の見出しで所見 (所見 / real か refuted か / 根拠 file:line / 是正案)、最後に `## 焦点走に足す test file` (grep で当たった registry / pin を含む file の path 列挙)。
