### B1 「TPC-C を門の対象にした」という主張は、この計画の成果を超える

重大度: must-fix
根拠: `s1-brief.md:5`、`plan.md:45-49,77-83,95-99`、`orchestrator/campaign/pipeline.py:456-466,702-735`、`output/insights/2026-09-29/vhash-cicada-verifier/README.md:143-155`。
放置すると: repo 外起動器で得た小走行の結果が、campaign で受理される正しさの門を TPC-C に開いた実績として一次資料や台帳に載る。campaign は Delivery 入り mix を受け付けず、Cicada の上限 `indeterminate` も `certified` を要求する経路で拒否する。
推奨対処: 今回の達成を「TPC-C の点読み・書きについて、repo 外で trace と巡回検出を実測した」と限定する。campaign 接続、Cicada の証拠面、phantom 検査を別の裁定パッケージ候補として明記し、評価計画の「TPC-C は門の対象外」を解消済みとは書かない。

### B2 insert 限定 no-rts 変異では、insert 経路の検出力を帰属できない

重大度: must-fix
根拠: `plan.md:53-58,61`、`external/ccbench/cc/cicada/transaction.cc:533-536`、`external/ccbench/include/tpcc/tpcc_tx_neworder.hh:294-324`、`output/insights/2026-09-29/vhash-cicada-verifier/README.md:90-98`。
放置すると: INSERT を持つ NewOrder で Customer の read timestamp 更新を省き、その Customer 上の rw 辺から巡回が出た場合、insert 自体を壊したかのように正例へ計上する。INSERT は変異を有効にする条件にすぎず、壊れる操作は既存 record の read である。
推奨対処: この候補は「insert を含む取引での read timestamp 欠陥」として扱い、insert 経路の完了条件には数えない。insert または delete の意味を実際に壊し、その対象の `(table,key,version)` と cycle の辺が一致する変異を先に設計する。巡回を作れなければ検出力未確認として止める。

### B3 Delivery 限定変異も delete 経路への帰属が弱い

重大度: must-fix
根拠: `plan.md:53,58,61`、`external/ccbench/cc/cicada/transaction.cc:543-569`、`output/insights/2026-09-29/vhash-cicada-verifier/README.md:96-98`。
放置すると: DELETE を持つ取引で別 record の古い R を通した巡回を、delete の検出力として報告できてしまう。plan の table/key/版照合は「壊した read 再検査」への帰属にはなるが、DELETE 操作への帰属にはならない。
推奨対処: この候補は read 再検査の正例と呼ぶ。delete を完了条件に含めるなら、delete 対象と巡回の因果関係を事前登録した別候補が要る。`plan.md:59` の物理除去省略は plan 自身が認めるとおり巡回正例の代わりにならない。

### B4 生死確認の停止条件を先に固定する必要がある

重大度: should
根拠: `plan.md:19-33,61,77-83`、`external/ccbench/cc/cicada/transaction.cc:324-340`。
放置すると: stock の insert 後 abort に残存 tuple が生じ、存在違反や進行異常が出ても、cell を増やして「巡回 0」の負例を探す工程へ進みうる。約 1 node 時間という見積りも、再 build・再走の範囲を含まない。
推奨対処: 最初の stock 走行で非零 integrity、C 数不一致、異常終了、残存 tuple の兆候が出たら本走と変異探索を止めて原因を記録する。生死確認後に build 本数・cell 数・実時間から残予算を再計算し、2 node 時間未満を確認してから投入する。

### B5 TRACE=0 の追加比較は対象を保ち、証拠の主張を分ける

重大度: should
根拠: `request-md_17.txt:9-14`、`plan.md:65-73`、`output/insights/2026-09-29/vhash-cicada-verifier/README.md:114-124`、`external/ccbench/cc/cicada/CMakeLists.txt:1-14`。
放置すると: tpcc だけの比較では、前段で未実施と明記された bomb / sbomb の TU が未検査のままになる。一方、C1' を含む比較を既存 patch 単体の保証と混同すると、共有 header の差分を見落とす。
推奨対処: plan の二系列を維持する。pin C 対既存 patch は tpcc・bomb・sbomb、pin C 対 C1'＋両 patch は tpcc とし、各系列の対象 TU と結果を別々に記す。前処理と `nm` / `strings` は診断、命令列比較を合否根拠にする。

## 総括

plan はそのまま採用しない。最大の修正点は、repo 外の TPC-C 実走を campaign の門の成立と同一視しないこと、そして read 検査を条件付きで壊した変異を insert/delete の検出力に数えないことである。重ね patch は md_14 の既存 patch bytes と YCSB v2 を守る実務上の理由があり、C1' への依存と pin 前進後の再適用確認を明記するなら採用できる。fixture の追加や delete 物理除去の第三候補は、この wave の巡回正例には不要。まず stock の生死確認と実費を測り、帰属可能な変異を確保したうえで本走を固定する。phantom、`certified` 上限、campaign 接続は未対応として一次資料に残し、研究計画の拡張に必要な別裁定として提示する。