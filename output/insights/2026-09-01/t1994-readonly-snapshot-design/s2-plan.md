## 1 分岐点の判定

**判定: (a) は成立する。`buildcache.py` の変更は不要。**

根拠は次のとおり。

- [`buildcache.py:2977-3009`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:2977) は `admitted_build_snapshot` の `yield` 中に `_build_v2_impl` 全体を実行する。context manager が `yield` 前に現 process の mount namespace を変更すれば、その view は本体と全子孫に継承される。
- 実 configure/build は [`buildcache.py:2611-2635`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:2611) の 2 箇所から `_run` に集約され、実際の起動は [`buildcache.py:3376-3392`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:3376) の単一 `subprocess.run` である。toolchain、Git、`nm` 等の補助 subprocess は [`buildcache.py:949`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:949)、[`1184`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:1184)、[`1218`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:1218)、[`3360`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:3360)、[`3407`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:3407) に散るが、いずれも `_build_v2_impl` の内側なので同じ namespace を継承する。
- `admitted_build_snapshot` が yield するのは [`s8b_expected_materialization.py:915-920`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:915) の digest、再導出 evidence、EVOLVE-BLOCK hash だけである。caller は [`buildcache.py:2988-3008`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:2988) でそれらを照合・転記しており、subprocess wrapper を yield 値へ追加する必要はない。
- `pegasus02`、Linux 5.15 上で、現 uid/gid を同じ数値へ identity-map する `unshare(CLONE_NEWUSER)`、続く `unshare(CLONE_NEWNS)`、private mount、tmpfs mount、`mount_setattr(AT_RECURSIVE, MOUNT_ATTR_RDONLY)` が成功した。exec 後の子 process は uid/gid が元の `31609/30410` のまま、`CapEff=0`、対象 mount は `tmpfs ro,nosuid,nodev` だった。したがって build の所有権意味論を root mapping へ変えずに成立する。
- `/usr/bin/unshare --map-current-user ... mount ...` は exec 後に capability が落ちるため mount に失敗した。実装は `unshare` command の起動ではなく、context manager の Python process が exec 前に syscall を直接行う必要がある。
- user namespace から元 namespace へ安全には戻れないため、process ごとに一度だけ identity user/mount namespace を作り、その後は tmpfs mount/unmount を再利用する。毎 build で user namespace を重ねてはならない。

単純な read-only bind は、別 mount namespace の同一 uid actor が下層 inode を書くと build viewにも変更が見える。したがって実装は元 tree の bind ではなく、private namespace 内の匿名 tmpfs へ exact copyを作り、digest 再照合後に recursive read-only 化する。これで外側の元 tree に対する A→B→A も compiler inputへ届かない。

生成時不変の代案については、現行 checkout は [`patchharness.py:346-383`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/patchharness.py:346) が writableな `/tmp` worktree を作り、patch 適用を必要とするので初めから read-only filesystemへ置けない。`squashfuse` と `mksquashfs` は存在するが `/dev/fuse` がなく、ERoFS toolingもない。`chattr +i` は初期 user namespace の capability が必要である。private tmpfs が追加 binaryなしで成立する最小経路である。

## 2 プラン

### 実装ファイル

- 新規 `orchestrator/campaign/s8b_readonly_snapshot.py:1-end`

  低レベルの Linux 隔離だけを担当する。

  - `:1-100`: `ctypes` による `unshare`、`mount`、`umount2`、`mount_setattr`、定数と exact errno変換。
  - `:101-170`: process が単一 threadであることを確認し、現在の uid/euid/gid/egid を同じ内側 IDへ mapする。`/proc/self/{uid_map,gid_map}` を再読して exact 一致を要求し、mount propagationを privateにする。初期化済み PIDを固定し、fork後の再利用や並行 contextは拒否する。
  - `:171-270`: held `root_fd` から regular file、directory、symlinkだけを fd-relativeに匿名 tmpfsへコピーする。device、FIFO、socket等は拒否する。byte数・inode数に上限を置き、現 CCBench約12 MBを十分含む値に固定する。
  - `:271-end`: `private_snapshot_mount(root, root_fd)` contextと `seal_readonly()`。元 rootへtmpfsを overmountし、seal時に `mount_setattr(..., AT_RECURSIVE, MOUNT_ATTR_RDONLY)` を適用して `/proc/self/mountinfo` と `statvfs` の双方で `ro` を確認する。通常 unmountに失敗した場合は detachで隠さず fail-closedにする。
  - 公開する保証名を `unprivileged-build-descendant-private-tmpfs-readonly/v1` とする。build子孫、外側同一 uidによる元 tree変更、通常の `chmod` を射程に含め、host rootやtrusted Python parentの mount capabilityは含めない。

- [`s8b_expected_materialization.py:2-26`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:2)、[`847-929`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:847)

  `admitted_build_snapshot` を次の固定順序にする。

  1. 宣言 replayと元 tree digest照合を現行どおり実施する。
  2. [`make_snapshot_non_writable:541-610`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:541) を削除・置換せず、そのまま適用する。
  3. 現行 [`878-883`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:878) の元 root identityと permission-state digest照合をtmpfs overmount前に行う。
  4. `permission_state.root_fd` からprivate tmpfsへコピーし、tmpfs viewに対して `snapshot_tree_digest` を再計算する。元の `actual_digest` と不一致ならbuild前に拒否する。
  5. tmpfsをrecursive read-only化し、確認後にだけ [`source_digest.resolve_evidence:884-905`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:884) と [`yield:915-920`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:915) へ進む。
  6. yield終了後にtmpfsをunmountして元 rootを再表示してから、現行 [`924-929`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:924) のdev/ino照合とpermission復元を行う。mount失敗、unmount失敗、copy raceのどれも `ExpectedMaterializationError` へ変換して拒否する。
  7. moduleと関数docstringを、単なるmode-bit境界ではなく上記の限定付き保証へ更新する。同一materializer、特権actor、外部compiler inputを保証しない記述は残す。

- [`s8b_binary_admission.py:2-10`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_binary_admission.py:2)、[`39-69`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_binary_admission.py:39)、[`183-287`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_binary_admission.py:183)、[`317-390`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_binary_admission.py:317)

  receipt schemaを `s8b-binary-admission/v3` に上げ、`proof.source_protection_kind` を exact fieldとして追加する。値は上記の限定名に固定する。validatorも同じliteralを要求する。これはhistorical mountのconsumer独立証明ではなく、標準producerが実行した限定付きexecution contractであることをmodule docstringへ明記する。旧v2を新しい正式受入へ流用しない。

  `buildcache.py` には変更を加えない。

### テスト

- [`test_buildcache_v2.py:2919-2990`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/tests/test_buildcache_v2.py:2919) 付近に、別 Python processで実 `buildcache.build_v2`、実 `admitted_build_snapshot`、実tmpfs防護を通す統合テストを追加する。

  reference replayとevidenceだけをfixtureへ固定し、`_build_v2_impl` の代役は実 subprocessを起動する。subprocess自身がsource所有者であることを確認し、`chmod u+w` と書込みの両方が `EROFS` になること、内容Aが維持されることを要求する。外側test processはbuild中に元 treeをA→B→Aと変更し、内側build viewが常にAであることも確認する。防護層、`build_v2` wrapper、context manager、実 subprocessはstubしない。

- 同じattacker programを防護context外の同じsourceへ実行し、`chmod u+w` とBへの書込みが成功する負例を対にする。production APIへ防護off knobは追加しない。

- [`test_s8b_expected_materialization.py:90-117`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/tests/test_s8b_expected_materialization.py:90) は現行chmod層の独立テストとして維持する。tmpfs層を対象としない既存テストでは低レベルcontextだけを明示的にno-op化し、chmod、digest、evidence順序の検査を残す。

- [`test_s8b_expected_materialization.py:399-411`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/tests/test_s8b_expected_materialization.py:399) は `exact → chmod → private copy → copied digest → recursive seal → evidence → yield` の順序を固定する。

- [`test_s8b_expected_materialization.py:643-652`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/tests/test_s8b_expected_materialization.py:643) を拡張し、tmpfs unmount後も元rootのdev/inoが同じである正例と、外側namespaceで元rootを交換した場合にafter-build照合が拒否する負例を追加する。全modeが元へ戻ることも同時に確認する。

- [`test_s8b_floor_campaign.py:9456-9500`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/tests/test_s8b_floor_campaign.py:9456) の実build_v2 canaryは現在descriptorを渡しておらず、新防護を通らない。freeze entryから実descriptorを作って渡し、返却された2 digestを確認するよう変更する。可能なら現freezeの全configurationへparametrizeし、最低でも通常FetchContentの`stock_common`と外部masstree sourceを使う`sort_best`を計算ノードで実buildする。

- [`test_s8b_binary_admission.py:142-198`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/tests/test_s8b_binary_admission.py:142)、[`503-520`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/tests/test_s8b_binary_admission.py:503) はv3 round-trip、限定付きproof kind、v1/v2拒否、kind改変拒否へ更新する。

### P3: build中のsource書込み

静的に確認できる実buildは [`buildcache.py:1905-1945`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:1905) の `cmake -S <snapshot> -B <staging>` と `cmake --build <staging>` であり、主出力はsnapshot外である。

- [`external/ccbench/CMakeLists.txt:85-87`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/external/ccbench/CMakeLists.txt:85) のprotocol matrixは `CMAKE_BINARY_DIR` へ書く。
- [`ThirdParty.cmake:57-78`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/external/ccbench/cmake/ThirdParty.cmake:57) はmasstreeの`config.h`、object、archiveを`masstree_SOURCE_DIR`へ書く。ただし通常はbuild側FetchContent base、sort経路では [`buildcache.py:1895-1904`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/buildcache.py:1895) で明示された外部dependency treeであり、admitted snapshot rootではない。新防護はこの外部書込みを塞がない。
- build対象から呼ばれるCMakeにsnapshot rootへの明示的writeは静的検索では見つからなかった。tracked script群には相対結果fileへのwriteがあるが、`ycsb_<protocol>.exe` build targetからの起動経路は見つからない。

ただしgenerator、compiler launcher、FetchContent、custom commandの実効pathは実configure/buildでしか確定しない。上記descriptor-bound slow canaryを計算ノードで実行し、成功したconfigurationだけをP3確認済みとする。今回はpytestも実buildも実行していない。

## 3 変異候補

- 新規 `s8b_readonly_snapshot.py` の `seal_readonly()` で `MOUNT_ATTR_RDONLY` を0へ変えると、所有者subprocessの`chmod`とwriteが成功し、実path統合正例が **KILLED** になる。
- 新規moduleのtmpfs overmountを元treeのrecursive bindへ変えると、外側processのA→Bがbuild viewへ現れ、cross-namespace A→B→A正例が **KILLED** になる。
- [`s8b_expected_materialization.py:915`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:915) の`yield`をprivate snapshot contextの外へ移すと、`_build_v2_impl`代役の所有者writeが成功し、`build_v2`実path正例が **KILLED** になる。
- [`s8b_expected_materialization.py:579`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:579) の`chmod(mode & ~0o222)`を削ると、既存mode-bit正例 [`test_s8b_expected_materialization.py:90-117`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/tests/test_s8b_expected_materialization.py:90) が **KILLED** になる。
- [`s8b_expected_materialization.py:924`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:924) のafter-build dev/ino照合を削ると、外側namespaceによる元root交換負例が通り、追加するreplacement testで **KILLED** になる。

digestをmaskから再導出するだけの冗長gateは候補にしていない。

## 4 射程の限界

- 現行の直接syscall probeはPegasus login node上であり、計算ノードでは未検証である。D1201の正式完了には計算ノードでidentity mapping、tmpfs、recursive read-only、owner write拒否、実buildを再実証する必要がある。
- host root、初期user namespaceの特権actor、trusted Python parent自身によるmount syscall、kernel compromiseは閉じない。execされた通常build子は`CapEff=0`だが、namespaceを作ったPython parentはそのnamespace内のmount capabilityを保持する。
- [`s8b_expected_materialization.py:21-26`](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t822-arm-source-binding/orchestrator/campaign/s8b_expected_materialization.py:21) の同一materializer両側再現は閉じない。
- user namespace作成は単一thread processが前提である。公式callerにthreading使用は静的には見つからず、今回のprocessも`Threads: 1`だったが、実行時に複数threadなら変更前にfail-closedとする。
- snapshot外のFetchContent source、dependency prefix、absolute symlink先などのexternal compiler inputはtmpfs snapshotの不変性に含まれない。既存compiler-input manifestのhash束縛は残るが、外部入力自体のread-only化ではない。
- tmpfs copyはtree digestが扱うpath、node type、mode、regular bytes、symlink targetを保つ。ownership、xattr、ACL、hardlink関係は現schemaの証明対象ではない。
- v3 receiptのproof kindはproducer execution contractの種別名であり、後続consumerが過去のmount namespaceを独立再観測した証明ではない。
- pytest、実CMake build、計算ノードprobeは未実行であり、緑とは報告しない。
- worktree HEADは指定どおり`259e02209c0202762e9a4b051f71e2f2657c69ee`だったが、確認時点のlocal `main`は`1b8710811f316405bd5ed0afa516e5e131fd74d1`へ進んでおり、既に同一ではない。本行番号はworktree HEAD側の現物に基づく。

## 総括

(a) は成立し、identity user/mount namespaceとprivate read-only tmpfs snapshotにより`buildcache.py`無変更で実装できる。  
最大の懸念は計算ノードと実buildが未検証であること、ならびにuser namespace初期化が単一thread processを要求することである。