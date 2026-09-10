## 総括

親の P1 には反対する。1 段目は 30 module ではなく **36 module** であり、明示 import 6 本が測定から漏れているため、実装対象は exact **60 path** とすべきである。  
既存 24 path の順序は epoch preimage なので固定し、新規 36 path は末尾へ repo-relative path の辞書順で追加する。測定済み 131 module のうち 60 を収載し、**未収載 71 module** と記述して推移閉包完成を名乗らない。  
現行 golden だけを 60-path 文言へ更新し、fig2b / fig2c / fig4 の凍結 bytes は据え置く。編集面は密結合しているため author 1 子で足りる。  
本回答は静的読解のみで、pytest は実行していない。

## プラン (file:line 粒度)

1. 正本 tuple を exact 60 path へ拡張する。

   - `orchestrator/campaign/campaign_lock.py:47-74`
     - コメントを exact 24 から exact 60 へ更新する。
     - 既存 24 path は 1 本も並べ替えない。現在の順序は分類順や辞書順ではなく、D442、D473、D526、D1127、D1139 ごとの**歴史的な末尾追加順**であり、`artifact_admission.py:924-927` の epoch preimage に効く。
     - 下表の corrected frontier 36 path を末尾へ辞書順で追加する。
     - 「AST で自動生成した正本」にはせず、curated exact tuple のまま維持する。

2. binding の count 文言を実体へ合わせる。検査ロジック自体は tuple 参照なので変更しない。

   - `orchestrator/campaign/contract_loader_binding.py:2`
   - `orchestrator/campaign/contract_loader_binding.py:57-60`
     - 24 path を 60 path へ更新する。
   - `orchestrator/campaign/contract_loader_binding.py:80-94`
     - exact key 集合検査はそのまま。新旧 map の互換分岐は足さない。
   - `orchestrator/campaign/contract_loader_binding.py:348-361`
   - `orchestrator/campaign/contract_loader_binding.py:364-383`
   - `orchestrator/campaign/contract_loader_binding.py:386-401`
     - capture、live verify、committed verify は自動的に 60 path を巡回するためロジック編集不要。

3. scope 診断を、未完であることが文字列だけでも分かる形へ改める。

   - `orchestrator/campaign/artifact_admission.py:72-80`
     - `CAMPAIGN_VERIFIER_EPOCH_SCOPE` の案:
       - `enforcement source closure (exact 60 path; 2026-09-01 source-import 測定 131 module 中 60、直接委譲 1 段目までを収載)`
     - `CAMPAIGN_VERIFIER_EPOCH_EXCLUDED_SCOPE` に次を明記する:
       - 同測定で未収載 71 module。
       - source-import 推移閉包は未完。
       - data file、subprocess、external command を含む非 import 委譲の完全性を主張しない。
       - 既存の verifier `__main__.py` / `cli.py` / `orchestrator/verify.py` 除外も残す。
   - 同じ count・保証説明を以下で同期する。
     - `orchestrator/campaign/artifact_admission.py:159-168`
     - `orchestrator/campaign/artifact_admission.py:898-908`
     - `orchestrator/campaign/artifact_admission.py:978-988`

4. epoch 導出と受理挙動は変更せず、変化をテストで固定する。

   - `orchestrator/campaign/campaign_lock.py:215-249`
     - `_validate_authority` は exact-24 grammar から exact-60 grammar への置換になる。
   - `orchestrator/campaign/artifact_admission.py:898-936`
     - `_recorded_campaign_verifier_epoch` は tuple 順で 60 path の digest を作る。domain `campaign-verifier-epoch/v1` は変更しない。
   - `orchestrator/campaign/artifact_admission.py:957-975`
     - D1163 の現行挙動、すなわち certified artifact 読み取りでは current closure の**可用性だけ**を確認し、記録 closure と clean current closure の bytes 差を拒否しない挙動は変更しない。
   - `orchestrator/campaign/ident.py:323-369`
     - certified run の resume は記録 commit blob と live bytes を照合するため、こちらは拡張した 60 path で fail-closed のまま。

5. source-binding の独立 literal fixture を 60 path へ更新する。

   - `orchestrator/tests/test_t671_source_binding.py:23-55`
     - 現行 24 path を `_PRE_T733_ENFORCEMENT_SOURCE_PATHS` として固定する。
     - corrected frontier 36 path を独立 literal tuple として追加する。
     - `_EXPECTED_ENFORCEMENT_SOURCE_PATHS = (*_PRE_T733..., *_T733_DIRECT_IMPORT_FRONTIER_PATHS)` とする。
     - `_RECEIPT_IMPLEMENTATION_PATHS` は現在の `[19:]` のままだと新規 36 path を誤って receipt 面へ取り込むため、旧 24 tuple の `[19:24]` から作る。
   - `orchestrator/tests/test_t671_source_binding.py:180-206`
     - current closure の test 名・期待値を exact sixty paths へ更新する。
     - suffix 36 path の exact 順序と、親が落とした 6 path の存在を独立に assert する。
   - `orchestrator/tests/test_t671_source_binding.py:334-352`
     - exact-24 は T1287 当時の歴史テストとして残す。ただし production 60 を使って検出する形ではなく、明示した `_PRE_T733...` を使い、本当に exact 24 が S8C / receipt 面を検出するテストへ直す。
   - `orchestrator/tests/test_t671_source_binding.py:355-388`
     - clean closure capture の現行 count・名前を 60 へ更新する。
   - `orchestrator/tests/test_t671_source_binding.py:470-685`
     - 既存の path 全数 parametrization を 60 path へ拡大し、新規 36 path それぞれについて dirty capture、live verify、recorded blob mismatch、共有 fixture の記録 blob 使用を検査する。

6. artifact admission の literal fixture と current golden を更新する。

   - `orchestrator/tests/test_artifact_admission.py:46-71`
     - `_EXPECTED_E1_CLOSURE_PATHS` に同じ 36-path suffix を同順で追加する。
   - `orchestrator/tests/test_artifact_admission.py:403-437`
     - fixture docstring を exact 60-path に更新する。fixture epoch は独立 literal tuple と index から再計算する構造を保つ。
   - `orchestrator/tests/test_artifact_admission.py:1031-1053`
     - E0 rejection の current scope / excluded scope golden を新文言へ更新する。
   - `orchestrator/tests/test_artifact_admission.py:1163-1171`
     - authority map count を `== 60` へ更新する。
   - `orchestrator/tests/test_artifact_admission.py:1473-1650`
     - clean committed drift は受理、uncommitted drift は `current-closure-unavailable`、HISTORICAL_RAW は live bytes 非依存、という既存の目的別挙動を維持する。
   - `orchestrator/tests/campaign_lock_test_support.py:10-48`
     - tuple を動的参照しているため編集不要。60 path へ自動追随することを `test_t671_source_binding.py:647-685` で確認する。

7. codec の exact grammar 移行を明示する。

   - `orchestrator/tests/test_campaign_lock_codec.py:34-48`
     - fixture は tuple 動的参照なので編集不要。
   - `orchestrator/tests/test_campaign_lock_codec.py:193-206`
     - missing-key parametrizationは自動的に 60 case へ増える。
   - `orchestrator/tests/test_campaign_lock_codec.py:209-251`
     - exact-2 / exact-12 rejection に加え、**pre-T733 exact-24 map を拒否するテスト**を追加する。
   - `orchestrator/tests/test_campaign_lock_codec.py:86-110`
     - v1 / authority-null の E0 decode 互換は変更しない。

8. current と frozen の golden を分離したまま更新する。

   - `orchestrator/tests/test_s1_9pair_figure_provenance.py:74-87`
     - `CURRENT_E0_EPOCH` だけを 60-path scope / 未収載 71 の excluded scope へ更新する。
   - `orchestrator/tests/test_s1_9pair_figure_provenance.py:88-101`
     - `FROZEN_E0_EPOCH` の exact-27 文言は据え置く。
   - 凍結 provenance 3 点と PNG / PDF は再生成しない。対応は次節の表のとおり。

9. `identity_scope` producer は原則編集しない。定数を参照するため、再生成時の対象 bytes だけが変わる。

   | producer | 射影・出力位置 | 影響 |
   |---|---|---|
   | `layer3_report.py` | `:290-303`, `:588-620`, `:720-755` | 新規 Layer3 JSON の epoch object が変わる |
   | `s1_report.py` | `:117-134`, `:428-430`, `:1126-1144` | JSON は変わる。Markdown は scope を描画しないため scope 由来では変わらない |
   | `backoff_sweep_report.py` | `:90-128`, `:155-164` | `.dat` provenance と report Markdown が変わる |
   | `p2_2_report.py` | `:97-109`, `:149-194`, `:214-246` | `.dat` provenance と workload Markdown が変わる。summary は scope を出さない |
   | `s8b_oracle_report.py` | `:566-620`, `:2312-2525` | observations JSON の epoch entry が変わる |
   | `s6_sort_sweep.py` | `:562-570`, `:645-647` | report Markdown が変わる |
   | `s8a_trigger_sweep.py` | `:667-675`, `:773-776` | report Markdown が変わる |
   | `critic/digest.py` | `:1202-1221`, `:1575-1605` | render 結果または標準出力だけが変わる |
   | `tools/plotting/plot_s1_9pair.py` | `:530-606`, `:1489-1560` | provenance JSON が変わる。scope は図面へ描画されない |
   | `tools/plotting/plot_backoff.py` | `:347-356`, `:592-615` | provenance JSON が変わる。scope は PNG / PDF へ描画されない |
   | `autonomous_trial_completeness.py` | `:4724-4736`, `:4981-5032` | producer ではなく persisted/fresh 比較器。自ら bytes は書かないが、旧 current report との不一致を検出する |

   親の 9 本一覧は、plotting 2 本を落とし、`autonomous_trial_completeness.py` を producer と誤分類している。

10. 実装子は分割しない。

   - author 1 子に以下をまとめて持たせる:
     - production: `campaign_lock.py`、`contract_loader_binding.py`、`artifact_admission.py`
     - tests: `test_t671_source_binding.py`、`test_campaign_lock_codec.py`、`test_artifact_admission.py`、`test_s1_9pair_figure_provenance.py`
   - tuple、epoch preimage、scope golden が密結合しており、production/test を分けると suffix 順序や count の不一致を作りやすい。
   - 別子を使うなら編集子ではなく、実装後の read-only reviewer に限定する。

11. 親の受入では、少なくとも上記 4 test file と producer consumer tests を `tools/run_tests.py` 経由で実行し、凍結 9 file の bytes 不変を確認する。私は未実走なので緑とは記録しない。

## 追加する path の一覧と根拠

親の 30 path に、`【親漏れ】` の 6 path を加えた corrected direct frontier 36 path である。

| path | import している現行閉包 member | 収載する理由 |
|---|---|---|
| `orchestrator/calibrator/__init__.py` | `execution_guard.py:22-23`, `loop.py:24`, `pipeline.py:26`, `qualification/artifacts.py:21`, `t126_driver.py:39` | calibrator package import 面 |
| `orchestrator/calibrator/effective_clock_policy.py` | `execution_guard.py:23` | 【親漏れ】clock policy 判定の直接委譲先 |
| `orchestrator/calibrator/perf_preflight.py` | `loop.py:24`, `pipeline.py:26`, `qualification/artifacts.py:21`, `t126_driver.py:39` | perf 可用性・観測の強制面 |
| `orchestrator/calibrator/runner.py` | `pipeline.py:27` | 【親漏れ】実測起動・結果取得の直接委譲先 |
| `orchestrator/calibrator/schema_v2.py` | `execution_guard.py:22` | 【親漏れ】環境 attestation schema の直接委譲先 |
| `orchestrator/calibrator/stability.py` | `pipeline.py:29`, `replay.py:46` | 【親漏れ】再測定・比較判定の直接委譲先 |
| `orchestrator/campaign/__init__.py` | `artifact_admission.py:26`, `ident.py:20`, `loop.py:25`, `pipeline.py:43`, `wal.py:38` ほか | package object を経由する import 面。現状が docstring 主体でも将来の side effect 差し替えを許さない |
| `orchestrator/campaign/axis_trigger_gating.py` | `pipeline.py:59` | trigger source 位置・marker の強制面 |
| `orchestrator/campaign/build_admission.py` | `artifact_admission.py:33`, `guided.py:38`, `ident.py:19`, `loop.py:27`, `pipeline.py:45`, `wal.py:32`, `t126_driver.py:34` | build authority / receipt 判定 |
| `orchestrator/campaign/buildcache.py` | `loop.py:25`, `pipeline.py:43,54` | build 実体と site 判定への委譲 |
| `orchestrator/campaign/calibration_verify.py` | `env_contract.py:448,603` | calibration bytes と admission semantics の検証 |
| `orchestrator/campaign/campaign_claim.py` | `loop.py:25` | campaign claim 排他・所有面 |
| `orchestrator/campaign/diff_quarantine.py` | `pipeline.py:64` | source template / diff quarantine 判定 |
| `orchestrator/campaign/env_attestation.py` | `env_contract.py:531`, `execution_guard.py:26`, `loop.py:25`, `t126_driver.py:27` | 実環境証明の判定面 |
| `orchestrator/campaign/genome.py` | `guided.py:40`, `replay.py:41` | seed 自身が guided/replay を含むため、その探索空間委譲先も閉包に必要 |
| `orchestrator/campaign/layout.py` | `artifact_admission.py:34`, `guided.py:41`, `ident.py:26`, `loop.py:29`, `pipeline.py:56`, `replay.py:42`, `wal.py:40` | lock/WAL/campaign path の解決面 |
| `orchestrator/campaign/lock.py` | `loop.py:34`, `pipeline.py:57` | campaign / bench 排他 |
| `orchestrator/campaign/model.py` | `artifact_admission.py:35`, `guided.py:42`, `ident.py:27`, `loop.py:35`, `pipeline.py:65`, `replay.py:43`, `wal.py:46`, `t126_driver.py:38` | stage・config・record 型の意味論 |
| `orchestrator/campaign/p2_2.py` | `guided.py:45`, `replay.py:45` | workload / noise 定数の直接委譲先 |
| `orchestrator/campaign/p3_b4_launcher.py` | `wal.py:475-603` | function-local import で B4 authorization を実行 |
| `orchestrator/campaign/p3_b4_protocol.py` | `wal.py:41` | WAL の B4 protocol marker 判定 |
| `orchestrator/campaign/reflux_ir.py` | `pipeline.py:69` | trigger predicate IR の生成 |
| `orchestrator/campaign/reservation.py` | `loop.py:25`, `t126_driver.py:27` | 計測時間・予約 authority |
| `orchestrator/campaign/search_baselines.py` | `guided.py:46` | guided 停止判定への直接委譲 |
| `orchestrator/campaign/site_policy.py` | `execution_guard.py:27` | 実行 site の許可判定 |
| `orchestrator/campaign/source_digest.py` | `loop.py:25`, `pipeline.py:43,71`, `t126_driver.py:27` | source evidence / digest |
| `orchestrator/campaign/trigger_gate_binding.py` | `loop.py:42`, `pipeline.py:70`, `wal.py:60` | trigger gate commitment と WAL binding |
| `orchestrator/critic/online_digest.py` | `guided.py:47` | 【親漏れ】guided の online digest 直接委譲先 |
| `orchestrator/holdout_observation.py` | `pipeline.py:30` | 【親漏れ】holdout observation admission |
| `orchestrator/qualification/attempt_ledger.py` | `qualification/artifacts.py:1288`, `t126_driver.py:60` | qualification attempt 状態 |
| `orchestrator/qualification/collector.py` | `qualification/artifacts.py:1282` | post-job receipt 検証 |
| `orchestrator/qualification/contract.py` | `qualification/artifacts.py:31`, `t126_driver.py:61` | protocol、identity、SPRT 契約 |
| `orchestrator/qualification/identity.py` | `t126_driver.py:74` | series / submission identity 検証 |
| `orchestrator/qualification/qsub_binding.py` | `t126_driver.py:78` | qsub invocation binding |
| `orchestrator/qualification/retry_index.py` | `qualification/artifacts.py:37`, `t126_driver.py:79` | retry index 検証 |
| `orchestrator/qualification/series.py` | `t126_driver.py:73` | qualification FSM / ledger replay |

「enforcement らしく見えるか」は選別基準にしない。現行 seed member から source-level に到達し、その差し替えが結果、拒否、identity、receipt、計測証拠のいずれかを変えられるなら収載する。`campaign/__init__.py`、`p2_2.py`、`search_baselines.py`、`genome.py` もこの基準では収載対象である。不要なら、依存先だけを恣意的に除くのではなく、元の seed member を閉包に置く理由から別裁定で見直す必要がある。

## 現行側 golden と凍結側 golden の対応表

| file:line | 現行 or 凍結 | 更新する or 据え置く | 理由 |
|---|---|---|---|
| `orchestrator/campaign/artifact_admission.py:72-80` | 現行 production | 更新 | 現行 60/131、未収載 71 を出す正本 |
| `orchestrator/tests/test_artifact_admission.py:1045-1053` | 現行 golden | 更新 | production scope / excluded scope の完全一致 |
| `orchestrator/tests/test_s1_9pair_figure_provenance.py:74-87` | 現行 golden | 更新 | current admission view だけを固定 |
| `orchestrator/tests/test_s1_9pair_figure_provenance.py:88-101` | 凍結 golden | 据え置く | fig4 生成時の exact-27 世界を固定 |
| `docs/paper-story/figures/fig2b_backoff_sweep_3workload.provenance.json:69,123,177` | 凍結 | 据え置く | exact-25 と批准比較を含む生成時記録 |
| `docs/paper-story/figures/fig2c_b10_extended_backoff.provenance.json:1811,3333,4855` | 凍結 | 据え置く | exact-24 だが current golden ではない |
| `docs/paper-story/figures/fig4_s1a_9pair_direct_comparison.provenance.json:44,82,120,158` | 凍結 | 据え置く | exact-27 の生成時記録 |
| `orchestrator/tests/test_backoff_figure_provenance.py:43-47` | 凍結検査 | 据え置く | fig2b provenance / generator の生成時固定 |
| `orchestrator/tests/test_b10_extended_figure_provenance.py:25-36` | 凍結検査 | 据え置く | fig2c provenance と PNG/PDF hash の固定 |

`exact 24 path` または同義の current count を持つ production/test 面は以下が全件である。

- 更新:
  - `campaign_lock.py:47`
  - `contract_loader_binding.py:2,57,60`
  - `artifact_admission.py:73,163,903,984`
  - `test_artifact_admission.py:404,1046,1170`
  - `test_s1_9pair_figure_provenance.py:79`
  - `test_t671_source_binding.py:180,355`
- 歴史的な exact-24 テストとして残すが、現在値と誤読できないよう構造を直す:
  - `test_t671_source_binding.py:334,347`
- 凍結のため据え置く:
  - fig2c provenance の上記 3 行。

他の test にある `== 24` は sweep row 数、token 数、秒数などであり closure count ではない。

## 親 brief への反論

- **refuted: 1 段目フロンティアは 30 module。**  
  実際は 36 module。親漏れ 6 本にはすべて明示 import 行がある。特に `pipeline.py:27,29,30` の `runner` / `stability` / `holdout_observation` は enforcement の中心であり、54 path で止める合理性はない。

- **real: first-party source-import 推移集合は 131 module。**  
  相対 import を正しく解決した独立な発見補助でも、親の 131 module と集合差ゼロだった。ただし D368 により、これは正本や完全性証明にはならない。

- **refuted: 閉包拡張は受理集合を単純に狭めるだけ。**  
  `campaign_lock.py:222-224` と `contract_loader_binding.py:80-94` は exact key 集合を置換する。旧 24-map は拒否され、新 60-map は旧コードでは拒否だったものが受理されるため、wire language は部分集合化ではなく**非互換な置換**である。新 map がより強い証拠を要求するので規律 2 の意味論的弱化ではないが、「受理集合は広がらない」とは書けない。

- **real: tracked authority 付き lock が 0 件なら repo 内 certified campaign の追加失効は 0 件。**  
  ただし repo 外の旧 exact-24 E1 lock は、HISTORICAL_RAW でも decode より前に exact-key rejection される。D1245 の `current-closure-unavailable` 扱いとは別問題である。

- **refuted: producer 一覧 9 本は正しい。**  
  plotting 2 本が不足し、`autonomous_trial_completeness.py` は producer でなく比較器である。

- **非 import 委譲の漏れは real。**
  - admission data: `artifact_admission.py:52,487-493` の `legacy_admission_overlay_v1.json`。歴史 artifact の分類を制御するが closure map 外。
  - policy data: `loop.py:83-98` の `tools/pegasus/policy.json`。
  - qualification data/schema: `qualification/artifacts.py:639-652,870`、`t126_driver.py:933,1305,1334,1341,1365`。T126 identity では `qualification/contract.py:39-76` に別途束縛されるが campaign epoch の tuple 外。
  - S8C data: `s8c_preregistration.py:41-49,1606,1868-1878,2080-2085`。commit blob / protected hash の別機構はあるが source tuple 外。
  - external Git:
    - `contract_loader_binding.py:18,287-300` の `/usr/bin/git`
    - `artifact_admission.py:598-610`
    - `s8c_preregistration.py:1071-1098`
    - `t126_driver.py:322-330,384-393`
  - subprocess binary: `pipeline.py:418-427`。generated benchmark binary は build receipt 等の別束縛面であり、Python source tuple には入らない。
  - dynamic import: `s8c_preregistration.py:1769-1801,1804-1839` の 2 target は既に現行 tuple 内なので、この 2 本自体は漏れではない。
  - activation/calibration data: `env_contract.py:381-386,617-624,667-700` は pinned state hash / content hash で別途束縛される。

これらを含めない本 wave は「source-import の直接 1 段目」と明記すべきであり、「委譲経路一般の 1 段目」や「推移閉包」とは名乗れない。

## 変異事前登録の候補

- `CONTRACT_LOADER_RELATIVE_PATHS` から `orchestrator/calibrator/runner.py` を落とす  
  → `test_t671_source_binding.py:180-206` の corrected exact suffix test が KILL。

- clean binding 取得後に `orchestrator/campaign/buildcache.py` へ 1 byte 追加する  
  → `test_t671_source_binding.py:518-543` の全-member live drift test が KILL。

- `_validate_authority` を「必要 key の subset があればよい」に緩め、旧 exact-24 map を受理させる  
  → `test_campaign_lock_codec.py:209-251` に追加する pre-T733 exact-24 rejection test が KILL。

- `verify_live_contract_loader_binding()` の loop を `CONTRACT_LOADER_RELATIVE_PATHS[:-1]` にする  
  → `test_t671_source_binding.py:518-543` の最後の `qualification/series.py` mutation case が KILL。

- 追加 36 path のうち 2 本を入れ替え、key 集合だけを同じにする  
  → `test_t671_source_binding.py:180-206` の exact tuple order と、`test_artifact_admission.py:426-437,1174-1188` の独立 epoch preimage golden が KILL。

## 未解決・親が測るべきこと

- P1 を 54 から **60 path** へ裁定し直し、残数を 77 から **71 module** へ直す。
- 非 import material を同じ campaign closure に含めるか、別 binding の存在を根拠に明示除外するかを裁定する。特に admission overlay JSON と qualification schema は correctness gate に直接効く。
- repo 外に exact-24 authority map を持つ lock が残っていないか再測し、あれば HISTORICAL_RAW decode 非互換を明示する。
- 実装後、producer が生成する current report の旧 scope が persisted/fresh 比較で赤にならないか確認する。凍結成果物は再生成しない。
- `tools/run_tests.py` による関連 test と全受入、凍結 PNG/PDF/provenance の byte hash、不変な tracked `campaign.lock` bytes を親が実測する。