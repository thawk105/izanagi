## 所見

### A-01 / blocker — S2 は producer ではない

根拠: 親 brief は raw 受領証を「書く」とするが `s1-brief.md:64-67`、プランは永続 writer を実装せず純粋 assembler に縮小している `s2-plan.md:35-52,89-110`。D264 も部品だけを producer 実装済みと扱う半実装を禁じる `docs/decisions.md:12194-12204`。  
成果物影響: raw receipt の実体は引き続き 0 件で、D481 の backlog と D162 発火条件は進まないのに、S2 完了という誤った参照だけが残る。

### A-02 / blocker — attempt 全単射が caller 選択集合との自己比較になる

根拠: 公開 dataclass の snapshot を caller から受け、そこから `attempts` を注入した後、同じ snapshot と全単射を検査する `s2-plan.md:7-20,40-44`。canonical registry path、外部固定 tip、snapshot の真正性が無い。`atomic_publish.publish_bytes` も任意 `Path` を受けるだけで RF の canonical namespace を定めない `orchestrator/qualification/atomic_publish.py:24-31`。  
成果物影響: 失敗 attempt を snapshot 作成前に intent ごと落とせば registry と receipt は一致したままになり、不完全な試行系列が将来の RF 受理集合へ入る。

### A-03 / blocker — 親系列 ID は registry と受領証で結合されていない

根拠: snapshot は `series_id` と `parent_series_id` を持つが `s2-plan.md:8`、assembler が snapshot から注入すると明記するのは `attempts` だけ `s2-plan.md:40-44`。root の両 ID は caller 入力のままで、schema は hex64 型しか検査しない `receipt-schema-v1.json:1227-1255`。  
成果物影響: receipt の `parent_series_id` だけを新しい値に替えて累積有意水準の系列をリセットでき、D229 の第 2 必須変異が一側改ざんでも生存する。

### A-04 / blocker — anomaly の clean 申告を producer 自身が決められる

根拠: `close_attempt` は caller から `reason_code` を受ける `s2-plan.md:15-18`。schema は `completed` を正規値として受理し、raw correctness の再計算は行わない。record-items は `reason_code` を受理入力に使うことを明示的に禁じる `record-items-v2.md:784-799`。プラン自身も kill 不能を認める `s2-plan.md:149-150,172`。  
成果物影響: anomaly を `completed` として registry と receipt の両方へ整合して書けば、独立 validator なしでは候補の終端 reject が消え、将来の受理集合が広がる。

### A-05 / blocker — D229 の 3 変異は実際には全件完全 kill 不能

根拠: D229 は 3 件すべてを必須 kill とする `docs/decisions.md:10767-10772`。一方、プランは失敗投入の intent ごとの除去、整合した lineage 改ざん、anomaly 再分類をそれぞれ現 scope では検出不能と認める `s2-plan.md:143-150,170-172`。それにもかかわらず総括は「後二件」だけが不可能と誤記する `s2-plan.md:183`。  
成果物影響: mutation matrix が 3 件を KILLED と記録できず、親 brief の P4 と S1 の成果物影響 `s1-brief.md:60-63,89-90` が成立しない。

### A-06 / must-fix — `dry` は隔離札にならない

根拠: schema は空の `attempts` と `allocations` を許す `receipt-schema-v1.json:1274-1300`。さらに `declared_use_class` は受理入力にしてはならない `record-items-v2.md:784-799`。したがって `dry` は semantic acceptance から隔離する安全札には使えない。プランは P2 を正しく反証したが、production module に `prepare_rf_receipt_bytes` という名称を残す `s2-plan.md:35-45`。  
成果物影響: qsub の直接迂回は現 plan には無いが、空 attempt の pilot 形状が「受領証」として永続化または参照されると、D481 の発火証拠を満たしたという誤った参照が生じる。

### A-07 / must-fix — closed schema 自体は発火するが、テスト計画は別理由による偽緑を防いでいない

根拠: 静的実測で、12 field を持つ schema-valid attempt に `validator_result: "passed"` だけを追加すると、`additionalProperties` ちょうど 1 件で拒否された。根拠 schema は `receipt-schema-v1.json:1092-1218`。一方、プランは基底 fixture の合格確認、拒否 keyword、instance path、エラー件数を固定していない `s2-plan.md:58-68`。F150 の既知失敗型そのもの `docs/failures.md:4530-4548`。  
成果物影響: 基底 fixture が別制約で既に赤なら closed-schema 分岐を削除してもテストが緑になり、未知 field を許す受理拡大を見逃す。

具体的な拒否正例は、`reason_code="completed"`、`cluster_slot_or_null=null`、`allocation_id="x"`、有効な `intent_ref` と `qsub_result.raw`、空の `environment_observations`、他の必須 field を null または有効値にした attempt である。この基底は schema-valid で、`validator_result="passed"` の追加だけが拒否理由になった。pytest は実行していない。

### A-08 / must-fix — DW-G01 probe の依存順が循環している

根拠: 順序は probe より後に S1 とする `s2-plan.md:70` が、probe 入力には S1 registry snapshot が必要 `s2-plan.md:116-122`。さらに未実装の `PreregBinding` と実 allocation を緑条件に含め、現状は赤と既知である `s2-plan.md:130-137`。  
成果物影響: probe は既知の欠落で常に赤になるか、偽 snapshot を渡して本物でない緑を作るため、producer の生死について新しい証拠を一つも生成しない。

### A-09 / must-fix — M4 の「floor 文字列 0 件だから依存なし」は成立しない

根拠: 新規 module を置く `orchestrator.qualification` は package import 時に `contract` を import する `orchestrator/qualification/__init__.py:7-18`。同 contract は calibrator を importし `:18`、floor 由来の threshold と判定を持つ `:145,207-215,332-353`。プラン自身も canonical JSON の接続先として contract を挙げる `s2-plan.md:22`。D496 も変動係数を明示的に維持する `docs/decisions.md:20625-20626`。  
成果物影響: RF の数値受理が直ちに変わる証拠は無いが、参照集合には別名の floor 系依存が残るため、「D496 関門は発火しない」という変更面裁定を根拠なく固定する。

## 親 brief への反証

- M1 は確認できた。`s8b_floor_stats.py:412-416,682-694` は attempt registry を保証しない。
- M2 は直接再利用不能という範囲では確認できた。ただし「一切再利用可能でない」は、原子公開などの primitive まで否定する過剰一般化である。
- M3 の台帳は公開 API だが中立部品ではない。T-126 固有 schema、lineage、FSM、capability に束縛される `attempt_ledger.py:169-207,312-373`。
- M4 は反証済み。2 blob の文字列検索は import graph、別名の CV、数値 source を調べていない。
- M5 は schema の field 名と enum については支持される。これを合格宣言として読む経路が無いことは、producer 側テストだけでは証明できない。
- M6 の 2 digest は実測一致した。ただし pin 閉包は不完全である。`approved_blobs` は 6 role だが `target_core` を含む固定三つ組は 7 件 `test_t139_approval_payload.py:120-125`。brief の不変条件 `s1-brief.md:48-49` は 7 対象を「6 blob」と数えている。また role-keyed parser `approval_payload.py:29-47,166-171` は path 検索に現れない。
- M7 は支持される。そしてプランも永続 writer を作らないため、実装被覆 0 の主要部分は変わらない。
- M8 は静的環境で `jsonschema 3.2.0` と確認した。ただし pytest と probe は未実走である。
- M9 は「非空 attempt は qsub fact に束縛される」までなら正しい。配列自体に `minItems` が無いため、空集合では制約が空振りする点を親 brief は落としている。
- P1 は部分採用まで。新規 RF FSM は妥当だが、canonical namespace と producer 外の intent authority が無い現在案は authoritative registry にならない。
- P2 は反証。`dry` は qsub fact を免除せず、隔離札にもならない。
- P3 は未検証で、しかも依存循環と既知欠落により有効な生死実験になっていない。
- P4 は反証。現 scope では 3 変異すべて完全 kill 不能である。
- P5 は `hostname=pegasus02` まで確認した。受入、pytest、probe は走らせておらず、緑の実測は無い。

## scope 外だが real な所見

- D162 の本当の負検査は consumer が `declared_use_class`、`reason_code`、`qsub_result.returncode` などを受理入力に使わないことの検査である `record-items-v2.md:784-799`。producer wave の closed-schema test では代替できない。
- 失敗投入の完全性には、producer が選べない durable intent authority、PBS driver との qsub 前結線、producer 外 collector が必要である。`record-items-v2.md:470-476,801-817`。
- 親系列の alpha reset を閉じるには canonical family root から measurement head までの全履歴 validator が必要である `record-items-v2.md:652-667`。
- anomaly の clean 化を閉じるには raw correctness を再実行する独立 semantic validator が必要である。schema engine はその代替ではない `record-items-v2.md:739-740,825-827`。
- 永続 producer には approval manifest resolver、`PreregBinding`、唯一の writer namespace、正式 conformance vectors の pin が必要である `record-items-v2.md:719-743`。
- D229 の必須 kill と、D282 が明記する「台帳外投入は見えない」という保証境界の関係を裁定パッケージへ返すべきである。現 wave が前者を達成済みと記録することはできない。

## 総括

NO-GO。closed schema には実際に拒否される正例があり、その分岐自体は恒真ではない。  
しかし S2 は producer ではなく、S1 の全単射は caller が選んだ snapshot との自己比較に留まる。  
D229 の 3 必須変異は全件完全 kill 不能で、プラン自身の risk 記載と総括も矛盾している。  
段 4 では、成果物を非権威な registry 基盤だけへ縮小して T-338 未完を明記するか、authority、binding、writer、validator を含む別 scope を裁定する必要がある。  
pytest と probe は未実走であり、緑の検査結果は無い。