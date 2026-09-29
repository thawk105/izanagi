## 指摘

- [must-fix] insight §3・worklog「運用の新事実」・runbook §1(f): `submit-pair-c3.log` と `submit-pair-c4.log` は request ID と `qsub rc=0` だけで、`--after` の指定値を記録していない。さらに `submit-policy.sh:41` が出すはずの `argv qsub` 行も両ログに無い。実際に「`qsub -h --after <前>` で投入した」とする記録は、この一次資料では照合できない。
- [must-fix] insight §2.2: 「投入前に `auditor_gate.parse_auditor_dict` で読んだ」という記述に対応する実行記録が無い。`release-policy.sh:10–18` の照合は preview 通過・digest・coder 一致であり、parser は呼ばない。`AuditorGateFailure` 0 件という結果と、未記録の事前操作を根拠にした説明を分ける必要がある。
- [must-fix] insight §2.3: 「claim file 4 つ、各 job_id と一致」は、`verify-series.py` に確認用コードがあるだけで、指定された一次資料に claim の内容や実行出力が無い。claim の件数・一致を照合済みの値として記録すると根拠を超える。

## 照合済み

- insight §2.4 の全 7 attempt の 5 rep、中央値、abort 率は各計測 campaign の `runs/wal.jsonl` の `bench_done` と一致。同じ job の中央値比も 2.17・1.86・2.64。
- `evidence/{stock-c0,pair-c2,pair-c3,pair-c4}/job.stderr` は各 attempt の legacy verify 1 回、性能構成 verify 5 回について、すべて `serializable`・`0 anomalies` と記録している。
- 系列 dir の `loop_state.json` は iteration 4、`policy_history.jsonl` は iteration 1 の rejected 1 行と iteration 2〜4 の certified 3 行。`verbatim/llm/auditor-output-{2,3,4}.json` はいずれも pass・違反 0。
- insight §3 の投入・開始・終了時刻は各 `job.stderr`、保留解除時刻は `release-pair-c{3,4}.log` と一致。解除から開始までは 37 秒・22 秒。
- insight §4 の Elapse は各 `job.stderr` の 308・706・696・807 秒と一致し、合計は 2,517 秒。

## 総括

**NO-GO。** 計測値、verify の結果、時刻、Elapse と主要な分類は一致した。  
ただし、実際の `--after` 指定、投入前の parser 実行、claim 4 件の一致には、指定された一次資料で確認できる証跡がない。  
この 3 点は証跡を示すか、記述を確認できた範囲に狭める必要がある。