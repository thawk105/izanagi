## Blocker

### B1 — staging recovery は「再開」ではなく永続停止を作る

- **file:line**: `out/s2-plan-v2.md:307-318`, `docs/pegasus-runbook.md:296-298`
- **筋**: plan は `generation-NNNNNN.staging` を破損時に削除せず、series reader でも staging 残留を拒否する。一度 pilot bytes が欠落・破損する crash が起きると、次回以降は recovery 不能のまま永続停止する。また `renameat2(RENAME_NOREPLACE)` は `/work` で使えないと runbook に明記されている。
- **壊れ方**: `mkdir → init_pilot → pilot fsync → staging dir fsync → rename` の各境界で kill すると、valid staging は復旧できても、partial staging は人手削除まで全自動 start を拒否する。さらに fsync 対象の「directory entry」が staging parent なのか publish 後の series base なのか不明で、rename 後の正式 entry の durability も保証されない。
- **検出案**: 各境界へ kill を注入し、再起動した新プロセスで `validate-series` と automatic start を実行する。partial staging の quarantine/修復/明示 cleanup がなく、何回再起動しても同じ diagnostic になるケースを fail にする。
- **重大度**: blocker

### B2 — dispatch/bounded の sidecar payload は、可視性と durability の両方が未証明

- **file:line**: `out/s2-plan-v2.md:320-351`, `tools/pegasus/dispatch_compute.py:76-90,509-580,656-660,1507-1514`, `tools/task_runs/pytest_stats.py:87-131`, `ledger.py:891-987`, `docs/pegasus-runbook.md:258-268`
- **筋**: `/work` が compute node から見えることは runbook の実測で支持されるが、login node と compute node が同じ directory entry・inode・lock/fsync semantics を共有することまでは示されていない。既存 selfcheck も同一 node 内の fork しか検査しない。さらに sidecar writer は file を fsync するだけで親 directory を fsync しない。
- **壊れ方**: compute 側で sidecar を書いても login 側から見えない、または crash 後に directory entry が消えると、plan は null metrics event と diagnostic に倒れる。しかしこれは B3 の「全経路で同じ counts/digest shape」を満たさない。現行 dispatch は allowlist、job script、`_job_run` の三箇所で sidecar を除去しており、どこか一箇所でも変更漏れがあれば同じ欠測になる。
- **検出案**: 実 compute job で login 側が作った capability file を compute 側が `lstat/read` し、compute 側の write を login 側が `lstat/read` する往復 probe を追加する。device/inode/path、mode、O_EXCL、fsync 後の再読込、cleanup 前の parent read を確認する。allowlist/job-script/`_job_run` の各境界を個別に落とす mutation も必要。
- **重大度**: blocker

### B3 — B4 の「全 outcome 記録」は task-run/v1 では正直に表現できない

- **file:line**: `out/s2-plan-v2.md:337-351,353-381,507-514`, `tools/run_tests.py:1396-1508,1521-1574,953-970`, `tools/task_runs/schema.py:314-324,436-449`, `tools/pegasus/dispatch_compute.py:188-220,1516-1530,2145-2181`
- **筋**: plan は `CHILD_RC`、`CAP_OOM`、`DISPATCH_INFRA`、timeout、setup failure を記録しつつ、schema は v1 のまま event field を増やさないとしている。だが v1 の `test_run` には route、outcome、`child_started`、infra reason がない。brief の P3 根拠である「direct/dispatch/scope を別 field で区別する予定」も、plan v2 では実装先が示されていない。
- **壊れ方**: pytest child 未起動の setup failure・queue failure・attestation failureを `test_run` として追加すれば、B5 の「実際に child を起動した wrapper invocation のみ」という主張に反する。追加しなければ B4 の全 outcome 記録に反する。dispatch 側が持つ `child_started` は `_invoke_dispatch()` が integer rc に潰しており、setup failure は現状 `child_started=True` に正規化される。また bounded scope は `process.wait()` に timeout がなく、plan の timeout 契約自体が未実装である。
- **検出案**: setup failure、queue timeout、attestation failure、CAP_OOM、child未起動、child負 rc、child hang をそれぞれ再現し、(a) event の意味が「pytest実行」と矛盾しない、(b) route/outcomeが復元可能、(c) task_end が一度だけ、を同時に検査する。
- **重大度**: blocker

### B4 — preflight reject と recording boundary の順序が経路間で不一致

- **file:line**: `out/s2-plan-v2.md:142-160,383-405,709-726`, `tools/run_tests.py:1757-1830,1832-1840`
- **筋**: plan は gate/preflight reject を被覆分母から除外し、child 実行後に lazy session を作る方針だが、現行 main では login local bounded scope が preflight より先に起動される。
- **壊れ方**: local admission が通る経路では、unstaged deletion・ruleops・submodule preflight が reject する状態でも `_launch_local_scope()` が先に child を起動する。これでは「preflight reject は未被覆」という線引きが経路依存になり、reject されるべき invocation が記録対象になり得る。逆に session を scope 内で作ると、同じ invocation の中で child 起動前に記録を開始する別の不整合が生じる。
- **検出案**: preflight 各関数を reject に差し替え、login local、login dispatch、compute direct、bounded、force-dispatchで child 起動有無と task/event 有無を比較する。全経路で gate → preflight → child start → recording の境界を同じにできなければ fail。
- **重大度**: blocker

## Must-fix

### M1 — series lock の適用範囲と初期作成競合を実装契約に固定する

- **file:line**: `out/s2-plan-v2.md:280-291`, `tools/task_runs/ledger.py:527-563`, `tools/task_runs/cli.py:197-216`
- **筋**: plan 上は discovery から `start_run()` まで直列化すれば 20 並行 start の 11 件目以降を拒否できる。ただし lock は generation manager 側にしかなく、低レベル `start_run()` は直接呼べる。series base/lock/generation がまだ存在しない最初の同時 start の lock bootstrap 手順も具体化されていない。
- **壊れ方**: auto caller が全て manager を通る場合だけ成立し、古い Python caller や未更新経路が managed generation を直接触ると series lock を迂回する。空 series の同時初期化では lock file 自体の作成競合が残る。
- **検出案**: generationなしの空 sibling に20 processを同時投入し、さらに managerを経由しない `start_run()`、CLI、lock作成途中 killを混ぜる。最終的に generation数、task directory数、cap理由、series reportを検査する。
- **重大度**: must-fix

### M2 — managed generation の CLI 拒否条件が未定義

- **file:line**: `out/s2-plan-v2.md:595-618`, `tools/task_runs/cli.py:40-55,197-239`
- **筋**: plan は managed generation への `init/start/event/finish` を CLI から拒否するとするが、「managed」の判定方法、symlink経由、`--root` が series base・generation root・無関係な同名 directory の場合の区別が書かれていない。
- **壊れ方**: 名前の正規表現だけなら無関係な `generation-000001` まで拒否し、逆に symlink・相対 path・別 series 経由で managed root への write を許す可能性がある。拒否が bytes 作成前に行われることも、既存 CLI の全 write commandで証明されていない。
- **検出案**: managed root、series base、checkout-local root、同名の無関係 root、symlink、relative path、環境変数指定を全組合せで試し、拒否前の作成物が0 byteであることを確認する。
- **重大度**: must-fix

### M3 — signal 契約の監査範囲が狭すぎる

- **file:line**: `out/s2-plan-v2.md:540-566`, `tools/run_tests.py:953-970,1044-1077,1099-1145`, `tools/pegasus/dispatch_compute.py:2145-2181`
- **筋**: plan は bootstrap/record/finish の signal 再送出を挙げるが、既存コードには `KeyboardInterrupt` を捕捉する admission、dispatch、scope bind/release、queue fallback、dispatcher setup の経路が残る。
- **壊れ方**: `KeyboardInterrupt` や `SystemExit` が infra rc・diagnosticへ畳まれ、child rcや task lifecycle を変える。D66 の「signals never swallowed」に反する。
- **検出案**: admission、queue state、dispatcher setup、scope bind/release、sidecar read、record append、finishの各 call siteへ signal injectionし、signalが再送出され、偽の task_end/event が追加されないことを確認する。
- **重大度**: must-fix

### M4 — 被覆主張は改善されたが、分母と “event” の定義がまだ曖昧

- **file:line**: `brief.md:36-57,84-88`, `out/s2-plan-v2.md:383-405,795-813`, `output/task-runs/README.md:68-79,91-116`
- **筋**: brief の現況は主に手動 ID 経路の既存テストと静的 file count に基づき、20並行、cross-node、crash、非 `CHILD_RC` の実測ではない。plan は raw pytest/mutation local/別 clone/gate/preflight reject を除外しているが、infra eventを test event と数えるか、child未起動を coverage対象とするかがB3/B4と衝突している。
- **壊れ方**: “`run_tests.py` 経由のみ被覆”が wrapper invocation 全体の被覆に読まれ、記録不能 invocationを分母から黙って落とす。現行 README の「記録された event のみ」という下限契約を越える一般化になる。
- **検出案**: READMEに経路別の母集団を明記し、`child_started=true` の wrapper invocation、gate/preflight reject、raw pytest、mutation local、別 clone、infra/no-child を別集合として表にする。coverage率・欠測率を出さず、未記録を0件扱いしないことを静的検査する。
- **重大度**: must-fix

### M5 — 見積りは算術上は整合するが、未計上の必須作業がある

- **file:line**: `brief.md:49-57,143-154`, `out/s2-plan-v2.md:815-839`, `docs/decisions.md:9840-9847,10371-10375`
- **筋**: brief の320–505行から plan の455–663行への増加理由（generation、reader、transport、複数event、CLI、schema sync）は説明されており、142行上限を撤回した点は妥当。ただし、D205/D220の最小主義に照らすと、series reader・sidecar lease・managed CLIのような複雑性を残す一方、cross-node probe、dispatch outcome parser、child_started表現、bounded timeout、全 signal audit、partial staging処理がproduction見積りに明示されていない。
- **壊れ方**: 455–663行に収めるため、route/outcomeを捨てるか、staging/transportの安全性を省くか、診断を曖昧にする可能性が高い。逆に全要求を維持するなら、`run_tests.py:1396-1574` と dispatchの結果受け渡しだけで150–220行に収める見積りは楽観的。
- **検出案**: 実装前に「要求→関数→テスト→production diff」の対応表を作り、cross-node probe、timeout、child_started、partial staging cleanup/recovery、signal call siteを必須項目として追加する。削る候補と削った場合に失われる保証を明記する。
- **重大度**: must-fix

## 裁定へ返す候補

### R1 — v1 schemaを維持したまま B4 を要求するか

`test_run` に route/outcome/child_started を追加しないなら、no-child infraを task-run event として記録する契約は撤回し、diagnostic-onlyに限定する必要があります。逆にB4を維持するなら、task-run/v1 exact-field invariantとの衝突を明示して別schemaまたは既存eventの意味変更を裁定へ返すべきです。

### R2 — cross-node sidecar の保証水準

「共有 `/work` path を使う」ことと「login/compute間で payload 完全性を保証する」ことは別です。compute-side probe・directory fsync・read receiptまで実装するか、dispatch/boundedを今回の被覆対象から外して null metrics を許容するかを選ぶ必要があります。Q2(a)の記録先・改竄検出なしを再裁定する話ではありません。

### R3 — D205/D220に合わせた縮小案

安全性を維持する最小案は、series横断 reader・managed CLI write policy・複雑なsidecar leaseを削り、automatic `run_tests.py` の単一 generationと明示的な diagnosticに限定する方向です。ただし、その場合はB1/B2/B4の保証範囲も縮小してREADMEへ明記する必要があります。

## 実行経路の被覆表

| 経路 | plan v2 の意図 | 静的に確認できる実際の状態・未閉鎖点 |
|---|---|---|
| login direct | login nodeで wrapperを通り、preflight後に bounded child として記録 | 現行は local bounded child が preflight より先に起動する。child起動前のsession境界が不統一 |
| login → compute dispatch | parentがsessionを所有し、sidecarを sibling transport経由でcomputeへ渡し、parentが読む | `/work` の可視性はrunbookにあるが、cross-node durability/receipt未証明。現行dispatchはsidecarをallowlist/job/childで除去 |
| compute direct | compute node上の `run_tests.py` がauto sessionを作り、direct childのsidecarを読む | path/FS selfcheckは同一node内のみ。compute directの実FSで sibling transportを検証する手順なし |
| bounded scope | scope childはauto-off、parentがscope eventを記録。CAP_OOM後は同じtask-runへfallback event | 現行は `CHILD_RC` 以外で記録前return。timeoutも未定義。no-child outcomeをv1 eventへ正直に表せない |
| raw pytest | 記録対象外 | Q3に適合。wrapperを通らないためeventなし |
| mutation harness local mode | 記録対象外 | Q3に適合。`python -m pytest` local modeはuncovered |
| mutation harness dispatch mode | `run_tests.py --force-dispatch` 経由ならdispatch routeとして記録 | runbook上も `--force-dispatch` が必要。dispatch receipt、sidecar、child_startedの三者対応は未閉鎖 |
| linked worktree 並行 | git common dir由来の同一 sibling seriesを共有し、series lockでcapを一元化 | path共有の設計は整合するが、初期series作成、低レベルAPI直呼び、staging残留時の停止を未検証 |
| 別 clone | cloneごとに別 common dir・別 sibling series。cross-clone共有・集計はしない | Q3の未被覆境界として正直。ただし「全走行」や全clone分母の主張は不可 |

## 総括

NO-GO。blocker 4件、must-fix 5件。pytest・mutation・受入走行は未実施で、静的検査のみです。