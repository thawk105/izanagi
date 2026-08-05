## 判定

**partially-refuted**。  
「現時点で sanctioned な完走経路を実行すべきでない」という結論自体は確認できる。しかし「登録較正の自己不整合ゆえ attestation は必ず失敗する」という中核の因果説明は誤りである。

## 1. `attestation_mode`

production の契約型が受理する値は `"none"` と `"required"` だけで、第三の mode は存在しない。registry も `linux-baremetal=none` と `pegasus=required` の2件だけである。`orchestrator/campaign/env_contract.py:91-125`、`orchestrator/campaign/env_contract.py:163-193`

Pegasus compute の trigger 経路は site を `"pegasus"` へ閉じて写像し、`orchestrator/campaign/p3_s4_loop_trigger_gating.py:86-95`、`orchestrator/campaign/p3_s4_loop_trigger_gating.py:313-324`、`run_campaign` は明示契約が登録済み Pegasus 契約と完全一致しなければ拒否する。`orchestrator/campaign/loop.py:68-83`

`none` の v1 receipt は `attestation_mode=="none"` のときだけ consumer に受理され、required 契約へ流用できない。`orchestrator/campaign/execution_guard.py:103-118`  
したがって sanctioned な Pegasus trigger campaign で第三 mode や `none` を使う seam はない。

## 2. 別 calibration への seam

防壁を維持したまま別 calibration を選ぶ production seam は見つからない。

- registry は静的で register API を持たず、外部注入経路を設けない設計である。`orchestrator/campaign/env_contract.py:16-17`、`orchestrator/campaign/env_contract.py:197-205`
- D125 も site→env の閉じた写像と「環境変数 override を作らない」を明記する。`docs/decisions.md:6093-6096`
- loader は contract の path を解決して、その bytes の SHA-256 が pin と完全一致することを要求する。`orchestrator/campaign/env_attestation.py:811-828`
- issuer も verified calibration SHA と contract pin の一致を再検査する。`orchestrator/campaign/execution_guard.py:336-343`
- 別 `ExecutionEnvironmentContract` を production caller が組んでも、Pegasus compute の exact-contract 検査で拒否される。`orchestrator/campaign/loop.py:71-83`

fixture 内には別契約を作る例があるが、production seam ではない。`orchestrator/tests/test_execution_guard.py:233-256`

## 3. `effective_clock` と「必ず失敗」

ここが親の主張に対する最も強い反証である。

述語は expected の全標本を検査しない。expected の中央値から帯を作り、**observed の全標本だけ**が帯内かを検査する。`orchestrator/campaign/execution_guard.py:198-217`  
issuer 側の独立実装も同じである。`orchestrator/campaign/env_attestation.py:721-748`

登録 artifact の expected idx 40 = 3080.935 は中央値を変えないため、直接の失敗原因ではない。artifact は 47 個の 2101.0 と1個の 3080.935、許容幅2%を持つ。`output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1440-1493`

実際、read-only inline 検査では、**現登録較正をそのまま expected とし、observed を48個すべて2101.0にした場合、issuer が v2 receipt を発行し consumer も受理した**。この挙動は、全比較 pass なら receipt を発行するコードそのもので説明できる。`orchestrator/campaign/execution_guard.py:315-377`  
worklog も既に「live 観測が偶然すべて帯内なら certified receipt が出る」と明記している。`docs/worklog.md:1462-1469`

ただし、これだけでは実機で得られるとはいえない。production probe は `/proc/cpuinfo` の `cpu MHz` を読み、全 CPU の observed 列を作る。`orchestrator/campaign/env_attestation.py:404-450`  
T-419 の実機因果実験では、reader が busy な CPU の帯外化を 240/240 で確認し、現行方式の静穏 should-pass は0とされた。`output/insights/2026-08-04_t419-probe-causality/README.md:23-43`、`output/insights/2026-08-04_t419-probe-causality/ruling-package.md:24-34`

したがって正確な判定は次のとおり。

- 「expected の自己不整合そのものが必敗を起こす」— **refuted**
- 「現在の production probe は実機で少なくとも1個の observed 帯外値を作る」— bnode138 では強く確認済み
- 「Pegasus 全ノードで物理的に絶対不可能」— **未証明**。実験自身が外的妥当性を bnode138 の exact config に限定している。`output/insights/2026-08-04_t419-probe-causality/ruling-package.md:108-111`

## 4. attestation を通らない campaign 経路

存在し、build → verify → bench までコード上到達する。

`run_campaign` は `env_contract=None` なら即座に receipt なしで進む。`orchestrator/campaign/loop.py:62-70`  
旧 `p3_s4_loop` と sort driver は `linux-baremetal` 値を固定し、env contract を渡さず `run_campaign` を呼ぶ。`orchestrator/campaign/p3_s4_loop.py:80-85`、`orchestrator/campaign/p3_s4_loop.py:730-736`、`orchestrator/campaign/p3_s4_loop_sort.py:90-94`、`orchestrator/campaign/p3_s4_loop_sort.py:242-252`

その後は実際に、

- trace/perf の別 build：`orchestrator/campaign/pipeline.py:728-794`
- correctness verify：`orchestrator/campaign/pipeline.py:815-891`、`orchestrator/campaign/pipeline.py:952-990`
- bench と commit：`orchestrator/campaign/pipeline.py:1017-1059`

へ進む。Pegasus compute は heavy-work 拒否集合に入っていない。`orchestrator/campaign/site_policy.py:70-76`

これは既知の穴でもあり、D125 は sibling/legacy driver の compute 拒否を撤去し、さらに7本の無防壁 legacy driver が残ると記録している。`docs/decisions.md:6150-6155`

さらに、artifact admission の post-policy 経路は build-admission receipt を検査するが execution-attestation receipt を必須にしておらず、最終的に `admitted-new-schema` を返し得る。`orchestrator/campaign/artifact_admission.py:637-695`、`orchestrator/campaign/artifact_admission.py:699-712`

ただし、これを Pegasus で走らせると実機 Pegasus の値を `linux-baremetal` と記録するため、環境同一性の偽装になる。したがってユーザー指定どおり、sanctioned な反例や実行案には採用できない。この穴は別途閉じるべき防御上の所見である。

## 5. 今日、壁1を確認する別手段

既存の sanctioned な別手段は確認できなかった。

- 使い捨て smoke driver 自身が「sanctioned CLI ではない」と明記している。`output/insights/2026-08-04_wave-a-campaign-transport-smoke/driver/smoke_driver.py:1-2`
- T-506 のユーザー裁定は、U-2 までは certified campaign を開かない運用宣言を維持すると明記する。`docs/worklog.md:2874-2877`
- legacy bypass は実行可能だが、環境タグ偽装になるため不採用。
- 非認証 probe lane はまだ設計案であり、現存経路ではない。

なお、exploration type の分離だけでは proof-chain 非流入の保証にならない。`ExplorationCampaignLayout` は official layout と継承関係を持たないが、`orchestrator/campaign/layout.py:431-432`、artifact admission は文字列 path を通常の `CampaignLayout` に包み直せる。`orchestrator/campaign/artifact_admission.py:335-340`  
非認証 lane を将来設けるなら、consumer/admission 側で exploration marker を明示拒否する防壁が必要である。

pytest、ジョブ投入、ファイル作成・編集は行っていない。

## 総括

- 中核主張の判定: **partially-refuted**
- 最も強い反例: expected の外れ値は検査されず、全 observed が帯内なら現登録較正でも v2 receipt が受理される (`orchestrator/campaign/execution_guard.py:198-217`, `orchestrator/campaign/execution_guard.py:315-377`)
- 親が段 4 で採るべき行動: 「自己不整合ゆえ必敗／道は2つだけ」を撤回し、production probe の観測者効果と T-506 運用裁定を真の blocker として T-420 を U-2 後へ送り、legacy compute bypass と exploration→admission 流入穴を別件起票する