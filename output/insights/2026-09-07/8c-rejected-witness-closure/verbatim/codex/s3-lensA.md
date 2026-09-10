## must-fix

### 1. 任意の dict が「既知 kind・構造整合済み witness」として通る

- file:line: [s2-plan.md:47](</home/SFC/tanab/.claude/jobs/96047219/wave/artifacts/dev-wave-rejected-witness-closure/s2-plan.md:47>)、[reflux_result_evidence.py:652](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_result_evidence.py:652)、[phase3-8c-wiring-design.md:196](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/docs/phase3-8c-wiring-design.md:196)
- 通ってしまう実入力:

```json
{
  "reason": "non-serializable",
  "verify": {
    "verdict": "non-serializable",
    "certified": true,
    "serializable": true,
    "total_cycles": 1,
    "anomaly_count": 1,
    "anomalies": [{}]
  }
}
```

`physical_result.constraint_sha256` と ledger member の constraint を、空 object の正規化 digest

```text
44136fa355b3678a1146ad16f7e8649e94fb4fc21fe77e8310c060f61caaff8a
```

へ揃えると、提案された FC07 は通る。`stats` と `integrity` は省略でき、相互矛盾する `certified=true` / `serializable=true` も検査されない。ordered-WAL resolver は record が dict で、source bytes と一致することしか要求しない。

- なぜ規律 2 に触るか: 設計が要求する「既知 kind・構造整合済み witness」を、内容不明の空 object へ緩める。production verifier の証拠でない入力を qualifying rejection として新規受理する。

### 2. 実在する dirty trace の cycle を candidate 起因と誤認する

- file:line: [s2-plan.md:121](</home/SFC/tanab/.claude/jobs/96047219/wave/artifacts/dev-wave-rejected-witness-closure/s2-plan.md:121>)、[model.py:393](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/model.py:393)、[model.py:503](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/model.py:503)、[test_verifier.py:701](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_verifier.py:701)
- 通ってしまう実入力: repo の既存実例は、2 transaction の write-skew cycleを持つ一方、末尾 `E 1` が欠けた trace である。`serializable=False`、`framing_violations=1`、`integrity.clean=False` だが、verdict は priority 規則により `non-serializable` になる。pipeline はそのまま `reason=vr.verdict` と full `verify` を書く。
- anomaly listが非切詰めで constraint digest が一致すれば、提案式はこの production payload を通す。`verify.integrity.clean` を一度も読まないためである。
- なぜ規律 2 に触るか: verifier 自身の契約は dirty integrity を「CC variant の anomaly でない可能性が高い」とする。壊れた trace 由来の cycle を candidate-attributable として受理するのは、正しさ防壁の直接的な拡張である。

### 3. truncation は counter を偽装すれば隠せる

- file:line: [s2-plan.md:82](</home/SFC/tanab/.claude/jobs/96047219/wave/artifacts/dev-wave-rejected-witness-closure/s2-plan.md:82>)、[report.py:134](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/report.py:134)、[mocc_g2_discriminator.py:424](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/mocc_g2_discriminator.py:424)
- 通ってしまう実入力:

```json
{
  "reason": "non-serializable",
  "verify": {
    "verdict": "non-serializable",
    "total_cycles": 2,
    "anomaly_count": 2,
    "anomalies": ["実際には1件だけ"]
  }
}
```

anomaly を有効な dict 1 件にし、その digest を physical constraint に置けば、`total_cycles == anomaly_count` と cardinality 1 がともに成立する。実際の anomaly 列は 2 件中 1 件しかない。

- なぜ規律 2 に触るか: production の `anomaly_count` は `len(anomalies)` から作られるが、formal consumer の入力境界ではその関係を再検査していない。先例は先に `anomaly_count == len(anomalies)` を検査し、その後 `total_cycles != len(anomalies)` を truncation とする。

### 4. 重複排除が構造不整合を正常 witness と同じ digest に潰す

- file:line: [s2-plan.md:12](</home/SFC/tanab/.claude/jobs/96047219/wave/artifacts/dev-wave-rejected-witness-closure/s2-plan.md:12>)、[mocc_g2_discriminator.py:548](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/mocc_g2_discriminator.py:548)、[mocc_g2_discriminator.py:594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/mocc_g2_discriminator.py:594)
- 通ってしまう実入力: 正常な2-cycle anomaly `A` と、最初の edge の同じ rw reason を2回入れた `B` は、提案 normalizer でともに次の digestになる。

```text
2ef167bcc438c5712b3eaafad7c84543f41073a0993cb1b6ff88018ce3ffb498
```

したがって `anomalies=[A,B]`, `total_cycles=2`, `anomaly_count=2` でも digest 集合は1件となり通る。既存 discriminator は同じ入力を `rw-reason-multiplicity-mismatch` として明示的に拒否する。cycle、edge の重複も同型である。

- なぜ規律 2 に触るか: 「複数 entry が同じ class」ではなく、「正常 witness と構造破損 witness」を同一化している。cardinality 1 が構造検査の代用品になっている。

### 5. 同じ構造の違反が occurrence ID だけで別 class になる

- file:line: [s2-plan.md:55](</home/SFC/tanab/.claude/jobs/96047219/wave/artifacts/dev-wave-rejected-witness-closure/s2-plan.md:55>)、[model.py:363](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/model.py:363)
- 落ちてしまう実入力: 同じ2-edge G2構造を txid `[1,2]` で表した anomaly の digest は

```text
2ef167bcc438c5712b3eaafad7c84543f41073a0993cb1b6ff88018ce3ffb498
```

txid だけ `[3,4]` へ改名したものは

```text
dc592885e2da85adfeeb3c6ed29c03838961866f057b1b6c0dadbfd863155824
```

となる。別 SCC に同じ構造の違反が2回現れると cardinality 2 で拒否される。

- なぜ規律 2 に触るか: 「class」を occurrence identity 込みの完全な anomaly bytes と定義する裁定は存在しない。意図が構造的違反 class なら、今回の受理集合はその意味と一致しない。これは安全側の偽陽性だが、FC07 の意味を変える。

### 6. 恒真・冗長連言と変異の帰属が未成立

- file:line: [pipeline.py:1601](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/pipeline.py:1601)、[s2-plan.md:74](</home/SFC/tanab/.claude/jobs/96047219/wave/artifacts/dev-wave-rejected-witness-closure/s2-plan.md:74>)、[s2-plan.md:156](</home/SFC/tanab/.claude/jobs/96047219/wave/artifacts/dev-wave-rejected-witness-closure/s2-plan.md:156>)
- production verifier abort は、同じ `vr.verdict` を `_abort()` の reason と `result_to_dict(vr)["verdict"]` へ複製する。したがって `reason == verify["verdict"]` は production 集合上恒真である。
- `type(verify["verdict"]) is str` は、`reason` が allowlist 内の文字列であり、かつ両者が等しい時点で論理的に含意される。
- `total_cycles == anomaly_count` の下では、二つの `>= 0` の片方がもう片方を含意する。各連言を単独反転したという表は成立していない。
- RW-02 の唯一の具体負例 `reason="build-error", verify.verdict="non-serializable"` は equality だけでなく allowlist でも落ちる。equality を `True` にしても allowlist が先に拒否するため、その入力では RW-02 は KILLED にならない。
- RW-07 は、mutant が選ぶ「sorted digest の先頭」と physical constraint を一致させなければ、別の exact-digest gate が落とす。RW-08 も physical と sealed member を同時更新しなければ FC04 が先取する。
- なぜ規律 2 に触るか: load-bearing と主張する連言と変異が、実際の受理判定力を証明していない。特に attribution は実質的に `reason == "non-serializable"` だけへ縮退している。

## 親 brief への指摘

アンカー表は大半を再確認できた。ただし二点に修正が要る。

- [s1-brief.md:21](</home/SFC/tanab/.claude/jobs/96047219/wave/verbatim/s1-brief.md:21>) の「production abort payload」は verifier reject が通る `_abort()` の形としては正しいが、production 全体の abort 形ではない。`loop.py`、`screening_driver.py`、`p3_s4_loop.py`、`wal.py` に別 writer がある。
- [s1-brief.md:31](</home/SFC/tanab/.claude/jobs/96047219/wave/verbatim/s1-brief.md:31>) の先例は正しく `total_cycles != len(anomalies)` である。一方、P1 はこれを `total_cycles != anomaly_count` へ一般化しており、consumer 境界で必要な `anomaly_count == len(anomalies)` を落としている。

次は独立走査で確認できた。

- `candidate_attributable`、`truncated`、`witness_class_sha256s`、abort `witnesses` の production writer は0件。
- verifier reject の `verify` は [pipeline.py:1594](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/pipeline.py:1594) から実在する。
- commit `verify_configs` は [pipeline.py:1817](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/pipeline.py:1817) と `:1831` に実在する。
- `OriginProducerInputs(...)` の構築は repo 内では test 1件だけで、production runtime は外部注入値を読む。
- verifier-policy artifact の実 file は無く、fixture builder と test のみ。

P1 の「producer に3 fieldを書くと必ず恒真になる」は一般化しすぎである。例えば全 verifier reject で次を型付き `VerifyResult` から書けば、それぞれ false の production 入力が存在する。

```python
candidate_attributable = (
    vr.verdict == "non-serializable" and vr.integrity.clean()
)
truncated = vr.total_cycles != len(vr.anomalies)
witness_class_sha256s = normalized_classes(vr.anomalies)
```

`indeterminate`、dirty cycle、`max_report=1` かつ2 SCC がそれぞれ反例になる。producer 側は `Anomaly` / `CycleEdge` 型と positional relation を失う前に検査できるため、少なくとも「producer なら必ず弱い」という推論は成立しない。

consumer 側導出そのものは否定されない。しかし、現在のプランのように untyped JSON の完全な schema と導出関係を再検査しない実装は、producer 側より明確に弱い。

## abort reason の独立列挙

`STAGE_ABORT` の実 writer は `pipeline.py:1116,1260`、`loop.py:532,648`、`screening_driver.py:603`、`p3_s4_loop.py:735`、`wal.py:2411,2798,2805` である。

| reason | writer | candidate witness 判定 | プランとの差分 |
|---|---|---:|---|
| `non-serializable` | `pipeline.py:1594-1604` | integrity clean のときだけ帰属可能 | プランは無条件 yes |
| `indeterminate` | 同上 | no | 一致 |
| `identity-error` | `pipeline.py:1198-1201`; `loop.py:508-534` | no | 一致 |
| `admission-error` | `pipeline.py:1198-1233` | no | 一致 |
| `build-source-state-error` | `pipeline.py:1347-1354` | no | 一致 |
| `build-error` | `pipeline.py:1355-1392` | no | 一致 |
| `bench-binary-mismatch` | `pipeline.py:1422-1431` | no | 一致 |
| `trace-timeout` | `pipeline.py:1463-1470` | no | 一致 |
| `trace-no-commit-witness` | `pipeline.py:1471-1498,1541-1548` | no | 一致 |
| `trace-witness-unsupported-workload` | `pipeline.py:1499-1511` | no | 一致 |
| `trace-run-nonzero-exit` | `pipeline.py:1519-1524` | no | 一致 |
| `trace-empty` | `pipeline.py:1525-1532` | no | 一致 |
| `trace-no-abort-counts` | `pipeline.py:1533-1540` | no | 一致 |
| `trace-batch-commits-unattributed` | `pipeline.py:1549-1555` | no | 一致 |
| `trace-parse-error` | `pipeline.py:1556-1571` | no | 一致 |
| `screen-slower-than-floor` | `pipeline.py:159-160,1668-1680` | no | 一致 |
| `verify-probe-error` | `pipeline.py:1698-1707` | no | 一致 |
| `verify-competing-tenant` | `pipeline.py:1709-1714` | no | 一致 |
| `bench-probe-error` | `pipeline.py:775-785,2117-2129` | no | 一致 |
| `bench-competing-tenant` | `pipeline.py:786-789,2131-2137` | no | 一致 |
| `bench-unsettled` | `pipeline.py:801-807,2091-2106` | no | 一致 |
| `bench-returncodes-round-unbound` | `pipeline.py:809-818` | no | 一致 |
| `bench-no-throughput` | `pipeline.py:820-826,2163-2196` | no | 一致 |
| `bench-cv-undefined` | `pipeline.py:827-836,2244-2250` | no | 一致 |
| `balanced-peer-prepare-failed` | `loop.py:665-671` | no | 一致 |
| `eval-exception: <type>: <message>` | `loop.py:628-648`; `screening_driver.py:589-603` | no | screening writer が表から欠落 |
| `diff-quarantine` | `p3_s4_loop.py:703-739` | no | 一致 |
| `recovery-abort-incomplete-attempt` | `model.py:114`; `wal.py:2595-2626` | no | 補足のみ |
| `a1-balanced5-interrupted-attempt-invalid` | `wal.py:126-128,2595-2626` | no | 補足のみ |
| `recovery-abort-trigger-binding-orphan` | `wal.py:87,2787-2805` | no | 完全に欠落 |

未知 reason は `reason in frozenset({"non-serializable"})` で false になるため fail-closed である。列挙漏れが未知 reason を自動受理する経路はない。

## scope 外だが real

- [reflux_formal_consumer.py:821](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/campaign/reflux_formal_consumer.py:821) の root→payload fallback と terminal 外枠非 exact は残る。root `verify` / `reason` が payload を shadow できる。D1715で明示的に scope 外へ送られた問題なので、本 wave 内の修正対象とはしない。
- result-evidence production producer は依然存在しない。外部入力側が ordered WAL、physical constraint、ledger constraint を整合して自作できる信頼境界は、consumer の digest 一致だけでは閉じない。これは result-evidence producer 全体の裁定パッケージ候補であり、本 wave に追加実装を求めない。

## refuted

- 未知 abort reason が fail-open になる疑いは否定した。一要素 positive allowlist により必ず FC07 となる。
- `total_cycles == anomaly_count` が production 上恒真という疑いは否定した。[core.py:173](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/verifier/core.py:173) は切詰め前 total と切詰め後 list を別に保持し、[test_verifier.py:2592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-rejected-witness-closure/orchestrator/tests/test_verifier.py:2592) に `total_cycles=2`, `len(anomalies)=1` の実例がある。問題は consumer が count と list の関係を検査しない点である。
- production が作る別 SCC は txid 集合が互いに素なので、二つの独立 SCC が提案 normalizer で同じ digest に落ちる経路は、SHA-256衝突を除き見つからなかった。逆に同じ構造を別 class へ割る問題は must-fix 5 のとおり実在する。
- dict key順、cycle/edgeの同時回転、reason順、同一 anomaly の重複は同じ digest になった。valid production の整数は canonical JSON の exact int であり、`1` と `1.0` の表現差は後者を明示拒否するため、健全な production reject が整数表現だけで分裂する例は見つからなかった。

## 総括

提案式は任意 dict、dirty verifier結果、偽装 counter を qualifying rejection として通す。  
normalizer は構造破損を正常 witness と同一化する一方、occurrence IDで同じ構造を分裂させる。  
P1 の producer恒真論は反例があり、consumer方向の優位は証明されていない。  
abort reason は未知値に対して fail-closed だが、表から1 reasonと1 writerが漏れている。  
現プランのまま author 段へ進めるのは規律 2 に反する。