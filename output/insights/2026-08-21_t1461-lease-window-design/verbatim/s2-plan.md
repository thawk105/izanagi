## 1. brief の file:line 引用の独立検証

- `docs/decisions.md:11172` は D239 の見出しで一致する。目的と「land の権威は変えない」は実際には `docs/decisions.md:11174-11187`、fencing token なしは `docs/decisions.md:11204-11207` にある。`dev_wave_wait.py:4396` の「no fencing token」も一致する。

- `wave_land_window.py:28-29` は TTL 2400 秒、待ち札 TTL 300 秒で一致する。holder digest は `wave_land_window.py:101-105`、land 側の release authority 照合は `tools/dev_wave_land.py:596-610` にある。

- `wave_land_window.py:651-781`、`:147-149`、`:592-648` は概ね一致する。ただし O_EXCL/flock の実体は `wave_land_window.py:300-324`、`:402-435` まで参照すべきである。

- `dev_wave_land.py:2018-2047` と `:_LAND_LOCK_WAIT_SECONDS` の参照は一致する。lock が common git dir 直下であることは `dev_wave_land.py:2140-2147`。ただし「唯一の正しさの砦」は過大で、receipt、provenance、clean-tree 等のゲートも独立に存在する。

- D254 の `dev_wave_land.py:3127-3218`、`_ProvenanceReceipt:270-276` は一致する。ただし lock 外監査の発火条件は厳密には `locked_main != tested_tip and active_plan is None` (`:3137-3140`)。480 秒は `dev_wave_land.py:2240-2257` にある。

- `dev_wave_land.py:79-107` は schema v5 の field 集合だが、現行は「26 field」ではなく 27 field。`acceptance_launcher.py:365-397` も 27 field を生成し、`docs/decisions.md:23559-23564` も「全 27 field」と明記する。

- `tested_tip` の固定と fingerprint 不変は `dev_wave_wait.py:4123-4133`、`:4203-4210` で一致する。値の供給元まで含めるなら launcher argv の `tested_main`/`tested_tip` は `:4163-4175`。

- `acceptance_launcher.py` が tested-tip の runner blob を実行する点は `:173-196`、`:210-233`、`:425-472` で一致する。ただし compute queue 待ちは launcher 内ではなく、後述の `run_tests.py` → `dispatch_compute.py` にある。

- `dev_wave_wait.py:4145-4148` の `timeout=none` は一致する。実際に process wait が無期限なのは `dev_wave_wait.py:550-553`。

- `dev_wave_wait.py:3881` の RETAINED は一致する。しかし現行の land helper は `dev_wave_land.py:3631-3677` で安全な終端時に自動 release する。D469 (`docs/decisions.md:19481-19503`) 後の実装では「親が明示 release」の意味が更新されている。

- `renew()` の「CLI 未配線」は半分だけ一致する。`wave_land_window.py:988-1040` の独立 CLI に renew subcommand はないが、`dev_wave_land.py:3596-3618` が Python import で実際に呼び出している。したがって「Python import でのみ呼べる」は現行 repo 全体については不正確。

- 「release 権限は digest のみ」も歴史的 D239 の説明としては正しいが、現行 land 経路では `wave_land_window.py:850-887` の `expected_main_sha` と `dev_wave_land.py:3664-3668` も使う。D469 の 3 段束縛は `docs/decisions.md:19494-19503`。ただし invocation/fencing の穴は残る。

- README の実測引用は部分的にしか裏付けられない。`output/insights/2026-08-20_t870-congestion-nproc/README.md:130-136` は 15 wave 超、queue-wait-timeout、queue congestion を示すが、brief の「7時間、実テスト8分44秒、残り98%超」という数値は同 README 内で確認できない。

## 2. 成果物の問い (a)〜(d)

### (a) `lease_holder` の検査

- `_verify_acceptance_receipt()` は `tools/dev_wave_land.py:728-732` で `sha256(acceptance_wave)[:12]` を計算し、`:762-767` で次だけを検査する。

  - `acceptance_wave` が期待値と一致。
  - `lease_holder` が文字列。
  - 12 桁 lowercase hex。
  - `lease_holder == sha256(acceptance_wave)[:12]`。
  - `tested_main` と `tested_tip` が caller の値と完全一致。

- receipt verifier は `acceptance.lease` の存在、holder の live ownership、lease payload の `main_sha`、TTL、mtime を読まない (`tools/dev_wave_land.py:716-786`)。したがって lease の claim 時点を変えても、同じ digest を receipt に残す限り、この検査自体は壊れない。

- ただし現行 waiter は receipt publish 前に live lease を再確認している (`tools/dev_wave_wait.py:4297-4383`)。lease を後段 claim に移す案では、この確認を「publish 直前の claim 成功・main_sha一致・TTL残量確認」へ移す必要がある。lease を完全撤去する案では、この確認を削ることになるため、`lease_holder` は ownership 証明ではなく deterministic wave identity と明示しなければ意味論が変わる。

### (b) `renew()` の利用可否

- `renew()` は `wave_land_window.py:784-847` で、lease 不在なら `free`、他 holder/stale/payload 不正なら失敗、自己 holder の場合だけ flock 下で mtime を更新して `held-self` を返す。ticket 作成や新 lease の取得はしない。

- したがって案1では、短時間 claim 後に land へ渡す境界での TTL 延長に利用できる。既存の `dev_wave_land.py:3596-3618` の呼出しを維持すべきで、失敗を acceptance 成功や land rc に変換しないという D595 (`docs/decisions.md:23971-23992`) も維持する。

- 受入テスト前の lease なし区間を renew することはできない。案2では未使用となる。`claim()` を renew 代わりに再利用するのは、D595 と現行 retry 経路 `dev_wave_wait.py:3623-3659` に反するため避ける。

### (c) D128 の 180 秒上限

- `_acquire_land_lock()` は `LOCK_EX|LOCK_NB`、指数 backoff、jitter で最大 180 秒待つ (`tools/dev_wave_land.py:2018-2047`)。FIFO や starvation 防止はない。

- D432 は 180 秒を安全保証ではなく availability cap と明記し、flock は公平性を保証しない (`docs/decisions.md:17940-17989`)。したがって「claim→即land」殺到時の結論は次の通り。

  - land の同時 mutation は flock により直列化され、lease 撤去だけで correctness race にはならない。
  - しかし一部は 180 秒で `lock-busy` になり得る。外側が無制限に再試行すると starvation/livelock 相当の運用状態は残る。
  - 180 秒を単純に延長するのは、D432 の cap、lease TTL、foreground deadline の契約を壊すので推奨しない。
  - `lock-busy` は lock/lease を保持しない fresh context へ返し、bounded random backoff 後に再監査・再受入して再試行する扱いにする。公平性が必要なら D253 の FIFO を残す案1が有利である。

### (d) 再設計案

#### 案1: lease primitive を残し、claim 保持区間だけを短縮

変更対象:

- `tools/dev_wave_wait.py:3942-4550` の順序を変更する。
- 現在の claim 部分 `:4015-4037` を merge/test より後ろへ移し、`tested_main` の snapshot、merge、provenance、受入全走を lease 外で行う。
- merge の全 gate `:4039-4102`、prerun clean/fingerprint `:4110-4133`、launcher/test/postrun/red-check `:4151-4279` は内容を変更しない。
- receipt は引き続き temp に生成する (`:4158-4175`、`acceptance_launcher.py:425-472`)。最終 publish は `:4297-4389` の claim 確認後に限定する (`:3814-3895`)。
- claim 後に `tested_main`、lease payload の `main_sha`、直後の `git rev-parse main` を比較する。違えば lease を解放し、temp receipt を破棄し、全量 merge＋受入を最初からやり直す。
- `run_acceptance()` の retry 境界 `dev_wave_wait.py:4551-4596` に race 用の full-retry 経路を追加する。既存の no-verdict retry (`:4440-4493`) に部分再検証として混ぜない。
- lock 時点でも `tools/dev_wave_land.py:2050-2137` または `:3127-3226` に `locked_main == tested_main` の strict check を追加する。不一致時は main を変更せず `stale-main`/retryable 結果を返し、D469 の release-safe 経路で lease を解放して fresh context に戻す。
- `tools/wave_land_window.py:651-903` の claim/queue/renew/release primitive は変更しない。

receipt 意味論:

- schema v5 の 27 field、`lease_holder` の digest、`tested_main`/`tested_tip` の exact binding は維持する (`tools/dev_wave_land.py:591-593, 762-774`; `acceptance_launcher.py:365-397`)。
- `tested_main` はテスト開始前に merge した main、`tested_tip` はその merge 後の wave HEAD のままにする。
- receipt は claim 前に final path へ出さず、claim 成功後だけ publish するため、「pair がテスト済み」という意味論を保てる。
- claim 後または lock 後に main が進んだら、lease/lock を保持したまま再測定しない。解放後に merge、全量受入、receipt を作り直す。

留意点:

- claim が後ろへ移るため、D253 の FIFO は「受入を始めたい順」ではなく「テストを終えて claim に到達した順」になる。これは safety ではなく fairness の変更だが、明示して裁定対象にすべきである。
- `held-self` は invocation を識別しない (`docs/decisions.md:13848-13862`)。race 時に `ACQUIRED` なら解放できるが、`HELD_SELF` なら release せず fail-closed にする必要がある。

#### 案2: lease を撤去し、D128 flock＋D254 型の再検証だけにする

変更対象:

- `tools/dev_wave_wait.py:636-652` の lease lifecycle、`:2896-3087` の claim loop、`:3122-3404` の release/cleanup、`:3623-3659` の retry renew、`:_run_acceptance_attempt()` の `:4015-4037` と `:4297-4383` を撤去または非 lease 化する。
- `tools/dev_wave_land.py:40` の lease import、`:3589-3689` の renew/release を撤去する。現行 CLI に `--lease-dir` はなく、環境変数だけを読むことも `:3558-3568, 3596-3605` で確認できる。
- D128 lock は `tools/dev_wave_land.py:2018-2047` のまま保持し、lock 取得後の `_locked_preflight()`、receipt 検証、ff-only、fold、postcondition は一切緩めない。
- lock 内で `locked_main != tested_main` を race として拒否し、lock を閉じた後、親が全量 merge＋受入を再実行する。現行 `_main_is_allowed()` の audited-closure 許可 (`:1930-1943`) だけに依存してはならない。
- D239/D253/D299/D469/D595 に依存する runbook/decision の更新が必要で、実装だけでは完結しない。

receipt 意味論:

- `tested_main`×`tested_tip` の pair 自体は、lease なしでも receipt verifier が exact 比較する限り維持できる。
- ただし `lease_holder` は live lease owner ではなく単なる wave digest になる。現行 field 名・D239 文脈の ownership 意味論まで維持することはできない。
- field を削除・改名すれば `_receipt_object()` の closed set (`tools/dev_wave_land.py:583-593`)、launcher 生成、land verifier が全て不一致になるため v6 相当の schema 変更が必要になる。したがって「schema 変更なし」と「lease 完全撤去」は同時には完全には成立しない。

## 3. acceptance launcher と compute dispatch queue

- launcher 自体は lease primitive を呼ばない。`acceptance_launcher.py:173-196` で tested-tip の `tools/run_tests.py` blob を読み、`:210-233` の `subprocess.run()` で実行する。受入 receipt は `:425-472` で生成する。

- waiter は runner argv を `dev_wave_wait.py:845-856` で固定し、実際の launcher 起動は `:859-880`、受入完了待ちは `:4177-4187, 4269-4279` にある。

- compute dispatch の入口は `tools/run_tests.py:1142-1183` の `_default_dispatch()`。ここから `tools.pegasus.dispatch_compute.dispatch()` を呼ぶ。login 側の queue 可用性観測は `run_tests.py:1384-1399, 2046-2082` にある。

- 実際の queue 待ちは `tools/pegasus/dispatch_compute.py:1716-1742` の qsub 後、`:1830-1897` の qstat polling。`QUE` のまま `queue_wait_timeout_s` を超えると `:1879-1893` で `queue-wait-timeout` になる。既定値は `:47` の 900 秒。

- よって brief の「queue 待ち込み」は呼び出し全体としては正しいが、発生箇所は `acceptance_launcher.py` ではなく `run_tests.py` と `dispatch_compute.py` である。`dev_wave_wait.py:4145-4148` の無期限待ちは、この dispatch 全体を包んでいる。

## 4. merge を claim より前へ移す場合の不変条件

- 現行契約は claim 直後に main を取り直し、behind のときだけ merge する順序 (`dev_wave_wait.py:4039-4103`; `docs/decisions.md:12433-12456`)。runbook も `rev-parse main → behind → merge → provenance → commit` を指定する (`docs/pegasus-runbook.md:976-999`)。

- AI-Agent trailer は `_validated_message_copy()`/self-report が `dev_wave_wait.py:3095-3119`、merge 後の commit message provenance が `:4062-4080`、commit dry-run/commit/postcheck が `:4081-4102`。merge を前倒ししても、この順序は維持する必要がある。

- 特に provenance checker を merge 前へ移すのは不可。checker は `MERGE_HEAD` と staged path を見ており、merge 前は検出力が落ちる (`docs/pegasus-runbook.md:985-993`)。D402 も claim 前の merge-message provenance 前倒しが clean index という別文脈になることを反証している (`docs/decisions.md:16889-16919`)。

- merge 前倒し後に main が進むと、merge commit の second parent、`tested_main`、`tested_tip`、launcher source binding が古くなる。`tested_tip` は merge 後の prerun HEAD (`dev_wave_wait.py:4123-4175`)、waiter source binding も merge 後 tip に対して行う (`:4129-4133`; `docs/decisions.md:16921-16945`)。不一致時に古い receipt を再利用してはならない。

- 現行 cleanup は lease ownership が `NONE` だと早期 return する (`dev_wave_wait.py:3369-3385`)。merge を claim 前へ移すなら、lease cleanup と `merge_pending` cleanup を分離しない限り、claim 前 merge の失敗で `MERGE_HEAD` が残る。

- 結論として、merge 自体の前倒しは隔離された wave worktree 内でなら設計可能だが、provenance preflight、AI-Agent trailer、clean/fingerprint、waiter source binding、receipt publish、race 時の merge cleanup を同時に組み替える必要がある。D254 の lock 外監査だけを根拠に単純移動するのは不十分。

## 5. 追加の障害契約と P1〜P4

- D239 は fencing token なし、claim〜release の機械的 transaction なしを受容している (`docs/decisions.md:11204-11207`)。D469 も同一 slug・同一 main_sha の別 invocation は区別できないと明記する (`docs/decisions.md:19535-19545`)。案1では `held-self` race の扱い、案2では lease 撤去後にこの穴がどこへ移るかを明記する必要がある。

- D253 の FIFO は待ち時間上界を保証しない (`docs/decisions.md:11616-11634, 11664-11670`)。案1の claim 後ろ倒しは FIFO の到着時点を変え、案2は FIFO 自体を失う。

- D432 は 180 秒を availability cap とし、fairness を保証しない (`docs/decisions.md:17942-17989`)。D128 lock の待ち中に受入・lease・テストを保持する設計へ戻してはならない。

- D469 の `release_safe and not retryable_same_request` 条件 (`docs/decisions.md:19483-19503`; `dev_wave_land.py:3631-3677`) を race 結果にも適用する。race を retryable とだけ宣言して lease を残すのは、今回の「資源なしで再測定」制約に反する。

- D595 は renew を best-effort、claim 再利用を禁止する (`docs/decisions.md:23971-24006`)。D619 は TTL、queue timeout、walltime の既定値変更を禁止している (`docs/decisions.md:24827-24855`)。

- 受入全走の内部 retry は現在 no-verdict に限定され、shared deadline と最大2 attemptで止まる (`dev_wave_wait.py:4440-4493, 4551-4596`; `docs/pegasus-runbook.md:837-842`)。race retry を追加する場合も、差分テストや既存結果の再利用ではなく、全量再走にする。

P 判定:

- **P1: 部分支持。** D254 は「重い監査を lock 外で実行し、再取得後に束縛を再照合する」型を実証する (`dev_wave_land.py:2260-2365`)。しかし merge＋受入全走まで成立する証拠ではなく、D270、D402、receipt publish、merge cleanup の追加条件がある。現状の「成立する」という断定は強すぎる。

- **P2: 支持。** D253 の FIFO と D239 の wasted acceptance 防止の目的 (`docs/decisions.md:11184-11187, 11616-11621`) に対し、D128/D432 単体は公平性を持たない。短縮した lease を残す案1の方が案2より安全側。ただし FIFO の到着時点が変わる点は残る。

- **P3: 支持。** D254 の lock 外原則、D102 の stale/busy は fresh context で再監査・再受入する契約 (`docs/decisions.md:4505-4525`) と一致する。race 時は lease/lock/ticket を保持せず、merge・受入・receipt を全量作り直す必要がある。

- **P4: 条件付き支持。** receipt schema の変更は案1では不要だが、現行 schema は 26 ではなく 27 field。案2では `lease_holder` の ownership 意味論が失われるため、schema 不変を主張するには deterministic identity として再定義する裁定が必要になる。

## 総括

- P1 は「D254 を雛形にできる」までは支持、無条件成立は反証。
- P2 は支持。
- P3 は支持。
- P4 は案1に限り条件付き支持。field 数は 27 に訂正。

推奨は案1。lease primitive と FIFO を残し、merge・受入テストを lease 外へ移し、claim 後の exact main 再確認と D128 lock 時の再確認を追加する形が最小の設計変更である。案2は D128 の公平性不足と `lease_holder` 意味論の変更が大きい。

段3で重点攻撃すべき論点は次の3つ。

- claim 後の main 不一致を検出した全経路で、lease/lock を本当に解放してから全量再受入できるか。
- merge 前倒し後も `MERGE_HEAD`、AI-Agent trailer、provenance preflight、`merge_pending` cleanup の順序が保たれるか。
- 多数 wave の D128 殺到時に、180 秒 cap と fresh-context retry が starvation/livelock を増幅しないか。