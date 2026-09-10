## 前提

指定された 9 ファイルだけを全文確認した。編集、実装、pytest 実行はしていない。以下は静的検査であり、緑は主張しない。

## 正しさ境界の所見

### 所見 1: 安定した同一 parent なら `os.link` 自体は既存先を置換しない

- 深刻度: 情報。ただし後続の parent 差し替え競走は高深刻度。
- 根拠 (`file:line`): `s2-plan.md:194-223`、`create_only_store.py:207-218`、`paper_story_a1_paired.py:796-813`
- 事象の並び:

  1. process A が staging regular file を `O_CREAT|O_EXCL` で作成し、bytes と file fd を fsync する。
  2. 同じ安定した directory に destination の directory entry が既に存在する。
  3. destination が regular file、symlink、別 file への hard link、または staging と同じ inode の既存 hard linkのいずれでも、`os.link(staging, destination, follow_symlinks=False)` はその entry を置換せず `EEXIST` になる。
  4. plan の `published` は `False` のままなので staging cleanup に入り、既存 destination の inode や bytes には書き込まない。

  `follow_symlinks=False` は source symlink の扱いであり、既存 destination を追って置換する指定ではない。したがって、parent の identity が安定し、file system が `link` の契約を守るという条件下では、「既存先への公開が成功する」または「既存 bytes が `os.link` 自体で変わる」という並びは見つからない。
- 提案: 既存 regular file だけでなく、既存 symlink と既存 hard-link alias についても、entry と target bytes が不変である負例を追加する。
- 推測か実証か: `os.link` の create-only 性は静的実証。Lustre の全構成で同じ障害原子性を持つかは今回の 1 回の probe では実証されていない。

### 所見 2: `dir_fd` を使わないため、parent 差し替えで「既存先があったのに成功」が成立する

- 深刻度: 高
- 根拠 (`file:line`): `s2-plan.md:25-29,194-219`、`paper_story_a1_paired.py:8008-8016`、`create_only_store.py:166-177,207-224`
- 事象の並び:

  1. directory D0 に staging と既存 destination がある。
  2. process A の `os.link` が source operand `D0/staging` を解決する。
  3. 同じ uid の process B が D0 を別名へ rename し、元の pathname に同一 file system 上の新 directory D1 を置く。D1 には destination がない。
  4. `os.link` の destination operand が D1 を通って解決される。
  5. source inode は既に保持されているため、D1 に新 destination link を作れて、呼出しが成功し得る。呼出し開始時に D0 には既存 destination があったが、それは検査対象から外れている。
  6. B が D0 を元へ戻せば、A は成功を返したのに期待 pathname からは旧 destination が見える。

  別の並びでは、link 成功後に B が parent を差し替えると、`_fsync_directory(path.parent)` は pathname を開き直すため、link を収容した D0 ではなく D1 を fsync する。cleanup も D1 を見るため、D0 に final と staging が残り得る。
- 提案: parent を staging 作成前に `O_DIRECTORY|O_NOFOLLOW` で開き、source create、link、unlink、fsync を同じ descriptor と basename で行う。成功前に pathname の parent identity が descriptor の `(st_dev, st_ino)` と同じか再検証する。ただし、悪意ある同 uid writer が directory 自体を rename できる契約なら、`dir_fd` だけでは最終 pathname の継続的な束縛までは保証できない。そこは threat model の裁定が必要。
- 推測か実証か: pathname を operand ごとに再解決し、fsync 時にも開き直すことは静的実証。競走の実機再現は未実施。

### 所見 3: source staging の差し替え後に foreign bytes または symlink を final 名へ公開できる

- 深刻度: 重大
- 根拠 (`file:line`): `paper_story_a1_paired.py:796-813,849-871`、`s2-plan.md:194-223`、`paper_story_a1_paired.py:753-790,509-514`
- 事象の並び:

  1. A が inode I の staging を作成し、I の `(st_dev, st_ino)` を保存して fd を閉じる。
  2. B が staging entry を unlink し、同じ名前へ foreign regular inode F を置く。
  3. A の `os.link` は F を destination へ link し、成功する。
  4. `published=True` となり destination directory が fsync される。
  5. cleanup は staging の identity が I でないため拒否する。plan は `_PublishedReceiptCleanupError` を返すが、destination の F は巻き戻さない。
  6. foreign bytes が create-only final 名を占有し、正しい receipt を再公開できない。

  foreign replacement が symlink の場合、`follow_symlinks=False` は target regular fileを公開せず symlink inode 自体を hard linkする。そのため arbitrary target の dereference は防ぐが、final 名が symlinkとして占有される。`_read_bytes_once` は Linux では `O_NOFOLLOW` により拒否する一方、`_sha256_file` は通常の `Path.open` なので final symlink を追う。

  さらに B が I への別 hard linkを staging 作成後に確保すれば、cleanup 後も I へ書き込める alias が残る。cleanup は `st_nlink` を検査しない。
- 提案: 少なくとも random staging 名、固定 parent fd、link 直前と直後の source/final identity 検査を入れる。path source の差し替えを完全に防ぐには、同 directory を書ける非協調 writer を threat model から除外するか、開いた inode を直接 linkする primitive が必要。final を残す cleanup error policyは、foreign inode を公開した場合と owned inodeを公開した場合を分けるべき。
- 推測か実証か: foreign regular inode と symlink が final に linkされる分岐は静的実証。実機競走は未実施。

### 所見 4: `nlink=2` は部分 bytes を見せないが、staging alias 経由の公開後改変窓を作る

- 深刻度: 高
- 根拠 (`file:line`): `s2-plan.md:242-259`、`paper_story_a1_paired.py:509-514,753-790`
- 事象の並び:

  1. A は完成済みかつ fsync 済みの inode I を destination へ linkする。
  2. destination の可視化直後から staging unlink まで、I は staging と destination の 2 名を持ち、`nlink=2` である。
  3. この時点で consumer C が destination を読むと、source が不変なら完成済み bytes 全体を見る。hard link 自体には partial publish はない。
  4. しかし B が staging 名を `O_WRONLY` で開き、fd を保持する。
  5. A が staging entry を unlinkしても B の fd は有効である。
  6. A が成功を返した後に B が I を上書きまたは truncateし、destination bytes が変わる。

  `_sha256_file` は読取り前後の identity、size、mtime を照合しないため、更新と重なれば混合 digestも作り得る。`_read_bytes_once` は size と mtime の変化を検出するが `st_nlink` は見ず、変更が open 前に完了した安定した foreign bytes は普通の snapshotとして読む。
- 提案: nlink 2 の状態を consumer が許すのか明記する。非協調同 uid writer を対象に含めるなら現在の mode 0600 と identity cleanupだけでは bytes 不変性を保証できない。少なくとも staging 名を推測困難にし、link 後の alias 撤去を最短化し、consumer 側で期待 digestまたは canonical documentを検証する。
- 推測か実証か: alias fd による改変可能性と consumer が `st_nlink` を見ない点は静的実証。攻撃 process の存在は threat model に依存する。

### 所見 5: link 可視化と directory durability の間を consumer が通過でき、fsync 失敗は未分類になる

- 深刻度: 重大
- 根拠 (`file:line`): `s2-plan.md:203-223,248-260,281-291`、`paper_story_a1_paired.py:8008-8016,8659-8671`
- 事象の並び:

  1. A の `os.link` が成功し、destination は他 process から直ちに見える。
  2. A は `published=True` にする。
  3. job body または consumer C が destination を読み、先へ進む。
  4. A の `_fsync_directory(path.parent)` が ENOSPC、EIOなどで失敗するか、process がここで停止する。
  5. crash recovery 後に destination entry が残るかはこのコードでは確定できない。C は receiptを観測済みなのに proof chainから receiptが消える可能性がある。
  6. fsync が Python の `OSError` を返した場合、plan の link用 `except OSError` は既に通過済みである。cleanup が成功すると生の `OSError` が外へ出る。
  7. `_run_submit_v3` の予定 catch は `_PublishedReceiptCleanupError` と `PaperStoryError` だけで、`main` も `PaperStoryError` しか捕捉しない。final が公開済みなのに専用状態にも failure receiptにも分類されない。

  cleanup 内の 2 回目の directory fsync が成功すれば destinationも結果的に durableになり得るが、コードはそれを証明または分類できない。
- 提案: `published` の bool を少なくとも `not-linked`、`linked-not-durable`、`link-durable`、`staging-removed` の状態へ分ける。destination fsync failureも公開済み専用例外へ変換し、v3 failure receiptとの排他を守る。link、最初の dir fsync、staging unlink、2 回目の dir fsyncの順を記録するテストを追加する。
- 推測か実証か: 生の `OSError` が予定 catchを抜けることは静的実証。crash recovery の具体的な残存 entryは file system依存なので推測。

### 所見 6: link errno の通常分岐は cleanup へ落ちるが、write/fsync 失敗は outer `finally` の外で staging を残す

- 深刻度: 重大
- 根拠 (`file:line`): `paper_story_a1_paired.py:796-813`、`s2-plan.md:200-223`、`s1-brief.md:50-55`
- 事象の並び:

  - EEXIST: destination は既存のまま、`published=False`、owned staging cleanupへ進む。
  - ENOSPC / EDQUOT: directory entry または metadata quotaの追加に失敗した通常の結果なら destination は作られず、同じ cleanupへ進む。
  - EMLINK: source inode の link count上限で destinationなし、同じ cleanupへ進む。
  - EPERM: hard link policyや権限で拒否され、destinationなし、同じ cleanupへ進む。
  - EXDEV: operandが別 mountへ解決された場合に destinationなし、同じ cleanupへ進む。
  - EINTR: Python層に `OSError` として現れれば同じ branchへ進む。ただし、remote file system上で server side effectが本当に無かったことは今回の probeでは測っていない。

  各 link失敗で cleanupが成功すれば stagingは消える。cleanupの lstat、unlink、dir fsyncが失敗すると、その cleanup例外が元の errnoを覆い隠す。

  より直接的な不変条件違反は linkより前にある。`_exclusive_write_bytes` が stagingを作成した後、`os.write` または `os.fsync(fd)` が ENOSPC、EDQUOT、EIOなどを返すと、partial stagingをunlinkしないまま例外を返す。plan は `_exclusive_write_bytes` の呼出し後からしか `try/finally` を開始しないため、brief の「失敗時に staging を残さない」は成立しない。
- 提案: staging作成後の identityを write前に確保し、write、file fsync、linkを全て cleanup対象の `try` 内へ置く。primary errorとcleanup errorを両方保存し、cleanup errorだけで元 errnoを消さない。EINTRなど「side effect不明」をどの状態として扱うかも裁定する。
- 推測か実証か: staging write/fsync失敗で entryが残ることは静的実証。Lustreで error return後にも link side effectが残る可能性は未測定のため推測。

### 所見 7: 同じ inode であることを利用すると cleanup が receipt の最後の link を消せる

- 深刻度: 致命的。最重要所見。
- 根拠 (`file:line`): `s2-plan.md:132-155,194-223`、`s2-plan.md:650-706`、`test_paper_story_a1_job_contract.py:2529-2556`
- 事象の並び:

  1. A が owned staging inode I を destinationへ hard linkする。staging と destinationは同じ I である。
  2. A が `published=True` にした後、cleanupへ入る前に B が staging entryを unlinkする。
  3. B が destination entryを staging名へ renameする。destination名は消え、staging名が I の唯一の linkになる。
  4. A の `_remove_receipt_staging(staging, identity_I)` は stagingを lstatする。
  5. regular fileで `(st_dev, st_ino)==identity_I` なので検査を通る。
  6. cleanupが stagingを unlinkし、I の最後の linkを消す。
  7. directory fsyncまで成功し、A は例外なく成功を返すが destinationは存在せず、receipt bytesも回収不能になる。

  安定した namespaceでは `unlink(staging)` は destination名を消さない。破れには上の rename競走が必要である。しかし、hard link化により destinationを staging名へ移しても identityが変わらない点が現行 rename方式との決定的な差である。

  plan の replaced-staging testは、linkを行わず stagingを別 inodeへ交換して EIOを投げる。これは foreign inode保存だけを検査し、同じ inodeを destinationから stagingへ移す攻撃を検査しない。
- 提案: cleanup helperへ destinationも渡し、unlink前に destinationが同じ identityで存在することを必須にする。少なくとも destinationが消えていれば stagingを消さずに公開状態不明として停止する。さらに parent fd、前後の final identity検査、協調 writer用の排他が必要。非協調同 uid writerまで防ぐなら、checkとunlink間の競走は残るため、directory書込み権限の threat model自体を裁定する。

  最小の負例は、monkeypatchした `os.link` wrapper内で real linkを行った直後に `staging.unlink(); destination.rename(staging)` を実行し、publisherが成功を返さず、少なくともどちらかの linkを保存することを検査する形である。
- 推測か実証か: この順序では planどおりの cleanupが最後の linkを削除することを静的実証できる。実機競走は未実施。

### 所見 8: 同一 attempt の二重 submit は intent が止めるが、PID staging gate は namespace 全体を守らない

- 深刻度: 高
- 根拠 (`file:line`): `paper_story_a1_paired.py:3077-3106,3275-3316`、`test_paper_story_a1_job_contract.py:2559-2590`、`s2-plan.md:114-129,294-324`
- 事象の並び:

  1. process A と B が同じ attemptで同時に freshness checkを通る。
  2. 両者が intentを `O_EXCL` で作ろうとし、一方だけが成功する。
  3. loserは qsub前に停止するので、通常の二 process競走で qsubが二重実行される経路は見つからない。

  一方、staging basenameは PIDだけで決まる。

  1. PID P1 の以前の processが `.s-P1` を残して終了する。
  2. 新 process P2 は自分の `.s-P2` だけを guarded pathに入れる。`.s-P1` は検査されず永久に残る。
  3. PIDがP1へ再利用された場合だけ、freshness gateが残留 `.s-P1` を検出して qsub前に拒否する。
  4. 既存 stagingを publisherが「拾って」公開することはない。`O_EXCL` が拒否するため、残留 bytesの再利用ではなく、拒否または残留物の無視になる。

  より悪い TOCTOU は次である。

  1. A が current PID staging不在を検査する。
  2. A が durable intentを作り、qsubを実行する。
  3. B が公開直前に予測可能な current PID staging名を作る。
  4. `_exclusive_write_bytes` が `EEXIST` となる。v3では3 job受理後に failure receiptへ落ち、legacyは indeterminateになる。

  現行 foreign-staging testは stagingが最初から存在する場合だけを扱い、check後の注入や旧PID残留を扱わない。
- 提案: random tokenを含む staging名にするか、qsub前に staging entryを先取りして fdと identityを保持し、qsub後にその fdへ完成 bytesを書いて公開する。旧PID stagingを拒否するのか、所有証明付きで回収するのかも明示する。
- 推測か実証か: intentによる二重qsub防止と、current PIDの1 pathしか検査しないことは静的実証。PID再利用の発生時期は推測。

### 所見 9: completion を揃える方向は妥当だが、v3では新しい staging collision が proof chain を閉じ不能にする

- 深刻度: 重大
- 根拠 (`file:line`): `paper_story_a1_paired.py:4173-4261,4349-4351`、`s2-plan.md:326-366,768-872`
- 事象の並び:

  1. 現行 completionは完成名を `O_EXCL` で直接作ってから書くため、ENOSPC、process停止などで partial finalが残る。この欠陥は実在する。
  2. planどおり staging + linkへ揃えると、finalの partial visibilityは除ける。
  3. しかし `_run_complete_v3` は completion stagingの freshnessを先に検査しない。
  4. staleまたはforeign `.c-<pid>` がある状態で completeを開始すると、result directory、`result.json`、`receipt.json`、sidecar、group terminalを先に create-only公開する。
  5. 最後の `_publish_completion_receipt` で staging作成が `EEXIST` になり、completionだけが生まれない。
  6. retryすると `result_root.mkdir(mode=0o700)` またはその下の create-only writeが既存物で失敗し、completionへ再到達できない。その attemptの proof chainは閉じられない。

  submission用 staging関数をそのまま再利用した場合、currentの固定名 `submission.json` と `completion.json` は先頭から異なるため、直ちに同じ staging basenameになるとは実証できない。legacyの `<attempt>.submission.json` と `<attempt>.completion.json` も現在のLinux PID幅では切り詰め後に区別部分が残る。ただし kindがbasenameへ符号化されず、将来の長い共通prefix名では衝突し得る。`.s-` と `.c-` の分離自体は維持すべき。
- 提案: P1は実施してよいが、共通 publisherの修正に加え、completion stagingを不可逆なv3成果物作成前に予約または freshness検査し、途中失敗後の再開契約を定めることを条件にする。v2とv3の end-to-end負例を別々に置く。
- 推測か実証か: v3の書込み順と retry不能は静的実証。将来のbasename衝突だけは推測。

### 所見 10: `submission-failure.json` 据え置きは失敗理由そのものを partial final にする

- 深刻度: 高
- 根拠 (`file:line`): `paper_story_a1_paired.py:3037-3067,816-833`、`s2-plan.md:394-442`
- 事象の並び:

  1. 2本目のqsub失敗などで `_write_v3_submission_failure` が呼ばれる。
  2. `_exclusive_write` が完成名 `submission-failure.json` を `O_EXCL` で作成する。
  3. stream write、flush、fsyncの途中でENOSPC、EDQUOT、EIOまたはprocess停止が起きる。
  4. malformedまたは千切れた final名が残る。
  5. durable intentが既にあるため同一attemptのsubmitは再実行されない。
  6. failure receiptから正当なrerun reasonを検証できず、元のscheduler failureより二次的な記録失敗が前面に出る。

  「成功attemptのcompletionを塞がない」は狭すぎる。失敗台帳と次attemptの正当化に必要な一次 evidenceを失う。
- 提案: P3も完成済み stagingからcreate-only公開する。ただし successful submission publication後には failure receiptを作らない排他を維持し、failure writer自身の失敗を元原因と別に記録する。
- 推測か実証か: direct final writeのpartial状態は静的実証。実際のquota failureは未実測。

### 所見 11: directoryへ `os.link` できない主張は正しいが、materialize据え置きの結論は導けない

- 深刻度: 重大
- 根拠 (`file:line`): `paper_story_a1_paired.py:8070-8088,8155-8185,8244-8252,8256-8309`、`s2-plan.md:368-392`
- 事象の並び:

  1. A が exclusive sibling claimを取る。
  2. A が destination不存在を `lexists` で確認する。
  3. 非協調process B がその直後に空のdestination directoryを作る。
  4. A が flags 0 の `renameat2(staging, destination)` を行う。
  5. B の空 directoryは置換され、Aは成功する。
  6. resultとREADMEには limitationが入るが、materialize command自体は成功扱いになる。

  regular directoryへのhard linkを通常のprocessが作れないという親の主張は正しい。しかし、これは「file receiptと同じprimitiveをそのまま使えない」ことしか示さず、「既知の排他性低下を成功扱いのまま残してよい」ことは示さない。完成済みunique directoryへのsymlinkをcreate-only公開する間接方式なら file primitiveは使えるが、destination typeとconsumer契約を変えるため別裁定が必要である。

  成果物への影響を1行で言えば、`PUBLISH_EINVAL_FALLBACK` の成功物をreportや台帳や将来のcertified selectorが入力にすると、先に存在したdestinationを消したwriterと最終bytesのwriterを一意に証明できず、create-only由来の選択一意性が成立しない。
- 提案: 「Lustreではmaterializeをfail-closedにする」か、「indirect file pointerを公開境界にしてconsumerも変更する」かをユーザーへ返す。据え置く場合は、少なくともこの成果物をcertified選択へ昇格できないことを機械的gateにする。
- 推測か実証か: 空 directoryをflags 0 renameが置換する競走と、コードが limitation付きで成功することは静的実証。将来のcertified consumerへの流入は推測。

### 所見 12: 1回のscratch probeは本番経路の成功性、durability、consumer可視性を代表しない

- 深刻度: 高
- 根拠 (`file:line`): `s1-brief.md:15-23,67-70`、`verbatim-F870.md:8-18,23-26`、`verbatim-insight-a1-attempt0002-s5-s7.md:7-20`
- 事象の並び:

  親が測ったのは durable base直下の1つのdirectory、1つのinode、quotaに余裕がある時点、単独processでの空き先成功と既存先EEXISTだけである。次は未測定である。

  - 別OST: hard link自体はmetadata操作なので、同一Lustre内の別OSTだけでEEXISTが上書きへ変わるとは考えにくい。ただしstaging writeやfile fsyncのENOSPCを通じ、end-to-endの「公開できる」は覆る。
  - quota逼迫: staging write、metadata追加、directory fsyncがEDQUOTまたはENOSPCとなり、空き先成功の結論を覆す。
  - 同時実行: 一方がEEXISTになるのは期待どおりだが、nlink=2、cleanup、parent差し替えの中間状態を新たに作る。
  - nlink上限: EMLINKとなり、空き先成功を直接覆す。
  - 別mount点: stableな同一parentならsourceとdestinationは同一mountだが、mount namespace差やparent差し替えではEXDEVまたは別の実体への公開が起こり得る。
  - 別MDTやdirectory policy: 同じLustre名でもmetadata構成やACL、hard-link policyが異なればEPERMなどで空き先成功を覆し得る。
  - job bodyから見た同じpath: job bodyはpublisherではなくconsumerである。login nodeでlink直後に見えたentryとbytesがcompute nodeで期限内に可視になること、同じmount namespaceと権限で読めることは測っていない。
  - crash、link後fsync前、cleanup前、directory fsync失敗はいずれも未測定。

  既存destinationを置換しない性質はlink primitiveの契約として主張すべきで、1回のprobeを根拠に一般化すべきではない。probeが支えるのは「そのdirectory、その時点、そのprocessで空き先成功、既存先EEXIST」だけである。
- 提案: 本番の実directory深さと権限で、同時publisher、quotaまたはfault injection、link後のconsumer可視性、nlink上限、dir fsync失敗、compute nodeからの読取りを分けて測る。別OSTだけでなく別MDTを明示する。
- 推測か実証か: 未測定条件の列挙は資料から実証。各条件が実際のLustre構成でどのerrnoになるかは推測。

### 所見 13: 単純な `os.replace` 変異は赤になるが、completionだけを check-then-replace にした変異は予定テストを通り得る

- 深刻度: 重大
- 根拠 (`file:line`): `s2-plan.md:471-555,768-872,933-968`、`test_paper_story_a1_job_contract.py:2310-2360,2529-2556`
- 事象の並び:

  単純変異についてplanの主張は正しい。

  1. 共通 helperの `os.link(staging, occupied)` を `os.replace(staging, occupied)` に直接変える。
  2. occupied destinationが上書きされ、例外が出ない。
  3. submission M2とcompletion負例の `pytest.raises` が成立しないため赤になる。
  4. submission M1も `os.link` monkeypatchのboundary countが0となるため赤になる。

  しかし次のkind別変異は予定テストを通り得る。

  ```python
  if receipt_kind == "completion":
      if os.path.lexists(path):
          _remove_receipt_staging(staging, staging_identity)
          raise PaperStoryError(
              "no-replace completion receipt publish failed: File exists"
          )
      os.replace(staging, path)
      return
  os.link(staging, path, follow_symlinks=False)
  ```

  - submission M1/M2は正しいlink branchを通る。
  - completion occupied負例は期待messageを出し、bytes不変、staging不在になる。
  - completion clean正例はcanonical bytesとなり、stagingもrenameで消える。
  - AST wiring testは `_publish_completion_receipt` が呼ばれていることしか保証せず、この内部退化を検出しない。
  - 非協調writerがcompletionの`lexists`後、`os.replace`前にdestinationを作ると上書きされる。

  ほかにも、link failure testは「副作用なしで例外を投げるmock」なので、destinationを作ってからEIOを投げる不確定結果を検出しない。identity testは別inodeへの交換だけで、所見7の同一inode移動を検出しない。dir fsync順序、parent差し替え、symlink destination、hard-link destination、v3 completion stale stagingも未検査である。
- 提案:

  - submissionとcompletionの両方で、`os.link`直前に staging canonical bytes、destination不存在、`follow_symlinks=False` を検査し、real linkへ委譲するboundary testを置く。
  - real link直前に競合destinationを作るwrapperを使い、両kindがEEXISTとなり競合bytesを保存することを検査する。
  - real link後に `staging.unlink(); destination.rename(staging)` を行う同一inode負例を追加する。
  - stagingをforeign regular fileまたはsymlinkへ交換してからreal linkする負例を追加し、finalが残らないことを要求する。
  - `_fsync_directory` とcleanup seamにevent logを入れ、`link -> destination dir fsync -> staging unlink -> dir fsync` の実順を固定する。
  - v3 complete開始前にcompletion stagingを置き、result、receipt、sidecar、group terminalのいずれも新規作成されないことを検査する。
  - mutation検査では共通 helper全体の単純置換だけでなく、上記completion専用check-then-replace変異を必須survivorとして追加する。
- 推測か実証か: 単純 `os.replace` 変異が赤になることと、示したkind別変異が予定assertionを満たすことは静的実証。pytestは実行していない。

## 総括

親が裁定すべき択一は次である。

- 非協調な同 uid processによるparent rename、staging差し替え、同一inode移動を正しさ境界に含めるか、協調publisherだけを対象にするか。
- link可視化後、directory fsync前の状態を「公開済み」と扱うか、「公開済みだがdurability未確定」と別状態にするか。
- completionを揃えるなら、v3の不可逆成果物作成前にstagingを予約するか、途中失敗後に再開可能なcompleteへ変えるか。
- `submission-failure.json` も同じwaveでatomic publishへ直すか、partial failure receiptを既知欠陥として別裁定へ返すか。
- materializeはLustre上でfail-closedにするか、indirect file publishへ設計変更するか、排他性を落とした成果物を非certifying専用として機械的に隔離するか。

次を変えなければ実装してはいけない。

- `_publish_receipt` の `try` を staging writeより前まで広げ、write/fsync失敗でもowned stagingを処理する。
- `dir_fd` 不採用を撤回し、少なくとも同じparent descriptorでcreate、link、unlink、fsyncする。
- `published` boolを複数状態へ分け、destination dir fsync失敗を公開済み状態として分類する。
- cleanupへdestination identityを渡し、destinationが消えた状態で同一inode stagingをunlinkしない。
- source差し替え後にforeign inodeやsymlinkをfinalへ残す現行planを修正する。
- v3 completion stagingの予約または事前gateを、result系成果物の作成前へ置く。
- 所見7の同一inode移動、completion専用check-then-replace変異、parent差し替え、symlink/hard-link destination、fsync順序を負例へ追加する。
- 1回のscratch probeを本番成立の十分条件として扱わず、probeが証明した範囲をそのdirectoryと時点へ限定する。