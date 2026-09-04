## 前提の検算

- production anchor A1-A9 は概ね正しい。`build_approved_manifest` の定義開始は `orchestrator/campaign/s8b_oracle_manifest.py:1198` で、実 gate は `:1205-1206`、gate 後の構築は `:1245-1255` である。
- test anchor T4 の helper 定義は `orchestrator/tests/test_s8b_holdout_freeze.py:1963`。`:1985` は helper 内の cell field である。
- T5 は decorator が `:2155`、test 定義が `:2160` であり、既存 test が v2 candidate 経路の実導出を検査済みという親の訂正は正しい。
- T7 は不足している。`test_s8b_oracle_manifest.py:1579,1595,1795,1836` が未記載だった。
- さらに caller file 自体が 1 本不足している。`orchestrator/tests/test_s8b_oracle_driver.py:2336,2347` も `build_manifest` / `write_manifest` を直接呼ぶ。

repo 全体の production `.py` を呼出し式で数え直すと、直接 call は `load_ratified_freeze` 9 箇所、`reverify_published_freeze` 3 箇所、`launch_validate` 2 箇所である。

| 入口、直接 call | 選択 identity | 判定根拠 |
|---|---|---|
| `s8b_oracle_report.py:2540` `main`、`:2547-2550` | 未強制 | `reverify_published_freeze` は `ReverifiedFreeze` を渡す `s8b_ratified_freeze.py:3658-3668`。選択 gate は `result_type is LaunchValidatedFreeze` のときだけ発火する `:3303-3321` |
| `s8b_oracle_judge.py:740` `main`、`:749-750` | 未強制 | 同上 |
| `s8b_verdict.py:823` `main`、`:828-829` | 未強制 | 同上 |
| `p3_autonomous_workload_trial.py:4710-4715` `run_trial` C06 | 未強制 | load の後は budget 入力へ直結し、狭い API も launch も呼ばない |
| `s8b_oracle_manifest.py:1198` `build_approved_manifest`、`:1205-1206` | 強制済み | load 直後に `assert_g1_floor_selection_identity` |
| `s8c_result_judge.py:2075-2081` `_load_selection_checked_ratified_floor` | 強制済み | load 直後に狭い API。consumer は `:2129` と `:2213` |
| `s8b_oracle_driver.py:594` `gate_check`、`:644,664` | 強制済み | v2 は同じ candidate を `launch_validate` へ渡す |
| `s8b_oracle_driver.py:1335,1351` `run_block` | 強制済み | load 後に launch |
| `s8b_oracle_driver.py:402` `_gate_check_core`、`:496` | 単独では未強制 | private core 内の load 自体は identity を強制しない。ただし public v2 経路は `gate_check:641-677` または検証済み object の `:687-710` を経由する |

したがって親の「未強制は 4 群、report / judge / verdict / C06」という母集合には過不足がない。ただし driver 行で `:496` 自体を launch 強制の根拠とするのは不正確で、強制根拠は `:664`、`:1351`、および validated object を要求する `:687-710` である。

## (c) のプラン

1. `orchestrator/campaign/s8b_oracle_manifest.py` を次のように改名する。

   - `:818` `build_manifest` → `_build_manifest`
   - `:842` `build_manifest_from_ratified` → `_build_manifest_from_ratified`
   - `:902` `write_manifest` → `_write_manifest`
   - `:1245` の内部 call も `_build_manifest_from_ratified` へ変更
   - `:1198` `build_approved_manifest` は唯一の public builder として維持
   - `_atomic_create_json:872` と `_write_approved_manifest:923` の意味、serializer、create-only 動作は変更しない

   `build_manifest_from_ratified` も private にする。exact `RatifiedFreeze` 型の要求 `:849-850` は選択 identity の証明ではなく、この関数自身は `assert_g1_floor_selection_identity` を呼ばないため、public のままでは迂回口が残る。

2. 改名が必要な全 test caller は次の 25 箇所である。

   - `orchestrator/tests/test_s8b_oracle_manifest.py`
     - `build_manifest` 9 件: `:196,424,469,571,607,657,858,1579,1795`
     - `write_manifest` 11 件: `:402,410,443,489,528,551,630,780,801,1595,1836`
   - `orchestrator/tests/test_s8b_oracle_report.py`
     - `build_manifest` 2 件: `:268,391`
     - `write_manifest` 1 件: `:402`
   - `orchestrator/tests/test_s8b_oracle_driver.py`
     - `build_manifest` 1 件: `:2336`
     - `write_manifest` 1 件: `:2347`

   これらは test fixture の低位構築面として `_build_manifest` / `_write_manifest` へ機械的に置換する。test 名、入力、期待値、例外型は変更しない。`build_manifest_from_ratified` の test caller は 0 件で、production 内部の `s8b_oracle_manifest.py:1245` だけを直す。

3. 公開迂回口の負例は `orchestrator/tests/test_s8b_oracle_manifest.py:1247`、現行 parser test の直前へ置く。

   ```python
   @pytest.mark.parametrize(
       "public_name",
       ("build_manifest", "build_manifest_from_ratified", "write_manifest"),
   )
   def test_ungated_manifest_apis_are_not_public(public_name):
       with pytest.raises(AttributeError):
           getattr(manifest, public_name)
   ```

   拒否の含意: 選択 gate を持たない旧 3 名は module の public attribute として解決できず、旧 caller は構築または保存へ到達できない。  
   受理の含意: `build_approved_manifest` は残り、既存正例 `test_build_approved_uses_one_active_snapshot_and_writes_valid_candidate` `:1395-1436` が gate 済み snapshot から candidate を構築、保存、再検証できる。

## (d) のプラン

- 実 earlier official run は `_build_launch_repo` の repo に追加できる。`test_s8b_ratified_verify.py:677-699` は `test_s8b_ratified_freeze.build_production_emitter_g1` へ委譲し、下位 fixture は run paths と文書を `test_s8b_ratified_freeze.py:1033-1048`、既存 admission 台帳を `:1069-1080`、選択済み artifact を `:1083-1088`、G/A topology を `:1147-1179` に用意している。
- production admission は campaign run ごとに measurement generation を導出する `s8b_holdout_admission.py:1495-1499`。新規 reservation は過去の effect-key claim を排他条件にしない `:1618-1620` ため、既存 selected-run 台帳を削除せず earlier run を追記できる。
- helper の共有 module 移動は不要。既存 `_install_real_floor_selection_runs` `test_s8b_holdout_freeze.py:1963-2107` はそのまま残し、launch fixture 固有の小さい helper を `test_s8b_ratified_verify.py:887` の直後へ追加する。したがって `test_s8b_holdout_freeze.py` と `s8b_v2_freeze_fixture.py` は編集しない。

追加 helper は次の順に処理する。

1. `freeze.document["floor_source"]["path"]` と `topology["paths"]` から selected run、同じ env/proto8 の `20260718T115959Z-*` earlier run を決める。
2. selected の `manifest.json` を earlier run へ複製し、空の `journal.jsonl` を作る。selected artifact は一切書き換えない。
3. canonical v1、`topology["protocol"]`、manifest cells/schedule から admission cell を作り、`reserve_floor_holdout_observations`、`finalize_floor_holdout_admissions`、各 session の `consume_attempt_ticket` を通す。既存 `.git/izanagi/s8b-holdout-admission-v1` は削除しない。
4. `session-start` と `session` を `journal.jsonl` へ順次書き、production `inspect_floor_holdout_admission_evidence` で `derived_eligible_for_refreeze is True` を確認する。
5. selected result を複製し、`eligible_for_refreeze=False`、earlier run 用 `holdout_admission`、正しい `manifest_sha256` を設定して `result.json` を作る。自己申告 false でも実導出 true となる fixture にする。
6. earlier run id と protocol hash に一致する `launch_certificate.json` を作る。これで要求された 4 artifact と admission 台帳がそろう。
7. earlier artifact を commit し、その HEAD を `activation_head` とする新しい `RatifiedFreeze` を返す。`generation_commit` と generation document は変えない。

既存 stub 版 `test_launch_validate_rejects_floor_selection_rule_mismatch` `:854-869` と `test_g1_selection_helper_rejects_rule_mismatch` `:872-886` は行内容、期待 reason/cause、monkeypatch を変更しない。その直後に別 node として次を追加する。

- `test_launch_validate_rejects_genuine_derived_earlier_floor_selection_rule_mismatch`
  - `M.launch_validate(freeze, root)` を呼ぶ。
  - `reason == "floor-selection-rule-mismatch"`、`cause == "earliest-eligible-official-run-id/v1"` を維持する。
  - 実経路は `s8b_ratified_freeze.py:3303-3321` から `s8b_holdout_freeze.py:1949-1963`、`:1849-1853`、`:1865-1925`。
- `test_g1_selection_helper_rejects_genuine_derived_earlier_floor_selection_rule_mismatch`
  - `M.assert_g1_floor_selection_identity(freeze, root)` を呼ぶ。
  - 同じ reason/cause を要求する。
  - 実経路は `s8b_ratified_freeze.py:3638-3655` から同じ holdout 導出へ入る。

実体を名指しするため、各新 test は invocation 前に `HF._derive_floor_selection_eligibility.__code__` を捕捉し、`sys.setprofile` でその exact code object の call frame と `result_rel` を記録する。例外後に記録が `[earlier_rel]` と完全一致することを assert し、`finally` で従来 profiler を復元する。導出関数、共有判定関数、inspector は monkeypatch しないため、両層が stub のままなら exact code frame が観測されず赤になる。

## (b) のプラン

production 実装は追加しない。親の docs 記録には次を純増で置く。

- 未強制母集合は 4 群: `s8b_oracle_report.py:2547-2550`、`s8b_oracle_judge.py:749-750`、`s8b_verdict.py:828-829`、`p3_autonomous_workload_trial.py:4710-4715`。
- 前 3 群は scope (a)、C06 は scope (e) に属し、本 wave では gate を追加しない。
- 強制済み対照は `s8b_oracle_manifest.py:1205-1206`、`s8c_result_judge.py:2075-2081`、driver の `:644-664,1335-1351`。
- `s8b_oracle_driver.py:496` は単独の強制点ではなく、public v2 wrapper の制御フローによって強制済みと分類する。
- `reverify_published_freeze` は `ReverifiedFreeze` を使うため、選択 identity 済みとは数えない。

worklog fragment の一意 path と `base:` digest は親が land 先 main から割り当てる。stable な更新対象は現行 T-2067 carry の `docs/worklog.md:2900`、insight は新規 `output/insights/2026-09-03_t2067-bcd-selection-closure/README.md:1` を想定する。brief の指示どおり、author はこの docs 面を編集しない。

## 編集面と所有単位

| file | 種別 | 所有単位 |
|---|---|---|
| `orchestrator/campaign/s8b_oracle_manifest.py` | production | manifest の低位構築、保存、approved public API |
| `orchestrator/tests/test_s8b_oracle_manifest.py` | test | manifest 単体 fixture、公開 API 閉包の負例 |
| `orchestrator/tests/test_s8b_oracle_report.py` | test | report fixture 用 manifest 構築 |
| `orchestrator/tests/test_s8b_oracle_driver.py` | test | driver fixture 用 manifest 構築 |
| `orchestrator/tests/test_s8b_ratified_verify.py` | test | launch validation と狭い consumer API の genuine 負例 |
| `docs/spool/worklog/<親が割り当てる一意 fragment>.md` | docs | 親所有の T-2067 記録 |
| `output/insights/2026-09-03_t2067-bcd-selection-closure/README.md` | docs | 親所有の静的検算、実測結果 |

`orchestrator/campaign/s8b_ratified_freeze.py`、`s8b_holdout_freeze.py`、`orchestrator/tests/test_s8b_holdout_freeze.py`、`s8b_v2_freeze_fixture.py` は参照のみで編集しない。

## 波及と焦点走

構造検査への影響は次のとおり。

- `test_ccbench_spawn_sites.py:194-203` は holdout/ratified の process site 数を pin する。今回の production 編集は manifest の関数名 3 個だけで process call を増減しないため更新不要。
- `test_official_perf_closure.py:66,72,206-225` は holdout/ratified の perf predicate を列挙する。両 production file は不変で、manifest 改名は perf token を導入しないため更新不要。
- `test_s8c_preregistration_invariant.py:54,81,88,112-128` は ratified function 名を pin する。該当名を変更しない。`:623-644` の holdout scan に対しても、新規 test fixture は三軸 literal を追加しない。
- `test_s8c_preregistration_predicates.py:29-34,535,1164-1166` は ratified path と `load_ratified_freeze` token を使う。変更対象外なので更新不要。
- `_GENERATOR_SOURCES` `s8b_oracle_manifest.py:65-73` は manifest 自身を pin していないため、凍結成果物 bytes の更新は不要。

変更 production file の test consumer 集合は、次の grep 相当で引く。

```text
rg -l '\bs8b_oracle_manifest\b|s8b_oracle_manifest\.py' orchestrator/tests/test_*.py
```

得られる焦点走対象は以下の 13 file。

```text
orchestrator/tests/test_s8b_binding_driftguards.py
orchestrator/tests/test_s8b_experiment_numbers.py
orchestrator/tests/test_s8b_holdout_admission.py
orchestrator/tests/test_s8b_materialization.py
orchestrator/tests/test_s8b_oracle_artifacts.py
orchestrator/tests/test_s8b_oracle_driver.py
orchestrator/tests/test_s8b_oracle_judge.py
orchestrator/tests/test_s8b_oracle_manifest.py
orchestrator/tests/test_s8b_oracle_manifest_contract.py
orchestrator/tests/test_s8b_oracle_n_pilot.py
orchestrator/tests/test_s8b_oracle_report.py
orchestrator/tests/test_s8b_ratified_freeze.py
orchestrator/tests/test_s8b_verdict.py
```

これに直接編集する `orchestrator/tests/test_s8b_ratified_verify.py` と、上記 4 構造検査 file を加える。新規 test file は作らないため、test file 集合を列挙するメタテストの更新対象はない。

## 変異事前登録の候補

| 変異 | 対象 | 期待する赤 | 単独性 |
|---|---|---|---|
| `_build_manifest` の直後へ `build_manifest = _build_manifest` を一時追加 | `s8b_oracle_manifest.py:818` | 新しい public-name 負例の `build_manifest` case | clean。attribute lookup の前後に別 gate はない |
| `_build_manifest_from_ratified` の直後へ旧 public alias を追加 | `:842` | 同 `build_manifest_from_ratified` case | clean。exact RatifiedFreeze 型検査は選択 gate ではなく、alias の存在を拒否する別層もない |
| `_write_manifest` の直後へ `write_manifest = _write_manifest` を追加 | `:902` | 同 `write_manifest` case | clean。保存を呼ばず public surface の存在だけを一点検査する |
| `_derive_floor_selection_eligibility` の `return inspection.derived_eligible_for_refreeze` を `return False` に変更 | `s8b_holdout_freeze.py:1925` | genuine consumer test は期待例外が出ず赤 | clean。狭い consumer は `:3638-3655` の後に別 selection gate がなく、同じ入力を拒否する前後層もない |
| 同じ `return False` 変異で genuine launch test を走らせる | 同上 | selection reason が消えて赤 | 冗長 gate。selection を抜けると earlier artifacts が後段 repository scan で未申告 hit になり得るため、単独変異の証拠からは外す |

差分 matrix は node を限定する。

1. 変更前 HEAD の `test_s8b_ratified_verify.py` に `return False` 変異を適用し、既存 stub 2 node を走らせる。両 test は自分で導出を `True` に monkeypatch するため緑のまま。
2. 実装後の同 file、同変異で既存 stub 2 nodeと新 genuine 2 nodeを走らせる。既存 2 node は緑、新規 2 nodeだけが赤になることを記録する。
3. consumer node の赤を clean kill とし、launch node の赤は経路被覆の補助証拠に限定する。
4. repo 全体では既存 `test_s8b_holdout_freeze.py` もこの変異を検出するため、「新テストだけ」の比較には含めない。比較対象を launch/consumer 所有 file に限定したことを実測記録へ明記する。
5. (c) は新 public-name test を変更前 HEAD の production module に対して単独実行すると旧名が存在して赤、実装後 baseline は緑、各 alias 再導入変異では対応する parameter case だけ赤、という三点比較にする。

## scope 外の所見

新たな scope 外所見はない。report / judge / verdict への選択強制、C06 budget 群への強制、launch certificate の実時間性には手を広げない。

## 総括

- (c) は低位 3 API を private 化し、approved builder だけを public に残す。
- brief が漏らした caller は 6 箇所で、後半 4 箇所に加えて oracle driver の 2 箇所も修正対象となる。
- (d) は既存 admission 台帳へ genuine earlier run を追記でき、共有 fixture の移動は不要。
- 最大の不確実性は、旧 schema の selected-run rows と新 measurement-generation rows の混在を fixture 実走が受理するかである。
- 親は最初に genuine 2 node を計算ノードで走らせ、混在受理と `__code__` trace を確認してから全焦点走と変異 matrix へ進むべきである。