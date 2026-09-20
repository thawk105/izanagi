## 実装した内容

指定の 4 ファイルを作成しました。

- [runner](tools/t2817_collection_stage_probe.sh)：9 cell の実行、環境・単独性・Lustre 記録、node-local 出力の回収と終了処理。
- [plugin](tools/t2817_probe_plugin.py)：指定 hook の計時、worker payload 回収、atomic JSON 書出し。一致検査を保持した実 `LoadGroupScheduling` instance を使用。
- [集計器](tools/t2817_collection_stage_aggregate.py)：指定順の Markdown／JSON、段差、参照照合、欠測表示。
- [model](tools/t2817_ledger_model.py)：48 worker、既定 cost、cardinality、partner 挿入、固定所要による比較。

差分は worktree に残しています。`git add`／`git commit` は実行していません。

## 実走した検査 (command と出力の逐語)

以下はいずれも rc=0。構文検査 2 件は出力なしです。

```bash
bash -n tools/t2817_collection_stage_probe.sh
PYTHONDONTWRITEBYTECODE=1 PYTHONPYCACHEPREFIX=/tmp/t2817-author-a-pycompile python3.10 -m py_compile tools/t2817_probe_plugin.py tools/t2817_collection_stage_aggregate.py tools/t2817_ledger_model.py
```

```bash
PYTHONDONTWRITEBYTECODE=1 PYTHONPATH="$PWD/tools" python3.10 -c 'import t2817_probe_plugin; print("plugin import: OK")'
```

```text
plugin import: OK
```

[合成入力検査スクリプト](/tmp/t2817-author-a-check.py)の実行：

```bash
PYTHONDONTWRITEBYTECODE=1 python3.10 /tmp/t2817-author-a-check.py
```

```text
aggregate positive: rc=4 cell valid=true; pre mean=58; boundary reference=68 => true; deltas=10,15,22; wall deltas=13,15,22
aggregate negative reference: reference=68.001 => false
aggregate negative missing: incomplete/missing JUnit/missing probe => invalid,n/a; unreadable Lustre => n/a; absent 9 cells => no crash
model positive: 48x10 + 2 unknown x30 + 48x1 => (a)=40, (b)=30, (a)-(b)=10
model partner: specified rule (a)/(b)=61/61; no-partner mutant=60/60 => expected 61 check rejects mutant
model default/index: 96th known=105; unknown=105; ties index 95 before 97; 95th-rank mutation=106 rejected
model cardinality: <96 sorts cardinality; cost-only negative rejected; infeasible partner/cardinality => ValueError
model scope/suffix/legacy cost: @ inside parameter preserved; runtime group extracted; real-repo strip and memo exception pass; canonical beats legacy; group cost=2+3=5, partial unit unknown
model distribution: initial 48 distinct workers at t=0; earliest available gets unit 49
synthetic artifacts: /tmp/t2817-author-a-synthetic-y72uu7wu
```

負例の model 改変は `/tmp` のコピーだけです。pytest collection、xdist、runner 本体は実行していません。

## 設計上の判断と限界

- 裁定 §3／§4 の計時区間と複合差の名称を採用しました。rc 非 0 でも `complete=true` かつ JUnit ありなら cell を有効とします。
- 元の collection index は report に保存されていないため、model は `selected` の保存順を index として使用し、「未再現」と明記します。
- real-repo suffix 除去は conftest から 112 node の集合を複写し、process-memo 例外を保持しました。将来の registry 変更には自動追随しません。
- JUnit／ledger の両方にない node の所要は、固定所要比較を保つため両案とも (a) の既定 cost を使用します。JUnit 中央値のない未収載 node は補完不能として表示します。
- 過去出力との混在を防ぐため、runner は空の `OUT_ROOT` を要求します。
- workeroutput 往復、shutdown、計算ノードでの挙動は未検証です。今回の検査は親の smoke／全走を代替しません。

## 所有外への波及

所有外 caller・共有 fixture・consumer test への変更は**無し**です。既存ファイル、docs、handoff は変更していません。

probe plugin は deselect・skip・hold・verifier に触れません。既存 shard plugin は指定された S2／S3 の argv から起動します。

## 総括

指定 4 ファイルは**実装済み・計算ノードでは未実走**です。構文・import・集計器と model の合成入力検査は通過しました。親による smoke と計算ノード実走が残ります。