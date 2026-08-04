# dev-wave 変異検査契約

変異事前登録、kill 意味論、harness、fix 後再検証の正本。

## DW-M01 — 事前登録と単一理由性

段 4 で B-057 の変異を実装前に登録する。各変異は位置に加え、同じ入力を拒否する層が前後に
無いこと、無効化時の赤理由が一つに絞れることをコードで確認する。確認できなければ
登録せず実効 gate へ再照準する（F28）。受理集合を縮小する wave では、承認外の過剰拒否を検出する
正例も登録する。テスト強化だけの wave は `DW-M08` の新旧両走も登録する。

## DW-M02 — 所見ゼロの裏取り

レビュー所見ゼロを変異なしで緑と数えない。変異が生存したらまず他層の mask と等価変異を疑い、実効 gate へ再照準して両層同時変異まで裏取りする。初回結果は消さず erratum とする。

## DW-M03 — kill の意味と fixture

kill は受理集合か fail-closed 挙動が期待方向へ変わったときだけ数え、診断文字列だけの赤を
kill にしない。fixture が単一理由か確認し、過剰決定なら単一理由へ差し替えるか、
冗長 gate と明記して単独変異の証拠から外す。

## DW-M04 — 置換と注入実在

置換対象が一箇所でなければ停止し、注入なしを緑と報告しない。
同一ファイルの複数置換は累積適用し、置換ごとに累積後の一意性を assert する。
SURVIVED は mutated 内容の diff で注入実在を確認するまで equivalent としない。
両層変異は kill 期待を必ず事前登録する（F33）。

## DW-M05 — 復元と単一走行

変異 harness は `tools/mutation_harness.py` を使う。同 tool は元ソースの固定 HEAD 束縛、
起動・復元時の内容比較、`flock` 単一走行、逐次 flush、HEAD/spec 束縛の `--resume`、signal 復元を
fail-closed で強制する（F32）。独自 harness は同等の検査を備えると段 4 で事前登録する。
起動前に総所要を見積り、外側の実行時間上限に掛からない経路で起動する。この 2 つは tool が
検証できない自己申告なので親の義務に残る。生存 process を `pgrep -f` で照合するなら
ERE か literal を使い BRE の `\|` を避け、待ち手自身と並行 wave の子に当たらないよう
worktree path で一意化する。

## DW-M06 — hang 変異

hang しうる変異は spec の `hang_risk` で部分集合と timeout に隔離する。timeout は当該変異が
fail-closed から fail-open へ倒れた証拠として記録し、harness 全体を落とさない（F32）。

## DW-M07 — fix 後 anchor

fix 後の最終 commit で変異 spec の anchor（old 逐語）を再検証してから本走する。
mask 時の再照準と erratum は `DW-M02` に従い台帳へ残す。

## DW-M08 — 失敗 node と検出力

harness は rc に加え赤くなった test node を毎回記録する。pytest は `-rf` を指定し、
node 抽出は F71 に従う（正本は job stdout 全文、行前置と ANSI を除去、` - ` 無しは行末まで、
rc≠0 で 0 件は fail-closed 停止）。
事前登録の期待 node と記録 node は突き合わせ前に同じ形式へ正規化する（F33）。
受理集合を変えず構造化シグナルだけを pin する変異は、kill でなく diagnostic sensitivity pin と
して別枠に記録する。テスト強化だけの wave は、新テストと変更前 HEAD 版テストの双方へ変異を走らせ、
新テストだけが検出する差分を示す。
