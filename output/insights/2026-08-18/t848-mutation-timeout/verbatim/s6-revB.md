### 1. queue 由来の terminal `TIMEOUT` は閉じている

**主張:** 全 timeout 経路を追った範囲では、repo が認める runner 経由で queue timeout が mutation の terminal `TIMEOUT` になる反例はない。ただし terminal `TIMEOUT` 自体は local で新規 submission がない実行 timeout に残るため、「全 timeout producer がゼロ」ではなく「queue timeout producer がゼロ」と限定すべきである。

**根拠 file:line:**

- collection timeout は記録前に拒否: [tools/mutation_harness.py:1318](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1318)、[tools/mutation_harness.py:1339](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1339)
- baseline timeout は baseline `TIMEOUT` になり、その後 production write gate で停止: [tools/mutation_harness.py:1732](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1732)、[tools/mutation_harness.py:2765](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:2765)
- mutation の dispatch または local 新規 submission timeout は status 算出前に停止: [tools/mutation_harness.py:1838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1838)、[tools/mutation_harness.py:1857](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1857)
- local かつ新規 submission なしだけは terminal `TIMEOUT`: [tools/mutation_harness.py:1665](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1665)、[tools/mutation_harness.py:1867](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1867)
- dispatch producer は qsub 前に新規 directory を作る: [tools/pegasus/dispatch_compute.py:1535](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/pegasus/dispatch_compute.py:1535)
- `_stop_process` 内の二つの timeout は cleanup timeout で台帳 status producer ではない: [tools/mutation_harness.py:1558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1558)、[tools/mutation_harness.py:1565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1565)

**深刻度:** nit

**成果物影響:** 現実装では queue timeout による `summary.TIMEOUT` と `completed` の増加はないが、裁定文を広く読むと正当な local 実行 timeout まで存在しないと誤記する。

### 2. `--runner-mode` と runner argv の整合は wrapper 層で強制されない

**主張:** worktree は申告 mode と任意の runner argv をそのまま harness へ渡し、fanout は `dispatch` をハードコードしながら `--force-dispatch` を追加も検証もしない。harness が timeout を fail-closed にするため偽の terminal は防ぐが、fanout の標準経路は caller が `--force-dispatch` を忘れると実 local へ倒れ、baseline が証拠不一致で停止する。

**根拠 file:line:**

- worktree の無検証転送: [tools/mutation_worktree.py:674](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_worktree.py:674)、[tools/mutation_worktree.py:1090](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_worktree.py:1090)
- harness は `run_tests.py` を両 mode で許し、force の有無を検証しない: [tools/mutation_harness.py:725](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:725)、[tools/mutation_harness.py:743](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:743)
- fanout は `dispatch` を申告するだけ: [tools/mutation_fanout.py:656](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_fanout.py:656)、[tools/mutation_fanout.py:683](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_fanout.py:683)
- `run_tests.py` は Pegasus login でも force がなければ bounded scope 等で local 実行可能: [tools/run_tests.py:1856](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/run_tests.py:1856)
- dispatch 申告なのに local stdout なら receipt 検証で拒否: [tools/mutation_harness.py:1382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1382)

**深刻度:** must-fix

**成果物影響:** 偽の KILLED 値にはならないが、fanout shard が baseline で停止し、期待した K/M 台帳と merge 済み検出力が生成されない。dispatch mode では `--force-dispatch` を起動前に必須検証すべきである。

### 3. M2 の kill は現在の fixture では受理挙動へ帰属しない

**主張:** M2 で before snapshot を旧条件へ戻しても、機能テストの repo は開始時に submission がゼロなので、旧実装の `before=set()` でも新規 directory を検出できる。落ちるのは内部呼出順だけを固定した parameterized test であり、DW-M03 の受理集合または fail-closed 挙動の kill にならない。

**根拠 file:line:**

- M2 対象: [tools/mutation_harness.py:1601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1601)
- 機能 fixture は timeout 中に初めて directory を作る: [orchestrator/tests/test_mutation_harness.py:69](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:69)、[orchestrator/tests/test_mutation_harness.py:926](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:926)
- M2 を殺す現テストは inventory 呼出イベントだけを見る: [orchestrator/tests/test_mutation_harness.py:1694](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:1694)、[orchestrator/tests/test_mutation_harness.py:1731](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:1731)

**深刻度:** blocker

**成果物影響:** M2 を KILLED と数えると、実際には acceptance gate を検出していない 1 件が検出力の分子へ混入する。

実効 gate は [orchestrator/tests/test_mutation_harness.py:879](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:879) の正例に既存 submission directory を事前作成すること。正実装は terminal `TIMEOUT`、旧 snapshot 条件は偽の `runner-mode-violation` 停止になる。

### 4. M4 と M5 は共有 gate へ重なり、M5 の期待 node は一つではない

**主張:** M4 の自然な実装点と M5 の指定点はいずれも after-run の共有 `raise pending_stop` になる。M5 を削ると local と dispatch の両テストが落ちる。dispatch fixture では次の変異開始 gate が rc=2 を回復するため、赤の直接原因は追加された「terminal 0 件」assert だが、D454 専用の単一 node kill ではない。

**根拠 file:line:**

- local と dispatch が共有する停止点: [tools/mutation_harness.py:1838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1838)、[tools/mutation_harness.py:1847](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1847)
- 削除後も次の変異開始時に hold が再検出される: [tools/mutation_harness.py:1816](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1816)
- local node: [orchestrator/tests/test_mutation_harness.py:908](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:908)
- dispatch nodeの terminal 0 assert: [orchestrator/tests/test_mutation_harness.py:1002](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:1002)、[orchestrator/tests/test_mutation_harness.py:1011](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:1011)
- M4/M5 の事前登録: `/home/SFC/tanab/.claude/jobs/83ce835f/tmp/dev-wave-t848/s4-ruling.md:113-114`

**深刻度:** blocker

**成果物影響:** M5 の期待 node を dispatch test だけにすると実測は `MISMATCH` となり、M4とM5を別の独立 kill と数える検出力行列も成立しない。

M5 は [tools/mutation_harness.py:290](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:290) を dispatch 専用に再照準し、`if timed_out or receipt_requires_hold` を `if runner_mode_violation or receipt_requires_hold` へ変異させるべきである。M4 は local の即停止だけを無効化する別 anchor を明記すべきである。

### 5. parameterized node の完全集合が実装報告で丸められている

**主張:** 追加テストのうち inventory test は 2×2 の4 nodeである。実装報告の関数名だけを mutation spec へ転記すると、DW-M08 の完全一致に失敗する。

**根拠 file:line:** [orchestrator/tests/test_mutation_harness.py:1684](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_harness.py:1684)、実装報告 `/home/SFC/tanab/.claude/jobs/83ce835f/tmp/dev-wave-t848/s5-author.md:35`

完全な node ID は次の4件である。

- `orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[False-local]`
- `orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[False-dispatch]`
- `orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[True-local]`
- `orchestrator/tests/test_mutation_harness.py::test_dispatch_inventory_snapshot_precedes_runner_in_every_mode[True-dispatch]`

旧 snapshot 条件で落ちるのは先頭3件で、`[True-dispatch]` は生存する。

**深刻度:** blocker

**成果物影響:** 関数名へ丸めた期待集合では、記録 node との差が必ず生じ、M2 は KILLED ではなく MISMATCH になる。

### 6. DW-M06 は実装後の timeout 分類と逐語不整合

**主張:** DW-M06 は timeout を記録して harness を継続すると無条件に読めるが、実装後は queue 由来 timeout を非 terminal sidecar と rc=2で停止する。

**根拠 file:line:** [docs/dev-wave/mutation.md:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/docs/dev-wave/mutation.md:37)、[tools/mutation_harness.py:276](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:276)、[tools/mutation_harness.py:2828](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:2828)

**深刻度:** must-fix

**成果物影響:** docs を正本にした次 wave が queue timeout を正当な terminal `TIMEOUT` と再登録し、`completed` と検出力分母を再び汚染しうる。

1行置換案: `hang しうる変異は spec の hang_risk で隔離し、実行 timeout は fail-open の証拠として記録して継続し、queue 由来 timeout は非 terminal 停止にする（F32）。`

### 7. 新理由の production consumer がなく、local wrapper receipt が不整合

**主張:** 全件検索では、`runner-mode-violation` は論理 producer 1件と test assert 1件だけで、production reader はゼロである。`new_dispatch_submission` は producer 1件、runtime consumer 1件、test assert 1件であり、sidecar へは汎用 dict コピーされるだけで個別検証されない。特に worktree は sidecar の存在確認を dispatch mode に限定するため、local 停止の wrapper receipt は `failure=null` のまま container を保全する。

**根拠 file:line:**

- key producerと唯一の runtime reader: [tools/mutation_harness.py:1643](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:1643)、[tools/mutation_harness.py:280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:280)
- 新理由 producerとsidecar汎用保存: [tools/mutation_harness.py:292](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:292)、[tools/mutation_harness.py:2466](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:2466)、[tools/mutation_harness.py:2492](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_harness.py:2492)
- worktree の mode gate: [tools/mutation_worktree.py:1173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_worktree.py:1173)
- receipt の `failure` 出力: [tools/mutation_worktree.py:979](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/tools/mutation_worktree.py:979)
- 既存 consumer test は dispatch だけ: [orchestrator/tests/test_mutation_worktree.py:662](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_worktree.py:662)、[orchestrator/tests/test_mutation_worktree.py:671](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t848-mutation-timeout/orchestrator/tests/test_mutation_worktree.py:671)

**深刻度:** must-fix

**成果物影響:** mutation ledger は terminal 0を保つが、wrapper receipt の停止理由が `null` となり、「なぜ K/M 台帳が未完了か」を consumer が機械検証できない。

`mutation_worktree.py` は mode と独立に sidecar を読み、`reason.code` を `failure` へ伝播する必要がある。これは段4の no-touch 指定と衝突するため、fix 前に再裁定が必要である。

## 総括

blocker は3件。  
最優先はM2の再照準で、現状の kill は受理挙動ではなく内部呼出順しか証明しない。  
次にM4/M5の分離と、parameter suffix を含む期待 node 完全集合の確定が必要。  
pytest は実走せず、禁止ファイルとネットワークには触れていない。