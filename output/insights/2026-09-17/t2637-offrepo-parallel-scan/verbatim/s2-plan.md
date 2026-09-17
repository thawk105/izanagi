## 前提の検算

必読の4ファイルを指定範囲で読み、基準 HEAD が `abc7085ae6e1a69dc294c4f827ed7949e6df5305` であることを確認した。ファイル変更、pytest、監査・計測は実施していない。以下の行番号は変更前のもの。

以後、実装ファイルを **A** = `tools/audit_dangling_commits.py`、テストファイルを **T** = `orchestrator/tests/test_audit_dangling_commits.py` と略記する。新設関数・テストの位置は既存行を挿入起点として示す。

採用案は、**root の最初の `os.walk` iteration を主 thread で処理し、直下部分木を worker に分配、既存の走査順で merge する方式**。P2・P3を基本とし、次のずれを明示する。

- A:962 の戻り値 `True` は「候補が存在し列挙段へ入った」の意味。root が空集合でも、全 root が失敗しても `True`。成功した directory の有無に変えてはいけない。
- A:936 の identity は `(st_dev, st_ino)` だが、格納先は OID ごとの辞書。実際の集約単位は **`(OID, device, inode)`**。
- 代表 path の昇順最小と現行 first-seen は異なる。root 直下 `same.py` は `a/same.py` より先に処理される。P4の集合比較だけでは、この変更を見落とす。
- I6 の「OSError 以外も既存と同じ rc=2」は広すぎる。A:1807付近の `main` は `OSError / RuntimeError / UnicodeError` だけを捕捉する。`ValueError` や `AssertionError` まで rc=2 にする変更は含めない。
- T:2207〜2420 の指定末尾は、既に `_ShortReadBuffer` 等の cat-file テスト支援コードへ入っている。列挙の prefilter・fan-out テストは T:2207〜2385付近。
- D958 は上限を受理条件として明記する一方、P1は改善していれば超過だけで land を拒まないという暫定判断。D2038は上限超過を予期するが、D958の受理条件を明示的に撤回してはいない。実装計画はP1で進め、最終受理の根拠とは分けて記録する。

## 並列単位と等価性の論証

A:864〜962を次の構成へ分解する。候補選別規則を逐次版・並列版へ複製しない。

| 変更位置 | 計画 |
|---|---|
| A:864直前 | 1 iteration を処理する共通 helper、部分木を走査する worker、集約 helperを追加 |
| A:874〜881 | 空候補の早期 return、basename→size→executable index を維持 |
| A:889〜900 | root 検査を主 thread に残す |
| A:906〜959 | iteration 処理を共通 helperへ抽出 |
| A:906付近 | workers=1 は root 全体を従来順に走査。workers>1 は root の最初の iteration と各直下部分木に分ける |
| A:962直前 | root 順・部分木順の merge と failures 集計 |

具体的には、主 thread が `os.walk(root, topdown=True, onerror=..., followlinks=False)` を作り、`next()` を1回だけ呼ぶ。得られた root iteration を共通 helperで処理し、ソート済み `dirnames` をコピーして元 iterator を閉じる。その iterator を再開して二重走査しない。

各 worker は直下 path を入口に同じ `os.walk` を実行する。ただし、**入口の symlink 判定を明示的に行う**。`os.walk(symlink_path, followlinks=False)` は、渡された top 自身が symlink である場合まで除外する契約ではない。

現行との対応は次のとおり。

| 現行の意味論 | 並列化後の保持方法 |
|---|---|
| `sorted(roots)` | root 間は逐次処理し、この順を維持 |
| root の `lstat` 失敗で failures+1 | 主 thread で同じ例外範囲・同じ加算 |
| root が非directory、read bitsなし、execute bitsなしなら failures+1 | A:893〜900の条件をそのまま使用 |
| `onerror` 1呼出しにつき failures+1 | 各 walk のローカル計数へ加算し、主 thread が合算 |
| directory iteration ごとに `dirnames.sort()` / `filenames.sort()` | 共通 helperで実施。worker内部の深さ優先順も維持 |
| 候補照合は `filenames` のみ | `dirnames` を候補列へ混ぜない |
| symlink directory は `dirnames` に載るが降りない | 直下入口では現行再帰と同じ `os.path.islink()` 判定。部分木内部は `followlinks=False` |
| basename不一致では candidateの `lstat` をしない | 現行 index lookup の後だけ `lstat` |
| candidateの `lstat` 失敗で failures+1 | iteration helperのローカル計数へ同じく加算 |
| `S_ISREG` 以外を除外 | symlink file・FIFO・directoryを同じ条件で除外 |
| size、`S_IXUSR` による選別 | 現行条件をそのまま共有 |
| OID・identityごとの first-seen | 部分木内は現行順、部分木間は主 thread の順序付き merge |
| owners / aliases の集合 | `set.update()` で union。aliasのrootは部分木入口でなく元の探索root |

**子directoryへ root 用の permission 検査を再適用しない。** 現行では子directoryの読取不能は `os.walk` の `onerror` に任せている。rootと子の処理を統一すると、privileged userでの挙動や失敗数が変わる。

root の最初の iteration が `onerror` 後に終了した場合は、`StopIteration` を終了として扱う。failuresはcallback分だけ加算し、directory/file計数は0、子taskは0、`scan_performed=True` を維持する。途中まで列挙されたentryを独自に救済しない。

`os.scandir` による独自分類は採らない。`DirEntry.is_dir()` の失敗時にnondirectory扱いする処理、走査途中エラーでiteration全体を返さない処理など、`os.walk` の挙動を再実装する必要があるためである。

この等価性は、**同じ安定したfilesystemと同じアクセス結果**について成立する。走査中にrename・chmod・削除が起きる場合、逐次版同士でも同一観測は保証できない。既存の比較時検査を維持し、並列化でsnapshot保証を得たとは主張しない。

## 決定性

**(a) subdirectory名の昇順でmergeし、現行first-seenを再現する案を採る。**

主 thread はroot直下の結果を最初に格納し、workerの完了順と独立に、ソート済みsubdirectory順で結果をmergeする。既存groupがあれば `external` と `metadata` は保持し、owners / aliasesだけをunionする。

これで、同じOID内のidentity辞書の挿入順も保持できる。A:981付近は `possible[object_id].values()` の順で比較するため、代表pathだけを固定するより強い等価性になる。

A:989〜996では、次を同一groupから渡している。

- `group.external.path`
- `group.external.initial_stat`
- `group.metadata`

A:788以降の `_compare_regular_candidate` は、読取開始時の `fstat` と初期device・inode・size・modeを照合する。mergeでpathだけを置換せず、**`_ExternalCandidate` 全体を保持**する。

報告へ渡るのはA:1001の `group.aliases` であり、代表としての `external` は直接出力しない。ただし代表が読めるかどうかは比較成否に影響するため、「報告されないから自由に選べる」とは扱わない。

辞書と集合でmergeし、`x not in list` による重複排除を導入しない。完了順の並べ替えに全候補pathの再ソートも不要であり、F628型の二次化を避ける。

## heartbeat と計数

A:217〜240の `_ProgressRateLimiter` は変更せず、列挙段では主 threadだけが生成・呼出しする。

共通iteration helperは、directory加算後と各filename加算後に計数通知を行える構造にする。

- 主 threadのroot処理とworkers=1経路では、現在どおり通知ごとに `heartbeat.pulse()`。
- workerではローカル計数を更新するだけ。例えば256 fileごと、directory終了時、worker終了時に、lockで保護したslotへ累積値を公開する。
- 主 threadは待機中にslotを読み、root分と各workerの最新累積値を合算してpulseする。
- 完了時には最終値へ置換する。公開済み値と戻り値を二重加算しない。

これによりheartbeatの値は「主 threadが受領済みの処理件数」を表し、単調増加する。全worker完了後の値は正確な総数になる。fileごとのqueue投入は、176万entry分のメモリ・同期費用になるので避ける。

結果待ちは `concurrent.futures.wait(..., timeout=POLL_CEILING_SECONDS, return_when=FIRST_COMPLETED)` とし、完了futureをpending集合から取り除く。報告間隔0でも待ち時間を0にしない。完了futureの `result()` は必ず呼ぶ。候補結果は順序付きmergeまで保持するが、計数は完了順で受領できる。

T:1035のflat fixtureには子directoryがないため、pool・待機処理を作らない。monotonic呼出しは現行どおり次の3回だけになる。

1. limiter初期化：`0.0`
2. root iterationのpulse：`0.5`、出力なし
3. file加算後のpulse：`2.0`、1行出力

したがって期待値は変更せず、厳密に次を維持できる。

```text
["repo 外走査 heartbeat directories=1 files=1"]
```

追加の「終了heartbeat」は出さない。T:1014の空directory・間隔0もroot iterationのpulseで成立する。

## 並列度の定数

A:29付近に `OFFREPO_SCAN_WORKERS = 16` を追加し、計測用env名を `IZANAGI_AUDIT_SCAN_WORKERS` とする。CLIは増やさない。

envはimport時ではなく列挙実行時に読む。未設定なら定数を使い、設定値は正整数のみ受理する。空文字・非整数・0・負数は明確な `RuntimeError` とし、既存 `main` のrc=2経路に乗せる。既定値自体も同じ正数検査を通す。

処理順は次のとおり。

1. `candidates` 空なら直ちに `({}, 0, False)`。
2. workers設定を解決。
3. 共通indexを構築。
4. root検査・列挙。

空候補時はenv不正でもfilesystemやpoolへ到達しない。これはI5を優先した仕様としてテストに固定する。

**workers=1ではpoolを作らず、root全体への従来のwalkを使う。** 逐次と並列は異なる走査制御を比較しつつ、候補判定helperを共有する。共有helperの同じ誤りを両経路が通過する危険は、独立の期待集合と既存prefilterテストで補う。

T:1728の `os.walk` trapは維持する。加えて列挙関数を直接呼ぶ新テストで `Path.lstat`、`os.scandir`、executor生成にもtrapを置き、早期returnがfilesystem全般とpoolを避けることを固定する。`audit_with_offrepo` 全体にはroot検証があるため、この強いtrapは直接呼出しに限定する。

## 例外と資源

workerごとに結果・failures・計数を所有させる。`onerror` の `nonlocal failures` は各worker専用closureへ閉じ、複数threadで同じ整数を更新しない。候補indexは構築後に変更しない。

通常の `OSError` は現行の捕捉位置で計数する。それ以外は `Future.result()` で再送出し、握りつぶさない。

- `RuntimeError / UnicodeError` は既存 `main` でrc=2。
- `AssertionError / ValueError` 等は既存同様に上へ伝播。
- 任意例外を一律に `RuntimeError` へ包む変更はしない。

executorは `with` で管理する。例外・Ctrl-C時には未開始futureをcancelしてから再送出する。既に実行中のthreadは強制停止できず、context終了はそれらの終了を待つため、LustreのI/O停止時の待ち時間に上限保証はない。この制約は `ThreadPoolExecutor` の仕様である。[Python公式資料](https://docs.python.org/3.10/library/concurrent.futures.html)

CPythonの `os.walk` はdirectoryのscandirを閉じてからiterationを返し、子へ降りる。worker16本なら走査用directory fdは概ね最大16本であり、深さ×16ではない。提示された `ulimit -n=262144` に比べ小さいが、実行時のsoft limit・既存fd・thread上限は別途記録する。本段では上限を実測していない。

GILについては、対象のCPython 3.10.12で次を区別する。

- `scandir` の `opendir/readdir`、`os.lstat` のsystem callはGILを解放する。
- Python側のsort、path生成、辞書・集合操作はGILを保持する。
- **`DirEntry.is_dir()` は `d_type` で判定できればstat不要だが、同版のstat fallbackはGILを解放しない。**

したがってmetadata待ちの一部は重ねられるが、D985の20%を大きく超える保証はない。C版との差はPython処理、GILを保持するfallback、走査分割・cache条件で説明可能だが、寄与は未計測である。[CPython 3.10.12実装](https://github.com/python/cpython/blob/v3.10.12/Modules/posixmodule.c)

Lustreの確認方法：**同じ小directoryに対し、`scandir`列挙のみと全entryへの`is_dir()`追加を `strace -c -e getdents64,newfstatat,statx` で比較し、非symlink entryの追加stat数を数える。**

## test の置換

T:1183の旧テストを、同じ位置の `test_parallel_offrepo_scan_preserves_enumeration` へ置換する。旧名は意味が逆になるので残さない。

新しいテスト群は以下とする。いずれも小さいtreeを使い、新設テスト自体はsubprocessを起動しない。

| 新設node | 固定する内容 |
|---|---|
| `test_parallel_offrepo_scan_preserves_enumeration` | workers=1/4のcanonical結果・failures・scannedと、独立に書いた期待集合の一致 |
| `test_parallel_offrepo_scan_preserves_report` | 同じ入力で `AuditReport` 全体と意味のある報告行が一致 |
| `test_parallel_offrepo_scan_uses_multiple_threads` | 実workerのthread ID集合が2以上 |
| `test_parallel_offrepo_scan_preserves_failure_counts` | root開始時・部分木内部のwalk失敗、candidate lstat失敗 |
| `test_parallel_offrepo_scan_preserves_first_seen` | 完了順を逆転してもroot直下優先・部分木名順の代表と比較順を維持 |
| `test_parallel_offrepo_scan_propagates_worker_exception` | worker例外の再送出 |
| `test_parallel_offrepo_scan_heartbeat_runs_on_caller` | callbackは呼出threadのみ、最終計数一致、間隔0でも待機timeoutは正 |
| `test_offrepo_scan_worker_configuration` | env未設定16、1/4、空文字・不正・0・負数 |
| `test_empty_offrepo_candidates_touch_neither_filesystem_nor_pool` | I5 |
| `test_parallel_offrepo_scan_unreadable_subdirectory` | chmod 0の子directoryによるfailures。privileged実行はこのnodeだけskip |

主要fixtureにはroot直下file、複数部分木、入れ子、部分木間hardlink、異basenameの同inode、symlink directory、symlink file、同名別size、同名同size別modeを含める。symlink directoryはroot直下と部分木内部の両方に置き、その先に固有候補を配置して、誤って降りれば結果が増える構成にする。

canonical化は次の構造を保存する。

```text
object_id → (device, inode) →
    (代表path, 代表root, metadata, sorted(owners), sorted(aliases))
```

`initial_stat` と代表pathのdevice・inode・mode・sizeも照合する。辞書挿入順はcanonical化で失われるため、比較呼出順は別assertで固定する。

複数threadの証拠はsubmit回数だけに頼らない。worker wrapper内の最初の2taskをtimeout付きBarrierで同期し、lock付き集合に `threading.get_ident()` を記録する。小treeが速すぎて1threadで終了する偶然を排除する。

reportテストではGit入力生成部分、cat-file、landed参照入力をstub化する一方、**列挙・実file比較・抑止集約は実コード**を通す。抑止あり、未参照copyあり、残存findingあり、scan failureありの期待を独立に書く。全reportが空で一致する恒真テストにしない。

## 既存 test の期待値変更

**既存の期待値を変更するのはT:1183〜1186の置換1件だけ。** 「並列実装文字列が存在しない」から「逐次・並列の範囲、規則、結果が一致し、並列実行が実際に起きる」へ変える。

以下は期待値を維持する。

| 位置 | 維持できる理由 |
|---|---|
| T:1014、1035 | root iterationとfilenameのpulse順を維持。flat treeではpool・追加monotonic呼出しなし |
| T:1058 | 比較段は逐次のまま。hardlink比較1回とread-chunk heartbeatを維持 |
| T:1102〜1180 | stage名・境界・候補sessionのmaterialization位置を変更しない |
| T:1538 | 到達不能symlinkはmetadata段で対象外。空候補returnにより `scan_performed=False` |
| T:1728〜1744 | 空候補でwalkを呼ばない |
| T:1746 | root permission検査を主threadに残すため、root実行でもfailures=1 |
| T:1702 | 読取失敗は比較段で計数され、findingが残りrc=1 |
| T:2056、2102付近 | 比較は主threadで1回。開始・終了fstatの2回、変更検出とfailures=1を維持 |
| T:2207 | basename・size・mode選別を同じhelperへ抽出し、blob取得は比較段だけ |
| T:2249付近 | prefilter後のmode変更を比較時に拒否 |
| T:2280付近 | OID・inode単位で比較1回、全ownerへの既存fan-outを維持 |
| T:2343付近 | 異inodeの同bytes実体は2groupとして維持 |

新envの影響を排除するため、テスト側で `IZANAGI_AUDIT_SCAN_WORKERS` をclearするfixtureをT:27付近に置く。各workers比較テストだけ明示設定する。これは期待値の変更ではなく実行環境の固定である。

## 変異 matrix の事前登録候補

対象行は変更前の対応位置。author後、親が実装済み関数・行へ対応を確定してから変異を適用する。KILLEDは予定であり、実測結果ではない。

| ID | 対象 | 単一変異 | 期待node・結果 |
|---|---|---|---|
| M0 | A:873 | docstringの意味不変な言い換え | 等価変異。SURVIVEDを期待 |
| M1 | A:902〜904、962相当 | workerのwalk failuresを合算しない | `test_parallel_offrepo_scan_preserves_failure_counts`：KILLED |
| M2 | A:906相当のtask生成 | sorted subdirectoryの末尾1個をskip | `test_parallel_offrepo_scan_preserves_enumeration`：KILLED |
| M3 | A:919相当 | root直下filename処理をskip | 同上、およびT:1035：KILLED |
| M4 | A:910相当のworker walk | `followlinks=True` | enumerationテストの内部symlink固有候補：KILLED |
| M5 | A:943〜952相当のmerge | 既存groupの代表を後着結果で上書き | `test_parallel_offrepo_scan_preserves_first_seen`：KILLED |
| M6 | A:962直前のfuture回収 | worker例外を捕捉して空結果へ置換 | `test_parallel_offrepo_scan_propagates_worker_exception`：KILLED |
| M7 | A:914〜922相当 | workerからprogress callbackを直接呼ぶ | `test_parallel_offrepo_scan_heartbeat_runs_on_caller`：KILLED |
| M8 | A:29付近の新定数 | 既定workersを16→0 | `test_offrepo_scan_worker_configuration`：KILLED |
| M9 | A:874〜875 | 空候補returnより前にexecutorを生成 | `test_empty_offrepo_candidates_touch_neither_filesystem_nor_pool`：KILLED |

`filenames` に `dirnames` を混ぜる変異は、通常directoryが後続の `S_ISREG` で除外されるため、結果集合だけでは生き残り得る。採用するならdirectoryへの追加lstatをtrapする独立controlが必要であり、上の10件には混ぜない。

## 計測計画の検算

workers=1/16の交互走行は妥当。ただし、次を補う。

1. **旧版対照を1走追加する。**
   `abc7085ae` のtoolを親の成果物領域に取り出し、明示的な `--repo <同じrepo>` と `--ref <固定したmainのOID>` を付ける。別pathへ移すとA:28の `DEFAULT_REPO` が変わるため、`--repo` は必須。

2. **「変更前と同じ経路」の意味を限定する。**
   workers=1はpoolなし・従来のroot全体walkだが、抽出helperを通る変更後コードである。変更前そのものとの一致は旧版対照で確認する。

3. **stdout・stderr・rcを別々に保存する。**
   監査をパイプへ流さず、終了直後にrcを保存。その後に正規化する。

4. **正規化は行頭に基づいて行う。**
   比較から除くのは次の3種類だけとする。
   - `audit_dangling_commits: 進捗 ` で始まる行
   - 最終 `audit_dangling_commits: elapsed_seconds=...` 行
   - `audit_dangling_commits: 所要上限超過 elapsed_seconds=...` 行

   超過行もelapsed依存なので意味結果の比較から除くが、性能判定には必ず残す。単に `elapsed_seconds=` を含む全行を削除すると、pathやsubjectを誤って消し得る。残りはソートせず逐語比較する。

5. **D958の形を各条件へ適用する。**
   workers=1、16それぞれwarm-upを1走捨て、独立3走を交互に実施する。各条件でmax/min>1.5ならその条件に3走追加し、全採用走の最大を報告する。列挙段と監査全体の所要を両方示す。

6. **変動入力を記録する。**
   他の監査走行0だけではrepo・探索根の不変を保証しない。実行中のwave生成・削除、refs変更、共有node負荷を記録し、結果不一致を正規化で隠さない。

7. **login node計測は規律との不整合を明示する。**
   `docs/pegasus-runbook.md:345` は性能測定を計算nodeへ限定している。親briefのlogin node計画を通常規律で実施可能とは判定できない。今回のlogin指定を個別例外として扱う根拠がなければ、同じ割当計算node上でwarm交互走行を行う。既存login実測との比較にはnode差を付記する。

P5の別node初回走はcold相当の補助観測として分離する。server cache等は残るため「cold実測」と断定せず、取れなければT-2660(b)に持ち越す。

## 焦点テスト集合と影響範囲

参照検索と該当箇所の読取りで、2段までの関係を確認した。

| 参照元 | 関係・影響 |
|---|---|
| `tools/check_branch_rescue.py:58`、1789、1822 | toolをsubprocess起動。rc、commit報告数、最終elapsed行を検査 |
| `.claude/commands/cleanup-branches.md:37`、39 | 監査単独実行とrescue checker呼出し |
| `tools/check_docs.py:752`、6571 | cleanup commandのwhole-file SHA pin。監査source自体のpinではない |
| `tools/check_docs.py:6054` | cleanup commandの可視呼出し契約検査 |
| `orchestrator/tests/test_check_branch_rescue.py:20`、337、1492 | 実監査利用、zero結果、最終elapsed契約 |
| `orchestrator/tests/test_branch_rescue_ledger.py:172`、180、344 | cleanup→監査／rescueへの実行edge検査 |
| `orchestrator/tests/test_check_docs.py:663`、9812以降 | cleanup本文とpinの検査 |
| `.agents/skills/cleanup-branches/SKILL.md:14` | cleanup commandへの導線。今回は実行せず参照関係だけ確認 |

`check_branch_rescue.py:209` のenv allowlistには既存root envはあるが、新workers envはない。したがってrescue経由では既定16になり、計測envのoverrideは伝わらない。計測は監査toolを直接実行し、allowlist変更は本waveへ入れない。

後段の再走対象は次の4ファイルとする。

- `orchestrator/tests/test_audit_dangling_commits.py`
- `orchestrator/tests/test_check_branch_rescue.py`
- `orchestrator/tests/test_branch_rescue_ledger.py`
- `orchestrator/tests/test_check_docs.py`

実装後のテストは `tools/run_tests.py` 経由で実施する。docs・adapter検査、commit後のprovenance監査は親の完了手順で行う。本段では実行していない。

新設テストは小tree・process内stubを使い、実根の176万fileを走査しない。5分の性能受理条件を緩めず、テスト実行時間とも混同しない。受入所要への追加費用は、pool生成、計数公開、mergeであり、実根計測で評価する。

## リスクと未確定点

- **倍率不足時の扱い。** 3.8倍に届かなくても、再現可能な短縮があればP1に沿って結果を評価できる。ただし改善なし・悪化なら、このPython実装の採用を止める。既定1へ戻して「並列化完了」としてlandする案は採らない。項20とD2038は、実装して実測することを求めており、未改善の休眠機構を着地させる根拠ではない。
- **D958との関係。** 改善したが300秒超の場合のland可否はP1の暫定解釈として残る。「D2038でD958が撤回された」とは書かない。
- **並列性の偏り。** 最大部分木の長さが下限になる。root直下だけの巨大flat treeは並列化されない。細粒度taskへの一般化は今回行わない。
- **GILとLustre。** `d_type` 不明時のfallbackが支配的ならPython threadの伸びは小さい。C版の観測倍率を受入期待値にしない。
- **障害時の待機。** 実行中threadのI/O停止を強制中断できない。fdだけでなくthread生成上限・stack・候補結果の保持量も観測する。
- **時間依存入力。** 走査中の変更に対する全結果同一は保証不能。`O_NOFOLLOW`、初期statとの照合、読取後の変更検査を維持する。
- **T-2662との重複。** 同じtool・testファイルだが、境界helperとそのテストは変更しない。
- **T-2663との重複。** rescueの二重実行・env継承を修正しない。consumer検査だけ行う。
- **T-2664との重複。** A:943〜958、1001付近のgroup／aliasは編集面が近い。異basename・同OID・同inodeに対する既存fan-outをそのまま固定し、owner別aliasへの修正を混ぜない。
- **抑止集合。** 代表の選び直し、分類規則変更、境界helper修正、alias配布修正を入れない。既存結果が増減した場合は性能改善と交換せず、等価性違反として止める。

## 総括

P2の部分木並列化を採り、**既存順のmerge、候補判定helperの共有、主thread限定heartbeat、workers=1のpoolなし経路**で実装する。変更対象はtoolとそのテストに限定する。

実装前に特に固定すべき点は、直下symlinkをworker入口に渡して追跡しないこと、root検査を子へ広げないこと、代表pathとinitial_statを一体で保持すること、失敗数を漏れなく合算することである。

本段は静的検算のみ。Pythonでの倍率、実根の逐語一致、D958受理、計測場所の扱いは未確認であり、成功扱いにはしていない。
