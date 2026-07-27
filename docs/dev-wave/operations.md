# dev-wave 条件付き運用

条件付き運用 `DW-O01`〜`DW-O20` の正本。発火条件は入口の条件 dispatch が正本で、本書は各条件が
成立したときの実行手順だけを持つ。操作の直前に該当節を読み、停止条件を迂回しない。

## DW-O01 — codex subprocess 起動

`codex exec -m gpt-5.6-sol -c model_reasoning_effort="<効いた値>" -s <sandbox> -C <dir> -o <出力>.md "$(cat prompt.txt)" < /dev/null` を `bash -c '<cmd>; echo $? > <log>.done'` で包む。
投入前に prompt が非空か検査し、完了は `.done` の存在と exit code だけで判定する。
ログ本文を grep して完了判定してはならず、成果物は `-o` の最終メッセージから読む（F23/F24）。

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

## DW-O07 — task-run pilot

`output/task-runs/README.md` の start/check/finish 契約と
`start --slug <slug> --objective "<1 行>" --task-class 3 --task-kind <kind>` の 4 必須引数を使う。
受入は task-run ID 付きで走らせ、check の後に `finish --outcome <outcome> <id>` で閉じる。
上限拒否時は上限を変更せず、台帳なしで wave を継続して発火条件を最終報告する。

## DW-O08 — freeze 族の初期化

最初に `git submodule update --init` を行う。
未初期化による skip や手前の赤を破損なしと報告してはならない。

## DW-O09 — 凍結 bytes の pin 閉包

着手前に `grep -rn "<成果物パス>" --include=*.py` を使い、
bytes を pin する台帳・test・trust root を全列挙する。
`FROZEN_MANIFEST`、generator source hash pin、key→canonical path 束縛を既定対象に含め、
durable manifest が未発行か、発行済みで再発行が必要かを区別して brief の不変条件へ書く（F27/F30、D84）。

## DW-O10 — producer write-path

`DW-O09` が成立し対象 producer の出力 bytes が変わりうるときだけ適用する。
producer が書く全ファイル種を棚卸しして brief に列挙する。非凍結 producer 一般へ拡張しない。

## DW-O11 — ファイル削除

受入全走より前に `git add -A` で削除を stage する。
未 stage 削除で freeze test が偽赤なら受入結果にせず、stage 後に再走する。

## DW-O12 — 裁定手順と実行手順の差

worklog には裁定予定を写さず、実際に実行した手順を書く。
一次資料と逆の工程記録を残してはならない。

## DW-O13 — gate 入力の実在

設計を書く前に入力が実成果物のどの field に存在するかを確認し、同名識別子を二義化しない（D75）。

## DW-O14 — no-touch と monkeypatch

対象実装まで読み、resolver や `current_head` 等の正規注入 seam がないか確認する。
monkeypatch は最後の手段とする（D78）。

## DW-O15 — fix 後の変異

手順は `DW-M07` に従う（同節を複製しない）。

## DW-O16 — fix 後の焦点再レビュー

所見ごとの closed / partial / regressed 対応表を要求し、表なしで root cause が閉じたと判定しない（D78）。
NO-GO が返り続ける場合は無制限に fix を重ねず、3 巡を上限として親が変異で裏取りし、
残る所見を real/refuted に裁定して閉じる。閉じた根拠は worklog に書く。

## DW-O17 — commit trailer

件名、本文、末尾 trailer block を分け、
`AI-Agent` と `Co-Authored-By` を空行なしの同一最終段落へ置く（F25）。
詳細は `docs/ai-provenance.md` に従い、commit 後の監査を省略しない。
検査の rc はパイプに通さず単独で取り、赤のまま commit しない（F37）。

## DW-O18 — 親のテスト cwd

cwd を必ず repo root にする。nested subprocess の import path による偽赤を、差分の回帰として扱わない。
差分が到達しえないファイルで出た赤は、単独再走で再現性を実測してから扱う。
再現しなければ実装差分へ帰属せず、フレークとして新規所見に起票する。
測定値は測った checkout を併記する（F41）。

## DW-O19 — tracked file の一時変異

復元の正本は `git diff` と `git checkout --` とし、外部 backup に頼らない。
編集前後で `git diff --stat` が対象ファイルの意図した単一変異だけ (単一 entry が複数行ならその複数行に限り、他ファイル・意図外の変更なし) であることを必ず確認してから `git checkout --` で復元する。
この方式の本走は統合 commit 後だけに限定し、commit 前の実装へ実行してはならない。
段 1 の前提実測は本走ではなく、`DW-S01` に従って復元規律だけを借りる。
復元後は内容を commit 済み内容と比較する。

## DW-O20 — clean-tree gate

専用 handoff を対象 worktree の外へ置く。
untracked handoff を残したまま gate を走らせず、job tmp または main checkout 側で生存性を確保する。
背景 job が worktree 隔離下にある場合、harness が main checkout への書込を拒否するため job tmp を使う。
背景 job の cwd が既に worktree なら `EnterWorktree` は新規作成を拒む。そのまま作業してよいが、
ディレクトリ名と branch 名の食い違いを handoff と worklog に明記し、別 wave の worktree を流用しない。
