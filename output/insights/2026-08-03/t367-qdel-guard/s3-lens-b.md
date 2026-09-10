指定資料を全文または指定節まで静的読解した。pytest・実 qstat/qdel は実行しておらず、緑は主張しない。

### [所見 1] request と state が束縛されず、RUN ジョブを許可集合へ混入できる

深刻度: **blocker**

根拠: plan は `_qstat_mentions_request()` と `_scheduler_state()` の独立結果を連言するだけとしている（[stage2-plan.md:28](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:28)）。前者は出力中の任意の `Request ID` を探し（[dispatch_compute.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:173)）、後者は出力中で最初に一致した状態を返す（[dispatch_compute.py:207](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:207)）。同じ request block の証拠であることも、状態が一意であることも検査しない。

再現または成立条件: rc=0 の stdout が次なら、対象は RUN なのに `request_present=true`、`scheduler_state=QUE`、`allowed=true` になる。

```text
Request ID = 999999.nqsv
Request State = QUE
Request ID = 424242.nqsv
Request State = RUN
```

対象 ID 一つでも、`QUE` と `RUN` が重複すれば最初の状態だけで許可される。`qstat -f <ID>` が通常一件を返すという期待は、malformed/schema drift を fail-closed に扱う本件では防壁にならない。

成果物影響: receipt は誤って `qdel.gate.allowed=true` と記録し、走行中のテストジョブを殺す。親の task-run ledger は rc=16、受入レポートは欠測となり、将来 T-360 がこの経路を再利用すれば試行 attempt と transport receipt の対応も切れる。

提案: 「正規化 ID がちょうど一件」「その block に状態がちょうど一件」「競合状態なし」を同時に検査する結合 parser を作る。複数 ID・複数状態・競合状態は UNKNOWN として拒否する。mixed-block と duplicate-state の負例を必須化する。brief の「二関数をそのまま再利用」は撤回が必要。

### [所見 2] テスト反転は概ね正当だが、fake scheduler 分類に一件の明確な取りこぼしがある

深刻度: **major**

根拠: `_Scheduler` は引数付き qstat ごとに state を一つ消費し、枯渇すると副作用付きの `DONE` を返す（[test_pegasus_dispatch_compute.py:140](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:140)、[同:160](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:160)）。

14 定義の検算結果は次のとおり。

- `933`: QUE/RUN/DONE 後、gate は暗黙 DONE。分類どおり。
- `946`: `visible=False` は index を進めず、gate も request 不在。分類どおり。
- `1013`: immediate と gate がともに rc=153。分類どおり。
- `1096`: QUE/RUN/DONE 後、gate は暗黙 DONE。分類どおり。
- `1295`: immediate と gate がともに例外。分類どおり。
- `1324`: immediate RUN、poll RUN、既存三個目の RUN が gate。分類どおり。
- `1389`: QUE/RUN/RUN/UNKNOWN/UNKNOWN を監視が消費し、追加 UNKNOWN が gate。分類どおり。
- `1411`: untrusted 側への末尾 ERROR 追加は正しい。しかし同じテストの trusted 側は QUE/RUN/UNKNOWN×3 を使い切り、gate が暗黙 DONE を読む。plan はこの二回目の dispatch を分類していない（[stage2-plan.md:131](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:131)、[test:1411](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1411)）。
- `1174`: HLD 四個目追加で正しい。
- `1253`、`1267`: discovery の引数なし qstat は state を消費せず、gate が最初の QUE。正しい。
- `1350`、`1369`、`1458`: 正常終了で gate 未到達。正しい。

また、既存の pre-RUN UNKNOWN テスト（[test:1480](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:1480)）も変更後は第三の UNKNOWN を gate が読むが、plan は qdel 非実行・gate receipt の期待追加を挙げていない。これは「変えるべきなのに据え置かれた期待」である。

テスト弱体化については、plan が反転する八件――interpreter、M6、F47、accounting grace、scheduler exception、overall RUN、post-run UNKNOWN、nonzero qstat――はいずれも裁定に基づく qdel 許可集合の縮小で説明できる。skip・削除・期待緩和の提案は見当たらない。ただし暗黙 DONE で負例を通すのは、plan 自身の「tuple 枯渇で偶然通さない」（[stage2-plan.md:139](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:139)）に反する。

成果物影響: trusted 側が request 不在として偶然緑になり、UNKNOWN 処理または gate 呼出回数の欠陥を受入レポートが見逃す。認定選択値そのものは直ちに変わらないが、その前提となる受入証拠が偽陽性になる。

提案: `1411` の trusted tuple に明示 UNKNOWN を追加し、両 dispatch の `qdel.gate` と qdel 非実行を検査する。`1480` にも同じ期待を追加する。暗黙 DONE を使うテストは gate 用 response を明示し、少なくとも gate qstat 回数を固定する。

### [所見 3] P2 の one-shot は transient 下で、消せる QUE ジョブを系統的に孤児化する

深刻度: **major**

根拠: plan は gate qstat を一回に固定する（[stage2-plan.md:25](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:25)、[同:167](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:167)）。一方、現行 immediate 経路は transient を最大三回再試行し（[dispatch_compute.py:1108](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1108)）、一回失敗後の回復を既存テストで固定している（[test:978](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/orchestrator/tests/test_pegasus_dispatch_compute.py:978)）。retry 後も「fresh rc=0・QUE/HLD」でしか qdel しないため、retry 自体は確定裁定を広げない。

再現または成立条件: 実際は QUE のまま、gate の一回目だけ接続エラー、次回は rc=0/QUE となる場合。`initial_qstat_failures=1/2` が模す一過性 burst に条件づければ、one-shot の取消失敗率は100%、三回 retry は0%である。

独立な一回失敗確率を `p` と仮定すると、one-shot の見逃しは `p`、三回全滅は `p³`。例えば `p=1%, 5%, 10%` なら、one-shot はそれぞれ `1%, 5%, 10%`、三回は `0.0001%, 0.0125%, 0.1%`。実機の `p` は測定されていないので絶対頻度は確定不能であり、「性質が違うから一回でよい」という plan の断定には実測根拠がない。

成果物影響: receipt は `attempted=false/qstat-nonzero`、親 task-run ledger は rc=16になる一方、QUE ジョブは後から実行して `result.json` とログを遅延生成する。親 ledger の失敗 attempt に遅れて成功実行がぶら下がり、再実行すれば二重走行になる。

提案: permission・RUN・END は即拒否しつつ、transient だけを絶対 cleanup deadline 内で2～3回再試行する。各回で最新の状態を再評価し、最後に fresh QUE/HLD を得た場合だけ qdel する。`ERROR→QUE`、`ERROR→ERROR→QUE`、全滅の三系列を追加する。

### [所見 4] cleanup は既存 deadline の外側で最大約95秒はみ出し、receipt から観測できない

深刻度: **major**

根拠: 各 scheduler command の既定 timeout は30秒（[dispatch_compute.py:252](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:252)）。監視 deadline は loop 冒頭でしか検査されず、その後に sleep と qstat がある（[dispatch_compute.py:1229](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1229)）。plan は gate 30秒＋qdel 30秒を既存 deadline 外に足すだけとしている（[stage2-plan.md:179](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:179)）。

再現または成立条件: deadline 直前から既存 poll が `poll_interval_s` 5秒＋qstat 30秒を消費し、その後 gate qstat 30秒、許可後 qdel 30秒を消費すれば、deadline 超過は概ね最大95秒になる。既に qstat `TimeoutExpired` で outer except に入った場合も、同じ障害へさらに30秒問い合わせる。SIGINT/SIGTERM で outer except に入った後に gate qstat が止まれば、単一 signal から復帰まで最大30秒、QUE 応答後の qdel も止まれば最大60秒かかる。

gate を `state_history` に入れない方針に加え、提案 receipt には開始時刻・所要時間・使用 timeout がない（[stage2-plan.md:100](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:100)）。外側の task-run duration は cleanup 分まで含む（[run_tests.py:880](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/run_tests.py:880)）のに、増分を帰属できない。

成果物影響: task-run ledger の `duration_s` が最大約60～95秒膨らみ、queue/test 所要時間と cleanup 遅延が混ざる。親 supervisor の外側 timeoutにも到達し、receipt・受入レポート自体が欠測し得る。

提案: cleanup 専用の絶対 deadline と per-command remaining timeout を設ける。signal 経路はさらに短い上限を定める。receipt に `cleanup_started_elapsed_s`、`qstat_duration_s`、`qdel_duration_s`、`cleanup_budget_s` を残し、fake clock で上界を固定するテストを追加する。

### [所見 5] gate 許可後の qdel 失敗には「ジョブが残る」警告が出ない

深刻度: **major**

根拠: `_best_effort_qdel()` は qdel が非ゼロでも例外でも `attempted=true` を返すだけである（[dispatch_compute.py:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:889)）。plan の残存警告は gate が「見送った場合」に限定され（[stage2-plan.md:13](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:13)、[同:54](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:54)）、許可後の qdel rc/exception は既存形のままとする（[同:105](/work/1/SFC/tanab/dev-wave-jobs/t367-qdel-guard/stage2-plan.md:105)）。

再現または成立条件: fresh qstat が HLD を返し、続く qdel が rc=153、`TimeoutExpired`、`OSError` のいずれかになる。receipt は `gate.allowed=true, attempted=true` だが、外側 except 経路では人間向け残存警告が一切ない。`active=False` も維持されるため再確認されない。

成果物影響: 親は rc=16だけを受け取り、同じ受入全走を再投入できる。旧 HLD/QUE ジョブが残れば複数の試験実行と複数 receipt が生まれ、どの attempt が正規か曖昧になる。

提案: `returncode==0` 以外と例外時にも必ず残存警告を出す。receipt には `command_accepted` または少なくとも `job_may_remain=true` を設け、`attempted` と成功を混同させない。fake scheduler に qdel 非ゼロ・例外 vector を追加する。

### [所見 6] 自己適用が壊れた際の bootstrap・復旧契約がない

深刻度: **major**

根拠: brief は「親の全走が通ること」だけを不変条件にする（[brief.md:43](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/output/insights/2026-08-03_t367-qdel-guard/brief.md:43)）。ログインノードの `run_tests.py` は変更対象を import して整数 rc だけを受け取り（[run_tests.py:826](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/run_tests.py:826)）、想定外例外も rc=16へ畳む（[run_tests.py:839](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/run_tests.py:839)）。infra 経路は receipt の保存先戻り値を捨て、成功時のように path を表示しない（[dispatch_compute.py:1404](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:1404)）。

再現または成立条件:

- syntax/import 破損: qsub 前に rc=16となり、dispatch receipt が存在しない場合がある。
- qsub/monitoring 破損: pytest は開始されず、infra receipt だけ残る。
- gate deny/qdel failure: 親は rc=16で戻るが、旧ジョブが後から全走を開始する。
- cleanup 遅延: 外側 acceptance timeoutが先に切れる。

成果物影響: `rc=16` は pytest 不合格ですらなく「pytest 未実行」である。node 数・pytest summary・`outcome.kind=child/accounting_verified=true` がない限り、受入レポートに全走結果を記録できない。孤児がある状態で再走すれば task-run ledger が二重化する。

提案: 実装前に `py_compile`、次に当該テストファイル、最後に全走という bootstrap 手順を明記する。rc=16時は receipt の `outcome/qdel.gate/qdel.returncode/request_id` を確認し、qstat で旧 request の終了を確認するまで再投入しない。dispatcher 自身が import不能なら、runbook の直接 qsub による計算ノード実行を独立 fallback として事前登録する。infra 時も永続 receipt path を表示する。

### [所見 7] v2 据え置きは直ちに破壊しないが、consumer 根拠は検証になっていない

深刻度: **minor**

根拠: repo-wide 検索では、`receipt["qdel"]` 自体を読む production consumer は見つからず、brief の狭い主張（[brief.md:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/output/insights/2026-08-03_t367-qdel-guard/brief.md:29)）は反証できなかった。一方、dispatch receipt 全体の consumer は `mutation_harness._read_dispatch_stdout()` に実在する（[mutation_harness.py:1008](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/mutation_harness.py:1008)）。ただしこれは成功 receipt の既存 field だけを読み、新しい gate 形を検査しない。

`collect_receipt.py` は別の `submit-receipt.json` を読み `pegasus-final-receipt/v1` を生成する（[collect_receipt.py:118](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/collect_receipt.py:118)、[同:153](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/collect_receipt.py:153)）。`tools/dev_waves/receipt.py` と `orchestrator/qualification/` も別 schema であり consumer ではない。

再現または成立条件: 過去 v2を exact-key schema と解釈する repo 外 consumer があれば additive field で壊れるが、repo 内では確認できない。逆に plan が挙げる mutation harness は gate 付き infra receipt を通常読まないため、互換性の実証にもなっていない。

成果物影響: repo 内の mutation artifact の `receipt_path/job_stdout_path/artifact_error` は現状変わらない。certified 選択・試行台帳への直接影響を立証できないため minor とする。

提案: v2を維持するなら「qdel は open/additive object、gate は optional」と契約化し、旧 v2と新 v2の両 fixture を consumer testへ通す。closed schema を意図するなら v3へ上げる。

### [所見 8] runbook は新しい orphan・retry 契約と食い違う

深刻度: **major**

根拠:

- 一般手順は「待機中・実行中ジョブを qdel」とだけ書く（[pegasus-runbook.md:124](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/docs/pegasus-runbook.md:124)）。これは人間の明示操作なら有効だが、自動 dispatcher の RUN 禁止との境界がない。
- §8 は qstat の transient error を再試行すると明記する（[pegasus-runbook.md:563](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/docs/pegasus-runbook.md:563)）。one-shot gate を採ると、同じ `dispatch_compute.py` 正本内でこの記述が偽になる。
- rc=16 の説明は dispatch infra failureまでで、request が残る可能性と再投入前の確認がない（[pegasus-runbook.md:527](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/docs/pegasus-runbook.md:527)）。
- hook は dispatcher path と qsub/qstat/qdel head を sanctioned とするだけで（[guard_bash.py:174](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/hooks/guard_bash.py:174)）、fresh-state gate を強制しない。bytes pin ではないという brief の説明は正しいが、安全性の補助にもならない。

再現または成立条件: gate denyまたは qdel failureで rc=16を受けた利用者が、runbookどおり infra failureとして即再実行する。前 request が QUEなら後から走り、RUNなら並走する。

成果物影響: 同じ受入対象について複数の dispatch receipt、scheduler log、task-run attempt が生成され、レポートがどれを正規実行として参照すべきか不明になる。

提案: docs 側には次の差分が必要。

- §3 の qdel は「人間の明示的な手動操作」と明記する。
- immediate visibility retry と cleanup gate retryを分けて記述する。
- `qdel.gate.allowed=false`、qdel 非ゼロ・例外時は live job の可能性があり、qstat 確認前に再投入しないと追記する。
- hook は実行面の許可だけで、state gate の保証ではないと明記する。

### [所見 9] 親 brief は現行の成果物影響を campaign trial まで過大一般化している

深刻度: **minor**

根拠: dispatcher 自身は development harness で certification submitter ではない（[dispatch_compute.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:3)）。現行 task enum は `tests` と `provenance` だけである（[dispatch_compute.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/tools/pegasus/dispatch_compute.py:55)）。それに対し brief は、未実装の現状でも campaign の試行と attempt/receipt 対応が失われると書く（[brief.md:56](/work/1/SFC/tanab/izanagi/.claude/worktrees/wave-t367-qdel-guard/output/insights/2026-08-03_t367-qdel-guard/brief.md:56)）。

再現または成立条件: 現行 HEAD の task 閉集合のまま T-367だけを評価する場合。壊れるのはテスト・provenance の transport と開発受入証拠であり、certification/campaign 本走はこの dispatcherへ投入できない。

成果物影響: 現時点の certified 選択値・材料レポート・CC試行台帳を直接変える経路はない。T-360 の前提として将来影響するだけなので minor とする。

提案: brief を「現在の直接影響＝開発テスト/provenance receipt」「将来 T-360 が task追加裁定を経て再利用した場合の影響＝mutation trial」に分ける。

## 総括

この plan は現状では受理不可。最大の blocker は、対象 request と状態を結合せず、malformed な rc=0応答から RUN ジョブへの qdel を許せる点である。

P1「request 不在は取消不可」と P3「END は取消不可」は確定裁定と整合し、静的反証は得られなかった。P2「one-shot」は反証された。transient の実測頻度は未取得だが、一回 burst 条件では取消失敗100%、独立確率モデルでも見逃しは `p` 対 `p³` となる。

八件の期待反転は許可集合の縮小として正当で、skip・削除・無関係な緩和は見当たらない。ただし dual-dispatch test の state 枯渇と pre-RUN UNKNOWN の未更新により、false green が残る。加えて timeout 予算、qdel 自体の失敗警告、自己適用の復旧手順、runbook の orphan 契約を実装前に閉じる必要がある。テストは実行していない。