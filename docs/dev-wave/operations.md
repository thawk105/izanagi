# dev-wave 条件付き運用

発火条件の正本は入口の条件 dispatch、成立時の実行手順だけは本書が正本。
該当節を操作直前に読み、停止条件を迂回しない。

## DW-O01 — codex subprocess 起動

`tools/dev_wave_codex.py --stage <stage> [--lane <lane>] -o <出力>.md` で起動（他の引数は `--help`）。model は全段、effort は段 5 / 6 が docs 権威から導出。caller 指定は不可。
背景jobは`nohup setsid bash -c '<cmd>; echo $? > <log>.done' </dev/null`でdetach。
prompt非空と`--dry-run`のargvを先に検査（段別flag違反はrc=2即死）。既存`.done`を消去・再利用せず再投入を止める。
待機は `tools/dev_wave_wait.py producer` を使い、`--pid-file` は producer script 自身が `echo $$` で書く。
wait側`--receipt-file`はworker launcher receiptと別pathにする（同pathは証拠を上書き）。
完了は`.done`とexit codeだけで判定し、grepも通知も待ち手rcも判定にしない。成果物は最終メッセージから読む（F23/F24）。
採用は`tools/check_codex_output.py` rc=0（promptに`## 総括`必須、F43）。
`<model>`: 全段 `gpt-6-astra` (段 3 の 2 本も同じ)。
`--artifact-root`は先に作る。出力は`<root>/<wave>/`だけ、不在はrc=2。
`--max-*`は非権威で増量可。重い巡はcall/tokenを見積もる。未受理は未完了と記し次の子に監査させる。

## DW-O02 — job artifact

prompt・log・patch・親brief・前段の子成果物はwave専用dirへ置き、job tmp直下や過去waveと共有しない。
確保不能なら停止。全文複製せず絶対パスで読ませ、promptに「読めなければ即停止」と書く。context欠落の出力は採用しない。
必読資料と既裁定は逐語を job dir へ出す。repo 内 path は worktree の遅れで fail-closed。**prompt の repo path は投入先 worktree のもの**にする（親側だと子は書けず空の
成功で戻る、F819）。
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

## DW-O04 — 防護パスを含む commit message

Write ツールで message file を作り、`git commit -F <file>` を使う。
heredoc と command substitution を併用してはならない。

## DW-O05 — read-only codex

書込可能 tmp がないため pytest 緑を要求せず静的検査でよいと明記する。
テスト実測は親が行い、子の非実走を緑と記録しない。予算が尽きそうなら途中結論を出力形式どおり
書いて終われ、も入れる（無出力が最悪）。

## DW-O06 — submodule 系 real-repo test

submodule の index lock を作れない sandbox 由来の偽赤と連鎖赤を親環境で独立再現し、
再現しない赤を実装差分へ帰属しない。

## DW-O08 — freeze 族の初期化

最初に `git submodule update --init` を行う。
未初期化による skip や手前の赤を破損なしと報告してはならない。

## DW-O09 — 凍結 bytes の pin 閉包

着手前に `git grep -n "<成果物パス>"` を使い、
bytes を pin する台帳・test・trust root を全列挙する。
`FROZEN_MANIFEST`、generator source hash pin、key→canonical path 束縛、output 外の
review ledger、全 field から同一性 hash を導く dataclass・schema も対象に含める。path 検索が見つけるのは path を key にする
pin だけである。role 名や xdist group 名など path 以外を key に張る pin も key 側で検索し、
path の hit 0 件を pin なしと結論しない（F30）。
durable manifest が未発行か再発行要かを区別して brief の不変条件へ書く（F27/F30、D84）。
統一系 wave では各出現を live copy / 独立 golden / 凍結 snapshot / 歴史記録へ分類してから
scope を裁定する（F39）。
**docs のみの wave でも成立する** — 判定をコードの有無で代用せず docs path も検索する（F78）。

## DW-O10 — producer write-path

`DW-O09` が成立し対象 producer の出力 bytes が変わりうるときだけ適用する。
producer が書く全ファイル種を棚卸しして brief に列挙する。非凍結 producer 一般へ拡張しない。

## DW-O11 — ファイル削除

受入形では未 stage 削除と git 検査不能を `run_tests.py` が止める (bypass 不可)。
復旧・stage・復元の後に再走し、gate の赤を受入結果にしない。
`output/` 配下の一括削除は `git ls-files -- <path>` の空を確認してから行う。`git status` は
tracked 無変更を出さず不在証明にならない。理解だけの `rm -rf` は別 wave の tracked file を消す。
変異 scratch は `rm -rf` の後 `git worktree prune` まで行う。登録残置で次走が共有木検査で止まる。

## DW-O12 — 裁定手順と実行手順の差

worklog には裁定予定を写さず、実際に実行した手順を書く。
親担当と分割した裁定項目は段 7 前に着地差分と突き合わせる。
一次資料と逆の工程記録を残してはならない。
受理集合を変える指示を子へ出す直前に、この wave で凍結済みの事前登録・判定式を再読する。
凍結は自分が直前に書いたものでも拘束する。
DW-S06-C の受入投入記述は段6内の中間走行 (変異検証目的) を指す。land 対象 tip への最終受入投入は
DW-S07 と段 8 の commit 完了後に行う——取り違えると記録 commit が tested tip から漏れ land が rc=23
になる。測定値は測った checkout を併記する（F41）。dispatch した走の所要は job の Elapse か
runner 自身の報告時間を正とし、親側の外側 wall を所要として記録しない（queue 待ちを含む）。

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

## DW-O16 — fix 後の焦点再レビュー

所見ごとの closed / partial / regressed 対応表を要求し、表なしで root cause が閉じたと判定しない（D78）。
PATH 構築・interpreter 解決・外部 command 選定など実行環境に依存する実装は、レビュー通過だけで
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

受入赤返却時が判定主体の境界。待ち手は赤返却だけ。人・AIが判定し根拠をworklogへ残す。assertion本文・差分実体で判定、署名一致禁止。非帰属赤の着地5分超禁止、悩まない(D690)。自分起因は直す。N走完全一致はflakeでも非帰属の証拠でもない。差分到達不能は単独再走、非再現なら受入再走。同一tipで各1回だけ。再赤/決定的赤はmain既存Fを証拠にCodex`role=author`が`orchestrator/tests/flaky_test_holds.py`へ登録(field正本=同file)。F不在は登録せず裁定送り、判定不能・原因未理解は除外せず共に停止。停止条件外は治すかhold登録後だけ投げ直しwaveを止めない。受理は`child-green`だけ、赤の受領証禁止。

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

専用handoffはworktree外（背景jobはrepo外）。untrackedを残してgateを走らせない。
cwdがworktreeなら作らず、directory/branch不一致をhandoff・worklogに記しwave用へ流用しない。
開始gateは`tools/check_wave_startup.py`（再開は`--mode resume`、背景jobは
`--external-handoff`も）。非0で停止。resumeもbranch・clean tree・main包含を要求。
gate成功後の再走は`DW-S05-A`だけ。取り込みは
`tools/dev_wave_wait.py acceptance`のpost-claim merge。
待ち手・launcher・runnerのbytesを変える前進は先に取り込む（F524）。
HEAD差は`--ff-only`で揃える（F48）。新規worktreeは未初期化submoduleで非0。
`DW-C01`に従い初期化して再検査（`deinit`禁止）。取り込みはpointerだけ進む。受入前に
`git submodule update --recursive`で揃える。
子を走らせるworktreeは`git worktree lock`（cwd走査はlauncher型を逃す）。

## DW-O23 — 並行 session の local main land

`tools/dev_wave_land.py`へmain/waveの絶対path、tested main/tip、着地tip、監査commit列を渡す。
監査列の範囲は`<tested main>..<tested tip>`で固定。着地tipで数え直すとrc=23。
協調wave lock内で再照合して着地tipへff-onlyし、**同じlock内**で`docs/spool/`をfoldする。
T/D/F採番・canonical3台帳追記・worklogローテーションは一度だけ。fold赤は`landed`を返さず、0件はno-op。
tracked/index/submodule dirtとincoming衝突untrackedを拒否し、
docs/handoff直下とGit adminに双方向束縛したClaude/Codex worktreeは書式不問で非接触。

成功は`landed`/`already-landed`だけ。postcondition failureは停止。stale/busyは終了せず、
他sessionの処理中dirtyは非接触で終端を待つ。新main監査、固定SHAのwave-side merge、
条件再評価を既存branchで行いlandedまで再試行する。
他session所有物、rebase、force、remote、pushで解消しない。
## DW-O25 — ff-only land の全史 provenance 関門

D254 に従い、land は `locked_main != 着地tip` のときだけ lock を解放して全史 provenance 監査を自ら走らせ、480 秒以内の rc=0 を必須とする。赤は `RC_PROVENANCE = 29` で main を 1 bit も変えず拒否し、CLI flag・環境変数・警告化の逃がし道を作らない。
lock 再取得後に全検査をやり直し、`tip_sha` / `checker_blob_sha` / `executed_bytes_sha` / `returncode` を束縛した receipt を lock 内で再照合する。`already-landed` の no-op と active fold transaction の recovery では監査を起動しない。
## DW-O26 — 焦点走の consumer test 拡張

`DW-O18` の焦点走対象 file 集合は、変更した test file だけでなく、変更した production file を
参照する consumer test も含める。名前の推測でなく参照関係で引く（例: 変更した production module 名で
`orchestrator/tests/` を grep する）。この拡張を欠く焦点走は、静的レビューが見落とした破れを
初回実測でも取り逃す（F242）。
同一 worktree からの dispatch は全種を直列にする。並行投入は orphan hold で rc=16 になる。
変更した test file は受入全走前に単独走で確認する（全走緑は file 単独緑を含意しない）。新規
test file を足す走は file 集合列挙のメタテストも焦点走に含める。並行 wave が自分の編集 file を
所有するなら main 取込み済みの木で既存走行に相乗りし受入後に足さない。
## DW-O27 — acceptance は lease を待たない

D662 により lease 待ち行列は廃止。`acceptance`は投入前 claim を 1 回だけ行い`held`でも待たず
wave digest の疑似 holder で投入する。待つ経路は flag でも戻らない。
`--lease-optional`と`--poll-seconds`は no-op。`stale-held`・`unavailable`は fail-closed。
integrity 検査と receipt 全 field は未取得でも不変。`--lease-dir`は省略せず専用 dir で迂回しない。
未取得が確定した走行は`release`しない。`--wave`は branch 名の末尾一致を要求 (codex の wave slug
とは別でよい)。不一致は`preflight-branch` rc=2。

`tools/check_docs.py` の dispatch 契約へ新節を登録する際は、
`orchestrator/tests/test_check_docs.py` の合成 fixture との整合性を同じ
commit で確認する（`DW-O26` の精神を checker 変更にも適用。怠ると多数の
テストが連鎖的に失敗する — T-1458 実測、320 件）。

## DW-O28 — land 後の自己撤去

親は `landed` / `already-landed` を確認後、同じ段 9 で先に対象 worktree 外の main worktree へ移り、投入した計算ノード job の終端後に次を実行する（`<MAIN>` / `<WAVE>` は絶対 path）。
`python3 tools/dev_wave_cleanup.py --main-worktree <MAIN> --wave-worktree <WAVE> --wave-branch <BRANCH> --tested-wave-tip-sha <TIP>`
tool は unoccupied、clean、tested tip が `refs/heads/main` の祖先、fold state 不在、wave が非 primary、cwd が対象外を全て要求し、どれかが不成立または判定不能なら fail-closed で停止する。
同一 wave の worktree と branch を撤去し、次 wave・ユーザー・`/cleanup-branches` へ引き渡さない。
F26 に従い `git worktree remove` と `git submodule deinit` は使わない。branch は `git branch -d` だけで消し `-D` を使わない。撤去できない理由は報告し、次 wave の worklog へ記録する。
