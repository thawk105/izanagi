## 所見

1. **should・成立 — C6 の変異は結合固有の確認に対して多い。** H-set は共有 `tpcc.hh` の setter を一度消し、C2' の silo と mocc がともに v2 へ落ちることを示すため、結合確認として有効。一方、H-count-D/M と H-line は両側で実施済みの変異の再演であり、S-table・M-type・S-line・M-line も既存の検出層を再確認する比重が大きい。特に各 `#line` 変異の前処理は21 entryを再走する。根拠: `s2-plan.md:29-40`、単位1・2 `README.md:85-100`、単位3 `README.md:72-86`、C2' `include/tpcc.hh:60-63,118-124`。**代替案:** H-set を結合固有の主変異として残し、protocol 側を残すなら片側の代表例1件に絞る。削った変異に対応する selftest 負例も作らない。

2. **should・成立 — 「非影響側 PASS」は強い結合証拠にはならず、判定を不安定にする。** S-table と M-type の変更先は別々の `transaction.cc` で、CMake は silo と mocc を別 target として作る。同じ変異 build 木で他方を build・走行しても、他方の emitter はその変更を取り込まない。1秒の別走行で偶発的に赤になれば、変異の検出力とは無関係に同じ row が失敗する。根拠: `s2-plan.md:32-38`、C2' `cc/silo/CMakeLists.txt:1-13`・`cc/mocc/CMakeLists.txt:1-10`、`probe/run_probe.py:442-469`。**代替案:** 非影響側の結合時の健全性は C4・C5 の B0 で判定する。protocol 変異を残す場合、他方の再 build・再走行を kill 条件から外す。

3. **should・成立 — P2・P3 の「結合」の射程を明記する必要がある。** C2' の4 target は同じ source tree と共有 header から作られるが、silo と mocc が一つの binary に入る構成ではない。`tpcc_tx_type_context()` は inline 関数内の thread-local 値で、各 binary 内の workload TU と transaction TU の受け渡しを C4 が実走で確かめる。二つの protocol 間で同じ context が衝突する経路は、この構成にはない。根拠: C2' `include/trace.hh:122-136`・`include/tpcc.hh:59-63`・`cc/silo/transaction.cc:601-606,742-743`・`cc/mocc/transaction.cc:1159-1165,1317-1318`、両 `CMakeLists.txt:1-13`、`s2-plan.md:10-14`。**代替案:** 結合確認の命題を「C2' の単一 source tree から作る各 protocol binary が、共有 header と各 emitter を正しく使う」と記す。両 protocol 入り binary の追加検査は要らない。

4. **should・成立 — 計算の再投入には累積上限の判断が要る。** 191秒と206秒から1 job 8〜15分という推測は妥当な出発点だが、両側 build・変異走行が増えるため実測値とは扱えない。60分上限の job を2本使い、約0.25 node 時間の受入を足す経路は2 node 時間を超え得る。plan は2本目の前に再見積りするとしており、その条件を守れば現時点の投入を止める理由にはならない。根拠: `s2-plan.md:19-21,40`、単位1・2 `README.md:64`、単位3 `README.md:56`、`D2212.md:45-47`。**代替案:** 失敗後は消費済み node 時間と次 job・受入の上限を合算し、2 node 時間以上の見込みなら投入前にユーザーへ確認する。

5. **nit・成立 — C1 の include 負例は前例の再演である。** 前例は既に TPC-C 9 entry すべてで include 活性の差を検出し、同じ負例が完全展開でも検出されたと記録している。C2' の header blob は C1' と同一なので、新しい検出層を示す負例ではない。根拠: `s2-plan.md:11`、単位1・2 `README.md:76-80`、`probe/run_probe.py:591-609`。**代替案:** C1 の21 entry の本比較は残し、負例の再走は省くか、probe 改修の小さな自己試験として扱う。

6. **nit・不成立 — anchor が C2' に存在しないという攻撃。** 指定箇所を `git show 40a7f4ac...:<path>` で照合した。H-set、H-count、H-line、S-table の呼出し、M-type の最終引数、S-line、M-line は、挙げられた行に存在する。出現1回の逐語確認を spec 確定時にも行う plan は妥当。根拠: C2' `include/tpcc.hh:61,63,118-124`・`cc/silo/transaction.cc:628-632,692`・`cc/mocc/transaction.cc:1162-1165,1283`、`s2-plan.md:25-34`。**代替案:** 予定どおり置換直前の出現数 assert を維持する。

7. **nit・不成立 — 前例の重要な fix が落ちているという攻撃。** `export-ignore` 対策と tree/blob 照合は C0 に残る。R 行0件は既存 `v3check.check()` が拒否し、H-count-M には marker・1000 C 以上・C/E/commit 数の条件がある。4走行の生 trace 保持と、残す変異の verdict に対応した selftest は、結果を後から調べるために妥当な範囲である。根拠: `s2-plan.md:9,15,19,30,38`、`probe/run_probe.py:218-311,754-777`、`probe/v3check.py:238-248`、単位1・2 `README.md:106-107`。**代替案:** C6 を縮めた分だけ selftest を縮め、これらの既存検査は維持する。

8. **nit・不成立 — 親 brief の branch・blob・P6・P7 が誤りという攻撃。** local branch と C→C1'→C3→C2' の親子関係、C..C2' の4 file 差分を照合できた。P6 は推測と再見積り条件を付けており、P7 の「superproject の実装面差分ゼロ」は job dir の probe と記録を成果物にする範囲と整合する。根拠: `s1-brief.md:5-8,14-20`、`s2-plan.md:3,21`、C2' `cc/silo/transaction.cc:601-606`・`cc/mocc/transaction.cc:1159-1165`。**代替案:** 実測前の所要と合格を確定値として記さない。

## 総括

- **成立した攻撃:** C6 は単位検査の再演が多く、非影響側 PASS を同じ変異の kill 条件にする価値は低い。再投入時には累積 node 時間を確認する。
- **不成立の攻撃:** 両 protocol が同一 binary 内で衝突する構成、C2' の anchor 欠落、`export-ignore`・R 行0件・M2 発火確認の脱落は確認できなかった。
- **削るべきもの:** H-count-D/M、H-line、S-line、M-line の再演。protocol 変異と対応 selftest も代表例まで縮められる。
- **足すべきもの:** repo の gate や検査ではなく、結合確認が「同一 source tree の別 binary」を対象とするという結果文の限定だけ。C0〜C5 の本比較には実質的な取り漏れを見つけなかった。