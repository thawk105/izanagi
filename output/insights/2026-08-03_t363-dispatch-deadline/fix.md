実装を完了しました。編集は指定2ファイルのみで、docs・commit・git indexには触れていません。

### 対応表

| 所見 | 判定 | 対応 |
|---|---|---|
| F1 latch分離 | closed | `run_deadline_rebased` を追加し、最初の `rc=0` RUNだけで期限を張り直す |
| F2 回帰テスト | closed | `QUE→ERROR(stdout RUN)→RUN→RUN→DONE` を追加 |
| F3 assertion整理 | closed | T2は最終時刻＋RUN存在、T3は最終時刻・状態の個別比較へ縮小 |
| レビュー1 N1 等価変異 | closed | 旧V2を使わず、非等価なgrace脱落変異で検出根拠を確認。実台帳登録は親段 |
| レビュー1 N2 過剰決定 | closed | 指定されたT2/T3部分だけを縮小 |
| レビュー2 N-1 nonce seam | partial | 親裁定の3項目外なので変更せずbacklog維持 |

### 変更箇所と挙動差分

- [dispatch_compute.py:1047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1047)
  - `run_deadline_rebased=False` を追加。

- [dispatch_compute.py:1216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1216)
  - 変更前: rc≠0のRUNで `run_seen=True` になると、後続rc=0 RUNでも張り直せない。
  - 変更後: `run_seen` と独立して、最初のrc=0 RUNで `now + walltime_s + overall_grace_s` に一度だけ張り直す。
  - latch判定を `run_seen` 更新より先に置き、latchを `run_seen` に戻す変異をF2が固有に検出できる形にした。
  - queue wait、receipt schema、二度目以降のRUN、信頼済みRUNが来ない場合の挙動は不変。

- [test_pegasus_dispatch_compute.py:1387](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1387)
  - T2の全履歴比較を、最終 `elapsed_s == 4.0` とRUN存在確認へ縮小。

- [test_pegasus_dispatch_compute.py:1432](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1432)
  - T3の最終dict全体比較を、`elapsed_s` と `state` の個別比較へ縮小。

- [test_pegasus_dispatch_compute.py:1438](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1438)
  - F2回帰テストを追加。

### F2の時刻展開

条件は `W=2`、`G=1`、poll=1秒、初期deadline=`t=3`です。

- `t=0 QUE`
- `t=1 rc=153/stdout RUN`
  - `run_seen=True`、queue wait=1秒。
  - 信頼できないためdeadlineは3のまま。
- `t=2 rc=0/RUN`
  - 旧実装: `run_seen=True` に遮られ、deadline=3のまま。
  - 修正後: 独立latchでdeadline=`2+2+1=5`。
- `t=3 RUN`
  - 旧実装はoverall-timeout、qdel、rc=16。
  - 修正後は継続。
- `t=4 DONE`
  - 修正後は期限判定より先にENDとして完走し、rc=0、qdelなし。

### 変異耐性

- `submitted_at` 起点へ戻す:
  - T1はdeadline=3のまま、`t=3` timeoutとなり `rc==0` が赤。
  - T2は`elapsed_s=3`で終了し、期待する4秒が赤。
  - T3のtrusted対照も3秒となるため追加で赤。

- `overall_grace_s` 脱落:
  - T2は`t=1+W=3`でtimeoutし、最終4秒のassertionが赤。
  - T3 trusted対照も追加で赤。T1は`t=4 DONE`が期限判定より先なので通る。

- RUNごとに張り直す:
  - T2はdeadlineが4→5へ延び、`t=5 DONE`で成功するためinfra期待が赤。
  - 既存overall-boundテストもdeadlineが1→2→3と延び、`t=3 DONE`で成功して赤。

- `rc==0` gateを恒真化:
  - T3の偽RUNでdeadlineが3→4へ延び、`t=4 DONE`で成功するためinfra期待が赤。

- latchを `run_seen` に戻す:
  - F2では`t=1`の偽RUNが `run_seen` を立て、`t=2`のtrusted RUNが張り直せず、`t=3` timeoutとなってrc=0期待が赤。
  - latch判定順により、最初からtrusted RUNであるT1/T2はこの変異だけでは影響されない。

### 既存テストへの影響

- T3のuntrusted列には後続trusted RUNがないため、初期deadline=3、`t=3` timeoutの挙動は不変です。静的追跡上は既存期待を維持しますが、実測の緑は主張しません。
- `test_overall_walltime_plus_grace_bound_qdels_running_job` は最初のRUNが`t=0`なので、新旧ともdeadline=1です。
- `test_qstat_error_during_poll_does_not_end_or_latch_job` のERROR stdoutは空でRUNと解釈されず、後続trusted RUNで従来どおり張り直します。
- UNKNOWNのみのテストはRUN分岐へ入らず不変です。
- 既存テストの期待値、skip、削除、緩和は行っていません。

### 検査

実行済みの静的検査:

- `git diff --check`
- 対象2ファイルのインメモリ構文コンパイル
- `git diff --name-only`と`git status`による変更範囲確認

未実行:

- pytestの全走・部分走
- `tools/run_tests.py`
- qsub・qdel・qstat
- 変異の実走
- `check_codex_agents.py`、`check_docs.py`、provenance監査

## 総括

F1の期限latchを`run_seen`から分離し、偽RUN後のtrusted RUNで実行予算を回復できるようにしました。  
F2回帰テストとF3の最小assertionで、指定5変異の静的な検出根拠を維持しました。  
pytest等はログインノード制約により未実行で、実測判定は親の計算ノード走行待ちです。