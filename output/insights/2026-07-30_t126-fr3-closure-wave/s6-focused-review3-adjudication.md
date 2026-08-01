# T-126 FR3 closure — focused review 3 親裁定

日付: 2026-07-30  
段: 6 / `DW-O16` 最終巡  
判定: **NO-GO / 残存所見 1 件を real**

## 固定入力と review 成立性

- current integrated patch:
  `01ca4c2bd94f434f9380e8632f93cd48b504df97f4ad9c3c04f879fbbac0dd04`
- current source manifest:
  `08dd34250c3cb4a2daa52ff4b7b1bdaa5ce37aa8e1110bc43776ccb5c2d50073`
- focused review 3:
  `.codex/dev-wave-t126-fr3-closure-jobs/s6-focused-review3/output.md`
- review output SHA-256:
  `430c896b71478e7c60670bc136812631bbb24069f29c8eb5720550d916037dec`
- review 結果:
  closed 14 / partial 1 / regressed 0 / blocker 1 / NO-GO
- review validator:
  Pegasus `874390.nqsv`、bnode009、5秒。
  output validator、固定 hash、manifest 30 source、overall は全 rc=0。

したがって review は固定した current bytes に対する有効な最終 review として採用する。
F3-1 の create stage grammar と F3-3 の 9 mutation 再照準は closed を採用する。
残存対象は F3-2 のみである。

## F3-2 裁定

裁定: **real / scope 内 / must-fix**

入力は次の直積である。

1. attempt canonical A は submit/accounting と意味的に整合する。
2. A には正規 after-publish crash stage
   `.job-result.json.create-123-0123456789abcdef` が同一 inode hardlink として残り、
   target/stage は regular 0600、双方 nlink=2 である。
3. bound early namespace B は structurally valid だが、A と異なり
   `wmax_s=29101` のため semantic-invalid である。

`orchestrator/qualification/collector.py:894` の semantic-conflict return は、
同 `:902` の A stage cleanup より前にある。このため正規 crash lifecycle と
semantic conflict を組み合わせると A の stage が残る。

review はその後に public verifier が nlink=2 を拒否して ledger が
`outcome_pending` へ残ると記した。この停止点は実測と一致しないため、次のように訂正する。

- series-result あり:
  `collect()` 前段の attempt verifier が stage を unreferenced in-job evidence として拒否する。
  receipt / rejected evidence は未発行で、ledger は `initial_submitted` のまま。
- pre-series failure:
  semantic conflict と B の rejected evidence 保存までは到達する。
  post-job copy 後、`collector.py:1233` の closure manifest が
  `collector.py:225-227` で残存 stage を拒否する。
  failure receipt は未発行で、ledger は `initial_submitted` のまま。
- 二回目の `collect()` も同じ拒否へ収束し、attempt は閉じない。

従って review の exact ledger state は訂正するが、root cause と must-fix 判定は維持する。
成果物影響は、pre-series failure で rejected evidence と post-job copy が作成された後も
receipt / outcome event が発行されず、正規 submitted attempt が恒久的に
`initial_submitted` のまま閉じないことである。retry authority は得ないが、
qualification series を完了も失敗確定もできないため `DW-G05` を満たす実害である。

## 親の計算 node 裏取り

最終 reproducer:

- job: Pegasus `874396.nqsv`、bnode010、6秒
- source checkout HEAD:
  `efa3786833b41cb5c1ed6cd579063cfc7f8cbbb7`
- artifact:
  `.codex/dev-wave-t126-fr3-closure-jobs/compute-focused-review3-reproducer3/`
- current assertion:
  series-result あり / pre-series failure の 2 条件で `2 passed`
- 隔離 scratch の診断変異:
  semantic-conflict return の直前に、既に preflight 済みの A stage cleanup を 1 回だけ挿入
- mutation anchor:
  exact 1 件
- mutant closure assertion:
  同じ 2 条件で `2 passed`
- product source compare:
  `collector.py` 前後 SHA-256
  `9c2d3fa5ea8d556cb319f674ca287faea53f33d74fbfa5adab4cb9336be06d91`
  で一致、rc=0
- overall:
  rc=0

診断変異は fix 提案・採用ではなく、残存所見が具体的 decision point に到達し、
stage cleanup の欠落だけで closure artifact が変わることを確認する
`DW-O16` の裏取りである。

初回 job `874393.nqsv` は series-result ありだけを入力し、前段 verifier の拒否を
reviewer 記載の receipt verification と誤って期待したため harness rc=1。
再走 `874395.nqsv` は pre-series で実害へ到達し、診断変異側は 2 passed だったが、
current 側の正確な拒否点を receipt verification と期待したため rc=1。
両結果を消さず erratum とし、`874396.nqsv` で正確な artifact state を固定した。

## `DW-O16` 終端

本 wave は focused review / fix を 3 巡実施済みである。残存所見は計算 node の
current / isolated diagnostic mutation で real と裁定したため、第4 fix を起動しない。

段6は NO-GO で閉じる。次は実装 commit を作らない新しい T-126 dev-wave とし、
本裁定と reproducer を入力に正規 author worker へ fix を委ねる。
本 wave では次を実行しない。

- latest main 統合
- rejected dirty tree の commit
- `DW-O19` tracked mutation matrix
- acceptance / live qualification
- 段7〜9と local main 取り込み

これは停止条件の迂回ではなく、`DW-O16` の有界終端である。
