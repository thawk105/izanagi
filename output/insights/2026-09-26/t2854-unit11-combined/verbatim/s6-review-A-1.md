## 所見

| 優先度 | 判定・箇所 | 放置した場合の成果物への影響 | 最小修正 |
|---|---|---|---|
| must-fix | **real** — [run_probe.py](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:839) は C・C1'・C3・C2' の OID を40桁の形式でしか検査しない。C0 の系譜・差分検査も、渡された OID 間の整合性を検査する。[同ファイル](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:231) | 別の整合した系列を渡して全段が合格すると、裁定済み C2' `40a7f4ac…` を検査していないのに probe が緑になる。 | 起動時に4 OIDを裁定済みの値と照合し、結果にもその照合結果を記録する。少なくとも親の起動側で同じ照合を必須にする。 |
| nit | **real** — 親が anchor を確定した [mutation-spec.json](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/spec/mutation-spec.json:3) に `anchor_status: provisional` が残る。 | kill 判定は変わらないが、成果物を読む人には anchor が未確定に見える。 | 確定済みの状態と注記に更新する。 |

## 不成立の攻撃

- **規律 1 の片木比較・一部 entry 比較:** 不成立。[C1](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:583) は C を左、C2' を右とし、両木それぞれの期待21 entry集合を確認した上で、全21件の完全展開と include 活性を比較する。1件の不一致でも不合格。include 負例も同じ `preprocess` 比較器を通り、TPC-C 9件の include 活性不一致を要求する。
- **protocol・binary・witness の取り違え:** 不成立。実行 file は protocol から `cc/silo`／`cc/mocc` に解決され、C3 は4 binaryを比較する。C4・C5 は両 protocol の合格を要求し、YCSB は verifier の rc に加えて `certified`、集計値、commit 数を確認する。[実行と verifier](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:461)
- **変異の誤 kill:** 不成立。H-set は両側の先頭理由 `schema` を要求する。H-line はTPC-C 9件の展開不一致、他12件と全21件の include 活性一致を要求する。S-table／M-type は登録理由だけを要求する。build・走行例外は `ERROR` となり kill に数えない。[判定](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:765)
- **anchor 重複・復元検査の欠落:** 不成立。[check_anchors.log](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/check_anchors.log) は C2' の該当 blob と4 anchor各1回を記録する。harness も注入前に出現1回を要求し、各変異後に pristine の SHA-256 を照合する。[harness](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2854-unit11-combined/probe/run_probe.py:635)
- **起点からの弱化:** 不成立。C0 の祖先・raw diff・tree/blob 照合、TPC-C の R 行0件拒否、`clean_env` の allowlist は残っている。`v3check.py` は起点版と差分がない。

## 判定

**NO-GO。** 計算ノードで走らせる前に、裁定済み OID への固定を入れるべきです。これは静的レビューであり、probe の実走結果は判定していません。

## 総括

検査の中身に、指定された規律 1・4 binary・両 protocol・4変異の偽緑経路は見つかりませんでした。残る受理上の穴は、検査対象そのものを別系列に差し替えられる点です。