## 共有木と並行競合

- **[refuted] `_ccbench_dir()` は primary checkout 固定ではない。** `buildcache.py` 自身の位置から outer repo を求め、`<その repo>/external/ccbench` を返すため、別 outer worktreeなら別パスになる。`orchestrator/campaign/buildcache.py:614-618`、`orchestrator/campaign/patchharness.py:266-269`。親 brief の「共有 submodule」は「同じ outer checkout 内では共有」が正確。
  - 成果物への影響: 別 worktree 間の直接衝突は通常ないが、同じ worktreeを使う複数 process は衝突する。

- **[real、plan の node-local clone で回避可能] sweep/repro は stock checkout ではなく base tree 自体へ patch する。** stock用 worktreeを作った後、sweep は `ccbench_dir`、repro は `_ccbench_dir()` に直接 `applied()` を掛ける。`backoff_sweep.py:359-365`、`backoff_repro.py:66-72`、`patchharness.py:247-263`。`checkout()` は base HEADを動かさないだけで、source側を隔離しない。`patchharness.py:345-372`。
  - 成果物への影響: planどおり driver別 node-local cloneを使えば primary treeは保護される。共有 treeへ誤って束縛すると gate/build入力が汚染される。

- **[real] flock は別ノード・別 `$TMPDIR` 間で共有されない。** lockは `realpath(sub)` のhashを `$TMPDIR` に置くだけである。`patchharness.py:113-134`。競合すると同一patchでは片方が失敗し、非重複patchでは合成状態が発生しうる。さらに cleanup は `git checkout -- .` なので、片方がもう片方のtracked変更まで消す。`patchharness.py:214-243`。planが親 brief のP3を撤回した判断は正しい。`s2-plan.md:251-259`。
  - 成果物への影響: 共有 treeで走らせると偽のroot、途中revert、dirty treeを生みうる。driver別cloneならこの競合は閉じる。

- **[real] 強制終了ではpatchとworktree metadataが残る。** revert/removeはPythonの`finally`だけである。`patchharness.py:260-263,370-383`。SIGKILLでは走らない。さらにplanはshellの`EXIT trap`を置きつつPythonを`exec`してよいとしているが、`exec`後はshellのEXIT trapは実行されない。`s2-plan.md:171-176`。
  - 成果物への影響: planではprimary treeではなく `/scr` のclone、patch、Git worktree登録、lock、cacheが残る。共有 treeで実行した場合はpatchそのものが残り、次runはdirty拒否になる。

## 偽の緑

- **[refuted] 実際に返ったgate赤を例外握り潰しで緑へ変える経路は、対象production関数にはない。** sweep helperは両腕を評価し、admission拒否なら必ず例外を投げる。`backoff_sweep.py:127-169`。reproとs1もその例外を捕捉しない。`backoff_repro.py:70-84`、`s1_direct_comparison.py:288-307`。planも例外時は`ok=False`を要求している。`s2-plan.md:144-155`。
  - 成果物への影響: exactに観測したcell/requestについて、gate赤がpayload上の緑へ付け替わる経路は見当たらない。

- **[real] s1の1 cellだけをdriver全体の緑とするのは偽の緑を作れる。** planはschedule上の最初の`BACKOFF_FIXED=-1` cellだけを選ぶ。`s2-plan.md:74-95`。しかし`prepare_cell()`はconfigurationごとに異なるpatch、quarantine、oracle処理を行い、その後でgateを呼ぶ。`s1_direct_comparison.py:803-921`。従って一つのroot materializationが緑でも、他configurationのinert requestは未測定である。
  - 成果物への影響: s1 JSONが緑でも、未測定configurationの赤を隠したままT-2329不要と誤結論しうる。

- **[real] sweepはscreening結果がabortでも`ok=True`になりうる。** `_run_screened_workload()`はabortを集計するだけでsummaryを返し、`run_workload()`もabortを表示してそのまま返す。`backoff_sweep.py:309-319,420-432`。probe runnerはcampaign IDだけを記録する予定で、summaryの`aborted`や`committed`を成功条件に含めていない。`s2-plan.md:144-151`。これは「post-gate失敗ならdriver全体false」というplan自身の記述と不一致。`s2-plan.md:277`。
  - 成果物への影響: gate record自体は本物でも、aborted campaignをdriver-level `ok=true, rc=0`として保存しうる。

- **[refuted] 0 request・0 recordでadmitted扱いにはならない。** s1 production helperはrequestなしなら空tupleを返すが、probeは実`BACKOFF_FIXED=-1` request、各腕1 record、対応admissionをすべて必須にする。`s1_direct_comparison.py:272-275`、`s2-plan.md:144-150`。
  - 成果物への影響: 選択cellにinert requestが無い場合は緑にできない。

- **[real] wave全体の「3 driverすべて揃った緑」を機械判定する設計がない。** PBSのsite、path、clone、submodule、容量preflightはPython probe起動前に行われる。`s2-plan.md:167-176`。そこで失敗したdriverはJSONを一件も作らないが、`afterany`で後続は進む。exact 3 filesとdriver集合を検証するaggregate stepはplanにない。
  - 成果物への影響: 2件の緑と1件の欠落を、利用者が3件完了と取り違える余地が残る。

## 成果物の汚染

- **[refuted、条件付き] campaign layoutとWALの既存root汚染はscratch束縛で防げる。** official rootは絶対path、`..`、symlink component、Git祖先、uid、worktree containerを検査し、未指定時のrepo fallbackも拒否する。`layout.py:323-367,412-458`。`$TMPDIR`直下のclone外 siblingを`IZANAGI_OFFICIAL_OUTPUT_ROOT`へ渡せば有効である。clone内の`output/`を渡すとGit祖先検査で正しく拒否される。
  - 成果物への影響: 正常cleanup時はsweep campaign、WAL、lock、variant、reportはscratchだけ。`exec`または強制終了時はscratchに残る。

- **[real] build cacheの置き場所についてplanの表が不正確。** legacy `build()`の既定cacheはrepo/outputではなく`<ccbench source>/build-variants`である。`buildcache.py:3142-3149`。s1は`<node-local repo>/output/s1-build-cache`を返すが、`prepare_cell()`だけならbuildしない。`s1_direct_comparison.py:815-816,928-933`。
  - 成果物への影響: sweepのbinary、admission sidecar、staging残骸はnode-local `external/ccbench`配下へ書かれる。clone隔離は効くが、cleanup失敗時の残存先をplanが取り違えている。

- **[refuted] s1 session ledgerと予算台帳はdirect `prepare_cell()`では進まない。** ledger、budget、condition receiptの永続化は`run_role()`側にある。`s1_direct_comparison.py:988-1080,1190-1202,1275-1287`。planは`run_role()`を呼ばない。
  - 成果物への影響: session WAL、`time_ledger.json`、review receiptは作られず、freezeもread-onlyになる。

- **[real] create-only JSON writerはatomicでもdurableでもない。** planは最終pathを`open("x")`して直接書く。`s2-plan.md:124-125`。write途中のkill、ENOSPC、NFS障害では0 byteまたは途中JSONが残り、同じattemptへの再走は`EEXIST`で修復不能になる。fsync、temporary file、完成時のcreate-only publishも設計されていない。
  - 成果物への影響: 壊れた証拠fileが専用attempt namespaceを占有し、再測結果を保存できなくなる。

- **[real] official output root検査は最終evidenceを保護しない。** campaign rootの検査は`campaign_layout()`経由だけである。`layout.py:248-251`。最終JSONはprobe独自の`--output` writerで、briefが要求する先はrepo内`output/insights/...`である。`brief.md:18-20`。
  - 成果物への影響: 最終JSONは意図的なrepo-local fileになる。Git ignore状態次第ではuntrackedとして現れ、layoutのGit祖先・symlink検査は適用されない。

- **[real] PBS管理のstdout/stderrが書込先一覧から漏れている。** probeはstdoutへJSONを出すが、PBS側の`-o`/`-e`またはsubmission時overrideがplanにない。`s2-plan.md:155,163-176`。既定動作なら`PBS_O_WORKDIR`へjob stdout/stderr fileが作られる。
  - 成果物への影響: repo worktreeをsubmission directoryにすると、evidence JSON以外の`.o*`/`.e*`がrepo内へ残りうる。「永続書込はdriver JSONだけ」という主張は成立しない。

## 外乱

- **[real] driver間を別jobにするとnode、toolchain、network条件が揃わない。** `afterany`は順序だけを保証し、同一nodeを保証しない。compute siteではcompiler名が単に`gcc`/`g++`へなる。`buildcache.py:1838-1842`。planのJSON項目にはhostname、compiler full manifest、network状態がない。`s2-plan.md:133-155,178-184`。
  - 成果物への影響: driver差として記録された緑/赤が、node imageやcompiler version差だった可能性を除けない。

- **[real] single-tenant検査は瞬間検査で、測定区間全体を保証しない。** sweepは冒頭の検査後にsite解決、calibration、toolchain、FetchContent、gateへ進む。`backoff_sweep.py:326-378`。repro/s1もcontext enter前の一度だけである。planは自waveの3 jobを直列化するだけで、他waveとのnode排他をPBS資源指定で保証していない。`s2-plan.md:167-184,271`。
  - 成果物への影響: 後から同居jobが開始するとconfigure timeoutやsweep性能値が外乱を含み、偽の赤または無効なscreening値になる。

- **[real] 2時間walltimeは機械的上界ではない。** Masstree準備には900秒のconfigureと900秒のbuildがある。`backoff_sweep.py:370-376`。その後のlegacy buildはtimeout引数を持たず、`_run()`へ`timeout=None`で到達しうる。`buildcache.py:3104-3111,3231-3236,3483-3499`。PBS kill時はPythonのfinallyとJSON writerが走らない。
  - 成果物への影響: gateが既に緑でも後段screeningがhangし、最終JSONなし、dirty scratch clone、途中WAL/cacheだけが残りうる。

- **[real] repro/s1のnetwork状態は未束縛である。** configure argsが空なので各temporary build rootがFetchContent取得を試み、plan自身もnetwork禁止、遅延、timeoutの影響を認めている。`s2-plan.md:236-247,265`。network preflight、offline宣言、結果へのnetwork state記録はない。
  - 成果物への影響: `configure-failed`をdriverの恒常的な赤と、一時的なDNS/proxy/remote障害に分離できず、再現不能な結果になる。

- **[refuted] submodule未初期化やcommit object不足から別pinへfallbackする経路はない。** `git worktree add`失敗は例外になる。`patchharness.py:364-369`。planも必要objectをread-only確認し、不足時はnetwork fetchせず停止する。`s2-plan.md:261`。
  - 成果物への影響: 誤pinでの緑は作らない。ただしPBS preflight停止なのでstructured JSONは残らない。

- **[real] `git clone --shared`はworking treeだけを隔離し、object lifetimeはoriginへ依存する。** planは元submoduleから`--shared --no-checkout`する。`s2-plan.md:173-174`。origin側のprune、破損、移動が実行中に起きればnode-local cloneも必要objectを失いうる。
  - 成果物への影響: checkout、worktree remove、source解決が途中失敗し、driver赤ではなくsetup由来の欠落またはscratch残骸になる。

- **[real] temporary容量・inode対策は宣言だけで閾値と失敗記録経路がない。** planは「十分なinode/容量を事前確認」とするだけである。`s2-plan.md:267`。
  - 成果物への影響: ENOSPCがJSON直接書込中に起きると、create-onlyの壊れたevidenceと再走不能を同時に生む。

## 謳うだけの不変条件

1. **[real、機械保証なし] production codeを1行も変えない。** planは追加fileを2本に限定すると述べるが、base `d19d2182f`とのdiff allowlistやproduction path hashをPBSで検査しない。exact HEAD検査は「そのHEADをcloneした」ことしか保証せず、wave HEADにproduction変更が含まれていても通る。`brief.md:77`、`s2-plan.md:115-119,169-174`。
   - 成果物への影響: 変更済みdriver/gateを「production現状」として測定したJSONを作れる。

2. **[refuted、exactに実行したrequestに限る] gate赤を緑にしない。** production helperの拒否例外とprobeの初期`ok=False`、実request/両腕/admission必須条件で保証される。`backoff_sweep.py:156-169`、`s2-plan.md:144-155`。ただしs1 driver全体への一般化は未保証である。
   - 成果物への影響: 観測対象cellの赤は緑にならないが、未観測cellの赤はdriver緑表示の外へ落ちる。

3. **[refuted、完成payloadに限る] 実測値とreason codeを実走出力からだけ取る。** exact code object、exact dataclass、canonical JSON、例外reasonの非推測という設計はこの不変条件を満たす。`s2-plan.md:126-150`。
   - 成果物への影響: 完成JSONの値は実object由来。ただしPBS preflight、kill、partial writeには完成JSON自体がない。

4. **[real、機械保証なし] `s1_direct_comparison.py`のbytes不変。** exact HEADだけでは承認済みbytesとの一致を証明しない。s1の固定digest、base commitとのpath限定diff、既存materializer bindingの照合がplanにない。`brief.md:80`、`s2-plan.md:105-111,169-174`。
   - 成果物への影響: wave commitでs1 bytesが変わっていても、その変更済みfileをimportして緑を出せる。

5. **[refuted、既存storeについては条件付きで保証] 既存campaign、freeze、予算台帳を汚さない。** driver別clone、clone外scratch official root、direct `prepare_cell()`、create-only evidenceを正しく実装すれば既存storeへは到達しない。`s2-plan.md:186-198`。残るのは新規evidence、PBS log、cleanup失敗時のscratchである。
   - 成果物への影響: 既存storeの上書きは避けられるが、「永続書込はevidenceだけ」までは保証されない。

## 裁定へ返す候補

- **実装せず裁定へ返す候補:** s1の合格単位を「最初のinert cell一件」とするか、「全inert cell、少なくとも全configuration」とするか。現planのdriver-wide緑は後者を証明しない。
- **実装せず裁定へ返す候補:** network起因の`configure-failed/timeout`をdriver赤と確定するか、環境不成立としてinconclusiveに分けるか。
- **実装せず裁定へ返す候補:** sweepをgate通過直後で終了するか、後段screening完走までdriver成功条件に含めるか。後者ならsummaryのabort検査と有限timeoutが必要。
- **実装せず裁定へ返す候補:** 3 driverのexact completenessを検査するaggregate manifest/gateの追加。これは新しい検査・台帳に当たり明示scope外。
- **実装せず裁定へ返す候補:** `patchharness`自体へ共有filesystem対応lockやkill recoveryを追加すること。production一般化であり本wave scope外。今回のprobeは完全なnode-local cloneで回避すべき。
- **実装せず裁定へ返す候補:** 赤だった既存campaign成果物の訂正・失効処理。briefのP5どおり、本waveでは名指しまでに留める。

## 総括

現planはそのままauthor段へ進める状態ではありません。blockingなのは、s1一件をdriver全体へ一般化する偽の緑、sweep abortを見ない成功判定、`exec`で失われるcleanup、非atomicなevidence writer、無期限の後段build、別node/network差をdriver差と分離できない点です。

node-local cloneとscratch official rootは、共有primary checkout、既存campaign、WAL、予算台帳の保護には有効です。ただしcloneはdriver別・fallbackなしとし、shellを`exec`せずcleanupさせるだけでは強制killを覆えないため、残骸を前提に専用pathを再利用しない必要があります。

静的検査のみ実施しました。編集、commit、push、pytest、計算ノード実測は行っていません。