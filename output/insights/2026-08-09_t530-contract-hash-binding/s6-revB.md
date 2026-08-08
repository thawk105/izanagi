結論は **NO-GO** です。production の must-fix が3件あります。親実測の7赤は、いずれも既存テストの期待が誤っているとは立証できず、実装差分側へ帰属します。pytest は実走していません。

## 実所見

### B-01 — S1 raw reader が新 identity へ迂回する scope 逸脱

- 対象: [s1_direct_comparison.py:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_direct_comparison.py:214)、[s1_report.py:329](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_report.py:329)
- 判定: **real — must-fix**

```python
# s1_direct_comparison.py
return ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))

# s1_report.py
layout = layout_for(document, role, output_root=output_root)
records, line_issues, truncated_tail = wal.read_records_collected(layout)
```

`config_for()` の変更が共有 `layout_for()` を介して、明示的に scope 外とされた raw reader `s1_report` の探索先IDまで T530 化しています。これは「writer だけの変更」ではありません。

- 成果物影響: S1 report の `schedule_gate`、`samples`、campaign path参照が旧policy-bound campaignから新H-bound/不在ディレクトリへ変わり、レポートの受理集合と後続参照が変わります。
- 修正案: contract bind は `run_role()` の認可後writer経路だけに置く。`s1_report` が使う `layout_for()` はwave前の導出を維持し、新T530成果物のraw report対応は裁定済みの別waveへ返す。

### B-02 — trigger site projection が競合hashを黙って上書きする

- 対象: [p3_s4_loop_trigger_gating.py:328](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:328)、[同:471](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_s4_loop_trigger_gating.py:471)
- 判定: **real — must-fix**

```python
existing_contract = cfg.search_config.get(ENVIRONMENT_CONTRACT_SEARCH_KEY)
if existing_contract is not None and existing_contract != contract.contract_sha256:
    cfg = replace(cfg, search_config={
        key: value for key, value in cfg.search_config.items()
        if key != ENVIRONMENT_CONTRACT_SEARCH_KEY
    })
...
return ident.bind_environment_contract(cfg, contract)
```

これは [ident.py:61](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/ident.py:61) の「既束縛値が違えば拒否」を迂回します。また `default_cfg()` は既存 `_lookup` seam ではなく直接ambient lookupします。

```python
return ident.bind_environment_contract(cfg, env_contract.lookup(ENV_TAG))
```

- 成果物影響: H_Aに事前束縛された要求がH_B campaignとして受理され、campaign-id、lock、WAL/台帳参照が要求と異なるH_Bへ移ります。逆にambient registryに固定tagがない正当なsite contractは成果物作成前に拒否されます。
- 修正案: `default_cfg()` は未束縛の純粋configに戻し、site解決後に一度だけbindする。既存Hは削除せず不一致を拒否し、注入layoutも最終campaign-idとの一致を検査する。

### B-03 — autonomous producer/offline consumer がambient current Hを再計算する

- 対象: [p3_autonomous_workload_trial.py:549](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/p3_autonomous_workload_trial.py:549)、[autonomous_trial_completeness.py:1130](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/autonomous_trial_completeness.py:1130)
- 判定: **real — must-fix**

```python
return ident.bind_environment_contract(
    cfg, env_contract.lookup("linux-baremetal"),
)
```

そのIDで先にlayoutを作り、後でsiteを再解決するtrigger driverへ渡しています。

```python
campaign_id = prepared.campaign_id
layout = exploration_campaign_layout(campaign_id)
...
drive(cfg, ..., layout=layout)
```

offline completenessも同じambient helperで期待IDを再計算します。

```python
expected_cfg = producer._campaign_for(...)
if campaign_id != str(producer.ident.campaign_id(expected_cfg)):
    _fail(...)
```

- 成果物影響: 認可契約がH_AからH_Bへ変わると、H_Aで作成済みのreportが拒否されます。また実行中に解決Hが異なると、cellの`campaign_id/root`とtrigger lock/WALのidentityが分裂し得ます。
- 修正案: `_campaign_for()` に明示contract/Hを渡し、ID・layoutより前に一度だけ確定する。offline検証はcurrent lookupではなくcampaign.lockに束縛されたHをever-active解決して再構成する。世代切替方針そのものはT657へ残す。

### B-04 — guided lane指定のcaller取り残しと偽の正例

- 対象: [test_guided.py:280](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_guided.py:280)、[同:382](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_guided.py:382)、[test_campaign.py:1001](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:1001)
- 判定: **real — 成果物severityはnit。ただし既知赤なのでland前修正必須**

```python
ident.ensure_resumable_wal(..., admission_policy=guided._NO_BUILD_POLICY)
ident.ensure_campaign_identity(..., admission_policy=guided._NO_BUILD_POLICY)
```

両方とも `require_environment_contract=False` が欠落しています。さらに新しいguided正例は、public resume経路ではなくvalidator単体しか呼びません。

```python
records = wal.read_records(guided)
wal.validate_commit_contract_bindings(records, campaign_lock=guided_lock)
```

- 成果物影響: 現行productionの`guided.cmd_start/cmd_evaluate`は正しくfalseを渡すため、durable成果物への現在影響はありません。したがってproduct severityはnitです。
- 修正案: 2 fixture callerへ明示laneを渡す。正例は`ensure_resumable_wal(..., False)`またはguided public commandを通し、lock照合・repair・terminal readまで検査する。

### B-05 — 歴史ID定数は残ったが、exact pinが弱体化した

- 対象: [test_campaign.py:344](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:344)、[test_p3_autonomous_workload_trial.py:311](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_p3_autonomous_workload_trial.py:311)、[test_p3_s4_loop_trigger_gating.py:592](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_p3_s4_loop_trigger_gating.py:592)、[test_s8a_trigger_sweep.py:299](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_s8a_trigger_sweep.py:299)
- 判定: **real — nit**

例:

```diff
- assert current == _T343_REPRESENTATIVE_CAMPAIGN_ID
+ assert _T343_REPRESENTATIVE_CAMPAIGN_ID != historical
+ assert current == _T530_REPRESENTATIVE_CAMPAIGN_ID
```

同様に、T343/T428は`disjoint`、`len(set)==3`、`endswith`、同一ファイル内literal同士の比較へ弱まりました。定数自体は削除されていませんが、任意の別文字列へ変えても多くが緑になります。

- 成果物影響: production成果物は直接変わらないためnit。ただし歴史campaign参照の監査pinが漂流しても検出できません。
- 修正案: admission-bound/no-HのT343 preimage、T428 descriptor preimageを明示構成し、完全なIDを再計算してexact比較する。

### B-06 — `_T530_*` 定義は明示的だが、実行側がambient authorization

- 対象: [test_campaign.py:88](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:88)、[同:98](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:98)、[同:3247](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:3247)
- 判定: **real — nit**

固定値の定義自体はgeneration-1とliteral hashなので適切です。しかしwriter testはcurrent authorizationを使います。

```python
_T530_CONTRACT = ec.GENERATIONS["linux-baremetal"][0].contract
authorization = ec.authorize("linux-baremetal")  # ambient current
...
assert commit["contract_sha256"] == _T530_CONTRACT_SHA256
```

matching-resume正例もgeneration-1 lockにambient `_AUTHORIZATION` を渡しています。

- 成果物影響: production成果物は不変。linux contract世代更新時にgoldenが偽赤になるためnitです。
- 修正案: 固定golden用authorityもgeneration-1へ明示固定するか、writer伝播テストは「認可されたcontractのhash」と比較し、固定ID vectorとは分離する。

## scope 4ファイルの個別判定

- [artifact_admission.py:604](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/artifact_admission.py:604): **refuted**。historical branchは`historical-not-reclassified`を返して終了し、新しいtopology呼出しは [同:646](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/artifact_admission.py:646) のpost-policy側だけです。成果物影響なし。修正不要。
- [screening_driver.py:101](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/screening_driver.py:101): **refuted**。authorization取得後のwriter/resume configとlayoutだけをbindしています。offline `read_records_collected` readerは新設していません。成果物影響なし。修正不要。
- [s1_direct_comparison.py:214](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/s1_direct_comparison.py:214): **real**。B-01のとおり共有`layout_for`経由でraw reportまで変更しています。
- [guided.py:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/guided.py:172): **refuted**。productionのstart/evaluate双方が`require_environment_contract=False`を明示し、guided受理集合を維持しています。成果物影響なし。テストcallerのみB-04。

その他の禁止事項も **refuted** です。

- S8b private lock/reportファイルは差分なし。
- qualification event sink payloadは [pipeline.py:1035](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/pipeline.py:1035) と [同:1090](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/pipeline.py:1090) のままHを持ちません。
- mode-noneは [loop.py:75](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/loop.py:75) で`(contract, None)`を返し、receiptを発行しません。
- identityへ入るのは [model.py:27](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/campaign/model.py:27) のscalar Hだけです。`generation`はcontract外の`GenerationEntry`にあり、identityへ直接入りません。

## 実測赤7件の帰属

| 系統 | root cause | 帰属 | テストが守る不変条件 |
|---|---|---|---|
| guided 2件 | `test_guided.py:280,382`のlane指定漏れ | 実装wave側のcaller/fixture取り残し | repair順序、atomic loserがmeta/WALへ触れないこと。現在も必要 |
| trigger gating 4件 | `default_cfg()`が注入済み`_lookup`より前にambient `env_contract.lookup`を呼ぶ | production実装側 | siteで解決した同一contractがmeasurement/reject sinkへ流れること。現在も必要 |
| exploration namespace 1件 | 同じambient lookupがpublic CLIのbuild-context spyより前に発火 | production実装側 | exact `BuildRunContext`と注入authorityがbuild sinkまで届くこと。現在も必要 |

したがって、テスト側の期待が誤りとできる系統はありません。

## caller / consumer 全件監査

- `ensure_resumable_wal`: productionは `guided.py:199`（unbound明示）、`loop.py:147`、`s1_direct_comparison.py:252`、`screening_driver.py:111,165`（後4件はH-bound）。testは`test_campaign.py:782,804,1186`、`test_screening_driver.py:303`がH-bound、`test_guided.py:280`だけB-04。
- `ensure_resumable_attempts`: `p3_s4_loop.py:882,1002`、`p3_s4_loop_sort.py:240,326`、`p3_s4_loop_trigger_gating.py:565,743`、`s6_sort_sweep.py:279`、`s8a_trigger_sweep.py:381`。全件Hを渡しますがtriggerのH生成はB-02です。
- `canonical_preimage`: `ident.py:196`はcertified既定、`:225,305`はlane boolを伝播。guided testの`test_guided.py:100,348`はfalse明示。それ以外の直接callerは各`_bound/config_for/default_cfg`経由でH-boundです。例外は意図的欠落拒否`test_campaign.py:371`と、ambient問題の`test_p3_autonomous_workload_trial.py:171`です。
- `verify_against_lock`: production内部`ident.py:291,318`はlaneを伝播。直接test `test_campaign.py:643,647,662`はH-boundです。
- 追加確認した`ensure_campaign_identity`: production guidedはfalse、他はH-bound。`test_guided.py:382`だけ指定漏れです。
- 19 production外のconsumerでは、`s1_report.py:339`がB-01、`autonomous_trial_completeness.py:1130`がB-03です。その他のdirect-ID consumerに取り残しは見つかりませんでした。
- `_validate_attempt_topology`の4 callerは`artifact_admission.py:646`、`wal.py:1340,1435,1450`で、全件`campaign_lock`を渡しています。

## 変更テスト9ファイル

| ファイル | 判定 |
|---|---|
| `test_autonomous_trial_completeness.py` | B-05。T428定数は残るが現行preimageからのexact pinを失った |
| `test_campaign.py` | B-05/B-06。新規検査自体は強い |
| `test_critic.py` | **refuted**。fixtureのenv/H追加のみ |
| `test_guided.py` | B-04。assert緩和はないがcaller取り残し |
| `test_p3_autonomous_workload_trial.py` | B-05。T343 pinが`len(set)==3`へ弱化 |
| `test_p3_exploration_namespace.py` | **refuted**。期待layoutのH追随のみ |
| `test_p3_s4_loop_trigger_gating.py` | B-05。既存動作assertは維持され、4赤は有効 |
| `test_s8a_trigger_sweep.py` | B-05。T343 exact derivationがdisjointだけになった |
| `test_screening_driver.py` | **refuted**。fixture COMMITのH/env補完のみ |

skip、xfail、test削除、非ID挙動assertの削除はありません。

## 二重runner

- 対象: [test_campaign.py:7951](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t530-contract-hash-binding/orchestrator/tests/test_campaign.py:7951)
- 判定: **refuted**

新設14テストはすべて引数なしの`def test_*():`です。fixture、parametrize、pytest専用例外を使わず、`_run()`の`globals()`自動収集に入ります。

- 成果物影響: なし。
- 修正案: なし。

## 総括

- must-fix: B-01 — S1 raw reportを新identityへ迂回させるscope逸脱。
- must-fix: B-02 — triggerが競合Hを削除して再束縛し、ambient seamも迂回。
- must-fix: B-03 — autonomous producer/completenessがcurrent Hを再計算。
- nit: B-04 — guided productionは正しいがtest caller 2件と正例が不完全。
- nit: B-05 — T343/T428定数は残るがexact historical pinが弱体化。
- nit: B-06 — 固定T530期待とambient authorizationが混在。
- refuted: artifact historical分類、screening writer、guided productionのscope逸脱。
- refuted: S8b、qualification ledger、mode-none receipt、raw generation identity追加。
- refuted: skip/xfail/test削除、非ID挙動assert削除。
- refuted: 新設14テストの素Python runner非収集。
- 親実測7赤はすべて実装差分側へ帰属し、期待値変更で直してはならない。
- pytestは実走しておらず、緑とは判定していません。