NO-GO です。P2 を棄却して短時間 lock を置く方向は妥当ですが、現 plan には trust 境界を破る must-fix が残っています。以下は編集・テスト実走なしの静的検査結果です。

## Real findings

### R1 — Critical: Git 2.34.1 の worktree porcelain は安全に構文解析できない

- file:line: [s2-plan.md:36](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:36)、[s2-plan.md:43](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:43)、[s2-plan.md:177](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:177)
- Git 2.34.1 の `worktree list --porcelain` は、worktree path と lock reason の unsafe byte を正しく quote しません。これを直す `-z` は Git 2.36 で追加されています。[Git 2.36 release notes](https://code.googlesource.com/git/+/8da1481bdcd6c85a0e8839df61a16180b9434f10/Documentation/RelNotes/2.36.0.txt)
- 攻撃 sequence:

  1. foreign worktree が改行を含む path、または改行を含む lock reason を持つ。
  2. 出力中へ偽の `HEAD`、`branch`、空行、`worktree <candidate>` field が注入される。
  3. 「safe basename を先に検査」「未知・重複 field は拒否」では、構文的に正しい偽 recordを区別できない。
  4. 少なくとも任意の land 拒否が可能。unregistered child の `.git` を既存 admin dirへ向けられると、登録済み identity の偽装余地も残る。

- 最小 fix: Git 2.34.1 を維持するなら、この porcelain を trust root にしない。common git-dir の `worktrees/*` を bytes・dirfd で走査し、child の `.git` → admin dir → `gitdir` backpointer を双方向に束縛する。代案は Git 2.36 以上を明示要件にして `--porcelain -z` を使うこと。
- 必須負例: 改行/invalid UTF-8 の worktree path、改行 lock reason、偽 record 注入、登録 admin dir の別 path alias。

### R2 — Critical: `shell=False` と hook 無効化だけでは任意 code execution / network を閉じない

- file:line: [s2-plan.md:106](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:106)、[s2-plan.md:108](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:108)
- 攻撃 sequence:

  1. local config に `filter.evil.smudge` / `filter.evil.process` がある。
  2. `.gitattributes` または `.git/info/attributes` が変更対象 path に `filter=evil` を付ける。
  3. `merge --ff-only` の checkout が外部 filter command を実行する。Python の `shell=False` はGit自身が起動する commandを防がない。[Git attributes](https://git-scm.com/docs/gitattributes/2.36.0)
  4. partial clone では不足 object の参照が promisor remote の lazy fetchを起動し得る。

- `post-merge` は fast-forward 後にも発火するため、`core.hooksPath` の固定も必須です。さらに `merge.verifySignatures`、fsmonitor、autostash、auto-maintenanceも固定しないと、追加 processや禁止済み stash が残ります。
- 最小 fix:

  - `GIT_NO_LAZY_FETCH=1`、`GIT_NO_REPLACE_OBJECTS=1`、`GIT_OPTIONAL_LOCKS=0`を安全値として再設定する。
  - hooks/fsmonitor/autostash/signature verification/auto-maintenanceを明示無効化する。
  - executable filter config と config-based hookを拒否するか、変更対象 path に filter が無いことを機械検査する。
  - global/system config を単に捨てると `core.autocrlf` や required filter 等の既存 checkout 契約を変えるため、「対応 repo 契約」か「unsupported なら拒否」を明示する。

現 snapshot の common config には active hook/filter はなく、hooks も sample のみです。ただし plan が謳う一般的な実行境界はまだ成立していません。

### R3 — High: `A,T,L` は受入証拠ではなく caller の自己申告

- file:line: [s2-plan.md:49](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:49)、[s2-plan.md:90](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:90)
- race sequence:

  1. acceptance は `A,T,L` で実施される。
  2. main が `C`、wave tip が `U` へ動く。
  3. buggy caller が現在値から CLI の `--accepted-*` と `--audited-commit` を再生成する。
  4. helper の exact 比較は全て通るが、`C,U` に対する acceptance は実行されていない。

- 最小 fix: acceptance runner が canonicalな schema固定 receiptを生成し、helper は個別 SHA argv ではなくreceiptだけを読む。receiptには repo identity、object format、A/T/L、受入 command結果、対象 checkout、gate digestを束縛する。main再同期時の `old-A..C` auditも別receiptとして残す。
- foreign receipt は指示として解釈せず、strict schemaのデータとしてのみ読む。

### R4 — High: helper crash 時に flock が merge child より先に消える

- file:line: [s2-plan.md:63](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:63)、[s2-plan.md:66](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:66)
- race sequence:

  1. Python helper が flock を保持し、`git merge` childを起動する。
  2. helperだけが SIGKILL / session死する。
  3. helperのFDが閉じて flock は解放されるが、Git childは継続できる。
  4.次helperがlockを取得し、先行Git childと同じmain worktreeを更新する。

- 通常の flock は全FDが閉じれば解放されるので、lock fileが残っても「stale lock」にはなりません。[flock(2)](https://www.man7.org/linux/man-pages/man2/flock.2.html) 問題は逆に、merge childの生存中に早く解放されることです。
- 最小 fix: merge childにもlock FDを限定継承させ、Git process終了までlock lifetimeを束縛する。filter/hooks/lazy-fetch/maintenanceを閉じ、FDを長寿命 descendantへ漏らさない。helper kill後もchildがlockを保持する境界テストを追加する。

### R5 — High: handoff/worktree identity の path-based TOCTOU と own-name 偽foreign化

- file:line: [s2-plan.md:28](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:28)、[s2-plan.md:30](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:30)、[s2-plan.md:38](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:38)、[s2-plan.md:41](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:41)
- race sequence:

  1. helper が `lstat` でregular file/dirを確認する。
  2. active foreign session がrenameして同名symlink、別inode、admin-dir aliasへ置換する。
  3. 後続の `open(path)` / `git -C path` は別objectを検査する。
  4. 検査済みbytes/inodeと、実際に例外許可したpathが一致しない。

- handoffの `st_nlink == 1` も一時点だけでは、検査後のhardlink/renameを捕まえません。
- `--own-handoff-name` はcaller typoだけで破れます。実own handoffを別名として渡すと、構文が正しいためforeign扱いで許可されます。
- また「child top-level と main の inode が同じ」は文字どおりなら常に偽です。等値にすべきなのは両worktreeから見たcommon git-dirの `(dev, ino)` です。
- 最小 fix:

  - container/child/handoffをdirfd + `O_NOFOLLOW` で開く。
  - `lstat` と `fstat` の `(dev,ino,mode,nlink)` を一致させ、読後にもpathが同inodeを指すか確認する。
  - status/worktree/pathはbytesで解析し、ASCII safe grammarをbytesへ適用する。
  - own handoff identityはbranchまたはacceptance receiptへ束縛し、wrong-own-name負例を追加する。

### R6 — High: graft fileで ancestry・L・ff-onlyを同時に偽装できる

- file:line: [s2-plan.md:53](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:53)、[s2-plan.md:106](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:106)、[s2-plan.md:179](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:179)
- 攻撃 sequence:

  1. common git-dir の `info/grafts` がTの親をAと偽装する。
  2. `merge-base`、`rev-list A..T`、`merge --ff-only` が同じ偽 ancestryを見る。
  3. `refs/replace` は空なのでplanのreplace検査を通る。
  4. 実commit object上はnon-FFなのにmain refがTへ動く。

`info/grafts` は commit の親をローカルに偽装する独立機構です。[repository layout](https://git-scm.com/docs/gitrepository-layout/2.24.0)

- 最小 fix: common git-dir の `info/grafts`、`shallow`、replace refsを明示拒否し、全Git呼出しでreplaceを無効化する。現 snapshot では三者とも不在だが、負例は必要。

### R7 — Medium: wave tipの「受入中に動けば破棄」がpostconditionまで実装されていない

- file:line: [s2-plan.md:55](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:55)、[s2-plan.md:64](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:64)、[s2-plan.md:96](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:96)
- race sequence:

  1. helperがwave HEAD/ref=`T`を確認する。
  2. wave側writerが`U`をcommitする。
  3. helperはimmutable `T`をmainへlandする。
  4. main=`T`、wave branch=`U`でも現在のpostconditionは成功し得る。

- 最小 fix: acceptanceからland完了までwaveをfreezeする協調lockを定義し、merge後にもwave HEAD/ref=`T`を再確認する。後段で動きを検出した場合は、既にmainを変更済みなので通常のrc24へ潰さず、`landed-T-but-wave-moved`として正確に報告する。
- `already-landed` も状態行列を固定するべきです。推奨は `C=A`ならland、`C=T`かつ同receipt・clean・wave=`T`ならalready-landed、それ以外はstaleです。

### R8 — Medium: gitlink検査のexact predicateが不足

- file:line: [s2-plan.md:62](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:62)、[s2-plan.md:106](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:106)、[s2-plan.md:178](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:178)
- 攻撃 sequence:

  1. `T` が nested path `external/ccbench` のmode `160000`を変更する。
  2. 非recursiveな `diff-tree --raw A T` は上位tree変更だけを返す。
  3. mode `160000` を検索する実装は変化なしと誤判定する。
  4. land後にmainのsubmodule worktreeがdirtyになる。

- 最小 fix: `git diff-tree -r --raw -z --no-commit-id A T`相当で、A/Tの最終treeにある全gitlinkのpath→OID mapが同一であることを検査する。「履歴中に一度でも変更」を拒否すると、変更後に戻したcommitやupstream mergeを過剰拒否するため、v1の性質は「accepted base Aからfinal Tへのnet gitlink不変」と明記する。

### R9 — Medium: ancestor race例は「未監査land」の証明になっておらず、過剰再受入を生む

- file:line: [s2-plan.md:19](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:19)、[s2-plan.md:53](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:53)、[s2-plan.md:74](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:74)、[s2-plan.md:186](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:186)
- sequence:

  1. `T1` が `T2` の祖先で、acceptanceは `L=A..T2` 全体を監査済み。
  2. process Pが`T1`をlandする。
  3. process Qが`T2`をlandしてもfinal treeと監査済みclosureは変わらず、`T1∈L`。
  4. planはこれを一律staleとして `9→6→7→8→9` 全再走する。

- これはexact-Aという運用policy違反ではありますが、未監査commitの混入ではありません。
- 最小 fix: 段4で二択を明示する。

  - exact-Aを保存則上の強いpolicyとして維持し、過剰拒否を意図したものと記録する。
  - または `A ≤ C ≤ T`、旧`L=A..T` exact、final T receipt不変なら再受入なしを許す。

flockを残す根拠はこのancestor例ではなく、次節のindex/worktree/ref非原子性です。

## Refuted

### X1 — 「exact比較 + ff-onlyだけで全raceがfail-closed」は棄却

二processに対するGitの保証は次の範囲です。

| 面 | 保証する | 保証しない |
|---|---|---|
| ref lock/CAS | branch refの原子的更新、Gitが読んだold HEADとの比較 | acceptanceのAとの比較、index/WT rollback |
| `index.lock` | index file writerの直列化とrename置換 | branch ref、working tree全体、precheck |
| working tree | 個別pathのcheckout | 全pathのtransaction、他process排除 |
| postcondition | 観測時点の不整合検出 | 復元、観測後の変更防止 |

Gitのfast-forward経路は `checkout_fast_forward()` でindex/worktreeを更新した後、`finish()` でold HEAD付きref更新を行います。[Git merge source](https://code.googlesource.com/git/+/8da1481bdcd6c85a0e8839df61a16180b9434f10/builtin/merge.c) ref CASが負けても既にindex/worktreeへ書いた内容はtransactionalに戻りません。

したがって、協調helper同士では専用flockが必要です。

### X2 — 「flock fileが残るとcrash後にstale lockになる」は棄却

flockはopen file descriptionに結び付き、全FD closeで解除されます。残存lock file自体はstale lockではありません。`LOCK_NB`なので長時間待機もありません。

現在のcommon git-dirはLustre上で、mount optionに`flock`があります。Lustreのcluster-wide coherent flockは対応mountで提供されます。[Lustre FAQ](https://wiki.lustre.org/Frequently_Asked_Questions)

ただしR4の「merge childより先にFDが消える」問題は別です。またSIGKILL後のGit自身の `index.lock` / ref `.lock` は残り得ますが、自動削除せずrc24で停止するのが正しい裁定です。

### X3 — 「merge commitのside parentはexact Lから隠せる」は条件付きで棄却

replace/graft/shallowを排除し、receiptのA/Tを固定すれば、`rev-list A..T` はmerge commitの全parentから到達する、Aから未到達のcommitを含みます。hidden/reordered/omitted commitのexact比較は有効です。穴はLの定義ではなく、R3のreceipt不在とR6のhistory modifierです。

## Scope外裁定候補

### S1 — High: 非協調writerまで保証するか

- file:line: [parent-brief.md:3](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/parent-brief.md:3)、[parent-brief.md:5](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/parent-brief.md:5)、[s2-plan.md:68](/home/SFC/tanab/github/izanagi/.codex/worktrees/dev-wave-skill/output/insights/2026-07-29_dev-wave-parallel-land/s2-plan.md:68)
- briefはClaude/Codex dev-wave session間を対象としているため、「全stage9 writerがhelperを使う」境界なら整合します。ただし明文化が必要です。
- 非協調race:

  1. helperがAを検証しcheckoutを開始する。
  2. direct writerが専用flockを無視してmain refをA→Cへ更新する。
  3. helperはindex/WTをTへ更新した後、ref CASで負ける。
  4. HEAD=C、index/WT=Tのdirty mainを残す。postconditionは検出するだけ。

- `reference-transaction` hookやCASだけではWT/index/refを一transactionにできず、同一UIDはhook設定自体も変更できます。
- scope内にするなら、main checkoutを単一writer daemon/専用ownerへ隔離し、他processに直接更新権限を与えない設計が必要です。

### S2 — Medium: cross-host filesystemを保証するか

現環境のLustre `flock` mountは対象にできます。NFSの`local_lock`、Lustreの`localflock`/`noflock`、異なるclient mount optionまで対応するなら追加契約が必要です。最小境界は「同一host、またはcluster-coherent flockが確認されたcommon git-dir」に限定し、lock errorはfail-closedにすることです。

### S3 — Low: detached/prunable/branch rename中のforeign worktree

これらを拒否すると、foreign sessionのcleanup中だけ一時的にlandが止まります。ただし「形式が正しい安定worktreeだけ例外」というP1には整合します。ユーザー要求が「どんな遷移中でも止めない」まで含むなら、安定snapshotの短いbounded retryを別途裁定してください。

## 総括

**NO-GO。** 短時間flockは削除せず、段4 must-fixを次に固定すべきです。

1. Git 2.34.1 のline-based worktree parserを撤回し、NUL対応版へのupgradeかadmin metadataのbytes/dirfd検証へ置換する。
2. Git filter、hooks、lazy fetch、fsmonitor、autostash、signature、maintenanceを含む実行面を閉じ、既存config契約は対応/拒否を明示する。
3. A/T/Lをcanonical acceptance receiptへ束縛し、own handoff identityとupstream auditもreceipt化する。
4. flock lifetimeをmerge childまで延長し、lock inodeの`O_NOFOLLOW`・`fstat`・`nlink/owner`を固定する。
5. graft/shallow/replaceを拒否し、gitlinkをrecursive NUL形式でnet比較する。
6. merge後のwave tipと`already-landed`状態行列を固定する。
7. 非協調writerはscope外と明記する。含めるならhook/CAS追加ではなくsingle-writer設計へ戻す。