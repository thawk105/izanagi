現行プランは、このままでは受理不可です。特に、状態と request の非結合解析、TOCTOU、gate 拒否後も生存する job と同期 caller の契約破壊が未解決です。以下はすべて静的読解による所見であり、pytest は実行していません。

### [所見 1] state と request が結合されず、malformed 出力で RUN を QUE と誤認できる / 深刻度 blocker

- **根拠:** [`_qstat_mentions_request():173`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:173) は stdout 全体のどこかに対象 ID があれば真、[`_scheduler_state():207`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:207) は stdout 全体で最初の state を返す。両者は同じ request block に属することを検査しない。さらに `_STATE_RE` を `_CURRENT_STATE_RE` より先に採用する。プランはこの2関数をそのまま destructive gate に再利用する（[stage2-plan.md:27](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:27)）。既存 parser test は単一 state だけである（[test_pegasus_dispatch_compute.py:776](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:776)）。

- **再現または成立条件:** rc=0 の出力が次なら、対象 ID は可視、state は `QUE` と判定される。

  ```text
  Request ID = 424242.nqsv
  Request State = QUE
  Current State = Running
  ```

  複数 request block で、先頭の別 job が QUE、対象 job が RUN の場合も同じである。また `waiting`、`wait`、`queue`、`hold`、`holding` まで取消可能状態へ拡張しており、裁定の raw 語彙 QUE/HLD/STG より広い。

- **成果物影響:** gate receipt は `scheduler_state=QUE, allowed=true` と記録しながら RUN 中の対象へ qdel を出し得る。該当 test/provenance attempt、mutation ledger の job stdout・receipt 対応が欠測し、後続の試行受理集合が縮む。resource 競合が後続計測へ及べば、その計測は certified 選択から除外すべきになる。

- **提案:** gate 専用 parser を作り、対象 ID の exact 1 block、exact 1 state、相互矛盾なしを連言で要求する。複数 ID・複数 state・`Request State` と `Current State` の不一致はすべて UNKNOWN とする。実測 NQSV block、複数 block、QUE+RUN 矛盾を negative test に追加する。

### [所見 2] request ID の grammar と discovery が destructive target を束縛していない / 深刻度 major

- **根拠:** [`_parse_request_id():163`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:163) は任意の `\S+`、[`_normalize_request_id():154`](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:154) は空文字以外を受理する。qdel はその値を option separator なしで渡す（[dispatch_compute.py:896](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:896)）。一方、qualification 側は先頭英数字の閉じた job-ID grammar を既に持つ（[qsub_binding.py:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/qualification/qsub_binding.py:14)）。discovery は job name または submission-dir の部分文字列の一方だけで候補にする（[dispatch_compute.py:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:827)）。job name は nonce の先頭10文字だけである（[dispatch_compute.py:333](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:333)）。

- **再現または成立条件:** qsub 出力が `Request --all submitted...` のような値を返すと、qstat/qdel がその文字列を request ID ではなく option と解釈し得るため、gate が確認した対象と qdel の意味が一致しない。また、同じ先頭10文字の nonce を持つ旧 job だけが qstat 全件出力に見えると、parse 失敗した新 job の代わりに旧 job を一意発見して削除できる。

- **成果物影響:** 別 attempt の queued job を削除し、TOCTOU と組み合わされば別の RUN job にも及ぶ。試行台帳の request ID と実際に削除された job の対応が偽になる。

- **提案:** `0:` を除いた後に「先頭英数字＋許可文字列」の exact grammar を強制する。discovery は exact request-name と exact path field の双方を要求し、名前だけの一致を権威にしない。先頭 `-`、名前衝突、複数候補、別 submission-dir の negative test を追加する。

### [所見 3] QUE→RUN の TOCTOU により「走行中を殺さない」は成立しない / 深刻度 blocker

- **根拠:** プラン自身が qstat と qdel の間を非 atomic な残余リスクと認める（[stage2-plan.md:184](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:184)）。実装案も別々の subprocess 呼出しである（[stage2-plan.md:26](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:26)、[dispatch_compute.py:898](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:898)）。

- **再現または成立条件:** fresh qstat が QUE を返した直後に scheduler が job を RUN へ遷移させ、続く qdel が RUN job を受理する。両 command 間に sleep がなくても、process 起動・scheduler 通信・OS scheduling の窓は消えない。

- **成果物影響:** receipt は裁定準拠の `gate.state=QUE` を残す一方、実際には走行中の attempt が中断される。結果・stdout・会計の対応が欠け、mutation ledger や試行台帳は当該 attempt を受理できない。

- **提案:** 確定裁定が直接保証するのは「fresh snapshot が取消可能状態のときだけ qdel を発行する」までだと成果主張を限定する。「qdel 時点で RUN ではない」は保証しないと明記する。絶対保証を完了条件に残すなら、scheduler 側の atomic conditional delete／状態付き取消 primitive が必要であり、本 helper だけでは完了扱いにできない。少なくとも QUE snapshot 後に fake state を RUN へ変える characterization test を置き、残余を不可視化しない。

### [所見 4] gate 拒否後も job が生存するため、同期 API と mutation harness の source 隔離が壊れる / 深刻度 blocker

- **根拠:** プランは rc・return・`active=False` の順序を変えず（[stage2-plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:52)）、`active=False` は scheduler 非活動を意味しないと認める（[stage2-plan.md:185](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:185)）。一般 except には submission latch がなく（[dispatch_compute.py:1371](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1371)）、request ID 不明でも receipt を書いて戻るだけである（[dispatch_compute.py:1397](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1397)）。`run_tests.py` は整数 rc しか消費しない（[run_tests.py:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/run_tests.py:826)）。

  mutation harness は runner 終了後、必ず変異 source を復元する（[mutation_harness.py:1275](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/mutation_harness.py:1275)）。timeout 時は dispatcher の process group を TERM→KILL し（[mutation_harness.py:1098](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/mutation_harness.py:1098)）、TIMEOUT record なら次の変異へ進み得る（[mutation_harness.py:2048](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/mutation_harness.py:2048)）。

- **再現または成立条件:** overall timeout の gate が RUN を見て qdel を拒否する。dispatcher は rc=16 で戻るが job は live repo を使って継続する。harness は source を復元し、timeout 分岐では次の mutation を適用できる。request ID discovery 失敗、qstat error、許可後の qdel nonzero/exception でも同型である。

- **成果物影響:** job が「投入時の mutation」ではなく復元後または次 mutation の source を読むため、mutation ledger の `repo_head`・mutation ID・stdout が実行実体と一致しない。孤児が複数化すると計算資源を消費し、後続 wave の単独性検査を落とし、受理可能な計測 attempt を減らす。D131 の永続 attempt 対応と子 rc 契約（[decisions.md:6400](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/docs/decisions.md:6400)）も満たさない。

- **提案:** qsub 受理後は「scheduler terminal または削除確認済み」になるまで同期 return を許さないか、durable な unresolved-job lease を発行し、全 caller の次回投入・source 復元・worktree 廃棄を停止させる。request ID 不明、gate UNKNOWN、qdel失敗にも create-only latch を必要とする。mutation harness との lifecycle test は本 wave に含めるべきで、警告文だけでは足りない。

### [所見 5] P1/P2/P3 の根拠づけが崩れている / 深刻度 major

- **根拠:**

  - **P1:** F47 は request が「一度も走らず消えた」と記録するだけで、qdel による掃除を恒久対応としていない（[failures.md:989](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/docs/failures.md:989)）。一方、現行コードと test は request 不在時の qdel を明示的に要求する（[dispatch_compute.py:1161](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1161)、[test_pegasus_dispatch_compute.py:946](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:946)）。P1 は確定裁定どおり必要だが、「F47 と衝突しない」ではなく「既存の保険的 cleanup を廃止する」が正確である。
  - **P2:** plan は immediate retry を可視性遅延用と説明する（[stage2-plan.md:167](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:167)）が、実コードは rc=0/request不在でも即 break し、retry するのは非ゼロ transient だけである（[dispatch_compute.py:1125](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1125)）。P2 の比較根拠は事実と違う。
  - **P3:** visible END を削除しないこと自体は妥当。しかし監視が END で停止した後（[dispatch_compute.py:1209](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1209)）、plan は矛盾する fresh QUE/HLD を取消許可する（[stage2-plan.md:66](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:66)）。END→QUE は再queue、ID再利用、parser不整合を区別できず、fail-closed なら UNKNOWN であるべき。

- **再現または成立条件:** transient error の1回目だけで gate が終了し、実際は HLD の job が残る。あるいは terminal history=END の後に malformed qstat が QUE を返して qdel を許す。F49 は qstat が実際に可視だった QUE→RUN の事例であり（[failures.md:1039](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/docs/failures.md:1039)）、request 不在下の hidden RUN を実証していない。

- **成果物影響:** cleanup 可能な queued job が孤児化し、また矛盾状態で別 attempt を削除し得る。いずれも receipt/request/attempt の受理可能な対応集合を減らす。

- **提案:** P1 は裁定として維持しつつ unresolved-job reconciliation を必須化する。P2 は「retry禁止」を安全性から自動導出せず、error/absent の bounded retry後に得た最後の fresh rc=0 QUE/HLDだけを許す案と比較する。P3 は過去の trusted END と fresh cancellable state の矛盾を UNKNOWN とする。

### [所見 6] BaseException 境界が自己矛盾し、signal・例外時の once-only と receipt 真実性がない / 深刻度 major

- **根拠:** plan は「正規化から qstat capture まで」を `BaseException` で囲むと書く一方（[stage2-plan.md:32](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:32)）、「gate 全体」を囲んで再呼出ししないとも書く（[stage2-plan.md:180](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:180)）。また `active=False` は helper の後のまま（[stage2-plan.md:52](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:52)）。現行 `_best_effort_qdel` は `_run` が process 起動前に OSError を投げても `attempted=True` を返す（[dispatch_compute.py:897](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:897)）。

- **再現または成立条件:** 狭い try なら、分類・record 構築・signal 例外が `active=True` のまま外側 except に入り、gate が再度呼ばれる。広い try なら、qdel 実行後から helper return までの SIGTERM が「gate exception」として結果を上書きし、実際は qdel 済みなのに `attempted=False` を記録し得る。qdel の `_run` が pre-spawn OSError の場合は逆に「実際に起動した」という plan の意味と食い違う。

- **成果物影響:** qdel の実行有無、gate snapshot、request ID の対応が receipt 上で偽になる。試行台帳やレポートが destructive action の有無を監査できない。

- **提案:** helper 呼出し前に once-only cleanup latch を立てる。qstat decision 部分と qdel primitive 部分の例外境界を分離し、qdel result を一度得た後は gate exception で上書きしない。`attempted` は「invocation requested」に定義し直すか、spawn/returncode を別 field にする。二重 SIGTERM、各 bytecode seam、pre-spawn OSError、qdel 後 signal、submission-dir 消失を直接テストする。

### [所見 7] optional v2 gate と tail-only capture では安全性を後から証明できない / 深刻度 major

- **根拠:** plan は schema v2 を維持し、gate を optional とし、旧 v2 receipt も有効とする（[stage2-plan.md:109](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:109)）。receipt には dispatcher source、qstat/qdel executable identity、cleanup-policy version がない。さらに `_capture()` は stdout/stderr の末尾65536文字だけを無印で保存する（[dispatch_compute.py:244](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:244)）。実測 qstat では Request ID と Current State は出力先頭にある（`output/env/pegasus/smoke/0:867861.nqsv/qstat_job.stdout:1,7`）。

- **再現または成立条件:** `qdel.attempted=true` かつ `gate` 不在の v2 receipt は、旧 unconditional 実装、新実装の bypass、将来の不正 caller を区別できない。oversized/malformed qstat では、判定に使った先頭 state が receipt の tail から消え、plan の「STG raw 証拠が残る」という主張も成立しない。

- **成果物影響:** report や mutation ledger が v2 receipt を参照しても、「guarded qdel だった」という proof chain が成立しない。安全性を証明できない attempt は受理集合から外す必要がある。

- **提案:** v3 へ上げるか、少なくとも全 receipt に必須の `cleanup_policy`、dispatcher source identity、scheduler executable realpath/version を置く。qdel attempted receipt には gate object を必須化する。qstat は exact parsed block、raw byte数・SHA-256・明示的 head/tail omission を保存し、decision evidence が保存不能なら取消を拒否する。

### [所見 8] 親の三つの「実測」は、狭い事実は正しいが一般化が過大 / 深刻度 major

- **根拠:**

  - 親が緑と報告した `test_overall_walltime_plus_grace_bound_qdels_running_job` は、synthetic RUN 列と、常に rc=0 を返す fake qdel の組合せである（[test_pegasus_dispatch_compute.py:1324](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1324)、[同:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:184)）。「fake が qdel command を観測した」は支持するが、「実 NQSV が RUN job を削除した」は支持しない。
  - `FROZEN_MANIFEST` 23件が全て `output/` なのは literal と exact assert から確認できる（[test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_frozen_artifacts.py:38)、[同:139](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_frozen_artifacts.py:139)）。しかし mutation harness は dispatcher の HEAD blob SHA を runner identity に含め（[mutation_harness.py:475](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/mutation_harness.py:475)）、resume 時に exact 一致を要求する（[mutation_harness.py:1657](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/mutation_harness.py:1657)）。したがって frozen bytes が動かなくても旧 mutation ledger は再利用できない。
  - repo 内で `qdel` object の key を読む production consumer が見当たらない点は静的には正しい。しかし、それだけで durable schema を据え置く根拠にはならない。また production dispatch caller は `run_tests.py` だけではなく、provenance checker もある（[check_ai_provenance.py:1019](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/check_ai_provenance.py:1019)）。

- **再現または成立条件:** dispatcher source 更新後に旧 mutation ledger を `--resume` すれば `runner_sha256/runner_identity` 不一致で拒否される。旧 v2 receipt の外部 consumer は repo grep では確認できない。

- **成果物影響:** 本 wave の mutation ledger は fresh に採り直す必要があり、その `runner_sha256` と `dispatch_entrypoint_sha256` が変わる。親実測は実 scheduler の kill 証拠や既存 ledger 継続性の証拠には使えない。

- **提案:** 実測主張を「fake command sequencing」「FROZEN_MANIFEST literal 非波及」「現 repo 内 qdel-key consumer」に限定する。実 NQSV の kill 成否は未実測とし、旧 ledger 非再利用と provenance caller への波及を計画へ追記する。

### [所見 9] 現行4 callsite の閉包は静的には成立するが、機械的に固定されていない / 深刻度 minor

- **根拠:** 現行 repo の自動 qdel command は `_best_effort_qdel` 内の1箇所（[dispatch_compute.py:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:889)）で、production callsite は提示された4箇所である。別に、人間向け runbook は実行中 job の手動 qdel を許し（[pegasus-runbook.md:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/docs/pegasus-runbook.md:124)）、hook も qdel head を許可する（[guard_bash.py:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/hooks/guard_bash.py:184)）。submit family は qsub/qstat を直接使うが qdel は持たない。campaign task は未実装である（[pegasus-runbook.md:540](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/docs/pegasus-runbook.md:540)）。

- **再現または成立条件:** 将来 `_best_effort_qdel` を直接呼ぶ5番目の caller が追加されても、現プランの状態別テストだけでは「全 caller は gate 経由」という閉包を必ずしも固定しない。supervised runner の TERM→KILL（[worker.py:181](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/dev_waves/worker.py:181)）は scheduler job を直接削除しないが、dispatcher を殺して孤児化させる点は所見4の対象である。

- **成果物影響:** 現時点の追加 qdel 経路は見つからず、現在の成果物値を直接変える所見ではないため minor とする。submit family の orphan reconciliation は本 wave の automatic-qdel scope 外だが、別タスクとして返すべきである。

- **提案:** AST/meta-test で `_best_effort_qdel` の production caller が新 gate の1箇所だけであることを固定する。低水準 primitive は危険性が分かる名称に変え、直接 import/call を禁止する。runbook の手動 qdel は自動 policy と射程が異なることを明記する。

## 総括

最大の欠陥は三つです。

1. request と state を同一 block に束縛しない parser は、malformed `QUE + RUN` を取消許可できる。
2. qstat→qdel は非 atomic なので、実現できる保証は「直前 snapshot に基づく許可」に限られ、「走行中を絶対殺さない」ではない。
3. qdel を拒否して同期 callerだけ終了すると live job が残り、mutation harness が source を復元・次走できる。これは試行台帳の実行実体を壊す。

したがって、少なくとも target-bound parser、strict request-ID grammar、unresolved-job lifecycle、once-only signal設計、監査可能な receipt 契約をプランへ戻すまで実装へ進めるべきではありません。テスト実行は行っておらず、緑は主張しません。