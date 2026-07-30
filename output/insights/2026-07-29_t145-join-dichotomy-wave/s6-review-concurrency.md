差分前提は、実装面について確認できました。

- tracked diff は `orchestrator/tests/test_dev_waves_integration.py` のみ
- `291 insertions / 24 deletions`
- production 差分 0 byte、staged diff なし
- 現在の diff は `s5-author.patch` と byte-for-byte 一致
- ただし `git status` は wave artifact ディレクトリを untracked として示すため、worktree 全体は clean ではない
- 指示どおり pytest・probe・mutation は実行しておらず、静的レビュー結果だけを示す

## 所見

### 1. `[blocker][real]` outcome 非観測経路が無期限に停止し、cleanup と patch restore まで到達しない

`_ServeSelectProxy.wait_for()` は timeout なしです。主経路と cleanup の双方がこれに依存しています。

- `orchestrator/tests/test_dev_waves_integration.py:1261`
- `orchestrator/tests/test_dev_waves_integration.py:1429`
- `orchestrator/tests/test_dev_waves_integration.py:1463`

具体的 interleaving:

1. target thread が `PARKED` を通知
2. main が `shutdown()`、`release()` を実行
3. proxy は `([], [], [])` を返す
4. serve thread が `daemon.py:1615` から loop predicate `daemon.py:1613` へ戻る途中で永久停止する変異
5. `SERVE_RETURNED` / `SERVE_RAISED` は一度も記録されない
6. main は `wait_for()` から戻らず、`thread.join()`、`patcher.stop()`、temporary directory cleanup のすべてが未到達

外部 mutation subprocess ceiling は変異プロセスを殺せても、このテスト自身の受入実行を containment しません。`tools/run_tests.py:785` も `subprocess.call()` に ceiling を設けていません。

また、outcome 観測済みでも、それは thread termination の観測ではありません。`note_serve_returned()` は thread が終了する前に通知するため、通知直後に target が停止すれば `thread.join()` は永久待機します。`orchestrator/tests/test_dev_waves_integration.py:1473` の「only reaps」というコメントは scheduler fairness を仮定した説明であり、証明ではありません。

### 2. `[blocker][real]` 実 thread・long-path 経路が一度も実走していない

capability skip は proxy 構築・patch・thread start より前です。

- `orchestrator/tests/test_dev_waves_integration.py:1360`
- `s5-author.md:16`
- `s5-author.md:18`
- `s5-author.md:45`

したがって今回の環境では次がすべて未実走です。

- `daemon_mod.select` の実 patch
- `Supervisor.serve_forever()` と proxy の結合
- listener / relay shape の取得
- exchange 後 park
- shutdown / release / outcome
- cleanup と patch restore

単体 proxy probe は tracked test ではなく、実 `serve_forever()`、AF_UNIX long-path exchange、例外回収、finally を結合していません。`s4-adjudication-plan-v2.md:39-40` 自身が capability skip を `NOT_RUN` とし、wave を完了しないと規定しています。

なお、author はこれを代替証拠として wave 完了扱いしておらず、残リスクを明記しています。その主張自体は `[refuted]` です。しかし現時点の受入証拠不足は real blocker です。

### 3. `[must-fix][real]` cleanup が primary exception を変更し、cleanup 中の BaseException を別種の失敗へ変換する

- `orchestrator/tests/test_dev_waves_integration.py:1446`
- `orchestrator/tests/test_dev_waves_integration.py:1467`
- `orchestrator/tests/test_dev_waves_integration.py:1492`

M2 の具体例では、serve thread の `_ServeLoopIgnoredShutdown` を main が `:1434` で再送出した後、finally が同じ serve failure を cleanup error として再登録し、同一例外の `args` を変更します。primary と cleanup の帰属が混ざります。

さらに、primary error がない状態で `shutdown()`、`release()`、`join()`、`patcher.stop()` 中に `KeyboardInterrupt` / `SystemExit` が来ると、`except BaseException` が捕捉し、最終的に `AssertionError` へ変換します。`primary_error.args = ...` 自体が失敗すれば、元の primary error を上書きします。

成果物影響: mutation/受入記録の第一失敗型・診断文字列・帰属が変わり、どの退行を検出したかを正しく台帳化できません。

### 4. `[must-fix][real]` 「thread 回収後だけ patch restore」は全出口で保証されない

- `patcher.start()` が `try` の外: `orchestrator/tests/test_dev_waves_integration.py:1384`
- `thread.start()` と flag 更新が分離: `orchestrator/tests/test_dev_waves_integration.py:1392`
- join 失敗後も restore: `orchestrator/tests/test_dev_waves_integration.py:1475`
- restore: `orchestrator/tests/test_dev_waves_integration.py:1481`

具体的には次の穴があります。

1. `patcher.start()` 成功直後、`try` 進入前に BaseException → patch 未復元
2. `thread.start()` 成功直後、`thread_started=True` 前に BaseException → live thread を回収せず patch 復元
3. `thread.join()` が割込み・例外 → live の可能性を確認せず patch 復元

成果物影響: 同じ pytest worker の後続 node が live serve thread、socket、または汚染された `daemon_mod.select` を観測し、受入結果の独立性と第一失敗帰属を失います。

### 5. `[nit][real]` `daemon_mod.select` patch は module-local ではなく process-global

`mock.patch.object(daemon_mod, "select", ...)` は同じ module object を見る全 thread / Supervisor / import consumer に波及します。

- `orchestrator/tests/test_dev_waves_integration.py:1382`

別 Supervisor の serve thread は target thread ではないため、現在の proxy は実 `select` へ委譲します。この経路は機能上は透明です。一方、patch 中に以下を実行した consumer は proxy を恒久的に捕捉できます。

```python
from tools.dev_waves.daemon import select as captured_select
```

`patcher.stop()` はその local binding を戻せません。また並行する別 patch があれば、stop がその binding を上書きします。repository 内に現在その consumer は見つからなかったため must-fix の成果物影響までは立証できず、nit とします。

### 6. `[nit][real]` trace は重複を隠し、normal path でも shutdown/release が二重実行される

- deduplication: `orchestrator/tests/test_dev_waves_integration.py:1255`
- main release: `orchestrator/tests/test_dev_waves_integration.py:1428`
- finally release: `orchestrator/tests/test_dev_waves_integration.py:1457`

正常経路でも finally が `shutdown()`、`note_shutdown_set()`、`release()` をもう一度呼びます。`Event.set()` は冪等なので現在の機能上の害はありませんが、`if observation not in self._trace` が重複を消すため、最終 trace は exactly-once を証明しません。順序付き「集合」に近く、呼出回数の証拠ではありません。

### 7. `[nit][real]` relay は object identity ではなく fd 値しか束縛していない

- `orchestrator/tests/test_dev_waves_integration.py:1299`
- `orchestrator/tests/test_dev_waves_integration.py:1301`

listener は `is` で束縛していますが、relay は `SignalRelay` object ではなく `fileno()` の整数を保存し、`!=` で比較しています。現在の production call shape が整数 fd を渡すため比較方法自体は正しいものの、「relay identity」を証明するものではありません。relay が差し替わり同じ fd が再利用された場合は通過します。

### 8. `[nit][real]` xdist meta-test が証明するのは marker の構文対応だけ

- 語彙検出: `orchestrator/tests/test_dev_waves_isolation_contract.py:35`
- marker 集合比較: `orchestrator/tests/test_dev_waves_isolation_contract.py:102`
- scheduler override は警告だけ: `tools/run_tests.py:767`

証明すること:

- `daemon_mod` / `threading.Thread` 等へ構文的に到達する node に、単一の `dev-waves-runtime` marker がある
- module-wide marker や real-repo group との重複がない

証明しないこと:

- thread / socket / patch が node 終了時に回収済み
- same-worker background thread や import consumer への非波及
- retained proxy が存在しない
- cleanup が primary error を保存する
- `--dist loadgroup` が実際に使われたこと

`run_tests.py` は別 `--dist` を拒否せず警告だけなので、marker/meta-test 成功を実行時隔離の証明にはできません。

### 9. `[nit][real]` 291行の test-only harness は private production contract の shadow になっている

この harness は次を複製・固定しています。

- `Supervisor._shutdown`
- readers の順序と長さ
- listener object / relay fd
- positional timeout `0.25`
- serve loop の反復順
- post-exchange select の挙動

proxy は post-exchange の実 `select.select()` を呼ばず、自身で park して空 ready set を返します。このため完全な production shadow ではなく、実 bind・exchange・dispatch は引き続き production を通ります。しかし合法的な selector API、reader ordering、timeout policy の変更も harness failure となるため、強い white-box coupling です。現時点の contract pin としては意図的ですが、drift 時には production 正誤より harness 更新が先に問題になります。

## Refuted

- `[nit][refuted]` target thread identity の race: thread object は start 前に束縛され、target はその同一 `Thread` object です。
- `[nit][refuted]` listener publication の data race: listener を設定後、同じ Condition lock を通じて `LISTENER_BOUND` を通知し、main はその待機後に読みます。
- `[nit][refuted]` Condition lost wakeup: predicate と trace は同じ Condition lock 内で検査・更新されるため、notify が wait より先でも predicate が拾います。
- `[nit][refuted]` Event lost wakeup: `exchange_completed`、`parked`、`released` は level-triggered Event で、set が wait より先でも失われません。
- `[nit][refuted]` lock inversion: proxy は Condition を保持したまま Supervisor lock を取得せず、`released.wait()` 前にも Condition を解放しています。
- `[nit][refuted]` list lookup の並行破損: trace の全 read/write は Condition 下で、要素数も最大8種に固定されています。
- `[nit][refuted]` outcome が正常に発行される範囲の exchange前・exchange後・park後・serve例外・main assertion失敗: finally の shutdown→release→outcome→join→restore の順で回収できます。ただし blocker 1、must-fix 4 の出口は除きます。

## 総括

**NO-GO** です。

fix必須項:

- outcome 非観測／観測後未終了を test process 外の ceiling で containmentし、timeout を green にしない
- cleanup で primary exception の `args` を変更せず、`KeyboardInterrupt` / `SystemExit` を cleanup failure に変換しない
- patcher start から thread reap までを一つの cleanup 所有範囲に入れ、live thread のまま restore しない

変異前に必要な証拠:

- capability のある環境で long-path node が skip せず実走し、実 `serve_forever()`、park、shutdown、reap、restore を通ること
- focused node と isolation meta-test の実結果
- failure 注入後も target thread 消滅、socket 消滅、`daemon_mod.select is real_select_module` 復元を独立に確認する control
- hang 変異の subprocess ceiling、`INFRA_TIMEOUT`/`NOT_RUN` 非green化、親側復元・単一走行 guard の実在確認

現段階の proxy 単体 probe と `2 passed / 1 skipped` は、これらの代替証拠にはなりません。