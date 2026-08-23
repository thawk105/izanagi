現プランのままでは導入不可です。read-only のため pytest は実走しておらず、以下は静的検証だけの所見です。

### 所見 1

- 主張: cleanup は「自己所有」を証明せず、整合した被害対象の引数一式を渡せば他 session・他 repository の worktree を削除できる。
- 具体的な破れ方: 呼び手が別 session の `<main, worktree, branch, tip>` を一組そのまま取り違えると、common-dir、branch、tip、ancestry はすべて整合するため全検査を通り、被害 session の clean worktree と branch が削除される。同じ task slug の二重起動が既存 worktree を resume する実例もあり、land 後の遅延中に後着 session が同じ path を所有しても同じ結果になる。
- 根拠: ユーザー許可は「dev-wave 自身が作った worktree と branch」に限定される (`brief.md:19-21`)。一方 CLI は4個の自己申告引数だけで、所有者・acceptance wave・land receipt を受けない (`plan.md:42-61`)。lock reason も所有権証明に使わない (`plan.md:123-130`)。同名起動が同じ worktree を共有した実例は `docs/failures.md:6090-6107`。
- 提案する対処: **実装で閉じる**。作成時から land、cleanup まで引き継ぐ一回限りの capability/lease を設け、repository common-dir、worktree gitdir ID、path、branch、tip、session generation を束縛する。tool 自身の repository と `--main-worktree` の一致も必須にする。

### 所見 2

- 主張: path の inode 再検査と `rm -rf` は原子的でなく、検査済み path を別 directory に差し替えるだけで誤削除できる。
- 具体的な破れ方: 対象 P の最終 inode 検査後、別 session が P と sibling worktree Q を `renameat2(RENAME_EXCHANGE)` で交換する。続く `rm -rf P` は検査していない Q を削除し、事後検査は不可逆な削除後に `partial` を返すだけになる。同様に、削除走査中に重要 directory を P 配下へ rename すればそれも削除対象へ入る。
- 根拠: plan は binding 検査を順11に置く (`plan.md:69-80`) が、実際の順序は再検査の後に別 process の `rm -rf` を起動する (`plan.md:136-144`)。checker 自身も走査後に始まる process を観測不能と明記する (`tools/check_worktree_occupancy.py:4-10`)。
- 提案する対処: **実装で閉じる**。共通 lease を保持したまま、親 directory の fd に対する原子的 rename で対象を予測不能な quarantine 名へ移し、移動後の dev/ino/gitdir を再照合してから fd-relative に削除する。検査した canonical path と削除 argv が同一オブジェクトであることをコード上の型で固定する。

### 所見 3

- 主張: primary worktree や `.git` の直接指定は計画どおりなら拒否できるが、その保証は path 正規化の記述だけでは完成していない。
- 具体的な破れ方: `--wave-worktree MAIN` は primary 判定、`MAIN/.git` は worktree record 不在で拒否されるべきであり、直接入力による削除経路は計画上ない。しかし raw path、lexical absolute、`resolve()` 後の pathを別々に保持し、検査に canonical、`rm` に raw を使う実装なら、symlink、末尾 slash、`..` を介して検査対象と mutation 対象が分離する。
- 根拠: plan は「絶対・正規化 path」と symlink 負例を挙げるだけで (`plan.md:26,69`)、正規化の定義、raw==lexical==real の条件、mutation に使う値を規定していない。primary/common-dir/container 検査は `plan.md:70-74`。
- 提案する対処: **実装で閉じる**。raw argv に `..`、末尾 slash、symlink component があれば拒否し、`lstat` ベースの lexical path、strict realpath、porcelain path の byte-for-byte 一致を要求する。削除関数には検証済み path オブジェクト以外を渡せない構造にする。

### 所見 4

- 主張: branch の tip 再検査と `git branch -d` の間にも CAS がなく、別 session が再所有した branch を削除できる。
- 具体的な破れ方: cleanup が ref=tested-tip を再確認した直後、別 session が checkout せず同 branch を別の main 取り込み済み commit へ更新する。upstream 未設定なら `branch -d` は更新後 tip も merged と判定して branch を削除する。別 session が checkout した場合は `-d` が拒否するが、その時点で元 worktree directory と registry は既に消えており、partial state が残る。
- 根拠: ref/ancestry の再確認と `branch -d` は別手順である (`plan.md:140-144`)。F51 の縮退手順も、detach 後は branch が他処理から利用可能になることを前提にしている (`docs/failures.md:1726-1735`)。
- 提案する対処: **実装で閉じる**。repository-wide の cooperative lock を branch の最終照合から削除完了まで保持する。全 branch 操作者がその lock を守れないなら、自動 branch 削除は scope 外として裁定へ返す。`branch -d` の非0は、branch の事後不存在だけで成功へ読み替えない。

### 所見 5

- 主張: occupancy payload の検査条件が `unreachable.cwd_permission` を落としており、さらに P4 の `git status` 代用は process 不在証明にならない。
- 具体的な破れ方: 他 UID の process が対象を cwd にしていて `/proc/<pid>/cwd` が PermissionError になると、checker は `cwd_permission=1` を記録するが `issues` を増やさず `status=unoccupied` を返す。plan 記載どおり occupants/issues/same-UID 候補だけ確認すれば削除へ進む。計算ノード job は login node の `/proc` に一切現れず、read-only job なら status も空のままなので確実に同じ関門を通る。
- 根拠: 他ユーザー・non-dumpable・scan 後開始・別 PID namespace・FD は明記された盲点 (`tools/check_worktree_occupancy.py:4-10`)。他 UID の PermissionError は `cwd_permission` だけを増やす (`:262-276`) が、status は occupants/issues だけで決まる (`:424-439`)。P4 は status で代用する (`brief.md:51-52`) が、plan 自身も代用不能と認める (`plan.md:265-271`)。
- 提案する対処: **実装で閉じる**。最低限 `unreachable.cwd_permission == 0` も要求する。ただし remote job、FD、late start は lease でしか閉じないため、scheduler job ID を束縛した外部 lease と全 job の終端証明を cleanup の必須入力にする。

### 所見 6

- 主張: `git status --porcelain` が空でも、削除してよい byte 集合や job 不在は証明されない。
- 具体的な破れ方: `.gitignore` または `.git/info/exclude` に一致する job artifact、local cache、メモを対象 worktree に置くと、指定された status はゼロ byteを返す。occupancy scan 後に compute job がその ignored pathへ出力する状態でも cleanup は `rm -rf` を実行し、artifact を消す。
- 根拠: plan が要求するのは `status --porcelain=v1 -z --untracked-files=all` だけ (`plan.md:76,120-121`)。brief はこれを remote job 検査の代用にする (`brief.md:51-52`)。F251 では cwd 0件でも実際に7走が worktree を使用しており、削除で6走が破壊された (`docs/failures.md:7162-7187`)。
- 提案する対処: **scope 外として裁定へ返す**。「ignored bytes は無条件に廃棄可能」という方針がない限り、全 filesystem inventory を取り known-safe allowlist 外があれば拒否する。これは lease の代替ではないため、job 終端証明も別途必要。

### 所見 7

- 主張: `git worktree prune --expire=now` は単一対象操作ではなく、別 session の prunable record まで同時に消す。
- 具体的な破れ方: 対象 P の削除と同時に、別 session が unlocked worktree Q の directory を一時 rename しているとする。cleanup の global prune は P だけでなく Q の administrative record も削除し、Q を未登録 worktree にする。P だけを対象にした argv と事後検査ではQの損失を防げない。
- 根拠: mutation 手順は無条件の `worktree prune --expire=now` (`plan.md:139-144`)。対象だけが `prunable` でないことは要求するが (`plan.md:123-130`)、他 record が prune 対象でないことは要求していない。brief の I4 は「1 worktree ずつ」とする (`brief.md:32`)。
- 提案する対処: **実装で閉じる**。global lock 下で `worktree prune --dry-run --verbose --expire=now` の候補が対象1件だけであることを検査し、prune 前後の全 registry snapshot が対象以外で完全一致することを要求する。候補が複数なら停止する。

### 所見 8

- 主張: 親の rc/status 判定は land の部分成功を区別できるが、cleanup CLI 自身はその証明を持たないため、赤い land 後にも単独で削除できる。
- 具体的な破れ方: fold commit の検証後に finalize が失敗すると main は fold commit のまま、status=`fold-finalize-failed`、rc=30、active transaction が残る。この状態では tested tip は main の祖先なので cleanup 単体の ancestry 検査を通る。wave ref/worktree を消すと recovery が要求する wave HEAD/ref 検証を破壊する。`landed-postcondition-failed` でも main が tested tip に到達済みの形があり、同じく ancestry だけでは拒否できない。
- 根拠: finalize failure は verified commit 後に返る (`tools/dev_wave_land.py:2884-2896`)。recovery は wave HEAD/ref を要求する (`:2716-2721,2929-2937`)。`landed-postcondition-failed` は main_after=tested_tip の状態でも返る (`:3024-3055,3413-3421`)。plan は親が rcと `landed`/`already-landed` を確認するとするだけ (`plan.md:61`)。
- 提案する対処: **実装で閉じる**。cleanup に land が create-only で発行した一回限りの receipt を必須化し、rc=0、最終 status、tip、fold commit、active transaction 不在、lease generation を再検証して消費する。任意の `--land-status` 文字列ではなく authority を持つ receipt にする。

`already-landed` については、active fold があればそのまま成功返却せず recovery/fold へ進む (`tools/dev_wave_land.py:3237-3345`)。no-op の場合だけ `already-landed` が返る (`:3422-3462`)。したがって親が rc/status を厳守する限り、この区別自体は妥当である。

### 所見 9

- 主張: tip の ancestry は現在の branch tipしか保護せず、branch/worktree reflog にだけ残る commit を消失経路へ送る。
- 具体的な破れ方: branch が一度 commit U を指した後、tested tip Tへ reset/rebaseされ、Tはmainへland済みとする。worktreeはcleanで全preflightを通る。detach、directory削除、prune、`branch -d` により branch reflog と worktree側の回収手掛かりが失われ、Uは後のgcで消える。`branch -d` は現在のTがmergedであるため拒否しない。
- 根拠: canonical cleanup は削除前に dangling audit の rc=0 を必須とする (`cleanup-branches.md:17-18`) が、新 plan にはこの工程がない。F118 は branch 消失で4 commitが到達不能になった実例と audit の導入を記録し、同 audit も既存file変更等を検出しない限界を持つ (`docs/failures.md:4190-4208`)。
- 提案する対処: **実装で閉じる**。削除前 audit を復活させ、branch/worktree reflog 中の main 非到達 commit も検査する。削除前に期限付き rescue ref と manifest を作り、一定期間後の別工程でのみ expire する。完全不可逆な即時削除を要求するなら裁定へ返す。

### 所見 10

- 主張: I5 の「冪等」は成功後の二度目しか扱わず、mutation 中断からはほとんど再入できない。
- 具体的な破れ方:

  - unlock 後停止: 次回は進めるが、間の期間は既存保護 lock を失う。
  - detach 後停止: 次回は「branch に接続」を満たさず拒否される。
  - `rm -rf` 中断: directory は半壊し、status/path binding 検査で拒否される。
  - directory 削除後・prune 前: stale recordとbranchが残り、通常preflightにも`already-clean`にも該当しない。
  - prune 後・branch削除前: branchだけが残り、同じく再開不能。
  - branch削除後・postcondition前: この状態だけ次回`already-clean`になれる。

- 根拠: 通常 preflight は branch-attached を要求 (`plan.md:72-79`) し、`already-clean` は path・record・branch の全不存在だけを許す (`plan.md:168-175`)。`--resume` は明示的に設けない (`plan.md:58-59`)。plan 自身が rc=30 は部分状態と認める (`:154-175`)。
- 提案する対処: **実装で閉じる**。対象外 directory に fsync 付き transaction journal を置き、各phaseと期待inode/gitdir/ref SHAを記録する。各prefix stateを明示的に再認識してCAS付きで再開する。これを実装しないなら「非0なら無変更」というbrief契約を撤回し、partialは自動再試行禁止にする。

### 所見 11

- 主張: F26 の三罠は方針上は避けているが、コードでの構造保証と実体submodule検証が不足している。
- 具体的な破れ方: 単数CLIにより8本一括loopは避けられるが、1本の巨大なsubmodule worktreeに対する`rm -rf`がtimeout/killされれば、その1本は半壊し再入不能になる。また禁止argvの静的literal検索は、動的に組み立てた `("worktree", mode)` や別wrapper経由を検出しない。実submoduleを作らないテストでは共有configが不変かも確認できない。
- 根拠: F26 の実事故は remove拒否、deinitの共有config破壊、loop killによる半削除 (`docs/failures.md:552-582`)。同config消失には機序未同定の再発もある (`:608-618`)。plan は source/argv spyだけを予定し、実submodule fixtureを作らない (`plan.md:193-196`)。
- 提案する対処: **実装と検査で閉じる**。git wrapperを許可commandのruntime allowlistにして禁止verbを構築方法に関係なく拒否する。実submodule worktreeでmainの `.git/config` と `git submodule status` の前後不変を検査する。rm kill後のjournal再開も必須にする。

### 所見 12

- 主張: 親の「実測済み前提」と予定テストは、競合する実運用へ一般化できない。
- 具体的な破れ方: 一時repo正例ではoccupancyをrc=0 fixtureへ差し替えるため、他UID、non-dumpable、remote node、FD、late startを一件も通らない。初期symlink負例やcommand失敗注入が通っても、「最終検査後にpath/refを交換する」競合は残る。1回のdogfood成功も同時実行者がいないhappy pathしか証明しない。
- 根拠: 正例はoccupancyを差し替え (`plan.md:179-187`)、競合ではなく各commandの失敗だけを注入する (`:189-196`)。brief の測定は特定 checkout `59ef288c` での docs件数、byte、baseline、lock観測に限定される (`brief.md:55-63`)。さらに段2後の訂正で当初P1が既裁定と矛盾していたこと自体が、単発調査の不完全さを実証している (`brief.md:70-86`)。
- 提案する対処: **検査で閉じる**。各TOCTOU境界にbarrierを設け、別processがpath交換、ref更新、checkout、late process開始を行う決定的競合テストを追加する。checkout固有のbyte/baseline/lock観測は安全根拠から外し、各実行時のruntime identity/lease検査へ置き換える。

## 総括

(a) 最も危険なのは、所有権のない整合済み引数一式で他 session を消せること、最終 inode 検査後の path 差替え、remote jobを `git status` で不在扱いすることの3点です。

(b) 現状では入れてはいけません。最小防壁は、landからcleanupまで切れない一回限りlease/receipt、原子的quarantine＋repository-wide lock、remote job終端証明とpartial-state journalです。branch削除にはCAS相当の排他と期限付きrescue refも必要です。