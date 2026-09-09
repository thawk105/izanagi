## 総括

既存 fixture registry は、現行 HEAD `8fbcb70a5f4f5c098c13026c425ade66a4d6db23` の fresh official 走行を塞がない。official が使う組は `freeze=315b1eb8…`、`protocol=2c8cf9be…` であり、既存 registry の `db07b575…` / `d388477f…` とは両方異なる。`consumption-catalog.jsonl` も現行実装では明示的に無視される。

推奨は **Q4(a)**。sanctioned preflight 後にそのまま投入し、別 gate で止まれば、その gate と実値を C3b の実測結果として記録する。Pegasus 投入、pytest、driver 実行はしておらず、緑とは報告しない。

## Q1 protocol と freeze の一致判定

**判定: 一致しない。静的に決まる。**

`floor_campaign.sh` は job 内で `resolve-current-protocol` を実行し、その返した pathを固定 `--mode official --protocol ...` で driver へ渡す。[floor_campaign.sh:1172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:1172) [floor_campaign.sh:1216](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:1216)

現行 contract に合う候補が複数ある場合、resolver は HEAD の `external/ccbench` gitlink と一致する候補を選ぶ。[s8b_floor_campaign.py:1032](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:1032) [s8b_floor_campaign.py:1064](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:1064) 現 HEAD の gitlink は `511c9538e4e8efa54b45cda62e72389ed3b706ec` なので、選ばれるのは次の versioned protocol である。

- 選択される protocol: `output/s8b-freeze/floor-protocols/e576e9cd…--511c9538….json`
- `protocol_sha256`: `2c8cf9be929d83653814ecf5f2d5ed134a2af89686d796b8144da2fd45dfa58a`
- `freeze_sha256`: `315b1eb83d6fbdc525448c3c96c66ab6013df72487f35d8fa519c27ba34bc688`

この protocol の `ccbench_pin` と freeze hash は現物の 1 行目にある。[versioned protocol:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/s8b-freeze/floor-protocols/e576e9cd1369bba3ae8faca084d1b7256bf919a7dd2e5d6facb093cd9e242c01--511c9538e4e8efa54b45cda62e72389ed3b706ec.json:1) Driver は正規化 protocol の canonical JSON を hash する。[s8b_floor_campaign.py:482](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:482) [s8b_floor_campaign.py:8667](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:8667)

質問で指定された legacy anchor `floor_protocol.json` も freeze は同じ `315b1eb8…` で、protocol hash は `261cec1c…` であるため、仮にこちらでも fixture 組とは一致しない。[floor_protocol.json:1](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/output/s8b-freeze/floor_protocol.json:1)

production wrapper は caller が別 protocol を渡しても current resolver recordとの document、bytes、SHA の一致を要求する。[s8b_floor_campaign.py:7136](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:7136) [s8b_floor_campaign.py:7160](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:7160) Freeze bytesも protocol の hash と照合される。[s8b_floor_campaign.py:7373](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:7373)

したがって新 registry の path は `floor-attempt-registries/315b1eb8…/2c8cf9be…/registry.jsonl` であり、既存の `db07b575…/d388477f…/registry.jsonl` とは交差しない。[s8b_attempt_profile.py:530](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_profile.py:530)

投入直前には resolver の返す path、`git ls-tree HEAD external/ccbench`、canonical protocol SHA、freeze file SHA、導出 registry path の既存件数を snapshot すれば安価に再確認できる。

## Q2 一致時の停止点

現行 official では一致条件が成立しない。仮に `db07b575…` / `d388477f…` を使うとすると、**静かに既存 genesis を再利用せず fail-closed で停止する。**

実在 registry は schema v1 だが、C3a の新 plan は five-axis の schema v2 profileを使う。[registry.jsonl:1](/work/1/SFC/tanab/izanagi/.git/izanagi/s8b-holdout-admission-v1/floor-attempt-registries/db07b575390d1e6e76763c9dc7f5be9e07e270e101cd763eabc973b77e59cb41/d388477f0272b8d41fbc0e82956841cf5eff45f68b0c8fd40e74dc1bb6dae920/registry.jsonl:1) [s8b_floor_attempt_launcher.py:386](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:386) [s8b_attempt_profile.py:509](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_profile.py:509)

最初の非競合 session では次の順になる。

1. `_ensure_registry_genesis()` が v2 genesis の create-only publish を試みる。既存 generation に対する `[s8b-attempt-registry-create-only] durable registry generation already exists` は resume 候補として一度だけ握られる。[s8b_floor_attempt_launcher.py:1199](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:1199) [s8b_attempt_registry.py:1825](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_registry.py:1825)

2. 続く authoritative read が、v2 profile で v1 genesis を replayしようとして、core の schema gate で止まる。最初の実例外は  
   **`[attempt-registry-schema] attempt registry genesis.schema_version is unsupported`**  
   である。[attempt_registry_core.py:520](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/attempt_registry_core.py:520) [s8b_attempt_registry.py:2436](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_registry.py:2436)

3. 仮に既存物が replay可能な valid v2 schema で、slot 数だけが 96 対 288 だった場合は、`_ensure_registry_genesis()` の完全 slot 集合比較で  
   **`existing registry genesis differs from the complete slot set`**  
   となる。[s8b_floor_attempt_launcher.py:1217](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:1217)

どちらでも `_reserve()` は `_ensure_registry_genesis()` より後なので、`slot was reserved more than once` には到達しない。[s8b_floor_attempt_launcher.py:1364](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_attempt_launcher.py:1364) [attempt_registry_core.py:1232](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/attempt_registry_core.py:1232)

実在 v1 の schema 例外は `FloorAttemptRegistryError` へ包み直されないため、driver は非 0 で落ち、job wrapper が `failure.json` に `floor_driver` / `official floor driver returned nonzero` を書く。[floor_campaign.sh:1397](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:1397) なお campaign は launcher 呼出し前に consumption marker を作るため、仮想衝突時には registry の `start` は増えない一方、marker は残りうる。[s8b_floor_campaign.py:8913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:8913)

## Q3 catalog の影響

**現行コードでは `consumption-catalog.jsonl` は何も塞がない。A-5 は解決済みである。**

解決は C1b / C2 / C3a より前の registry generation 実装で行われた。世代列挙は freeze directory 直下の名前を見て、lowercase 64 hex でない sibling をそのまま無視するため、`consumption-catalog.jsonl` は列挙対象にならない。[s8b_attempt_registry.py:685](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_registry.py:685) [s8b_attempt_registry.py:729](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_attempt_registry.py:729)

専用 test も catalog 名の sibling を置き、v1 lifecycle、classification、observation、terminal、最終 read が通ることを固定している。[test_s8b_attempt_registry.py:2488](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/tests/test_s8b_attempt_registry.py:2488) C1b、C2、C3a の後もこの実装と test は現存する。

さらに actual official は freeze `315b1eb8…` を使うため、catalog がある `db07b575…` directory 自体を freeze-wide budget 列挙しない。したがって official 走行が catalog の「未知 entry」で止まる段は存在しない。

## Q4 推奨する手

**推奨は (a)。** sanctioned preflight と投入直前の pair snapshotを行ったうえで、そのまま official を投入する。

- **(a) 採用。** fixture registry と official の path は異なる。別 gate で止まった場合も、`job-result.json`、`failure.json`、driver stderr、journalから「どの gate がどの実値で止めたか」を C3b の receipt にでき、本 wave の目的に合う。

- **(b) 投入の前提にはしない。** fixture 由来であることは確定しており、既に F793 に記録されている。[failures.md:21368](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/docs/failures.md:21368) ただし exact pytest nodeは registry bytesに記録されず、現行 tracked sourceにも `campaign-fixture-execution` 等の literalが無いため、この静的範囲からは特定できない。別の追跡課題として報告する価値はあるが、C3b の投入を待たせる根拠にはならない。

- **(c) mitigation としては不可能。** official shell は protocol pathを resolverに決めさせ、production wrapperも supplied protocol と resolver recordの exact一致を要求する。任意の別 generationを指定する sanctioned seamはない。[floor_campaign.sh:1172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/tools/pegasus/floor_campaign.sh:1172) [s8b_floor_campaign.py:7210](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t1851-unit-c2/orchestrator/campaign/s8b_floor_campaign.py:7210) 別 source commitを使えば resolver結果を変えられる可能性はあるが、wave tip の C3a 実装を実測するという scopeを外れる。Freeze変更も凍結 bytes不変条件に反する。なお actual official は既に fixture とは別世代なので、回避操作自体が不要である。

- **(d) 不採用。** registry と catalog による静的 blockerは無く、実値域を得る機会を捨てる理由がない。

## Q5 危険度と報告先

fixture が本番共有 root に書ける状態は、規律 2 の観点では canonical generationの先取り、freeze-wide budgetの偽消費、正規走行の拒否、fixture proofの運用証拠への誤認を招き、正しさ gateの可用性と証拠性を脅かす。現行 collision経路は fail-closed なので、この実例だけから silent acceptanceは確認されないが、同じ production hashへ書かれれば official を止め、markerだけを残す可能性もある。規律 6 の観点では、test processという本来別 authorityの出力が耐久 production namespaceへ侵入しており、「共有 rootにあるから信頼済み」という扱いを禁じるべき信頼境界違反である。本 waveでは削除、書換え、実装修正、landをせず、既存 F793 を正本として、C3b receiptに exact path、hash、mtime、fixture identity、actual official pairとの非衝突を記録し、T-1851の統合裁定パッケージへ「test shared-root isolationとwriter provenanceの修正課題」として返すべきである。

## 未解決の問い

- fixture を書いた exact pytest nodeは、registry/catalogの durable bytesからは特定不能。実行ログ、当時の一時 worktree、または shared-rootを既定値のまま使う testの履歴監査が必要。
- 投入時に別 sessionが共有 rootへ書く可能性や、registry以外の claim、marker、queue、quota、環境 gateの成否は実行時状態であり、投入直前 snapshotと実 jobでしか確定しない。
- 仮想的な v1/v2同一 path衝突では core例外が campaignの整形済み `CampaignAbort` を迂回する。非 0停止自体は fail-closedだが、診断整形の不足は別の実装課題として報告対象になる。