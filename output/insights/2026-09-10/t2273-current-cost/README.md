# T-2273 / T-2559 — 現行受入の律速と局所コピー費用を診断し、実装を採用しなかった

2026-09-10。wave `dev-wave-t2273-current-cost`。
正本は D1936項35、D104、前回の `2026-09-10_t2273-accwall-maxocc/README.md`。

**最新の観測群ではshard-0が最遅で、最大workerはgw8だった。ただし最大workerだけの終了tailは
2.610〜7.666秒にとどまる。局所候補の費用を追加診断した結果、変更を採用する根拠は得られず、
コード・テスト・probe・prewarm・共有cacheの新規実装は0で閉じた。**
安全な短縮が不可能と証明したわけではなく、改善効果ゼロをA-B実験で確定したわけでもない。

## 既存受入の観測

一次資料は `/work/1/SFC/tanab/.izanagi-acceptance-shards/<run>/shard-{0,1,2}/{junit.xml,report.json}`。
起動時にdirectory mtime降順で全3shardが揃う6走を選び、相談中に完了した2f3d232882を追加した。
以下の7走をこの診断の固定観測集合とする。全21shardでpytest_rc=0、selectedとfinishedが一致した。

単位は秒。wallはJUnit testsuiteのtime、占有はreportのworker_occupancy.duration_s。

| run | shard-0 wall | shard-1 wall | shard-2 wall | gw8占有 | 最後1workerのtail |
|---|---:|---:|---:|---:|---:|
| 2f3d23288242db9879936059107ffd32 |397.021|244.561|210.527|272.355|2.610|
| aa816b219efd6a259227d4a54d9f86eb |336.325|211.511|207.431|247.270|5.624|
| 01a5db37ccec57b1c8a3f3ec9ac947b8 |338.828|209.134|207.180|247.009|5.100|
| 549722180c16c5ed67fdacf4f66f3dce |345.937|228.732|206.444|240.058|6.744|
| b3031f5eb2116d8fdce4b2c301ac54b9 |349.854|209.365|224.652|235.038|7.666|
| f88a815b9fec7de129648655d63e659f |320.826|205.051|202.579|233.707|3.801|
| 1f198f2d42899d2930f828477596b385 |325.161|200.729|204.013|241.728|4.688|

全てshard-0が最遅、gw8は2item、最後のworkerもgw8、次点はgw9だった。
worker占有はsetup/call/teardownの合計であり、CPU実作業量でもfixture構築費でもない。

旧6走のJUnitから、gw8占有と丸め誤差内で一致する2itemの組は各走1組だった。
`test_t080_stub_free_e2e_single_defects_have_single_exact_reason_b5[ccbench-current-known_axes.ccbench_current]`
（204.207〜217.835秒）と
`test_v2_candidate_rejects_later_run_using_derived_earlier_eligibility[use-reported-eligible]`
（29.435〜29.866秒）である。追加走も243.176+29.179=272.355秒と整合する。
**これは時間和からの推定で、保存されたnode→worker割当の直接観測ではない。**

## 最大占有と非重複tailを分ける

観測tailはsession_timeline.workersのlast_test_finished_epoch_s最大−次点である。
他workerの終了時刻・割当・前後処理を固定した場合だけ、gw8をδ秒縮める直接利益は
`min(δ, tail)`となる。最大占有234〜272秒全体を除去可能量とは呼べない。
300秒未満にはshard-0を20.826〜97.021秒超縮める必要があり、gw8単独への変更では届かない。
共通fixtureの短縮は複数workerへ効き得るため、この条件付き上限で全ての局所改善を否定しない。

aa816bの時刻分解は、session開始→最後のworker collection完了53.245秒、そこから
最初のtest開始29.015秒、test開始→gw9終了241.649秒、gw9→gw8終了5.624秒、
gw8→JUnit終端6.793秒。計336.325秒である。
2f3dの対応値はcollection73.033秒、dispatch44.740秒、test span272.358秒、終端側6.890秒。
`tools/acceptance_shards.py`の_controller_stateはworker collection時刻の最大を返す。
worker間のcollection完了幅、controller prewarmの開始・終了・発火回数は記録されていない。

**観測した最後1workerのtailは、未実装prewarmの非重複tail Pとは別である。** Pは未測定のまま。
wall−最大占有を独立な床と扱わず、dispatch全量をprewarm費用とも扱わない。
JUnit終端以後のreport生成や後始末もこのwallの外にある（D1830）。

各shardは同時に開始しない。例えば2f3dのsuite時刻包絡は445.516秒で、最後に終了したのは
shard-2だった。aa816bでは包絡336.325秒でshard-0が最後だった。
最大shardの所要と全受入の経過時間を区別する。包絡にも投入前の待ちは含まれず、
異なるhostの時計を比較する限界がある。

## 局所候補の追加診断

候補は`test_s8b_oracle_driver.py`の初期orchestrator copytree後にhistorical basis等で
上書きされるsourceの先行コピーだけに限定した。private copy、runtime source配置、
public gate、明示validateとfinalize内部の反復検出は削らない。

既存の`2026-09-04_t2298-t2273-shard0-critical-path/measure/phase_plugin.py.txt`とbyte一致する
repo外のphase_plugin.pyを**改変せず**再利用した。
plugin SHA-256: `06dd4f6fedb115c0e885219da71b3dcf840acfade807c62a059c6da48b214d6b`。
generic taskを通し、計算ノード内でtools/run_tests.pyを実行した。argvは[request](phase-request.json)、
選択はsingle_defectsの4paramとdraft_finalizeの1node、`-n 0 -p phase_plugin --durations=0`。

- source HEAD: `98a3d7c9e4ed2fb67c0854825eee868fadfc9bcb`。実走前のgit statusは空で、実走中の編集なし。
- request: `990044.nqsv`、host: `bnode022`、開始13:05:00、終了13:08:32 JST、会計Elapse216秒。
- **5 passed、runner/dispatcher rc=0**。pytest表示210.48秒、JUnit210.328秒。
- [JUnit](phase-current-junit.xml)、[dispatchログ](phase-current-dispatch.log)、[receipt](phase-receipt.json)、
  [親processの観測JSONL（gzip）](phase-current.jsonl.gz)。
  解凍bytesのSHA-256は`7e0f6350b53dfce576b2c7507656f75f95f58df593c18192b5c40f3e0d3676ec`。
- dispatchログは末尾空白検査のため、内容が`| `だけの4行を`|`へ正規化した。
  復元は内容が`|`だけの各行の末尾へASCII spaceを1個足す。原文3618bytes、SHA-256
  `62593a610fdd08adfd91e0f48a6350f5c314ce66e23f041c1e135c833b0a1327`。表示文字は不変。

| 直接観測した処理 | 発火数 | 包含時間（秒） |
|---|---:|---|
| base構築 |2|81.1253 / 73.2786|
| orchestrator全体copytree |2|0.9863 / 0.8216|
| Git-visible output複製 |2|30.3418 / 23.4245|
| 子Pythonの実検証経路 |2|39.9497 / 40.1946|
| fixture helper |5|83.4862 / 2.3879 / 2.3971 / 2.3755 / 75.6350|
| historical basis file復元 |60|回数のみを候補診断に使用|

入れ子の包含時間なので表の各行を合算しない。全orchestratorコピーでさえ、今回のbase構築の
約1.2%以下だった。上書きされるsourceはその一部にすぎない。
先行コピー削除にはmetadata/実行bitと失敗挙動を保つ確認も必要であり、この小さい観測費用から
追加probeや実装へ進む根拠は得られなかった。大きいoutput複製と子Pythonは検査実体と実検証で、
所要を減らすために除去しない。

### 測定の限界とD104の採否

これは1processの計装付き費用診断で、48worker受入へ秒数を外挿しない。
pluginは親helperを包むだけで子Python内部は観測しない。上書き対象だけのcopy回数・bytesも
未分離であり、全orchestratorコピーを候補区間の包含として見た。
割当ては専有の保証ではなく、nodeへの読取sshはhost key verificationで失敗したため
同居processの直接確認は未充足。設定を変更して接続を通すことはしていない。

**改善実装の採用なし。D104の同一allocation A-B/B-Aは未実施で、効果実証を主張しない。**
今回の診断は候補の優先度を判断する材料までである。prewarm Pの値や共有cache効果を推定して
先行実装することもしていない。D104当時の高価な履歴走査は現行では安価raw diff先行へ
変わっており、当時の約80秒という内訳を現行の律速説明へ転用しない。

## 裁定と終端

独立planと相談2本は[逐語](verbatim/)に保存した。親は相談Bの「診断1件は残る」を採り、
追加実走後に実装不採用を確定した。相談Aの「検証反復を削る案は不可」も採用した。
実装差分0なのでdispatcherの4→7経路で段5/6と変異を省略し、関連実repo 5nodeは記録前に実走した。
記録後の最終受入は共通launcherのreceiptを権威とする。焦点5nodeを受入全走とは呼ばない。
稼働T-2515のhandoffとbranchを起動時に照合し、t1259/conftest・較正変更は編集していない。
改善候補はhandoffに記録するだけで、skill改善実装・次wave起動・pushは行わない。

### 最終受入の再走経緯

初回投入は親の所有指定が共有docs/phase3.md全体を含んだため、mainの別節追加を
owned-path-overlapとして実走前に拒否した。所有検査を外さず、固定mainを通常mergeして解消した。

実走した次の受入（tip `70dec646b`、run `f1374cb03852013baf8dccbb20c9b301`）は
22473passed / 68skipped / 2errorで赤だった。shard所要は548.105 / 223.316 / 236.631秒、
shard-0の最大占有415.846秒、最後1workerのtail5.067秒。これを改善効果とは扱わない。
2errorは所有外t1259の`test_pbs_early_ulimit_failure_emits_one_prefixed_result`と
`test_repo_unchanged_claim_compares_target_content_digests`の共通setupで、
`git ls-files --others --exclude-standard -z`が30秒timeoutしたものだった。
対象test/probe/conftestはmainとbyte同一、今回の文書内容を判定するassertionにも到達していない。
ただしrepo走査なので記録量や同時負荷の間接的影響まで否定するものではない。

同tipでt1259ファイルをtools/run_tests.py経由で1回単独再走し、**51passed/rc0、484.16秒**。
timeoutは再現しなかった。DW-O18に従い検査を変更・除外せず受入を再走する。
その間にlandしたT-2581のmainは固定SHAで通常mergeした。t1259/conftestの編集は0のまま。

### 2026-09-11の再開

続く受入は22464passed/68skipped/6failed/5errorで、t1259の同timeout、s8c snapshotの
git archive timeout、launcherの時間制限に掛かった。親は非帰属赤の処置をscope外と解釈して停止したが、
ユーザーがmain landまでの続行を指示したため、この停止判断を撤回して同じwaveを再開した。
mainには`e28a62d26`のmodule snapshot化とreader登録が着地済みで、各testは独立copyを受け取る。
固定main `d85bbb211`を通常mergeし、今回の診断実装やholdを追加せず修正済みの受入を使う。
資料配置は現行output/README.mdに合わせた。計測日時・source・raw bytesは元の記録を維持する。

### 着地に必要だったfixture競合の修正

取り込み後の関連480件は479passed/1failed。旧版`test_limit_stop_is_never_accepted`は単独でも
子exitが-15となった。fakeの`term_success`がカウント証拠を公開してからSIGTERM handlerを
登録するため、親が上限を検出してhandler登録前に停止させる競合があった。
Codex authorの初回signal mask案は実走で-9となり不採用。最終案は`term_success`だけ
output/terminal準備とhandler登録を先にし、token_countを最後に公開する。
handlerのI/Oとterminal二重出力を除き、正常exit0だけを行う。11行追加・4行削除で、
本番launcher・timeout・既存assertion・t1259/conftestは変更しない。

修正後の単独は1passed/1.67秒。file全体の4worker走は他モード3件が証拠待ちで赤となったが、
review終了後の直列走は**211passed/146.63秒/rc0**。他モードの分岐と期待値は不変である。
独立review2本はblocking0/GO。事前登録M1はhandlerのexit0をexit7へ変え、
既存の子終了コードassertionで検出する。M1は終了コードの感度であって、競合の完全消失の証明ではない。
このfixは受入を閉じるためのテストfixture修正であり、全走短縮のD104採用結果ではない。
最初の診断が実装0だった事実と、再開時のこの局所fixを区別する。
