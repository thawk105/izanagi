## 攻撃シナリオの結果

1. 正規 JSON の `verify_done` 1 件だけを `anomalies=1` へ変え、各系列 45 block record、campaign lock、WAL 90 件、tag 15/75、variant を維持する攻撃は、意図どおり実装されれば停止する。

   - 経路: `main():4260` → `run_formal():3970-3975` → legacy validator `:3560-3578` → lock `:3581` → `_verification_source_disclosure():3590` → WAL read `:3390-3395` → stage filter `:3405-3407` →現行 `:3408` への挿入予定述語。
   - 停止点は新設する `raise PreflightError("legacy-wal-verdict", ...)`。段 2 は最終的な新行番号を示していないため、正確に言えるのは起点版 `:3408` の挿入位置までである。
   - 例外は `:3390-3395` の `try` 外なので、`:3988` の `_write_reports` には到達しない。
   - 判定: refuted / nit
   - 影響: parse 可能な `verify_done` の値を崩した WAL は受理集合から除外され、report は発行されない。

2. ただし段 2 の「exact predicate」をそのまま貼ると `payload` が未定義である。現行ループには `payload` 代入がなく、`:3409` も `record.payload.get(...)` を直接使っている。

   - 判定: real / must-fix
   - 影響: `verify_done` を 1 件でも含む WAL は最初の record で `NameError` となり、現物 3 系列もすべて拒否される。

3. 止まらない変種を作れる。90 件すべてについて variant と tag を現物どおりにし、3 field だけを `0 / true / "serializable"` と自己申告した偽 WAL は述語を通る。`build_attempt_id`、`commits`、`aborts`、timestamp、生成主体は偽造できる。

   - 判定: real / must-fix
   - 影響: counts と公開 disclosure が同じなら成果物の値は同じままで、受理集合には verifier を実行していない偽 WAL が残る。

4. 別の止まらない変種として、WAL を読取例外になる JSON にする、WAL を欠落させる、または悪い `verify_done` を未終端 tail に置ける。例外は `:3393-3395` で `wal_read_error` と空 counts に変換され、collector は `:3596-3608` から正常 return する。未終端 tail は述語へ到達しない。

   - 判定: real / must-fix
   - 影響: core judgement と 135 block record は維持したまま report が発行され、変わるのは incomplete/error の disclosure だけである。

5. stage を見ない変種もある。悪い 3 field を `commit` などへ置けば `:3406-3407` で飛ぶ。90 件の偽 `verify_done` を正常値で別途用意すれば counts と tag も維持できる。

   - 判定: real / nit
   - 影響: 述語が狭めるのは reader が返した `stage == "verify_done"` の集合だけで、他 stage の payload は受理集合に影響しない。

## 所見

1. 述語自体は恒真ではない。既存 test fixture は `test_b10_backoff_shape_sweep.py:2761-2769` で 3 field のない正規 `verify_done` を作り、`:2776` から production disclosure へ到達させている。block validator と lock は WAL payload と独立なので、攻撃条件では production collector からも到達できる。

   - 判定: refuted / nit
   - 影響: `record.payload` を正しく参照すれば、parse 可能な不正 field は実際に新述語を発火させ、受理集合を狭める。

2. 「全 `verify_done`」という散文は実装より広い。実体は「`read_records_checked` が例外なく返した、終端済み record のうち stage が exact なもの」だけである。

   - 判定: real / must-fix
   - 影響: 欠落、読取例外、未終端 tail に含まれる判定は検査母集合から消え、report 発行可能性は維持される。

3. formal report の in-file production 経路に consumer 取り残しはない。CLI `main():4253-4274` の `--phase report` は `run_formal():3970-3998` の一経路だけで、collector `:3975`、disclosure `:3590`、集約 `:3605`、writer `:3988` を順に通る。source 内の `_collect_report_inputs`、`_verification_source_disclosure`、`_write_reports` の production call も各 1 箇所である。

   - 判定: refuted / nit
   - 影響: この CLI 経路では新述語を迂回して同じ legacy formal report を発行する分岐は増えない。

4. report を発行できる別 surface は存在する。

   - `--phase trial-cell`: `run_formal():4207-4232` → `_write_trial_report_create_only():2793-2860`。WAL 述語を通らないが、schema が `b10-backoff-shape-trial-report/v1` の non-formal report であり、legacy 3 系列 report ではない。
   - `_write_reports()` の直接呼出し: private helper だが、test 自身が `test_b10_backoff_shape_sweep.py:2718,2740,2834` から collector を通さず実ファイルを発行している。
   - `_write_trial_report_create_only()` の直接呼出しも可能。
   - 判定: real / nit
   - 影響: CLI formal report の受理集合は閉じる一方、直接 helper 呼出しで作る formal-shaped 成果物は WAL 述語に束縛されない。

5. 受理集合の向きは、`payload` 問題を直した意図上の実装では緩まない。既存 validator `:3560-3578` と lock `:3581` の後に新しい conjunction を追加するため、旧受理集合との積集合になる。unknown tag と unmapped variant にも `continue` 前で要求するので、むしろ従来より広く狭まる。

   - 判定: refuted / nit
   - 影響: 既存検査を迂回する新分岐はなく、parse 可能な WAL に限れば受理集合は狭まる方向だけである。

6. 不変条件への直接または間接の破壊はプラン上見当たらない。定数は `:125,183,241`、binding/validator は `:2863-3206` にあり、編集予定面外である。現物 `record_sha256` の sorted meta hash も source literal と一致した。

   - write-heavy: 45、`6cb14801e858cedd955d983267436585d75c713be48d79b50b0076fd99845b71`
   - balanced: 45、golden `8e5f0b48ba9e635e3d0e4e6c9c312c7436008dbe1a34f91a5763300920c37bad`
   - read-heavy: 45、golden `27195442abce632ffae7a7241abd3cd8e765fe63fb590a62a37d4166049400c8`
   - 判定: refuted / nit
   - 影響: 135 literal、2 個の指定 meta golden、凍結 block record、既存 legacy validator の値と述語は変わらず、最終受理集合だけが後段で狭まる。

## 親 brief への所見

1. 現物実測表は、測定した 3 campaign に限れば再現できた。各 WAL は 135 record、stage は `15/15/90/15`、`verify_done` は 15 variant 各 `legacy=1 / performance=5`、3 field 欠落 0、値は全 270 件で exact だった。read-heavy だけ全 90 payload に `proof_surfaces` があった。

   - 判定: refuted / nit
   - 影響: 現物 3 系列の正例適合性に関する親の数値は変わらない。

2. block record も各系列 45 file で、封筒 key は `record,record_sha256,schema_version`。内側 record の `anomalies/certified/verdict` は各 0/45、`correctness_certified` は各 45/45 だった。

   - 判定: refuted / nit
   - 影響: 3 field を既存 block-record digest の現行 preimage から直接検査できないという親の観測は維持される。

3. 親 brief の「現物 verifier 判定へ束縛される」「正しさ認定つき」という研究前進の一般化は成立しない。採用案が束縛するのは WAL に書かれた 3 値であり、その値の生成主体、verifier 実行、block record との attempt 対応ではない。段 2 自身も WAL に真正性がないと認めている。

   - 判定: real / must-fix
   - 影響: 放置すると成果物の説明だけが実装より強くなり、偽の正常値を持つ WAL も同じ report として受理される。

4. 完了判定の「3 field のいずれかを崩した WALでは必ず止まる」も母集合が未定義である。正しい範囲は、現物 3 file の終端済みで parse 可能な `stage=="verify_done"` 270 件であり、missing WAL、read error、truncated tail は含まれない。

   - 判定: real / must-fix
   - 影響: 無限定のままでは、実際には発行できる malformed/truncated 入力を不合格にしたと誤って報告する。

5. 「現物が全件正常だから将来も正例」という一般化はできない。今回確認したのは固定 3 campaign の現在の bytes だけであり、同じ campaign path の将来差替え、別系列、live campaign、trial campaignには及ばない。

   - 判定: real / nit
   - 影響: 親表の参照範囲を超えると、正例保証も受理集合の説明も根拠を失う。

## 変異の帰属評価

1. 候補 1、2、4、5、7、8、9、10、11 は、`payload` 参照を直すことを前提に帰属可能である。いずれも disclosure を直接呼ぶ fixture なので、block digest、lock、report completeness が先に赤になる余地はない。

   - 判定: refuted / nit
   - 影響: 指定 node の失敗は新述語の削除、型緩和、順序移動、例外握り潰し、stage 範囲変更へ直接帰属できる。

2. 候補 3 の「正数も許す条件」は変異が具体化されていない。例えば `== 0` を `>= 0` にするなら `[anomalies-nonzero]` に帰属できるが、現状は再現可能な一意の mutant ではない。

   - 判定: real / nit
   - 影響: mutation ledger の参照が曖昧になり、どの受理集合拡大を検出したか一意に説明できない。

3. 候補 6 の `[verdict-missing]` は、truthy 化の帰属証拠にならない。missing の `None` は元述語でも truthy 述語でも拒否されるため、その case は mutant を殺さない。部分一致も具体的演算次第で同じ問題がある。

   - 判定: real / must-fix
   - 影響: 放置すると test が赤にならない mutant を「述語が効いた証拠」と誤記し、受理集合の緩和を見逃す。

4. 候補 12 は、記載どおり 3 validator と lock を通過済み fixture に固定し、実 disclosure だけを残す場合に限り帰属可能である。既存 collector test `:2552-2651` は disclosure 自体を mock するので、この証拠にはならない。現物 production-evidence node も block、receipt、lock などの先行 gate があるため単独帰属には使えない。

   - 判定: real / must-fix
   - 影響: fixture 固定が欠けると collector bypass ではなく既存 legacy gate の失敗で赤になり、WAL 述語の consumer 束縛を証明できない。

## 総括

段 2 の意図した述語は恒真ではなく、`record.payload` を正しく参照すれば、parse 可能な `verify_done` の 3 field mutation を起点版 `:3408` の挿入位置で確実に止める。formal CLI 経路にも legacy report の別分岐はなく、既存受理集合を緩めない。

一方、プラン記載どおりでは `payload` が未定義で現物正例まで拒否する。また、正常値を自己申告した偽 WAL、読取例外、missing WAL、未終端 tail は止まらない。この実装を「現物 verifier 判定への束縛」や「任意の 3 field 破壊を必ず拒否」と説明するのは不正確である。

pytest は実行していない。実施したのは指定コードの静的経路検査と、現物 WAL・block record の `jq` 集計だけである。