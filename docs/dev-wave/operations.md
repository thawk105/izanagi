# dev-wave 条件付き運用

発火条件の正本は入口の条件dispatch、成立時の実行手順だけは本書。

## DW-O01 — codex subprocess 起動

`tools/dev_wave_codex.py --stage <stage> [--lane <lane>] -o <出力>.md` で起動（他の引数は `--help`）。model は全段、effort は段 5 / 6 が docs 権威から導出。caller 指定は不可。
背景jobは`nohup setsid bash -c '<cmd>; echo $? > <log>.done' </dev/null`でdetach。
prompt非空・参照path実在・`--dry-run`のargvを先に検査（段別flag違反はrc=2即死）。既存`.done`を消去・再利用せず再投入を止める。
待機は `tools/dev_wave_wait.py producer` を使い、`--pid-file` は producer script 自身が `echo $$` で書く。
wait側`--receipt-file`はworker launcher receiptと別pathにする。
完了は`.done`とexit codeだけで判定し、grepも通知も待ち手rcも判定にしない。成果物は最終メッセージから読む（F23/F24）。
採用は`tools/check_codex_output.py` rc=0（promptに`## 総括`必須、F43）。
`<model>`: 全段 `gpt-6-sol` (段 3 の 2 本も同じ)。
`--artifact-root`は先に作る。
重い巡はcall/tokenを見積もる。未受理は未完了と記し次の子に監査させる。

## DW-O02 — job artifact

prompt・log・patch・親brief・前段の子成果物はwave専用dirへ置き、job tmp直下や過去waveと共有しない。
確保不能なら停止。全文複製せず絶対パスで読ませ、promptに「読めなければ即停止」と書く。context欠落の出力は採用しない。
必読資料と既裁定は逐語をjob dirへ出す。repo内pathはworktreeの遅れでfail-closed。**promptのrepo pathは投入先worktreeのもの**にする（親側だと子は書けず空成功、F819）。
出力・読取ログはNFC。U+0300〜U+036F禁止。非NFC資料はASCII escape表示、原文保持。
prompt 先頭は AGENTS.md の単独段例外と同形式。

## DW-O03 — 防護パスを含む file

WAL、campaign lock、campaign output、submodule 等の防護パス文字列を含む file は
Bash heredoc や不透明な command substitution で作らず Write ツールで作る。guard を迂回しない。
prompt に限らず brief、裁定、runner script、spec も同じ。`python3 -c` も同じ理由で拒否される。
**作る command だけでなく読む command も掛かる。** 防護 path と `$()`・プロセス置換・`<<<`・
`eval`・`xargs` の同居は分類不能として拒否されるので、読取りは cat / grep / jq を直に使う。
Bash 側は部分文字列で判定するため防護 path の兄弟 directory も掛かる。Write/Edit 側は
subtree 判定で掛からない。射程が違うので Bash の拒否を Write の可否と読み替えない。
隔離 session では repo 外の絶対 path も同型に掛かる。job dir への作成・追記も Write/Edit を使う。

## DW-O04 — 防護パスを含む commit message

Write ツールで message file を作り、`git commit -F <file>` を使う。
heredoc と command substitution を併用してはならない。

## DW-O05 — read-only codex

書込可能tmpがないため静的検査でよいと明記する。
テスト実測は親が行い、子の非実走を緑と記録しない。予算が尽きそうなら途中結論を出力形式どおり
書いて終われ、も入れる。

## DW-O06 — submodule 系 real-repo test

submodule の index lock を作れない sandbox 由来の偽赤と連鎖赤を親環境で独立再現し、
再現しない赤を実装差分へ帰属しない。

## DW-O08 — freeze 族の初期化

最初に `git submodule update --init` を行う。
未初期化による skip や手前の赤を破損なしと報告してはならない。
`DW-C01` の初期化 tool は一過性に失敗しうる。同じ引数で 1 度だけ再実行し、なお赤なら止める。
rc=0 と OK 表示でも submodule 木が空でありうるので、rc でなく木の中身で効果を実測する。
最初の失敗を「この worktree では初期化できない」と一般化して brief へ書かない。

## DW-O09 — 凍結 bytes の pin 閉包

着手前に成果物・変更 source の path・module/file 名で `git grep -n` し pin する台帳・test・trust root を全列挙。
`FROZEN_MANIFEST`、generator source hash pin、key→canonical path 束縛、output 外の
review ledger、全 field から同一性 hash を導く dataclass・schema を含む。path 検索は path key の
pin しか出さない。role 名や xdist group 名など key 側でも検索し、hit 0 件を pin なしとしない（F30）。
**変更 file の変更前 sha256 で output/ も検索**（F370）。hit した test は中身を読む —
行番号・本数・live 比較の pin は一覧に出ない。
durable manifest の未発行/再発行要を区別し brief の不変条件へ書く（F27/F30、D84）。
統一系 wave は各出現を live copy/独立 golden/凍結 snapshot/歴史記録へ分類し scope を裁定（F39）。
docs のみの wave でも成立 — docs path も検索（F78）。

## DW-O10 — producer write-path

`DW-O09` が成立し対象 producer の出力 bytes が変わりうるときだけ適用する。
producer が書く全ファイル種を棚卸しして brief に列挙する。非凍結 producer 一般へ拡張しない。

## DW-O11 — ファイル削除

受入形では未 stage 削除と git 検査不能を `run_tests.py` が止める (bypass 不可)。
復旧・stage・復元の後に再走し、gate の赤を受入結果にしない。
`output/` 配下の一括削除は `git ls-files -- <path>` の空を確認してから行う。`git status` は
tracked 無変更を出さず不在証明にならない。理解だけの `rm -rf` は別 wave の tracked file を消す。
変異 scratch は `rm -rf` の後 `git worktree prune` まで行う。登録残置で次走が共有木検査で止まる。
landの登録木前後比較は自wave木と着地差分のpathに重なる木だけなので、重ならない他waveの
撤去はlandをrc=21で落とさず、landと並行してよい。撤去の同時実行を絞る理由はLustre混雑。
撤去途中で`gitdir`を欠く管理dirはt810 coordinatorの登録走査で他waveの受入を赤にしうるので、
受入の走行中は撤去を避ける。

## DW-O12 — 裁定手順と実行手順の差

worklogへ裁定予定でなく実行した手順を書く。
親担当と分割した裁定項目は段7前に着地差分と照合する。
一次資料と逆の工程記録を残さない。
受理集合を変える指示を子へ出す直前にこのwaveで凍結済みの事前登録・判定式を再読する。
自分が直前に書いた凍結も拘束する。
DW-S06-Cの受入投入は段6の中間走行(変異検証)を指す。land対象tipの最終受入は
DW-S07と段8のcommit後。tested tip後の記録commitと手解決mergeはrc=23。
受入後の前進merge競合はabortし解いたtipで再受入。
共有文書(phase3.md等)は段1で稼働waveの編集と重なれば追記位置を分ける(同位置は競合しうる)。
測定値は測ったcheckoutを併記する(F41)。dispatchした走の所要はjobのElapseかrunner自身の報告時間を
正とし、queue待ちを含む親の外側wallは使わない。

## DW-O13 — gate 入力の実在

設計前に入力が実成果物のどの field に存在するか確認し、同名識別子を二義化しない（D75）。
既存 exact 述語の改訂で受理形を増やす場合も新設に当たる。
field の実在では足りない。その field が実環境で取りうる値を実測し、要求する値が到達可能か
確かめてから述語を採用する。到達不能なら採用せず、測った値域を裁定へ書く。
時間予算は実測分布の max への倍率で決め、母集合と「観測 regime が適用対象と同じか」を併記する。
正例は余裕を取る。負例は向きで 2 分し、発火自体が目的なら小さい値（一律の余裕は恒真化）、
特定の時点で発火させたい負例は前段に余裕を取る（下限 = 不足が確定した値 x 裾 x 正例倍率）。
内側予算の和 + 終了余裕 < 外側 watchdog を検査自身に確かめさせる。

## DW-O14 — no-touch と monkeypatch

対象実装まで読み、resolver や `current_head` 等の正規注入 seam がないか確認する。
monkeypatch は最後の手段とする（D78）。
正例で許す差し替えは本数でなく位置で決める。検査対象の機構を構成する呼び出しは禁止、
その外側の既存定型 seam は許可、実物へ委譲する観測 wrapper は差し替えでない。
本数で列挙すると指定 fixture 内部の既存 patch と矛盾し、制約に合わせてコードを曲げる案を招く。

## DW-O16 — fix 後の焦点再レビュー

所見ごとの closed / partial / regressed 対応表を要求し、表なしで root cause が閉じたと判定しない（D78）。
親が書いた派生値（平均・差・率・補正値・「すべて」「だけ」「例外なく」の量化）は原データから
再計算して照合するまで closed としない。訂正にも同じ検算を掛ける。派生値の前提 (模型の仮定・計時起点) も裏取りする。
PATH 構築・interpreter 解決・外部 command 選定・signal 処理など実行環境に依存する実装は、レビュー通過だけで
closed とせず実機で動かすまで確かめる。実機の構造が子の推測と食い違えば親が測って prompt へ貼る。
NO-GO が続く場合は fix を重ねず 3 巡を上限とし (親の実機 blocker は別枠)、親が変異で裏取りして残る所見を real/refuted に
裁定して閉じる。根拠は worklog に書く。

## DW-O17 — commit trailer

trailerは`docs/ai-provenance.md`に従う（F25）。通常はmessage→`--message-file`検査rc=0→`commit -F`→full監査。
mergeは`OLD_HEAD`を保存し、ffはincoming監査（自commit 0件なら省略可）→`--ff-only`→full監査、非ffは`--no-ff --no-commit`→
競合解消→同じpreflight→`commit -F`→full監査。自動message/`--no-edit`は禁止。correctionは両commitを含む
rangeかfull監査だけが権威（`OLD_HEAD..HEAD`は補助）。検査rcをpipeへ渡さず赤で停止（F37）。複数preflightと
commitを同じshellで行うなら先頭を`set -e`にし、無ければtool callを分ける。両親と異なる実装面と実装面のrevertはCodex
`role=author`へ。競合時の`git add -A`は未解決gitlinkを旧側で確定しうるため`git ls-tree main <sub>`と照合し、
merge内でmain側pinへ揃える（後追い実装commitはCodex著者行を要求されlandが止まる）。

## DW-O18 — テスト cwd と非帰属赤の着地

cwd=repo root。nested subprocess import path偽赤は回帰外。file選択走は`from tests import`確立後に限り未確立赤も偽赤。

受入赤返却時が判定主体の境界。待ち手は赤返却だけ。人・AIが判定し根拠をworklogへ残す。assertion本文・差分実体で判定、署名一致禁止。非帰属赤の着地5分超禁止、悩まない(D690)。自分起因は直す。N走完全一致はflakeでも非帰属の証拠でもない。差分到達不能は単独再走、非再現なら受入再走。同一tipで各1回だけ。再赤/決定的赤でもhold登録簿へ登録しない(契約testが1件に固定、F1000)。真に決定的な不安定testはその1件のpin更新を個別に諮り、判定不能・原因未理解は除外せず共に停止。停止条件外は治すか上記の制限内で投げ直しwaveを止めない。受理は`child-green`だけ、赤の受領証禁止。

## DW-O19 — tracked file の一時変異

復元は `git diff` と `git checkout --` を正本とし、外部 backup を使わない。
本走は統合 commit 後に限る。変異前は `--porcelain` 空確認 (F174)。
変異後の `git diff --stat` が対象 file の意図した単一変異だけ (単一 entry が複数行ならその
範囲) であることを確認して復元する。
復元 bytes は commit と照合する。phase 完了は実装と同じ anchor commit へ含め、本走後の raw 台帳は
後続の記録 commit へ置く。anchor を amend して自己 hash 循環を作らない。
主 tree を変異させない経路として `tools/mutation_worktree.py --commit <commit>` が固定 commit の
使い捨て worktree で harness を走らせる。`--scratch-root` は既存 directory 必須で、
全 registered worktree の外に置く。再走は `--out` と `--attempt-out` を新 path にする
（既存は rc=2）。

## DW-O20 — clean-tree gate

専用handoffはworktree外(背景jobはrepo外)。untrackedを残してgateを走らせない。
cwdがworktreeなら作らず、directory/branch不一致をhandoff・worklogに記しwave用へ流用しない。
開始gateは`tools/check_wave_startup.py`(再開は`--mode resume`、背景jobは
`--external-handoff`も)。非0で停止。resumeもbranch・clean tree・main包含を要求。
gate成功後の再走は`DW-S05-A`だけ。取込は
`tools/dev_wave_wait.py acceptance`のpost-claim merge。
待ち手・launcher・runnerのbytesを変える前進は先に取り込む(F524)。
HEAD差は`--ff-only`で揃える(F48)。新規worktreeは未初期化submoduleで非0。
`DW-C01`で初期化して再検査(`deinit`禁止)。取込はpointerだけ進む。受入前に
`git submodule update --init --recursive`で揃える。
子を走らせるworktreeは`git worktree lock`(cwd走査はlauncher型を逃す)。
共有文書追記は段1で`DW-O12`。

## DW-O23 — 並行 session の local main land

`tools/dev_wave_land.py`へmain/wave絶対path、tested main/tip、着地tip、監査列(`<tested main>..<tested tip>`固定)を渡す。cwd=wave必須。
協調lock内で再照合・着地tipへff-only・`docs/spool/`をfold。
fold赤は`landed`を返さず、0件はno-op。
tracked/index/submodule dirt・incoming衝突untrackedは拒否。
docs/handoff直下・Git adminに双方向束縛のClaude/Codex worktreeは書式不問で非接触。
成功=`landed`/`already-landed`。postcondition failureは停止。stale/busyは継続し、他sessionの処理中dirtyは非接触で終端待ち。
新main監査・固定SHAのwave側merge・条件再評価を既存branchでlandedまで再試行。remoteで解消しない。
取込由来の追加再受入はtested mainと固定SHAの`tools/run_tests.py` blob差だけ(D987)。他の拒否は維持。
旧branch群はF266（一括merge・各親差分確認）に従う。
## DW-O25 — ff-only land の全史 provenance 関門

D254 に従い、land は `locked_main != 着地tip` のときだけ lock を解放して全史 provenance 監査を自ら走らせ、480 秒以内の rc=0 を必須とする。赤は `RC_PROVENANCE = 29` で main を 1 bit も変えず拒否し、CLI flag・環境変数・警告化の逃がし道を作らない。
lock 再取得後に全検査をやり直し、`tip_sha` / `checker_blob_sha` / `executed_bytes_sha` / `returncode` を束縛した receipt を lock 内で再照合する。`already-landed` の no-op と active fold transaction の recovery では監査を起動しない。
## DW-O26 — 焦点走の consumer test 拡張

`DW-O18` の焦点走 file 集合は、変更 test file と、変更 production file を参照関係で引いた consumer
test。private symbol は consumer 表に出ないので symbol 名で production を grep する。
欠くと静的レビューが見落とした破れを取り逃す（F242）。production file を変えた wave は repo 全体の
inventory test 4 群（`test_campaign.py` の certified-writer caller inventory、
`test_official_perf_closure.py` の perf file inventory、`test_p3_exploration_namespace.py`、
`test_p3_b4_wiring_probe.py`）を参照関係に依らず焦点走に含める。同一 worktree の dispatch は全種直列。
変更 test file は受入前に単独走で確認する。新規 test file を足す走は file 集合列挙のメタテストも含める。
並行 wave が自分の編集 file を所有するなら main 取込み済みの木の既存走行に相乗りし受入後に足さない。
## DW-O27 — acceptance は lease を待たない

D662 で lease 待ち行列は廃止。`acceptance`は投入前 claim を 1 回行い`held`でも待たず wave digest の
疑似 holder で投入する。待つ経路は flag でも戻らない。
`--lease-optional`と`--poll-seconds`は no-op。`stale-held`・`unavailable`は fail-closed。
integrity 検査と receipt 全 field は未取得でも不変。`--lease-dir`は省略せず専用 dir で迂回しない。
未取得が確定した走行は`release`しない。`--wave`は branch 名の末尾一致を要求 (codex の slug
と別でよい)。不一致は`preflight-branch` rc=2。
`--log-file`/`--receipt-file`は既存 file で rc=2。再投入は新 path にする。

`tools/check_docs.py` の dispatch 契約へ新節を登録する際は `orchestrator/tests/test_check_docs.py` の
合成 fixture との整合を同じ commit で確認する（`DW-O26` の精神。怠ると test が連鎖的に赤 —
T-1458、320 件）。

## DW-O28 — land 後の自己撤去

land 成功後、段 9 に main worktree から job 終端後 `python3 tools/dev_wave_cleanup.py` で撤去(絶対 path、`--main-worktree <MAIN>` は両方に付ける)。
先に manifest(`DW-S05-A`)の子木を `remove-child --manifest <M> --child-worktree <P> --evidence-dir <D>` で(回収 wave は旧分も)、次に wave を `--wave-worktree <WAVE> --wave-branch <BRANCH> --tested-wave-tip-sha <TIP>` で撤去し、他へ引き渡さない。
tool は非占有・main 祖先性(子木は所有 path の tree 一致でも可)・dirty 退避可否・manifest 束縛を検査。撤去前の不成立・不明は拒否し木と branch を残す(以後は rc=30)。統合証明済みの manifest 現行 branch は履歴を `<D>` へ bundle 後(HEAD が main 祖先なら省く)に `-D`。
F26: `git worktree remove`/`git submodule deinit` 不可。wave branch は `-d` のみ、手打ち `-D` 禁止。残る子木は unlock し理由を worklog へ。
