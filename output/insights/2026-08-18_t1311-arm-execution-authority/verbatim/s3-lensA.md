## 総括

判定は **NO-GO**。262 bytes と SHA-256 は正しいが、plan v1 の digest chain は「実際に provider へ送った payload」を証明せず、campaign 再導出も producer と同じ関数を読むため恒真化する。さらに T-1310 は正式 benchmark profile の前提ではあるが、中立 descriptor bytes や on/swapped descriptor の構成自体の前提ではない。

### 1. [real] `T-1310 → 単位 A` の全直列化は過剰

H1/H2 の完全 descriptor は今日構成できる。`docs/phase3-8b-descriptor-design.md:115-116` と `s8b_holdout_freeze.py:78-102` に全実値があり、凍結 selector payload に実 bytes も存在する。

| field | 値 | 現存する根拠 |
|---|---:|---|
| `schema_version` | `8b-v1` | `s8b_descriptor_schema.json:6` |
| `read_ratio_percent` | H1=80, H2=20 | `phase3-8b-descriptor-design.md:115-116`、`trial_registry.py:51-54` |
| `rmw` | 0 | `phase3-8b-descriptor-design.md:115-116` |
| `contention.skew` | 0.9 | 同上 |
| `contention.label` | `high` | `s8b_descriptor.py:25,125-128` |
| `records` | 1,000,000 | `phase3-8b-descriptor-design.md:115-116` |
| `threads` | 48 | 同上 |
| `objective` | `maximize_throughput_tps` | `s8b_descriptor.py:130` |
| `correctness` | `serializable_legacy_and_s2` | `s8b_descriptor.py:131` |
| `source` | on/swapped は `campaign_search_config_projection` | `s8b_descriptor.py:121-132`、`output/s8b-freeze/selector-runs/payload_rr80_on.json:1` |

`payload_rr80_on.json` と `payload_rr20_on.json` は full descriptor を既に保持し、その bytes は `test_frozen_artifacts.py:72-79` で pin されている。したがって P3 の「skew/rmw が無いので arm input を解決不能」は、`HOLDOUT_BINDINGS` 一個だけを見た一般化である。

一方、T-1310 は実 benchmark の production profile には必要である。現 runner は `WORKLOADS` に rr80/rr20 がなく (`p3_autonomous_workload_trial.py:188-192`)、campaign/perf/descriptor が 100k/4 固定 (`:648-690`) だからである。

P3 の「解決不能なら fallback せず拒否」自体への疑いは **refuted**。fail-closed は正しい。ただし順序は「中立 artifact と descriptor resolver は今作れる、正式 campaign/perf 実走は T-1310 後」が正確である。

成果物影響: 全 A を待たせると authority artifact は不要に未実装のまま残る。逆に T-1310 無しで正式実走まで開くと rr80/rr20 の report と campaign scale が偽る。

### 2. [real] P2 は blind 性を守らず、通常入力そのものが漏洩入力

`off` だけ `source="human_declared"` とする plan (`s2-plan.md:24-33`) に対し、on/swapped は `campaign_search_config_projection` である。planner/coder はこの一 field だけで off を識別できる。

さらに `_common_payload` は真の workload 名をそのまま渡す (`p3_autonomous_workload_trial.py:1589-1600`)。具体的な H1/off 入力は、descriptor が rr50 でも外側に `workload="rr80"` を持つ。H1/swapped も descriptor rr20 と workload rr80 の矛盾を見られる。この入力は plan の全 digest 検査を通るが、「固定中立入力だけを見た off」「別 workload descriptor だけを見た swapped」にはならない。

赤にすべき具体入力は、`workload="rr80"` と rr50 `human_declared` descriptor の組である。真の workload を表す透明 token を role-visible payload に残したままなら、descriptor ablation を迂回できる。

成果物影響: proposal・選択構成が中立/swapped descriptor ではなく `rr80` token に条件付けられ、6-cell report の on/off 差と swapped 追従を descriptor 効果として解釈できなくなる。

### 3. [refuted] 262 bytes と digest の計算誤りはない

plan の dict を

`json.dumps(sort_keys=True, ensure_ascii=False, separators=(",", ":"), allow_nan=False).encode("utf-8")`

で再生成した結果は、長さ 262 bytes、SHA-256 は

`b2c6a26304c78dadc62b4bc8996b4876e0ad6f1faba6eafd16e2b372f62208c3`

で一致した。

ただし rr50 を「中立」とする規則は凍結済み規範からは導出されない。H3 は rr50 でも skew=0.7 (`phase3-8b-descriptor-design.md:117`) なので exact collision ではない。一方、軸値 rr50/skew0.9/rmw0 は既知 ycsb-a と一致する。これは sentinel でない in-distribution 入力として blind 性には有利だが、「descriptor 無し」ではなく「既知の固定 descriptor」である。`source=human_declared` にすると、その利点も失う。

成果物影響: nit。計算値は正しいが、source と「固定既知点を neutral と呼ぶ」解釈は段 4 裁定が必要。

### 4. [real] P1 は content hash と label binding を一つの digest に過積載している

arm 名を content digest に混ぜない判断自体は正しい。混ぜれば同一 bytes が arm 名だけで異なる入力に見える (`s2-plan.md:51-55`)。しかし bytes-only digest だけでは label authority は完成しない。

具体例は、resolver regression により H1/on と H1/off が同じ bytes を返す場合である。label と arm-bearing path/ID を交換・再生成しても content digest は同一で、plan は on/off の pairwise digest 非同一を要求していない (`s2-plan.md:121-126`)。

必要なのは二層である。

- `content_digest = SHA256(canonical descriptor bytes)`
- 独立に凍結した mapping を使う domain-separated `arm_binding_digest = SHA256(version, holdout, arm, content_digest)`

arm-inclusive hashだけでは、producer/verifier が同じ manifest label を読めば再び恒真になる。arm-exclusive hashだけでは同一 content への label 交換を識別できない。加えて、同一 holdout の on/off/swapped が意図した pairwise 非同一条件を満たす検査が要る。

成果物影響: resolver が二 arm を同じ入力へ潰した run を6セルとして受理し、選択・レポートが実質4セル以下の比較になる。

### 5. [real] 6 sink の外に「実際の provider payload」という未検査 sink が残る

実 provider は payload bytes を保存し、その bytes を subprocess stdin へ送る (`claude_projected_provider.py:258-271`)。その hash も provenance に記録する (`:341-356`)。ところが completeness は provenance が非空であることしか要求せず (`autonomous_trial_completeness.py:725-735`)、`provenance.payload_sha256` を `input_payload_sha256` と比較しない。plan の新検査も proposal は再読するが provider payload/envelope は対象外 (`s2-plan.md:119-126`)。

したがって次が通り得る。

- manifest、cell、proposal、invocation、run-start、terminal は off/D50 digest。
- `provider/payload_*.json` と実 stdin だけは旧 on/D80 descriptor。
- provider が返す D80 payload hash は report に残るが、新検査は読まない。

これはまさに「label と台帳は off、実行は on」の赤入力である。既存の C10 契約も必要 field として `provider_payload_sha256` / `provider_envelope_sha256` を名指ししている (`s8c_preregistration_evidence.py:1503-1534`)。

成果物影響: 実際の proposal は on 入力から生成されたまま、台帳・report・campaign は off を名乗って受理される。

### 6. [real] campaign 検査は producer と同じ `_campaign_for` を読む恒真になる

plan は acceptance でも `_campaign_for` へ descriptor/digest を再投入する (`s2-plan.md:128-130`)。現行 completeness も producer の `_campaign_for` を直接呼ぶ (`autonomous_trial_completeness.py:2291-2342`)。

具体的な変異は、署名を保ったまま `_campaign_for.search_config` への sealed digest 追加だけを削るもの。producer と verifier の双方が digest 無し config から同じ campaign ID を導くため、runtime gate は赤にならない。固定 campaign ID の test が殺しても、それは golden の効果であり新設 acceptance gate の検出力ではない。

独立 verifier は persisted campaign lock/config bytes を読み、closed key set と digest field を直接要求すべきで、producer helper を呼んではならない。

成果物影響: arm input が変わっても campaign ID が変わらず、manifest の旧 campaign pin が別入力を受理する。

### 7. [real] 5段の label 交換理路は段 3・4・5が単独で破れる

`s2-plan.md:57-65` の各段を攻撃すると次になる。

- 段1は事象であり防壁ではない。
- 段2は resolver と verifier が同じ mutable mapping を読む限り独立証拠にならない。
- 段3は二 arm が同じ bytes へ潰れた時点で成立しない。
- 段4は、問題文が明示する「campaign pin も再生成する」攻撃には効かない。
- 段5は provider payloadを再読せず、campaign は同じ `_campaign_for` で再導出するため破れる。

成果物影響: metadata 全体を新 label/digest に再生成し、実 provider 入力だけ旧 arm に残す攻撃を受理集合から排除できない。

### 8. [real] terminal sink が `enforcement_arm` の意味を壊す

plan は digest を既存 `evaluate_formal_origin(enforcement_arm=...)` へ渡す (`s2-plan.md:107`)。同 API は任意の非空 token を受理するだけ (`reflux_formal_consumer.py:287-290,893-916`) なので 64hex は型検査を通るが、receipt にはそれを `enforcement_arm` という名前で保存する (`:368-385`)。

これは検査が赤にならない schema 意味違反である。issued binding から導いた実 arm label はそのまま保持し、digest は独立 field として formal receipt/projection に追加する必要がある。現在の P5 分割には `reflux_formal_consumer.py` の owner がいない (`s2-plan.md:164-178`)。

成果物影響: formal receipt の `enforcement_arm` 参照が arm 名でなく digest を指し、proof chain の参照意味が壊れる。

### 9. [real] 変異 matrix は削除変異では帰属を証明できない

`s2-plan.md:162` の「各 sink の消費を除く」は、次の形でなければ別防壁に殺される。

| sink | 帰属可能な変異 | 避けるべき偽 kill |
|---|---|---|
| descriptor | 別 descriptor の有効64hexを sealed digestへ入れる | key削除による shape/schema 赤 |
| campaign | 署名を保ち search_config の digest だけ省く | TypeError、既存 campaign golden |
| proposal | 有効だが誤った digest の path/content | 同名作成による `_write_bytes_bound` collision |
| invocation | uniqueかつ正規表現適合の digest-free ID | provider ID形式違反、raw pathも同時に壊す複合変異 |
| run-start | stale な有効64hexを置く | key削除による exact-key 赤 |
| terminal | stale な有効64hexを置く | `enforcement_arm` 非空検査や report shape 赤 |

各 test は期待する新設 gate の reason code を固定し、import/TypeError/FileExistsError/既存 assert なら KILLED と数えないことが必要である。

成果物影響: 帰属不能な変異を KILLED と数えると、実際には digest-free sink を受理する gateを完成扱いしてしまう。

### 10. [real] 親 brief の grep 実測は一部誤り

次は実ファイルと一致した。

- `arm` hit は4行だけ: `p3_autonomous_workload_trial.py:338,852-853,962`
- `OriginProducerInputs` constructor は `test_p3_autonomous_workload_trial.py:6490` の1件
- `output/s8c-trial-registry/` は不在
- test の `p3-t178` hit は4ファイル

一方、`brief.md:44-47` の「output 0件」は誤りである。`rg --no-ignore -l p3-t178 output` は **tracked 29ファイル**を返した。例として実 report に campaign ID がある (`output/insights/2026-08-01_t241-compute-llm-transport/evidence/control-876813-report.json:6,71,136`)。

29件は主に historical report/mutation ledger で、現行 campaign ID の live pin ではない。したがって「これら29件を書き換える必要がある」という攻撃は refuted だが、「output hit 0だから collateral 無し」という一般化も成立しない。独立 golden、FROZEN_MANIFEST、role-key pin を分類して初めて結論できる。

成果物影響: historical output を current epoch と誤認して更新すると過去台帳の再現参照が壊れる。preserve する限り current acceptance への直接影響はなく、この部分は nit 相当。

### 11. [real] 現 scope では production で一度も発火しない

C02 は依然 machine-checkable でなく (`s8c_preregistration_evidence_contract.v1.json:45-72`)、evaluator table に C02 が無く satisfiable 集合も空 (`s8c_preregistration_evidence.py:1648-1675`) である。registered launch は exact `EffectivePreregistration` を要求する (`trial_registry.py:1331-1347`)。さらに plan は exploratory admission の `arm_execution=None` を維持する (`s2-plan.md:90-93`)。

T-1310 が land しても、以下は残る。

- C02 evaluator と `accept_trial` 不在
- provider payload/envelope cross-binding、すなわち C10
- report の `scientific_claim=false` / `exploratory wiring pilot` (`p3_autonomous_workload_trial.py:2311-2318`)
- receipt v1 の `c02-arm-binding-unproven` (`s8c_acceptance_receipt.py:23-28`)

これは実装不足を隠して scope 内扱いしてはならない。段4では「T-1311は将来の registered path 用 prerequisite gateに限定する」か、「C02/C10/production-mode結線まで scopeを広げる」かを裁定パッケージにすべきである。

成果物影響: 現時点の certified 選択・certifying receipt の受理集合は1件も広がらず、生成 report は引き続き pilot/non-certifying のままである。

pytest・build は実行しておらず、緑とは判定していない。