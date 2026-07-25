# dev-wave 条件付き運用

この文書は `/dev-wave` の条件付き運用 `DW-O01`〜`DW-O20` の正本である。
入口の条件を成立させる操作の直前に該当節を読み、停止条件を迂回しない。

## DW-O01 — codex subprocess 起動

発火: codex subprocess を起動する直前。`codex exec -m gpt-5.6-sol -c model_reasoning_effort="<効いた値>" -s <sandbox> -C <dir> -o <出力>.md "$(cat prompt.txt)" < /dev/null` を `bash -c '<cmd>; echo $? > <log>.done'` で包む。
投入前に prompt が非空か検査し、完了は `.done` の存在と exit code だけで判定する。
ログ本文を grep して完了判定してはならず、成果物は `-o` の最終メッセージから読む（F23/F24）。

## DW-O02 — job artifact

発火: prompt、log、patch を作る直前。すべて wave 専用 subdirectory に置き、
job tmp 直下や過去 wave の同名 artifact と共有しない。専用場所を確保できなければ作成を止める。
親 brief と前段の子成果物は同 subdirectory のファイルへ置き、prompt へ全文複製せず絶対パスで読ませる。
その prompt には読めなければ即停止する指示を入れ、context 無しの子出力をレビュー結果と数えない。

## DW-O03 — 防護パスを含む prompt

発火: prompt に WAL、campaign lock、campaign output、submodule 等の防護パス文字列を含める直前。
Bash heredoc や不透明な command substitution で作らず、Write ツールで作る。guard を迂回してはならない。

## DW-O04 — 防護パスを含む commit message

発火: 防護パス文字列を含む commit message を作る直前。Write ツールで message file を作り、
`git commit -F <file>` を使う。heredoc と command substitution を併用してはならない。

## DW-O05 — read-only codex

発火: read-only codex へ相談・レビューを依頼する直前。書込可能 tmp がないため pytest 緑を要求せず、
静的検査でよいと明記する。テスト実測は親が行い、子の非実走を緑と記録しない。

## DW-O06 — submodule 系 real-repo test

発火: workspace-write 子が submodule 系 real-repo test を扱う直前。
submodule の index lock を作れない sandbox 由来の偽赤と連鎖赤を親環境で独立再現し、
再現しない赤を実装差分へ帰属しない。

## DW-O07 — task-run pilot

発火: task-run pilot が有効な wave の開始前。`output/task-runs/README.md` の start/check/finish 契約と
`start --slug <slug> --objective "<1 行>" --task-class 3 --task-kind <kind>` の 4 必須引数を使う。
受入は task-run ID 付きで走らせ、check の後に `finish --outcome <outcome> <id>` で閉じる。
上限拒否時は上限を変更せず、
台帳なしで wave を継続して発火条件を最終報告する。

## DW-O08 — freeze 族の初期化

発火: freeze、oracle gate、proof chain に触る可能性が判明した時点。最遅読了は段 1 brief 前。
最初に `git submodule update --init` を行う。期限後に判明したら既存 brief 以降を invalidate し、
段 1 brief から再実行する。未初期化による skip や手前の赤を破損なしと報告してはならない。

## DW-O09 — 凍結 bytes の pin 閉包

発火: 凍結成果物の bytes を変えうる可能性が判明した時点。最遅読了は段 1 brief 前。
着手前に `grep -rn "<成果物パス>" --include=*.py` を使い、
bytes を pin する台帳・test・trust root を全列挙する。
`FROZEN_MANIFEST`、generator source hash pin、key→canonical path 束縛を既定対象に含め、
durable manifest が未発行か、発行済みで再発行が必要かを区別して brief の不変条件へ書く（F27/F30、D84）。
期限後に判明したら brief 以降を invalidate し、段 1 brief から再実行する。

## DW-O10 — producer write-path

発火: `DW-O09` が成立し、対象 producer の出力 bytes が変わりうる時だけ。最遅読了は段 1 brief 前。
producer が書く全ファイル種を棚卸しして brief に列挙する。非凍結 producer 一般へ拡張しない。
期限後に判明したら brief 以降を invalidate し、段 1 brief から再実行する。

## DW-O11 — ファイル削除

発火: ファイル削除を伴うと判明した時点。受入全走より前に `git add -A` で削除を stage する。
未 stage 削除で freeze test が偽赤なら受入結果にせず、stage 後に再走する。

## DW-O12 — 裁定手順と実行手順の差

発火: 裁定した手順と実行した手順が食い違った時点。worklog には裁定予定を写さず、
実際に実行した手順を書く。一次資料と逆の工程記録を残してはならない。

## DW-O13 — gate 入力の実在

発火: gate・検証を新設する可能性が生じた時点。最遅読了は段 2 のプラン起草前。
設計を書く前に入力が実成果物のどの field に存在するかを確認し、同名識別子を二義化しない（D75）。
段 2 後に判明したら段 2 以降の成果物を invalidate し、段 2 から再実行する。

## DW-O14 — no-touch と monkeypatch

発火: no-touch 対象の検査へ monkeypatch を検討する直前。対象実装まで読み、
resolver や `current_head` 等の正規注入 seam がないか確認する。monkeypatch は最後の手段とする（D78）。

## DW-O15 — fix 後の変異

発火: fix round 後に変異を走らせる直前。最終 commit で anchor を再検証し、
mask 時は両層変異へ再照準する。初回結果を消さず erratum とする。詳細は `DW-M07` に従う。

## DW-O16 — fix 後の焦点再レビュー

発火: fix 後の焦点再レビューを依頼する直前。所見ごとの closed / partial / regressed 対応表を要求し、
表なしで root cause が閉じたと判定しない（D78）。

## DW-O17 — commit trailer

発火: commit を作る直前。件名、本文、末尾 trailer block を分け、
`AI-Agent` と `Co-Authored-By` を空行なしの同一最終段落へ置く（F25）。
詳細は `docs/ai-provenance.md` に従い、commit 後の監査を省略しない。
検査の rc はパイプに通さず単独で取り、赤のまま commit しない（F37）。

## DW-O18 — 親のテスト cwd

発火: 親がテスト・受入を走らせる直前。cwd を必ず repo root にする。
nested subprocess の import path による偽赤を、差分の回帰として扱わない。

## DW-O19 — tracked file の一時変異

発火: tracked file を一時変異し `git checkout --` で復元する直前。
復元の正本は `git diff` と `git checkout --` とし、外部 backup に頼らない。
編集前後で `git diff --stat` が対象ファイルの意図した単一変異だけ (単一 entry が複数行ならその複数行に限り、他ファイル・意図外の変更なし) であることを必ず確認してから `git checkout --` で復元する。
この方式の本走は統合 commit 後だけに限定し、commit 前の実装へ実行してはならない。
復元後は内容を commit 済み内容と比較する。

## DW-O20 — clean-tree gate

発火: worktree で clean-tree gate を走らせる前。専用 handoff を対象 worktree の外へ置く。
untracked handoff を残したまま gate を走らせず、job tmp または main checkout 側で生存性を確保する。
背景 job が worktree 隔離下にある場合、harness が main checkout への書込を拒否するため job tmp を使う。
