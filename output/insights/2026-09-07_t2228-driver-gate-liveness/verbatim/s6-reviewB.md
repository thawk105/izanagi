## 段 3 lens B の 16 件の閉じ具合

段 4 の表には、実際には `real` とされた行が 18 件あります。B-23/B-24 は同じ処置ですが別行なので、漏れを避けて18件すべて確認しました。

| # | 判定 | コード確認 | 放置時の成果物への影響 | 稼働中 job |
|---|---|---|---|---|
| B-2 | refuted | s1/repro/sweep ごとに独立した clone を作り、import 元も clone 内へ照合している。[PBS:219](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:219) [probe.py:184](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:184) | 通常環境では元の `external/ccbench` は patch 対象にならず、JSON の測定 root は driver 専用 clone に限定される。 | 有効 |
| B-3 | refuted | patch lock は job 固有 `TMPDIR` 内で、clone の実 path ごとの hash 名になる。[PBS:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:81) [patchharness.py:113](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/patchharness.py:113) | ノード間 flock に依存せず、別 job・別 driver は別 tree なので gate/build 入力を合成しない。 | 有効 |
| B-4 | refuted | Python は `exec` せず子として起動され、shell は `exit "$PROBE_RC"` まで残る。通常終了では EXIT trap が走る。[PBS:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:86) [PBS:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:279) | SIGKILL では残骸があり得るが、job 固有 path は再利用せず、既存 repo や次の通常 run の値は汚さない。 | 有効 |
| B-6 | refuted | s1 は全 freeze cell の到達性を列挙し、実走は裁定された2 cellとして別々に記録する。[probe.py:620](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:620) [probe.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:729) | 最初の inert cell 1件を s1 全体へ一般化する旧設計は消えた。ただし新しい s1 判定欠陥は後述する。 | 有効 |
| B-7 | refuted | sweep の `ok` は gate 成功に加え `committed == 2`、`aborted == 0` を要求する。[probe.py:457](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:457) | aborted campaign を `ok=true` として受理しない。 | 有効 |
| B-9 | refuted、限定付き | 実行済み prefix を各 JSON に入れ、最終 sweep には3 driverが並ぶ。[probe.py:1038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:1038) | 段 4 が要求した最小の実行集合記録はある。publish 完全性の aggregate gate は依然 scope 外。 | 有効 |
| B-11 | refuted | legacy cache の既定は各 clone の `external/ccbench/build-variants` である。[buildcache.py:3138](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/buildcache.py:3138) | build binary、sidecar、staging は driver clone 内に留まり、元 repo の cache を参照しない。 | 有効 |
| B-13 | refuted | JSON は同じ evidence directory の temp に全量書込み、file fsync、hard-link create-only publish、directory fsync の順である。[probe.py:107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:107) | write 中の kill/ENOSPC では最終名が無い。link 後なら最終名は完全な JSON で、途中 JSON は残らない。 | 有効 |
| B-14 | refuted | PBS は evidence を元 repo 外へ限定し、Python も全 driver clone 外であることを再検査する。[PBS:64](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:64) [probe.py:968](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:968) | 最終 JSON は repo の `output/insights` に直接書かれない。 | 有効 |
| B-15 | must-fix | `-o/-e` はコメント内の qsub 例だけで、PBS directiveにも実行時検査にもなっていない。[PBS:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:7) | qsub 側で省略すると `.o*`/`.e*` が `PBS_O_WORKDIR` に戻り、「repo 外だけへ永続書込み」という受理条件が偽になる。 | 部分的 |
| B-16 | refuted | 1回の Python 起動が `s1 → repro → sweep` を直列実行する。[PBS:279](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:279) [probe.py:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:1027) | hostname、process environment、開始時 network/capacity 観測を3 driverで共有できる。 | 有効 |
| B-17 | nit | job 全区間の排他資源指定はなく、瞬間的 single-tenant 検査という既知限界は残る。[PBS:2](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:2) [s4:81](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2228-driver-gate-liveness/s4-adjudication.md:81) | screening 値を本 wave の insight に使うと外乱値を参照し得るが、gate liveness だけに限定すれば受理集合は変わらない。 | 有効 |
| B-18 | refuted | walltime は3時間になり、各 driver の runner 復帰後、次の driver 前に publish する。[PBS:5](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:5) [probe.py:1040](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:1040) | 後続 driver の hang で先行 JSON は失われない。hang 中の driver 自身の JSON が無いのは設計どおり。 | 有効 |
| B-19 | refuted | network は開始時に観測し、判定には使わず全 driver metadataへ写す。[probe.py:497](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:497) [probe.py:1027](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:1027) | network 赤を隠して `ok=true` にする retry/fallback は probe にない。観測は github.com の先頭アドレス1件に限る。 | 有効 |
| B-21 | must-fix | clone は `--no-local --no-hardlinks` で、on-disk alternates も検査するが、最初の Git 呼出し前に `GIT_*` を拒否・解除していない。[PBS:91](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:91) [PBS:229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:229) [patchharness.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/patchharness.py:82) | `GIT_ALTERNATE_OBJECT_DIRECTORIES` や repository 指定環境があると、alternates file 不在だけでは自己完結性を証明できず、Git 操作の対象も submission environment に依存する。 | 部分的 |
| B-22 | refuted | driver 開始時の scratch free bytes と free inode を全 payload に記録する。[probe.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:524) [probe.py:1030](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:1030) | 閾値 gate は無いが、これは段 4 で scope 外として受容済み。 | 有効 |
| B-23 | refuted | import した production 4 file の SHA-256を driverごとに記録する。[probe.py:565](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:565) | insight 作成時に測定 bytes を基点と照合できる。digest 自体は gate にしないという裁定どおり。 | 有効 |
| B-24 | refuted | 上記4 file に `s1_direct_comparison.py` が含まれる。[probe.py:40](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:40) | s1 bytes が不明なまま参照されることはない。基点との比較は親の収容時作業として残る。 | 有効 |

追加の must-fix が1件ある。s1 の成功判定は、arm record が `green` であること、request digest が一致すること、admission がその2 record IDを含むことを確認していない。[probe.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:431)  
放置すると赤い supply/meaning recordでも `s1.ok=true` になり得て、実測 JSON の受理集合が段 4 §4および事前登録 M2 より広がる。稼働中 job: **部分的**。

## 共有状態への漏れ

- refuted: 通常の環境では、元の `PBS_O_WORKDIR/external/ccbench` は clone 元として読むだけである。patch、checkout、legacy build cache は3つの node-local clone内に限定される。

- refuted: official campaign root は `$TMPDIR/runtime-output/<driver>` に切り替わる。[probe.py:948](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:948) `layout.py` は official root を repo 外へ再検査する。[layout.py:412](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/layout.py:412) campaign lockもその root の `campaign-locks` に置かれる。[layout.py:50](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/layout.py:50)

- refuted: `/scr` 名は sanitized `PBS_JOBID` に束縛され、`mkdir` は create-onlyである。同名 path が残っていれば後続 job は起動前に停止し、既存 scratch を共有・削除しない。[PBS:21](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:21) [PBS:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:81)

- must-fix: evidence directoryには job/attempt claim がなく、出力名は固定3個である。さらに `EEXIST` などの publish 失敗後も次の driver を実行する。[probe.py:30](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:30) [probe.py:1055](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:1055)  
  2 jobまたは再走が同じ evidence dirを使うと、古い s1、新しい repro、別 job の sweep という3 file集合を作れる。各 JSON に `PBS_JOBID` や共通 run nonceもないため、同一 process由来か事後判定できず、1-job/1-nodeという insight の参照が偽になる。稼働中 job: **部分的**。

- must-fix: ambient `GIT_*` を最初の Git 操作前に閉じていない。`patchharness._git()` も環境を丸ごと継承し、`GIT_OPTIONAL_LOCKS` だけを上書きする。[patchharness.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/patchharness.py:73)  
  放置すると clone 自己完結性、HEAD/status対象、patch/revert対象が submission environment に依存する。稼働中 job: **部分的**。

## 結果が失われる形

driver終了直後の publish は実装されている。失われ方は次のとおり。

| 停止地点 | 残る最終 JSON |
|---|---|
| PBS preflight、gflags/glog build、clone 中 | なし |
| s1 実行中または s1 publish 前 | なし |
| s1 publish 後、repro 実行中 | `s1.json` |
| repro publish 後、sweep 実行中 | `s1.json`, `repro.json` |
| sweep publish 後 | 3件すべて |

- hang/walltime: driver単位の外側 timeout はない。walltimeで Python が kill されると、その時点の driver JSON は出ないが、先行 driver JSON は既に evidence dirにある。特に sweep の後段 legacy build は timeoutなしで到達できる。[buildcache.py:3231](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/buildcache.py:3231)

- ENOSPC: `/scr` 側の失敗が Python例外として戻り、evidence filesystemに空きがあれば現在 driverは `ok=false` として publishされる。evidence側がENOSPCなら、link前の途中 tempは削除され、最終名は作られない。link後なら最終名は完全なJSONだが、directory fsync失敗を報告したまま final pathが残る可能性がある。

- networkなし: probe自体は retryしない。production callが有限時間で例外を返す限り、各 driverは `ok=false` と例外 chainを直後に保存し、次の driverへ進む。外部コマンドが無期限に待てばwalltime時点の driverは欠落する。

- must-fix: publish失敗後も処理を継続するため、既存 fileと今回の成功 fileを混ぜた集合が残る。個別 JSON は完全でも、3件集合の出所が失われる。稼働中 job: **部分的**。

## cleanup

- refuted: `exec` はなく、通常の shell `exit` で EXIT trapが発火する。

- refuted: `rm -rf` は使っていない。削除対象は、検証済み `PBS_JOBID` から作り、create-onlyで確保した単一の `$TMPDIR` である。[PBS:81](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:81) `find` は既定では symlinkを辿らないため、clone内の symlinkから repoへ降りない。

- refuted: driver cloneの `.git/worktrees`、patch lock、build cacheもすべて同じ job scratch内なので、scratch全体削除で共有 Git metadataを消さない。

- nit: cleanupの失敗を `|| true` で捨てる。[PBS:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:86)  
  現在の JSON 値は変わらないが、権限変更やSIGKILLで残骸が蓄積すると、将来の `/scr` ENOSPCやjob-id再利用時の起動拒否を招く。稼働中 job: **有効**。

- nit: SIGKILLではPythonの `finally` もshellのEXIT trapも保証されない。これは段 4 が job固有 path非再利用で受容した残余であり、今の成果物を無効にはしない。

## 投入契約

- refuted: `PBS_JOBID`、`PBS_O_WORKDIR`、expected HEAD、evidence dirは必須である。expected HEADは40文字lowercase hexに限定され、実HEADと完全一致を要求する。[PBS:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:17) [PBS:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:37)

- refuted: tracked-clean検査は outer repoで行い、元 ccbenchはuntrackedを含めてclean検査する。clone後も outer、nested ccbenchを再検査する。[PBS:47](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:47) [PBS:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:254)

- refuted: `realpath -e` は代入commandの成功を要求し、scriptは `set -e` なので解決失敗時に素通りしない。`readlink` は使っていない。[PBS:14](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:14) [PBS:32](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:32)

- refuted、限定付き: compute-only検査は実行時hostnameを `bnode...` に限定する。[PBS:26](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:26) ただし scheduler署名ではなく、PATH上の `hostname` と環境変数を信頼する契約である。

- must-fix: Git関連環境を閉じていないため、上記HEAD、clean、alternates、checkoutの検査がself-containedではない。少なくとも `GIT_DIR`、`GIT_WORK_TREE`、`GIT_COMMON_DIR`、`GIT_INDEX_FILE`、`GIT_OBJECT_DIRECTORY`、`GIT_ALTERNATE_OBJECT_DIRECTORIES` とGit config注入面を、最初のGit呼出し前に拒否または解除する必要がある。稼働中 job: **部分的**。

- must-fix: PBS stdout/stderrの外部配置は必須環境変数のようには検査されず、qsub例のコメントだけである。稼働中 job: **部分的**。

## must-fix 一覧 (走行中 job への影響つき)

1. **s1 arm判定が段 4 §4とM2を実装していない — 部分的。**  
   `terminal_status == "green"`、request digest、2 record IDとadmissionの結合を要求していないため、`s1.ok` の受理集合が広すぎる。[probe.py:431](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:431)

2. **同一 evidence dirでjob間・再走間のJSONが混成できる — 部分的。**  
   共通 run ID/claimがなく、publish失敗後も続行するため、3 JSONが同一 process由来という参照を証明できない。[probe.py:1038](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.py:1038)

3. **PBS stdout/stderrのrepo外配置が強制されない — 部分的。**  
   qsubで `-o/-e` を省略した実行も受理され、repoを汚したjobのJSONが正式成果物候補に残る。[PBS:7](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:7)

4. **ambient Git environmentがclone独立性とGit検査を迂回できる — 部分的。**  
   on-disk alternates不在だけでは自己完結性を証明できず、HEAD/status/checkout/patchの対象が外部環境に依存し得る。[PBS:229](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/tools/pegasus/probes/t2228_driver_gate_liveness_probe.pbs:229) [patchharness.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-driver-gate-liveness/orchestrator/campaign/patchharness.py:82)

## 裁定へ返す候補

- **実装せず裁定へ返す候補:** 3 driverのpublish済み集合を確定するaggregate manifest/gate。今回のmust-fixには共通run bindingと混成防止が必要だが、正式な新台帳まで作るかは段 4 のscope外指定に触れる。

- **実装せず裁定へ返す候補:** `patchharness` 自体の共有filesystem lock、SIGKILL recovery、stale lock/worktree一般回収。今回のdriver別cloneでは回避済み。

- **実装せず裁定へ返す候補:** job全区間のsingle-tenant保証と、screening値の再測条件。現裁定どおり、このwaveのinsightでscreening値を使わなければよい。

- **実装せず裁定へ返す候補:** scratch容量/inodeの閾値gate、network赤を環境不成立へ分離するpolicy。

- **実装せず裁定へ返す候補:** hostileな `PATH`、`BASH_ENV`、scheduler環境まで投入契約の脅威モデルに含めるか。Git環境の閉鎖は局所修正できるが、完全なscheduler attestationは別設計になる。

## 総括

driver別clone、非shared clone、scratchへのcampaign/cache隔離、atomic create-only JSON、非`exec`起動、driver直後publishは実装されている。hangやwalltimeでも、完了済みdriverのJSONは設計どおり残る。

一方、現状の成果物を無条件には受理できない。blockingは4件で、s1の偽陽性、evidence集合のjob間混成、PBS log配置の非強制、ambient Git環境によるclone・検査契約の抜けである。稼働中jobのJSONは、各armが実際にgreenであること、3 fileが同じrun由来であること、qsubの`-o/-e`、Git環境不在を外部確認できた範囲だけ有効であり、総合判定は **部分的**。

静的検査のみ実施した。編集、commit、push、pytest、計算ノード実測は行っていない。