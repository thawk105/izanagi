# dev-wave 変異検査契約

この文書は `/dev-wave` の変異事前登録、kill 意味論、harness、fix 後再検証の正本である。

## DW-M01 — 事前登録と単一理由性

段 4 で B-057 の変異を実装前に事前登録する。各変異は位置だけでなく、
その位置より前に同じ入力を拒否する検査がないこと、無効化時の赤理由が一つに絞れることを
コードで確認する。確認できなければ登録せず実効 gate へ再照準する（F28）。

## DW-M02 — 所見ゼロの裏取り

レビュー所見ゼロを、変異なしで緑と数えてはならない。変異が生存したら、まず他層による mask と
等価変異を疑い、実効 gate へ再照準して両層同時変異まで裏取りする。初回結果は消さず erratum とする。

## DW-M03 — kill の意味と fixture

kill は単なる赤ではなく、受理集合または fail-closed 挙動が期待方向へ変わった場合だけ数える。
診断文字列だけの赤を kill にしてはならない。fixture が単一理由か確認し、過剰決定なら単一理由へ
差し替えるか、冗長 gate と明記して単独変異の証拠から外す。

## DW-M04 — 置換と注入実在

置換対象が一箇所でなければ harness を停止し、注入なしを緑と報告してはならない。
同一ファイルへの複数置換は累積適用し、置換ごとに累積後内容で一意性を assert する。
SURVIVED は mutated 内容の diff で注入実在を確認するまで equivalent と結論しない。
両層変異は kill 期待を必ず事前登録する（F33）。

## DW-M05 — 復元と単一走行

変異後の復元は対象ファイルの内容比較（`read_text() == 元ソース`）で検査する。
未追跡・未 stage に恒真な `git diff` を復元検査に使わない。harness は `flock` 等の単一走行 guard を持ち、
取得失敗で abort する。生存 process を `pgrep -f` で照合するなら ERE または literal を使い、
BRE の `\|` を使わない（F32）。

## DW-M06 — hang 変異

hang しうる変異は部分集合と timeout で隔離する。timeout を fail-closed から fail-open への
当該変異の証拠として記録し、harness 全体を落とさない。SIGTERM に Python の finally を期待せず、
subprocess timeout と親側 finally によって必ず復元する（F32）。

## DW-M07 — fix 後 anchor

fix 後の最終 commit で変異 spec の anchor（old 逐語）を再検証してから本走する。
単層が他層に mask されたら両層同時変異へ再照準し、初回結果を erratum として台帳へ残す。

## DW-M08 — 失敗 node と検出力

harness は rc だけでなく赤くなった test node を毎回記録する。pytest は `-rf` を指定し、
ANSI を除去して `FAILED <node> - <error>` の `FAILED ` 後から ` - ` 手前までを node として取る。
受理集合を変えず構造化シグナルだけを pin する変異は、kill でなく diagnostic sensitivity pin として
別枠に記録する。テスト強化だけの wave は、新テストと変更前の Git HEAD 版テストの双方へ変異を走らせ、
新テストだけが検出する差分を示す。
