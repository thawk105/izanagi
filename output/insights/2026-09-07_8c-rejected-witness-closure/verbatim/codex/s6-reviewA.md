## M1-M10 対応表

| ID | 判定 | 根拠 |
|---|---|---|
| M1 | partial | `{}` 自体は `orchestrator/campaign/reflux_formal_consumer.py:835-887,966` で拒否される。しかし production では生成不能な型・関係を持つ anomaly がまだ通る。具体例は must-fix 1。 |
| M2 | closed | 実 production の dirty cycle は `integrity.clean=False` なので `reflux_formal_consumer.py:950-954` で落ちる。ただし `clean=True` と dirty counter の矛盾は別の穴として残る。 |
| M3 | closed | `verdict`、`serializable is False`、`certified is False` を独立に検査する。`reflux_formal_consumer.py:942-949`。 |
| M4 | closed | counter は exact int、`anomaly_count == len(anomalies)`、`total_cycles == anomaly_count` を順に検査する。`reflux_formal_consumer.py:955-965`。 |
| M5 | closed | 整列・重複排除はなく、anomaly の canonical JSON を直接 hash する。`reflux_formal_consumer.py:890-894,967-970`。 |
| M6 | closed | reason と verdict は定数との独立した 2 連言になった。`reflux_formal_consumer.py:937-947`。対応負例も `test_reflux_formal_consumer.py:1018-1025` で独立している。 |
| M7 | partial | 大半の負例は組み直されたが、boolean counter 負例が 2 連言を同時に壊す。`test_reflux_formal_consumer.py:1055-1057`。 |
| M8 | closed | full closure ではなく WAL 側だけと裁定内で明記した。`s4-adjudication.md:34,59-72`。commit 表題も「実在 field へ合わせた」に留まる。 |
| M9 | closed | 非単調な schema migration と訂正済み。`s4-adjudication.md:35,233-245`。 |
| M10 | closed | certified 選択・ledger event・reason は不変、fixture digest と receipt/reference が変わると訂正済み。`s4-adjudication.md:36,233-245`、`reflux_formal_consumer.py:1149-1175`。 |

段 3 の具体入力を判定順で追うと次になる。

- レンズ A の元の `anomalies=[{}]` 入力は `serializable=true` なので、まず `reflux_formal_consumer.py:948` で落ちる。そこを `False`、`certified=False`、clean integrity に直した単一理由版は `:966` の `_valid_witness_anomaly({})` で落ちる。
- dirty production cycle は reason、verdict、serializable、certified を通った後、`:951-954` の `integrity.clean is True` で落ちる。
- 元の counter 偽装例は必要 field 欠落により `:948` で先に落ちる。その他を正例にし、`anomaly_count=2,total_cycles=2,anomalies=[A]` とした単一理由版は `:964` で落ちる。`:965` の total/count 比較には到達しない。

## must-fix

1. anomaly の構造言語が production 出力より広く、production verifier では生成不能な witness を受理する。

   `orchestrator/campaign/reflux_formal_consumer.py:835-887` は、次の anomaly を真と判定する。

   ```json
   {
     "phenomenon": "G0",
     "length": 2.0,
     "cycle": [1, 2],
     "edges": [
       {
         "from": 1.0,
         "to": 2.0,
         "types": ["bogus"],
         "reasons": [{"type": "bogus", "key": ""}]
       },
       {
         "from": 2.0,
         "to": 1.0,
         "types": ["bogus"],
         "reasons": [{"type": "bogus", "key": ""}]
       }
     ]
   }
   ```

   独立確認で `_valid_witness_anomaly()` は `True`、digest は `6c94a1d20a3597062a16f56842c1d905fe5100b4b5d8c3c63803126897c2f633` だった。

   production では edge type は `ww/wr/rw` だけであり、`types` は reasons の type を重複除去した列、phenomenon はその types から分類される。`orchestrator/verifier/model.py:343-389`、`orchestrator/verifier/dsg.py:517-567`。また `length` と edge endpoint は int 由来である。実装は `length` と endpoint に exact type を要求せず、Python の `2.0 == 2`、`1.0 == 1` で通している。段 4 の「canonicalizer が float を拒否する」という説明 `s4-adjudication.md:49-52` も誤りで、実物は有限 float を許す。`orchestrator/campaign/reflux_origin_artifacts.py:33-39`。

   成果物影響: 全 rejected record と ledger constraint を上記 digest に揃えると、production verifier の証拠でない anomaly が FC07 を通り、`P6Unavailable` receipt と evidence reference に採用される。

2. `verify` と `integrity` の production schema、及び `clean` と counter の導出関係を検査していない。

   consumer が読むのは `reflux_formal_consumer.py:942-966` の一部 fieldだけである。したがって、実 anomaly を使っても次が通る。

   ```json
   {
     "verdict": "non-serializable",
     "certified": false,
     "serializable": false,
     "integrity": {
       "clean": true,
       "orphan_reads": 1
     },
     "anomaly_count": 1,
     "total_cycles": 1,
     "anomalies": ["fixture の有効 anomaly"]
   }
   ```

   `stats` は丸ごと欠落してよく、integrity の残りも不要である。production `result_to_dict()` は exact な top-level、stats、integrity field を必ず出す。`orchestrator/verifier/report.py:96-137`。また production の `clean()` は `orphan_reads == 0` を要求する。`orchestrator/verifier/model.py:450-467`。

   成果物影響: production report ではあり得ない自己矛盾 payload が FC07 を通り、fixture-derived receipt/reference の受理集合を拡張する。

3. B-060-M8 の負例が単一理由でなく、計画された変異を kill しない。

   `test_reflux_formal_consumer.py:1055-1057` は `total_cycles=True` と `anomaly_count=True` を同時に設定するため、`reflux_formal_consumer.py:962` と `:963` の両方が偽になる。`type(total_cycles) is int` だけを `isinstance` に緩めても、`:963` が残って拒否する。これは `s4-adjudication.md:222` の KILLED 主張に反する。

   単一理由となる具体形は、total 側なら `total_cycles=True, anomaly_count=1`、count 側なら `total_cycles=1, anomaly_count=True` である。Python equality により後続の二つの等式はどちらも真になる。

   成果物影響: 現状の負例では boolean を受理する exact-int 回帰を変異検査が誤って見逃し、その回帰版が FC07 receipt の受理集合を広げうる。

## 新たに通る入力の集合

FC07 より前の全 gate と build attempt/stage が有効であることを `U`、新判定式を `N`、旧三条件を次とする。

```text
O =
  candidate_attributable is True
  and truncated is False
  and witness_class_sha256s == [physical.constraint_sha256]
```

変更前に落ち、変更後に通る集合は、網羅的には次である。

```text
U and N and not O
```

すなわち旧 3 field の少なくとも一つが欠落または旧期待値以外で、新しい verify 条件がすべて成立する入力である。この集合は無限である。

具体形は次の三群になる。

- 正当な production 形: `reflux_origin_fixture_builder.py:409-463` の abort payload。旧 3 field は存在せず、production `verify` 形と anomaly digest が一致する。
- 非 production 形: must-fix 1 の fake anomaly を持ち、`stats` を欠落させ、`integrity={"clean":true}` だけを置く形。全 rejected record と ledger member の constraint を上記 `6c94...f633` に揃えると通る。
- hybrid 形: 新しい正例 payload に、さらに `candidate_attributable=false`、`truncated=true`、`witness_class_sha256s=[]` を追加しても通る。旧 consumer なら必ず落ちるが、新 consumer は三 field を一切読まない。

連言の独立性は次のとおり。

| 連言 | 単独反転できる入力 | 判定 |
|---|---|---|
| reason 定数比較 | reason だけ `indeterminate` | 独立 |
| verdict 定数比較 | verdict だけ `indeterminate` | 独立 |
| serializable exact false | serializable だけ `true` | 独立 |
| certified exact false | certified だけ `true` | untyped 境界では独立。production 型上は serializable false から含意される内部整合 gate |
| integrity clean | clean だけ `false` | 独立 |
| anomaly 1 件 | 有効な相異なる anomaly 2 件、両 counter 2 | 独立 |
| total exact int | total `true`、count `1` | 独立だが test 不備 |
| count exact int | total `1`、count `true` | 独立だが test と変異登録なし |
| count/list 一致 | count 2、total 2、list 1 件 | 独立 |
| total/count 一致 | total 2、count 1、list 1 件 | 独立 |
| anomaly validator | `{}` の digest まで合わせる | 独立 |
| digest 一致 | anomaly は正例、record/ledger constraint だけ別の同一値 | 独立 |

`type(verify) is dict` は受理集合を単独で区切るというより、後続 `.get()` の例外を FC07 に封じる guard である。JSON の非 dict 値では、この guard だけを除いても後続で正常受理にはならない。

## 負例の単一理由性

| test / id | 判定 |
|---|---|
| `non_candidate_reason_with_valid_verify` | single。reason 比較だけ。 |
| `non_candidate_verdict_with_valid_reason` | single。verdict 比較だけ。 |
| `dirty_integrity_with_valid_cycle` | single。clean 比較だけ。 |
| `serializable_true_with_reject_verdict` | single。serializable 比較だけ。 |
| `certified_true_with_reject_verdict` | single。certified 比較だけ。 |
| `anomaly_count_different_from_list_length` | single。count/list 比較だけ。total も 2 にして後続 equality を保っている。 |
| `truncated_verifier_anomaly_list` | single。total/count 比較だけ。 |
| `boolean_cycle_counts` | 非 single。total と count の exact-int 連言を同時に壊す。 |
| `two_anomalies_even_when_first_digest_matches` | single。anomaly 1 件条件だけ。 |
| `ring_position_mismatch_with_matching_digest` | single。ring predicateだけ。digest は再計算済み。 |
| `anomaly_extra_key_with_matching_digest` | single。anomaly exact-key predicateだけ。 |
| `empty_anomaly_with_matching_digest` | single。top-level anomaly validatorだけ。 |
| `witness_digest_mismatch_after_other_gates_pass` | single。digest 比較だけ。 |
| `unknown-phenomenon` | single。phenomenon allowlistだけ。 |
| `empty-cycle` | single。非空条件だけ。length と edges も 0 に揃えている。 |
| `cycle-not-list` | leaf 単位では非 single。list 型判定を外しても element exact-int 判定で落ちる。 |
| `boolean-cycle-id` | single。cycle id exact-intだけ。ring は boolean endpoint に揃えている。 |
| `duplicate-cycle-id` | single。distinctnessだけ。 |
| `length-mismatch` | single。length equalityだけ。 |
| `edge-count-mismatch` | single。edge countだけ。 |
| `edge-key-missing` | leaf 単位では非 single。exact-key判定を外すと `edge["types"]` 参照で例外になる。 |
| `empty-types` | single。types 非空だけ。 |
| `non-string-type` | single。types element 型だけ。 |
| `empty-reasons` | single。reasons 非空だけ。 |
| `reason-required-key-missing` | leaf 単位では非 single。key-set判定を外すと `reason["key"]` 参照で例外になる。 |
| `reason-extra-key` | single。reason key 上限だけ。 |
| `reason-type-not-string` | single。reason type 型だけ。 |
| `reason-version-not-list` | single。optional version の list 型だけ。 |
| `reason-version-boolean` | single。version element exact-intだけ。 |
| `canonicalization_artifact_error` | exception 変換経路として single。ただし実入力ではなく production canonicalizer の monkeypatch。 |
| 修正後 `test_fc09_rejects_kmax_excess` | single。各 FC07 を通して aggregate FC09 だけで落ちる。 |

top-level `_valid_witness_anomaly` の一連言として見れば parametrized 16 例はすべて他の FC07 gateを通る。しかし内部の leaf predicate の変異証拠としては、上記 3 id が単一理由ではない。

## 既存テスト弱体化の有無

「削除なし」ではない。親 commit の `orchestrator/tests/test_reflux_formal_consumer.py:922-929` にあった `test_fc07_rejects_rejected_without_single_candidate_witness` が丸ごと削除された。

新 fixture に同じ変異、すなわち `payload["witness_class_sha256s"]=[]` を加えても、新 consumer はその field を読まないため P6 まで進む。これは hybrid 旧 field の拒否を pin していた coverage の消失である。一方、純粋な旧 root 3-field 形を拒否する test は現在も `test_reflux_formal_consumer.py:939-951` に残る。ただしこれは `stage` 欠落で最初に落ちるため、旧 witness field 自体の拒否を証明しない。

それ以外に assert の反転・緩和、skip、xfail はない。FC09 kmax test は新 schema に合わせて組み直され、期待 reason は維持された。

fixture へ working-tree hash を差し込んだ箇所もない。5 baseline entry と golden 4 個は独立再計算値と一致した。`_CONSTRAINT_SHA256` も fixture 独自の `_canonical_bytes` と `_sha256` から導出される。`reflux_origin_fixture_builder.py:94-114`。

## scope 外だが real

- result-evidence production producer は依然なく、外部入力者が WAL anomaly、physical constraint、ledger constraint を同時に整合させられる。WAL と record の digest 一致だけでは独立 provenance にならない。`s4-adjudication.md:71-72`。
- `_wal_field()` の root shadow と terminal exact-shape 非閉包は残る。`reflux_formal_consumer.py:828-832`。hybrid 旧 field が通る問題もこの裁定パッケージに属する。
- occurrence identity 込み class のため、同じ違反構造が txid `[1,2]` と `[3,4]` に二度現れると 2 class扱いになり、FC07 の `len(anomalies)==1` で拒否される。qualifying rejection の receipt/reference が失われるが、構造同値 class の定義は明示 scope 外。
- reason 重複の構造破損は引き続き受理可能。`s4-adjudication.md:64-68` の既裁定どおり、consumer 単独では production 上の正当な重複可能性を排除できていない。

## refuted

- `anomalies=[{}]` を他条件が正しい状態で通す疑いは否定した。`test_reflux_formal_consumer.py:1091-1093` と `reflux_formal_consumer.py:966`。
- 実 production の `clean=False` cycle と、`count=2,total=2,list=1` の counter 偽装はそれぞれ `reflux_formal_consumer.py:951-954`、`:964` で拒否される。
- reason と verdict は冗長な equality ではなく、untyped 境界上で独立した二連言になった。
- positive control は `verify_trace_dir()` を `r9_dense_cycle4` に直接実走し、`result_to_dict()` の実 anomaly を検査する。stub、monkeypatch、手書き positive はない。`test_reflux_formal_consumer.py:925-936`。
- fixture の verify key 集合は `result_to_dict()` の `trace_dir` を除いた集合と一致し、stats/integrity の nested key も一致する。`reflux_origin_fixture_builder.py:420-460`、`report.py:96-137`。
- fixture builder は production `canonical_json_bytes` を import・呼出しせず、constraint digest は独立 canonicalizer 由来である。
- baseline 5 entry、result-evidence golden 4 個、constraint digest `c17af4fe39df550b032ab8e672f27db22be2ca16458aeeed8662f0a3bac8b2c8` は実物から独立再計算して一致した。
- list の整列・重複排除は実装されておらず、witness digest は順序を保持した anomaly 全体の直接 hash である。

## 総括

M2-M6 と M8-M10 は閉じたが、M1 と M7 は partial。  
production 生成不能な anomaly と自己矛盾 verify payload が新たな受理集合に残る。  
boolean counter 負例は二重失敗で、B-060-M8 を kill しない。  
positive control、fixture 独立性、pin 再計算、正規化全廃は成立している。  
静的検査と純粋な digest 再計算のみを行い、pytest は再実行していない。