# dev-wave 条件付き運用

条件付き運用の正本。発火条件は入口の条件 dispatch が正本で、本書は各条件が
成立したときの実行手順だけを持つ。操作の直前に該当節を読み、停止条件を迂回しない。

## DW-O01 — codex subprocess 起動

`codex exec -m gpt-5.6-sol -c model_reasoning_effort="<効いた値>" -s <sandbox> -C <dir> -o <出力>.md "$(cat prompt.txt)" < /dev/null` を `bash -c '<cmd>; echo $? > <log>.done'` で包む。
投入前に prompt が非空か検査し、完了は `.done` の存在と exit code だけで判定する。
ログ本文の grep も harness の task 完了通知も完了判定にしてはならず（通知は子より先行しうる）、
成果物は `-o` の最終メッセージから読み（F23/F24）、
採用条件 = `tools/check_codex_output.py <出力>.md` の rc=0（prompt に `## 総括` を義務付ける。F43）。

## DW-O02 — job artifact

prompt、log、patch はすべて wave 専用 subdirectory に置き、
job tmp 直下や過去 wave の同名 artifact と共有しない。専用場所を確保できなければ作成を止める。
親 brief と前段の子成果物は同 subdirectory のファイルへ置き、prompt へ全文複製せず絶対パスで読ませる。
その prompt には読めなければ即停止する指示を入れ、context 無しの子出力をレビュー結果と数えない。

## DW-O03 — 防護パスを含む prompt

WAL、campaign lock、campaign output、submodule 等の防護パス文字列を含む prompt は、
Bash heredoc や不透明な command substitution で作らず、Write ツールで作る。guard を迂回しない。

## DW-O04 — 防護パスを含む commit message

Write ツールで message file を作り、`git commit -F <file>` を使う。
heredoc と command substitution を併用してはならない。

## DW-O05 — read-only codex

書込可能 tmp がないため pytest 緑を要求せず、静的検査でよいと明記する。
テスト実測は親が行い、子の非実走を緑と記録しない。

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
review ledger も対象に含める。path 検索が見つけるのは path を key にする
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

未 stage 削除は `run_tests.py` が受入形の前に検出して止める (final は bypass 不可)。
stage (`git add -A`) 後に再走し、gate の赤を受入結果にしない。

## DW-O12 — 裁定手順と実行手順の差

worklog には裁定予定を写さず、実際に実行した手順を書く。
一次資料と逆の工程記録を残してはならない。

## DW-O13 — gate 入力の実在

設計を書く前に入力が実成果物のどの field に存在するかを確認し、同名識別子を二義化しない（D75）。

## DW-O14 — no-touch と monkeypatch

対象実装まで読み、resolver や `current_head` 等の正規注入 seam がないか確認する。
monkeypatch は最後の手段とする（D78）。

## DW-O15 — fix 後の変異

手順は `DW-M07`。

## DW-O16 — fix 後の焦点再レビュー

所見ごとの closed / partial / regressed 対応表を要求し、表なしで root cause が閉じたと判定しない（D78）。
NO-GO が続く場合は fix を重ねず 3 巡を上限とし、親が変異で裏取りして残る所見を real/refuted に
裁定して閉じる。根拠は worklog に書く。

## DW-O17 — commit trailer

trailer は`docs/ai-provenance.md`に従う（F25）。通常commitはmessage file→`--dry-run -F`単独rc=0
→`commit -F`→既定full-history監査とする。mergeは`OLD_HEAD`を保存し、fast-forwardならincoming監査
→`--ff-only`→full監査、merge commitなら`merge --no-ff --no-commit <tip>`→競合解消→同じpreflight
→`commit -F`→full監査とする。自動message/`--no-edit`は禁止。`OLD_HEAD..HEAD`は補助で、correctionを
含むときは両commitを含むrangeかfull監査だけを権威とする。検査rcをパイプに通さず、赤なら止める（F37）。
競合解消が実装面ならCodex`role=author`へ回す。

## DW-O18 — 親のテスト cwd

cwd を必ず repo root にする。nested subprocess の import path による偽赤を、差分の回帰として扱わない。
差分が到達しえないファイルで出た赤は、単独再走で再現性を実測してから扱う。
再現しなければ実装差分へ帰属せず、フレークとして新規所見に起票する。
測定値は測った checkout を併記する（F41）。

## DW-O19 — tracked file の一時変異

復元は `git diff` と `git checkout --` を正本とし、外部 backup を使わない。
本走は統合 commit 後に限る。変異前を clean 確認し、変異後の `git diff --stat` が対象 file の
意図した単一変異だけ (単一 entry が複数行ならその範囲) であることを確認して復元する。
復元 bytes は commit と照合する。phase 完了は実装と同じ anchor commit へ含め、本走後の raw 台帳は
後続の記録 commit へ置く。anchor を amend して自己 hash 循環を作らない。
段 1 前提実測は本走でないが、この復元規律に従う。

## DW-O20 — clean-tree gate

専用handoffはworktree外（背景jobはrepo外）に置き、untracked handoffを残してgateを走らせない。
cwdが既にworktreeなら作成せず、directory/branch不一致をhandoff・worklogへ記録してwaveの
worktreeを流用しない。作成・再開直後に`tools/check_wave_startup.py`（背景jobは
`--external-handoff <handoff>`付き）を実行し、非0なら停止する。HEAD差は`--ff-only`だけで揃える（F48）。

## DW-O23 — 並行 session の local main land

`tools/dev_wave_land.py`へmain/waveの絶対path、tested main/tip、監査commit列を渡す。
協調wave lock内で再照合し、tipへのff-onlyだけ行う。ff-only成功後は**同じlockを保持したまま**
`docs/spool/`のfragmentをfoldし、T/D/Fの採番・canonical3台帳への追記・worklogローテーションを
一度だけ行う。foldが赤なら`landed`を返さない。fragment0件のfoldはno-opで、既存挙動を変えない。
**wave側でfoldしてはならない**（lock外のfoldは直列化されず、採番衝突とfold commit破棄を招く）。tracked/index/submodule dirtとincoming衝突untrackedを拒否し、
docs/handoff直下とGit adminに双方向束縛したClaude/Codex worktreeは書式不問で非接触。

成功は`landed`/`already-landed`だけ。postcondition failureは停止。stale/busyはfresh contextで
既存branchを再利用し、新main監査、固定SHAのwave-side merge、条件再評価・受入後に再試行する。
他session所有物、rebase、force、remote、pushで解消しない。
