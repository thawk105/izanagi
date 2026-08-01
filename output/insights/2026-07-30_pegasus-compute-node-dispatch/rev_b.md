## 総括

- must-fix は **7件**:
  1. PBS 会計痕跡の偽陽性
  2. qsub 成功後の所有権移行が非 atomic で孤児化
  3. F49(a) の「実 FS 永続」検査が自己参照
  4. qstat 一時障害による恒久ラッチ
  5. receipt / task-run 永続化失敗を無視して rc=0
  6. 新規 `site_policy.py` が Python 3.9 で import 不可
  7. `guard_bash` の literal command 迂回
- 受入経路は happy path の配線だけなら到達可能。しかし、**得られた rc=0 を正しい compute-node 受入証拠として信用できないため、受入実行可能とは判定しない**。
- **孤児ジョブの危険あり**。qsub 応答解析失敗、親死亡、qdel 失敗で残る。
- **恒久ラッチの危険あり**。一度の immediate qstat 障害で自動復旧不能になる。
- 判定: **NO-GO**

## must-fix

### M1. PBS accounting の検査が文字列検索にすぎず、偽の `accounting_verified=true` を作る

根拠は [`dispatch_compute.py:43–46`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:43) と [`dispatch_compute.py:416–418`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:416)。正規表現は `memory`、`walltime`、`nqsv` のどれか一語を見つけるだけで、[`dispatch_compute.py:750–790`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:750) はそれを根拠に `accounting_verified=true` とする。

純関数検査では、実会計でない `worker hit MemoryError but recovered` や `test_walltime_policy passed` に対しても `True` になった。実測 NQSV epilogue は Request ID、Started、Ended、Elapse を持つ [`izanagi-probe-compute.e874129:3`](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/izanagi-probe-compute.e874129:3)。既存コードには Request ID の一致と必須3 field を検査する正しい実装が既にある [`silo_ladder_rung1.py:3662–3701`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/silo_ladder_rung1.py:3662)。

失敗シナリオ: child stderr に `MemoryError` が出て回復し rc=0、NQSV epilogue はまだ遅延中。親は会計済みと誤認して rc=0 を返す。

成果物影響: **dispatcher receipt と task-run が、PBS 会計未確認なのに verified/green を主張し、provenance を偽る。**

### M2. qsub 成功とジョブ所有権取得が atomic でなく、孤児ジョブが残る

[`dispatch_compute.py:637–657`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:637) では qsub rc=0 の後に stdout を parse し、その後で初めて `active=True` にする。parse 例外時は `request_id=None`、`active=False` のため、例外処理の qdel 条件 [`dispatch_compute.py:795–808`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:795) に入らない。

さらに捕捉する signal は SIGINT/SIGTERM だけ [`dispatch_compute.py:615–622`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:615)。SIGHUP、SIGKILL、OOM、親プロセス死亡に対する scheduler-side lease がない。qdel 自体も一回の best-effort で、成功確認も再試行もない [`dispatch_compute.py:469–494`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:469)。

失敗シナリオ: NQSV がジョブを受理したが応答形式が変わり parse 不能、または qsub return 直後に親が死亡。ジョブは walltime まで shared worktree 上で走り続ける。

成果物影響: **孤児テストが後続受入と競合し、後続 task-run の rc・ログ・生成物を再現不能にする。**

### M3. F49(a) の実 FS 永続検査が、親自身の namespace を読み直すだけ

[`dispatch_compute.py:421–434`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:421) は親が直前に作った3ファイルを同じ process から `is_file()` しているだけである。overlay/sandbox 内でも当然 `True` になる。`fsync` も別 namespace や compute node からの可視性を証明しない。

失敗シナリオ: qsub と qstat は見えるが submission dir は sandbox overlay にしか存在しない。F49(a) は通過し、compute bootstrap は request/probe を読めない。その後は F49(c) 型として rc=16 になるだけで、ラッチされず同じ無効投入を繰り返せる。

成果物影響: **receipt が `output_dir_persistent=true` と虚偽記録し、本来必要な F47 handoff/latch 成果物が作られない。**

### M4. immediate qstat の一時障害一回で harness が恒久停止する

qsub 直後の qstat は一回だけ [`dispatch_compute.py:659–670`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:659)。非ゼロなら直ちに F47 として global latch を作る [`dispatch_compute.py:671–690`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:671)。次回以降は scheduler を一度も呼ばない [`dispatch_compute.py:562–566`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:562)。テストもこの永久停止を仕様として固定している [`test_pegasus_dispatch_compute.py:232–257`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/tests/test_pegasus_dispatch_compute.py:232)。

失敗シナリオ: qsub は正常だが scheduler の eventual consistency または一時的 qstat 障害で最初の照会だけ rc≠0。ジョブを削除してラッチし、復旧 CLI も再検証経路もない。

成果物影響: **一過性障害以後、全走 receipt と task-run 成果物を二度と自動生成できない。**

### M5. receipt 永続化に失敗しても child rc=0 を返す

[`dispatch_compute.py:497–512`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:497) は preferred/fallback の両方へ書けない場合 `None` を返す。成功経路は返値を確認せず rc を返す [`dispatch_compute.py:787–794`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:787)。task-run 側も記録例外を握り潰す [`run_tests.py:893–907`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:893)。

失敗シナリオ: home quota/inode 枯渇で child は rc=0 だが receipt 作成だけ失敗。親はそのまま 0 を返す。

成果物影響: **dispatcher receipt または task-run 台帳が存在しないのに、shell 上は受入成功になる。**

### M6. `site_policy.py` は Python 3.9 で import 時に落ちる

新規 [`site_policy.py:19`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/site_policy.py:19) は `from __future__ import annotations` がないまま `str | None` を使用している。Python 3.9 では関数定義時に `TypeError` となる。

他の新規ファイルは確認済みで、`dispatch_compute.py`、`test_pegasus_dispatch_compute.py`、`test_build_site_gate.py` は future import あり、`test_site_policy.py` は PEP 604 annotation なし。問題はこの production module 一件である。

dispatcher の正規 job script は先に 3.10 を選ぶため happy path は逃げるが、Python 3.9 の非 Pegasus 環境で [`run_tests.py:45`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:45) を import しただけで既存挙動が破壊される。既定 `python3` を直接使う compute-side module も同様である。

成果物影響: **site gate・result.json・receipt の作成前に import crash し、受入成果物が残らない。**

### M7. `guard_bash` の明示的な wrapper/shell 対応を実際の literal command で迂回できる

LOGIN を明示して `decide()` のみを呼び、コマンド自体は実行していない。偽許可は以下。

- `env -S 'pytest -q'`
- `env -S 'python3 -m pytest -q'`
- `bash -xec 'pytest -q'`
- `sh -euxc 'cmake --build build'`
- `python3 -mpytest -q`

原因は、`env -S` の文字列を再 tokenize せず値として捨てる [`guard_bash.py:177–201`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:177)、shell option を `-c/-lc/-ic` の完全一致でしか認識しない [`guard_bash.py:401–405`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:401)、Python の `-m` を分離 token でしか認識しない [`guard_bash.py:341–347`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/hooks/guard_bash.py:341) こと。

これは docs に列挙された「script/変数展開等の既知限界」ではなく、裁定が機械対応を要求した literal wrapper/shell command そのものである。

成果物影響: **ログインノード上の pytest/build 出力を compute-node 受入ログとして誤採用できる。**

## 中断・失敗経路

| 事象 | 実際の挙動 | 判定 |
|---|---|---|
| SIGINT/SIGTERM | `active=True` 後なら qdel を一回試す | qdel 失敗確認なし |
| 親死亡/SIGHUP/SIGKILL | lease/heartbeat なし | 孤児化 |
| walltime/overall timeout | bounded、後で qdel | 無限待ちはないが qdel 失敗で孤児 |
| HLD | queue timeout または overall timeout で終了 | 無限待ちはない |
| qsub rc≠0 | infra rc=16 | 正常。ただし「受理済み・応答解析不能」は孤児 |
| immediate qstat 一時障害 | 即 qdel＋永久 latch | must-fix M4 |
| RUN 中の qstat 一時障害 | polling を即終了し、60秒だけ result を待って qdel | valid job を誤停止 |
| `.e` 遅延 | 60秒猶予、失敗時は invocation rc=16、ラッチなし | 型分け自体は裁定どおり。ただし M1 で偽陽性 |
| child signal return | receipt/task-run は `-9` 等、shell は `247` 等へ変換 | rc の意味が二義化 |

F49(ii) のコード上の分離は、(a)(b) が [`dispatch_compute.py:659–690`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:659)、(c) が [`dispatch_compute.py:725–814`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:725) で、**構文上は裁定どおり**。しかし M1/M3/M4 により意味上は成立していない。

## guard_bash の20例

| 分類 | コマンド | 判定 |
|---|---|---|
| 通常操作 | `git status --short` | ALLOW |
| 通常操作 | `python3 tools/check_docs.py` | ALLOW |
| 通常操作 | `codex exec 'review this diff'` | ALLOW |
| 通常操作 | `qsub job.sh` | ALLOW |
| 通常操作 | `python3 tools/run_tests.py -q` | ALLOW |
| 正常拒否 | `pytest -q` | DENY |
| 正常拒否 | `python3 -m pytest -q` | DENY |
| 正常拒否 | `sudo -u tanab pytest -q` | DENY |
| 正常拒否 | `bash -lc 'pytest -q'` | DENY |
| 正常拒否 | `cmake --build build` | DENY |
| 偽許可 | `env -S 'pytest -q'` | ALLOW |
| 偽許可 | `env -S 'python3 -m pytest -q'` | ALLOW |
| 偽許可 | `bash -xec 'pytest -q'` | ALLOW |
| 偽許可 | `sh -euxc 'cmake --build build'` | ALLOW |
| 偽許可 | `python3 -mpytest -q` | ALLOW |
| 偽拒否 | `ctest --show-only=json-v1` | DENY |
| 偽拒否 | `pytest -h` | DENY |
| introspection | `make -n -j48` | ALLOW |
| introspection | `ninja -t targets` | ALLOW |
| introspection | `ctest -N` | ALLOW |

## should-fix

1. RUN 中の qstat 非ゼロを一回で終了扱いする  
   [`dispatch_compute.py:698–723`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:698)。連続失敗数または bounded retry が必要。現在は一時障害で正常な長時間ジョブを60秒後に削除する。

2. child の signal rc を正規化する  
   [`dispatch_compute.py:315–341`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:315)。raw signal と shell-visible rc=`128+signal` を別 field にし、receipt/task-run/shell の意味を一致させるべき。

3. live dirty worktree を source identity なしで実行している  
   request は repo path、args、env しか束縛しない [`dispatch_compute.py:573–595`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:573)。queue 待ち中に tree が変わると別 bytes を試験する。既存 submitter は source commit、clean gate、job hash を束縛している [`submit_certify.sh:75–85`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/submit_certify.sh:75)。本 wave は dirty tree を試験する必要があるため clean gate の流用は自己拒否になる。submit時/child開始時の worktree manifest hash、または snapshot が必要。

4. dispatcher が既存 submission logic を再実装している  
   request ID parser/normalizer、scheduler filename 検出、accounting regex、receipt writer が重複する。特に弱い accounting regex は既存 [`collect_receipt.py:27–73`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/collect_receipt.py:27) から同じ欠陥を増殖させた一方、厳格 validator は別に存在する。共通核抽出は裁定で別 wave に送られているため今回は backlog 扱いだが、規律5違反の実体は残る。

5. worker 数が構造化記録されない  
   裁定は PBS ID、queue wait、host、interpreter、worker 数を要求する [`adjudication-plan-v2.md:242`](/home/SFC/tanab/.claude/jobs/2ad09d57/tmp/wave-pegasus-compute/adjudication-plan-v2.md:242)。result payload は host/interpreter までで worker/affinity がない [`dispatch_compute.py:328–336`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:328)。高速終了して RUN を観測できない場合は `queue_wait_s` も欠ける。

6. 48 worker のメモリ前提が無計測  
   実装上の既定は affinity 全数で正しい [`site_policy.py:100–112`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/site_policy.py:100)。115 GiB / 48 は約2.4 GiB/worker で、peak RSS の gate/receipt はない。明示 `-n`、`IZANAGI_TEST_NPROC` は後勝ちで保持されている [`run_tests.py:129–143`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:129)、[`run_tests.py:290–308`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:290)。既定48を静的に否定はしないが、本 wave の全走と `-n 16` 対照を記録するまで安全とは言えない。`buildcache jobs=1` 等の明示値と既定16も維持されている [`buildcache.py:569–595`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/orchestrator/campaign/buildcache.py:569)。

7. docs が実装・裁定と矛盾する

   - runbook は F49(c) 欠落でも以後停止すると書く [`pegasus-runbook.md:378–383`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:378) が、コードは c ではラッチしない。
   - runbook は全 build を割当コア数の `-j` にすると書く [`pegasus-runbook.md:259`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:259) が、裁定どおり `buildcache` は既定16のまま。正しくは「テストの既定が最大」「coverage 4経路の既定が最大」であって、「全て最大」ではない。
   - runbook は部分 pytest も login 禁止 [`pegasus-runbook.md:254–260`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:254) だが、AGENTS は自分が触った1ファイルの pytest を許可する [`AGENTS.md:29–34`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/AGENTS.md:29)。
   - runbook の preflight は `pegasusinfo`、`check_quota`、`rbudgetcheck` まで列挙する [`pegasus-runbook.md:361–375`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/docs/pegasus-runbook.md:361) が、自動 dispatcher は `qstat -Q` だけ。operator checklist と自動保証の境界を明記すべき。

8. scheduler の元 `.o/.e` は無制限に残る  
   receipt へ取り込む tail は2 MiBだが [`dispatch_compute.py:393–413`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:393)、submission dir の元ファイルは full size のまま。長い pytest 出力で home quota を圧迫し、M5を誘発する。

## nit

- 省略 marker は改行ではなく文字列 `\n` を埋め込んでいる [`dispatch_compute.py:407`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:407)。receipt の可読性だけの問題。

## 正常に配線されている点

- `output/pegasus-dispatch/` は [`.gitignore:25`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/.gitignore:25) にあり、`git check-ignore` でも一致した。dispatcher 生成物は status/deletion gate を新たに汚さない。
- qsub cwd と `.o/.e` 探索先はどちらも submission dir [`dispatch_compute.py:344–390`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:344)、[`dispatch_compute.py:637–649`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:637)。
- job は `$PBS_O_WORKDIR` を使わず repo root へ `cd` する [`dispatch_compute.py:248–260`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:248)。
- nested `run_tests.py` は `bnode*` を COMPUTE と判定するため再 dispatch しない [`run_tests.py:927–968`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/run_tests.py:927)。
- compute branchは pip を呼ばず、xdist 不備なら rc=16 で止まる。job bootstrap は3.10を選び、その directory を PATH 先頭へ置く [`dispatch_compute.py:235–260`](/home/SFC/tanab/github/izanagi/.claude/worktrees/dev-wave-pegasus-compute-node/tools/pegasus/dispatch_compute.py:235)。

修正は Pegasus dispatcher/guard と annotation 評価に限定できる。厳格 accounting、bounded qstat retry、compute側 visibility handshake、lease、receipt fail-closed は非 Pegasus 経路を変えない。receipt field を足す場合は additive または schema v2 とし、既存 frozen bytes を書き換えない。実 job ID・source identity・会計 field を照合してから成功させるので provenance も偽らない。

検査は read-only の静的検査のみ。`git diff/status/check-ignore`、純粋な `guard_bash.decide()` と accounting helper を実行した。**pytest、qsub、cmake、build は実行しておらず、緑とは報告しない。**