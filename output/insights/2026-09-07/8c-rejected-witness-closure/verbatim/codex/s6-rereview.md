## 所見対応表

| 所見 | 判定 | 根拠 |
|---|---|---|
| レビュー A must-fix 1 | closed | length・端点の exact int、cycle 長 2 以上、reason type 閉集合、types・phenomenon・version の導出関係が実装された。[reflux_formal_consumer.py:896](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:896)。WW・WR・RW の version 関係は production の各分岐と一致する。[dsg.py:517](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/dsg.py:517) |
| レビュー A must-fix 2 | partial | top・stats・integrity・permutation details の外側 key 集合と clean counter は閉じた。[reflux_formal_consumer.py:1026](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:1026)。ただし stats の値型、permutation `counts` の key 集合・非負性、`sample` / `unknown_reason_sample` の型が未検査で、production 生成不能 payload が残る。 |
| レビュー A must-fix 3 | closed | `total_cycles=True, anomaly_count=1` と逆側の二本に分離され、後続 equality は `True == 1` で通る。[test_reflux_formal_consumer.py:1107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_formal_consumer.py:1107) |
| レビュー B must-fix 1 | closed | A-1 と同じ。type 閉集合・types 導出・phenomenon 再導出・version 存在関係まで production と一致する。[reflux_formal_consumer.py:936](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:936) |
| レビュー B must-fix 2 | partial | A-2 と同じ。具体的な欠落 key と非ゼロ counter は閉じたが、「untyped JSON を production schema に閉じる」という root cause は内部値で残る。[report.py:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/report.py:72) |
| レビュー B must-fix 3 | partial | fix は `dsg.py` を変更しておらず、WW は依然 set intersection を未整列で走査する。[dsg.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/dsg.py:524)。anomaly 全体を直接 hash するため、理由順の差は digest 差になる。[reflux_formal_consumer.py:974](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:974)。producer 側として scope 外にする裁定は妥当だが、root cause 自体は未閉包。 |
| レビュー B must-fix 4 | closed | A-3 と同じ。B-060-M8 の対象 gate だけを偽にする負例になった。[test_reflux_formal_consumer.py:1107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_formal_consumer.py:1107) |
| レビュー B must-fix 5 | partial | コード修正不要という裁定は妥当。ただし fix commit は二つの Python file だけで、段 4 の「材料レポートは変わらない」は未訂正のまま。[s4-adjudication.md:235](/home/SFC/tanab/.claude/jobs/96047219/wave/verbatim/s4-adjudication.md:235)。実物では projection が report に入り、acceptance receipt まで伝播する。[p3_autonomous_workload_trial.py:3618](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/p3_autonomous_workload_trial.py:3618)、[trial_registry.py:6300](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/trial_registry.py:6300) |

## regression

新たに落ちるようになった、現行の正当な production 入力は見つからなかった。

- `result_to_dict()` の現行 top・stats・integrity・permutation details は consumer 定数と一致し、pipeline は `trace_dir` だけを除いて abort payload に載せる。[report.py:96](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/report.py:96)、[pipeline.py:1601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/pipeline.py:1601)
- `qualification_policy` の有無で `emit` の送り先は変わるが、その前に作る `verify` payload は同じである。[pipeline.py:1050](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/pipeline.py:1050)。qualification event 自体は canonical payload を包む別 schema であり、formal consumer の ordered WAL 入力ではない。[artifacts.py:873](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/qualification/artifacts.py:873)
- clean な production result では対象 11 counter はすべて組み込み `int` の 0 である。これは `Integrity.clean()` の必要条件と一致する。[model.py:427](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/model.py:427)、[model.py:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/model.py:450)
- WW は両 version、WR は `u_ver` だけ、RW は両 versionを生成する。[dsg.py:523](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/dsg.py:523)
- phenomenon は双方とも全 edge type の和集合から RW、WR、その他の順で導出する。[dsg.py:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/dsg.py:548)
- 自己辺は作られず、SCC は size 2 以上に限定されるため、cycle 長 2 以上は正しい。[dsg.py:384](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/dsg.py:384)、[dsg.py:429](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/dsg.py:429)

将来 `result_to_dict()` に field が追加された場合は、consumer 更新まで fail-closed になる。ただし drift test がその差を直ちに検出するため、現時点の regression ではない。

## 新しい恒真連言

なし。すべて、他を保ったまま偽にできる JSON 入力がある。

| 新規連言群 | 単独反転例 |
|---|---|
| length / endpoint exact int | `length=2.0`、`from=1.0`、`to=2.0` |
| cycle 長 2 以上 | ring を整合させた一節点 cycle |
| reason type 閉集合 | reason と types をともに `"bogus"` |
| version 長・存在関係 | `u_ver=[1]`、WR に `v_ver` を追加、WW/RW の必須 version を除去 |
| types 導出 | reasons は RW のまま types に WW を追加 |
| phenomenon 再導出 | RW edge のまま phenomenon を `G1c` |
| verify 系 exact key | 各階層から一 key を除去、または余分 key を追加 |
| clean wire counter | `orphan_reads=1`、または bool |
| framing relation | count 0 のまま details を非空にする |
| permutation counts 型・和 | counts を list にする、bool と負数で和を 0 にする、または和を 1 にする |

なお framing 条件の `framing_violations != 0` 側は、先行する clean counter 条件により受理経路では到達不能だが、条件全体は details 非空で偽になるため恒真ではない。

## 負例の単一理由性

追加された負例 20 件のうち 18 件は single、2 件は非 single。

| 判定 | test / id |
|---|---|
| single | `length-float`、`single-node-cycle`、`edge-from-float`、`edge-to-float` |
| single | `types-not-derived-from-reasons`、`phenomenon-not-derived-from-types` |
| single | `reason-version-not-two-elements`、`wr-reason-has-v-ver`、`ww-reason-missing-u-ver`、`rw-reason-missing-v-ver` |
| single | `test_fc07_rejects_stats_with_missing_key`、`test_fc07_rejects_integrity_with_missing_key`、`test_fc07_rejects_permutation_details_with_missing_key` |
| single | `test_fc07_rejects_clean_integrity_with_nonzero_wire_counter`、`test_fc07_rejects_zero_framing_count_with_nonempty_details`、`test_fc07_rejects_permutation_count_sum_mismatch` |
| single | `test_fc07_rejects_boolean_total_cycles`、`test_fc07_rejects_boolean_anomaly_count` |
| 非 single | `reason-type-outside-closed-set`: 閉集合比較だけを除くと `_REASON_VERSION_KEYS[reason_type]` が `KeyError` になり、受理まで到達しない。[reflux_formal_consumer.py:946](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:946) |
| 非 single | `test_fc07_rejects_verify_without_stats`: top-level exact-key gate だけを除くと、直後の `verify["stats"]` が `KeyError` になり、受理まで到達しない。[reflux_formal_consumer.py:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:1028) |

anomaly 系負例は helper が anomaly digest、全 rejected record、ledger member を同期するため、FC04・FC09 や digest gateによる先取りはない。[test_reflux_formal_consumer.py:371](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_formal_consumer.py:371)

## drift test の実効性

実効性あり。

[test_real_dense_cycle4_report_schema_matches_consumer_key_sets](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_formal_consumer.py:973) は実の `verifier_core.verify_trace_dir()` を `r9_dense_cycle4` に対して呼び、その戻り値を実の `result_to_dict()` に通している。stub、monkeypatch、手書き report は使っていない。

比較対象も次の四つをすべて覆う。

- top-levelから `trace_dir` を除いた集合
- `stats`
- `integrity`
- `permutation_violation_details`

ただし nested `counts` の key・値や `sample` の型は比較していない。このため、上記 F2 の残存穴は drift testでも検出されない。

## 既存テスト弱体化の有無

なし。

`394a80ed2..284c4bd26` の test 差分は 144 行追加、2 行削除で、削除されたのは旧 `test_fc07_rejects_boolean_cycle_counts` の名前と二重変異行である。二本の単一理由 test に置換され、期待 `FC07` は維持された。[test_reflux_formal_consumer.py:1107](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_formal_consumer.py:1107)

assert の削除・反転・緩和、skip、xfail の追加はない。fix commit が変更した file も consumer と同 test の二つだけである。

## 残る must-fix

1. [reflux_formal_consumer.py:1028](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:1028) — F2 は内部値 schema が未閉包。例えば正例 fixtureのまま `stats["txns"]="bad"`、または permutation details を `counts={}`, `sample="bad"`, `unknown_reason_sample={}` にしても全連言を通る。production は三つの固定 count keyと list sample を生成する。[report.py:72](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/report.py:72)  
   成果物影響: production report ではない verify payloadに formal receipt、evidence root、report/lifecycle referenceが発行される。

2. [test_reflux_formal_consumer.py:1181](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_formal_consumer.py:1181) と [test_reflux_formal_consumer.py:1237](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_reflux_formal_consumer.py:1237) — `reason-type-outside-closed-set` と `verify_without_stats` は対象連言を外しても後続 `KeyError` で落ちる。  
   成果物影響: mutation 成果物が対象 gateを KILLED と誤認し、閉集合または top-level schema gateの認定根拠が虚偽になる。

3. [s4-adjudication.md:235](/home/SFC/tanab/.claude/jobs/96047219/wave/verbatim/s4-adjudication.md:235) — 記録を「cell の測定材料と certified 選択集合は不変だが、report artifact全体、lifecycle terminal、acceptance receiptは変わる」へ訂正する必要がある。コード修正は不要。  
   成果物影響: 未訂正のままでは report・lifecycle・acceptance receipt の bytesと digestが不変だという誤った影響評価が残る。

## scope 外だが real

- B-3 の process 間理由順非決定性。`u_writes.keys() & v_writes.keys()` の未整列走査が理由列と anomaly digestを変えうる。[dsg.py:524](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/dsg.py:524)。成果物影響: 同一 traceから異なる constraint class、result record、receipt/reference digestが生じうる。
- terminal 外枠の exact shapeと `_wal_field()` の root shadow。[reflux_formal_consumer.py:889](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:889)
- result-evidence record全体の production producer不在。[s4-adjudication.md:69](/home/SFC/tanab/.claude/jobs/96047219/wave/verbatim/s4-adjudication.md:69)
- `Integrity.clean()` の proof-surface・commit witness条件は wireへ射影されないため、consumer単独では十分条件を再計算できない。[model.py:450](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/model.py:450)

## 総括

8件は closed 4、partial 4、regressed 0。  
F1とF3の実装は production導出と一致し、現行の正当入力を落とす regressionはない。  
F2には内部値 schemaの受理穴が残り、新規負例2件も単一理由性を満たさない。  
B-3はscope外だがreal、B-5はコードでなく記録訂正が未完である。