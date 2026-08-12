## 総括

**NO-GO。** 数値の独立再計算には不一致がないため、数値 blocker はない。しかし次の防壁欠落が blocker であり、現プランのまま「§S7 #1〜#3 を閉じた」「gate を出荷可能」としてはならない。

1. **resolver が下流を支配していない。** submit、PBS preflight/driver/collector、唯一の受領証 writer、固定 semantic validator、certified 選択・材料レポート・試行台帳 consumer が本 session の scope 外である。
2. **Git trust root が未完。** same-fd `/usr/bin/git` は PATH 差替えには効くが、既に汚染された Git、動的 loader/library、repo-local config、commit-graph、alternates/partial clone、canonical common-dir の同一性を守らない。
3. **resolver 自身の trust root が無い。** descendant commit で resolver の `F_r`・期待 SHA・seal を変更でき、Python の seal/non-export も security boundary ではない。現行 `BlobRef` には `str` subclass による digest 比較迂回もある。
4. **祖先条件は実行時刻を証明しない。** pre-`F_r` の測定結果を保持し、後から `F_r` を merge した checkout へ貼り付けられる。さらに resolve 後に checkout を動かす stale-binding 経路も、submit 層が無いので未閉鎖。
5. **§S7 #3 は未完。** resolver が読む production raw path はないが、実際に TOCTOU 対象となる `fileRecord` consumer もない。加えて、承認済み record-items が要求する conformance-vector digest が、段 2 の manifest exact-key 集合から欠落している。

基礎 API を非公開で起草すること自体は可能だが、上記を解かずに land・export・完了記録へ進むのは反対する。

## 独立再計算

製品 parser/API を使わず、固定 commit の blob を直接読み、LF 込み行置換と SHA-256 を別実装で再計算した。

| 項目 | 親／段 2 の値 | 独立再計算 | 判定 |
|---|---|---|---|
| `F_r` | `39d760985a5e37d20464c394760bf65596156566` | 同一。`core.commitGraph=false` でも `F_r ≤ HEAD` | 一致 |
| `F_r:docs/decisions.md` | `ec588bb6…9cf` | `ec588bb6b8149b1d35e62246045771a4b9769a5a2b2de3160575bb1a6cec79cf`、1,200,423 bytes、13,006 行、CR 0、末尾 LF | 一致 |
| D282 構造 | heading/kind/fence 各一意 | ASCII `D282` 1、heading 1、decision kind 1、`text` opener/closer 各1 | 一致 |
| core の `較正` | 221 / 333 行の2件 | 2件、行集合 `{221,333}`。長い旧句は221行の1件 | 一致 |
| S7 old 行 SHA | 221=`225268a9…8e89`、333=`a7852ad9…9952` | 両方 full digest 一致 | 一致 |
| S15 old 行 SHA | 404=`6e87b981…681e`、424=`b5e2c7b2…b7d1` | 両方一致 | 一致 |
| v2 new 行 SHA | `92fd7175…01a4`、`b8741cc9…b37fe` | 両方一致 | 一致 |
| S15 のみ合成 | `d1782b04…de82` | `d1782b04ceb7cd56a3d10e2e6efb4eb7f90e6a89506a74bba727d34a5f79de82` | 一致 |
| S15 + v1 草案 | `dfb821a5…678c` | `dfb821a5ff0b085f7092bbd5536772a8c6728ec946291a6e6eb61da9fbef678c` | 一致 |
| S15 + v2 | `e0b0caea…8e0c` | `e0b0caeaca9300acffbb5cd6b81db7b6fb7fa8f9eeab81219affb4e2f94a8e0c`。逆順も同一、適用後 `較正` 0 | 一致 |
| v2 artifact SHA | `deedd71b…4df2` | `deedd71b97640213035c76dac1b22ea15bb21d447991000b0e433de873684df2`、16,614 bytes、249行 | 一致 |
| D282 pin 閉包 | target 1 + approved 6 | 7/7 の `(commit,path,sha256)` が一致し、7 commit とも HEAD の祖先 | 一致 |
| Python pin 差替え箇所 | 2 | 草案 path prefix は2箇所。承認 v2 path の現 pin は0箇所 | 一致※ |
| prereg file 行数 | 28 / 186 / 266 / 509 | 同一 | 一致 |

※「草案から v2 へ差し替える live site が2」という意味では一致する。ただし親 brief の「承認 blob path を pin する2箇所」という表現は誤りで、現時点の承認 v2 path pin は0である。

D282 の7 artifact は `F_r..HEAD` で差分なし。現 test が `dfb…`・221行だけを持ち、段2が `e0b…`・221/333へ直すとした診断も正しい。

## 攻撃所見

### 1. gate の支配点が存在しない — blocker

**(a) 攻撃手順**

1. 良い descendant checkout で resolver を一度だけ通し、binding を得る。
2. checkoutを別 commitへ動かす、または pre-`F_r` に取得済みの raw を持ち込む。
3. binding を再検査しない submit/writer、または resolver を呼ばない writer から受領証を publishする。
4. certified selector・レポート・試行台帳が受領証の申告値を読む。

親自身が writer、validator、submit/driver/collector、certified consumerを後続へ送っている。[s1-brief.md:17](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s1-brief.md:17) 現 package も「投入 gate ではない」と明記する。[__init__.py:3](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/__init__.py:3)

**(b) 成立条件**

- submit が同一呼出し内で binding と現在の checkout/job identity を再導出しない。
- binding 必須の writer 以外にも publish 経路がある。
- consumer が固定 validator を同一呼出しで再実行しない。

これは承認済み record-items が禁じている形である。[record-items-v2.md:719](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:719)

**(c) 成果物への波及**

preapproval／別 checkout の attempt が ineligible から eligible へ移り、certified 選択行・推定値・CI が変わりうる。材料レポートは良い binding の三つ組を表示しながら別 raw を材料にし、試行台帳は「承認後に実行済み」という偽の履歴を残す。

さらに段2の manifest exact-key 集合には conformance-vector digest がない。[s2-plan.md:94](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s2-plan.md:94) 一方、承認済み record-items はその digest を manifest が pin すると要求する。[record-items-v2.md:741](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:741) このまま exact-key manifest を発行すると、後続 validator は承認契約を満たせない。

### 2. `F_r` parser 自体の構造攻撃は現 blobでは不成立。ただし resolver source が自己承認する — blocker

**(a) 攻撃手順**

構造攻撃としては、四つの backtick fence 内へ偽 `## D282` と三つの `text` fenceを置く、別 decisionへ同じ見出しを置く、`D２８２`・zero-width文字を使う、といった入力を考えられる。しかし固定 `F_r` blobにはその材料がない。

実際に成立する経路は次である。

1. `F_r` の descendant commitで resolver sourceを変更する。
2. hard-coded `F_r`、`docs/decisions.md` の期待 SHA、parser、binding sealを同時に変更する。
3. その descendant自身を `measurement_head` として実行する。
4. 改変済み resolver が偽 manifestから bindingを発行する。

**(b) 成立条件**

resolver/Python sourceの identityが、repo外の launcher・承認済み source closure・署名済み配布物のいずれにも束縛されていないこと。D282は「trusted resolver」と書くだけで、その trusted 性を作る機構は今回のプランにない。[D282:12933](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12933)

**(c) 成果物への波及**

偽 manifestの core/erratum/record/schema三つ組が bindingへ入り、certified 選択、材料レポート、試行台帳の全 provenance が攻撃者の blobを指す。

したがって parser は必ず「固定 SHA-256照合完了後」にだけ動かし、Unicode normalizationをせず、fence delimiter長を追跡して fail-closedにすべきである。ただしそれでも resolver source trustは別途必要である。

### 3. Git/runtime/config trust root が未完 — blocker

**(a) 攻撃手順**

代表的な実経路は次の二つである。

1. 既に置換済みの `/usr/bin/git` を、内部で計算した digestだけ記録して実行する。比較対象となる承認済み Git digestがないので、悪性 binary自身が「観測された identity」になる。
2. callerが独立 clone/common-dirを渡し、repo-local include、partial-clone/promisor、または偽 commit-graphを置く。resolverは boundary文字列を比較するだけで実 common-dirを固定せず、偽 ancestryを採用する。

現環境では `/usr/bin/git` は動的 ELF、SHA-256 は `587ef21868c948b883993e23209b86a72a6ddc06aab1545c697ffc31075acd4a`、ownerは `uid/gid=65534/65534` である。したがって「root owner必須」なら現環境を拒否し、「現在 ownerなら信用」とすると外部 trust policyが必要になる。common-dirには実際に `objects/info/commit-graph` が存在する一方、段2は shallow/replace/graftしか挙げていない。[s2-plan.md:108](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s2-plan.md:108)

**(b) 成立条件**

- OS/root、または resolverが受理する common-dirを攻撃者が制御できる。
- arbitrary `repository_root`を canonical local main と照合しない。
- `core.commitGraph=true` のまま `merge-base`を使う。
- alternates、partial clone/promisor、local includeを拒否しない。

環境・設定経路の評価は次のとおり。

| 面 | 除去・拒否が必要な経路 | 判定 |
|---|---|---|
| ELF loader | `LD_PRELOAD`, `LD_LIBRARY_PATH`, `LD_AUDIT`, `LD_DEBUG*`, `LD_PROFILE*`, `GLIBC_TUNABLES`, `GCONV_PATH`, `LOCPATH`, `NLSPATH`, `MALLOC_*` | 現 allowlist方式を維持すれば ambient値は落ちる。ただし loader、共有 library、`/etc/ld.so.preload`、ld cacheは Git本体hashの外 |
| repo/object選択 | `GIT_DIR`, `GIT_WORK_TREE`, `GIT_COMMON_DIR`, `GIT_OBJECT_DIRECTORY`, `GIT_ALTERNATE_OBJECT_DIRECTORIES`, `GIT_INDEX_FILE`, `GIT_NAMESPACE`, `GIT_REPLACE_REF_BASE`, discovery/pathspec変数 | 全 `GIT_*` を捨てて固定値だけ再投入する必要あり |
| config注入 | `GIT_CONFIG`, `GIT_CONFIG_SYSTEM/GLOBAL/NOSYSTEM`, `GIT_CONFIG_PARAMETERS`, `GIT_CONFIG_COUNT/KEY_n/VALUE_n`, `HOME`, `XDG_CONFIG_HOME` | system/globalは `/dev/null` + `NOSYSTEM` で閉じられる。repo-localは残る |
| helper実行 | `GIT_EXEC_PATH`, `GIT_SSH*`, `GIT_ASKPASS`, `SSH_ASKPASS`, `GIT_EXTERNAL_DIFF`, `GIT_EDITOR`, `GIT_SEQUENCE_EDITOR`, `GIT_PAGER`, `PAGER`, `GIT_PROTOCOL_FROM_USER`, `GIT_ALLOW_PROTOCOL` | ambientは除去可能。partial clone時はrepo configから helperが再到達する |
| side effect | `GIT_TRACE*`, `GIT_TRACE2*`, `GIT_TRACE_CURL*`, `GIT_FLUSH`, `GIT_OPTIONAL_LOCKS` | 除去または固定。任意pathへの書込み・情報漏洩を避ける |
| config file | `.git/config`, common-dir `config`, `config.worktree`, `include.path`, `includeIf.*.path` | 段2に拒否策なし。includeから下記 keyを再注入可能 |
| command key | `alias.*=!cmd`, `core.fsmonitor`, `core.hooksPath`, pager/editor、credential helper、`core.sshCommand`、diff/textconv/filter/merge driver、difftool/mergetool、`gpg.program`、`remote.*.uploadpack`、`url.*.insteadOf`、`core.alternateRefsCommand` | 固定 builtinでは aliasは既存 commandを隠せず、fsmonitor/hooks/filter等も現在の object-only commandでは dormant。だが lazy fetchの remote/helper経路は到達可能 |
| graph/object metadata | shallow、replace、graft、commit-graph/split graph、alternates、promisor/partial clone、`commondir` | shallow/replace/graftだけでは不足 |

最低でも、`core.commitGraph=false`、alternates/partial clone/promisor拒否、local include/config.worktreeの検査、exact common-dir identity、固定 builtin allowlist、`--no-pager`、`core.fsmonitor=false`、`maintenance.auto=false`、`gc.auto=0` が要る。

**(c) 成果物への波及**

Gitだけの偽装では Python側の SHA-256 preimage検査を破れないため、直ちに任意 blobをD282 blobへ化けさせるわけではない。しかし偽 ancestryにより pre-`F_r` measurement／manifest commitを適格にでき、certified 選択へ混入させ、材料レポートと試行台帳に偽の承認順序を残せる。resolver source攻撃と組み合わされれば任意 blobまで進む。

**この防壁が守る範囲を1行で言うと:** same-fd `/usr/bin/git` が守るのは「ambient PATHとleaf path差替えで、hashしたGit本体とは別inodeを実行すること」だけであり、既に汚染された本体、loader/library、repo-local config/object graph、common-dir writer、resolver/Python、下流consumerは守らない。

`/proc/self/fd/<n>` はLinux依存である。現環境では存在するが、non-Linux、proc未mount、chroot/LSM制約では壊れる。`hidepid`単独は通常selfを隠さないが、依存してよいportable契約ではない。失敗時は必ず hard rejectし、`/usr/bin/git`再openやPATH実行へfallbackしてはならない。可能なら `execveat(..., AT_EMPTY_PATH)`/`fexecve` を採るべきである。

### 4. merge・stale bindingによる時間順序laundering — blocker

**(a) 攻撃手順**

1. `F_r` の祖先でない commit `C` 上で測定し、rawを保存する。
2. 後から `F_r` を `C` へ mergeし、descendant `M` を作る。
3. `M` で resolverを呼ぶ。`F_r ≤ M` は正しく真になる。
4. pre-`F_r` rawを `M` の測定結果としてwriterへ渡す。

別形として、良い `measurement_head` でbindingを得た直後にcheckoutを動かし、stale bindingでsubmitできる。

**(b) 成立条件**

submit/job prologueとcollectorが同じbinding・job identity・raw生成時刻を束縛せず、writerが現在HEADを再確認しないこと。これはfirst-parent検査でも完全には解けない。Git DAGはeventの壁時計順序を証明しない。

shallow/replace/graft拒否自体は実装可能で、現repoは shallow=false、replace 0、graftなし。ただし graft/shallow検査と ancestry commandの間のrace、commit-graph、alternatesは残る。同一権限writerを明示的に保証外とするなら、その前にcanonical common-dirを機械的に固定しなければならない。

**(c) 成果物への波及**

preapproval測定がcertified候補へ入り、選択結果が変わる。材料レポートは`M`をmeasurement headとして表示し、試行台帳は実際より後に承認された実験として記録する。

### 5. §S7 #3は「resolver-localにはrawなし、全体では未完」

**(a) 攻撃手順**

将来のsemantic validatorが `a03`、run log、intent、correctness evidenceをpathで検査した後、別openでhash/parseする。間にsymlinkまたはrenameでleafを交換する。

**(b) 成立条件**

`fileRecord` consumerがcomponent-wise `openat`、`O_NOFOLLOW`、同一fd/bufferを使わないこと。

現production resolverはまだ存在せず、prereg package内にraw evidence path読取はない。manifestは `approval_manifest_ref` から同じtrusted Git contextで読むべきで、worktree JSONを `Path.read_bytes()` してはならない。現存するraw読取はtestの草案読取だけである。[test_t139_preregistration_binding.py:827](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:827)

したがって段2の「global #3完了ではない」は正しい。ただし本sessionでも、manifestと7 blobがすべて同一Git runtimeのpinned blob経路だけを通る、というresolver-local部分は閉じられる。

**(c) 成果物への波及**

`a03`、run log、intent、G2 evidenceのbytesが検査時と利用時で変わり、certified選択の適格性、材料レポートの根拠、試行台帳のraw pointerが別物になる。

### 6. erratum ID membershipだけを迂回する直呼び経路が残る

**(a) 攻撃手順**

1. 承認v2と同じ `erratum_id`、同じ4 operation bytesを持つが、他のproseやblob identityが異なる文書を作る。
2. resolverを通さず `compose_core` または予定の `compose_core_from_blobs` を直接呼ぶ。
3. composition成功を「承認済み」と誤解してwriterへ渡す。

現 `compose_core` は `_ERRATUM_VALIDATORS` を直接呼び、`approved_erratum_ids()`も `_validate_erratum_registry()`も呼ばない。[erratum.py:477](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/erratum.py:477)

さらに現 `BlobRef` は `isinstance(value, str)` を許し、検査済みのexact `str`へ固定しない。[blobref.py:55](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:55) 64桁hexの`str` subclassで `__eq__→True` / `__ne__→False` とすれば、`actual != ref.sha256` を恒偽にできる。[blobref.py:130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/preregistration/blobref.py:130) `expected_composed_sha256`にも同型の問題がある。

**(b) 成立条件**

consumerがpure API成功、またはID membershipをapproval証明として扱うこと。resolver由来のbuilt-in `str`とauthority refsだけをbindingへ入れるなら閉じられる。

**(c) 成果物への波及**

proseだけを変えたvariantではcomposed digestとcertified数値は同じでも、材料レポート・試行台帳のerratum path/commit/SHAが未承認blobへ変わる。digest比較の`str` subclass迂回まで使えば、別composed bytesを成功扱いでき、certified選択も変わりうる。

なお、短い `_S7_OLD_TEXT="較正"` 自体は受理を広げない。固定coreでは出現がexact 2で、将来追加されれば件数検査がfail-closedする。`DRAFT_ERRATA=∅` も恒真ではなく、`approved | draft == registered` は `approved == registered` になる。ただしこの分類検査がcompose call pathに無いことが問題である。

### 7. 親の「6 blob」とD264非export検査は契約として不正確

**(a) 攻撃手順**

- 実装者が「6 blob」をliteralに取り、target coreまたはapproved roleの1件をfreeze/比較集合から外す。
- R5後の実API名 `verify_prereg_receipt` を半実装のままexportする。現testは禁止集合に旧名`verify_receipt`しか持たないため緑になる。[test_t139_preregistration_binding.py:865](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/orchestrator/tests/test_t139_preregistration_binding.py:865)

**(b) 成立条件**

stage 5がD282のexact 7 roleではなくbriefの件数を権威にする、または段2が「既存testでD264を機械保証」とした主張を信じること。[s2-plan.md:117](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t139-manifest-land2/s2-plan.md:117)

**(c) 成果物への波及**

比較対象から落ちたroleへ未承認blobを置ける。または未完成verifierが受領証を通し、certified選択・材料レポート・試行台帳を発効させる。

正しい数は **target core 1 + approved blobs 6 = 7三つ組** である。[D282:12893](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:12893)

「bytesを1 bitも動かさない」は、歴史blobについては三つ組再hashで機械保証できる。一方、D234はcurrent worktree pathの変化を明示的に許している。[D234:11017](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t139-manifest-w2/docs/decisions.md:11017) よって保証文は「このwaveのdiffで7 artifact pathを変更しない」「runtimeは歴史blobだけを読む」と書き分けるべきである。

## (P2)〜(P5) の評価

| 項目 | 親 brief | 段2 | 判定 |
|---|---|---|---|
| P2 | 誤り。PATHで解決したbinaryのdigest記録は認証にならず、正式receipt fieldもない | 親への反論は正しい。しかしfixed path/same-fdだけで「trusted」とした点は誤り。loader/config/common-dir/commit-graphが欠落 | **両方不十分、段2代案もNO-GO** |
| P3 | 同一fdは必要だが、component walk・regular/size上限・consumer結線が欠落 | global完了主張を退けた点は正しい | **段2が正しい。ただしmanifestのGit-only読取は本sessionで閉じるべき** |
| P4 | secure Git・trusted resolver・全consumerの再導出が真なら追加署名不要、という原理は正しい | conditional賛成も原理上正しいが、その前提を実装していない | **条件未充足** |
| P5 | multi-sessionと非exportは矛盾しない | この結論は正しい。ただし非exportはsecurity boundaryではなく、R5後の新名を現testが見ていない | **論理は正しい、機械保証の主張は誤り** |

## Scope判定と裁定パッケージ候補

現状は次の状態で、成果物が効く全層はscopeに入っていない。

| 層 | 状態 |
|---|---|
| D282 canonical payload | 実在・再計算一致 |
| manifest / resolver | 本sessionで予定 |
| submit / PBS preflight / driver / collector | scope外 |
| 唯一のreceipt writer | scope外 |
| fixed semantic validator / vectors | scope外。manifest keyも不足 |
| `a13` ledger consumer | scope外 |
| certified selector / material report / trial ledger | scope外 |
| public-core `b03` / pilot | 外部依存でblocked |

裁定パッケージ候補は次の4件とする。

1. **RP-T139-E2E-GATE-DOMINANCE** — resolver再導出、submit/job binding、唯一のwriter、固定validator、certified/report/ledger全callsiteとalternate writer census。
2. **RP-T139-GIT-RESOLVER-TRUST-ROOT** — canonical common-dir、Git binary/loaderをOS trustとするかdigest closureを持つか、repo config/object metadata、resolver/Python source identity、`/proc` failure policy。
3. **RP-T139-RAW-SNAPSHOT-CONSUMER-CLOSURE** — snapshot API単体ではなく、全`fileRecord` consumerへのcomponent-wise same-fd結線。
4. **RP-T139-PUBCORE-B03-PILOT-ACTIVATION** — public core stage2の凍結/fold、`b03`正本、pilot投入解除条件。

テストは指示どおり一切実行していない。ファイル変更もない。静的Git object読取、SHA-256再計算、設定・callsite検査のみを行った。