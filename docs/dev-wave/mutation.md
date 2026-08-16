# dev-wave 変異検査契約

変異事前登録、kill 意味論、harness、fix 後再検証の正本。

## DW-M01 — 事前登録と単一理由性

段 4 で B-057 の変異を実装前に登録する。各変異は位置に加え、同じ入力を拒否する層が前後に
無いこと、無効化時の赤理由が一つに絞れることをコードで確認する。確認できなければ
登録せず実効 gate へ再照準する（F28）。受理集合を縮小する wave では、承認外の過剰拒否を検出する
正例も登録する。テスト強化だけの wave は `DW-M08` の新旧両走も登録する。

## DW-M02 — 所見ゼロの裏取り

レビュー所見ゼロを変異なしで緑と数えない。変異が生存したらまず他層の mask と等価変異を疑い、実効 gate へ再照準して両層同時変異まで裏取りする。初回結果は消さず erratum に残す。

## DW-M03 — kill の意味と fixture

kill は受理集合か fail-closed 挙動が期待方向へ変わったときだけ数え、診断文字列だけの赤を kill に
しない。fixture が単一理由か確認し、過剰決定なら単一理由へ差し替えるか、冗長 gate と明記して
単独変異の証拠から外す。

## DW-M04 — 置換と注入実在

置換対象が一箇所でなければ停止し、注入なしを緑と報告しない。同一ファイルの複数置換は累積適用し、
置換ごとに累積後の一意性を assert する。SURVIVED は mutated 内容の diff で注入実在を確認するまで
equivalent としない。両層変異は kill 期待を必ず事前登録する（F33）。

## DW-M05 — 復元と単一走行

変異 harness は `tools/mutation_harness.py` を使う（元ソースの固定 HEAD 束縛、起動・復元時の
内容比較、`flock` 単一走行、逐次 flush、HEAD/spec 束縛の `--resume`、signal 復元を fail-closed で
強制する。F32）。独自 harness は同等の検査を備えると段 4 で事前登録する。
起動前に総所要を見積り、外側の実行時間上限に掛からない経路で起動する。この 2 つは tool が
検証できない自己申告で親の義務に残る。生存 process を `pgrep -f` で照合するなら ERE か literal を
使い BRE の `\|` を避け、待ち手自身と並行 wave の子に当たらないよう worktree path で一意化する。

## DW-M06 — hang 変異

hang しうる変異は spec の `hang_risk` で部分集合と timeout へ隔離する。timeout は当該変異が
fail-closed から fail-open へ倒れた証拠として記録し、harness 全体を落とさない（F32）。

## DW-M07 — fix 後 anchor

fix 後の最終 commit で変異 spec の anchor（old 逐語）と期待 node を再検証してから本走する。
mask 時の再照準と erratum は `DW-M02` に従い台帳へ残す。
本走は `--runner-mode dispatch` を既定とし、runner argv へ `--force-dispatch` を入れる。
local は同一 target set の 2 巡目以降で予算 attest が落ち収集段が `rc=16` になる。
`--attempt-out` と `--wrapper-attempt` は dispatch 専用で、local 指定は起動前に中止する。
`--wrapper-attempt` は整数、実走は `--detached` 必須で、欠けると変異を 1 件も実行せず中止する。
KILLED 期待で期待 node が空の spec も起動前に中止するため、probe は全件 SURVIVED 期待で登録して
観測 node を集める。
`--out` は `--scratch-root` と同一 device に置く（別 device は evidence 退避の rename が落ちる）。

## DW-M08 — 失敗 node と検出力

harness は rc と失敗 test node を毎回記録する。pytest は `-rf`、node 抽出は F71 に従う
（正本は job stdout 全文、行前置と ANSI を除去、` - ` 無しは行末まで、rc≠0 で 0 件は
fail-closed 停止）。
**期待 node は完全集合**で、同形式へ正規化した記録 node との完全一致だけを KILLED とする（F33）。
確定できない場合に限り初回を probe と明記し erratum を残して再登録・再走する。
受理集合を変えず構造化シグナルだけを pin する変異は kill でなく diagnostic sensitivity pin へ
別枠記録する。テスト強化だけの wave は新テストと変更前 HEAD 版の双方へ変異を走らせ、新テスト
だけが検出する差分を示す。
