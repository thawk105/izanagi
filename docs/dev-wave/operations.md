# dev-wave 条件付き運用

発火条件の正本は入口の条件 dispatch、成立時の実行手順だけは本書が正本。
該当節を操作直前に読み、停止条件を迂回しない。

## DW-O01 — codex subprocess 起動

`tools/dev_wave_codex.py --stage <stage> [--lane <lane>] -o <出力>.md` で起動（他の引数は `--help`）。model は全段、effort は段 5 / 6 が docs 権威から導出。caller 指定は不可。
背景 job は `nohup setsid bash -c '<cmd>; echo $? > <log>.done' </dev/null` で detach。
prompt 非空を先に検査し、既存 `.done` は消さず再利用せず再投入を止める。
待機は `tools/dev_wave_wait.py producer` を使い、`--pid-file` は producer script 自身が `echo $$` で書く。
完了は `.done` と exit code だけで判定し、grep も通知も判定にしない（通知は先行しうる）。成果物は最終メッセージから読む（F23/F24）。
採用は `tools/check_codex_output.py` の rc=0（prompt は `## 総括` 必須。F43）。
`<model>`: 全段 `gpt-5.6-sol` (段 3 の 2 本も同じ)。
`--artifact-root` は `<root>/<wave>/` しか作らず、`<root>` 未作成は rc=2。投入前に作る。
`--max-*` は非権威の運用既定で caller が上げてよい。重い巡は所要 model call と token を見積もる。
中断子の部分成果物は未完了と明記して保全し、次の子へ監査させる。

## DW-O02 — job artifact

prompt、log、patch はすべて wave 専用 subdirectory に置き、job tmp 直下や過去 wave の同名
artifact と共有しない。専用場所を確保できなければ作成を止める。
親 brief と前段の子成果物は同 subdirectory のファイルへ置き、prompt へ全文複製せず絶対パスで
読ませる。その prompt には読めなければ即停止する指示を入れ、context 無しの子出力をレビュー結果と
数えない。必読資料は job dir へ取り出して渡す（repo 内 path は worktree の遅れで fail-closed する）。
出力へ結合文字 U+0300〜U+036F を使わせない。
prompt 先頭は AGENTS.md の単独段例外と同形式。

## DW-O03 — 防護パスを含む prompt

WAL、campaign lock、campaign output、submodule 等の防護パス文字列を含む prompt は
Bash heredoc や不透明な command substitution で作らず Write ツールで作る。guard を迂回しない。

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

着手前に `grep -rn "<成果物パス>" --include=*.py` を使い、
bytes を pin する台帳・test・trust root を全列挙する。
`FROZEN_MANIFEST`、generator source hash pin、key→canonical path 束縛、output 外の
review ledger、全 field から同一性 hash を導く dataclass・schema も対象に含める。path 検索が見つけるのは path を key にする
pin だけである。review ledger のように role 名を key に張る pin は key 側でも検索し、
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

## DW-O12 — 裁定手順と実行手順の差

worklog には裁定予定を写さず、実際に実行した手順を書く。
一次資料と逆の工程記録を残してはならない。
受理集合を変える指示を子へ出す直前に、この wave で凍結済みの事前登録・判定式を再読する。
凍結は自分が直前に書いたものでも拘束する。
DW-S06-C の受入投入記述は段6内の中間走行 (変異検証目的) を指す。land 対象 tip への最終受入投入は
DW-S07 の記録 commit 完了後に行う——取り違えると記録 commit が tested tip から漏れ land が rc=23
になる。測定値は測った checkout を併記する（F41）。

## DW-O13 — gate 入力の実在

設計前に入力が実成果物のどの field に存在するか確認し、同名識別子を二義化しない（D75）。
既存 exact 述語の改訂で受理形を増やす場合も新設に当たる。
時間予算を持つ検査を新設するなら、値は実測分布の max に対する倍率で決め、母集合と
「観測した regime が予算の適用対象と同じか」を併記する。正例は余裕を取り、負例は確実に
発火する小さい値にする（要求が逆向きで、一律に余裕を取ると負例が恒真になる）。
内側予算の和 + 終了処理余裕 < 外側 watchdog を、定数でなく検査自身に確かめさせる。

## DW-O14 — no-touch と monkeypatch

対象実装まで読み、resolver や `current_head` 等の正規注入 seam がないか確認する。
monkeypatch は最後の手段とする（D78）。

## DW-O16 — fix 後の焦点再レビュー

所見ごとの closed / partial / regressed 対応表を要求し、表なしで root cause が閉じたと判定しない（D78）。
NO-GO が続く場合は fix を重ねず 3 巡を上限とし、親が変異で裏取りして残る所見を real/refuted に
裁定して閉じる。根拠は worklog に書く。

## DW-O17 — commit trailer

trailer は`docs/ai-provenance.md`に従う（F25）。通常commitはmessage file→`--dry-run -F`単独rc=0
→`commit -F`→既定full-history監査。mergeは`OLD_HEAD`を保存し、fast-forwardならincoming監査
→`--ff-only`→full監査、merge commitなら`merge --no-ff --no-commit <tip>`→競合解消→同じpreflight
→`commit -F`→full監査。自動message/`--no-edit`は禁止。`OLD_HEAD..HEAD`は補助で、correctionを
含むときは両commitを含むrangeかfull監査だけが権威。検査rcをパイプに通さず、赤なら止める（F37）。
実装面pathが両親と異なればCodex`role=author`へ。
競合解決の`git add -A`はsubmoduleの未解決gitlinkを古い作業ツリー側で確定させる。`git ls-tree main
<sub>`と突き合わせ**merge commit内で**main側pinへ揃える。後追い単独commitは実装面判定で書けない
Codex著者行を要求されlandが止まる。

## DW-O18 — 親のテスト cwd

cwd は必ず repo root。nested subprocess の import path 偽赤は差分の回帰として扱わない。
file 選択走は `from tests import` の import path 確立後に走らせる (未確立の赤は偽赤)。
差分到達しえない赤は単独再走で実測し、再現しなければ非帰属フレーク起票。
`tools/check_acceptance_reds.py` は rc=1 停止・rc=2 判定不能で非帰属根拠なし・checker infra
失敗 (no-verdict retry 対象外、新規 attempt 再投入) の3種を区別。rc=0+
non-attributable-only は受理成功、赤だけで失敗と早合点しない。変更した test file は受入全走前に単独走で確認する
(全走緑は file 単独緑を含意しない)。新規 test file を足す走は file 集合列挙の
メタテストも焦点走に含める。並行 wave が自分の編集 file を所有するなら main 取込み済みの
木で既存走行に相乗りし受入後に足さない。

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
（既存は rc=2）。`--wrapper-attempt` は試行番号。

## DW-O20 — clean-tree gate

専用handoffはworktree外（背景jobはrepo外）に置き、untracked handoffを残してgateを走らせない。
cwdが既にworktreeなら作成せず、directory/branch不一致をhandoff・worklogへ記録してwaveの
worktreeを流用しない。作成直後は`tools/check_wave_startup.py`、再開直後は`--mode resume`付きで
実行し（背景jobは`--external-handoff <handoff>`も）、非0なら停止する。resumeも
branch・clean tree・main包含を要求。HEAD差は`--ff-only`で揃える（F48）。
新規worktreeはsubmodule未初期化で非0になる。worktree内で`DW-C01`に従い初期化して
再検査する（`deinit`は使わない）。取り込みはsubmodule pointerを進めるがworking treeを更新しない。
受入投入前に`git submodule update --recursive`で記録へ揃える。
子を走らせるworktreeは`git worktree lock`する（cwd走査はlauncher型の子を検出しない）。

## DW-O23 — 並行 session の local main land

`tools/dev_wave_land.py`へmain/waveの絶対path、tested main/tip、監査commit列を渡す。
協調wave lock内で再照合し、tipへのff-onlyだけ行う。ff-only成功後は**同じlockを保持したまま**
`docs/spool/`のfragmentをfoldし、T/D/Fの採番・canonical3台帳への追記・worklogローテーションを
一度だけ行う。foldが赤なら`landed`を返さない。fragment0件のfoldはno-op。
**wave側でfoldしてはならない**（lock外のfoldは直列化されず、採番衝突とfold commit破棄を招く）。tracked/index/submodule dirtとincoming衝突untrackedを拒否し、
docs/handoff直下とGit adminに双方向束縛したClaude/Codex worktreeは書式不問で非接触。

成功は`landed`/`already-landed`だけ。postcondition failureは停止。stale/busyはfresh contextで
既存branchを再利用し、新main監査、固定SHAのwave-side merge、条件再評価・受入後に再試行する。
他session所有物、rebase、force、remote、pushで解消しない。
## DW-O25 — ff-only land の全史 provenance 関門

D254 に従い、land は `locked_main != tested_tip` のときだけ lock を解放して全史 provenance 監査を自ら走らせ、480 秒以内の rc=0 を必須とする。赤は `RC_PROVENANCE = 29` で main を 1 bit も変えず拒否し、CLI flag・環境変数・警告化の逃がし道を作らない。
lock 再取得後に全検査をやり直し、`tip_sha` / `checker_blob_sha` / `executed_bytes_sha` / `returncode` を束縛した receipt を lock 内で再照合する。`already-landed` の no-op と active fold transaction の recovery では監査を起動しない。
## DW-O26 — 焦点走の consumer test 拡張

`DW-O18` の焦点走対象 file 集合は、変更した test file だけでなく、変更した production file を
参照する consumer test も含める。名前の推測でなく参照関係で引く（例: 変更した production module 名で
`orchestrator/tests/` を grep する）。この拡張を欠く焦点走は、静的レビューが見落とした破れを
初回実測でも取り逃す（F242）。
## DW-O27 — acceptance は lease を待たない

D662 により受入 lease の待ち行列は廃止し、待ち機構を実装から除去した。
`tools/dev_wave_wait.py acceptance` は投入前 claim を 1 回だけ行い、`held` でも待たず
wave digest の疑似 holder で投入する。待つ経路は無く flag でも戻せない。
`--lease-optional` と `--poll-seconds` は後方互換の no-op。`stale-held`・`unavailable`
は従来どおり fail-closed。integrity 検査と receipt の全 field は未取得でも不変。
`--lease-dir` は省略せず専用 dir で迂回しない。未取得が確定した走行は `release` しない。

`tools/check_docs.py` の dispatch 契約へ新節を登録する際は、
`orchestrator/tests/test_check_docs.py` の合成 fixture との整合性を同じ
commit で確認する（`DW-O26` の精神を checker 変更にも適用。怠ると多数の
テストが連鎖的に失敗する — T-1458 実測、320 件）。
