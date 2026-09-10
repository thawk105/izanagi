## 総括

実装着手は不可。最大の blocker は、v3 の `cross_binding_receipt_sha256` が現行設計では再計算されず、受領証が実成果物を実際には拘束しない点。次に、v1/v2/v3 の exact key set を schema ごとに分離しないと、凍結済み fixture を壊す。

親 brief の「pin 閉包は 3 件」は、関数分類器の移動対象としては正しい。ただし、逐語 reason、schema、v1/v2 fixture まで含めた実際の pin 閉包は 3 件ではない。brief の「全 fixture が `cells=[]`」は反証できた。

### Pin 閉包

| 対象 | 現在の分類 | 実装後の分類 | 判定 |
|---|---|---|---|
| C09 `trial_registry.assert_campaign_layer3_chain` | exclusion: different-module | checked | `orchestrator/tests/test_s8c_preregistration_invariant.py:100`。brief の 1 件目は正しい |
| C10 `autonomous_trial_completeness.verify_s8c_cross_binding` | exclusion: declared-unimplemented | exclusion のまま | `:104`。実装するだけでは移動しない。除外から削除し、CHECKS へ追加必須 |
| C10 `trial_registry.verify_s8c_cross_binding` | exclusion: declared-unimplemented | exclusion のまま | `:106`。上と同じ |
| C09 producer `assert_campaign_layer3_chain` | checked | checked | `:69`。変更不要 |
| C09 `trial_registry.assert_trial_registry_acceptance` | checked | checked | `:71`。変更不要 |
| C10 `trial_registry.assert_trial_registry_acceptance` | checked | checked | `:73`。変更不要 |
| C10 autonomous `assert_trial_registry_acceptance` | exclusion: different-module | exclusion のまま | `:102`。変更不要 |
| C10 autonomous `authoritative bytes reread` | exclusion: nonidentifier | exclusion のまま | `:103`。関数 pin ではない |
| C09 producer `layer3 report publish` | exclusion: nonidentifier | exclusion のまま | `:99`。変更不要 |
| C10 registry `registry append` | exclusion: nonidentifier | exclusion のまま | `:105`。変更不要 |

分類順序は `test_s8c_preregistration_invariant.py:241-269` の通り、declared-unimplemented が local symbol 判定より先。したがって、C10 の 2 件は実装後も exclusion のままだと exact assert `:321-329` は通るが、実装済み consumer の証明にならない。

`read_and_verify_bytes` は reachable token として分類される pin ではなく、`TOKEN_ONLY_C10` の文字列検査対象に過ぎない。

### B-01: aggregate digest が受領証の実成果物を拘束しない

深刻度: blocker

該当: `s2-plan.md:101-107`, `orchestrator/campaign/s8c_acceptance_receipt.py:887-912`, `orchestrator/campaign/trial_registry.py:2913-2934`

影響: `cross_binding_receipt_sha256` に任意の正しい形式の SHA-256 を入れても、既存の受領証検証は six report の内容との対応を再計算せず、受理集合が変わらないまま誤った成果物参照を受理する。

トップレベル配置自体は妥当。既存の受領証全体を一つの acceptance object として拘束でき、契約 JSON の `assert_trial_registry_acceptance.cross_binding_receipt_sha256` とも整合する。per-trial 配置なら trial key set の変更が必要で、receipt 外に出すなら既存 parser と `verify_acceptance_receipt` の信頼境界外になる。

ただし、トップレベルに置くなら次のどちらかが必要。

- six report digest の leaves を受領証に保存し、検証時に aggregate を再計算する
- 受領証検証時に six report の C10 projection を再読込し、各 digest と aggregate を再計算する

これがない v3 化は schema の外観だけを増やす変更になる。

### B-02: v1/v2/v3 の exact key set 分岐が必須

深刻度: must-fix

該当: `s2-plan.md:120-129`, `orchestrator/campaign/s8c_acceptance_receipt.py:23-53`, `:293-307`, `orchestrator/tests/test_s8c_acceptance_receipt.py:62-132`, `orchestrator/tests/test_layer3_report.py:309-322`

影響: 共通の `_TOP_LEVEL_KEYS` に新 key を追加すると、v1/v2 receipt が unknown key または missing key で拒否され、凍結済みの受理参照が失われる。

`LEGACY_SCHEMA_VERSION` は v1 のまま保持し、v2 用の key set と v3 用の key set を分ける必要がある。schema version を読む前に共通 key set を exact assert している `:304` の構造も変更対象。

v3 化そのものは必要。ただし「v2 を旧 schema として保存し、v3 だけ aggregate digest を必須にする」という設計に限る。

### B-03: dotted contract 名と実 record key が混同されている

深刻度: must-fix

該当: `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:399-429`, `orchestrator/campaign/s8c_preregistration_evidence.py:1657-1697`, `orchestrator/campaign/p3_autonomous_workload_trial.py:1746-1860`, `orchestrator/campaign/wal.py:98-110`, `orchestrator/campaign/layer3_report.py:304-312`

影響: `_C10_FIELDS` の flat 名を実 record の key として比較すると、評価器は green でも、実ファイル・WAL・Layer3 report 間の値が拘束されず、受理される参照集合が過大になる。

実際の対応は次の通り。

| 契約上の論理名 | 実際の保存形 |
|---|---|
| `role_event.input_payload_sha256` | role event の flat key `input_payload_sha256` |
| `provider.payload_sha256` | event の flat key `provider_payload_sha256`。path は `provider_artifacts.payload_path` |
| `provider.envelope_sha256` | event の flat key `provider_envelope_sha256`。path は `provider_artifacts.envelope_path` |
| `proposal.path` | proposal descriptor の `path` |
| `campaign_wal.build_records` | `WalRecord` の `variant/stage/env_tag/ts/payload` から作る projection |
| `layer3.artifact_refs` | Layer3 report の `artifact_refs`。campaign directory の実ファイル集合 |
| `layer3.source_refs` | WAL と loop state の canonical ref multiset |
| `layer3.runs` | raw WAL ではなく `_view_row` による projection |

特に WAL には `build_records` や `bench_records` という実 key はない。`layer3_report.py:113-145, 525-562` の projection と同じ正規化を C10 側でも使う必要がある。

### B-04: raw response の「存在確認」と「byte reread」が分離している

深刻度: must-fix

該当: `orchestrator/campaign/autonomous_trial_completeness.py:444-475`, `:1289-1333`, `orchestrator/campaign/p3_autonomous_workload_trial.py:1821-1860`, `s2-plan.md:48-57`

影響: `raw_response_path` と SHA の形だけを検査する現在の経路では、raw response を一 byte 改変しても受理できる。さらに `_bound_regular_bytes` は相対 path を `run_root/value` としてではなく process cwd 基準で解決する。

新 helper は少なくとも次を明示すべき。

- relative path は指定された campaign/run root に結合する
- absolute path は許可 root 内に正規化する
- 読み込んだ bytes の SHA を event の flat key と比較する
- provider、proposal、raw response の各 path で同じ境界検査を行う

### B-05: `do_build` と `cells` の分岐を誤ると既存 acceptance が巻き添えになる

深刻度: must-fix

該当: `s2-plan.md:29-44,97`, `orchestrator/tests/test_trial_registry.py:360-396`, `:672-787`, `orchestrator/campaign/autonomous_trial_completeness.py:2837-2843`, `orchestrator/campaign/p3_autonomous_workload_trial.py:2720-2736`

影響: no-build fixture に C09/C10 build gate を適用すると既存の成功・負例テストが本来のエラーではなく新 gate で赤くなり、逆に `cells` の有無だけで分岐すると `do_build=True,cells=[]` が chain 検査を通過する。

brief の「全 acceptance fixture が `do_build=False,cells=[]`」は誤り。`_base_report` は `cells=[]` だが、`_complete_report` は `:672-787` で一つの cell を生成する。

正しい設計は次の順序。

1. `do_build=False` なら C09 build chain を skip し、C10 は no-build projection を生成する
2. `do_build=True` なら `cells` が空であることを即時 reject
3. build cell がある場合だけ campaign root、WAL、loop state、Layer3 report を検査する

fixture 側で no-build の reason 期待値を更新するのは正しい。production 側で no-build を拒否するのは誤り。

### B-06: exact acceptance test の影響範囲がプラン記載より広い

深刻度: must-fix

該当:

- `orchestrator/tests/test_trial_registry.py:1006-1027`
- `orchestrator/tests/test_trial_registry.py:1541-1548`
- `orchestrator/tests/test_trial_registry.py:2562-2590`
- `orchestrator/tests/test_s8c_acceptance_receipt_v2.py:64-157,229-405`
- `orchestrator/tests/test_reflux_originless_compatibility.py:261,594-689,832-945`
- `orchestrator/tests/test_s8c_acceptance_receipt.py:62-132`
- `orchestrator/tests/test_layer3_report.py:309-322`

影響: schema version、top-level key、reason 配列の一つでも共有変更すると、v3 の成功 fixtureだけでなく v2 helper、v1 frozen baseline、reflux の v2-to-v1 projection が変わり、受理集合または互換参照が変わる。

具体的には次が確実に fixture 側で更新対象。

- `test_trial_registry.py:1006-1027` の v2 exact receipt
- `test_trial_registry.py:1541-1548` の partial reason exact assert
- `test_trial_registry.py:2581-2584` の no-build reason exact assert

`test_acceptance_v2_has_no_certifying_issuance_branch` の source pin `:2589-2590` は残すべきで、名称を変えても `certifying=True` の issuance branch を導入してはいけない。

一方、次は production を弱めず、旧 schema のまま維持するべき。

- `test_s8c_acceptance_receipt.py:62-132` の v1 fixture
- `test_layer3_report.py:309-322` の v1 receipt
- `test_reflux_originless_compatibility.py:261` の frozen baseline
- `test_reflux_originless_compatibility.py:681-689` の v1 projection

### B-07: `no-build` を mandatory reason 集合へ無条件追加してはいけない

深刻度: must-fix

該当: `s2-plan.md:40-44,160-164`, `orchestrator/campaign/s8c_acceptance_receipt.py:26-32,232-263`, `orchestrator/tests/test_trial_registry.py:1541-1548,2581-2584`

影響: `no-build` を `MANDATORY_NON_CERTIFYING_REASONS` に追加すると、build-mode の非 certify receipt まで一律拒否され、追加しないと no-build reason の欠落を parser が検出できない。

`no-build` は条件付き reason であり、現在の global mandatory 集合に入れる性質ではない。receipt の report projection または acceptance path で、`do_build=False` の場合だけ存在を要求する設計が必要。

### B-08: C10 build-mode 正例の all-in-one fixture は存在しない

深刻度: must-fix

該当: `s2-plan.md:191-208`, `orchestrator/tests/test_autonomous_trial_completeness.py:398-466,710-871,1092-1273,2797-2957`

影響: raw response、provider payload/envelope、proposal、campaign lock、WAL、loop state、Layer3 report を同一 trial に揃えた正例がないため、12 field の一つを取り残しても lexical evaluator と個別 helper test だけは green になり得る。

既存資産は分割されている。

- role event と no-build trial: `:398-466,652-707`
- registered proposal/campaign lock: `:710-871`
- provider payload/envelope reread: `:1092-1273`
- lock/loop/WAL/Layer3: `:2797-2957`

新規 fixture は中程度の工数。既存 helper の統合と、実ファイル path の整合、少なくとも各 field の mutation case が必要になる。小さい tmp campaign に限定すれば実行時間は fixture 数に比例する固定費だが、production acceptance の hash は campaign 内ファイル数と総 byte 数に比例する。

### B-09: テスト時間の退行は履歴比例ではないが、campaign file 比例になる

深刻度: nit

該当: `s2-plan.md:74-80`, `orchestrator/campaign/layer3_report.py:192-197`, `:448-566`

影響: repository 履歴全体を走査する退行は見えないが、six report ごとに `rglob("*")` と byte hash を行うなら、受入時間は campaign 内ファイル数・総サイズに比例して増える。

これは小さい fixture では許容可能。ただし C10 が repo root や全 `runs/` を探索する実装になった場合は must-fix へ格上げする。

### B-10: 並行 wave の行単位衝突は現行 ref では再現しない

深刻度: nit

該当: `/work/1/SFC/tanab/dev-wave-jobs/wave-t1348-c09-c10-consumer/s1-brief.md:127-132`

影響: 現在見える `git diff main...worktree-dev-wave-t1333-t1310-workload-profile` は空で、対象 3 file の行単位衝突や acceptance 集合の変更は確認できない。

`git worktree list` にも該当 worktree はなく、branch ref は既存 commit のみだった。外部で未 commit の編集がある可能性までは反証できない。

もし衝突が出た場合は、着地済みの t1333 perf closure を残し、C09/C10 の状態行を同じ snapshot に追加する形が正しい。C01 の設計テストを反転させる解決は不可。

### B-11: docs/dev-wave の変更はこの wave では不要

深刻度: nit

該当: `s2-plan.md:1-25,147-164`, `tools/check_docs.py:257-259`

影響: 現行 plan に docs/dev-wave の編集面はなく、成果物の受理集合や参照値は変わらない。新たに normative な説明を追加するなら、既存 budget を確認してから裁定へ戻す必要がある。

### 反証できなかった点

- 現在の C09/C10 が未達であること、既存 production に acceptance consumer がないことは反証できなかった。
- `output/s8c-trial-registry/` に tracked receipt がないことは確認できた。したがって、凍結済み実 receipt の直接更新漏れは現時点ではない。
- S8c acceptance receipt を読む追加 CLI consumer は見つからなかった。`tools/dev_wave_land.py` の receipt は別 schema の dev-wave receipt であり、今回の v3 変更対象ではない。
- contract JSON の dotted `field_paths` 自体は invariant evaluator の検査対象ではなく、`reachable_from` token と consumer entrypoint が分類対象であることは確認できた。

### 採用してよい部分

- C09 の chain check を digest chain 後、accepted append 前に置く方針
- `do_build=False` を明示的に no-build として扱い、certifying にしない方針
- `do_build=True` で空の `cells` を reject する方針
- C10 で authoritative bytes を reread する方針
- C09/C10 の build-mode missing chain を certify 不可にする方針
- v1/v2 fixture を凍結したまま、v3 を別 schema として追加する方針
- evaluator、contract JSON、condition freeze を変更しない方針。ただし C10 の declared-unimplemented exclusion 2 件は invariant の exact set から移す必要がある
- docs/dev-wave を変更しない方針

実装前に、少なくとも B-01、B-02、B-03、B-05、B-06、B-07、B-08 を解消する裁定またはプラン修正が必要。