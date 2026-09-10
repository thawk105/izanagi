## D1245 は満たされるか

結論: **wave 全体としては満たされない。Layer 3 の一経路だけを満たす部分実装である。**

中央 gate 単体では、`HISTORICAL_RAW` が現行 closure を読まず記録 epoch を返すため、裁定の一部は既に成立している。[artifact_admission.py:953](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:953>)、[d1245.md:3](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/verbatim/d1245.md:3>)

しかし D1245 の理由は「過去の測定事実まで読めなくする」全面維持を明示的に退けている。[d1245.md:5](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/verbatim/d1245.md:5>)、[d1245.md:9](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/verbatim/d1245.md:9>)

実際の歴史データ消費面では次が残る。

- `load_landscape` は「記録済み結果」の replay であるにもかかわらず、`CERTIFIED_ACCEPTANCE` と exact certified view を要求する。[replay.py:179](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/replay.py:179>)、[replay.py:184](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/replay.py:184>)
- S-1 は lock-only gate を `CERTIFIED_ACCEPTANCE` で呼び、`current-closure-unavailable` なら WAL を読む前に標本ゼロで戻る。[s1_report.py:302](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s1_report.py:302>)、[s1_report.py:424](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s1_report.py:424>)
- 親 brief 自身もこの実害を認めながら、P1-1 で本 wave から外している。[handoff.md:64](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/handoff.md:64>)、[handoff.md:89](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/handoff.md:89>)

D1245 を完了扱いするための最小追加は次の二面である。

1. S-1 は [s1_report.py:302](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s1_report.py:302>) の epoch gate だけを historical にし、保存済み COMMIT 検査 [s1_report.py:352](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s1_report.py:352>) は維持する。unknown は [s1_report.py:117](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s1_report.py:117>) から report の campaign epoch 集合 [s1_report.py:968](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s1_report.py:968>) へ投影する。
2. replay は [artifact_admission.py:1247](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1247>) で「current closure 可用性」と「保存済み COMMIT 証拠」を分離した historical-evidence 経路を設け、[replay.py:179](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/replay.py:179>) から使用する。exact `CertifiedCampaignView` の受理集合は広げない。

この追加を scope に入れないなら、「D1245 完了」ではなく「Layer 3 historical raw 表示面だけ完了」とし、D1245/T-2060 を未完のまま残す必要がある。

## 付け替えの安全性

`replay.load_landscape` の purpose だけを historical に変えた場合、二つが同時に外れて正常動作するわけではない。

- 保存済み COMMIT 検査は `purpose is CERTIFIED_ACCEPTANCE` の内側なのでスキップされる。[artifact_admission.py:1263](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1263>)
- 一方、`require_certified_campaign_view` は残り、返された `HistoricalCampaignView` を exact 型拒否する。[replay.py:184](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/replay.py:184>)、[artifact_admission.py:1311](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1311>)
- wrapper まで削除して動かそうとすると、保存済み COMMIT 検査と exact 型防壁の双方が失われる。さらに replay evidence capability は certified view にだけ発行されるため、`admit_replay_evidence` も成立しない。[artifact_admission.py:1278](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:1278>)、[replay.py:203](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/replay.py:203>)

したがって、動作させるために wrapper を緩める単純案は**規律 2 に触れる**。

安全な分割は可能である。

- S-1 では既に epoch 可用性 gate と保存済み COMMIT 検査が別関数なので、可用性だけを historical にできる。
- replay では既存の `require_persisted_certified_commit` と view 型分離を再利用し、historical view に保存済み証拠用の別 capability を発行する並列 API が必要である。`require_certified_campaign_view` 自体は変更してはならない。

親 brief の「purpose を替えると両方同時に外れる」は、replay の最終的な危険方向としては正しいが、単純変更時の実挙動は「exact 型拒否で停止」である。また S-1 にはその一般化は当てはまらない。

## scope 外の追加の判定

判定は **(a) 本題に必要な意味互換性の検査**。scope 外の仮想リスク gate ではない。

現 schema は top-level `additionalProperties: false` である。[layer3_schema.json:5](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:5>) 新 field を通常の `properties` に追加すると、それだけで historical と certified の双方へ受理範囲が広がる。

一方、`certifying_input=true` では歴史専用の `verifier_assessment_basis` を禁止する既存条件がある。[layer3_schema.json:6](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:6>) 同じ歴史専用意味を持つ `current_verifier_conformance="unknown"` をここへ追加するのは、新 field 導入による certified 契約の意図しない拡張を相殺する条件である。

したがって、plan 手順 4、手順 9、および変異候補 6 は保持してよい。なお実際の plan 手順 6 は admission 正負例であり、schema 禁止条件ではない。[s2-plan.md:38](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:38>)

## 保存済み成果物の互換性

現在読める v2/v3 report が新変更だけで読めなくなる経路はない。

- 新 field は top-level `required` に追加しない。[layer3_schema.json:21](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_schema.json:21>)
- v3 は schema をそのまま検証する。[layer3_report.py:253](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:253>)
- v2 reader は v3 schema の複製から schema version と `admission_decision` だけを変更する。optional field の欠落は v2 でも受理される。[layer3_report.py:262](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:262>)
- 現 schema で読める保存済み report は `additionalProperties:false` のため、新 field を既に持つことができない。新しい certified-field 禁止条件が拒否する集合には、従来読めた report は含まれない。

これは現在 `_validate_schema` を通る全 v2/v3 に対する静的な集合包含の確認である。保存ファイルの実走査や pytest は行っていない。

## 表示が届く経路

提案された Layer 3 投影は実際に成果物へ届く。

```text
require_admitted_campaign(HISTORICAL_RAW)
  -> HistoricalCampaignView
  -> build_report の明示 top-level 投影
  -> _validate_schema
  -> render / _write_report_atomic
```

根拠は [layer3_report.py:497](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:497>)、report の明示構築 [layer3_report.py:588](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:588>)、書込み [layer3_report.py:716](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/layer3_report.py:716>) である。plan 手順 2 は property を明示列挙するので、「property を足しただけで消える」問題を回避している。[s2-plan.md:21](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:21>)

したがって wave 全体が成果物を 1 bit も変えない、という指摘は refuted。新規 Layer 3 historical report bytes は変わり、DW-G05 は成立する。

ただし S-1 には投影がなく、現行 gate で早期終了するため、親 brief が掲げる Layer 3 / S-1 の双方への効果は実現しない。

## oracle 契約への波及

oracle の exact key 集合と reason enum は変わらない。

- exact key 集合: [s8b_oracle_artifacts.py:45](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s8b_oracle_artifacts.py:45>)
- exact 集合拒否: [s8b_oracle_artifacts.py:164](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s8b_oracle_artifacts.py:164>)
- reason 対応: [s8b_oracle_artifacts.py:188](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/s8b_oracle_artifacts.py:188>)
- admission 側 reason 集合: [artifact_admission.py:181](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/artifact_admission.py:181>)

新 field は Layer 3 top-level にのみ置かれ、共有 `CampaignVerifierEpoch` や oracle projection へ入らない。production source bytes の変更により将来 campaign の E1 digest 値が変わることはあるが、key 集合・state・reason enum の契約変更ではない。

## 焦点走集合の漏れ

**漏れあり。** plan の集合には replay-facing test がない。

`replay.py` は `artifact_admission` の直接 consumer であり、exact certified view、保存済み evidence capability、purpose を [replay.py:34](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/replay.py:34>) と [replay.py:179](</work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2060-current-closure-unknown/orchestrator/campaign/replay.py:179>) で使用する。一方、plan の焦点集合 [s2-plan.md:132](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:132>) から [s2-plan.md:174](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/artifacts/dev-wave-t2060-current-closure-unknown/s2-plan.md:174>) には replay を直接検査する file がない。

最低でも既存の replay test file を加える必要がある。D1245 完了のため replay を変更するなら、親 brief が示す `guided.py` と `search_baselines.py` の consumer test も必要になる。[handoff.md:64](</work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2060-current-closure-unknown/handoff.md:64>)

plan は既存の `test_artifact_admission.py` と `test_layer3_report.py` に test を追加する案であり、新規 test file は予定していない。そのままなら「新規 test file を一覧走査する meta test」の条件は発火しない。replay 用 test file を新設する場合は、その時点で repository の test-file inventory 検査を焦点集合へ追加する必要がある。

射影外の test 本文は読んでいないため、既存 replay test の正確な filename と guided/search の test filename は nit 扱いとする。

## 所見一覧 (ID / real|refuted / 実体 / 成果物影響)

| ID | 判定 | 実体 | 成果物影響 |
|---|---|---|---|
| B-01 | real | `replay.py:179-212`, `s1_report.py:302-310,424-446`, `handoff.md:64-68,89-94` | current closure 不在時、過去の landscape と S-1 標本が依然として返らず、D1245 完了とは言えない。 |
| B-02 | real | `artifact_admission.py:1263-1287,1311-1317`, `replay.py:184-212` | replay の単純な purpose 変更は検査を一部外した後に exact 型拒否され、wrapper まで緩めれば規律 2 に触れる。 |
| B-03 | refuted | `layer3_schema.json:5-18`, `s2-plan.md:32-47,115-123` | certified-field 禁止は新 field 導入で広がる certified schema を元の意味へ戻す補償条件であり、仮想リスク gate ではない。 |
| B-04 | refuted | `layer3_report.py:253-270`, `layer3_schema.json:5,21` | optional field と certified-only 禁止では、従来読めた v2/v3 report は失われない。 |
| B-05 | refuted | `layer3_report.py:497-500,588-620,716-751`, `s2-plan.md:21-34` | new historical Layer 3 report には unknown が実際に書き込まれ、DW-G05 はゼロ影響ではない。 |
| B-06 | real | `s1_report.py:117-124,424-446,968-971` | S-1 成果物には unknown が届かず、現行 closure 不在時は標本自体が消える。 |
| B-07 | refuted | `s8b_oracle_artifacts.py:45-53,164-168,188-220` | oracle の exact key 集合と reason enum は不変。 |
| B-08 | real | `replay.py:34-40,179-212`, `s2-plan.md:132-174` | replay の purpose・証拠 capability の退行を焦点走で捕捉できない。 |

Nit:

- plan の「手順 6」は schema gate ではなく admission test 追加である。schema gate の 6 は「変異候補 6」。
- 射影外 test 本文を読めないため、漏れた consumer test の正確な filename は確定していない。

## 裁定パッケージ候補 (scope 外)

### RP-B1: D1245 完了範囲

- 選択肢 A: 本 wave に replay と S-1 の安全な availability 分離を追加し、D1245 完了とする。
- 選択肢 B: 親 brief の scope を維持し、「Layer 3 historical raw 表示面のみ完了」として D1245/T-2060 を未完で残す。
- 推奨: A。裁定逐語の「過去の測定事実まで読めなくする」を実効 consumer で解消する必要がある。

### RP-B2: replay の history evidence 型

- certified view の exact 型を広げず、historical view と保存済み COMMIT 証拠 capability を組み合わせる専用経路を設ける。
- `require_certified_campaign_view` を historical に開く案は規律 2 に触れるため却下候補とする。

## 総括

plan は Layer 3 の unknown 表示、保存済み report 互換性、certified schema の意味分離、oracle 非波及については妥当である。

重大な欠落は P1-1 である。中央 `HISTORICAL_RAW` API が正しくても、実際に過去の測定を読む replay と S-1 が `current-closure-unavailable` で停止する以上、D1245 全体を満たしたとは言えない。consumer の安全な分割を追加するか、wave の完了主張を Layer 3 部分実装へ縮める裁定が必要である。

pytest その他の実行検査は行っていない。