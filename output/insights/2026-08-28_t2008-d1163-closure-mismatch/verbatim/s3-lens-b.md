## 数え上げ

母集合は以下です。

- 呼び出し点: tracked な `*.py` 全体。`orchestrator/tests/**` と生成物 `output/**` を production から除外。
- 検索式: `rg '(require_admitted_campaign|require_campaign_verifier_epoch)\s*\('` と `rg 'CampaignReadPurpose\.(CERTIFIED_ACCEPTANCE|HISTORICAL_RAW)'`。
- 診断値: tracked text 全体を `git grep -I -o -F <literal> -- .`。binary は除外。
- campaign: repo 内 `output/**/campaign.lock` 全件と、既知の外部永続 root で見つかった lock。mutation scratch/worktree/archive copy は official 母集合から除外。

### API / purpose

| 区分 | 件数 | 内訳 |
|---|---:|---|
| production の意味的 consumer | 30 | certified 24、historical 6 |
| `require_admitted_campaign` の直接式 | 23 | 固定 purpose 22、`replay.py:149` の generic forward 1 |
| `require_campaign_verifier_epoch` の直接式 | 2 | いずれも certified |
| test の直接式 | 60 | admitted 59、epoch-only 1。成果物受理集合は変えない |

親プランの certified 24件は正しいですが、repository 全体では `tools/plotting/` の historical 2件が漏れており、purpose consumer は28件でなく30件です。

| 呼び出し点 | purpose | 受理集合・出力の変化 |
|---|---|---|
| `orchestrator/campaign/autonomous_trial_completeness.py:4421` | certified | committed closure mismatch だけなら cross-binding 再検証を通る。 |
| 同 `:4892` | certified | failure campaign が mismatch だけなら「独立 admission が残る」側へ進み、失敗 campaign として拒否される。 |
| 同 `:4939` | certified | success campaign の persisted Layer3 照合へ進む。 |
| `backoff_extended_sweep_report.py:463` | certified | normal point の discovery 集合へ入る。 |
| `backoff_overthrottle.py:149` | certified | AA reference binding 候補へ入る。 |
| `backoff_sweep_report.py:59` | certified | workload report 対象へ入る。 |
| `layer3_report.py:668` | certified | receipt 等が妥当なら accepted Layer3 を生成できる。 |
| `p3_autonomous_workload_trial.py:3090` | certified | critic digest 再計算へ進む。 |
| `p3_b4_closed_critic.py:735` | certified | stable snapshot 入力へ進む。 |
| 同 `:1734` | certified | receipt 再検証へ進む。 |
| `p3_b4_wiring_probe.py:1477` | certified | committed drift 後も probe view を発行できる。 |
| `p3_s4_loop.py:1218` | certified | bootstrap history の内容検査へ進む。 |
| 同 `:1537` | certified | iteration 後 digest を生成できる。 |
| 同 `:1745` | certified | CLI 後段の digest/red-record 検査へ進む。 |
| `p3_s4_loop_sort.py:505` | certified | sort iteration の critic digest を生成できる。 |
| 同 `:694` | certified | CLI 後段検査へ進む。 |
| `p3_s4_loop_trigger_gating.py:1035` | certified | trigger-gating digest を生成できる。 |
| `p3_s4_red.py:193` | certified | admitted WAL 検査へ進む。anomaly reject は不変。 |
| `replay.py:186` | certified | landscape/replay evidence に使える。 |
| `s1_report.py:387` | certified epoch-only | S1 schedule の早期除外から外れる。 |
| `s6_sort_sweep.py:476` | certified | certified rows の report 対象へ入る。 |
| `s8a_trigger_sweep.py:578` | certified | trigger sweep rows の対象へ入る。 |
| `s8b_oracle_report.py:556` | certified epoch-only | `eligible=false/rejection` から `E1/eligible=true` へ変わる。 |
| `orchestrator/critic/digest.py:1578` | certified | critic digest を生成できる。 |
| `layer3_report.py:482` | historical | 受理集合不変。プランでは marker を出す唯一の historical projection。 |
| `p2_2_report.py:132` | historical | 受理集合不変。現在は5-field epoch/read-purposeだけを表示し、新 marker は出ない。 |
| `orchestrator/critic/digest.py:1191` | historical | 受理集合不変。rendered digest に新 marker は出ない。 |
| `orchestrator/critic/online_digest.py:43` | historical | 受理集合不変。上の digest rendering を使うため marker は出ない。 |
| `tools/plotting/plot_backoff.py:270` | historical | 受理集合不変。figure provenance の手書き5-field epoch に marker が届かない。 |
| `tools/plotting/plot_s1_9pair.py:558` | historical | 受理集合不変。figure provenance の手書き5-field epoch に marker が届かない。 |

### 診断値

| 値 | production | schema | test | ledger | docs | 生成済み成果物 | 合計 |
|---|---:|---:|---:|---:|---:|---:|---:|
| `recorded-current-closure-mismatch` | 3 | 1 | 4 | 1 | 2 | 10 | 21 |
| `current-closure-unavailable` | 3 | 1 | 2 | 0 | 0 | 7 | 13 |
| `E1-stale` | 3 | 1 | 6 | 1 | 9 | 28 | 48 |

役割は次のとおりです。

- 産出側: `artifact_admission.py:838,857,863`。撤去後は `recorded-current-closure-mismatch` だけ非産出になる。
- 受理側: `artifact_admission.py:188-193`、`layer3_schema.json:219-220`、`s8b_oracle_artifacts.py:204-212`。3面とも legacy 値を引き続き読む。
- test: producer 挙動または legacy reader の合成記録。
- ledger: test node id の履歴であり campaign 診断ではない。
- docs / `output/insights`: 過去 wave の説明・逐語・入力 snapshot。campaign 記録そのものではない。

repo 内の実 campaign tree、構造化 JSON/JSONL/lock、および確認した外部永続 rootには、上記3診断値を保存した実記録は各0件でした。したがって P2 は「repo 内に実在する過去記録を救う」根拠ではなく、forward/legacy reader compatibility の根拠です。reader を残す判断自体は妥当です。

## 所見

- ID B1 / real / scope 内 / 実体: historical caller は6件で、プランが marker を投影するのは `layer3_report.py` だけ。`p2_2_report.py:97-107`、`critic/digest.py:1190-1215`、両 plotter の手書き epoch 射影が取り残される / 成果物影響: これら5 producer は撤去後も「当時の verifier での判定」を明示せず、現行再検証済みと誤読可能な旧形を生成する。

- ID B2 / real / scope 内 / 実体: repo 外の official root に現在の24-path mapと一致する campaign が5件ある。B10 3件と paper-story A2 2件 / 成果物影響: `artifact_admission.py` の commit 後、撤去しなければ5件が新たに mismatch 拒否され、撤去すれば E1 のまま読める。親の「この撤去で読める既存成果物0件」は誤り。

- ID B3 / real / scope 内 / 実体: plan の schema は `verifier_assessment_basis` を optional property として足すだけで、`certifying_input` との条件関係がない / 成果物影響: certified Layer3 に `"recorded-at-original-verifier-epoch"` を混入しても schema を通り、producer の型分離と reader 契約が非対称になる。

- ID B4 / real / scope 内 / 実体: reason集合は `artifact_admission.py:185-194`、`layer3_schema.json:219-220`、`s8b_oracle_artifacts.py:204-213` に3重化されている。3面を比較する test/helper はない。全3名を含む `test_s8b_oracle_driver.py` も別々の無関係な検査で同期は見ない / 成果物影響: schemaだけ狭めるとLayer3だけ旧記録を拒否、oracleだけ狭めるとofficial observationsだけ拒否、dataclassだけ狭めるとPython view/exception構築だけ失敗する。

- ID B5 / real / scope 外 / 実体: mismatch 比較撤去後も `capture_contract_loader_binding()` は返り値を捨て、可読性だけで `current-closure-unavailable` を産出する / 成果物影響: uncommitted closure edit中は完全なcampaignでも全certified consumerが拒否され続ける。親P1の所見どおり不自然だが、D1163の「1条件だけ」より広い変更なので別裁定。

- ID B6 / real / scope 内 / 実体: `artifact_admission.py` は campaign closure だけでなく `p3_b4_closed_critic.py:623` の projection closure、admission receipt の validator SHA (`artifact_admission.py:929`) にも入る。`layer3_report.py:579` は自身のSHAを全reportへ入れる / 成果物影響: A/L編集で B4 projection SHA、admission receipt、Layer3 generator SHAが変わる。検索した root に B4 v3 receipt・persisted Layer3 v3 は0件だったが、存在すれば current-hash/fresh-rebuild consumerで拒否される。

- ID B7 / 疑わしい / scope 内 / 実体: direct-name test union は30 test moduleで親プランと一致するが、全production sourceをglob/AST走査するtestと間接consumer testが別にある / 成果物影響: 今回の予定差分は対象文字列を増やさないため直ちに赤とは断定しないが、焦点走集合を「30件で悉皆」とは呼べない。

- ID B8 / nit / scope 内 / 実体: duration ledger の8 node idを改名・削除しても schema/collection join は失敗しない。consumerは収集されたnode idをlookupするだけ / 成果物影響: 旧keyは未使用のまま残り、新名はunknown costになる。full再生成なら旧key削除、`--add-only`なら旧keyを残して新keyを追加する。名称維持方針は妥当だが「改名すると受入が赤」は誤り。

## 取り残し candidate

### production / artifact

- `orchestrator/campaign/p2_2_report.py:97`
- `orchestrator/critic/digest.py:1190`
- `orchestrator/critic/online_digest.py:42`
- `tools/plotting/plot_backoff.py:269`
- `tools/plotting/plot_s1_9pair.py:529`
- `orchestrator/campaign/layer3_schema.json:213`
- `orchestrator/campaign/p3_b4_closed_critic.py:623`
- `orchestrator/campaign/autonomous_trial_completeness.py:4648`

現在のmapと一致する外部 official campaign:

- `/work/1/SFC/tanab/b10-backoff-grid-runs5/b10-backoff-grid-20260826T234647Z-783837-read-heavy/campaigns/b10-backoff-grid-silo-read-heavy-sweep-e2d75497/campaign.lock:1`
- `/work/1/SFC/tanab/b10-backoff-grid-runs5/b10-backoff-grid-20260826T234647Z-783837-balanced/campaigns/b10-backoff-grid-silo-balanced-sweep-9ded73c4/campaign.lock:1`
- `/work/1/SFC/tanab/b10-backoff-grid-runs5/b10-backoff-grid-20260826T234647Z-783837-write-heavy/campaigns/b10-backoff-grid-silo-write-heavy-sweep-0a386b45/campaign.lock:1`
- `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260827/jobs/rr5/campaigns/paper-story-a2-rr5-paper-story-a2-certification-rr5-df07b695/campaign.lock:1`
- `/work/1/SFC/tanab/izanagi-measurements/dev-wave-paper-story-a2-cert-20260824/t2022-20260827/jobs/rr50/campaigns/paper-story-a2-rr50-paper-story-a2-certification-rr50-794cfb1a/campaign.lock:1`

### direct reference test union

30 `test_*.py` は親プランと一致し、加えて helper 1件です。

```text
orchestrator/tests/commit_receipt_support.py:9
orchestrator/tests/test_artifact_admission.py:16
orchestrator/tests/test_autonomous_trial_completeness.py:26
orchestrator/tests/test_backoff_consumers.py:21
orchestrator/tests/test_bench_first_real_wal.py:32
orchestrator/tests/test_campaign.py:9960
orchestrator/tests/test_campaign_lock_codec.py:208
orchestrator/tests/test_ccbench_spawn_sites.py:80
orchestrator/tests/test_critic.py:32
orchestrator/tests/test_env_contract_activation.py:1953
orchestrator/tests/test_layer3_admission_diagnosis.py:21
orchestrator/tests/test_layer3_report.py:26
orchestrator/tests/test_official_perf_closure.py:53
orchestrator/tests/test_p3_autonomous_workload_trial.py:31
orchestrator/tests/test_p3_b4_closed_critic.py:39
orchestrator/tests/test_p3_b4_wiring_probe.py:157
orchestrator/tests/test_p3_build_authority_cli.py:92
orchestrator/tests/test_p3_s4_loop.py:58
orchestrator/tests/test_p3_s4_loop_sort.py:34
orchestrator/tests/test_p3_s4_loop_trigger_gating.py:38
orchestrator/tests/test_s1_9pair_figure_provenance.py:32
orchestrator/tests/test_s6_sort_sweep.py:44
orchestrator/tests/test_s8a_trigger_sweep.py:45
orchestrator/tests/test_s8b_oracle_driver.py:74
orchestrator/tests/test_s8b_oracle_report.py:33
orchestrator/tests/test_s8c_acceptance_receipt_v2.py:342
orchestrator/tests/test_t126_pegasus_tools.py:451
orchestrator/tests/test_t126_qualification_artifacts.py:18
orchestrator/tests/test_t1286_commit_receipt.py:24
orchestrator/tests/test_t671_source_binding.py:17
orchestrator/tests/test_trial_registry.py:24
```

名前grepでは拾えない内容走査 test:

```text
orchestrator/tests/test_login_headroom.py:1604
orchestrator/tests/test_p3_exploration_namespace.py:126
orchestrator/tests/test_pegasus_dispatch_compute.py:2249
orchestrator/tests/test_reflux_ir.py:293
orchestrator/tests/test_s1_known_axes_freeze.py:540
orchestrator/tests/test_s8b_floor_campaign.py:1592
orchestrator/tests/test_s8b_floor_campaign.py:6334
orchestrator/tests/test_s8b_floor_stats.py:891
orchestrator/tests/test_s8b_oracle_manifest_contract.py:49
orchestrator/tests/test_s8b_ratified_freeze.py:2403
orchestrator/tests/test_t338_submission_gate_unit5.py:494
```

間接consumer test:

```text
orchestrator/tests/test_backoff_extended_sweep.py:22
orchestrator/tests/test_backoff_extended_sweep_report.py:17
orchestrator/tests/test_backoff_overthrottle.py:15
orchestrator/tests/test_backoff_figure_provenance.py:510
orchestrator/tests/test_guided.py:46
orchestrator/tests/test_s1_report.py:36
```

## docs の食い違い

- D422 (`docs/decisions.md:17555`): E1/current exact一致とE1-stale/mismatchの定義は撤去後の現行定義ではない。ただし D1163 がこの条件だけを明示 supersede 済みなので、旧本文を書き換えず後発決定で読む形は成立する。

- D956 (`docs/decisions.md:34200`): 改訂が必要です。特に「1 byteでも変えると既存 campaign はすべて E1-stale」の理由は撤去後に偽になります。旧本文の改稿ではなく、後継決定で operational prohibition と理由を明示 supersede するのが妥当です。なお uncommitted 時の `current-closure-unavailable` と、B4/Layer3等の別pin影響は残るため、「閉包編集は無条件に無影響」とまでは書けません。

- D967 (`docs/decisions.md:34446`): 指定外ですが real な追加衝突です。「契約拡張で既存 campaign が E1-staleになることを正直なmigrationとする」は撤去後成立しません。D1163との関係を明示すべきです。

- D1128 (`docs/decisions.md:37981`): 判定器を同権限主体が無条件成功へ変更できる限界は残り、矛盾なし。

- D387 / D799: repo内testの偽造耐性上限、定数verdict二種だけを殺すという記述は不変。

- `docs/failures.md`: exact 3診断値の出現は0件。F357/F358のdirty-worktree偽赤は `current-closure-unavailable` が残るため現行でも正しい。F712の歴史scope/current scope分離も不変。

- 現行説明としては誤りになる historical insight:
  - `output/insights/2026-08-15_t817-verifier-epoch/README.md:15-16`
  - `output/insights/2026-08-17_t657-activation-rebuild/README.md:31`
  - `output/insights/2026-08-26_t1749-arm-source-binding/README.md:42`
  - `output/insights/2026-08-27_t1629-ratification-broker/verbatim/s4-ruling.md:96`

  これらは歴史資料なので逐語を改稿せず、現行索引側に D1163 supersession を表示するのが安全です。T1143 の `verbatim/` 群も同様です。

## 親 brief の誤り

1. `output/campaigns/` は「33 campaign dir」ではありません。30 directoryと3 summary fileです。さらに `output/insights/.../campaign-layout/` に legacy lock が2件あり、repo内 lock 母集合は32件です。これは既存test `test_artifact_admission.py:839` も exact に固定しています。

2. repo内32件が全E0という狭い結論は正しい一方、それを既存成果物全体へ一般化したのは誤りです。確認した外部永続rootには22 lockがあり、うち5件は現行24-path mapと完全一致するofficial campaign、17件は旧8/12-path記録です。

3. したがって「今この撤去で読めるようになる既存成果物は0件」は誤りです。Aの編集と同じcommitで比較を残した世界との差分は、少なくとも外部official 5件です。

4. production consumer は repository 全体で30件です。親プランの24は certified のみ、historical は `orchestrator/` 4件に加えて `tools/plotting/` 2件あります。

5. 「FROZEN_MANIFESTにcode pathが無いのでDW-O09/O10該当なし」は狭すぎます。23 frozen bytes自体は不変ですが、A/Lはcampaign closure、B4 projection closure、admission validator SHA、Layer3 generator SHAへ届きます。

## 総括

certified consumer 24件の列挙は正しいが、historical 2件と表示consumer 5面が漏れています。
外部official campaign 5件が実際の受理集合差であり、「既存0件」は撤回が必要です。
legacy reason readerは残すべきですが、repo内に実診断記録は0件です。
D956とD967は後継決定で明示 supersede すべきです。
実装・pytest・schema validationは実行していません。
