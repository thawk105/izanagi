## 1 攻撃の到達

- [severity: must-fix] 元 root の rename で overmount 自体を外せる。

  Linux の `mount_namespaces(7)` が明記する通り、ある namespace だけで mountpoint になっている directory を別 namespace から rename/remove すると、その mountpoint は前者から除去される。現設計は owner が rename 可能な元 root そのものへ tmpfs を overmount する (`s2-plan.md:29,39-41`)。

  具体的な二走攻撃は次の通り。

  1. Python parent が A の tmpfs snapshot を seal して yield。
  2. `_build_v2_impl` の入口検査後、外側 owner が parent mode を戻し、元 root を退避、B の directory を同じ pathname へ置く。
  3. private namespace の tmpfs mount が外れ、CMake/compiler は同じ `sub` pathnameから B を読む。`sub` は pathname のまま `_run` へ渡される (`orchestrator/campaign/buildcache.py:2589-2633`)。
  4. build 終了前に元の A directory を同じ pathname へ戻す。post-build evidence とmanifest は A を読む (`orchestrator/campaign/buildcache.py:2637-2709,2760-2766`)。
  5. B binary は cache へ publish される (`orchestrator/campaign/buildcache.py:2815-2825`)。
  6. cleanup の unmount は既に mount が外れているため失敗するが、これは publish 後である。`with` の cleanup は `_build_v2_impl` の後 (`orchestrator/campaign/buildcache.py:2979-3009`) なので、汚染 cache は残る。
  7. 次走では A の正常 snapshot から同じ cache keyを hitし、A を記録した manifest と B binary を再利用できる。

  このため「`buildcache.py` 無変更で成立する」という分岐判定 (`s2-plan.md:3,48`) は成立しない。

- [severity: must-fix] build 子孫は将来の writable mount を重ねられる。

  `mount_setattr(..., AT_RECURSIVE, RDONLY)` が閉じるのは、その時点で存在する mountだけである。exec 後に capability が消えても、子孫は `unshare(CLONE_NEWUSER|CLONE_NEWNS)` で子 user namespace を作り、snapshot 内の directory へ writable tmpfsやbind mountを重ね、その viewで compilerを起動できる。親側の post-build collector は A のnamespaceを読むため、B を使った compile を A の manifest で記録できる。

  repository 内の別 sandbox はこの攻撃面を認識して `--disable-userns --assert-userns-disabled` を使っている (`orchestrator/codex_roles/launcher.py:562-580`)。本プランには同等の閉鎖がない。未来の `unshare`、`clone3`、`setns`、`mount` 等を子だけで禁止する実行境界が必要であり、process 全体を `with` に入れるだけでは足りない。

- [severity: must-fix] 外へ解決する symlink は閉じない。

  tree digest は symlink target文字列だけを hashし、target bytesを含めない (`orchestrator/campaign/s8b_expected_materialization.py:389-428`)。コピーも symlink をそのまま保存する設計 (`s2-plan.md:28,95`) なので、例えば `config.in -> /owner/input` を CMake が読み、外側 owner が `/owner/input` を A→B→A と変更できる。generated headerを介すれば compiler depfileには生成後の B しか現れず、snapshot symlink検査では捕まらない。

  compiler-input collectorは直接 depfileに現れた snapshot symlinkを拒否する (`orchestrator/campaign/s8b_compiler_input.py:409-435`) が、CMake/custom commandの入力全体を覆わない。snapshot外へ解決する symlinkはcopy前に拒否するか、target bytesをsnapshot内へ閉じ込める必要がある。

- [severity: should-fix] `copy → copied digest → seal` の順序は低レベル境界単独ではTOCTOUを残す。

  外側の親 processは `/proc/<pid>/root/<snapshot>` 経由で、seal前のtmpfsへ到達し、ownerとして `chmod` とwriteを行える。現物の `_build_v2_impl` はseal後・build前にもfull tree digestを再照合するため (`orchestrator/campaign/buildcache.py:2423-2428`)、内容をBのままsealした攻撃はそこで拒否される。しかし防護module自身の主張としては不完全で、テストが `_build_v2_impl` を代役へ置換するとこの補助検査も通らない。順序は `copy → recursive seal → sealed digest → evidence → yield` にすべきである。

- [severity: nit] 元 tree の変更がcopy前またはcopy中だけなら、原理上は閉じる。

  Bがcopyへ入ればcopied digestと `actual_digest` が不一致になり、Aへ戻ってcopy結果もAならbuildはAを見る。hash衝突を除けば、この部分には受理攻撃を見いださなかった。

- [severity: must-fix] dev/ino照合は事前状態へ戻す攻撃を識別しない。

  root directoryを退避して同じinodeを最後に戻せば、現在の照合は通る (`orchestrator/campaign/s8b_expected_materialization.py:170-192,924-929`)。内容のin-place A→B→Aならdev/inoは最初から不変である。tmpfsが常時維持される限りこれは害を持たないが、上記のmountpoint除去攻撃と組み合わせるとbuild viewの差し替えを止めない。

## 2 正例の恒真性

- [severity: should-fix] 記述された正例は、条件を厳密に実装すれば単純no-opを殺せる。

  既存chmod層だけならowner subprocessの `chmod u+w` は成功するため、低レベルcontextがno-opならwriteも成功する。したがって次をすべてexactに要求すれば恒真にはならない。

  - `chmod` とwriteを別々に実行し、両方の `errno == EROFS` を確認する。
  - subprocessのeuidとtargetのuidが一致する。
  - 正例と負例で同じdev/ino、同じ初期modeを使う。
  - 負例で `chmod`、write、内容Bの三点すべてが成功する。
  - IPC barrierで、外側がBにしている間に内側がAを読んだことを固定する。
  - subprocessが実際に一度起動したことをnonceで確認する。

  ENOENTやEACCESを許す書き方、genericな非0 rcだけを見る書き方は不可である。

- [severity: must-fix] root交換負例は「拒否した」だけでは機構を証明しない。

  root交換はdev/ino検査より先にmountを消し、unmount failureでも拒否される。このため、単に `ExpectedMaterializationError` を期待するtestではafter-build dev/ino照合を削除しても緑になり得る。さらにpublish済みcacheの残存を検査していない。

  必要なのは、一走目でroot交換を行い、二走目で同cache keyを使ってもcache hitもreceipt発行も起きないことを確認する二走testである。

- [severity: must-fix] `proof.source_protection_kind` は現案のままでは恒真なliteralである。

  issuerは現在、callerが渡す二つのdigestが形式上正しく等しいことしか検査しない (`orchestrator/campaign/s8b_binary_admission.py:183-230`)。ここへ固定文字列を無条件で足してvalidatorが同じ文字列を要求しても、防護contextを実行した証拠にはならない。現行receipt testも実buildなしでissuerを直接呼べる (`orchestrator/tests/test_s8b_binary_admission.py:120-176`)。

  kindは低レベルcontextが生成したexact capabilityと、descriptor-bound `BuildResult`、receipt issuerの間で型として受け渡す必要がある。固定文字列の自己申告だけをproofに数えてはならない。

- [severity: must-fix] 5変異の判定は次の通り。

  1. `MOUNT_ATTR_RDONLY → 0`: **KILLED見込み**。ownerがchmod後にwriteでき、正例が落ちる。
  2. `tmpfs copy → recursive bind`: **KILLED見込み**。barrier付きで外側がBの間に内側を読ませればBが見える。
  3. `yieldをprivate context外へ移動`: **KILLED見込み**。元treeではownerがchmodを戻せる。
  4. 既存chmod削除: **KILLED**。現物testは全nodeとparentのwrite bitを直接検査する (`orchestrator/tests/test_s8b_expected_materialization.py:90-117`)。
  5. after-build dev/ino照合削除: **KILLEDではない**。上記の通りunmount failureが同じ拒否を起こし得るため、記述されたreplacement testでは変異が生存する。

  tree digestはwrite bitをmaskするが、path、node type、file bytes、symlink targetも含む (`orchestrator/campaign/s8b_expected_materialization.py:392-427`)。従ってdigest比較全部が純粋なmask gateというわけではない。一方、proof kindの固定literalは実体と無関係な冗長gateである。

## 3 namespace の生存期間

- [severity: should-fix] 現在の正式floor経路は直列だが、process全体の単一thread性はrepository全体では恒真でない。

  floor cellは同一processのloopで順次buildされる (`orchestrator/campaign/s8b_floor_campaign.py:4127-4162,4289-4302`)。一方、`orchestrator/` には実際の `ThreadPoolExecutor` (`orchestrator/campaign/t080_freeze_migration.py:964-1008`) とfork (`orchestrator/campaign/floor_job_checkpoint.py:136-167`) がある。

  初期化時の検査は `threading.enumerate()` だけでなく `/proc/self/task` のexact OS thread数を使うべきである。既存のPython-thread検査例 (`orchestrator/campaign/p3_b4_wiring_probe.py:1165-1175`) はnative threadを数えない。各context開始時にも再検査が必要である。

- [severity: should-fix] xdist自体はprocess分離なので原則安全だが、namespaceを作るtestは全て別process必須。

  受入runnerはxdistを有効化する (`tools/run_tests.py:2639-2686`)。各workerは別processなのでmodule stateは共有しないが、一度unshareしたworkerは以後もprivate namespaceのままである。正例だけでなく、低レベルsyscallを実行する全testをone-shot子processへ隔離しなければ、同workerの後続testを汚染する。

  fork前なら子が独自初期化、fork後ならPID不一致でfail-closed、spawnなら独自初期化、という三経路を固定するtestも必要である。

- [severity: must-fix] unmount failure後に同processを再利用できない。

  custom commandがgrandchildやcwdを残せば通常unmountは `EBUSY` になり得る。現プランはdetachせず拒否するだけで (`s2-plan.md:29`)、namespaceをpoisonしていない。floorは複数cellを同processで連続buildするため、callerが例外を捕捉すると古いsealed mountの残留やmount積層が次cellへ持ち越される。

  mount後の全例外点でcleanupを試み、通常unmountに失敗した時点でprocess-global stateを永久poisonし、以後のbuildを全拒否する必要がある。mountinfoのbaseline/current mount IDと積層数も連続build testで比較すべきである。

- [severity: must-fix] cleanupはpublishより後なので、例外・signal時のfail-closedがcacheまで届かない。

  Python例外、SIGINT、`subprocess.run` timeoutなら通常 `finally` は走る。SIGKILLや既定SIGTERMでは保証されない。ただし最大の問題はsignalそのものではなく、正常な `_build_v2_impl` return時点で既にcache publish済みであること (`orchestrator/campaign/buildcache.py:2815-2852`)。後続unmount/dev-ino検査の失敗がpublished binaryを無効化しない。

- [severity: must-fix] Python parentのcapability除外は限定名としては正直だが、D1201完了の名前ではない。

  `unprivileged-build-descendant-private-tmpfs-readonly/v1` はtrusted parentを除外しており、限定保証名としては正直である。しかしnamespaceを作ったowner Python自身はCAP_SYS_ADMINを保持し、unseal、overmount、unmountができる (`s2-plan.md:30,91`)。D1201の「所有者自身」を閉じた証明としてこの限定contractを扱うなら射程不足である。

## 4 既存防壁

- [severity: must-fix] 現在のfull tree/evidence再照合が元treeからtmpfsへ付け替わり、受理集合が拡大する。

  現在は `_assert_source_snapshot_sha256` と `_recheck_source_evidence` がbuild前後にlive `sub`を読む (`orchestrator/campaign/buildcache.py:2423-2428,2549-2552,2707-2709,2760-2766`)。overmount中は全てtmpfsを読むため、元treeがcopy後にBへ変わったままでも検査はAを見て通る。unmount後はdev/inoしか確認しない設計 (`s2-plan.md:41`) なので、旧gateが拒否した「元treeの持続的drift」を受理する。

  build input自体がAなら新snapshot保証として合理性はあるが、「既存防壁を弱めない」というbriefの不変条件には反する。元treeのfull digest/evidenceをunmount後にも再照合し、失敗時は既にpublishしたcacheも確実に無効化しなければならない。

- [severity: nit] `chmod(mode & ~0o222)` 自体は削除されず、独立testも有効である。

  現行実装は全nodeとparentへ適用し、digestとmodeを再確認する (`orchestrator/campaign/s8b_expected_materialization.py:541-610`)。直接testも明示mode assertionを持つため、chmod削除変異は捕れる。

- [severity: should-fix] 既存testの低レベルcontext no-op化は、scopeを狭く固定しないと新しい意味を検査しない。

  現在のevidence testは「chmod後の元treeを読んだ」ことを確認する (`orchestrator/tests/test_s8b_expected_materialization.py:513-564`)。contextをno-opにすると、改訂後に必要な「sealed tmpfs viewからevidenceを導出した」ことは証明しない。monkeypatchを各旧testへ局所化し、新規のreal-context testやslow canaryへ漏れないことを明示すべきである。

- [severity: must-fix] `resolve_evidence` の意味は変わる。変化は旧predicateに対する受理集合の拡大である。

  `SourceEvidence.source_root` は同じpathname文字列のまま (`orchestrator/campaign/source_digest.py:2195-2235`) だが、読んだinodeは元treeからtmpfs copyへ変わる。その結果、元treeのpost-copy driftを無視する実行も受理される。これはbuild-view保証として別種のevidenceであり、従来の「live source rootを再観測したevidence」と同一名で扱うべきでない。

## 5 判定

**判定: 却下。**

少なくとも次を満たす再設計が必要である。

- ownerがrenameできない安定したmountpoint、pivot/root view、またはfd-bound source pathを使い、別namespaceからのmountpoint除去を閉じる。
- build子孫によるnested user namespaceと将来mountを禁止する。
- snapshot外へ解決するsymlinkを拒否またはsnapshot内へ閉じ込める。
- seal後にdigestを計算する。
- unmount/dev-ino/元tree再照合をcache publishより前へ移すか、失敗時にpublished cacheを確実に破棄する。
- unmount failure後はprocessをpoisonし、連続buildを拒否する。
- root交換を用いた二走cache攻撃とnested-userns overmount攻撃を正例・変異testへ加える。
- Python直接syscall、identity mapping、tmpfs、recursive sealを計算ノードで実証する。

pytestや実buildは実行していない。上記は指定HEADの静的検査結果である。

## 総括

**却下。** 最大の懸念は、外側ownerのroot renameでprivate tmpfs mountを外し、publish後cleanup失敗を経由してB binaryをcacheへ残せること。  
次点は、build子孫がnested user namespaceで将来のwritable mountを重ねられることである。