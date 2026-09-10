## 総括

最も重い所見は、凍結検査が preflight 時点だけで、runner と catalog 生成器がその直後に旧凍結物へ書けることである。  
canonical 化の通常入力は多重度・深さ・join・型を保存するが、実応答は前段の `json.loads` で duplicate member を失い、未知 join を正常値で上書きできる。  
新 epoch の amendment/catalog は新成果物になるものの、旧 HTTP 応答を新 ID へ再包装する anti-replay は閉じていない。  
凍結集合拡張の commit・file 数・無差分は正しいが、現実装のままでは単体テスト約18秒が線形推定約318秒になる。  
active な parametrized node ID の波及はプラン記載の2 source＋3 ledger keyで合っている。pytest は実走していない。

## 所見

### 1. preflight 後に旧凍結物を書き換えられる

- **主張:** §5 の凍結集合拡張は、旧 bytes の変更を事前検出するだけで、変更そのものを防がない。
- **反例となる具体入力または file:line:** `tools/run_axis1_search.py:42,127-176` は任意の `--bundle` を受け、凍結検査通過後にそのまま runner へ渡す。旧 `output/insights/2026-08-29_t2033-axis1-retake/bundle` を指定すると、`runner.py:1587-1593` が同 directory を採用し、HTTP より前の `runner.py:1740-1746` で新 WAL を追記する。さらに `catalog.py:877-884` の生成器は任意の `--output` を `write_bytes()` で上書きできるため、旧 catalog path を渡せば直接破壊する。
- **帰結:** brief:29-30 の「1 byte も変えない」と、プラン:195 の運用宣言だけでは不十分。旧 frozen prefix を bundle/output target として拒否する create-only・path-disjoint gateが必要である。
- **確度:** 静的推論のみ。

### 2. duplicate JSON member により未知 join が正常形へ落ちる

- **主張:** canonical helper の前に行われる JSON parse が非単射であり、意味の異なる raw `oqo` が同一 canonical 入力になる。
- **反例となる具体入力または file:line:** `A={"column_id":"x","value":"v"}` とすると、正常形  
  `{"join":"or","filters":[A]}`  
  と不正形  
  `{"join":"xor","join":"or","filters":[A]}`  
  は Python の `json.loads` でともに `{"join":"or","filters":[A]}` になった。実応答は `parsers.py:205-212,229-279`、live 比較は `runner.py:446-451`、offline 比較は `validator.py:830-835` で同じ last-member-wins parseを使う。
- **帰結:** プラン:78-92 の未知 join fail-closed を raw response が迂回する。`object_pairs_hook` 等で重複 member を parse error にし、raw body を使う live/offline 両経路の負例が必要である。
- **確度:** 現物で確認した。

### 3. 新 epoch の証拠は依然として内部自己整合だけで再包装できる

- **主張:** 新 amendment/catalog が commit に入るため「新成果物ゼロ」という完全に同じ反例ではないが、P1-d の「旧証拠を算入しない」は機械的に成立していない。
- **反例となる具体入力または file:line:** 旧 bundle の raw gzip を変更せず新 bundleへコピーし、page/ledger の ID・epoch・`registration_commit` を新値へ張り替え、manifest digestを再生成する。query 本体は同じなので request URL は変わらず、旧 OpenAlex raw は新 canonical 比較を通る。`validator.py:1227-1263` は catalog digestと再導出 request、`:1265-1345` は raw内容を検証するが、rawが registration commit後に取得された外部事実は検証しない。schema の `issued_at` も `axis1_search_page_evidence.schema.json:224-260` の自己申告 date-timeである。
- **帰結:** 旧183完走 leafを新 epoch の leaf evidenceとして再包装できる。T-2090 と同型の anti-replay 問題が残るため、外部 receipt・nonce・append-only登録事実などの束縛方式が必要である。
- **確度:** 静的推論のみ。

### 4. 条件1テストは要求された変異をすべて殺さない

- **主張:** 擬似コードどおりなら `[A,A,B]` 対 `[A,B]`、join差、型差、欠落/nullは区別される。しかしテスト計画には同一 join の flatten と空文字列の反例がない。
- **反例となる具体入力または file:line:** プラン:270 は `or(A,and(B,C))` 対 `or(A,B,C)` だけである。  
  `or(A,or(B,C))` 対 `or(A,B,C)`  
  を同一化する「同じ join のときだけ flatten」変異はこの負例を通過する。さらにプラン:274 は欠落対 `null` だけで、`operator` 欠落対 `operator:""` を falsy coalesceする変異を殺さない。整列キーについても、値の異なる2 filterが明示的に異なるキーになるという検査がない。
- **帰結:** group境界保存と欠落/null/空文字列の三者区別に未被覆が残る。これらは `evaluate_page()` の条件1を直接見るテストに足すべきである。他条件が先に赤になる問題は、現テスト形式では起きない。
- **確度:** 静的推論のみ。

### 5. 2,258 file の凍結検査は線形拡張できない

- **主張:** commit と無差分は正しいが、1 fileごとに subprocessを起動する現実装のまま拡張すると開発・registration双方を著しく遅くする。
- **反例となる具体入力または file:line:** `validator.py:75-113,728-737` は各 fileに `git show` subprocessを1回起動し、bytesを二重にSHA-256する。テスト `test_axis1_search_runner.py:838-873` は復元時にも1回、受理・変異拒否でさらに2回、合計ほぼ `3N` blob取得を行う。現行128 file版は `acceptance_duration_ledger.json:135` で18.0秒。単純線形では2,258 file版は約318秒、単一 registrationは約106秒（現行約6秒、約100秒増）となる。263 leafを別CLI起動するなら増分だけで約7.3時間になる。
- **帰結:** batch `git cat-file --batch`、単一 `git diff`、または基準manifestとの一括比較へ変える必要がある。凍結保護自体はscope内で、旧 waveも commit `5da991745…` で旧128 pathに同じ保護を導入しており先例はあるが、実装方式の線形拡張は採れない。
- **確度:** 現物で確認した（将来値は18.0秒からの線形推定）。

### 6. 凍結集合の数値は一部だけ正しい

- **主張:** `da304403836591d484bf533313392fcdeae6d941`、2,258 file、無差分という結論は正しいが、98.5 MBは全凍結集合の大きさではない。
- **反例となる具体入力または file:line:** `da304403…` は実在する。既存3 pathは `164e2c355…da304403` で無差分、全7 pathは `da304403…HEAD(82a259c0)` で無差分。追加4 pathは2,130 files / 99,925,266 bytes、既存3 path込みでは2,258 files / 102,738,024 bytes（97.98 MiB）。旧 T-2033 directory単体は2,127 files / 98,585,751 bytes、旧記録のbundle単体は2,124 files / 98,570,351 bytes。
- **帰結:** 「2,258 files / 98.5 MB」を一組の値として扱うと対象量を約4.2 MB過小評価する。性能見積りは102,738,024 bytesと2,258 subprocess単位で行うべきである。
- **確度:** 現物で確認した。

### 7. schema更新後は旧 bundleをHEADの検査器で検証できない

- **主張:** epoch constと既定catalogを一括更新すると、凍結bytesは保たれても旧 bundleの現行検証経路が失われる。
- **反例となる具体入力または file:line:** 旧 bundleは `AX1-20260829-E1` を持つが、プラン:124-139 は3 schemaのconstと `validator.py:980-990` の既定catalogを新値へ置換する。旧 bundleを現行 schemaへ通すテストは実際に存在しない。
- **帰結:** 旧 commitをcheckoutすれば監査できるが、HEADからは失敗する。これを意図したversioned auditとするか、epoch別schema/catalog dispatchを残すか明記が必要である。「既存被覆は純増」という一般化は成立しない。
- **確度:** 現物で確認した。

### 8. parametrized node ID のactive波及は合っているが、歴史pinは他にもある

- **主張:** 変更必須のactive箇所はプラン記載どおりだが、旧node IDを持つ歴史的mutation証拠も存在する。
- **反例となる具体入力または file:line:** activeは `test_mutation_fanout_contract.py:587-594`、`test_mutation_harness.py:1051-1076`、`acceptance_duration_ledger.json:143-145` の計5箇所。加えて `output/insights/2026-09-02_t2123-mutation-node-normalize/` の `spec-real1.json`、`spec-probe2.json`、`real1.json`、`probe2.json`、`verbatim/s2-plan.md` が旧node IDを持つ。これらは歴史証拠なので更新してはならない。内容走査型では `test_acceptance_schedule_order.py:680-716` がcollectionとledger coverageを動的比較するが、完全一致pinではなく90%閾値である。
- **帰結:** active 3 ledger keyは置換し、`nodeid_count=19519`を維持する。stale-literal検査では歴史artifactを明示allowlistし、機械置換しない。
- **確度:** 現物で確認した。

## 親 brief の誤り

- A4は `catalog.py:749-752` の `supersedes`、A5はcatalog schema `:33,450`、A7はpage schema `:105`、A9はrunner fallback・CLI・mutation node・duration ledgerを漏らしている。プラン:221-228の訂正は正しい。
- (P1-c) の「新 epoch の bundle は新規」はコード上の保証ではない。quota状態がbundle外に無いことは確認したが、任意の旧bundleを渡せる。プラン:292自身も条件付きへ訂正している。
- (P1-d) は規範として正しいが、旧raw証拠の新epoch再包装を検査器が拒否しないため、実装上の前提としては誤り。
- 「既存被覆は純増」は条件1の直接unit testに限れば概ね正しいが、wave全体では旧bundleの現行schema検証を失うため過大な一般化である。
- 92頁という実測資料は内部不整合を持つ。`openalex-oqo-ordering.json:2-5` は92/92だが、同`:389` は「78頁」と記す。また収録物は集計値と1 sampleだけで、削除済みsource runから92件を再導出できない。観測範囲外への一般化はできない。
- 一方、A1/A2/A3/A6/A8の行アンカー、runner/validatorの3 call site、`blocked_on_ruling`分岐、`_canonical_query_object()`がlist順を扱わない点、183 leaf・36,179 ID・旧bundle約98.5 MB、D1207による全枝再実行、旧bundleを現行schemaで検証するtestが無いという主張は現物と一致した。
- (P1-a) の3索引全ID新規化は、D1207の「全枝の再実行」と単一epoch catalog契約から支持される。OpenAlexだけ新epochにするにはmixed-epoch schemaへ契約を再改訂する必要がある。

## 裁定候補

- **新epoch証拠のanti-replay束縛:** registration commit後に取得されたことを何へ束縛するか。外部receipt・nonce・append-only登録のいずれも現行契約にないため、継続取得前に方式の裁定が必要。
- **軸1の継続取得:** 明示的scope外。上の凍結target拒否とanti-replayを閉じ、新規・不存在bundle rootを機械的に要求してからT-2090で実行する。
- **無償枠gateの恒久修理:** `reset_seconds`を失効判定に使わない問題は実在するが明示的scope外。fresh bundleは初回だけ回避するにすぎない。
- **旧bundleの監査方式:** HEADがepoch別schemaをdispatchするか、旧commit checkoutを唯一の監査手順とするかを決める必要がある。仮想リスク一般化は本件へ追加しない。