静的検査のみ。対象は HEAD `1a3604b` の clean tree で、pytest は実行していない。

前提として、P1 を「`state == "RUN" and not run_seen` の内側で一度だけ再設定する」と厳密に解釈すれば、有限入力・前進する monotonic clock の下で RUN 後の上界は消えない。ただし、境界順序、RUN 観測の信頼性、入力検証、qdel の残存経路に real な穴がある。

## 所見 1 — 一回限りの P1 で RUN 後の状態列が無限化する、という攻撃は条件付きで refuted

(a) 主張: `run_seen` を一度だけ `True` にし、その同じ分岐内でだけ deadline を張り直すなら、質問に挙げられた状態遷移だけで deadline が滑り続ける経路はない。

(b) 根拠: `run_seen` は初期化後、`False` へ戻すコードがない。[dispatch_compute.py:1046](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1046)、[dispatch_compute.py:1215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1215)

| 状態列 | 実際の処理 | 有限性 |
|---|---|---|
| `RUN → RUN → …` | 二回目以降は `not run_seen` が偽。毎 poll で overall 判定 | 有限 |
| `RUN → UNKNOWN → RUN` | UNKNOWN でも `run_seen=True` を維持。再 RUN でも再設定しない | 有限 |
| `RUN → QUE/HLD → RUN` | queue timeout は戻らないが、RUN deadline は固定 | 有限。ただし scheduler の再実行 walltime とずれる候補 |
| `RUN → qstat rc≠0 → …` |通常は `QSTAT_ERROR` として overall 判定を継続 | 有限 |
| `RUN → rc=0・request ID 消失` | `request_absent=True` から `END` へ強制し、先に break | ループ終了 |
| qstat 呼出しが例外 | 監視を抜け、外側 except の qdel/receipt/rc=16 へ | ループ終了 |
| `QUE → END` で RUN 見逃し | deadline 再設定なしで成果物収集へ | ループ終了 |

`request_absent` は「初回 qstat で可視だった」「現在 rc=0」「構造化 ID がない」の積であり、監視ループへ入る正常経路では最初の条件は常に真になる。[dispatch_compute.py:1187](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1187)

(c) 成果物影響: この限定命題自体による certified 選択・レポート・台帳値の追加変化はない。正しい P1 の意図した変化だけ、旧 `overall-timeout/rc=16` が正常な `outcome.kind="child"` へ戻る。

(d) 修正案: `run_deadline: Optional[float]` を別変数にし、`is None` のときだけ同じ `now` から設定する。既存の `test_overall_walltime_plus_grace_bound_qdels_running_job` は、RUN ごとに再設定する変異を概ね殺せるが、`RUN→UNKNOWN` と `RUN→QSTAT_ERROR` の post-RUN 上界テストも追加すべきである。[test_pegasus_dispatch_compute.py:1308](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1308)

## 所見 2 — first RUN の処理順が pre-RUN deadline をすり抜ける

(a) 主張: real。P1 を現在の `state == "RUN"` 分岐へ素直に入れると、最初の RUN を観測した時点ですでに pre-RUN deadline が切れていても、期限判定より先に未来へ張り直せる。brief の「pre-RUN の初期 deadline は現状のまま残す」は、その境界点では成立しない。

(b) 根拠: 現在の順序は「RUN を記録」→「`not run_seen` の queue timeout」→「overall timeout」である。[dispatch_compute.py:1215](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1215)、[dispatch_compute.py:1219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1219)

例として `walltime=1s, grace=0, queue_timeout=20s`、`QUE@t=0 → RUN@t=5` とする。旧 deadline は `t=1` だが、P1 を RUN 分岐へ置けば `t=6` へ更新してから overall 判定する。さらに queue timeout も、RUN を先に立てる現順序では初回 RUN 観測時に回避される。これは queue timeout については既存欠陥、overall については P1 が新たに広げる受理集合である。

(c) 成果物影響: この境界入力では、旧実装の receipt は `kind="infra"`, `reason="DispatchError: overall-timeout"`, `qdel.attempted=true`。P1 後は child が終われば `kind="child"` と実 child rc になる。mutation harness 経由なら旧側は `rc=16/status=PARSE_ERROR`、新側は実際の `KILLED/SURVIVED/MISMATCH` へ変わり得る。

(d) 修正案: 親裁定が必要である。

- pre-RUN 上界を本当に保存するなら、`pre_run_deadline` と queue timeout を first RUN 遷移より先に検査する。
- 遅れて観測した RUN を無条件で救うなら、brief の不変条件を「現在 sample が credible RUN なら pre-RUN deadline を supersede する」と書き換える。
- `RUN` が queue/overall 境界の直前・同時・直後に来る三つのテストを追加する。

## 所見 3 — RUN 観測が qstat 成功に束縛されていない

(a) 主張: real なコード経路。P1 の再設定条件は「信頼できる RUN 観測」ではなく、stdout の文字列 parser が RUN を返したことだけになる。逆に、実際には走行中でも既知文字列に当たらなければ P1 は発火せず、旧型 qdel が残る。

(b) 根拠:

- `_scheduler_state()` は `running/pre-running/run` を RUN とし、未知値は `None` にする。[dispatch_compute.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:207)
- `state` は qstat の return code に関係なく stdout から解析される一方、表示だけは rc≠0 なら `QSTAT_ERROR` になる。[dispatch_compute.py:1192](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1192)
- したがって「rc≠0 だが stdout に `Request State = RUN`」なら、receipt の state は `QSTAT_ERROR` なのに `run_seen=True`、`queue_wait_observed=True`、P1 deadline 再設定となる。
- `pre-running` が scheduler walltime の開始後か前かは repo 証拠で未確定。前なら、そこで張り直すと pre-running 時間を再び実行予算から差し引く。
- 実測済み NQSV 文字列は `Current State = Running` と `Staging` で、前者は現 parser に入る。[parent-dogfood-findings.md:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/output/insights/2026-07-30_pegasus-compute-node-dispatch/parent-dogfood-findings.md:31)
- `QUE → 実RUN → 終了` を poll で飛び越して request 消失を観測する経路は、RUN deadline を使わず正常収集へ進む。既存テストもこの意味を固定している。[test_pegasus_dispatch_compute.py:1228](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1228)

(c) 成果物影響: 偽 RUN では `state_history="QSTAT_ERROR"` と `queue_wait_observed=true` が矛盾し、不要に deadline が延びる。未知状態の実 RUN では queue/initial overall timeout が走行中 job を qdel し、dispatch receipt は rc=16、mutation 台帳は PARSE_ERROR になり得る。

(d) 修正案: P1 の RUN 証拠を最低でも `current.returncode == 0 and request_present is True and state == "RUN"` に束縛する。`pre-running` の扱いと、marker を代替 RUN 証拠にする案は受理集合を変えるため「scope 外候補」として裁定へ返す。非ゼロ qstat stdout に RUN を混ぜた回帰テストも必要。

## 所見 4 — monotonic の時間領域は整合するが、基準時刻の説明が過大

(a) 主張: P1 は同一の monotonic 値 `now` を使う限り、時計領域そのものは壊さない。しかし deadline は「実際の RUN 開始」ではなく「RUN 初観測」から始まり、brief の exact な上界表現と「fake と実 scheduler の差は状態観測粒度だけ」は誤りである。

(b) 根拠:

- `started` は preflight 前で、state history の `elapsed_s` にしか使われない。[dispatch_compute.py:1060](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1060)
- `submitted_at` は qsub が戻り receipt capture した後で、`queue_started` と初期 deadline の基準になる。[dispatch_compute.py:1090](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1090)、[dispatch_compute.py:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1181)
- P1 の `now` は RUN を返した qstat 呼出し後に読むため、実 RUN から最大で sleep、qstat 遅延、先行する qstat error 分だけ遅れる。
- `_run()` 自体は実環境では最大 30 秒の command timeout を持ち、その所要時間も `time.monotonic()` に入る。fake scheduler は通常これを進めない。[dispatch_compute.py:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:252)
- deadline 判定は sleep/qstat の前なので、実際の停止は deadline より最大 `poll_interval + qstat所要` 遅れ得る。さらに END 判定が deadline より先なので、期限後の END は timeout ではなく収集へ進む。

(c) 成果物影響: `queue_wait_s` は実 queue 待ちではなく RUN 観測までの上界であり、state history の elapsed は preflight を含む。この意味は P1 で変わらないが、レポートで「実 RUN から厳密に walltime+grace」と記すと誤証明になる。現行 TASKS は tests/provenance だけなので certified 選択への直接値変更はない。

(d) 修正案: 二回目の `clock()` を呼ばず同じ `now` を使い、変数・テスト名を `run_observed_at` / `run_observation_deadline` 相当にする。fake runner が qsub/qstat 中にも clock を進めるテストを加え、brief の「差は観測粒度だけ」を撤回する。

## 所見 5 — 非有限 float と巨大 interval で実質無制限になる

(a) 主張: real、ただし既存欠陥なので scope 外候補。P1 の「RUN 後は必ず有限」という保証は現 accepted input では成立しない。

(b) 根拠:

- timeout 群の検査は `min(...) < 0` と `poll_interval == 0` だけで、`NaN`、`inf`、巨大有限値を拒否しない。[dispatch_compute.py:969](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:969)
- CLI は `type=float` なので `nan` / `inf` を受理する。[dispatch_compute.py:1515](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1515)
- `overall_grace_s=nan` なら RUN 後の deadline も NaN となり、`now >= deadline` は恒偽。`inf` なら有限時刻では恒偽。RUN 後に UNKNOWN/qstat error が続けば無限 poll になる。
- `queue_wait_timeout_s=inf` と `overall_grace_s=inf` の組合せなら pre-RUN UNKNOWN も無限。
- `accounting_grace_s=nan/inf` と不足成果物の組合せなら、END 後の collection loop が無限。[dispatch_compute.py:1236](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1236)、[dispatch_compute.py:1272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1272)
- `poll_interval_s=86400` のような巨大有限値も受理され、1 秒 walltime でも次回判定まで一日待てる。
- `_walltime_seconds()` は minute/second だけを制限し、hours は桁数無制限。[dispatch_compute.py:143](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:143)
- 注入 seam で固定 clock と no-op sleep を組み合わせれば、有限 deadline でも無限になる。production の既定 `time.monotonic/time.sleep` ではないが、boundedness の内部契約は未明記。

(c) 成果物影響: dispatcher が戻らなければ final receipt、task-run record、mutation record が作られず、これは brief が主張する「試行欠落」が実際に成立する経路である。certified 選択値を静かに変えるより、成果物生成自体を停止させる。

(d) 修正案: `math.isfinite()` を queue/overall/accounting/poll の全値へ適用し、poll には合理的な最大値を設ける。walltime hours も queue policy 上限へ束縛するか、少なくとも local deadline が有限 float へ変換可能かを qsub 前に確認する。NaN/inf の拒否テストは本 wave に含めるか別タスクとして明示する。

## 所見 6 — P1 後も「走行中を殺す qdel」は多数残る

(a) 主張: real。P1 は一つの早過ぎる overall-timeout を後ろへずらすだけで、qdel の状態非依存性を直さない。D131 が列挙する「active job に対する qdel の禁止」は満たさない。

(b) 根拠: `active` は qsub 成功直後に立ち、scheduler の QUE/RUN を表さない。[dispatch_compute.py:1089](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1089)

| qdel 箇所 | 走行中を殺し得る条件 | receipt / latch |
|---|---|---|
| immediate qstat permission error | job が qstat 確認前に RUN、または状態不明 | `kind=f47`、恒久 latch あり |
| immediate qstat success・request 不在 | false absence / visibility race なのに実 job は RUN | `kind=f47`、latch あり |
| 外側 `except BaseException` | qsub parse/capture失敗、qstat例外、signal、queue/overall timeout、収集・結果検証例外の時点で RUN | `kind=infra`、通常 latch なし |
| compute marker 不在 | 通常は END 後だが、rc=0・ID欠落を false END とした場合は RUN の可能性 | `kind=f47`、latch あり |

直接箇所は [dispatch_compute.py:1139](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1139)、[dispatch_compute.py:1160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1160)、[dispatch_compute.py:1283](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1283)、[dispatch_compute.py:1361](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:1361)。`_best_effort_qdel()` は qdel の command result を保存するだけで、実際の終了・会計着地を再確認しない。[dispatch_compute.py:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:889)

順番待ち中 qdel は child 未起動の cancellation で、compute marker/result がなく、実計算課金も通常発生しない。走行中 qdel は部分出力・実使用課金・共有 worktree の途中状態を残し得るが、generic except は会計収集をせず receipt を確定する。overall/queue timeout は F47 でも latch でもないため、同じ事故を次の投入で繰り返せる。

(c) 成果物影響:

- 現在の mutation dispatch 形では outer harness は生存し、`finally` で変異を戻しつつ、当該 record を `rc=16/status=PARSE_ERROR` として保存する。[mutation_harness.py:1299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:1299)、[mutation_harness.py:2075](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:2075)
- 将来の T-360 束ね形では harness 自身が計算 job 内に入るため、qdel が harness を殺すと `finally` 復元と現在 record の write が走らず、dirty tree・台帳欠落になり得る。
- running qdel の receipt は `accounting_verified` を持たず、certified 選択や材料レポートへ採用できる値ではない。

(d) 修正案: scope 外候補として落とさず裁定へ返す。少なくとも `run_seen=True` 後の infrastructure error では自動 qdel を禁止し、scheduler walltime と人間 handoff に委ねる。RUN 未観測時も fresh な rc=0 qstat が QUE/HLD/STG を示した場合だけ queued cancellation を許し、UNKNOWN/error では走行中かもしれない request を殺さない。signal 時の明示取消しは別ポリシーとして裁定する。

D131 は共通前提として「`total_deadline` の修正と、active job に対する qdel の禁止」の両方を要求している。[decisions.md:6398](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/docs/decisions.md:6398) brief の deadline-only scope では T-360 のこの前提を完了扱いにできない。

## 所見 7 — 親 brief の逐語・一般化・成果物説明に複数の反証がある

(a) 主張: real。欠陥の中心算術は正しいが、file:line、テスト被覆、300 秒一般化、成果物帰属が過大または誤りである。

(b) 根拠:

| brief の主張 | 判定 |
|---|---|
| `1181-1182`, `1215-1217`, `1219`, `1221` | 現 HEAD と一致 |
| `1358-1385 except 節` | 誤り。except は `1361`、qdel 呼出しは `1381-1386` |
| queue timeout 900 / overall grace 300 | 正しい。[dispatch_compute.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:29) |
| 「順番待ち >300s で walltime 満了前 qdel の余地」 | 理想算術上の必要条件としては正しいが、十分条件ではない |
| fake と real の差は状態観測粒度だけ | 誤り。qsub/qstat 実時間、30秒 timeout、poll overshoot も deadline 算術へ入る |
| unknown-state test が未知状態の上界を覆う | pre-RUN UNKNOWN だけ。`RUN→UNKNOWN` の張り直し後上界は未被覆 |
| 該当試行が台帳から欠落 | 現行 consumer について一般には誤り |
| receipt が原因をジョブ側へ誤帰属 | `outcome.kind="infra"` なので child/job outcome への分類ではない。reason の粒度が粗い、が正しい |
| 数時間 walltime なら発火確率が上がる | `Q>grace` の算術からは導けない。実行時間分布と queue 分布の証拠が必要 |

旧 deadline を `W+G`、実 queue 待ちを `Q`、実行時間を `D` とすると、走行中の早期 qdel には概ね `Q < W+G < Q+D` が必要である。`Q>G` は「requested walltime 境界 `Q+W` より親 deadline が前」というだけで、job がそこまで走ることや poll が間に合うことを保証しない。

既存 unknown test は最初から UNKNOWN であり、RUN 後ではない。[test_pegasus_dispatch_compute.py:1334](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1334)。また `test_walltime_override_is_bound_to_pbs_and_total_bound` は名前に反し、実際には qsub argv の walltime しか assert しない。[test_pegasus_dispatch_compute.py:1366](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/orchestrator/tests/test_pegasus_dispatch_compute.py:1366)

台帳については、task-run context があれば dispatch の最終 rc=16 も記録対象である。[run_tests.py:859](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/run_tests.py:859)。mutation harness も baseline なら `PARSE_ERROR` baseline を書いて停止し、mutation 中なら当該 `PARSE_ERROR` record を書いてから停止する。[mutation_harness.py:2013](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:2013)、[mutation_harness.py:2040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/mutation_harness.py:2040)。欠落するのは主に後続予定試行、または将来の bundled harness 自体が殺された場合である。

(c) 成果物影響: 現行 `TASKS` は `tests` と `provenance` のみで、この dispatcher 自身は「certification submitter を置換しない」と明記されている。[dispatch_compute.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:3)、[dispatch_compute.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t363-deadline/tools/pegasus/dispatch_compute.py:55)。したがって現時点の certified 選択値への直接変更はない。mutation report では欠落ではなく、当該 record の `rc=16`、`status=PARSE_ERROR`、`summary.PARSE_ERROR += 1`、`summary.completed` は増えない、が正確である。

(d) 修正案: 段 4 前に brief を訂正する。

- except 行範囲を現 HEAD に合わせる。
- 300 秒を「理想 deadline が requested walltime 境界より前になる条件」に限定する。
- post-RUN UNKNOWN/error と first-RUN 境界を新規テストへ入れる。
- 回帰テストは qdel 不実行、child rc、receipt outcome まで見る。
- 「trial 欠落」「job 側誤帰属」「長時間なら高確率」を consumer ごとの実証値へ置き換える。
- T-363 完了と D131 の active-qdel 禁止完了を分離する。

## 総括

- P1 は一回限りなら有限だが、first RUN を期限判定より先に処理すると pre-RUN queue/overall 上界をすり抜ける。
- `NaN/inf` と巨大 poll が受理されるため、「RUN 後は必ず walltime+grace で閉じる」は現 accepted input では偽である。
- deadline を直しても走行中 qdel は多数残り、D131 の active-job qdel 禁止も、brief の台帳・certified 成果物説明も満たされない。