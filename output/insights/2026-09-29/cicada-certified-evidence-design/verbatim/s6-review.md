## 所見

- **R1｜must-fix｜一次資料 §3.2・§3.5・§4、decisions fragment 項 1・4。** 段 4 裁定は、B を「Version 外の、退役・再利用事象が消えない TRACE 専用台帳」で照合し、版ポインタを終了時に再参照しないと定めた（`s4-ruling.md:10,22,30`）。一次資料は Version 内の世代番号を終了時に再読する方式へ変更し（`README.md:58,93,100`）、fragment もそれを決定として記す（`decisions fragment:12,15`）。**放置すると、裁定された B とは別の方式と安全性の根拠が台帳上で確定する。** 裁定どおり外部事象台帳へ戻すか、方式変更を明示して再裁定し、並行する退役・再利用時の照合条件を示す。調べた YCSB・`REUSE_VERSION=1`・inline なしの経路では、走行中に Version object を `delete` する反例は見つからなかった。`gcAfterThisVersion` と未設置版の `writeSetClean` は pool へ戻す（`external/ccbench/cc/cicada/include/transaction.hh:173-195,343-365`）。一方、この陰性結果だけでは裁定変更は成立しない。

- **R2｜must-fix｜一次資料 §3.2・§6、decisions fragment 項 1。** 段 4 裁定 A3 は、certified 化では write intent **と**成功した read API と read set の照合を必須にした（`s4-ruling.md:11`）。一次資料は両者を「任意」「推奨」とし（`README.md:62`）、案 A の全層にも明記しない（`README.md:137-143`）。fragment 内も項 1 では「含める」、項 1 冒頭では必須面を B・U・P の 3 面と記し、位置付けが曖昧である（`decisions fragment:9,12`）。**放置すると、read set を通らない成功 read が trace から消える variant を、案 A の認定対象に残す。** A の必須連言と完了条件へ API の双方向照合を明記し、再読・read-own-write をどう数えるかも定義する（実際の分岐は `transaction.cc:153-189`）。

- **R3｜should｜一次資料 §3.1・§3.3、decisions fragment 理由。** 「版の選び方を誤れば巡回として現れる」は過大である（`README.md:50,70`、`decisions fragment:20`）。判定器は wts 順の直後版へ rw 辺を張る（`orchestrator/verifier/dsg.py:752-785`）。例えば W₂ が確定した後の R が古い W₁ を読んでも、R→W₂ の辺だけなら非巡回になり得る。これは 1SR と Cicada の snapshot 規則を区別すべき例であり、段 3 所見も終状態などへの拡張を戒めている（`consult-a.md:9`）。**放置すると、巡回 0 が誤った版選択全般を検出するかのように論文の限界が広がる。** 「忠実に記録された履歴がこの版順で 1SR か」を判定する、と表現を限定し、版選択規則そのものの適合は未検査と書く。

- **R4｜should｜一次資料 §8。** 段 4 裁定は B の壊しを「退役事象が B カウンタへ届く最小列」、U を「公開漏れ 1 件を後続待機なしで作る」と具体化した（`s4-ruling.md:15`）。完了条件は B・U の違反行と異常終了の除外までで、両壊しの成立条件が抜ける（`README.md:168`）。**放置すると、壊し試験の失敗や停止を検出力の証拠と取り違え得る。** 裁定した各変異の作り方と、対象カウンタの増加を完了条件に追記する。

- **R5｜nit｜一次資料 §5.1・§5.2。** trace の 78,823,348／196,322,301 byte は、原本の trace **ファイル**合計 78,819,252／196,318,205 byte にそれぞれディレクトリ 4,096 byte を加えた値である（`README.md:107-112`、原本 `runs/j1-c/raw/J1/STOCK_INSTR-{K,R}-t4.trace/`）。また 10〜16 run × 80 s は約 **0.22〜0.36** node 時間で、表の 0.3〜0.4 とは下端が合わない（`README.md:124`）。**放置すると、見積りの基準量と算術を再計算できない。** byte は「ディレクトリを含む」と注記し、node 時間の範囲を計算値か保守的な丸め値として揃える。

## 正しいと確認した点

- `certified` の連言、X・P の文面評価、Cicada が対象 protocol 外であることは記述どおり（`orchestrator/verifier/model.py:37,77-82,233-267,501-519,569-572`）。header を現行評価が読まないこと、未知 tag を parser が拒否することも一致する（`model.py:119-180`、`parse.py:503-505`）。
- 3,938 件中 159 件は GC 接続記録の **E-hb** の値で、同記録には E の 174／3,882 件もある（`vhash-gc-connection-prototype/README.md:60-65`）。一次資料の引用は E-hb の例として読めば一致する。175,139／917,498 txn と 4.67／13.14 s も `result-J1.json` と一致する。
- campaign lock の exact 96 path closure には挙げられた verifier 7 file が入り、source 許可・floor baseline に Cicada が無いという記述もコードに一致する（`campaign_lock.py:47-73`、`source_digest.py:85-100`、`between_run_floor.py:60-84`）。
- worklog fragment の [T-2874] は元 item の (1)・(3)・(4)・(5) を保持し、(2) を判断待ちへ更新している（`docs/worklog.md:469`、`worklog fragment:25`）。ユーザーへの判断点 3 つは一次資料と fragment の双方に明記されている（`README.md:170-174`、`worklog fragment:25`）。

## 総括

**R1・R2 の修正が必要。** とくに B の実装方式は段 4 裁定と食い違い、案 A の API 照合は必須条件から落ちている。走行中の Version 解放については指定した YCSB 構成で反例を確認しなかったが、それは Version 内 field 方式への裁定変更を意味しない。