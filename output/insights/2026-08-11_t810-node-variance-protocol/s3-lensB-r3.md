判定は NO-GO です。静的監査で blocker 8件、must-fix 2件、nit 1件です。`build_v2` の claim と SHA-256 自体は実装されていますが、実行契約と非流入境界が閉じていません。

### 1. build_v2 を使う実行経路が固定されていない

- **severity:** blocker
- **主張:** `build_v2` は明示的な `ExecutionEnvironmentContract` が必須なのに、計画の preregistration に contract hash がなく、実装が `env_contract=None` の legacy `build()` 分岐へ落ち得る。
- **根拠:** `orchestrator/campaign/buildcache.py:575-665` は `contract` と `cache_root` を必須化、`orchestrator/campaign/pipeline.py:748-799` は contract 無しで legacy build、`orchestrator/campaign/buildcache.py:802-829` は既定 cache を `build-variants` に置く。計画は `s2-plan.md:305-327,529-550` で `build_v2` を要求するが contract hash を固定していない。
- **成果物影響:** legacy cache が使われると同一 binary の前提が崩れ、12 job 全体を無効化して計算時間を空費する。
- **提案:** 既存の active Pegasus contract（現行 g2 なら `env_contract.py:253-269`）の `contract_sha256`、calibration ref、activation state hash を `protocol.json` に固定し、`None` と legacy build を fail-closed で拒否する。

### 2. binary の SHA-256 だけでは計算ノードで実行可能とは言えない

- **severity:** blocker
- **主張:** buildcache の identity は compiler・toolchain・`dependency_prefix` までで、module、loader、runtime library の path/hash、build path 依存性を束縛していない。
- **根拠:** `orchestrator/campaign/buildcache.py:237-266` の preimage に runtime manifest と source path がなく、`:376-430` の completion manifest も binary SHA と toolchain だけ。`external/ccbench/CMakeLists.txt:33-35,73-75` は Boost/gflags/glog を解決し、`external/ccbench/cmake/Findgflags.cmake:5-18` は host の library path を採用する。gflags/glog が static でも、`facts.md:84-92` のとおり libstdc++ 等の残余 runtime は未検査である。
- **成果物影響:** builder では動くが measurement node で loader failure または別 runtime になり、全測定値が無効になる。
- **提案:** `readelf`/`ldd` 相当の依存名・解決 path・bytes hash、module list、`LD_LIBRARY_PATH`、`/scr` 参照検査を builder と全 node で実施し、manifest hash を release token に束縛する。

### 3. N 本の投入を group として閉じる barrier/revocation がない

- **severity:** blocker
- **主張:** `#PBS -b 1` と logical host 48 CPU は同一 host への配置を起こしにくくするだけで、N 本の全件 ready、後発 QUE の無実行、失敗時の revocation を保証しない。
- **根拠:** `docs/pegasus-runbook.md:33-50` は `Exclusive submit = OFF`、`:999-1037` は generic N-job gate/verifier が無いと明記。`tools/pegasus/dispatch_compute.py:1286-1314` は 1 invocation=1 job、`tools/pegasus/submit_certify.sh:167-201` も単一 qsub。計画は `s2-plan.md:258-278` で barrier を要求するが、timeout 後の revoke/late job 処理を定義していない。
- **成果物影響:** 一部 RUN・一部 QUE の状態でノードを待たせ、最大20分単位のノード時間を捨てる。release 漏れがあれば欠損値が集計へ入る。
- **提案:** 全 request ID を含む group state machine、共有 revoke marker、全 job の benchmark 直前 revoke 再確認、N 件 exact terminal verifier を設ける。部分成功は必ず `premeasurement_invalid` にする。

### 4. `run_probe.py` は静穏 preflight ではない

- **severity:** must-fix
- **主張:** `run_probe.py` は hardware attestation と任意 JSON 出力だけで、load、pgrep、hostname、quiet threshold を実行しない。
- **根拠:** `tools/pegasus/run_probe.py:29-94`、`orchestrator/campaign/env_attestation.py:600-686`。競合検出は別の `orchestrator/calibrator/runner.py:171-203,221-285`、load gate は `orchestrator/calibrator/cli.py:51-54,234-258` に分散している。既存 wrapper は `certify_calibration.sh:342-343` で bare `python3` を使う一方、probe wrapper は `python3.10` を明示している。
- **成果物影響:** interpreter failure または静穏確認漏れで、N job 分の計算を無効化する。
- **提案:** T-810 専用 PBS wrapper を作り、`python3.10` の実体/version 検査、load `≤1.0`・30秒×3・1200秒、local pgrep、canary probe、host receipt を一つの closed schema に束ねる。

### 5. `--certify` 禁止が機械的に強制されていない

- **severity:** blocker
- **主張:** 「certify route を使わない」は計画上の argv allowlist に留まり、既存経路は実際に calibration attempts と registered artifact を自動生成する。
- **根拠:** `tools/pegasus/certify_calibration.sh:37-41,722-748`、`orchestrator/calibrator/cli.py:625-666` は attempts を作成し、`:793-856` は accepted artifact を `registered/` へ publish。`--certify` では `--out-root` も禁止される。
- **成果物影響:** 未較正の T-810 値が calibration/registered surface に入り、certified environment の候補へ流入する。
- **提案:** T-810 専用 executable enum と child-side argv validation を実装し、calibration writer capability を持たない runner だけを許可する。

### 6. 非流入の expected set と監査が repository 全体を閉じていない

- **severity:** blocker
- **主張:** 61ファイルの成功集合、`git status`、既存 frozen manifest だけでは、ignored file・新規 output・wildcard consumer への流入を検出できない。
- **根拠:** `orchestrator/tests/test_frozen_artifacts.py:38-85,125-153` は既存23 pathだけを検査。`orchestrator/tests/test_campaign_import_invariant.py:1001-1005` と `orchestrator/tests/repo_tree_util.py:94-108` は gitignored untracked file を除外する。`orchestrator/campaign/screening_driver.py:33-53` は calibration directory の `between_run_noise_*.json` を wildcard 走査する。なお、より強い freeze namespace scan は `orchestrator/campaign/s8b_floor_campaign.py:1637-1724` に存在するが、計画はそれを使わない。
- **成果物影響:** accidental output が downstream consumer に拾われ、未較正値が certified 系列へ流入する。
- **提案:** 測定 job の write capability を repo 全体に対して deny-by-construction にし、外部 root だけを許可する。補助監査として ignored file、symlink、socket、全 child process の write target を走査し、全 consumer namespace を明示 deny-list 化する。

### 7. 推奨 evidence root が既存の durable-root policy と噛み合わない

- **severity:** blocker
- **主張:** 計画が推奨する repo 外 root は、既存 capability の既定許可範囲である repo `output/` 外にある。
- **根拠:** `orchestrator/campaign/layout.py:49-77` は既定 `approved_roots` を repo `output/` だけに限定し、外部 root を拒否する。計画は `s2-plan.md:387-412` で repo 外 root を推奨する。
- **成果物影響:** runner が capability を使えば開始前に失敗し、使わずに直接 `open()` すれば非流入防壁を失う。
- **提案:** Stage 4 で `/work` 配下の root、owner/mode、retention、mount identity を固定し、T-810 専用 `DurableRootPolicy` と repo-wide forbidden root を明示する。

### 8. B 系並走ガードは「設計のみなので自明」ではない

- **severity:** blocker
- **主張:** 将来の実施時に必要な T-139 状態確認と A 優先裁定の fail-closed gate が、既存 submitter に存在しない。
- **根拠:** `docs/phase3-8b-restart-runbook.md:19-23,103` は `qstat -u` と A 優先を要求するが、`tools/pegasus/submit_certify.sh:116-120` が取得するのは `qstat -Q` 等だけで、T-139 job state や ruling priority を判定しない。計画自身も `s2-plan.md:294-301` で未実装・未実測としている。
- **成果物影響:** T-810 が T-139 と並走して測定を無効化し、ノード時間を空費する。
- **提案:** 投入直前に `qstat -u <user>` の exact job/state parser、unknown-state 拒否、A ruling ID/priority receipt、競合時の T-810 withdrawal を group manifest に必須化する。

### 9. 予算残高に対する admission rule がない

- **severity:** blocker
- **主張:** `37,080 node-s` という概算はあるが、実際の walltime・retry・liveness を含む reservation と `rbudgetcheck` 残枠の比較が未定義である。
- **根拠:** `s2-plan.md:237-246,494-512` は最終 reservation 式を実装前に調整すると記載。`tools/pegasus/submit_certify.sh:116-151` は `rbudgetcheck` の raw output/rc を保存するだけで、残枠比較をしない。最後の記録済み実測は `docs/worklog.md:1341-1344` の `SFC 残 5084.76 / 6000`。
- **成果物影響:** 12本・retry・liveness の投入で quota/ポイントを消費し、途中失敗または測定不能になる。
- **提案:** node-second から site budget point への承認済み換算を固定し、`builder + N jobs + liveness + retry上限` の全量が残枠内の場合だけ投入する。N=12 は統計的根拠を持つが、空きノードだけを理由に増やしてはいないことも receipt 化する。

### 10. §8投入前手順と失敗時の exact set が未接続

- **severity:** must-fix
- **主張:** 計画の slot scheduler log は、runbook §8 の `qsub -o/-e`、queue状態、quota、interpreter、投入形状のチェックと結び付いていない。
- **根拠:** `docs/pegasus-runbook.md:1074-1133` はこれらを必須化する一方、`s2-plan.md:258-301,420-449` は group manifest と成功集合を示すだけで、`qsub -o/-e` の逐語形と全 failure-state presence matrix がない。既存 submitter の qsub は `tools/pegasus/submit_certify.sh:167-180`。
- **成果物影響:** PBS の `.o/.e` が repo に落ち、または部分失敗の receipt が集合外になって、計算空費・非流入監査失敗を招く。
- **提案:** Stage 4 で pre-submit receipt、`qstat -Q`/`pegasusinfo`/`check_quota`/`rbudgetcheck`、`-o/-e` path、failure state 別 exact set を literal に固定する。

### 11. 文書参照規律に反する line reference が残っている

- **severity:** nit
- **主張:** 将来の protocol 文書へ s2-plan の `file:line` 参照をそのまま移すと、docs 間の行番号参照禁止に反する。
- **根拠:** `s2-plan.md:10-13` などに多数の行番号参照があり、`CLAUDE.md:155` は docs 間を section reference に限定。新文書の地図は `docs/README.md:41-49` に追加が必要。
- **成果物影響:** 直接の流入ではないが、参照切れにより誤った preflight を行い再走・無効化を招く。
- **提案:** 新文書では見出し・schema ID・commit hash を参照し、Stage 4 の同一 commit で `docs/README.md` の地図と stale な §7.5 記述を整理する。

## 総括

**NO-GO。blocker 8件。**

攻撃面1・2・4は blocker を確認しました。攻撃面3は既存 probe と threshold の実装箇所までは確認しましたが、T-810 用の接続は未実装です。実機での `ldd`、loader smoke、qstat barrier、fair-share、実 budget 換算、全 consumer の実走追跡は未検査です。qsub、build、benchmark、pytest は実施していません。

段4で最低限裁定すべき択一は次のとおりです。

- 既存 active Pegasus g2 contract を再利用して hash 固定するか、新しい非 production build identity を設けるか。
- runtime を完全 self-contained にするか、依存 manifest＋全 node loader smoke を採用するか。
- N 本独立 request の group barrier/revoke を実装するか、実装完了まで本走を禁止するか。
- repo 外 root に専用 capability を設けるか、repo 内 namespace＋全域 allowlist を採用するか。
- B guard を `qstat -u`・A ruling receipt 付きで機械化するか。
- `N=12,R=10`、liveness、最大 retry を含む全 reservation が残 budget 内かをどう固定するか。
- `≤1.0 / 30秒×3 / 1200秒`、start spread 5秒、ready timeout 20分を採用するか、別値を実走前に裁定するか。