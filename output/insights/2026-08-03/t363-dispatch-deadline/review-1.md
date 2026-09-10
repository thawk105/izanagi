判定は **NO-GO**。must-fix 2 件、nit/backlog 2 件です。pytest・`qsub/qdel/qstat` は実行しておらず、以下は fake clock とコードの静的追跡結果です。

## Must-fix

### 1. rc≠0 の偽 RUN が、後続の信頼できる RUN まで永久に無効化する

- (a) 主張: [`run_seen=True`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1215) が `current.returncode == 0` gate より先に立つため、rc≠0/stdout RUN の後に rc=0/RUN が来ても分岐へ再入場できず、deadline は submit 起点のままです。これは意図した受理集合の修復漏れです。
- (b) file:line: [dispatch_compute.py:1215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1215)–1224、初期 deadline は [同:1182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1182)。
- 時刻列: `S=0, W+G=3, poll=1` とすると、`t=0 QUE`、`t=1 rc=153/stdout RUN` で `run_seen=True`・deadline=3、`t=2 rc=0/RUN` は無視、`t=3` に overall-timeout。正しい trusted-RUN 起点なら deadline=5 で、`t=4 DONE` を受理できました。
- 判定: 後続の実 RUN を早期 qdel する点は **fail-closed**。一方、偽 RUN が queue timeout を解除する点は pre-existing な **queue 層の fail-open** ですが、初期 overall deadline は残るため無上界ではありません。
- (c) 成果物: receipt は `queue_wait_observed=true`、`queue_wait_s=1.0` のまま `outcome.kind="infra"` / `reason="DispatchError: overall-timeout"` / qdel attempted となり、該当 caller では task-run `exit_status=16`、変異台帳 `PARSE_ERROR`・`summary.completed` 非増加になります。
- (d) 修正: `run_seen` と一回限りの deadline latch を分離してください。`run_seen`/queue receipt は最初の文字列 RUN で従来どおり立て、別の `run_deadline_rebased` は最初の **rc=0/RUN** でだけ立てます。`QUE → ERROR(stdout RUN) → RUN → … → DONE` の回復テストと、現欠陥へ戻す review-derived mutation を追加すべきです。

### 2. 変異事前登録の expected node 集合が実際の赤集合と一致しない

- (a) 主張: plan v2 の「期待 kill テスト」は主検出先しか列挙していませんが、現テストは別 node も赤にします。harness は失敗 node 集合の完全一致を要求するため、表をそのまま `expected_nodes` にすると [mutation_harness.py:1191](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:1191) で `MISMATCH` です。
- (b) file:line: [plan-v2.md:77](/work/1/SFC/tanab/izanagi-jobs/466a006d/t363/plan-v2.md:77)–86、新規テスト [test_pegasus_dispatch_compute.py:1350](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1350)–1443。
- (c) 成果物: 変異台帳が期待した `KILLED` ではなく `status="MISMATCH"` / `matches_expectation=false` を記録し、`summary.KILLED` ではなく `summary.MISMATCH` が増えます。
- (d) 修正: fix 後に全 node 集合を再事前登録してください。また V3/P1 は持続 RUN/UNKNOWN で無期限化し得るため `hang_risk=true` にします。診断だけで赤になる node は独立 kill 根拠に数えません。

現差分での静的な赤集合は次のとおりです。

| 変異 | 時刻展開 | 最初に赤くなる assertion |
|---|---|---|
| V1 | T1 は `t=2 RUN` 後も D=3、`t=3` timeout | T1 [rc==0 :1362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1362)、T2 [elapsed列 :1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1387)、T3 trusted [elapsed=4 :1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1432) |
| V2 | V1 と同じ | V1 と同じ 3 node |
| V3 | T2 は D=`4→5`、`t=5 END` で成功。既存テストも D=`1→2→3`、`t=3 END` | 既存 [rc==INFRA :1340](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1340)、T1 [queue_wait_s=2 :1365](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1365)、T2 [rc==INFRA :1383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1383) |
| V4 | untrusted RUN が `t=1` に D=4 へ延長され、`t=4 END` が deadline 判定より先に成功 | T3 [untrusted_rc==INFRA :1433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1433) |
| P1 | deadline が消え、有限 fixture はすべて既定 DONE まで進んで成功 | 既存 :1340、T2 :1383、T3 [trusted_rc :1431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1431)、UNKNOWN [rc==INFRA :1462](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1462) |

登録変異に SURVIVE はありません。ただし T2/T3 による V1/V2 の追加赤と、T1 による V3 の追加赤は診断値由来であり、独立した受理集合 kill ではありません。

## Mask と上界

- pre-RUN では queue timeout と overall timeout の早い方が勝つため、HLD/QUE fixture では P1 が queue timeout に mask され得ます。登録済み UNKNOWN テストは `overall=1 < queue=20` なので回避できています。
- post-RUN は queue timeout が無効になり、固定された overall deadline が唯一の上界です。V3/P1 以外では張り直しは一度だけです。
- END 判定は deadline より先ですが、各 mutant fixture はこの順序を利用して受理集合差を作っています。`_finish()` が result/log/accounting をすべて作るため collection 層の infra エラーにも隠されません。
- 有限値・単調 clock・正の poll の範囲では、RUN、UNKNOWN、QUE/HLD/STG、QSTAT_ERROR の全非終端状態が固定 deadline に到達し、END は collection へ進みます。現差分に有限性の反例はありません。`NaN/inf` による反例は裁定済み scope 外のまま残っています。
- P1 と V1/V2 を同時適用すると deadline 自体を検査しないため V1/V2 の差は消えますが、P1 単独で赤になるため「両層同時変異でしか検出できない」穴ではありません。

## Nit / backlog

### N1. V1 と V2 は相互に等価

- (a) 初期 deadline と V1 の再代入式が同一なので、V1 と「代入削除」V2 は全実行経路で同じです。正しい実装との等価変異ではありませんが、独立な二つの欠陥型でもありません。
- (b) [dispatch_compute.py:1182](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1182)、[同:1220](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1220)。
- (c) 成果物: mutation ledger の `registered=2/KILLED=2` が独立な変異耐性を二重計上します。
- (d) 修正: 一方を畳んで等価 caveat を記録するか、grace/walltime 項を落とす非等価変異へ差し替えてください。製品成果物へ直接影響しないため nit です。

### N2. `state_history` assertion がテスト目的を超えている

- (a) T2 は `elapsed_s` と state の全列、T3 は最終 entry の dict 全体を固定しています。特に `elapsed_s` は fake fixture で `started == submitted_at == 0` という偶然にも依存します。receipt 全体比較はありませんが、T3 の subrecord 全体比較は同じ脆さです。
- (b) [test_pegasus_dispatch_compute.py:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1387)–1392、[同:1436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1436)–1441。
- (c) 成果物: harmless な診断 key 追加や setup 時刻の現実化でもテスト node が赤くなり、変異台帳を `MISMATCH` にし得ます。dispatch receipt 自体の値は悪化しません。
- (d) 修正: deadline を識別する最終 `elapsed_s` と必要な `state` だけを個別比較し、`qstat_rc/request_present` の全 dict 等価は外してください。nit です。

受理集合の意図しない拡大や scope 外 3 件の混入はありません。qdel 経路、UNKNOWN 処理、NaN/inf の現行検査は未変更で、production 差分は deadline 張り直しだけです。

## 総括

- NO-GO: untrusted RUN が trusted RUN の予算張り直しを永久に潰すため、deadline latch の分離が必要です。
- 登録変異は静的には全て検出されますが、現 plan の expected node 集合では mutation ledger が MISMATCH になります。
- 有限入力での監視上界と scope 境界は保存されており、pytest 等の実測は親の計算ノード走行待ちです。