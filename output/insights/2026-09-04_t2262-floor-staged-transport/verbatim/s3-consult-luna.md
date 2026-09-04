## 照合結果

指定された9資料は全て読めた。静的検査のみで、pytest は実走していない。

主な file:line のずれは次のとおり。

- brief A4 の `s8b_floor_campaign.py:2986-3060` は不完全。`None` 分岐は `:2990-3038`、関数全体は `:2986-3096`。
- brief A5 の `:3234-3245` は分岐と staged 検査呼出しまで。3本の SOURCE_DIR 追加は `:3267-3272`、`transport_mode="source-dir"` は `:3320-3324`。
- brief A6 の `:2380-2440` は主に payload policy の読込と schema 検査。v3 literal は `:2410`、shared pin との一致は `:2446-2465`、3 source の実際の pin・clean 検査は `:2570-2787`。
- brief erratum 2 の `_assert_official_permitted` は `:463-473`。public `run_campaign` の呼出しは `:7044` であり、記載の `:7045` は `authority_root` の代入。core 側は `:7140`。
- CLI 定義は `:8234-8237`。brief の `:8236` は help 文字列だけだが、内容自体は一致する。
- brief `:117-118` の「結果の `nondefault_seams`」は不正確。`:7718` は holdout reservation への引数で、実際の保存先は `s8b_holdout_admission.py:1608` の claim。`result.json` の組立範囲 `s8b_floor_campaign.py:6649-6687` に同 field はない。
- s2-plan `:137` の既存 nodeid は実在しない。実在する ID は acceptance ledger `:13613` の  
  `test_public_official_rejects_each_nondefault_seam_before_side_effects[fetchcontent_base_dir-seam_value11]`。

それ以外の主要 anchor、特に shell `:697-721`, `:1209-1211`, `:1231`、submitter `:396-517`, `:621-635`、driver `:2570-2787`, `:6918-6967`、contract `:42-50` は記述と一致する。

導出規則は discovery を使っていない。`IZANAGI_SUBMISSION_NONCE` と `TMPDIR` は環境入力だが、exact 名を必須入力として読み、固定 prefix・固定 leaf と組み合わせ、候補探索、glob、directory 走査、最新値選択、既定値 fallback を行わない。したがって「環境からの推測」ではなく明示契約による一意導出と判定できる。

`cp -a` 移管案は、現 shell の全検査を計画上は再現している。payload/source の non-symlink directory、destination の事前不在、exclusive mkdir、3依存の存在、exact `cp -a --`、コピー後検査が s2-plan `:61-63` にある。source は repo 内の `ROOT/output/.../<nonce>/masstree-payload`、destination は repo 外の `TMPDIR/izanagi-floor-fetchcontent` と別々に固定されている。repo 外制約は既存 driver `:2605-2612` と `:3079-3095` に実在する。

「凍結 bytes pin は不在」は追認する。対象3 file の現 SHA-256 は repo 内に literal 参照がなく、`tools/pegasus/admission_registry.json:70-74,310-314` は dispatch 分類だけ、`test_official_perf_closure.py:27-43,479-543` は perf predicate/call inventory だけである。

可視な全 worktree の commit 差分と未commit差分では、プランの5編集 file と交差する別 wave はなかった。ただし後述の claim consumer 修正まで所有範囲を広げる場合、locked な T-1851/T-2107 が既に `s8b_holdout_admission.py` とその test を変更しており、「交わらない」は成立しなくなる。

## 投入から実行までの経路

1. `submit_floor.sh:299-307` が32桁 lowercase hex nonce を生成し、`:396-506` が persistent source を submission payload へコピーする。payload root は `:509`。
2. `:621-624` が `export_spec` を作り、`:633-635` が `qsub -v` に渡す。実投入は `:649-652` で repo root へ `cd` してから行うため、PBS が作る `PBS_O_WORKDIR` は同 checkout になる。
3. job は `floor_campaign.sh:41-44` で nonce、`:22-24` で `PBS_O_WORKDIR` を必須化し、`:46` で repo root を確定する。
4. `:547-552` で nonce を再検査して submission directory を固定し、receipt の nonce と job ID を `:647-654` で照合する。
5. nonce は shell 変数だけでなく qsub 由来の環境変数であり、driver 起動まで export 属性を失わない。`:1211` が export を解除するのは evidence-root だけである。`python -I` も一般の process environment は消さない。
6. driver は従って `os.environ["IZANAGI_SUBMISSION_NONCE"]` を読める。`IZANAGI_RESERVATION_NONCE` への alias も `:971` にあるが、導出には不要。

投入から floor driver まで切れる箇所はない。新しい env 変数も不要である。

## 取り残される consumer

| consumer | 実際の影響 | プラン状況 |
|---|---|---|
| Holdout claim | `s8b_holdout_admission.py:1608` の値が pilot で `["fetchcontent_base_dir"]` から `[]` へ変わる | 未記載 |
| Resume claim | `:1656-1668` が既存 claim の seam を保存するため、完全な既存 claim 集合は読める。部分集合では新旧 seam が混在する | 未記載 |
| Claim-derived eligibility | `:6149-6171` が全 cell の seam basis 一致と空集合を検査する | 未記載 |
| Checkpoint/liveness | shell の `fetchcontent-staging` stage が消え、失敗は `floor-driver` に畳み込まれる | test fixture 更新だけで意味変更は未処理 |
| Process spawn inventory | driver 内の exact `cp -a` は新しい process launch site になる | 未記載 |
| `s8b_oracle_n_pilot.py` | `:51-55,822-828` が変更 helper を `None` で直接利用する | 未記載 |
| buildcache binding/digest | `buildcache.py:2434-2449,2485,2527-2548`。現 job も既に同じ base と source-dir mode なので production pilot の digest 値は変わらない | 間接確認だけ |
| completion manifest/receipt | `buildcache.py:2850-2879` と floor `:2155-2184,2240-2246`。現 job との値差はない | 専用 consumer test なし |
| floor manifest/runtime projection | floor `:4501-4503,4731-4767,5578-5600,7485-7495`。raw base は portable artifact から除去されるため値差なし | 専用 consumer test なし |

抜けている関連 nodeid は少なくとも次。

- `orchestrator/tests/test_ccbench_spawn_sites.py::test_reviewed_process_launch_inventory_is_recursive_and_exact`
- `orchestrator/tests/test_s8b_holdout_admission.py::test_resume_claim_transition_table_is_run_wide_and_marker_guarded[one-claim]`
- `orchestrator/tests/test_s8b_holdout_admission.py::test_inspection_v2_nondefault_seam_is_valid_but_disqualifying`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_captured_refreeze_seams_are_forwarded_to_claim_reservation_canonically`
- `orchestrator/tests/test_pegasus_floor_tools.py::test_floor_liveness_terminal_reads_job_staging_failure_json`
- `orchestrator/tests/test_s8b_oracle_n_pilot.py::test_sort_best_materialize_receives_oracle_environment`
- `orchestrator/tests/test_s8b_oracle_n_pilot.py::test_sort_best_oracle_preflight_failure_stops_before_build`
- `orchestrator/tests/test_buildcache_v2.py::test_prepare_masstree_fetchcontent_emits_all_three_staged_source_dirs`
- `orchestrator/tests/test_buildcache_v2.py::test_v2_fetchcontent_transport_mode_separates_base_and_source_identity`
- `orchestrator/tests/test_buildcache_v2.py::test_v2_source_dir_transport_reaches_configure_and_completion_identity`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_sort_runtime_record_with_fetchcontent_base_stores_and_projects`
- `orchestrator/tests/test_s8b_floor_campaign.py::test_sort_best_swo_pass_receipt_reaches_manifest_and_result`

## real 所見

1. 部分作成済み claim の resume が永続的に壊れる。`s8b_holdout_admission.py:1636-1668` は既存 claim だけ旧 seam を保存し、欠けた claim は新しい `[]` で作る。その後 `:6149-6152` が混在を拒否する。claim path digest 自体は `:805-815` のとおり seam を含まないため衝突する。  
   成果物影響: resume は測定・attempt 消費後の `s8b_floor_campaign.py:7767-7787` で artifact-invalid となり、台帳が進んでも result/report が発行されない。fail-closed の向きは正しいが、既存 run を破棄して新しい campaign_run_id で再投入する回復手順、または backfill basis の明示処理が必要。

2. staging 失敗の liveness 診断が退化する。現 shell は `floor_campaign.sh:713-720` で `fetchcontent-staging` failure/checkpoint を記録する。移管後は `:1403-1404` の一般的な `floor_driver` failure になる。`floor_liveness.py:407-443` は driver stderr と generic failure/result だけを読み、driver が `s8b_floor_campaign.py:8317-8368` で stdout に出す詳細 JSONや private preflight markerを読まない。  
   成果物影響: liveness report の stage/reason が具体的な staged-payload failure から generic `floor-driver` へ変わり、再投入判断の参照が失われる。

3. exact `cp -a` の追加は process-launch inventory を必ず変える。`test_ccbench_spawn_sites.py:177-190` は floor driver の subprocess site を exact 列挙し、`:2558-2565` が完全一致を要求する。新 helper の launch site とこの nodeid はプランにない。  
   成果物影響: mandatory test の受理集合が空になり、inventory 更新なしでは wave を受入済みにできない。

4. `[source-missing]` test の予定手順は現機構では成立しない。現 fixture は `test_s8b_floor_campaign.py:4583-4593,4635-4649` で空 base を残して後段 `source-missing` を発火させる。新 default staging に正しい3-source fixtureを与えると `masstree-src` は既に存在し、initial missing を与えると新 helper が `s8b_floor_campaign.py:2636-2646` 相当より前で拒否する。  
   成果物影響: private diagnostic `floor-dependency-source-missing` の report branch が未検査になる。後段を狙うなら prebuild stub 内で staging 後に source を除去するなど、発火点を明示する必要がある。

## 疑い

- `s8b_oracle_n_pilot.py:822-828` は `_canonical_floor_fetchcontent_base(None)` と `_prepare_floor_oracle_dependency` を直接使うが、`submit_oracle_n_pilot.sh:318-330` は `IZANAGI_SUBMISSION_NONCE` を渡さない。新 semantics では nonce 不在で即拒否する。ただし現実装も空 base を staged input として渡して後段で拒否するため、成功集合の縮小とはまだ断定できず、主に共有 helper の所有漏れと診断理由の変化である。
- 新 staging 失敗を `_FloorOraclePreflightError` にする際の detail code が未指定。許可集合は `s8b_floor_campaign.py:215-268`、未知 code は `:1985-1990` で `ValueError` になる。既存 code に写すなら成立するが、author が新 code を足すか再利用するかを決める必要がある。
- plan は repo 外検査を staged verification に委ねている。production の `TMPDIR=/scr/...` では成立するが、helper 単体では repo 内 destination へコピーした後に拒否する実装にも読める。外部性検査をコピー前に行うかは明示されていない。
- planned 5 file だけなら他 worktree と交差しない。しかし real 所見 1 の production 修正または test 追加まで含めると、T-1851/T-2107 の `s8b_holdout_admission.py` 系と file 単位で交差する。

## 変異の帰属不成立

- invalid nonce は driver より前に `floor_campaign.sh:41-44`, `:547-550`, `:647-648` が同じ入力を拒否する。新 driver validator の変異を production 経路で単独帰属できるのは helper 直呼び unit testだけ。
- `staging-exists` と `staging-symlink` は事前 `lexists` と exclusive `mkdir` の双方が拒否する。一方だけの変異では同じ入力がなお赤になる。
- `payload-symlink` と `source-symlink` は pre-copy lstat、コピー後 destination 検査、さらに `_verify_pristine_floor_dependency_sources:2595-2603,2647-2657` が重なる。各変異の赤理由は単一にならない。
- initial `*-missing` は新 staging helper が拒否するため、後段 `floor-dependency-source-missing` 変異へ届かない。後段 disappearance と initial unsafe layout を別 fixture に分ける必要がある。
- fresh official の end-to-end 正例は CLI `:8434-8440`、public/core `:7038-7044,7140`、job の pilot 固定 `floor_campaign.sh:1228` に遮断される。`test_default_staged_transport_is_not_counted_as_refreeze_seam` は policy-unit 帰属しか証明しない。
- source-dir は buildcache の all-or-nothing gate `buildcache.py:848-869,2434-2445` と floor postflight `s8b_floor_campaign.py:3677-3694` の双方が検査する。prebuild kwargs、cell build kwargs、postflight を別々に stub しなければ変異理由が混ざる。

## scope 外候補

- §8 の `_assert_official_permitted` と CLI 拒否の解除。
- `floor_campaign.sh` の `--mode pilot` 固定を認可済み official mode へ結線する作業。
- official 実走と性能測定。
- 既存 `s8b_oracle_n_pilot` の FetchContent transport を独立して修復する作業。
- 新しい gate、台帳、凍結 bytes pin の追加は不要。部分 claim の回復は既存 create-only claim を書き換えず、新 run ID で再投入する手順を第一候補にできる。

## 総括

最大の危険は、旧 seam を持つ部分 claim を新 `[]` claim で補完すると basis が混在し、測定後に report が拒否される点である。  
プランには holdout claim の移行挙動と回復手順を追加すべきである。  
次に、driver 側 `cp -a` の process-launch inventory と checkpoint/liveness の意味変更を変更面へ加える必要がある。  
nonce と payload の投入経路は実在し、PBS から driver まで切れていない。  
導出式は固定的で discovery ではなく、source と repo 外 destination も別々に固定されている。  
本 wave 後も §8 gate と pilot 固定が残るため、official は起動できない。