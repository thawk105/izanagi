## must-fix

1. **D1593 鎖1は現行 run について refuted。ただし「裁定時点で既に不在」までの歴史的主張は未証明。**

   [conftest.py:1988–2061](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/conftest.py:1988) は worker の collection wrapper 内で、yield 前に全 real-repo itemへ markerを付け、yield 後に process-memo 4 node以外の `@real-repo` suffixを剥がす。[acceptance_shards.py:825–852](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/tools/acceptance_shards.py:825) はその間に markerを `ItemRecord.group` へ保存する。

   21:16 runでは `report.json.group_to_workers["real-repo"]` が100 itemを38 workerへ実配分し、`junit.xml testcase/@name`で suffixが残るのはちょうど4件です。従って「この run の100件が1 workerで303.7秒直列」は明確に refuted です。

   一方、report schemaには commit/hash fieldがありません（[acceptance_shards.py:61–65](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/tools/acceptance_shards.py:61)）。D1593自身が303.7秒を得た artifactと実行commitを結び付けない限り、「D1593の測定時にも既に不在」は未判定です。

   影響: 放置すると、裁定パッケージが「現行説明の反証」から「過去の実測そのものが虚偽」へ証拠なしに飛躍します。

2. **「lock待ちはjunitにも含まれない」は表現修正必須。**

   [acceptance_shards.py:862–872](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/tools/acceptance_shards.py:862) は各 setup/call/teardown reportの `duration` を加算します。[conftest.py:2073–2090](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/orchestrator/tests/conftest.py:2073) の real-repo lock取得はそのreport生成より外側なので、次の判定になります。

   - testcaseのjunit time／`worker_occupancy`: lock待ちを含まない — real
   - testsuiteのjunit wall `411.888秒`: session中のlock待ちを含む — 「含まれない」は refuted

   したがって `411.888 − 232.844 = 179.044秒` は「real-repo lock待ち」ではなく、collection、worker起動終了、protocol外lock待ち、session cleanup等の混合残差です。

   影響: 放置すると、台帳と裁定パッケージで179秒を誤った原因へ帰属し、次の最適化対象が変わります。

3. **T-2298の5分達成効果は未証明で、21:16 runを単独で5分へ入れることは refuted。**

   [measurements-draft.md:68–70](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/measurements-draft.md:68) の丸め列は合計81.8秒です。一方、[stage2-plan-out.md:35–53](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/stage2-plan-out.md:35) の17本をjunitから合計すると84.914秒です。後者はM09を含まず、`driver` 19.417秒と `non-guarantees` 2.447秒を含むため、そもそもconsumer集合が一致していません。

   fixture lock待ちはsetup内なので、この84.914秒に含まれます。全84.914秒が消えるという不可能な上限でも `411.888 − 84.914 = 326.974秒` で、300秒に届きません。T-2298がworker-timeや一部tailを減らす可能性はrealですが、D1620のwallを何秒動かすかは未判定です。

   影響: consumer集合を誤るとwriter閉包検査の期待値が誤り、競合によって受入の緑やcertified選択が順序依存になり得ます。また、台帳上の5分達成寄与を過大計上します。

4. **「T-2297は実装済み」は refuted。ただし承認されたruntime outcomeの大半が既に存在する点はreal。**

   現行はmarkerをshard affinity用に記録した後、runtime nodeidだけstripすることで、全100件を同一shardへ保ちながら38 workerへ分散しています。これはD1618の実行時効果を既に実現しています。

   しかしD1618が要求した明示的な契約は未実装です。

   - `ItemRecord` は `nodeid/file/group` のみでaffinity属性がない（[acceptance_shards.py:102–106](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2298-certified-evidence-lock/tools/acceptance_shards.py:102)）。
   - payload/parserも3 field固定（同:259–290）。
   - componentとclosure gateは依然 `group` をshard affinityとして使用（同:321–342、445–473）。
   - process-memo 4 nodeは引き続き `@real-repo` runtime groupとして残す必要がある。21:16 junitでは4件とも存在するものの合計0.000秒。
   - `test_g6_all_real_repo_items_stay_one_unit_and_keep_relative_order` は12.699秒で緑ですが、投影資料にtest sourceがないため、期待値のexactな変更有無は判定不能です。新契約では「単一runtime group」ではなく「単一affinity unit＋相対順序」を検査すべきです。

   影響: 実装済みとしてT-2297を閉じると、台帳が未実装のschema・closure gateを完了扱いし、将来hook順序が変わった際にshard affinityを失っても検出できません。

5. **「shard-0固有の原因」という因果結論は refuted。観測上の関連だけがreal。**

   [measurements-draft.md:12–39](/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2298-certified-evidence-lock/artifacts/measurements-draft.md:12) では、shard 1/2の `wall−maxocc` が57–73秒、shard-0が95–207秒なのはrealです。しかしhostと時刻を固定していません。

   同じbnode010のshard-0でも残差は207秒（16:30）と122秒（21:33）。また21:16→21:33で、bnode002/shard-1はwall 185→265秒ですが、bnode003/shard-2は216→221秒、shard-0は412→356秒です。「21:33は全体が1.5倍遅い」もrefutedです。

   影響: 放置すると、裁定パッケージが相関をshard-0のlock原因と誤認し、効果のない改修を優先します。

## nit

- `group_to_workers["real-repo"]` は「26+」ではなく正確には38 workerです。これはmarker消失の証拠ではなく、markerで分類されたnodeの実配分結果です。
- 21:16 shard-0は、48 worker、占有合計6702.829秒、最大232.844秒（gw27、2 item）、testsuite wall 411.888秒です。「gw27の2 itemがt080」とするnode-to-worker対応はreport/junitに記録されておらず、この資料だけでは未証明です。
- 現行runのreal-repo 100件のjunit phase合計は604.541秒です。これは38 workerに分散したworker-timeであり、D1593の旧303.7秒と直接比較して直列長の増減を論じられません。

## 親 brief と実測値への指摘

残差候補は次のように序列化できます。

| 候補 | 数字 | 判定 |
|---|---:|---|
| 共通のcollection・worker起動終了 | shard 1/2残差57–73秒 | realだが内訳未計測 |
| real-repo protocol外lock待ち | 100 node、38 worker、phase合計604.541秒 | 妥当な候補だが量は未計測 |
| shard-0の追加残差 | 21:16で基準より約106–122秒 | real、原因未判定 |
| process-memo 4 node runtime group | junit合計0.000秒 | 直接原因としてrefuted。collection時prewarm費用は未判定 |
| `campaign-repository-scan` | 6 node、junit合計0.000秒 | runtime鎖としてrefuted |
| `s8c-predicate-snapshot` | 3 node、77.857秒、gw3占有132.870秒 | realだがoccupancyへ計上済み |
| per-item teardown | `_REPORT_DURATIONS`へ計上 | 未計上残差の説明としてrefuted |
| session teardown／tmp cleanup | 計測fieldなし | 未判定 |
| shard別collection差 | 全20452件をcollect後、shard-0は6818件選択 | 時刻がなく未判定 |

17 consumerのsetup時間分布だけから直列鎖長は推定できません。setupは「lock待ち＋他fixture＋自身の準備」で、並行して待った複数consumerを合計すると同じwall区間を重複計上します。最大setupも開始時刻が揃っていなければ鎖長になりません。

必要なのは、nodeid・worker・lock modeごとの monotonic な「取得試行、取得成功、release」時刻と、pytestのlogstart／setup／call／teardown／logfinish時刻です。その区間をunionし、最終test終了との重なりを見ることで初めてD1620 wallへの寄与を算出できます。

## 総括

現行コードと21:16 artifactについて、D1593の「real-repo全体が1 worker」という鎖1は反証成立です。ただし、D1593自身の測定artifactまで遡る歴史的反証にはcommit bindingが足りません。

T-2298のRW lock化は意味論上妥当でも、現資料から証明できるのはworker-time削減の可能性までです。21:16 runを単独で5分以内へ入れる効果は数値上否定されます。T-2297はruntime上の迂回実装が既にある一方、D1618が要求したaffinityの明示契約は未了です。