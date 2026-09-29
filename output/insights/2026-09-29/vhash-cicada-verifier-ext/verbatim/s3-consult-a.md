### A1 変異の帰属が insert / delete の欠陥を証明しない

重大度: **must-fix**。根拠: `plan.md:53-61`、`external/ccbench/cc/cicada/transaction.cc:533-569`。候補が変えるのは共通の read timestamp 更新・read set 再検査であり、INSERT / DELETE は発火条件にすぎない。提案された witness 照合も、巡回辺に I / D が関与することを要求していない。放置すると、従来の点読み・更新の巡回を「挿入・削除を壊して検出した正例」と台帳に記録しうる。推奨対処: I / D 自体の単一 site 変異を用意するか、完了条件を変更する裁定を受ける。前者を採るなら、変異した `(表, key, 版)` と巡回の辺を照合し、存在履歴違反だけの検出を除外する。

### A2 中途失敗した insert は trace に無い存在を木に残しうる

重大度: **must-fix**。根拠: `plan.md:23-24,33`、`external/ccbench/cc/cicada/transaction.cc:317-340,745-756`、`external/ccbench/cc/cicada/include/version.hh:46-52`。木への挿入後、`node_map_` 不一致で `write_set_` 登録前に戻ると、abort の除去対象から漏れ、pending 版を持つ tuple が残る。放置すると、後続 insert の失敗や読みの停止が trace に現れず、存在契約と stock 小走行の解釈が誤る。推奨対処: この経路の再現と cleanup の確認を stock 合格の前提に置く。発火した場合は実装欠陥として扱い、trace の存在検査を緩めない。

### A3 不在読みと scan の範囲は巡回グラフに入らない

重大度: **must-fix**。根拠: `plan.md:27-31,93-99`、`external/ccbench/cc/cicada/transaction.cc:121-126,170-178,421-456,595-602`。不在・deleted 版の読みには R がなく、scan は返した tuple の R だけを出す。放置すると、空の scan や範囲への insert が作る依存を落としたまま「TPC-C の正しさの門を掛けた」と一般化する。推奨対処: 今回の合格主張を**記録された点読みと書きからの巡回検出**に限定する。phantom を含む TPC-C の門や campaign 受理は、S/Q と初期 key 集合の対応を含む別裁定候補にする。

### A4 campaign の受理経路は今回の成果物につながらない

重大度: **must-fix**。根拠: `s1-brief.md:5,30`、`plan.md:75-89`、前段 `output/insights/2026-09-29/vhash-cicada-verifier/README.md:143-155`、`orchestrator/campaign/pipeline.py:454-466`。実走は repo 外起動器による検査で、campaign は Delivery を含む TPC-C mix を trace 前に拒否し、Cicada の証拠面も unavailable のままである。放置すると、一次資料の「門」を評価 campaign が受理できる門と誤読する。推奨対処: 成果を独立した診断走行として明記する。campaign への trace 供給・allowlist・証拠面は所有範囲外の裁定パッケージとして分ける。

### A5 「insert / delete は TPC-C だけ」という親の実測は誤り

重大度: **should**。根拠: `s1-brief.md:8`、`external/ccbench/include/bomb.hh:620,762-806,843`。BOMB にも insert と delete がある。放置すると、対応範囲表と未検証範囲が実際より広く読める。推奨対処: 「今回検査する YCSB と TPC-C の比較では」と限定し、BOMB / SBOMB は TRACE=0 の命令列比較のみ実施した対象として記す。

### A6 TPC-C の read-only 早期 return は提示された経路では使われない

重大度: **should**。根拠: `plan.md:11-15`、`external/ccbench/cc/cicada/include/transaction.hh:55`、`external/ccbench/include/tpcc.hh:59-126`、`external/ccbench/include/ycsb.hh:106`。TPC-C は `is_ronly_` を設定せず、OrderStatus / StockLevel も通常の `writePhase()` を通る。放置すると、read-only hook とその commit 計数を TPC-C で実証したかのような一次資料になる。推奨対処: その経路は YCSB 用の互換経路と記し、TPC-C の C 行数は実際の通常 commit 経路で照合する。

### A7 読み版の不一致診断が負例の受入条件から抜けている

重大度: **should**。根拠: `plan.md:80-81`、`patches/instr-cicada-trace.patch:80-88`、前段 `output/insights/2026-09-29/vhash-cicada-verifier/README.md:46-49,74-82`。計装は取得時の wts と commit 時の版 object の wts の不一致を別計数するが、plan の「integrity 数値項目 0」には含まれない。放置すると、版 object の再利用が疑われる stock run を健全な負例に算入しうる。推奨対処: `CICADA_TRACE_READ_WTS_MISMATCH n=0` を stock の受入条件に明記し、非ゼロ時は raw trace と事象を保留して原因を調べる。

## 総括

plan は**現状のままでは採用しない**。特に、read validation を取引種別で絞った変異を insert / delete の正例に数える帰属規則を直す必要がある。中途失敗 insert の残骸も、stock 合格前に確認が要る。TPC-C 小走行の「巡回 0」は記録された依存に限り、phantom と campaign 受理を含む正しさ認定へ広げない。BOMB の操作範囲、TPC-C の read-only 経路、読み版の不一致条件を訂正すれば、独立起動器による限定的な検査計画として採用できる。TRACE=0 の比較対象と C1' を含む独立比較は妥当な設計だが、命令列一致そのものは親の実測待ちである。