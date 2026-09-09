## 総括

結論は **条件付き GO**。1 job・1 node 直列で、狭く「この 1 campaign で到達した gate 入力」を記録する方針は成立する。ただし段 2 plan のままでは、次の運用穴が残る。

- 実装面差分 0 は成立しうるが、repo の tracked 差分 0 とは別である。receipt と台帳 fragment を commit するなら受入全走は免除できない。
- 4 点 bundle だけでは、共有 admission 状態、外部 checkpoint、campaign claim の参照が閉じない。
- clean-scan は別 worktree の `output/` を走査しない。一方、git common dir 内の attempt registry は全 worktree で共有され、次 run と衝突する。
- all-null、`job-result.json` 欠落、`failure.json` の弱さは plan が事後検出できる。早期全滅検査と停止動作は未完成である。
- 1 run は到達実証には足りるが、`DW-O13` の時間分布や未発火分岐には足りない。限界文言は過大主張を防ぐが、未観測を観測済みにはしない。
- 待ち手の既定 6 時間は、queue 待ち込みで walltime 10 時間の job より短い。request ID と scheduler accounting を使う待機へ具体化が必要である。

pytest、Pegasus 投入、qstat は実行していない。静的読解、grep、既存 submit-tree と共有 admission root の読み取りだけで判定した。

## 所見

**B-1 — refuted: 「実装面差分 0 は成立しない」という攻撃は退けられる。**

D95 の実装面は、`orchestrator/`、`tools/` 等の非 Markdown/RST、および場所を問わない Python・shell・C/C++ 等で決まる。docs-only commit は対象外である。`docs/decisions.md:4244-4253`。計画上の tracked 成果物は `output/insights/.../README.md` と `docs/spool/` fragment であり、非 `.md` を `orchestrator/` へ置く計画はない。`s1-brief.md:67-70`、`out-s2-plan.md:157-162`。

実 submit-tree の現況も、HEAD は `8fbcb70a...` のままで、dry-run の副作用は `?? output/env/pegasus/floor/attempts/submissions/228bc...` 以下だけだった。したがって、抽出器を `.py` 等として保存せず、run artifact を commit しなければ実装面差分 0 は維持できる。

**B-2 — real: tracked file 差分 0 と受入全走免除は成立しない。**

brief は receipt に加えて `docs/spool/` fragment を成果物とする。`s1-brief.md:67-70`。これらを wave branch へ残すなら tracked file の追加である。`DW-S07` も insight と fragment を branch へ commit するよう要求する。`docs/dev-wave/core.md:103-108`。

`DW-S04` が免除するのは変異 matrix だけで、受入全走は免除しない。`docs/dev-wave/core.md:89-97`。段 2 plan には受入全走の工程がなく、receipt を commit するかどうか自体を未解決に残している。`out-s2-plan.md:202-207`。よって次のどちらかを先に確定すべきである。

- repo に receipt と spool を commitする: 実装面差分 0、変異 matrix 免除、受入全走は必須。
- repo へ一切 commit しない: tracked 差分 0 だが、brief の成果物形と dev-wave 記録契約を満たさない。

**B-3 — real: P1-2 は producer 不要まで支持できるが、抽出変換の保存が不足する。**

plan は一回限りの strict Python readerで値を集約するとするが、保存するのは値、source hash、集約説明だけである。`out-s2-plan.md:128-152`。抽出コード、argv、interpreter、rc、stdout hash が残らなければ、raw bundle から同じ min/max・distinct・join を再生成した手順を監査できない。

新しい tracked producer は不要だが、最低限次を README 内へ埋め込めば P1-2 を保ったまま閉じられる。

- 実際に使用した here-document 全文。
- その UTF-8 bytes の SHA-256。
- interpreter realpath/version、cwd、argv、rc。
- extractor stdout の SHA-256。
- 読んだ各 artifact の bundle 内相対 path と SHA-256。

**B-4 — real: plan の bundle は改善されているが、現行 writer の全参照をまだ閉じていない。**

W-2 は run directory、binary store、submission receipt、job staging の 4 点を要求し、run directory だけでは `store_path` が dangling になると明記する。`docs/phase3-8b-restart-runbook.md:252-260`。plan は共有 admission snapshot を追加している点では正しい。`out-s2-plan.md:100-102`。

しかし現行 wrapper はさらに次を作る。

- submission directory 全体。`scheduler.stdout`、`scheduler.stderr`、preflight、qsub raw、payload を含む。`tools/pegasus/submit_floor.sh:632-650`。
- repo 外の checkpoint。driver はそこへ `run_dir` と `journal_path` を結ぶ `run-linked` 行を書く。`orchestrator/campaign/s8b_floor_campaign.py:7604-7618`。
- submit-tree の `output/claims/` に campaign claim。
- git common dir 内の cell claim、consumed marker、attempt ledger、classification/external/terminal evidence、attempt registry。

submit-tree を消すと、run directory、binary store、submission directory、job staging、campaign claim、hydrate 済み third-party staging が失われる。外部 checkpoint と共有 admission root は消えないが、将来追記されるため、その時点の bytes を保存しなければ receipt の参照が不変にならない。

**B-5 — refuted: 別 worktree の raw `output/` が common dir 経由で clean-scan に混入することはない。**

clean-scan の列挙は、指定された repo root での `git ls-files -s` と `git ls-files --others --exclude-standard` である。`orchestrator/campaign/s8b_holdout_freeze.py:352-385`。git common dir 自体を再帰走査しない。

したがって、submit-tree A に残った untracked `output/env/.../result.json` は、別 worktree B の clean-scan には現れない。汚染するのは次の場合である。

- 同じ submit-tree A から次の official job を起動する。
- raw result を commitし、その commit を checkout した worktreeから起動する。

plan の「次の official run は止まる」は、同じ worktreeまたは raw artifactを含む commitに限定して書くべきである。`out-s2-plan.md:163-165`。

**B-6 — real: common dir の相互作用は clean-scan ではなく attempt registry にある。**

共有 root は明示的に git common dir から導出され、全 worktree で同一である。`orchestrator/campaign/s8b_holdout_admission.py:620-637`。v2 registry path は `{freeze_sha256}/{protocol_sha256}/registry.jsonl` に固定される。`orchestrator/campaign/s8b_attempt_profile.py:530-537`。同じ slot の 2 回目の start は `slot was reserved more than once` で拒否される。`orchestrator/campaign/attempt_registry_core.py:1232-1235`。

consult 時点の共有 root はすでに非空で、静的観測値は次だった。

- claims 36 件。
- consumed marker 228 件。
- measurement-generation claims 36 件。
- measurement-generation-consumed 288 件。
- attempt ledger 516 行。
- attempt registry 1 世代。

このため、bundle は「after snapshot」だけでは C3b 由来行を帰属できない。投入直前の path・size・hash・行数 manifestと、完走後の同 manifestとの差分が必要である。また最初の official run完了後、同じ freeze/protocol の単純な fresh 再投入は別 worktreeからでも安価にはできない。新しい sanctioned measurement/protocol generationが必要になる可能性がある。

**B-7 — refuted: all-null、job-result 欠落、failure.json の 3 穴は plan の事後停止条件で検出できる。**

wrapper は driver rc=0 後に、全 holdoutの `scale_ref`、`scalar_alt`、全 pair が有限実数であることを検査し、欠損なら rc=3 に置き換える。`tools/pegasus/floor_campaign.sh:1232-1351`。plan もこの変換が見えなければ停止するとしている。`out-s2-plan.md:181-183`。

`job-result.json` writer 失敗は driver rcを変更せず、driver成功なら wrapper rc=0になりうる。`tools/pegasus/floor_campaign.sh:1355-1400`。plan は欠落・不正を停止条件にしている。`out-s2-plan.md:183`。

`failure.json` は最初の失敗だけ、writer失敗を握る best-effort である。`tools/pegasus/floor_campaign.sh:368-408`。plan は不在を成功証拠にしない。`out-s2-plan.md:184`。この 3 点は、実 artifactを独立再検査する限り閉じている。

**B-8 — real: 早期全滅検査は検出方法も停止動作も未確定である。**

plan は「journal が現れたら最初の数 session」を見るだけで、対象 run の特定方法、「数」の値、全滅述語を定めていない。`out-s2-plan.md:93-98`。実際には外部 checkpoint の `run-linked` 行から exact `journal_path` を得られる。session 行には `valid`、`excluded_reason`、`exec_failures`、probeがある。`orchestrator/campaign/s8b_floor_campaign.py:6363-6380`。

また plan は RUN 中 jobを独断で qdelせず報告するとする。`out-s2-plan.md:180-181`。これは receipt の採用停止にはなるが、runbook の「残り10時間を捨てずに止める」にはならない。`docs/phase3-8b-restart-runbook.md:229-234`。一方、観測後の qdel は共有 registryに消費済み slotを残し、fresh再投入を塞ぎうる。`docs/phase3-8b-restart-runbook.md:310-344`。

したがって最低限、例えば「先頭3件の completed session がすべて `valid=false` かつ同じ infrastructure型 exclusion」のように検出述語を固定し、発火時の動作を次から裁定する必要がある。

- 採用だけ停止し、jobは終端まで走らせる。
- exact request IDを再照合して qdelし、当該 generationが再利用不能になる可能性を受容する。

**B-9 — refuted: P1-4 の 1 job・1 node直列は、この 1 campaign には正しい。**

job body は `#PBS -b 1` である。`tools/pegasus/floor_campaign.sh:2-5`。floor protocol は12セルを同一 campaign内の scheduleどおり直列・単一テナントで測る。`docs/pegasus-runbook.md:1357-1362`。セルを複数ノードへ分割すると protocol変更になるため、運用上の短縮策として採れない。

ただし「1 jobが通った」から他ノード、他時点、他protocolでも通るとは言えない。これは P1-4 の反証ではなく、主張範囲の制限である。

**B-10 — real: 限界文言は誠実だが、DW-O13 全体の充足にはならない。**

`DW-O13` は、実値到達性に加えて時間予算を「実測分布の maxへの倍率」で決め、母集合とregime一致を記録する。`docs/dev-wave/operations.md:98-107`。1 official jobの campaign Elapseは1点なので、campaign間分布の maxではない。pilotの2894秒は別 mode・別 commitの観測である。`output/insights/2026-08-25_t1431-floor-pilot-values/README.md:12-28`。

plan の限界文言は狭い1-run receiptとしては十分だが、未発火retry、competing branch、将来campaignの時間幅を充足済みに変えない。`out-s2-plan.md:153-155`。

**B-11 — real: 待ち設計は既定値と完了材料が不足する。**

compute waiterの既定上限は21600秒で、queue待ち、実行、会計追記を全部含む。`docs/pegasus-runbook.md:1221-1227`。floor jobのscheduler walltimeは36000秒である。`tools/pegasus/floor_campaign.sh:4-17`。planが単に waiterを使うだけでは、正常なRUN中に6時間で timeoutしうる。

また floor jobには最終 done-markerがない。`job-result.json` は `exit` より前に書かれ、失敗時にも作られうる。`tools/pegasus/floor_campaign.sh:1355-1400`。scheduler completionの権威は request固有の `scheduler.stderr` にある `Ended Request Time:` 行へ寄せるべきである。

## 退避 bundle の構成案

| bundle 内 path | 入れるもの | 理由 |
|---|---|---|
| `bundle-manifest.json` | schema、RID、nonce、source commit、script hash、各fileの相対path・size・mode・SHA-256、symlink拒否結果 | bundle全体の閉包 |
| `run-dir/` | `manifest.json`、`journal.jsonl`、`result.json`、`result.md`、`launch_certificate.json` と許可された付帯file | campaign本体 |
| `binaries/<sha>/` | manifest/resultの全 `store_path` が指すcontent-addressed directory | dangling防止 |
| `submission/<nonce>/` | directory全体。submit receiptだけでなくpre-submit、qsub raw、queue/quota raw、scheduler stdout/stderr、payload、evidence-index-status | 投入とscheduler終端の一次資料 |
| `job-staging/<RID>/` | `job-result.json`、`failure.json` があればそのまま、driver stdout/stderr、checkpoint、toolchain/dependency/build receiptとlog | wrapperとdriverの分離 |
| `external-checkpoint/` | `/work/1/SFC/tanab/izanagi-job-evidence/pegasus/<RID>/<nonce>/` と対応index/status | 早期run-linkとcrash位置 |
| `campaign-claim/` | submit-tree `output/claims/` の当該campaign claim | 単独campaign leaseの証拠 |
| `shared-admission/before-manifest.json` | 投入直前の共有root全pathのsize/hash/行数 | 既存stateとの分離 |
| `shared-admission/after-manifest.json` | job終端後の同じmanifest | C3b差分の帰属 |
| `shared-admission/delta/` | 新規・変更file。registryはresult `row_count`までのexact prefixを独立fileとして保存し、terminal/external/classification evidence、marker、ledger該当行を収録 | 後続追記後もresult proofを再生 |
| `extractor/` | READMEへ埋めた抽出sourceの複製、source hash、argv、interpreter、rc、stdout/stderr hash | P1-2をproducer新設なしで再現可能にする |
| `receipt/README.md` | repoへ置くreceiptとbyte同一のcopy | tracked記録とraw bundleの結節 |

退避は source と copy の各hash一致を確認してから submit-treeを廃棄する。full shared rootの単純コピーだけでなく、before/after差分とresultが束縛するexact prefixを残すべきである。

## 1 run で言えること・言えないこと

| 述語・主張 | 1 runで言えること | 言えないこと | 最小追加 |
|---|---|---|---|
| result v5とprefix proof | exact commit/env/mode/freeze/protocolでv5 producer、7-key proof、live registry prefixが到達した | 他generation、将来commitでも到達する | C3bには追加不要 |
| planned ordinal | 実際に現れた `attempt_ordinal=0`、`measurement_ordinal=0`、`retry_ordinal=null` の集合と件数 | retry非nullがproductionで到達すること | 通常runを増やしてもretry発火は保証不能。未観測と明記する |
| retry ordinal | 発火した場合だけ実値とjoinを示せる | retry 1、2の到達可能性 | 自然発火待ちでは有限N保証なし。別のproduction-representative canary設計が必要 |
| clean probeとmarker | `competing=false` sessionについてmarker存在とterminal化を示せる | `competing=true`、marker不在側 | official runへ競合を故意に入れない。未観測とする |
| all-null拒否 | このrunが有限floorを持ちwrapper検査を通った | all-null負例が実機wrapperでrc=3になること | C3bの成功receiptには追加不要。負例実証は別canary |
| session所要 | 同一run内の多数sessionについて標本分布とmaxを示せる | campaign間・node間・日間の尾 | 同一regimeのwhole campaignを追加 |
| campaign Elapse | この1jobが何秒で終わったか、36000秒内に収まったこと | campaign所要分布のmax、将来の上限 | **+1 official generation、計2本**で初めて非単一点のcross-run maxと再現差を言える。ただし尾のboundではない |
| campaign所要の粗い安定性 | 1本では不可 | 一回だけ速い・遅い可能性 | **+2 official generation、計3本**で一回性外れの兆候と3標本maxを言える。統計的上限ではない |
| 1 node直列の可用性 | このallocationでsanctioned経路が完走した | 全Pegasus nodeで完走する | C3bの狭い目的には追加不要 |

従って、追加runを払わない最小案は「C3bは時間予算を新設・改訂しない。1-run到達receiptだけを供給する」と明記することである。`DW-O13` の時間予算まで満たしたと主張するなら最低でも計2本が必要だが、B-6のとおり同じfreeze/protocol registryをそのまま再利用できないため、追加1本は単純な再投入ではない。

## 待ち設計の具体案

job名は使わず、submit receiptのexact request IDだけを使う。`qstat` は存在しないIDでもrc=0を返し、終了後5〜6秒で消える。`docs/pegasus-runbook.md:180-192`。

投入直後の生存確認は次の形にする。

```bash
RID='988492.nqsv'
REQUEST_VIEW=$(qstat -f "$RID" 2>&1)

case "$REQUEST_VIEW" in
  *"does not exist"*)
    echo "request is not visible; do not resubmit"
    exit 70
    ;;
  *"Request ID: $RID"*)
    printf '%s\n' "$REQUEST_VIEW"
    ;;
  *)
    echo "request identity is indeterminate; do not resubmit"
    exit 70
    ;;
esac

qstat -J -f "$RID"
```

`qstat -J -f` の直後の `does not exist` はjob record作成前の窓でも起こるため、それだけで消滅判定しない。request単位の `qstat -f` と組み合わせる。表形式のjob名列は8文字で切れるため、`grep floor_ca` のような判定はしない。

早期session検査では、nonceとRIDから外部checkpointを一意に決める。

```bash
NONCE='<submit-receipt.json の nonce>'
CHECKPOINT="/work/1/SFC/tanab/izanagi-job-evidence/pegasus/${RID#0:}/$NONCE/checkpoint.jsonl"
```

checkpointのexact job ID・nonceを検査し、`transition="run-linked"` 行の `journal_path` を採る。最初の3件を閾値とするなら、その値を投入前に固定し、各 `event="session"` の `valid`、`excluded_reason`、`exec_failures`、`probe_before`、`probe_after` を読む。3件未満は判定保留、3件すべてinvalidでも自動qdelはせず、B-8の裁定へ送る。

完了待ちは、floor jobに正式done-markerがないため、scheduler accounting側だけを真にする。次はqueue待ち上限12時間を運用上の例として明示した形である。

```bash
SUBMISSION_DIR='<exact nonce の submission directory>'
WAIT_SENTINEL="$SUBMISSION_DIR/no-floor-done-marker.$RID"
WAIT_RECEIPT='/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t1851-unit-c3b/compute-receipt.json'

test ! -e "$WAIT_SENTINEL" || exit 2

QUEUE_WAIT_BUDGET_S=43200
JOB_WALLTIME_S=36000
ACCOUNTING_GRACE_S=300
MAX_WAIT_S=$((QUEUE_WAIT_BUDGET_S + JOB_WALLTIME_S + ACCOUNTING_GRACE_S))

python3.10 tools/dev_wave_wait.py compute \
  --request-id "$RID" \
  --done-file "$WAIT_SENTINEL" \
  --accounting-file "$SUBMISSION_DIR/scheduler.stderr" \
  --max-wait-seconds "$MAX_WAIT_S" \
  --receipt-file "$WAIT_RECEIPT"
```

成功後は compute receipt が `done_evidence=false`、`accounting_evidence=true` であることを要求する。その後に別々に次を検査する。

- `job-result.json` が実在しstrict JSONとして正しい。
- `driver_rc=0`、`mode=official`、source/script/nonce/reservationが一致。
- driver summaryがexact `{"status","run_dir"}`。
- resultがv5で、有限floorとprefix proofを持つ。
- `failure.json` の不在を成功根拠にしない。
- scheduler stderrとsubmission directoryをbundleへ入れてから退避する。

## 未解決の問い

- receiptとspool fragmentをbranchへcommitし、受入全走を行う方針で確定するか。それともrepo無変更を優先してdev-wave記録契約から外すか。
- early全滅の閾値を何session、どのexact述語にするか。
- early全滅時、RUN jobをqdelする権限と、消費済みregistry generationを失う費用を受容するか。
- queue待ちの運用上限を12時間とするか。別値なら `MAX_WAIT_S` を投入前に固定する必要がある。
- accounting-only待ちのための不存在sentinel運用を認めるか。認めないならjob bodyへfinal done-markerを追加する必要があり、実装面差分0ではなくなる。
- 共有 admission root のbefore/after snapshotを取る間、他writer不在をどの証拠で固定するか。
- `DW-O13` を狭い到達receiptまでとするか。campaign時間分布まで要求するなら、新しいsanctioned protocol/measurement generationを用意して追加1本を走らせる必要がある。