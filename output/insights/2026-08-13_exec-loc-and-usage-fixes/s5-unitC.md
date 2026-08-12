## 変更したファイルと差分の要約 (file:line)

- [admission_registry.json](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/tools/pegasus/admission_registry.json:4): ledger entry の metadata 3 項目を是正。`class` は `unknown` のまま。
- [test_hooks.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/orchestrator/tests/test_hooks.py:1753): `_PEGASUS_EXPECTED_ENTRIES` の golden を更新。`_PEGASUS_EXPECTED_CLASSES` は `unknown` を維持。
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/orchestrator/tests/test_check_docs.py:1244): ledger fixture を新 metadata に同期。
- [test_check_docs.py](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/orchestrator/tests/test_check_docs.py:1292): 非 Pegasus entry の evidence を厳密に `runbook §7.0 実測` とすると、実測表の path 集合不一致になる負例を追加。

指定された既存 negative test 4 件は削除・反転せず残っています。

## registry の新 entry (4 field 全部を逐語で)

- `class`: `unknown`
- `reason`: `inputs are hard-capped; isolated-scope and cap-boundary measurements are unavailable`
- `primary_gate`: `hook deny pending isolated-scope admission evidence`
- `evidence`: `compute-node shared-service cgroup delta sampling (not runbook 7.0 isolated-scope evidence); default --json argv over 25 files; 5 valid runs, max +19.7 MiB, certified 147.7 MiB with +128 MiB margin; 1 negative-delta run excluded`

旧 reason は、`DEFAULT_MAX_FILES=25`、`MAX_TOTAL_BYTES`、`MAX_LINE_BYTES`、`MAX_RECORDS`、`MAX_REQUESTS` などの hard cap が実在する実装と矛盾していました。旧 evidence の `unmeasured` も、計算ノードで共有 service cgroup の delta sampling が行われた事実と矛盾していました。ただし専有 scope による canonical 測定でも cap 境界測定でもないため、`local-ok` にはせず `unknown` を維持しています。

## canonical bytes 契約を満たすことの確認方法と結果

loader で registry 全体を読み、次を assert しました。

- raw bytes と `json.dumps(..., ensure_ascii=False, indent=2, allow_nan=False) + "\n"` が一致
- entry の key 順が `class, reason, primary_gate, evidence`
- ledger の `class == "unknown"`

結果は `loader_rc=0 canonical_bytes=ok class=unknown` です。`git diff --check` も問題ありません。

## 実走した nodeid と結果

pytest nodeid は実行開始まで到達できませんでした。リポジトリ規律に従い、direct pytest ではなく次の対象を `tools/run_tests.py` 経由で 2 回試行しました。

- `orchestrator/tests/test_hooks.py` 全体
- `orchestrator/tests/test_check_docs.py::test_admission_non_pegasus_registry_entry_requires_projection_only`
- `orchestrator/tests/test_check_docs.py::test_admission_non_pegasus_runbook_measurement_is_absent_from_measured_table`

ログイン側は約 13.4–13.5 GiB／14 GiB 使用中で保留余白を満たさず、dispatch 側も `qstat -Q preflight rc=1` で停止しました。両試行とも runner rc=16 であり、これらを「緑」とは報告しません。

実走できた非 pytest 検査は次のとおりです。

- registry loader：rc=0
- `python3 tools/check_docs.py`：rc=0、違反なし
- `python3 tools/check_codex_agents.py`：rc=0

## 期待赤 1 件以外の赤があったか (あれば全部)

期待赤を含め、文書検査の赤はありませんでした。共有 worktree では親所有の [pegasus-runbook.md](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-exec-loc-and-usage-fixes/docs/pegasus-runbook.md:460) が既に新 evidence へ更新されており、投影不一致が解消済みだったためです。

pytest runner の rc=16 はテスト回帰ではなく、headroom／dispatch infrastructure による実行前停止です。

## 所有外への波及可能性

- `docs/pegasus-runbook.md`：class/evidence 投影行との完全一致が必要。親変更で既に同期済み。
- `tools/check_docs.py`：evidence が厳密に `runbook §7.0 実測` の entry だけを実測表へ要求する。非 Pegasus path は実測表 parser で表現できず、今回の負例で構造を固定。
- `tools/pegasus_admission_registry.py`：canonical bytes、field 順、非 Pegasus `local-ok` 禁止を検証。変更していない。
- `hooks/guard_bash.py`：registry の class を admission に使用する。`unknown` 据置のため受理集合は広がらず、ledger は引き続き拒否対象。
- `tools/collect_wave_usage.py`：registry を直接消費せず site policy で別途遮断するため、この metadata 是正だけでは収集を unblock しない。
- 同時変更中の `tools/claude_session_ledger.py`、`tools/collect_wave_usage.py`、関連テスト、docs、insight 類には一切編集を加えていません。

## 総括

所有対象 3 ファイルだけを変更し、ledger の hard cap と計算ノードでの非 canonical 実測を正確に反映しました。`class` は裁定どおり `unknown` を維持し、canonical loader と文書検査は通過しています。非 Pegasus entry を canonical 実測扱いにすると実測表の path 集合検査が赤になる負例も追加しました。pytest は実行基盤の rc=16 により未実走であり、緑とは扱っていません。