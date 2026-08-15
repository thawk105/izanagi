### 所見 1
- severity: must-fix
- 攻撃シナリオ: caller が公開済み `issue_holdout_observation_admission()` に既知の rr80／rr20 を含む最小 dict を渡して正規 token を取得し、その token で `run_once(..., "-ycsb_rratio=80")` を呼ぶ。cell claim も attempt ticket も不要で subprocess まで到達する。
- 根拠: `orchestrator/holdout_observation.py:15-24` が issuer を公開し、同 `:191-217` は caller 提供 mapping の集合一致だけで token を発行する。`orchestrator/calibrator/runner.py:417-425` はその token を正規 admission として受理する。実際に `orchestrator/tests/test_holdout_observation.py:23-50` が caller 構築 dict から正規 token を取得している。
- 成果物影響: 実測済み holdout に対応する cell claim、admission row、attempt row がすべて 0 件のままになり、台帳の受理集合が実測集合より小さくなる。
- 提案: issuer を公開 API から除去し、durable ticket 消費後の内部経路だけが attempt 束縛済み token を発行できるようにする。

### 所見 2
- severity: must-fix
- 攻撃シナリオ: 1 回目の iteration では `-ycsb_rratio=50`、2 回目では `-ycsb_rratio=80` を返す stateful `Sequence` を `run_once()` の `gflags` に渡す。gate は最初の値を非保護と判定するが、実行 argv は二度目の rr80 になり、token 無しで spawn される。別 thread が同じ list を gate 後に書き換えても同じ結果になる。
- 根拠: `orchestrator/holdout_observation.py:161-173` が入力を一度走査し、`orchestrator/calibrator/runner.py:417-420` がその可変オブジェクトを検査する。その後、同 `:425` から `:371-381` が同じオブジェクトを再走査して実行 argv を作る。
- 成果物影響: attempt ledger に行が無い rr80／rr20 実測が成立し、台帳の実測回数と実際の subprocess 回数が不一致になる。
- 提案: `run_once()` 冒頭で `gflags` を exact-str の tuple に一度だけ固定し、その同一 snapshot を分類と `_build_cmd()` の両方へ渡す。

### 所見 3
- severity: must-fix
- 攻撃シナリオ: public `run_campaign(..., mode="pilot", now_fn=malicious)` を呼び、`malicious` 内で rr80 の ccbench を spawn してから例外を投げる。pilot wrapper は `now_fn` を拒否せず、core は reservation より前に呼ぶため、cell claim すら残らない。
- 根拠: `orchestrator/campaign/s8b_floor_campaign.py:4162-4169` の pilot 共通拒否は `measure_fn`、`probe_fn`、`perf_preflight_fn` の三つだけで、完全な seam 拒否は同 `:4171-4191` の official 分岐にしかない。caller の `now_fn` は同 `:4280` で実行され、holdout reservation は同 `:4308-4320` まで行われない。新設 pilot テストも `orchestrator/tests/test_s8b_floor_campaign.py:3076-3090` の三 seam しか検査しない。
- 成果物影響: claim、admission、attempt の全台帳が空のまま holdout 値を取得でき、未記録観測を選択判断へ持ち込める。
- 提案: pilot でも public entrypoint の全 caller callable seam を拒否する。少なくとも `now_fn`、`prepare_fn`、`build_fn`、`sleep_fn`、provenance／receipt seam を production wrapper から外す。

### 所見 4
- severity: must-fix
- 攻撃シナリオ: `_run_campaign_core()` を直接 import し、`_holdout_reserve_fn`、`_holdout_finalize_fn`、`_holdout_assert_fn`、`_attempt_consume_fn` を no-op にする。外部 `measure_fn` で ccbench を直接実行して `ScalePoint` を返せば、claim／ticket 無しで通常の journal と `result.json` まで生成できる。
- 根拠: `orchestrator/campaign/s8b_floor_campaign.py:4213-4215` が四つの gate seam を caller に公開し、同 `:4308-4313` と `:4659-4666` が実装本体より注入値を優先する。同 `:4726-4733` は no-op assert／consume を wrapper へ渡し、同 `:3267-3274` は外部 callback をそのまま実行する。テスト自身も `orchestrator/tests/test_s8b_floor_campaign.py:380-405` でこの完全迂回を実装している。
- 成果物影響: ledger row が 0 件でも session 値を持つ `result.json`／`result.md` が成立し、台帳参照の無い floor レポートが生成される。
- 提案: production module の core から四つの admission 注入引数を削除し、常に実実装へ固定する。テスト用置換は production callable と分離した専用 harness に置く。

### 所見 5
- severity: must-fix
- 攻撃シナリオ: 一つの正規 ticket を `consume_attempt_ticket()` で消費して observation token を受け取り、その token を使って `measure_point(..., reps=5)` を二回呼ぶ。二度目の ticket 消費は不要で、同じ token は全 `run_once()` に繰り返し受理される。
- 根拠: `orchestrator/campaign/s8b_holdout_admission.py:796-829` は durable marker 作成後に再利用可能な observation token を返す。`orchestrator/holdout_observation.py:219-231` の検査は identity を見るだけで使用回数を減らさない。`orchestrator/calibrator/runner.py:530-557` は同一 token を各 rep へ転送する。`orchestrator/tests/test_s8b_holdout_admission.py:266-273` は二度目の ticket 消費だけを拒否し、返却 token の再利用を検査しない。
- 成果物影響: attempt ledger の 1 行に対して任意個の測定 session／rep を取得でき、best-of-N の母数と台帳の `attempt_count` が乖離する。
- 提案: raw observation token を返さず、attempt ID と固定 reps 上限へ束縛した一回限りの session executor を返す。許可回数を超えた `run_once()` は拒否する。

### 所見 6
- severity: must-fix
- 攻撃シナリオ: `backoff_profile.profile_point(2, {"ycsb_zipf_skew":"<<DEFANG>>","ycsb_rratio":"80","ycsb_rmw":"<<DEFANG>>"})` を直接 import 呼出しする。freeze と同じ records、threads、rr80 shape で build した binary が gateway を通らず三回実測される。
- 根拠: `orchestrator/campaign/backoff_profile.py:46-58` が records／threads と workload shape を定義し、同 `:137-160` の公開関数は任意 workload を `_profile_run()` へ渡す。同 `:104-109` は `subprocess.run()` で binary を直接実行する。allowlist テストは `orchestrator/tests/test_ccbench_spawn_sites.py:39-40,167-173` で CLI の `POINTS` だけを確認し、直接 import の引数を拘束しない。
- 成果物影響: admission／attempt 台帳に存在しない保護比率の profile 値が得られ、台帳の観測集合が実際の観測集合を表さなくなる。
- 提案: `_profile_run()` 自体を gateway 経由にするか、`profile_point()` で保護 signature を runtime 拒否し、caller workload を受け取れない閉じた API にする。

### 所見 7
- severity: should
- 攻撃シナリオ: `orchestrator/campaign/nested/driver.py` に直接 spawn を追加する、または既存 top-level file に `def launch(bench_path): subprocess.run([bench_path, "-ycsb_rratio=80"])` を追加する。新しい meta-test は候補を一件も増やさず緑のままになる。
- 根拠: `orchestrator/tests/test_ccbench_spawn_sites.py:82-85` は top-level の `*.py` しか列挙しない。同 `:62-76` は名前が literal `binary` の値だけを追跡し、同 `:124-136` は限定された `subprocess` 呼出し形しか候補にしない。それでも同 `:144-151` は得られた不完全な候補集合を閉集合として扱う。
- 成果物影響: 将来追加された未 admission spawn が検査を通過し、台帳外の holdout 実測を受理集合へ混入できる。
- 提案: `rglob("*.py")` で再帰走査し、変数名に依存せず全 process-launch API を先に列挙してから、各 site を gateway／allowlist へ分類する。

### 所見 8
- severity: must-fix
- 攻撃シナリオ: production core の real reserve／finalize／assert／consume 結線を壊しても、campaign の成功系テストは四つすべてを no-op fixture へ差し替えるため通る。admission 単体テストも関数を直接呼ぶだけなので、core と実装の間の配線切断を検出しない。
- 根拠: `orchestrator/tests/test_s8b_floor_campaign.py:380-405` が四 gate を no-op 化し、同 `:409-425` の共通 helper が既存 campaign テストへ常時注入する。同 `:6024-6080` の「defaults delegate」テストさえこの helper を使い、call counter に holdout admission 関数が無い。一方 `orchestrator/tests/test_s8b_holdout_admission.py:117-130,170-175,266-269` は各関数の直接試験に留まる。
- 成果物影響: 配線回帰により session を含む result と空の admission／attempt ledger が生成されても、land 前テストの受理集合に残る。
- 提案: real Git fixture と実 admission 関数を使う end-to-end test を一件追加し、subprocess spy 到達前に claim、admission row、attempt marker が durable に存在することを確認する。

## 総括

NO-GO。静的検査のみで、pytest 緑は主張しない。  
`O_EXCL` marker の callback 前作成自体は実装されているが、その権限を迂回・再利用できる。  
特に公開 issuer、pilot の未拒否 seam、直接 import 可能な no-op core seam は、台帳を一行も残さず実測へ到達する。  
さらに既存 campaign テストが real admission を全面的に stub 化しており、結線回帰を検出できない。