## 実測の検証

親の連鎖 7 段は、報告された「Pegasus LOGIN・queue 可用・明示 3 shard」という条件では正しい。host 名、queue の待ち数・実行数そのものは再実測していない。

1. 待ち手は LOGIN かつ `dispatch_possible()` が `ENA=ENA` / `STS=ACT` を返した場合だけ `IZANAGI_ACCEPTANCE_SHARDS=3` を launcher 環境へ追加する。`tools/dev_wave_wait.py:821-845`、実際の `Popen` への適用は同 `:848-867`。

2. launcher は `tested_main:tools/run_tests.py` を読み、`tested_tip` との等値を検査する。実行 source は main 側である。`tools/acceptance_launcher.py:435-441`。

3. ただし bootstrap は `__file__ = sys.argv[1]` とし、その引数は worktree の canonical path である。`tools/acceptance_launcher.py:51-61`、`:214-226`。したがって blob 内の `_REPO` は `__file__` から wave worktree を導く。`tools/run_tests.py:55-58`。

4. 明示 shard 値 3 は LOGIN acceptance で `shard_mode=True` となる。`tools/run_tests.py:282-297`。明示 shard の場合は local admission を飛ばし、LOGIN 分岐が dispatch を選ぶ。`tools/run_tests.py:2496-2503`、`:2620-2629`。

5. `_default_dispatch` は `repo_root=Path(_REPO)`、すなわち wave worktree を渡す。`tools/run_tests.py:1307-1324`。shard ごとの呼び出しにも同じ環境と dispatcher が渡る。`tools/run_tests.py:2302-2352`。

6. dispatcher はその root を request に保存する。`tools/pegasus/dispatch_compute.py:2854-2864`。compute 側は exact request から `repo_root` を復元する。`tools/pegasus/dispatch_compute.py:945-978`。

7. `tests` task の child path は `tools/run_tests.py` であり、compute 子 argv は `[python, repo_root/tools/run_tests.py, *argv]` となる。`tools/pegasus/dispatch_compute.py:112-130`、`:995-1022`。従って、この条件でテスト本体を駆動する二段目の runner は tested tip の worktree file である。main blob が直接動かすのは dispatch 前の外側プロセスまで、という親の結論は正しい。

dispatch しない、または主張が成立しない条件もある。

- queue 可用を確認できず待ち手が明示 shard を注入しない場合、既定 K=2 でも LOGIN admission が先に走る。local budget が得られれば bounded local を選ぶ。`tools/run_tests.py:2496-2560`。この経路も `systemd-run ... <worktree>/tools/run_tests.py` と pathname 再実行するため、dispatch ではないが同じ tip-runner 問題を持つ。`tools/run_tests.py:1895-1906`。
- queue も local capacity も無ければ rc=16 で止まり、pytest 自体を駆動しない。`tools/run_tests.py:2515-2530`。
- `OTHER`、既に `PEGASUS_COMPUTE`、bounded scope 内、または dispatch-exempt の非受入形では直接 pytest へ進み得る。`tools/run_tests.py:2620-2688`。最初の blob processがそのまま進む経路では main blob が駆動主体である。
- preflight、dispatcher setup、queue wait、compute marker などが先に失敗した場合も、pytest は起動していないので「tip runner が pytest を駆動した」とは言えない。

## 推奨

**第 4 案: 実行器を触らない準備 wave を先に着地させる三段ブリッジ**を推奨する。B には反対する。

親の「dispatch 束縛には必ず `run_tests.py` の編集が要る」という前提には代替がある。launcher は `tested_main` と main runner bytes を既に持ち、runner の `_dispatch_environment()` は環境をコピーして dispatcher へ渡す。`tools/acceptance_launcher.py:435-440`、`tools/run_tests.py:1290-1304`。dispatcher 側で必要なのは閉じた allowlist と request transport の追加である。`tools/pegasus/dispatch_compute.py:112-130`、`:2796-2800`。

以下は未実装の設計提案である。

1. **準備 wave P:** `tools/run_tests.py` は byte 不変のままにする。main launcher から `{tested_main, runner SHA-256}` を閉じた内部 transport で渡し、compute 子が exact `tested_main:tools/run_tests.py` blob を読み、hash 検証後に `compile/exec` する機構を入れる。外側の dispatcher import と compute job の dispatcher pathname も main blob へ束縛する必要がある。現在は前者が worktree import、後者が `DISPATCHER=<worktree path>` だからである。`tools/run_tests.py:1318`、`tools/pegasus/dispatch_compute.py:640-687`。この段では launcher/land の runner 等値を残す。

2. **撤去 wave Q:** P が main へ入った後、launcher と land の runner 等値だけを外す。Q 自身は `run_tests.py` を触らないので、P の main launcherが行う旧等値検査にも通る。受領証と通常 land をそのまま使える。

3. **実行器 wave R:** この時点で初めて `run_tests.py` を変更し、[T-1932] の既定 shard 変更を行う。同時に bounded scope 再入も main blob 実行へ変える。R の受入は Q/P の main-bound launcher・dispatcherが判定する。

P の activation 前は旧等値が守り、Q 後は新束縛が守る。等値を外したのに束縛が無い時点が存在せず、一度きりの receipt bypass も要らない。P/Q 間で queue が使えない場合は、main-bound bounded 経路が完成するまで authoritative acceptance を dispatch-only として fail-closed にするのが安全である。

なお、この案が束縛するのは runner と dispatcher の実行 bytes である。pytest plugin、`conftest.py`、import 閉包まで main に固定する主張はしない。

## 一度きり land 認可の実現性

**現行機構だけでは B は着地不能である。**

- main launcherは runner 不等値を suite 起動前に拒否する。`tools/acceptance_launcher.py:435-441`。
- land も main/tip runner object ID の等値を要求する。`tools/dev_wave_land.py:1065-1088`。
- `--acceptance-receipt` は必須で、receipt 検証は merge・`already-landed` より前に無条件で走る。`tools/dev_wave_land.py:5034-5042`、`:5546-5559`。
- D388 は receipt 欠落時の flag・環境変数・互換 bypass を明示的に禁止している。`docs/decisions.md:16470-16494`。

理論上は、pre-land 済みの trusted consumer が、repo 外の create-only capabilityを検証する形なら実現できる。capabilityには exact `tested_main`、exact `tested_tip`、監査 closure、main-bound runner/dispatcher hash、log hash、期限、user nonce を束縛し、land lock 内で一度だけ消費する必要がある。しかし、その consumer は現在存在しない。B wave 自身へ追加すると、その機構を着地させるために同じ例外が必要になる。

人間が `git merge --ff-only` や `update-ref` を直接実行することは技術的には可能だが、receipt、provenance、collision、fold、postcondition をまとめて迂回するため、B がいう「一度きり land 認可」の安全な実現ではない。

## 規律との整合

規律 2 は最優先であり、「正しさを攻撃する最適化圧力」を前提に verifier の弱化を禁じる。`CLAUDE.md:67-71`。この比較では、**適切に一度限り化された B より A の方が悪い**。

A は、等値撤去の land から束縛 wave の land まで、runner を変更する全 wave に自己判定を機械的に許す。受入 lease は他 wave の投入を止めないため、窓の母集団は「予定した次の 1 wave」に限定されない。`docs/decisions.md:27307-27317`。これは D838 が名指しした「実行器を書き換えて赤を child-green にする」経路そのものである。`docs/decisions.md:31681-31697`。

B は correctness gate 自体を main-bound のまま保てる一方、D388 の land authority に例外を作る。ただし exact tip、明示 user authorization、一回消費、通常 gate と同等の証拠が揃う場合に限れば、影響は一つの transition に閉じる。

D387 の事故モデルは、意図的な同一 user 偽造を防げないことを認めているだけで、虚偽 receipt や無印の手動 FF を推奨してはいない。防御対象は「直接走を権威ある受入として扱う事故」である。`docs/decisions.md:16451-16468`。したがって、機構の無い現状で B を手作業に読み替えるのも不適切である。

第 4 案は通常 receipt と通常 land を全段で維持するため、A の correctness window と B の authority exception の双方を避ける。

## 総括

反対: B  
親の dispatch 連鎖は、実測された LOGIN・明示 3 shard 条件では正しい。  
ただし B を着地させる一度きりの land authority は現行機構に存在しない。  
runner 不変の準備 waveから始める三段ブリッジなら、通常 receiptを外さずデッドロックを解ける。  
静的検査のみであり、pytest・queue・host 状態は再実測していない。