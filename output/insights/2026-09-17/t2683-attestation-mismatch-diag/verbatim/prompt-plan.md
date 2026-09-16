単独段 dispatch: stage=plan; sandbox=read-only; parent=/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag

必読事項の射影:
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/parent-brief.md — 親 brief (scope・実アンカー表・provisional 裁定 P1〜P4・不変条件)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/ruling-items-14-15.md — ユーザー裁定 (第 20 回 /rulings 項 14・15) の逐語。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/t2683-archive-item.md — T-2683 の起票原文 (段 6 レビュー所見)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/D474.md — D474 (診断は receipt を広げず独立 sidecar へ、rc を変えない)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/D2056.md — D2056 (較正 CLI の失敗時診断 sidecar の先例)。読めなければ即停止。
- /home/SFC/tanab/.claude/jobs/103fe2ce/tmp/wave/D2052-excerpt.md — D2052 抜粋 (T126 attestation の受理集合と T-2683 の位置づけ)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/t126_driver.py — 変更対象 (`_attest` L449-475、`run()` 内 `attest` closure L1191-1261、`run_series` の `fsm.reject("attestation", ...)` L761-769 / L815-823、例外階層 L99-140、RC 定数 L89-97)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/tests/test_t126_qualification_driver.py — 既存 test (`_attest_fixture` L270-288、`test_t541_attest_*` L290-367、`test_attestation_failure_is_terminal_reject_with_exact_rc` L661-676)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/artifacts.py — `file_record` L131、`create_bytes` L402、`create_json` L527、`load_json_strict` L557。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/campaign/env_attestation.py — `compare_profiles` L985-1017 (比較行の形)。読めなければ即停止。
- /work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2683-attestation-mismatch-diag/orchestrator/qualification/series.py — `SeriesFSM.reject` L366-378 (台帳 payload の形)。読めなければ即停止。

## 依頼

[T-2683] の実装 plan を file:line 粒度で起草せよ。あなたは read-only で、書込み可能な tmp が無いので pytest の実走は不要 (静的検査でよい)。テストの実測は親が行う。

**目的:** T126 資格判定 driver の attestation が不一致で終わるとき、既存 `compare_profiles` が返す比較行 (field / expected / observed / verdict) を捨てずに、失敗時だけ attempt dir に診断 sidecar を 1 つ残す局所修正。新しい gate は作らず、受理集合は変えない。

**親 brief の provisional 裁定 (P1〜P4) と不変条件 (a)〜(f) を前提に、次を書け:**

1. **変更一覧 (file:line 粒度):** 各 hunk について「現行コード → 変更後」の骨格 (関数名・引数・戻り値・例外型・sidecar の相対 path と JSON の key 集合) を示す。`execution_guard.py` は変更しない (P1)。
2. **子側処理の抽出:** `run()` 内の `attest` closure の forked 子側 (`_attest` → `create_json` → `os._exit`) を module-level helper に抽出する設計。helper の signature と、fork なしで test から呼べる形。`os._exit` は closure 側に残すか helper に含めるかを理由付きで決める。
3. **typed 例外:** `_attest` が不一致時に上げる例外の型名・属性 (比較行・両 sha256・projection schema)。既存 test の `pytest.raises(QualificationDriverError, match="comparison contains a mismatch")` を壊さない条件。
4. **親側 message:** 子 rc≠0 のとき sidecar の実在を見て `AttestationError` の message に相対 path と failed field 名を含める案の具体形。`run_series` は変更しない。sidecar が壊れている・読めないときの扱い (rc と reject payload は不変)。
5. **test 一覧:** 正例 (1 field 不一致 → sidecar に当該行が verdict≠pass で載る、他の行は pass)、負例 (一致 → sidecar 不在・accepted payload の bytes 不変)、空 comparisons、sidecar 書込み失敗で rc 不変、既存 test の維持。各 test の名前・配置・stub 境界 (何を monkeypatch し何を実物で通すか)。
6. **変異事前登録の候補:** 各 test を専属で殺す変異 (例: sidecar 書込み削除、成功時にも書く、failed_fields を空にする、rows を落とす) を 6〜10 件、期待 killer test 名つきで列挙。等価対照 (comment だけ) を 1 件含める。
7. **リスク:** create-only path の衝突、`evidence_manifest` (`rglob`) / `verify()` への影響、`attestation_records` (未使用) との関係、identity file (`contract.py:51` の識別集合) としての t126_driver.py の扱い、`V2_ENV_NEUTRAL_MODULES` の env literal 禁止。

予算が尽きそうなら途中結論を下の出力形式どおり書いて終われ (無出力が最悪)。

## 出力形式

Markdown。先頭に `## 総括` (10 行以内: 変更 hunk 数、新規 test 数、変異候補数、親 brief への異議の有無)。続けて上の 1〜7 を見出しにして書く。file path は worktree の絶対 path または repo 相対 path で書く。
