## 前提の検算

射影の全ファイルと指定アンカーを読んだ。以下の略記は repo root 相対パスを指し、行番号は変更前のものとする。

| 略記 | ファイル |
|---|---|
| S | `orchestrator/campaign/paper_story_a1_source.py` |
| D | `orchestrator/campaign/paper_story_a1_paired.py` |
| J | `tools/pegasus/paper_story_a1_paired.sh` |
| TJ | `orchestrator/tests/test_paper_story_a1_job_contract.py` |
| TP | `orchestrator/tests/test_paper_story_a1_paired.py` |
| TC | `orchestrator/tests/test_campaign.py` |

P1〜P7を採用できる。ただし次を補正する。

- `rulings-verbatim.md` の「D1986 項5」は、現物の項4「B-4」の取り違えである。`docs/decisions.md:60073` の実際の項5は A-1 を対象とし、60077行の決定は brief の引用と一致する。親の逐語資料を訂正する対象であり、裁定内容の変更ではない。
- D:7126 の所属関数は `run_measurement` ではなく `_run_measurement_v3`（6976行開始）。外側の `run_measurement` は7256行開始で、CCBench 検査を7263行で行う。
- `_parent_porcelain` 自体は dirty submodule を拒否しない。親 status では submodule を無視し、`_assert_ccbench_acceptance` が submodule を直接検査する組合せである。
- shell の追加4 pathを pilot/sized 別に丸ごと複製すると、共通 module・patch の文字列出現数が6になり、TJ:435 の既存 `count == 3` を壊す。共通2 pathを各箇所に一度だけ記載する必要がある。
- terminal の閉包は **5+4=9 path**、non-certifying 閉包は **10+4=14 path**。この二種類を混同しない。

読み取りによる SHA-256 検算結果は以下のとおり。

| 対象 | SHA-256 |
|---|---|
| v1 source 契約 | `21477b74ad440f9eed8c27f78417f0469d757cb2bea2f579b2b212632b69f4b7` |
| sized policy | `a6228bcd5d2db3eca45fed6e148ab7ba92dd4d179f60e9c9c4ed0ffcf4942f1a` |
| sized 事前登録 | `6047eff005fbd94bad8df0313124bd4ca037dedf0f2e3db05224d04ad34fd3c2` |
| patch | `a5e0710c3f76744755b58ec66024c277daba00e49ce3cbf3d6d263cd7228580a` |
| pilot 追補 | `391e9425c0dec2ef33910b2112e7b1c5e5b650d6b6444c8c92285d5568a879c4` |

本段ではファイル変更、git 状態変更、pytest 実行を行っていない。brief の「462 passed / 135.72秒」は親の baseline 記録であり、本段の実測結果ではない。

## 契約表の設計

**S:11–28に pilot/sized の2要素表を置く。既存 pilot 定数と既存呼出しの既定値は維持する。**

具体形は次とする。driver を import せず、循環依存を避ける。

```python
PILOT_STUDY_ID = "paper-story-a1-20260901-balanced5-pilot-v1"
SIZED_STUDY_ID = "paper-story-a1-20260901-balanced5-sized-v1"

# CONTRACT_PATH / CONTRACT_SHA256 / SOURCE_PATHS は現行 pilot 値のまま。
SIZED_CONTRACT_PATH = "orchestrator/campaign/paper_story_a1_source.v2.json"
SIZED_CONTRACT_SHA256 = "<親が実ファイルから検算した値>"
SIZED_SOURCE_PATHS = (
    SIZED_CONTRACT_PATH,
    "orchestrator/campaign/paper_story_a1_source.py",
    "patches/silo-backoff-fixed.patch",
    "output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md",
)

CONTRACTS = {
    PILOT_STUDY_ID: (CONTRACT_PATH, CONTRACT_SHA256, SOURCE_PATHS),
    SIZED_STUDY_ID: (
        SIZED_CONTRACT_PATH, SIZED_CONTRACT_SHA256, SIZED_SOURCE_PATHS,
    ),
}
```

汎用レジストリ、登録API、3 study目の拡張機構は設けない。

関数変更は以下に限定する。

| 箇所 | 計画 |
|---|---|
| S:21 `load_contract` | `load_contract(repo_root, study_id=PILOT_STUDY_ID)`。表の path/SHA を選んで現行検算を行う |
| S:32 `binding_matches` | `binding_matches(files, *, study_id=PILOT_STUDY_ID)`。選択契約について現行と同じ3 digestを照合 |
| S:44 `SourceContext.__init__` | keyword-only の `study_id=PILOT_STUDY_ID` を追加し、契約選択に使う |
| S:68付近 `materialized` | `materialized(repo_root, *, base=None, study_id=PILOT_STUDY_ID)` とし、load と context に同じ study を渡す |
| S:60 `SourceContext.validate` | 変更不要。root、pin、期待 materialization は study 非依存 |
| S:84以降の依存関数 | `prepare_dependencies` / `configure_dependencies` は変更不要 |

`binding_matches` 内で `files` の余分なキーを新たに拒否しない。既存の `binding_matches(files)` は従来どおり pilot の3 digestだけを検査するため、その判定を維持できる。

driver の D:4860 では、既に `set(files) == set(relative_paths)` を確認した後で、**`relative_paths` に含まれる契約 pathから studyを選ぶ**。

```python
for study_id, (contract_path, _, _) in a1_source.CONTRACTS.items():
    if contract_path in relative_paths:
        if not a1_source.binding_matches(files, study_id=study_id):
            return False
```

既存の閉包完全一致が study間の混入を拒否する。別の ambiguity gate は足さない。pilot 検証では sized 契約を load せず、sized の新ファイル不備で pilot 判定が巻き添えになる構造を避ける。

新規 `paper_story_a1_source.v2.json` のキー集合は次の12個とする。

```text
schema_version
study_id
canonical_head
patch
patch_sha256
policy
policy_sha256
preregistration
preregistration_sha256
amendment
amendment_sha256
```

上記は列挙すると **11個**であり、実装・テストではこの列挙そのものを exact set とする。`attempt` は含めない。

値は以下とする。

- `schema_version`: `paper-story-a1-source/v2`
- `study_id`: sized の既存 ID
- `canonical_head` / patch / patch SHA: v1 と同一
- `policy`: `orchestrator/campaign/paper_story_a1_paired.v3-sized.json`
- `policy_sha256`: 上表の `a6228bcd…`
- `preregistration`: `output/insights/2026-09-13/paper-story-a1-balanced5-sized-preregistration/README.md`
- `preregistration_sha256`: 上表の `6047eff0…`
- `amendment`: P4の新 README
- `amendment_sha256`: 親が完成した README の実 bytes から取得

S:26の検算 loop は既に `patch / policy / preregistration / amendment` の4項目だけなので、`attempt` 不在による変更は不要。schemaやキー集合のための新しい実行時検査は足さず、契約 bytes pinと契約テストで固定する。

親 README完成 → amendment SHA確定 → v2 JSON確定 → v2 JSONのSHAを moduleへ設定、の順とする。凍結済みファイルは変更しない。

## driver 側の分岐置換

| アンカー | 具体変更 |
|---|---|
| D:2243–2244 | `study_id in a1_source.CONTRACTS` のとき、その行の `SOURCE_PATHS` を末尾へ追加 |
| D:2636–2639 | 契約を持つ study のうち、sizedは全attempt、pilotは現行どおり `attempt-0004` で契約 load と hydrate必須を適用 |
| D:3409–3415 | 契約を持つ study に共通化。契約 load と hydrate dir存在検査を双方に適用。attempt名照合だけ pilot に残す |
| D:4860 | 上節のとおり relative_paths 内の契約 pathから照合 studyを選ぶ |
| D:5219–5230 | `any(path in files for path, _, _ in CONTRACTS.values())` で既存 amended admission 検査を発火 |
| D:7126–7128 | `load_contract(repo_root, study_id)`。study一致検査を維持し、attempt照合はpilotのみ |
| D:7137 | `materialized(repo_root, study_id=study_id)` として同じ契約を実source生成へ渡す |

D:2636 の pilot attempt条件を保持する理由は、`_v3_group_intent` が既存受領証の再構成にも使われるためである。新規pilot submitの制限は D:3411 で維持する。pilotの過去attemptの intent にまで hydrate必須を遡及しない。

D:7126–7128 は次の分離を推奨する。

```python
contract_source = a1_source.load_contract(repo_root, study_id)
if study_id != contract_source["study_id"]:
    raise PaperStoryError("A1 source amendment study differs")
if study_id == V3_PILOT_STUDY_ID:
    if attempt.name != contract_source["attempt"]:
        raise PaperStoryError("A1 source amendment requires pilot attempt-0004")
```

pilot の既存 attempt拒否文言は維持し、sized が同文言で拒否される経路をなくす。sized に `attempt-0001` 固定は設けない。

**D:4979–5060 `_trace0_commands_match` は変更しない。**

sized の consumer経路は次のようにつながる。

1. `_source_relative_paths(sized)` が v2契約を含む。
2. D:4601付近の `_source_binding` がその pathを記録する。
3. D:4860で v2契約・patch・sized追補の digestを照合する。
4. D:5219で v2契約を認識し、admissionから `amended_source_root` を取得する。
5. D:5223–5230の既存検査を通ったrootが、D:5315から `_trace0_commands_match` に渡る。
6. 既存述語が `-S <root>` と所定位置のFETCHCONTENT 4 tokenを要求する。

admission不正時に `"invalid"` を渡して拒否へ進む現行動作も維持する。受理する configure argv の形は増やさない。

D:8565–8573の pilot限定 `sizing-pilot.json` 生成条件は変更しない。

## job script 側の分岐置換

対象は J:74–81、450–455、984–989、1361–1371。P1の「条件置換だけ」は、前3箇所では study別の契約・追補path選択も必要になる。その範囲に限定する。

最初のsource閉包は次の構造とする。

```bash
if [[ "$POLICY_RELATIVE" == "...v3-pilot.json" ||
      "$POLICY_RELATIVE" == "...v3-sized.json" ]]; then
  if [[ "$POLICY_RELATIVE" == "...v3-pilot.json" ]]; then
    SOURCE_CONTRACT_RELATIVE="orchestrator/campaign/paper_story_a1_source.v1.json"
    SOURCE_AMENDMENT_RELATIVE="output/insights/2026-09-11/t2397-a1-source-amendment/README.md"
  else
    SOURCE_CONTRACT_RELATIVE="orchestrator/campaign/paper_story_a1_source.v2.json"
    SOURCE_AMENDMENT_RELATIVE="output/insights/2026-09-17/t2590-a1-sized-source-amendment/README.md"
  fi
  NON_CERTIFYING_SOURCE_RELATIVE_PATHS+=(
    "$SOURCE_CONTRACT_RELATIVE"
    "orchestrator/campaign/paper_story_a1_source.py"
    "patches/silo-backoff-fixed.patch"
    "$SOURCE_AMENDMENT_RELATIVE"
  )
fi
```

実装では `...` を使わず、既存の完全な policy相対pathを記す。

J:450と984の埋込Pythonも同じ二値選択にする。各箇所で次の順に4 pathを追加する。

1. pilotならv1、sizedならv2の契約path
2. 共通module
3. 共通patch
4. pilot/sizedの追補path

Pythonの条件式で契約・追補だけ切り替えれば、共通module・patchは一箇所につき一出現で済む。pilot固有pathも各箇所に一出現となるため、TJ:435の既存 `count == 3` をそのまま維持できる。sizedの4 pathにも同じcount assertを追加できる。

J:1361のstaging条件は完全な2 policy pathのORにする。1362–1371の本体は維持する。

- hydrate元の絶対path・symlink検査
- 3依存directoryの存在・symlink検査
- `$DEPENDENCY_ROOT/fetchcontent/{name}-src` へのコピー
- `--third-party-source-root "$THIRD_PARTY_ROOT"` の引渡し

閉包の比較は二種類に分ける。

| shell箇所 | 比較対象 |
|---|---|
| J:74 の配列 | `_source_relative_paths(policy, non_certifying=True)`、14 path |
| J:450 / 984 のterminal生成 | `_source_relative_paths(policy, non_certifying=False)`、9 path |

文字列countだけでなく、両studyについて抽出した小さい配列構築部分を評価し、**tupleの順序込み**で比較する。terminal側だけpilot固定に残る変異を拒否できるassertにする。job全体のbuild実行は不要である。

## hydrate 入力

D:2636では、次の条件で既存の必須検査を適用する。

```text
study が2要素表に存在
かつ
(sized または pilot attempt-0004)
```

D:2625–2635の既存intentからの復元、canonical absolute path検査、qsub変数として不適切な文字の拒否は維持する。

D:3409–3415では、pilot/sized双方について `third_party_source_root` が指定され、directoryが存在することを要求する。検査失敗時にintentやqsubへ到達しないことをfixtureで確認する。

D:7129–7134はstudy非依存であり、sizedにもそのまま効く。

- intentの該当workloadが記録したhydrate元と環境変数を照合する。
- CLIのstaged rootを解決する。
- dependency prefixから導いたscratch親の `fetchcontent` と一致することを要求する。

J:575付近もintentと環境変数を照合済み。hydrate元のpathとscratchのstaged pathは役割が異なり、同じ文字列であることは要求しない。

## T-2081 の閉じ

P5のとおり新規のsource検査は不要である。以下の既存機構をsizedへ接続したことを示して閉じる。

| 境界・機構 | 現物と既存被覆 |
|---|---|
| submit / driver / consumer | D:2381–2420。v2だけ除外し、v3はstudy名によらずsubmodule HEADとtracked statusを直接検査 |
| 親statusの扱い | D:2423–2429。v3では `--ignore-submodules=all`、直後・別境界のsubmodule直接検査で補完 |
| job preflight | TJの `test_v3_ccbench_five_boundary_wiring_is_exact_M10` が直接status検査と拒否文言をpin |
| trace/perf直前 | `pipeline.py:1083–1105`。厳密な `SourceContext` 型確認後に `validate` |
| materialized source | S:44–64。元checkoutはpin＋tracked-clean、実build sourceはpin＋既存の期待materialization |

既存nodeidは以下。

- `TJ::test_v3_ccbench_tracked_clean_gate_is_real_and_reason_is_layer_specific_M10`
- `TJ::test_v3_ccbench_five_boundary_wiring_is_exact_M10`
- `TJ::test_v3_measurement_runs_one_selected_campaign_but_registers_exact_triple`
- `TC::test_canonical_build_source_state_accepts_exact_clean_checkout`
- `TC::test_canonical_build_source_state_rejects_pin_or_tracked_drift`
- `TC::test_balanced_build_boundary_is_one_guarded_trace_perf_wrapper`
- `TC::test_balanced_loop_binds_build_guard_to_campaign_policy_pin`
- `TC::test_a1_build_source_contract_rejects_caller_chosen_digest`

不足は、既存M10の実checkout試験がpilot policyを使う点である。新たなclone/build試験は増やさず、次を追加する。

- sized policyで `_assert_ccbench_acceptance` を直接呼び、Git応答だけをstubする。canonical＋tracked-cleanを受理し、tracked dirty／HEAD不一致／HEAD解決失敗を各境界で拒否する。
- `_parent_porcelain` が空でも、submodule dirtyで拒否されることを確認する。
- sizedで発行した `SourceContext` がpipelineへ届き、trace/perf双方で既存validateを呼ぶことを軽量fixtureで確認する。
- 元checkoutの未宣言dirtyと、契約patch由来のmaterialized差分を区別する。後者の許容をtracked-clean偽装で実現しない。

既存reference生成・tree比較は保持するが、bytes級同一性検査を新設・拡張しない。T-2081の記録では「既存機構のsized適用を確認」と記し、新規gateを実装したとは記さない。

## 回帰テスト案

**既存testの期待値変更は不要にする設計を採る。** fixture追加・引数対応が必要でも、既存assertは保持する。

| 既存test | 扱い |
|---|---|
| TJ:407 `test_non_certifying_source_closure_matches_shell_and_preserves_legacy_set` | 9/10の基底集合、pilot exact tuple、4 pathのcount=3を全保持 |
| TJ:477 `test_v3_ccbench_tracked_clean_gate_is_real_and_reason_is_layer_specific_M10` | pilotの既定引数を残し、現行試験を保持 |
| TJ:530 `test_v3_ccbench_five_boundary_wiring_is_exact_M10` | 境界・文言・呼出し数を保持 |
| TJ:2203 `test_v3_measurement_runs_one_selected_campaign_but_registers_exact_triple` | context内のgate/build/collect構造を保持。study引渡しassertを追加 |
| TJ:3412 `test_v3_submit_fans_out_exact_workload_triple_and_publishes_group_receipt` | pilot fixtureと3 workloadの期待値を保持 |
| TP:4736 `test_a1_amended_exact_configure_consumer_M5_M6` | 全変異と期待値を保持 |
| TP:4774 `test_a1_amendment_binding_rejects_single_changed_input_M8` | 既定pilot APIと3 digest照合を保持。sized版は別test |
| TPのsized policy/certificate/statistics試験 | 凍結値と計算期待値を全保持 |

追加testの候補名と内容は以下。

1. `TJ::test_sized_source_closures_match_job_and_driver`
   sizedの14/9 pathをliteral期待tupleと照合。shell3箇所の実効配列、順序、count=3を検証する。

2. `TP::test_sized_source_contract_pins_bytes_and_four_bindings`
   v2のSHA、exactキー集合、`attempt` 不在、4束縛を確認。tmp上のコピーで契約自体と各参照入力を一つずつ改変し拒否を確認する。

3. `TJ::test_sized_submit_requires_hydrate_and_preserves_attempt_names`
   TJ:3186のfixtureを参考にsized用fixtureを追加。sized policy/prereg、v2/module/patch/追補を実bytesで配置する。`attempt-0001` と `attempt-0002` を別tmpで通し、hydrate欠落・非directoryを拒否する。qsubはstubするが、submitの契約選択・hydrate検査は実関数を通す。

4. `TJ::test_sized_group_intent_requires_hydrate`
   `_v3_group_intent` を直接呼び、3 jobの変数への記録、記録済みintentからの復元、入力欠落拒否を確認する。

5. `TJ::test_sized_job_stages_hydrate_for_measurement`
   production shellの該当小区間を小さい3 directoryで実行し、`*-src` とmeasure引数を確認する。clone/buildは行わない。

6. `TJ::test_sized_measurement_routes_amended_source_and_hydrate`
   `_run_measurement_v3` を軽量fixtureで通す。契約load・study選択・hydrate照合は実行し、materializer/build/実campaignはstubする。gateとcampaignへ同じcontext rootを渡すことを確認する。env不一致・scratch不一致も拒否する。

7. `TP::test_sized_consumer_requires_amended_admission`
   sized armの整合した証拠を用意し、`_validate_arm` の正例を通す。root不一致、`tracked_clean=True`、pin不一致を一つずつ変更し、`amended-source-admission-mismatch` を確認する。configureは既存buildcacheのargv生成を使う。

8. `TP::test_pilot_published_source_binding_remains_accepted`
   公開済みpilot receiptのsource_bindingをそのまま使い、`binding_matches(files)` とpolicy付きbinding検証の正例を確認する。moduleの歴史SHAを現在SHAへ置き換えない。

9. `TJ::test_sized_ccbench_acceptance_rejects_dirty_source`
   前節の軽量なsized専用D1323被覆を追加する。

10. `TJ::test_pilot_attempt_pin_remains_enforced`
    新規pilot submit/measureでattempt-0004以外を拒否する。sizedのattempt自由化がpilotへ漏れないことを確認する。

受入5分について、baselineの135.72秒だけから変更後の上限内を保証しない。追加は小さいファイルfixture、stub、AST・配列評価に限定し、既存のclone/materialization試験をstudy数分に倍増しない。

## 変異 matrix の事前登録候補

以下は登録候補であり、KILLEDを実測した結果ではない。

| # | 変異対象（変更前アンカー） | 単一変異 | 期待KILLED nodeid |
|---|---|---|---|
| M1 | S:11–18 | 契約表からsizedを落とす | `TJ::test_sized_source_closures_match_job_and_driver` |
| M2 | S:21–24 | sizedの契約自体のSHA検算を外す | `TP::test_sized_source_contract_pins_bytes_and_four_bindings` |
| M3 | S:26–28 | sizedの4束縛の一つの検算を外す | `TP::test_sized_source_contract_pins_bytes_and_four_bindings` |
| M4 | D:2243–2244 | sizedの追加4 pathを落とす | `TJ::test_sized_source_closures_match_job_and_driver` |
| M5 | J:450または984 | terminal閉包をpilot限定へ戻す | `TJ::test_sized_source_closures_match_job_and_driver` |
| M6 | J:1361 | staging条件をpilot限定へ戻す | `TJ::test_sized_job_stages_hydrate_for_measurement` |
| M7 | D:5219 | amended admission発火条件をv1契約限定へ戻す | `TP::test_sized_consumer_requires_amended_admission` |
| M8 | D:3411または7127 | attempt-0004照合をsizedにも掛ける | `TJ::test_sized_submit_requires_hydrate_and_preserves_attempt_names`／`TJ::test_sized_measurement_routes_amended_source_and_hydrate` |
| M9 | D:2636–2639 | sizedのhydrate必須を外す | `TJ::test_sized_group_intent_requires_hydrate` |
| M10 | D:4860 | binding照合をv1契約限定へ戻す | sized版の `test_a1_amendment_binding_rejects_single_changed_input` |

「または」と記した行は、親が事前登録時に一箇所へ確定する。一回の変異で複数箇所を同時変更しない。M7は不正admissionの固有errorをassertし、別理由による偶然の拒否をKILLEDに数えない。

## 焦点テスト集合と影響範囲

直接参照とhelper経由を二段で追った結果は以下。

| 起点 | consumer・伝播先 |
|---|---|
| `a1_source` | Dの契約load、閉包、binding検証、admission、materialization、依存configure |
| `paper_story_a1_source` / `SourceContext` | `pipeline.py:1097` の型検査、TJの実materialization試験、TCの偽context拒否 |
| `a1_source_context` | `loop.py:373,395,765` → `pipeline.py:1593,1990,2623,2700` → build直前validate |
| `_source_relative_paths` | D:2957/2989のintent関連、4607/4620のbinding生成、4875/4885のbinding検証、6677/6701のobservation、7560のcurrent source検証 |
| binding検証helper | D:6574/6579のobservation内容、7705のv3 raw documents、7997以降のraw検証 |
| amended admission | `_validate_arm` → `validate_workload_evidence` → `collect_workload`／raw WAL再収集 |
| `_trace0_commands_match` | `materializer_admission.py:63` の既存consumer登録、`test_p3_build_authority_cli.py:178` の対応確認 |

`s8c_result_judge._source_binding_matches` は同名に近い別機構で、本変更のconsumerではない。

再走対象の中心は次の3ファイル全体とする。

- `orchestrator/tests/test_paper_story_a1_job_contract.py`
- `orchestrator/tests/test_paper_story_a1_paired.py`
- `orchestrator/tests/test_paper_story_a1_balanced_sizing.py`

加えて `test_campaign.py` は前掲のsource/build境界nodeidを選択して再走する。全ファイル走を5分受入へ無条件に追加しない。

横断検索で見つかった周辺参照は、次のファイルにある。

- `test_p3_build_authority_cli.py`
- `test_p3_exploration_namespace.py`
- `test_ccbench_spawn_sites.py`
- `test_official_perf_closure.py`
- `test_pegasus_tools.py`
- `test_hooks.py`
- `test_paper_story_a1_headline.py`

これらはconsumer登録、driver契約、spawn箇所、shell分類、変更対象pathの集合を扱う。本計画では登録・spawn・分類を変えない。関連assertを静的に確認し、author差分がそこへ及んだ場合に該当nodeidを再走対象へ追加する。

balanced sizingのtestはmodule直接参照ではなく `tools/size_paper_story_a1_balanced.py` / `tools/verify_paper_story_a1_balanced_sizing.py` を経由する。sizing成果物の回帰対象として既存焦点集合に残す。

## リスクと未確定点

**pilot履歴検証とcurrent checkout検証を区別する。**

公開pilot receiptの `source_binding` は9 pathを持ち、moduleの歴史SHA `0ba074af…` を記録している。現行 `binding_matches` が固定するのはv1契約・patch・pilot追補の3 digestである。module、driver、shellの現在SHAとの一致はここでは要求しない。この判定を維持すれば、本変更による履歴bindingの拒否を避けられる。

一方、D:7519 `_verify_current_source_paths` はexpected HEAD、blob OID、working bytesを既存どおり照合する。変更後checkoutで過去のpilot束を再materialize・再発行すれば拒否され得る。これは既存の境界であり、緩和しない。新規回帰testの成功を「変更後checkoutで全履歴処理が通る」と拡大解釈しない。

`configuration="a1-attempt-0004"` は、`s8b_expected_materialization.py:631–729` では非空文字列検査にのみ使われ、返すtree digestの原像には入らない。pilotラベルは保持し、sizedだけ `a1-balanced5-sized-v1` にすることを推奨する。新しい契約キーは不要で、2 study間のラベル選択に留める。

shellとPythonの順序は、基底10 pathの最後がrunner、その後が契約/module/patch/追補であることを固定する。terminal側は基底5 pathの後ろへ同じ4 pathを追加する。set比較だけではこの不変条件を示せない。

親が作るsized追補READMEの最小内容は次である。

- sized study ID、source追補であること、attempt固定を設けない適用範囲。
- 凍結済みsized policy・事前登録のpathとSHA、およびそれらを変更しない旨。
- canonical HEAD＋tracked-cleanの元checkout。
- 既存patchharnessによる隔離checkoutと指定patchだけの適用、patch SHA。
- trace/perf直前の既存期待materialization検査。
- 条件gateと両armが同じmaterializer contextのsourceを使うこと。
- patched sourceの証拠を実態どおり記録し、consumerがbinding/admissionを検査すること。
- gflags/glog、hydrate/staging/prebuild、configure条件の整合。
- verifier/anomaly、studyの測定条件・利用制限を変更しないこと。

v2契約と新READMEは本段では未作成なので、二つの新SHAは未確定である。仮値を実装完了値として扱わず、親の実ファイル検算で確定する。

## 総括

2 studyの固定契約表を中心に、driverの契約選択、shellの3閉包とstaging、hydrate入力、consumerのamended admission発火を一単位で揃える。pilotのv1 bytes・閉包順序・3 digest判定・attempt制限と、既存configure述語は保持する。

T-2081は新規gateを足さず、既存5境界がsizedへ接続されることを試験と記録で閉じる。実装・回帰試験・変異試験は未実施であり、本段の成果は静的検算に基づく実装計画である。