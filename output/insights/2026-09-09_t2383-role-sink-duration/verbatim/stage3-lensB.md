## 親の実測の検査

結論は、親の「96% が I/O 待ちなので 4 thread なら速くなる」は成立しない。

- この環境の `time` は Bash の予約語だった。Bash は timed pipeline の user/system CPU を集計し、Unix の `RUSAGE_CHILDREN` は待ち合わせた子孫の使用量も含む。[GNU Bash manual](https://www.gnu.org/s/bash/manual/html_node/Pipelines.html)、[getrusage(2)](https://man7.org/linux/man-pages/man2/getrusage.2.html)
- `_run_git` は `subprocess.run` で Git の終了を待つため、Git subprocess の CPU 時間も user/sys に入る。[contract_loader_binding.py:293](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/contract_loader_binding.py:293)
- 従って `real=172.912`, `user+sys=14.726` の非 CPU 比率は `(172.912-14.726)/172.912 = 91.48%`。96% は user 7.48 秒だけを引いた値に近く、sys 7.246 秒を落としている。
- しかも user/sys は pytest session 全体の CPU であり、`run_trial` node 単独の CPU ではない。言えるのは「この login session の aggregate CPU seconds が wall の約 8.5%」までである。差分には I/O 待ちだけでなく、scheduler 待ち、Git 終了待ち、page fault、他 process による遅延も入る。

さらに、比較している実装 epoch が違う。

- D1714 の 63 走は 2026-09-04〜09-07 の窓である。[decisions.md:52164](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/docs/decisions.md:52164)
- Git を 62 process から 2 process にした D1795 は 2026-09-08 である。[decisions.md:54324](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/docs/decisions.md:54324)
- 17.44 秒と cProfile は D1795 後だが、268〜312 秒は D1795 前である。従って「17.44 → 268〜312、15〜18 倍」は同じ実装の競合倍率ではない。
- 台帳の 140.0 秒も [acceptance_duration_ledger.json:9062](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/acceptance_duration_ledger.json:9062) にあるが、`git blame` 上は 2026-08-25 導入で、D1795 後の値ではない。

既存の D1795 後・現 HEAD `2143a49c...` の緑な受入全走 3 本を読むと、状況は既に変わっている。

- 対象 node は 88.618 秒、75.850 秒、68.870 秒。[run 1 JUnit:1](/work/1/SFC/tanab/.izanagi-acceptance-shards/8e4035dac57309cb918cc0a6aadee3ac/shard-2/junit.xml:1)、[run 2 JUnit:1](/work/1/SFC/tanab/.izanagi-acceptance-shards/45da11dedfdb7af33ea71e7e339394a6/shard-2/junit.xml:1)、[run 3 JUnit:1](/work/1/SFC/tanab/.izanagi-acceptance-shards/632fb2f82edc5857889efdd81be94037/shard-2/junit.xml:1)
- 対象を持つ shard 2 の wall は 267.55、260.16、250.19 秒だったが、各走の shard 0 は 319.30、325.97、440.97 秒だった。[run 1 shard 0:17](/work/1/SFC/tanab/.izanagi-acceptance-shards/8e4035dac57309cb918cc0a6aadee3ac/shard-0/dispatcher.log:17)、[run 1 shard 2:38](/work/1/SFC/tanab/.izanagi-acceptance-shards/8e4035dac57309cb918cc0a6aadee3ac/shard-2/dispatcher.log:38)、[run 2 shard 0:17](/work/1/SFC/tanab/.izanagi-acceptance-shards/45da11dedfdb7af33ea71e7e339394a6/shard-0/dispatcher.log:17)、[run 2 shard 2:35](/work/1/SFC/tanab/.izanagi-acceptance-shards/45da11dedfdb7af33ea71e7e339394a6/shard-2/dispatcher.log:35)、[run 3 shard 0:17](/work/1/SFC/tanab/.izanagi-acceptance-shards/632fb2f82edc5857889efdd81be94037/shard-0/dispatcher.log:17)、[run 3 shard 2:38](/work/1/SFC/tanab/.izanagi-acceptance-shards/632fb2f82edc5857889efdd81be94037/shard-2/dispatcher.log:38)
- したがって、現在の配置を保ったまま対象 node をゼロ秒にしても、この 3 走の受入 wall は直接には縮まらない。D1714 の「複数 node が床を作る」という結論と一致する。

現行の単独 17.44 秒に対する同 tip 受入倍率は約 3.9〜5.1 倍である。これは競合の存在を示すが、CPU、repo metadata、Git fork、tmp filesystem の fsync のどれが律速かは特定できない。4 thread が shard 全体を速くする事前保証はない。

## thread 安全性の裏取り

対象 test が使う exact な `run_trial` 構成は、現行 CPython 3.10 では実行可能と追認する。ただし `run_trial` 一般や、任意 Python runtime に対する thread-safe API とは言えない。

- `WORKLOADS`、`FORMAL_WORKLOADS` は可変 dict だが対象経路では読み取りだけ。[p3_autonomous_workload_trial.py:225](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:225) `PARSERS` も同様。[p3_autonomous_workload_trial.py:667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:667)
- run scope は `ContextVar` であり、各 thread が設定し、`finally` で reset する。[p3_autonomous_workload_trial.py:534](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:534)、[p3_autonomous_workload_trial.py:5156](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:5156)、[p3_autonomous_workload_trial.py:5224](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:5224)
- `env_contract` の process cache は shared だが、snapshot と authorization の両方が lock で保護される。[env_contract.py:553](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/env_contract.py:553)、[env_contract.py:748](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/env_contract.py:748)、[env_contract.py:860](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/env_contract.py:860)
- replay capability の `issued` dict は process global で lock がない。[artifact_admission.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/artifact_admission.py:95) ただし各発行は新しい `object()` key への単一 insert で、現在の GIL 付き CPython 3.10 では衝突しない。free-threaded Python まで一般化してはならない。
- registered lifecycle の shared dict は lock 付きであり、そもそも対象は unregistered exploratory なので到達しない。[trial_registry.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/trial_registry.py:429)、[trial_registry.py:4047](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/trial_registry.py:4047)
- `coder_authority=None` なので build authority の nonce set は変更しない。各 thread は独自 context nonceだけを作る。[build_admission.py:480](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/build_admission.py:480)

cwd・環境・process 全体状態にも、対象経路を壊す変更は見つからない。

- `_validated_root` は cwd 依存ではない。`_REPO_ROOT` は `__file__` から決まり、Git も `-C root` と明示 `env` を使う。[contract_loader_binding.py:16](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/contract_loader_binding.py:16)、[contract_loader_binding.py:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/contract_loader_binding.py:98)、[contract_loader_binding.py:273](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/contract_loader_binding.py:273)
- exact call graph に `os.chdir`、`os.environ` の変更、signal handler、logging handler の変更はない。環境は site・reservation・Git allowlist で読むだけ。[site_policy.py:66](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/site_policy.py:66)、[p3_autonomous_workload_trial.py:3027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:3027)
- `sys.path.insert` は package でない直接実行時だけの import-time branchで、pytest import 後の `run_trial` では実行されない。[p3_autonomous_workload_trial.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:37)

書込 path も論理的には分離される。

- test は wire ごとに異なる `tmp_path / wire-*` を渡す。[test_p3_autonomous_workload_trial.py:1890](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/test_p3_autonomous_workload_trial.py:1890)
- campaign、raw、proposal、journal、report はその `run_root` 以下。[p3_autonomous_workload_trial.py:4023](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:4023)、[p3_autonomous_workload_trial.py:5004](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:5004)
- namespace の `tempfile.mkstemp` は固有 root 内で一意名を作る。[layout.py:485](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/layout.py:485)
- `/scr`、home、`~/.izanagi*`、repo 内 `output/` への書込みはない。共有するのは repo registry、63 source path、Git object databaseなどの読み取り面である。
- WAL flock も wire 固有 WAL file に掛かるため、相互排他による論理衝突はない。[wal.py:1272](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/wal.py:1272)

ただし path 分離は性能分離を意味しない。832 fsync は静的にも説明できる。

- 1 run あたり namespace 2、raw 4件と proposal 1件の file/dir fsync 10、journal 7、WAL 3 recordの file/dir fsync 6、report 1で計26回。`32 × 26 = 832` で profile と一致する。[layout.py:502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/layout.py:502)、[s8b_prediction_runner.py:658](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/s8b_prediction_runner.py:658)、[p3_autonomous_workload_trial.py:753](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:753)、[wal.py:1326](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/wal.py:1326)、[p3_autonomous_workload_trial.py:2426](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:2426)
- directory が別でも backing filesystem、journal、device queue は共有する。そこで fsync が直列化される場合、4 thread は待ちを重ねず、queue depth とtail latencyだけを増やし得る。

例外伝播について、計画の `executor.map` は正しい。結果 iterator を消費すると worker 例外が main thread に再送出され、context manager は pending task の終了を待つ。[Python 3.10 concurrent.futures](https://docs.python.org/3.10/library/concurrent.futures.html)

一方、hard timeout はない。`Executor.map(timeout=...)` を付けても実行中 thread は停止できず、`with` 終了時に待つ。Git batch の timeout は最大 `10 × 63 = 630` 秒である。[contract_loader_binding.py:383](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/contract_loader_binding.py:383) `max_wall_s` も blocking Git を割り込まない。

## blocker

- **B1: 対象選定と成功条件が古い。**  
  (a) 268〜312 秒は D1795 前であり、現 tip の緑な全走では対象は68.9〜88.6秒、かつ3/3走で別 shard が最遅だった。  
  (b) 根拠は [D1714:52173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/docs/decisions.md:52173)、[D1795:54344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/docs/decisions.md:54344)、上記3組の JUnit・dispatcher log。  
  (c) test-only変更なので certified 選択と production report bytes は変わらない。しかし duration ledger だけが小さくなり、受入 wall が不変でも「受入待ちを短縮した」と誤記録できる。現 brief の成果主張は受理できない。

- **B2: 固定4 threadは共有資源に対する根拠のない負荷増である。**  
  (a) 同じ63 source path、同じGit object database、同じtmp filesystemへ4本が同時アクセスする。独立なのは論理 path であって性能資源ではない。  
  (b) plan の根拠は非CPU比だけである。[stage2-plan.md:51](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2383-role-sink-duration/artifacts/stage2-plan.md:51) 実装は1 admissionごとに同じrepoでGit batchとclosure読取を行い、各runは26 fsyncを発行する。[contract_loader_binding.py:518](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/contract_loader_binding.py:518)  
  (c) certified 選択・report値は正常完了時には同じだが、飽和でGit timeoutやI/O errorが増えると同じ正しいcheckoutのpytest受理集合がload依存で狭まる。node ledgerが改善しても、他workerの遅延でshard wallは不変または悪化し得る。固定4を最終案として実装してはならない。

## should-fix

- **S1: 計測記述を訂正する。**  
  (a) 「nodeの96%がI/O待ち」を「login上のcProfile付きpytest sessionでaggregate CPU/wallが約8.5%」へ直す。  
  (b) briefの誤記は [brief.md:24](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2383-role-sink-duration/brief.md:24)。さらに一次資料とされた `prof1.out` は検査時点のjob dirに存在しなかった。  
  (c) test受理集合やproduction値は変わらないが、insightの再現性と並行化根拠が変わる。

- **S2: thread-safeの名乗りを狭める。**  
  (a) 「現行CPython 3.10、unregistered、do_build=False、固有provider/rootのexact構成」までに限定する。  
  (b) replay capabilityのshared dictはlockを持たない。[artifact_admission.py:95](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/artifact_admission.py:95)  
  (c) 現環境では値や受理集合は変わらないが、free-threaded runtime等へ一般化すると将来のpytest受理が未定義になる。

- **S3: timeoutの限界を明記する。**  
  (a) thread timeoutはrunning Gitを停止せず、executor contextも待つ。  
  (b) Git timeoutとexecutor待機の根拠は [contract_loader_binding.py:256](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/contract_loader_binding.py:256) と公式 `concurrent.futures` 仕様。  
  (c) 値は変えないが、飽和時に受入が長時間終端しない可能性を短縮成果として隠さずに済む。

## 別解

test-onlyで、threadを増やさず、同じ被覆を保って削れる重複が存在する。campaign lock用の記録済みbindingを32回作り直さず、1回だけ作って共有する案である。

現在の `_run_git` 640回は静的に次へ分解できる。

- `capture_contract_loader_binding` 64回 × 4 Git = 256
- `verify_committed_contract_loader_binding` 64回 × 4 Git = 256
- test helper `_binding_from_recorded_head` 32回 × 4 Git = 128

最後の128回はproduction admissionではなくfixture生成である。[campaign_lock_test_support.py:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/campaign_lock_test_support.py:10) `build_v2_lock` は既にbinding注入を受け付ける。[campaign_lock_test_support.py:23](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/campaign_lock_test_support.py:23)

test fileだけで次の形にできる。

- `_binding_from_recorded_head()` をloop前に1回実行する。
- `_write_admitted_rejection_digest` に任意の`binding`引数を足し、現行 [test file:210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/tests/test_p3_autonomous_workload_trial.py:210) の `build_v2_lock` へ渡す。
- 32本の`run_trial`、64回のreal admission、64回のcurrent live closure capture、64回のcommitted binding検証、全assertは残す。

これで `_run_git` は640回から516回へ減る。各campaign.lock bytesは同じで、production受理集合を変えず、追加I/O並行性も作らない。まずこの低リスク案を測るべきである。

`ProcessPoolExecutor` はPython import・memory・forkを増やし、Git・filesystemは結局共有するため安くない。`asyncio` は同期`subprocess.run`とfsyncを単独では重ねられない。production captureをtest側でmemo化する案は64回のlive closure検証を消すため、同じ被覆とは扱えない。

## scope 外の real 所見

- **裁定候補: 現在の床へ対象を移す。** 現tipの緑3走ではshard 0のt080系nodeが最長で、対象testはshard 2の2〜3番手だった。D1714が既に挙げた別の床である。T-2383からの対象変更になるため本waveの実装案にはしない。
- **裁定候補: productionのsingle-flight。** 同時進行中の同一closure captureだけを束ねる案はmemoの永続stale問題を避け得るが、各callのrace検出窓を変える。D1795の再裁定が必要なので実装対象外。
- **D1795のmemo禁止理由は正しい。** object storeのprune・root差し替え後に古いbytesを返すprocess cacheはfail-closedを壊し得る。[decisions.md:54347](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/docs/decisions.md:54347)
- **一方、「selfがclosure memberだから変更不能」は過大である。** memberである事実は正しい。[campaign_lock.py:68](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/campaign_lock.py:68) しかし旧bindingは記録commitのblobで検証され、current closureとの差異自体は拒否しない。[contract_loader_binding.py:558](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/contract_loader_binding.py:558)、[artifact_admission.py:1115](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/artifact_admission.py:1115) D1795自身も同fileを変更している。正しくは「pin追従費用がある」であって「変更できない」ではない。
- **裁定候補: partial reportの見逃し。** `run_trial` は一部例外を`fatal_error`付きpartial reportへ変換する。[p3_autonomous_workload_trial.py:3611](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/p3_autonomous_workload_trial.py:3611) 対象testは`report["status"] == "complete"`を検査しない。executorが伝播できるのは`run_wire`から外へ出た例外だけである。新しい検査追加になるため本waveの実装案には含めない。
- `CAMPAIGN_VERIFIER_EPOCH_SCOPE` がまだ「exact 62 path」と記す一方、実際のclosureは63 pathである。[artifact_admission.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2383-role-sink-duration/orchestrator/campaign/artifact_admission.py:73) production file変更になるため別裁定とする。

## 総括

現行exact構成のthread実行は、CPython 3.10では論理的に可能である。  
ただし96%という根拠は誤りで、正しくはsession全体の非CPU比約91.5%である。  
268〜312秒はD1795前の値であり、現tip緑3走では対象は68.9〜88.6秒、最遅shardでもない。  
固定4 threadが受入wallを縮める保証はなく、共有Git・metadata・832 fsyncを悪化させ得る。  
まずtest fixture bindingを1回へ前計算し、128中124件のGit起動を安全に除く案を採るべきである。  
現planはNO-GO。pytestや性能測定は実行していない。