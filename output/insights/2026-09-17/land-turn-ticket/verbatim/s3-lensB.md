## 前提の検算 (brief・plan の行番号と主張)

**現案のままでは、要求された進行保証を主張できない。** 非横取り grant と証拠保持は有効だが、再試行時の後続への引渡し、元 request 不在の recovery、registry lock の公平性が未確定である。テスト案にも、実 fold gate を worker thread で実行できない具体的な障害がある。

以下の略記を用いる。

- **brief**：[s1-brief.md](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-land-turn-ticket/s1-brief.md)
- **plan**：[s2-plan.md](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-land-turn-ticket/artifacts/dev-wave-land-turn-ticket/s2-plan.md)
- **裁定**：[rulings-verbatim.md](/work/1/SFC/tanab/dev-wave-jobs/worktree-dev-wave-land-turn-ticket/rulings-verbatim.md)
- **先行相談**：[out-liveness.md](/work/1/SFC/tanab/dev-wave-jobs/land-progress-consult-20260917/out-liveness.md)
- **land / cleanup / test / conftest / runner**：指定 repo の `tools/dev_wave_land.py`、`tools/dev_wave_cleanup.py`、`orchestrator/tests/test_dev_wave_land.py`、同 `conftest.py`、`tools/run_tests.py`。

**real** は現物または記述された設計から確認できる問題、**refuted** は攻撃仮説・保証主張が成立しないもの、**未確認** は設計や実測が不足するものとする。指定ファイルを読み、変更・pytest 実行はしていない。

| 主張 | 判定・検算 |
|---|---|
| brief:7、P2（brief:15）の「生存最小 seq が先頭」 | **real：plan は仕様を変更している。** plan:85–93 は休止票より現 grant を優先する。必要な補正だが、厳密な成功順 FIFO とは異なる。 |
| P3（brief:16）の「180 秒を残して期限まで待つ」 | **refuted：旧 availability cap を維持する説明にはならない。** plan:135–138 は実競合待ちが180秒を超えることを正しく認めている。 |
| P8（brief:21）の「8本全完了」 | **未確認。** plan:309 の累積 tip 列は条件付き正例。独立 branch は plan:310 の merge・再投入まで必要。 |
| brief:7(f) の死亡 fold recovery 優先 | **real：優先と復旧実行は別。** plan:425–427 は元 request 再投入を外部条件としており、復旧主体を作っていない。 |
| plan:285–296 の thread＋実 gate | **real：実装上の障害。** `land:3806` の `signal.signal` は worker thread で実行できない。 |
| 指定された「runner の受入5分上限」 | **refuted：指定現物に一律300秒の執行は確認できない。** `runner:79` は shard deadline **5100秒**、`2351` が適用点。5分を別途受入目標とすることと、コードの強制上限は区別が必要。 |

## 進行保証の反例 schedule

**1. real：480秒 timeout の最古 request が、成功可能な後続を繰り返し追い越せる仕様の穴。**

根拠：`land:3017–3024` は timeout を `retryable_same_request=True` にする。plan:87–101 は休止 seq を保持する一方、終了時に待機中後続へ grant を原子的に引き渡すとは定めていない。

具体的 schedule：

1. A(seq=1)、B(seq=2) を登録。B は成功可能。
2. A の provenance が480秒で timeout。A の grant とFDが解放される。
3. B が次の選出を行う前に A が同じ key で再入する。
4. grant 不在なので最小 seq の A が再び選ばれる。
5. これを反復。Bにも毎周期CPU時間は与えられるが、観測時には常にAが先頭。

赤を拒否するだけでは失敗分離にならない。**grant 解放と、その時点で待機していた後続への引渡しを同じ registry 更新で確定する規則**が必要である。これは receipt の受理条件を変えずに詰められる。

なお、確定した赤の seq を必ず破棄する解釈なら、この特定 schedule は消える。しかし plan:101 は「削除可能」で、timeout の扱いと再試行順位保持の関係が未確定である。

**2. refuted／real：単一 provenance の queue 待ちが、そのまま3600秒続くという想定は正しくない。ただし順番期限切れによる成果破棄は残る。**

`land:2958` の subprocess timeout は480秒。したがって通常の provenance 呼出し一回で3600秒 queue 待ちする想定は **refuted**。

一方、次は **real**：

- B は登録後3200秒で grant を得る。
- provenance が430秒で緑になる。
- plan:145–151 の再取得 loop に戻った時点で期限超過。
- main が変わらず flock が空いていても、記載どおりなら成果を破棄して rc=11。

「有限時間で緑になる」だけでは、「この invocation が残期限内に mutation へ到達できる」を含まない。FIFO はこの差を埋めない。

また、共通の絶対期限を採るなら、各180秒枠の deadline を `turn_deadline` で切る必要がある。残10秒で180秒枠へ入る境界は、plan:147 の記述だけでは閉じていない。

**3. real：生存 hang は止める主体がない。**

根拠：plan:164、437。`land:568` の Git 呼出しなど、順番期限が割り込んで停止させる構造ではない。

Schedule：AがgrantとFDを保持したまま停止し、B以降は3600秒ごとに終了・再入する。FDが保持される限り追い越せない。

これは「検査・I/Oが有限時間で応答する」という前提の外なので、その条件付き定理自体への反例ではない。しかし **hang 耐性を完了条件に含めるなら未実装**である。必要な形は「責任主体がAを停止する→子も含む停止とlock解放を確認する→状態に応じて引き継ぐ」。TTL追越しでは解消しない。

**4. refuted：旧 driver 混在でも進行する、という強い読み。**

根拠：brief:7(a)、plan:113、433、`land:2663–2675`。

Schedule：旧driver群が、新先頭Aの各試行直前にcommon flockを取得し、短時間後に解放する。各保持は有限でも、Aは毎回競合し3600秒で降りる。これを反復できる。

common flock は正しさを守るが公平性を与えない。「新driver同士だけの保証」は、**旧driverによる妨害が有限で終わることまで条件に入れない限り、着地の進行保証ではなく内部順位保証**に留まる。

**5. real：元 request 不在の recovery は全体停止を残す。**

根拠：plan:425–427、`land:5144–5147`。

Schedule：

1. Aがfold stateを永続化して死亡。
2. Bは成功可能な別waveだが、通常grantはrecovery優先で停止。
3. Aは再投入されない。
4. B以降は何度再試行しても復旧できない。

これはplan自身が認めた限界であり、元requestをschedulerが人工的に再投入する test:案（plan:318、324）では反証できない。

F977の実例は「rollback済みのwaveを誰も再landしない」であり、未完stateによる全体停止と同一事象ではない。ただし、**当事者不在では再投入が起こらない**という運用上の欠落は共通する（裁定:401–414）。

**6. real：公平性を registry flock へ移しただけになる余地。**

根拠：plan:55、81–83、295。

短いcritical sectionが有限時間で終わっても、取得者の公平性は導けない。例えば、Aのregistry取得試行のたびにBの待機票確認がlockを保持し、Aのsleep中にだけ解放する周期を繰り返せる。全workerが有限時間ごとに実行されても、Aの取得は成功しない。

plan:295 の「有限stepで解放」は不足する。必要な前提が **lock取得の公平性まで含むscheduler仮定**なのか、実装が進行を確保するのかを明記する必要がある。

## 公平性と再試行

| 照合key | 判定・具体的schedule |
|---|---|
| waveだけ | **real：粗すぎる。** 同waveの別tested_tip／別受入requestが旧seqを借りられる。 |
| wave＋tested_tip | **real：異なる受入証拠を同一順位へまとめる。** Aがreceiptを再発行しても旧seqへ戻れるため、「同一受入request」の保証にはならない。 |
| wave＋tested_tip＋raw receipt digest | **refuted：別waveが普通に他人のseqを奪える、という攻撃。** plan:73 のpath/common/tested_main照合と、`land:986–991` の照合を守れば別requestは一致しない。ただし実装・testは未確認。 |
| 同上でreceipt再発行 | **real：bytesが変われば自分のseqを失う。** log digest等が変わった新receiptは新key。これは設計どおりだが、wave単位の永久順位保持とは呼べない。 |
| landing_tipをkeyから除外 | **refuted：通常の前進mergeだけで順位を失う、という攻撃。** 元receipt・tested_tipを保てば同key。plan:73どおり旧provenance／fold証拠は失効させる必要がある。 |

さらに二つの未確定点がある。

- **未確認：同一keyの二重起動。** AのFDが生存中にA′が同keyで登録した場合、第二のticketを作らず、現grantを変更しない契約が明記されていない。別openの生存確認とregistry下の一意性を同じ境界で検証するtestが必要。
- **未確認：終端とseq廃棄の対応。** plan:101 の「確定したmutation前拒否」を広く解釈すると、`land:2808–2815` のstale-main後にseqを消し、正規の前進merge再試行でも順位を失う。rc・retryable・active state別の処理表が必要。

追越し窓の判定は次のとおり。

- **refuted：登録済みAと新規Bのinitial flock競争。** 登録公開・grant更新がregistryで直列化され、grant保有者だけinitialへ進むなら、BはAを追い越せない（plan:55–61、85–91）。
- **real：死亡／終了回収と再入の間。** 後続への原子的引渡しがなければ、前節のA再入scheduleが残る。
- **未確認：recovery優先判定中。** 「通常grantを止める」印をregistryに確定してからcommon lockへ進む必要がある。死亡確認後、印を付ける前にregistryを解放すると、Bが通常grantを取る窓になる（plan:100、425）。

## 待ち予算の整合表

| 予算・処理 | 値／起点 | 実際の意味・問題 |
|---|---|---|
| land順番期限 | 提案3600秒、repository検証直後 | 登録前検査・順番待ち・監査等の経過も消費する。処理全体のwatchdogではない（plan:117、135、164）。 |
| common flock待機 | 現行180秒累積 | lock外作業は差し引かない。提案では180秒消費後も待つため、総待ちcapではなくなる（`land:4059`、plan:136–138）。 |
| provenance | subprocess 480秒 | queueを含む呼出しのtimeout。前後のGit検査まで一括480秒ではない（`land:2948–3024`）。 |
| fold gate inner | 130秒＋終了grace10秒 | pytest子の監督（`land:168–170`、3863–3868）。 |
| fold gate outer | 145秒 | materialization～cleanup。selectionと事前receipt検査はwatchdog開始前（`land:3940–3944`）。 |
| 受入lease | 資料上TTL2400秒 | plan:176、438の値。`wave_land_window.py`は必読射影外のため本段では実装を追加検査していない。 |
| CLI renew | `land()`前に一回 | renew失敗でもlandへ進む（`land:5664–5686`）。 |
| CLI release | 終端後、条件付き | `release_safe`かつ非retryable。holderと元tested_mainを渡す（`land:5699–5735`）。 |
| 受入shard親 | 5100秒 | `runner:79、2351`。300秒とは異なる。 |
| real-repo lock | 245秒 | `conftest:1031`。受入全体の所要上限ではない。 |

**real：3600秒はD432／D1996の改訂であり、名前を分けるだけでは正当化できない。**

D432は180秒をavailability capとし（裁定:37–47）、D1996は待機増量による監査同時流入を理由に増量を却下した（裁定:123–128）。新driver間ではgrantによって同時流入を防ぐため、改訂理由は構成できる。しかし混在期にはその理由が全面的には成立しない。plan:138の明記は維持すべきである。

**real：lease保持は3600秒待機と両立しない。ただし、TTL失効だけで `expected_main_sha` 不一致になるとは限らない。**

Schedule：Aがt=0でrenew→t=2400以降に失効→別claimまたは同名requestの別mainによるclaim→Aがt=3000以降にrelease。holderまたはmain照合によってrelease拒否となる可能性がある。leaseが単に失効した場合と、別内容へ置換された場合を分ける必要がある。

releaseの引数を現mainへ置換して通すべきではない。必要なのはplan:178どおり、TTL跨ぎで**他のleaseを消さず、land結果とrelease結果を区別する**CLI testである。

## cleanup との交錯

**1. 自wave撤去：通常cleanupによる実行と、強制的な消失注入を分ける必要がある。**

- **refuted：通常の自己cleanupが、未landの実行中waveを自由に消せる。** ancestry、occupancy、fold stateの検査がある（`cleanup:813–855、970、993`、裁定:379–383）。
- **real：待機／監査／gate中に自waveが実際に消えれば、landは次の再取得・binding検証で拒否する。** `land:2602–2627、1631–1643`。scheduleは「lock解放→wave消失→再取得」で構成できる。
- **未確認：手動cleanup側まで含めた全経路の保証。** 本段の射影には手動dispatcher本体がない。process occupancyの観測と削除の間の全raceを、P6だけで閉じたとは言えない。

**2. 無関係child撤去：P5で消えるのはbinding観測の競合。**

**refuted：P5後も同じchildの`.git`消失で `_worktree_snapshot` が落ちる。** plan:209–218どおりopen前に除外すれば、その読取り自体がない。

対照scheduleは「container列挙→無関係childの`.git`消失→snapshot継続」。現行は `land:1691→1226` で拒否し得る。自wave／衝突対象にはこの除外を適用しない。

ただし **real：cleanup全体との非接触ではない。** plan:245が残す `_registered_worktree_paths` と、plan:273のcleanup側admin一覧読取りがある。

**3. admin直接削除中の一覧読取り：安全性と無停止性は別。**

根拠：`land:3460–3482、3823–3831`、plan:249–269。

Schedule：cleanupが対象wave directoryを消す→adminを部分削除→landが`git worktree list --porcelain`を読む。

- Gitが非zeroならlandはfail-closed。
- Gitが対象recordを省略して成功しても、対象directoryが既に不在なら、その省略だけで生存worktreeへの隔離先重複が生じるとは言えない。
- **未確認：各削除途中状態でGitが返すrc／recordと、その後のland結果。** 既存 `test:9316、9339` は欠損状態の静的testで、adminの段階的削除との交錯ではない。

cleanup側も **real：fail-closedは「無変更」を意味しない。** 現行 `_mutate` はdirectory撤去後の失敗をpartial mutationとして返す（`cleanup:972–1008`）。P6でもadmin削除途中に失敗すれば残骸は残り得る。plan:267のbranch削除停止に加え、その状態から対象限定で再入できることを確認する必要がある。

## test の決定性と代表性

**1. refuted：同一processだから実flock競合を再現できない。**

別々のopen file descriptionを使えば競合する。既存 `_held_land_lock`（`test:527`）とproductionの `_open_lock` は別openであり、fixtureの方向は妥当。同じFDや`dup`をworkerへ配ってはいけない。実probeは本段では未実行。

**2. real：threadで実 fold gate を走らせる案は、そのままでは成立しない。**

`land:3806` はSIGALRM handlerを設定し、`3934`から呼ばれる。worker threadでは失敗する。plan:296の「実検証」とplan:285のthread採用を一括して満たせない。

scope内の修正は、**順番状態機械のthread testと、実gateを各processのmain threadで動かす統合testを分ける**こと。thread testでgate seamを固定した部分は、実gate検証済みと数えない。

**3. 未確認：Conditionを使うだけでは決定的にならない。**

plan:291–303はcwd・global patch・時計の問題を認識しており妥当。ただし次を固定する必要がある。

- 同時刻イベントの順序。
- worker起動時と例外終了時のtoken返却。
- registry登録／grant公開／死亡回収の交代点。
- fake時計を進める唯一の主体。
- GILやOSの起床順に依存しないworker選択。

既存 `_FakeLandLockRuntime.sleep` は単純加算（`test:507–511`）。そのまま8workerへ共有すると、同時の待ちを直列加算して期限を早める。

**4. real：旧負例の再現仕様はまだ足りない。**

plan:326の「同じscheduler policy」は正しい。全員監査到達barrierは新構造ではdeadlockする。

一方、plan:328は旧treeで8本全timeoutを「親のprobeで実証」としているだけで、policyを提示していない。必要な記録は、各requestの取得・解放・監査・gate・累積待ち・rc・main SHAである。旧版に存在しないturn hookへ到達しないため落ちたtestは負例にならない。

**5. refuted／未確認：実flock＋tmp repoは、自動的にreal-repo lock対象ではない。**

`conftest:2226–2237` はnode inventoryからaccessを決め、accessなしなら `1454–1456` でlockを取らない。指定inventory検索には `test_dev_wave_land.py` の登録がなかった。したがって「実flockだからF976 lockを取る」は **refuted**。

ただし、追加fixtureが本repoの可変状態へアクセスするなら再分類が必要。所要20～60秒（plan:388）は **未確認**であり、既存136.355秒という台帳合計から受入wall-clockは算出できない。

**6. 変異の専属帰属は、現在のmatrixでは成立していない。**

| 変異 | 判定 |
|---|---|
| M1 | **未確認。** mutation直前guardが残るので、失敗点は順序違反ではなく後続拒否にもなり得る。旧全停止の再現にはならない。 |
| M2 | **未確認。** 外部再入で旧seqとの比較が必要。同一invocation待ちだけでは殺せない。 |
| M3 | **未確認。** owner自身の期限終了前に、他workerがTTL追越しを試みるscheduleが必要。 |
| M4 | **未確認。** ff／foldを別変異にする方針は妥当。別binding検査による拒否を固有guardの検出力と混同しない。 |
| M5 | **未確認。** 後段のactive-plan origin照合も拒否するため、「後続未入場／元票保持」の観測点が不可欠。 |
| M6 | **未確認。** 更新後の既存累積待ちtestも殺し得る。新test専属とは未証明。 |
| M7 | **未確認。** 後段検証で同じ拒否なら生存する。plan自身もこの可能性を認めている。 |
| M8 | **real：専属帰属の競合がある。** plan:241–243で成功へ反転する既存alias／不正名testも、広く旧観測を戻す変異に反応し得る。exact置換が必要。 |
| M9 | **real：新testだけという計画ではない。** plan:345は既存 `test:4246` もkill担当に指定している。 |
| M10 | **real：単一test専属ではない。** plan:346はstale-admin testとargv禁止testの二つを指定。禁止側で先に止まれば、foreign admin保持の検出力を示せない。 |
| M11 | **未確認。** 後段の受入拒否では不十分。登録前にseq未消費・ticket不在を観測できる必要がある。 |

実装後にexact mutationと指定nodeを固定し、指定nodeの単独結果と既存test側の結果を分けて帰属を判定すべきである。**現時点でKILLED済みは一件もない。**

## 親 brief への反証

**P3 — real：186秒一走は3600秒の根拠として不足する。**

brief:16の算術も、186秒×13本は **2418秒＝40分18秒**であり、約43分ではない。最後の一本が開始するまでなら12本分＝37分12秒で、何を含む時間かを定義する必要がある。

より本質的には、186秒は上限ではない。例えば一件あたり「provenance470秒＋gate120秒＋その他10秒」の全緑scheduleでも、13本目の開始は7200秒後になる。cold fallbackの残余も先行相談:23が指摘している。

3600秒を運用上の応答期限として選ぶことはできるが、**有限N本の全完了を導く数値ではない**。

**P7 — refuted：M1だけで旧構造の負例を恒久化したことにはならない。**

brief:20は旧tree probeとM1を併用する。plan:328の補正は必要である。

M1には新しい証拠保持と3600秒待機が残るため、全員が旧180秒予算を使い切るとは限らない。「順序が崩れた」と「8本全員が予算切れ」は別の負例である。

**P8 — real：既存fixtureの拡張という表現は実装量を過小評価している。**

既存fixtureは一つのlandと一つの妨害holderのschedule（`test:3414–3485`）。複数requestの共有時計、独立receipt、cwd切替、終了処理、実gateのsignal制約を新たに扱う必要がある。

**brief:3、7 — real：完了条件と保証条件の粒度が合っていない。**

「8本一つのscheduleで完了＋非等価変異全KILLED」は重要な検証だが、registry取得の公平性、失敗再入、元request不在を一般に証明しない。またP5は意図的に拒否を狭めるため、brief:22の「拒否は狭まらず」はscope記述とも整合しない。

## 裁定パッケージ候補 (scope 外)

以下は今回の推奨実装へ混ぜず、保証範囲を広げる場合に分離する。

- **元request不在の自動復旧主体。** plan:426のcwd・binding・receipt・結果帰属を満たす再起動責任を誰が持つか。別waveのorigin照合を緩める解決は不可。
- **生存hangの停止・停止確認・引継ぎ。** 現案には監督主体がない。親だけの死亡ではmerge childのcommon lockが残り得る（`test:7213`）。
- **lease保持をland待機全体へ広げる契約。** 現scopeでは保証しないと明記する。定期renew・再claimを本変更へ追加しない。
- **新receiptでもwaveの順位を引き継ぐ契約。** 現keyでは別requestとなる。変更するならrequest同一性の裁定が必要。
- **共有admin一覧の完全非接触化。** P5/P6の対象限定からさらに広げる場合の別問題。今回の部分削除交錯test自体はscope内で必要。

## 総括

**author前に、少なくとも次の四点をplanへ確定させる必要がある。**

1. timeout／死亡／stale／確定赤ごとのseq処理と、待機中後続への原子的grant引渡し。
2. 進行保証の追加前提――registry取得の公平性、期限内に成功できる機会、旧driver妨害の終息、元requestのrecovery再投入。
3. thread状態機械testと、実gate・実process死亡testの分離。
4. 旧tree全停止probeの具体的policyと、各変異のexact nodeへの帰属方法。

現案が支えられるのは、**条件付きの順序制御と、同一invocation内の競合による証拠破棄の削減**までである。元request不在や生存hangを含む無人進行保証、8本全完了の実証、変異全KILLEDは未達・未確認である。
