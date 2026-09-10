静的検査のみです。pytest は未実施です。

### A-01 — `DW-S09` の非成功結果 catch-all が消失

- **ID:** A-01
- **主張:** Sup-3 の担い手は上位互換ではない。削除前の「`landed` / `already-landed` 以外はすべて `DW-STOP`」という catch-all が残っていない。
- **根拠:** 削除前の `docs/dev-wave/core.md@60314069^:107-109` は「他結果は `DW-STOP`」と明記していた。現行 `DW-O23` は postcondition failure の停止と stale/busy の再開だけを規定する一方、helper は `not-landed`、`fold-failed`、`fold-recovery-failed`、`fold-rollback-failed`、`rejected` も返す（[operations.md:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:129)、[dev_wave_land.py:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/dev_wave_land.py:47)、[dev_wave_land.py:1549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/dev_wave_land.py:1549)、[dev_wave_land.py:1608](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/dev_wave_land.py:1608)、[dev_wave_land.py:1955](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/dev_wave_land.py:1955)）。段 9 では `DW-O23` と `DW-STOP` を読むが、これら全結果を `DW-STOP` へ結ぶ文はない（[dev-wave.md:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:75)、[core.md:20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:20)）。
- **深刻度:** must-fix
- **成果物影響:** 未分類の land 失敗を同一 context 内で再試行・迂回でき、監査済み集合だけを取り込む段 9 の fail-closed 境界が曖昧になる。

### A-02 — fresh-context 報告から既存 branch が脱落

- **ID:** A-02
- **主張:** Sup-3 の削除前にあった「既存 branch を含めて再開を報告する」義務は、`DW-O23` と入口終端を合わせても保存されていない。
- **根拠:** 削除前 `docs/dev-wave/core.md@60314069^:109` は「main HEAD と既存 branch、条件再評価を含む fresh-context 再開を報告」と要求した。現行 `DW-O23` は既存 branch の**再利用**と条件再評価を要求するだけで、報告を要求しない（[operations.md:129](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:129)）。入口終端の報告項目は main HEAD・停止理由・次タスク・再開コマンドで、既存 branch がない（[dev-wave.md:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:112)）。
- **深刻度:** must-fix
- **成果物影響:** 次 context が継続対象 branch を一意に復元できず、別 branch の再利用や成果物取り違えを招く。

### A-03 — `F146` の担い手参照が stale

- **ID:** A-03
- **主張:** 表義務そのものは `DW-O16` に残るが、failure 台帳は削除後も `DW-S06-C` が要求すると記している。
- **根拠:** [failures.md:3379](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/failures.md:3379) は `DW-S06-C` を指すが、現行節には表要求がない（[workers.md:65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/workers.md:65)）。実際の担い手は [operations.md:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:83)。
- **深刻度:** nit
- **成果物影響:** live dispatch は `DW-O16` を読むため受理集合は変わらないが、再発検知の正本探索が誤誘導される。

### 静的に確認できた非所見

- Sup-1 は保存されている。段 1 は `DW-S01` を無条件に読み、同節が前提実測を本走と区別して `DW-O19` の復元規律へ送る。tracked file 変異時にも条件 19 が発火する（[core.md:35](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:35)、[dev-wave.md:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:61)、[dev-wave.md:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:101)）。
- Sup-2 は保存されている。焦点再レビュー直前に条件 16 が発火し、`DW-O16` は対応表に加えて「表なしで root cause を closed としない」まで要求する（[dev-wave.md:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/.claude/commands/dev-wave.md:98)、[operations.md:83](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:83)）。

追加 test の分岐削除後は次のとおりで、3 件とも恒真ではない。

| test | 対象削除後の遷移 | 判定 |
|---|---|---|
| missing `-rf` | `main()` が runner 側まで進み、禁止 sentinel の `AssertionError` が期待する `HarnessError` を外す | 赤になる |
| mutation rc=1 / failed=[] | `expected_keys != failed_keys` により `MISMATCH` | `PARSE_ERROR` assert が赤 |
| baseline rc=1 / failed=[] | `PASSED` 条件を外れて `FAILED` | `PARSE_ERROR` assert が赤 |

根拠は [test_mutation_harness.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_mutation_harness.py:290)、[test_mutation_harness.py:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_mutation_harness.py:467)、[test_mutation_harness.py:480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/orchestrator/tests/test_mutation_harness.py:480)、対象実装は [mutation_harness.py:1187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1187)、[mutation_harness.py:1222](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1222)、[mutation_harness.py:1888](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/tools/mutation_harness.py:1888)。baseline の monkeypatch は runner 結果だけを差し替え、実物の `_failed_nodes` と status 分岐は通るため、検査対象の迂回ではない。既存期待値の変更もない。

待ち手 3 条は一次控えの三要素を保持している（[一次控え:23](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-05-background-waiter-duplication.md:23)、[core.md:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/core.md:17)）。残留 `.done` は一次控えでは候補名のみだが、その参照先の「旧結果の誤読」を、現行 `DW-O01` の削除禁止・再利用禁止・再投入停止が包含している（[一次控え:39](/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-05-background-waiter-duplication.md:39)、[operations.md:9](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/operations.md:9)）。

`mutation.md` は親・commit 双方の blob SHA が同一で、3,674 bytes のまま。`DW-M08` の全文も残り、今回削除した他義務との不整合は見つからなかった（[mutation.md:49](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t597-budget/docs/dev-wave/mutation.md:49)）。

## 総括

must-fix は **2 件**、nit は **1 件**。判定は **NO-GO**。Sup-3 で失われた「全非成功結果の停止」と「既存 branch の報告」を明示的に復元または完全委譲する必要があります。