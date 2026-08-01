指定4ファイルを全文確認し、静的監査しました。結論は両経路とも **closed** です。編集・pytest・mutationは実施していません。

| 監査対象 | 判定 | file:line・具体的race |
|---|---|---|
| 1. exit/reap済みdirect childのstale PGIDへsignalする経路 | **closed** | TERM直前に [`process.poll()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1782)、KILL直前にも再度 [`process.poll()`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1793) がある。exit済み未reapなら `poll()` が `waitpid(pid, WNOHANG)` でreapし、既reapなら確定済みreturncodeを返すため、どちらも `killpg` へ入らない。poll直後にexitしても、次のwaitまでPIDは再利用されないため無関係なPGIDへの置換raceは成立しない。group消滅raceは [`ProcessLookupError`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1755) で吸収される |
| 2. timed_out/live childのTERM→wait→KILL→reap経路 | **closed** | ceiling timeout後、live確認→TERM→5秒communicateが維持されている。[integration.py:1777](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1777)、[integration.py:1782](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1782)。TERM後もtimeoutなら再poll→必要時KILL→再度5秒communicate。[integration.py:1791](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1791)。pipe保持時もclose後にdirect childをbounded `wait()` し、最後にreapを確認する。[integration.py:1802](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1802)、[integration.py:1829](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1829) |

`poll()` は単なるキャッシュ参照ではありません。現環境のCPythonでは [`_internal_poll()`](/usr/lib/python3.10/subprocess.py:1879) が `waitpid(pid, WNOHANG)` を呼び、対象PIDを観測するとexit statusを確定してreapします。[subprocess.py:1896](/usr/lib/python3.10/subprocess.py:1896)

重要なraceは、TERM後にdirect childだけがexitし、descendantがPIPEを保持して最初のbounded `communicate()` がtimeoutする場合です。この場合、KILL直前の再pollがdirect childをreapしてKILLを抑止するため、旧stale PGID経路は再発しません。

primary exceptionについても閉じています。

- primary exceptionあり: [`primary_error`](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1781) の有無にかかわらずsignal条件はlive `poll()`だけです。cleanup exceptionはprimaryを置換せず、元の例外が維持されます。[integration.py:1827](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-t145/orchestrator/tests/test_dev_waves_integration.py:1827)
- primary exceptionなし: 正常終了なら`communicate()`がwait/reap済みなのでsignalしません。ceiling timeoutなら従来のTERM/KILL/reap後、必ず`INFRA_TIMEOUT`になります。

新所見はありません。したがって、新たなreal/refuted、must-fix/nit、DW-G05成果物影響の起票もありません。output size limit、専用FD、producer/parser追加control、nested session一般containment、M7は裁定済みbacklog／`NOT_RUN(design-invalid)`のままです。

## 総括

- 判定: **GO**
- stale PGID root cause: **closed**
- 従来のtimeout cleanup経路: **closed、回帰なし**
- mutationへ進めるか: **進めてよい**
- pytest・mutation: **本監査では未実行**