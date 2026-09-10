### 所見 1: P は着地可能だが、初回だけ binding 不在になる

**根拠 (file:line)**

- P の受入で実行される launcher は tip の新実装ではなく tested main の旧実装である。`tools/dev_wave_wait.py:2565-2577`
- 旧 launcher は runner の main/tip 等値を確認してから main blob を実行する。P は runner 不変なのでここは通る。`tools/acceptance_launcher.py:435-441`
- land の三つの bytes 束縛先は以下であり、tip launcher や dispatcher の等値要求はない。
  - launcher: tested main blob。`tools/dev_wave_land.py:1021-1053`
  - waiter: tested tip blob。`tools/dev_wave_land.py:1054-1079`
  - runner: tested main/tip の blob 等値と main 内容 SHA-256。`tools/dev_wave_land.py:1065-1088`
- 一方、main runner は canonical `__file__` から wave root を導き、P の新しい tip dispatcher を import する。`tools/run_tests.py:55-58`、`tools/run_tests.py:1307-1324`
- したがって P の初回だけ「旧 launcher なので新 binding 環境変数なし、新 dispatcher は稼働」という形になる。
- さらに、land 待ち中の旧 v1/v2 request を live dispatcher が読む互換契約がある。`tools/pegasus/dispatch_compute.py:160-174`、`tools/pegasus/dispatch_compute.py:719-735`、`tools/pegasus/dispatch_compute.py:951-973`

**再現できる形**

1. runner を変更せず launcher と dispatcher だけ変更する。
2. 新 dispatcher で `tests` request に binding を無条件必須化する。
3. P の受入を走らせる。
4. 旧 launcher が binding を渡さないため `_job_run` が bootstrap failure、rc=16 になる。

P は「binding 不在なら常に pathname fallback」なら着地できる。しかし、その fallback を P 後も残すと、将来 runner が環境伝播を落とした際にも silent fallback する。新 request schema、acceptance shard 形、旧 main dispatcher digestなどを使った一回限りの transition 判定が必要である。

**成果物影響**

無条件必須なら P の受入受領証は生成されず land の受理集合は増えない。恒久 fallback なら受領証の `runner_executed_sha256` は main のままでも実際の内側 runner が tip になり得て、worklog の `child-green` 記録では区別できない。

**重み (must-fix | nit | scope 外)**

must-fix

### 所見 2: P の執行者が tip dispatcher のままで、runner と dispatcher の同時変更を防げない

**根拠 (file:line)**

- 外側 runner は wave root を `sys.path` へ入れ、そこから dispatcher を import する。`tools/run_tests.py:55-58`、`tools/run_tests.py:1318-1324`
- job script も wave root の dispatcher pathname を実行する。`tools/pegasus/dispatch_compute.py:623-645`、`tools/pegasus/dispatch_compute.py:679-687`
- runner pathname から blob bootstrap へ切り替える分岐そのものも `_job_run`、すなわち tip dispatcher 内に置かれる。現行位置は `tools/pegasus/dispatch_compute.py:928-1022`
- dispatcher の親側検証は result の job ID、stage、request SHA、child rc を見るが、実行 runner SHA は検証しない。`tools/pegasus/dispatch_compute.py:3447-3459`
- 上位 receipt の `runner_executed_sha256` は launcher が実行した外側 main runner の SHA である。`tools/acceptance_launcher.py:436-458`
- land の receipt 検証対象三本にも dispatcher は含まれない。`tools/dev_wave_land.py:1047-1088`

**再現できる形**

Q 後の wave で `tools/run_tests.py` と `tools/pegasus/dispatch_compute.py` を同時変更する。tip dispatcher が binding 検査を削除して tip runner を pathname 起動し、通常の result を返せば、上位 receipt は外側 main runner の SHA を記録したまま green になり得る。

P の main launcher に dispatcher の main/tip 等値検査を追加する、または dispatcher 自体を main blob から起動して inner runner SHA を検証可能な成果物へ束縛する必要がある。P は旧 launcher で受入されるので、将来用 dispatcher 等値 gate を P で導入すること自体は可能である。

**成果物影響**

放置すると受入受領証は main runner を記録したまま、land の受理集合に runner+dispatcher 同時変更 wave が入る。worklog の main-bound、child-greenという記録値は実際の内側実行 bytes と食い違う。

**重み (must-fix | nit | scope 外)**

must-fix

### 所見 3: Q 後から R 前まで bounded local 経路が無防備である

**根拠 (file:line)**

- waiter が `IZANAGI_ACCEPTANCE_SHARDS=3` を加えるのは LOGIN かつ queue が `ENA=ENA`、`STS=ACT` の場合だけである。`tools/dev_wave_wait.py:821-845`
- 明示 shard でない場合、LOGIN admission は local budget があれば bounded local を選ぶ。`tools/run_tests.py:2496-2560`
- bounded 子は `Path(__file__).resolve()`、すなわち wave 側 `tools/run_tests.py` を pathname で再実行する。`tools/run_tests.py:1895-1906`
- P の定義は compute 子の binding だけなので、この経路を閉じない。
- binding の transport 自体も runner の単純な環境コピーに依存する。`tools/run_tests.py:1290-1304`

**再現できる形**

1. P、Q を land する。
2. R より先に別 wave が runner を変更する。
3. queue 不可用、LOGIN local capacity 有りで受入する。
4. 外側は main runnerでも、bounded 子は変更済み tip runnerを pathname 実行する。

queue 経路だけなら runner-only の介在 wave 自身は prior main runner によって判定される。ただし、その wave が `_dispatch_environment` を壊して land すると、次の R では binding が dispatcherへ届かない。所見1の恒久 fallback があれば、その時点で tip runnerへ戻る。

P の新 launcher が authoritative acceptance を常に shard dispatch に固定し、queue 不可時は fail-closed にする必要がある。bounded main-blob 再入は R で回復できる。

**成果物影響**

放置すると受領証の runner SHA は外側 main のまま、bounded 子が tip を実行した waveまで land 可能になる。worklog は同じ `child-green` と記録し、実行経路の差を保持しない。

**重み (must-fix | nit | scope 外)**

must-fix

### 所見 4: `tests` task の非受入 caller には unbound 互換が必要である

**根拠 (file:line)**

静的な production 参照を追った結果、`tests` task の受入以外の入口は以下で尽きる。

- 通常の `tools/run_tests.py` 全般。`_default_dispatch` が `task="tests"` を直接指定する。`tools/run_tests.py:1307-1372`
  - この入口は targeted test、通常全走、force-dispatchにも共用される。`tools/run_tests.py:2620-2637`
  - repo 内の直接 caller には dev-wave check と nproc study がある。`tools/dev_waves/cli.py:193`、`tools/pegasus/run_acceptance_nproc_study.py:596`、同 `:2391`
- mutation harness の dispatch-mode collection。dispatcher CLIを `--task tests` で直接起動する。`tools/mutation_harness.py:1372-1403`、呼び出しは同 `:1406-1436`、`:3075`
- dispatcher CLI は task 省略時も `tests` が既定なので、repo 外からの直接 CLI invocation も公開面に含まれる。`tools/pegasus/dispatch_compute.py:3842-3855`

他 task は別 `_TaskSpec` である。`tools/pegasus/dispatch_compute.py:112-158`

- provenance の production callerは `task="provenance"`。`tools/check_ai_provenance.py:2300-2305`
- mutation は別 taskであり、内部 argv に live runner pathを要求する。`tools/pegasus/dispatch_compute.py:761-794`
- generic は argv を直接実行する。`tools/pegasus/dispatch_compute.py:151-157`

**再現できる形**

binding を `tests` task 全体へ無条件必須化すると、mutation collectionと通常の direct dispatchには launcher由来 binding がないため rc=16 になる。binding fieldは `tests` allowlistだけへ追加し、authoritative acceptance形だけ必須、通常 testsは明示的 unbound modeとして維持する必要がある。環境の親側射影と子側再検査は `tools/pegasus/dispatch_compute.py:2796-2800`、`:976-994` にある。

**成果物影響**

無条件必須化すると非受入 dispatch receipt が infraへ変わり、mutation collection成果物が欠落する。受入 land の集合は直接変わらないが、関連 worklog の mutation/provenance記録が未完了になる。task分岐を閉じれば既存値は不変である。

**重み (must-fix | nit | scope 外)**

must-fix

### 所見 5: bootstrap 自体は shard、log、rc、timeout、二重 compute gateを壊さない

**根拠 (file:line)**

- shard argvは通常の runner argvとして渡される。`tools/acceptance_shards.py:992-997`、`tools/acceptance_shards.py:1012-1022`
- reportは各 shardの外部 session rootへ書かれ、親が読み直して process rcと併合する。`tools/acceptance_shards.py:1048-1058`、`:1368-1395`
- dispatcher子の stdout/stderr は scheduler logへ継承され、親が result、両 log、accounting、compute markerを収集する。`tools/pegasus/dispatch_compute.py:1015-1022`、`:3346-3384`
- child rcは resultへ保存され、親がそのまま返す。`tools/pegasus/dispatch_compute.py:1030-1044`、`:3447-3503`
- shard deadlineは dispatchへ渡され、全 scheduler commandとsleepを同じ deadlineで制限する。`tools/acceptance_shards.py:1000-1019`、`tools/pegasus/dispatch_compute.py:2775-2794`
- hostname gateは job scriptと `_job_run` の二重である。`tools/pegasus/dispatch_compute.py:656-660`、`:995-997`

**再現できる形**

`tests` 分岐だけを概ね次の形にすれば既存契約を保てる。

```text
main blobを読む
SHA-256を照合
python -I -c bootstrap canonical-runner-path args...
stdinへblob bytes
returncodeを既存child_rcへ入れる
```

`subprocess.call(..., stdin=DEVNULL)` から `subprocess.run(..., input=source)` へ変える際、cwd、env、stdout/stderr継承、shell=False、argv順を維持する必要がある。ここには静的に確認できる破壊は見つからなかった。

**成果物影響**

正しく分岐すれば shard report、dispatcher log、result rc、timeout分類、受入受領証、land受理集合、worklog記録値はいずれも不変である。

**重み (must-fix | nit | scope 外)**

nit

### 所見 6: Git blobとstdin方式なら tree fingerprintとは衝突しない

**根拠 (file:line)**

- shard session rootは repo 内を明示的に拒否する。`tools/acceptance_shards.py:177-199`
- session、report、Junit、dispatcher logはその外部 rootへ作られる。`tools/acceptance_shards.py:970-989`、`:1005-1022`
- split dispatch artifact rootも repo 外を必須とする。`tools/pegasus/dispatch_compute.py:2716-2733`
- repo 内 control rootは `output/pegasus-dispatch/` であり、Git ignore対象である。`tools/acceptance_shards.py:1198-1200`、`.gitignore:26`
- waiter は `git status --untracked-files=all` と binary diffを fingerprintへ含め、走行後の完全一致を要求する。`tools/dev_wave_wait.py:357-360`、`:2090-2132`、`:3821-3842`
- land は receiptの `status_bytes == 0`、`diff_bytes == 0` を要求する。`tools/dev_wave_land.py:805-817`

**再現できる形**

`git cat-file` で読み、検査済み bytesをstdinへ渡す案では新しい作業ツリー fileは不要である。逆に、canonical runner近傍など repo 内の非ignore pathへ source fileを実体化すれば postrun-cleanまたは fingerprintで拒否される。

**成果物影響**

Git/stdin方式なら受領証、land受理集合、worklog値は不変。repo内実体化を採ると受領証が発行されず、land不能、worklogは受入失敗になる。

**重み (must-fix | nit | scope 外)**

nit

### 所見 7: Q は P へ畳めるため、三段は論理上最小ではない

**根拠 (file:line)**

- P は runnerを変更しないので、旧 main launcherの runner等値を通る。`tools/acceptance_launcher.py:435-441`
- P の landも旧 main land実装で検証され、runnerが不変なら現行等値を通る。`tools/dev_wave_land.py:1065-1088`
- launcherは land後に初めてmain版として使われる。`tools/dev_wave_wait.py:2565-2577`

**再現できる形**

二段案は次である。

1. P': launcher、dispatcher、landを同一waveで変更する。runnerは不変。compute binding、dispatcher保護、acceptance dispatch-only化を導入し、将来用のrunner等値だけ同時に撤去する。
2. R: runnerを初めて変更する。

P' 自身は旧等値で受入・landされる。land後は新bindingと等値撤去が同時に有効になるため、Qという独立transitionは論理上不要である。

三段にする利点は、Qが新binding経路をrunner変更前にlive確認するcanaryになる点である。したがって三段は安全性の必須依存ではなく、検証上の選択である。

**成果物影響**

二段案ではQ専用の受領証とworklog entryが消える。landの受理集合が広がる時点はP' land後で同じだが、Rの `tested_main` はQではなくP'を指す。

**重み (must-fix | nit | scope 外)**

nit

## 総括

P/Q/R に致命的欠陥あり  
Pは条件付きで着地できるが、初回fallbackを恒久化するとbinding欠落時にtip実行へ戻る。  
Q後はtip dispatcher同時変更とbounded local経路がmain束縛を破り、R前の別runner waveで顕在化する。  
shard成果物、log、rc、timeout、fingerprint自体には静的な破壊を見つけなかった。  
dispatcher保護とdispatch-only化をPへ足し、QをPへ畳む二段案がより小さい。