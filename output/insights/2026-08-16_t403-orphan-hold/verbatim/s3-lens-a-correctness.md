静的検査のみであり、pytest は実行していない。

# 所見 1: `request_present=False` は不在証明ではなく、P1 に具体的 false negative がある

判定 (real/refuted): real

根拠 (file:line):

- qsub 成功直後に qstat が rc=0 でも request をまだ表示しない経路は、既存テスト自身が「ジョブが残っている可能性あり」と固定している。[test_pegasus_dispatch_compute.py:1724](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/orchestrator/tests/test_pegasus_dispatch_compute.py:1724) では `success-request-absent`、`request_present=False`、`job_may_remain=True`、警告出力が同時に成立する。
- ところが P1 は `request_present is False` だけで hold を抑止する。[brief.md:82](/home/SFC/tanab/.claude/jobs/610dedfd/tmp/wave-t403/brief.md:82)、[s2-plan.md:91](/home/SFC/tanab/.claude/jobs/610dedfd/tmp/wave-t403/s2-plan.md:91)
- 実コードでも、qsub 成功で `active=True` となった後、初回 qstat が request 不可視なら F47 経路へ入り、cleanup qstat が再び不可視なら `request-absent` を返す。[dispatch_compute.py:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1493)、[dispatch_compute.py:1567](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1567)、[dispatch_compute.py:1195](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1195)
- F47 は次回投入だけを止める。P1 の hold が立たなければ、今回の source 復元は止まらない。

全 return 経路との照合は次のとおり。

| `_fresh_qstat_gated_qdel` 経路 | `job_may_remain` | P1 hold | 評価 |
|---|---:|---:|---|
| ID 不明、clock/gate/qstat 例外、予算切れ、permission、RUN/UNKNOWN | `True` | 立つ | 妥当 |
| `success-request-absent` | `True` | 立たない | 上記の具体的 false negative |
| `terminal-history-conflict` | `True` | 立たない | 終端履歴の由来次第で false negative |
| qdel rc=0 | `False` | 立たない | qdel 後の終端再確認がなく、D142 の保証範囲外 |
| qdel 非ゼロ・例外 | `True` | 立つ | 保守的だが false positive を含む |
| `_capture` の BaseException、SIGKILL、process crash | return しない | 署名未評価 | 所見 2〜4 の false negative |

`terminal-history-conflict` も安全な例外ではない。`terminal_history_end` は対象 block に束縛されない permissive parser から立つ [dispatch_compute.py:1594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1594) 一方、fresh gate は対象 request が現在 QUE/HLD でも hold 抑止 reason を返す [dispatch_compute.py:1199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1199)。D142 自身が permissive parser は別 block の state を拾いうると認めている。[decisions.md:6947](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/docs/decisions.md:6947)

成果物影響 1 行: F47/PARSE_ERROR で受理自体は止まっても変異 source が復元され、attempt record と実際に後刻 job が読む bytes の対応が失われるため、その台帳を参照する proof は使えない。

推奨対処: `request_present=False` 単独を終端証明にしない。少なくとも「対象を以前に一意に可視化済み、その後対象束縛された不在または終端を観測」の provenance を追加し、P4 の「既存 3 field だけ」を撤回する。安全側なら `job_may_remain is True` を例外なく hold とする。

# 所見 2: qsub 受理から `active=True` まで hold が一度も武装されない

判定 (real/refuted): real

根拠 (file:line):

- qsub は [dispatch_compute.py:1479](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1479) で実行されるが、`active=True` は command が戻った後の [dispatch_compute.py:1493](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1493) である。
- scheduler が受理した後、qsub process の return 観測前に signal・例外・SIGKILL が来れば、outer exception は `active=False` と見て `claim_cleanup_once` を呼ばない。[dispatch_compute.py:1780](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1780)
- プランの hold 発行点は `claim_cleanup_once` 内だけなので、この経路には receipt、request ID、hold のいずれも保証されない。[s2-plan.md:140](/home/SFC/tanab/.claude/jobs/610dedfd/tmp/wave-t403/s2-plan.md:140)

成果物影響 1 行: job が実在しても hold 不在として復元・後続投入・checkout 削除が受理され、変異台帳と実行 source の対応が無条件に壊れる。

推奨対処: qsub 前に durable な「受理結果不明」claim を作り、qsub 非受理または job 終端を証明した場合だけ append-only の解決証拠で閉じる。`active` の in-memory bool を権威にしない。

# 所見 3: harness の 5 秒 SIGKILL が 90 秒 cleanup を途中で殺す

判定 (real/refuted): real

根拠 (file:line):

- dispatcher の cleanup budget は 90 秒で、scheduler command 1 回の timeout も 30 秒である。[dispatch_compute.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:37)、[dispatch_compute.py:352](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:352)
- harness timeout は process group へ SIGTERM を送り、5 秒で終わらなければ SIGKILL する。[mutation_harness.py:1328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1328)
- 計画では hold は `_fresh_qstat_gated_qdel` の return 後にしか書かれない。[s2-plan.md:142](/home/SFC/tanab/.claude/jobs/610dedfd/tmp/wave-t403/s2-plan.md:142) したがって cleanup 中の dispatcher だけが 5 秒で殺され、PBS job は残り、hold はない。
- harness はこの結果を `TIMEOUT` と分類する [mutation_harness.py:1434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:1434)。`TIMEOUT` は正規の terminal/expected status であり [mutation_harness.py:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:37)、期待値と一致すれば次変異へ進み、最終的に rc=0 も返せる。[mutation_harness.py:2355](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:2355)

成果物影響 1 行: expected `TIMEOUT` が matching record として台帳・terminal wrapper・fan-out 受理集合へ入りうる一方、孤児は復元後または次変異の source を読むため、B-057 の全 KILLED/TIMEOUT proof が偽になる。

推奨対処: cleanup 完了を待つ時間調整だけではなく、qsub 前の durable claim と dispatcher 終了 handshake を導入する。未解決 claim がある timeout は通常 `TIMEOUT` として受理せず、専用 orphan-stop に落とす。

# 所見 4: hold 作成失敗は INFRA へ落ちるだけで、再ラッチされない

判定 (real/refuted): real

根拠 (file:line):

- プランは `FileExistsError` 以外の `OSError` を伝播させるとしている。[s2-plan.md:70](/home/SFC/tanab/.claude/jobs/610dedfd/tmp/wave-t403/s2-plan.md:70)
- 現行 caller は `_fresh_qstat_gated_qdel` を呼ぶ前に `cleanup_claimed=True` とし、再入時は既存 `receipt["qdel"]` を返すだけである。[dispatch_compute.py:1430](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1430)
- よって `_latch_orphan_hold` の `os.open` が EACCES、ENOSPC 等で失敗すると outer exception へ移り、二度目の `claim_cleanup_once` は hold 作成を再試行しない。[dispatch_compute.py:1804](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1804)
- 反対に、hold 作成済み後の `_persist_receipt` 単独失敗は false negative ではない。プラン順では hold が先であり、receipt helper も失敗を `None` に畳むだけである。[dispatch_compute.py:1274](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1274)
- malformed JSON、directory、symlink を存在扱いする読取方針は fail-closed である。ただし permission error を「不存在」へ変換しない契約とテストは未記載である。

成果物影響 1 行: hold storage が壊れた場合ほど通常の rc=16 に見えて source が復元され、台帳には「INFRA だった」という結果だけが残って孤児との因果が欠落する。

推奨対処: hold 書込み不能を通常 INFRA と同一化しない。親子 pipe／attempt sidecarにも unresolved-cleanup を残し、consumer は file の不在ではなく「安全終了証拠の存在」を投入・復元・削除の条件にする。

# 所見 5: hold file は同期原語ではなく、三つの TOCTOU を閉じない

判定 (real/refuted): real

根拠 (file:line):

- プラン自身が、二 invocation が hold 不在検査を同時通過しうると認めている。qsub 直前の再検査は窓を縮めるだけである。[s2-plan.md:173](/home/SFC/tanab/.claude/jobs/610dedfd/tmp/wave-t403/s2-plan.md:173)
- mutation finally は一度存在検査した後に `_restore_targets` を実行する計画であり、その間を排他しない。[s2-plan.md:193](/home/SFC/tanab/.claude/jobs/610dedfd/tmp/wave-t403/s2-plan.md:193) 復元側は signal を block して全 target を上書きするため、検査後に hold が立っても復元を完遂する。[mutation_harness.py:892](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:892)、[mutation_harness.py:925](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_harness.py:925)
- worktree 側も bool を `_should_teardown` に渡した後、dispatch root 全体を rename し、container を `rmtree` する。[mutation_worktree.py:1131](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:1131)、[mutation_worktree.py:637](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:637)、[mutation_worktree.py:891](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:891)
- rename 後に latcher が走れば、元 root が消えて hold 作成自体が失敗する。rename 前に立てば hold ごと evidence へ移され、既に計算済みの `orphan_hold=False` は変わらない。

成果物影響 1 行: terminal ledger と wrapper rc=0/1 が成立した後でも孤児 checkout を削除でき、fan-out contract が要求する「teardown 完了」を誤って受理して proof chain に取り込む。

推奨対処: dispatch claim、source 復元、evidence 退避、teardown が共有する per-checkout lifecycle lock/state machine を設ける。再検査の追加だけでは閉じない。

# 所見 6: P1 には確実な false positive もあり、永久停止範囲が未評価である

判定 (real/refuted): real

根拠 (file:line):

- fresh qstat が QUE/HLD を返した直後に job が自然終了し、qdel が「対象なし」で非ゼロを返す競合では、実際の job は既に不在でも `job_may_remain=True` となる。[dispatch_compute.py:999](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:999)、[dispatch_compute.py:1241](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1241)
- malformed file、directory、symlink も hold とするため、孤児とは無関係な path residue でも全 dispatch が停止する。[s2-plan.md:75](/home/SFC/tanab/.claude/jobs/610dedfd/tmp/wave-t403/s2-plan.md:75)
- 自動解除がなく、最初の record を永久保存するため、この false positive は一 invocation の拒否ではなく手動解除まで受理集合全体を空にする。

成果物影響 1 行: 誤った成果物を受理する方向ではないが、変異台帳・wrapper・proof が一切生成されず、正当な acceptance run 全体が手動復旧まで拒否される。

推奨対処: 安全側の hold 自体は維持し、false positive を理由に署名を緩めない。request ID、qdel stderr、作成原因を必ず保存し、人手解除時に検証可能にする。

# 所見 7: 提案テストは false negative を固定し、producer-consumer の受理集合を検証しない

判定 (real/refuted): real

根拠 (file:line):

- 提案テストは `request-absent` と `terminal-history-conflict` で hold が立たないことを正解として固定する。[s2-plan.md:327](/home/SFC/tanab/.claude/jobs/610dedfd/tmp/wave-t403/s2-plan.md:327) 前者は所見 1 の既存「job may remain」経路と矛盾する。
- `cleanup-claimed` と `gate-not-evaluated` は helper の正常 return reason ではなく過渡状態である。[dispatch_compute.py:1064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1064)、[dispatch_compute.py:1434](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1434) それらを truth-table helper に直接渡すテストは、実際に latch codeへ到達することを証明しない。
- テスト一覧には qsub 受理直後の kill、5 秒対90秒 cleanup、hold write OSError、check→restore、check→rename の interleaving がない。[s2-plan.md:318](/home/SFC/tanab/.claude/jobs/610dedfd/tmp/wave-t403/s2-plan.md:318)
- fan-out の最終受理は wrapper rc、terminal ledger、teardown 完了を検査するが [mutation_fanout_contract.py:1288](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_fanout_contract.py:1288)、hold が立たなかった expected-TIMEOUT 経路はその条件を満たしうる。

成果物影響 1 行: 提案テストが全緑でも、実受理集合には「孤児あり・holdなし・terminal ledger・teardown済み」が残り、変異 matrix と proof の検出力は増えない。

推奨対処: durable claim から wrapper/fan-out 受理までを通す状態機械テストを追加し、kill と filesystem fault を各遷移点へ注入する。少なくとも slow cleanup＋expected TIMEOUT の E2E を acceptance test にする。

# 所見 8: 「計算 job は独立 copy を読む」という反論は成立しない

判定 (real/refuted): refuted

根拠 (file:line):

- job script は login 側の `repo_root` を `REPO` と `DISPATCHER` に直接埋め込み、`cd "$REPO"` 後にその dispatcher を exec する。[dispatch_compute.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:439)、[dispatch_compute.py:467](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:467)、[dispatch_compute.py:502](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:502)
- request にも同じ repo path を保存し [dispatch_compute.py:1380](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1380)、計算ノード側 `_job_run` はそれを resolve、chdir して、checkout 内の `tools/run_tests.py` を cwd=repo で起動する。[dispatch_compute.py:573](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:573)、[dispatch_compute.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:594)
- `run_tests.py` も自身の checkout を `_REPO` として `sys.path` に入れ、pytest をその cwd で起動する。[run_tests.py:53](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/run_tests.py:53)、[run_tests.py:1898](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/run_tests.py:1898)
- rsync、snapshot、job-local source copy はない。

成果物影響 1 行: 親 brief の因果前提は維持され、source 復元・次変異・checkout 削除はいずれも台帳と実行 bytes の対応を直接壊しうる。

推奨対処: hold 修正とは別案として、job ごとの immutable source snapshot を将来候補にする。現 wave では少なくとも live checkout 依存を受入テストで固定する。

# 所見 9: 「実 receipt 135 件」は保存成功条件付き標本で、全経路の一般化には使えない

判定 (real/refuted): real

根拠 (file:line):

- 指定された二 root を現在 read-only 再集計すると、v2 JSON は 136 fileだった。brief の 124＋8＋2＋1という135行は再現するが、これに setup receipt 1 件が加わる。
- 除外された [receipt-setup-53cdbd5c40a64294.json:1](/work/1/SFC/tanab/izanagi/output/pegasus-dispatch/receipt-setup-53cdbd5c40a64294.json:1) は `BrokenPipeError` の infra receipt で qdel fieldを持たない。孤児 receipt と同時刻・同じ test argvなので同一 invocation由来の可能性が高いが、除外・重複排除規則が brief にない。
- setup receipt は outer catch が独立に生成する。[dispatch_compute.py:1883](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/pegasus/dispatch_compute.py:1883) また、receipt 前の SIGKILL はそもそも標本へ現れない。したがって「欠落 field＝孤児なし」は survivorship bias を含む。
- 135 件中 124 件が正常 child、実 orphan は1件だけで、ID不明、cleanup 中断、hold write失敗などの署名一般化を支えない。
- 過去 receipt の無条件走査を避ける結論自体は妥当である。exact root は ignore 済み [`.gitignore:26`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/.gitignore:26) だが、evidence の再実体化で古い receipt が root に戻る。[mutation_worktree.py:616](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t403-orphan-job-hold/tools/mutation_worktree.py:616) ただしこれは「未解決 claim の索引」まで禁止する根拠ではない。

成果物影響 1 行: 標本外の crash 経路を「孤児なし」と一般化すると hold も停止 ledger も生成されず、受理 matrix と proof が未観測実行を除外できない。

推奨対処: 「全過去 receipt を走査しない」を「qsub 前に作成した未解決 claim だけを照合する」へ狭める。claim は terminal tombstoneとの対応で解決し、通常 receipt の field 欠落を安全証拠にしない。

## 総括

P1 は現行テストが `job_may_remain=True` と認める `request-absent` 経路で hold を抑止しており、署名そのものに具体的 false negative がある。  
さらに qsub 受理前後の未武装窓と、harness の「5 秒 SIGKILL 対 90 秒 cleanup」により、署名へ到達しない孤児経路が残る。  
単一の存在 file は復元・evidence rename・teardown と排他されず、再検査を増やしても correctness boundary は閉じない。  
一方、計算 job が login 側 checkout を直接読むという親 brief の因果前提は確認できた。  
現プランのまま段 4 で採用すべきでなく、qsub 前 durable claim と checkout lifecycle の排他を scope に戻す必要がある。