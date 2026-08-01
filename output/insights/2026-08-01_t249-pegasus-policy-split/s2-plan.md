# [T-249] 段 2 編集プラン

採用案は、repo-relative path だけをキーとする JSON registry と、完全性・実在・tracked 性だけを守る pytest node です。ただし、この変更だけでは shared policy の実際の分割や consumer の付替えは起きません。親 brief はその点を過大評価しています。

静的確認のみ実施しました。HEAD は base commit `7b24f81`、worktree は clean、ホストは `pegasus02` です。pytest は実行しておらず、緑とは主張しません。

## 現在の byte 境界

- `tools/pegasus/policy.json` の SHA-256 は `b1c42e493148517cf4adc055999c5706eb3f15500c57bfcb0dbfc2a36ac961ac`。
- base commit `7b24f81` の blob と現行 file は同一です。
- `tools/pegasus/policy.json`、`output/env/pegasus/silo_ladder_rung1/silo_ladder_rung1.json`、`orchestrator/qualification/t126_reservation_policy_v1.json` はすべて tracked、base との差分なしです。

## 全 key と consumer の棚卸し

「live」は production の py/sh が値を解釈する箇所、「test-only」は production header 等との一致をテストが読む箇所です。

| JSON path | 実際の consumer |
|---|---|
| `project`, `queue`, `nodes` (`policy.json:2-4`) | `certify_calibration.sh:109-141`、`floor_campaign.sh:209-255`、`submit_certify.sh:55-73`、`submit_floor.sh:135-165`、`submit_t126_qualification.sh:161-185` |
| `smoke_walltime` (`:5`) | live JSON reader なし。`test_pegasus_tools.py:124-133` が hard-coded PBS header と比較 |
| `smoke_walltime_s` (`:6`) | semantic consumer なし。repo 全検索で宣言以外の参照なし。ただし後述の whole-file hash には含まれる |
| `certify_walltime` (`:7`) | live JSON reader なし。`test_pegasus_tools.py:124-133` のみ |
| `certify_walltime_s` (`:8`) | `certify_calibration.sh:109-133`、`submit_certify.sh:55-73` |
| `floor_walltime` (`:9`) | live JSON reader なし。`test_pegasus_floor_tools.py:313-322,325-341` のみ |
| `floor_walltime_s` (`:10`) | `floor_campaign.sh:209-255,610-636`、`submit_floor.sh:135-165` |
| `finalize_reserve_s` (`:11`) | `certify_calibration.sh:109-141,630-634` |
| `expected_cpu_model`, `expected_physical_cores` (`:12-13`) | `certify_calibration.sh:119-141`、`t141_region_profile.sh:388-413,487-488` |
| `gflags_source_path`, `gflags_expected_head`, `glog_source_path`, `glog_expected_head` (`:14-17`) | `certify_calibration.sh:121-140`、`floor_campaign.sh:216-240`、`t126_qualification.sh:470-488`、`t141_region_profile.sh:396-400`、`qualification/submission.py:105-130`、`qualification/identity.py:212-225`、`silo_ladder_rung1.py:825-840,2029-2051`、`silo_ladder_rung1.sh:443-463` |
| `perf_candidates` (`:18-21`) | `certify_calibration.sh:125-141`、`t126_qualification.sh:550-566`、`t141_region_profile.sh:400-410`、`qualification/submission.py:105-112` |
| `silo_ladder_rung1` (`:22-71`) | 下記の全 nested reader |
| `.project`, `.queue`, `.nodes` (`:23-25`) | `submit_silo_ladder_rung1.sh:61-76`、`silo_ladder_rung1.sh:323-340`、`silo_ladder_rung1.py:2358-2365` |
| `.walltime` (`:26`) | `submit_silo_ladder_rung1.sh:61-76`。PBS header との一致は `test_silo_ladder_rung1_driver.py:2229-2245` |
| `.walltime_s` (`:27`) | `submit_silo_ladder_rung1.sh:61-76`、`silo_ladder_rung1.sh:323-340`、`silo_ladder_rung1.py:2358-2365,4058-4068` |
| `.walltime_formula` (`:28`) | live reader なし。`test_silo_ladder_rung1_driver.py:2257-2259` のみ |
| `.build_cap_s` (`:29`) | `silo_ladder_rung1.sh:323-340`、`silo_ladder_rung1.py:3792-3797,4085-4087` |
| `.dependency_build_cap_s` (`:30`) | `silo_ladder_rung1.sh:323-340` |
| `.attestation_cap_s` (`:31`) | `silo_ladder_rung1.sh:323-340`、`silo_ladder_rung1.py:4079-4083` |
| `.run_group_cap_s` (`:32`) | `silo_ladder_rung1.sh:323-340`、`silo_ladder_rung1.py:4138-4140` |
| `.collection_cap_s` (`:33`) | `silo_ladder_rung1.sh:323-340`、`silo_ladder_rung1.py:4297-4300,4450-4459` |
| `.finalize_reserve_s` (`:34`) | `silo_ladder_rung1.sh:323-341`、`silo_ladder_rung1.py:4058-4068` |
| `.solo_load1_threshold` (`:35`) | `silo_ladder_rung1.sh:323-340`、`silo_ladder_rung1.py:1890-1924,3454-3475` |
| `.dependency_pins.gflags`, `.dependency_pins.glog` (`:36-39`) | `silo_ladder_rung1.py:825-841,2008-2022`、`silo_ladder_rung1.sh:448-463` |
| `.third_party_sources[]` (`:40-62`) | `silo_ladder_rung1.py:844-900` が `name`, `source_name`, `url`, `fetchcontent_ref`, `pin` の exact shape と値を読む。`submit_silo_ladder_rung1.sh:154-163,200-219`、`silo_ladder_rung1.sh:348-360` も利用 |
| `.max_attempts` (`:63`) | `submit_silo_ladder_rung1.sh:61-76`、`silo_ladder_rung1.sh:323-340` |
| `.infra_retry_reasons` (`:64-70`) | `submit_silo_ladder_rung1.sh:87-94` |

さらに全 key は byte 単位でも consumer に束縛されています。

- T-139: `submit_silo_ladder_rung1.sh:284-304` が whole-file hash を campaign identity に入れ、`silo_ladder_rung1.py:2394-2424,3496-3516,4417-4433,4538-4562` が再照合します。
- T-126: `contract.py:38-65` の identity set、`t126_driver.py:344-359,398-422`、`t126_qualification.sh:675-682`、`identity.py:130-160` が whole-file bytes を series identity/prologue evidence に束縛します。

## 指定された既存 assert の確認

`test_silo_ladder_rung1_committed_evidence_rebinds_content_not_head` は、単なる policy hash test ではありません。

- `test_silo_ladder_rung1_evidence.py:1195-1206` で `policy` を含む全 bound path の path と現行 bytes の SHA-256 を一致させます。
- `:1305-1335` で raw submit receipt の `policy_sha256` も同じ binding に一致させます。
- patch、ledger、runtime modules、calibration、raw bundle、schedule、provenance、attestation、derived checks、`all_pass` も再導出します。

`test_shared_pegasus_policy_owns_no_t126_qualification_keys` は `test_t126_pegasus_tools.py:1228-1248` で次を assert します。

- top-level に `t126_` prefix key がない。
- `RESERVATION_POLICY_RELATIVE_PATH` が `REQUIRED_CODE_IDENTITY_PATHS` の member。
- committed evidence の `binding.policy.path` が `tools/pegasus/policy.json`。
- その `sha256` が現行 bytes の SHA-256。

したがって新 node では shared policy の hash、prefix、evidence binding を再検査しません。

## registry の採用形

新設先は `tools/pegasus/policy_registry_v1.json` とします。

```json
{
  "schema_version": "pegasus-policy-registry/v1",
  "policy_paths": [
    "orchestrator/qualification/t126_reservation_policy_v1.json",
    "tools/pegasus/policy.json"
  ]
}
```

この registry の lookup input は task ID ではなく、repo-relative policy path そのものです。

- T-139 の実在する committed artifact では `binding.policy.path` (`silo_ladder_rung1.json:41-43`) に `tools/pegasus/policy.json` が存在します。
- T-126 では final receipt に `policy_path` field はありません。`qualification_series_id` から `series-identity.json` を辿り、その `code_identity` field の key を使います。`t126_driver.py:398-422` が同 artifact を生成し、`contract.py:498-505` が key set を `REQUIRED_CODE_IDENTITY_PATHS` と exact 一致させています。
- T-126 の committed receipt は存在しないため、「committed artifact で実測済み」とは書きません。producer・schema・identity contract で確認済み、と限定します。

`schema_version` は registry 自身の形式識別子で、artifact selector や task identifier には使いません。これにより同名識別子の二義化を避けます。

### 却下案

- Python 定数: shell から使いにくく、`contract.py` の編集自体が T-126 code identity bytes を変えます。
- docs-only: 未登録 file を機械検出できません。
- `task_id` / `artifact_id` / artifact `schema_version` をキーにする registry: T-139 と T-126 に共通の task field がなく、T-126 は一 task に複数 schema があります。
- registry に SHA-256 を複写: evidence/series identity と別の hash 正本を作り、凍結意味論を重複させます。
- T-139 用 file を複製するだけ: consumer が読まない dead copy となり、設定正本が二つになります。

## file:line 編集プラン

| 所有 | file:line | 編集内容 |
|---|---|---|
| 実装子 | 新規 `tools/pegasus/policy_registry_v1.json:1-7` | 上記 exact schema と、現行 2 policy path の sorted list を作る。値・hash・task ID は持たせない |
| 実装子 | 新規 `orchestrator/tests/test_pegasus_policy_registry.py:1-約65` | 下記単一 pytest node、path 規約、実在・tracked・完全性検査を実装 |
| 親 docs | `tools/pegasus/README.md:6` の後 | registry が唯一の所在索引であること、per-task file の所在規約、registry は discovery であって proof binding ではないことを短く追記 |
| 親 docs | `docs/decisions.md:5184` の後 | D112 として path-keyed JSON registry、hash 非複写、consumer 非変更、残る実分割を記録 |
| 親 docs | 新規 `output/insights/2026-08-01_t249-pegasus-policy-registry.md` | consumer 棚卸し、artifact field の確認、変異台帳、実測結果を記録。走らせていない結果は書かない |
| 親 docs | `docs/worklog.md:1395` の後 | 段 7 で実際の nodeid・request ID・変異 kill 結果・protected-path diff を記録 |

`docs/phase3.md` には T-249 の対応 checkbox が存在しないため、機械的な追記対象にしません。

## 新規 pytest node

Node ID:

```text
orchestrator/tests/test_pegasus_policy_registry.py::test_pegasus_policy_registry_is_complete_and_tracked
```

予定する assert 順序は次のとおりです。

1. `:30-34`: registry の top-level keys が `schema_version` / `policy_paths` の exact 2 件で、version が exact。
2. `:35-39`: path list が非空・文字列・辞書順・重複なし。
3. `:40-47`: 各 path が相対・`.`/`..` なしで、実体が regular file、symlink でない。
4. `:48-54`: 各 entry に `git ls-files --error-unmatch -- <path>` が成功する。
5. `:55-63`: `orchestrator/<owner>/t<数字>_<purpose>_policy_v<正整数>.json` に一致する全 file を `rglob` で収集し、`{tools/pegasus/policy.json} ∪ discovered_task_paths` と registry 集合を exact 一致させる。

純増検出力は次の二つです。

- 規約に一致する per-task policy file が追加されたのに registry 未登録。
- registry entry が欠落・symlink・非 regular・untracked、または既に存在しない。

新 node は `output/env/pegasus/**` を読まず、`hashlib` を使わず、shared policy の内容・SHA-256・T-126 prefix を assert しません。

## 変異検査候補

| 変異 | 新 node の発火位置 | 手前の拒否がない根拠 |
|---|---|---|
| registry から現行 T-126 path を削除 | 最後の registry/discovery exact-set assert | 既存 T-126 node は固定 path の内容・identity wiring を検査するだけで registry を読まない |
| registry に存在しない `orchestrator/qualification/t999_reservation_policy_v1.json` を追加 | regular-file assert | path は安全かつ schema parse は通る。repo 内に既存 registry consumer はない |
| 上記 dummy file を filesystem に作るが `git add` しない | `git ls-files --error-unmatch` assert | `tools/run_tests.py:486-506` は未 stage「削除」だけを preflight し、untracked 追加を拒否しない。固定 T-126 identity setにも入らない |
| dummy file だけを作り registry entry を追加しない | 最後の exact-set assert | 既存 suite に `*_policy_v*.json` の閉集合 scan はなく、固定 T-126 path の検査はこの入力を見ない |

shared policy や committed evidence の byte mutation は既存 2 node が先に検出するうえ、今回の禁止対象なので候補から外します。

## 1 byte も変えない根拠

実装面の編集対象は新規 registry と新規 test の二つだけです。docs 面も README、decisions、worklog、新規 insight に限定します。

明示的な非編集対象:

- `tools/pegasus/policy.json`
- `output/env/pegasus/**`
- `orchestrator/qualification/t126_reservation_policy_v1.json`
- `orchestrator/qualification/contract.py`
- 全 live consumer py/sh
- 既存 2 pytest node

統合前に親が次を確認します。

```text
git diff --exit-code 7b24f81 -- tools/pegasus/policy.json output/env/pegasus
sha256sum tools/pegasus/policy.json
```

後者は既知値 `b1c42e...961ac` との一致を要求します。

## scope 外として裁定へ返すもの

- `policy.json:22-70` の T-139 固有 block を新 file へ移すこと。
- calibration、floor、T-141 の top-level key を各 task file へ移すこと。
- 全 shell/Python consumer の付替え。
- T-139 evidence の `binding.policy`、既存 output、proof chain の変更。
- registry を production resolver や新しい trust root にすること。
- registry を T-126 `REQUIRED_CODE_IDENTITY_PATHS` に加えること。
- `tools/pegasus/policy.json` を T-126 identity set から外すこと。
- `RESERVATION_POLICY_RELATIVE_PATH`、T-126 policy path/content の変更。
- orphan の `smoke_walltime_s` や test-only key の削除。byte drift になるため別裁定が必要です。

特に `REQUIRED_CODE_IDENTITY_PATHS` の増減だけでなく、member である `contract.py` 自体の編集も T-126 series identity preimage を変えます。D96 に従う独立判断なしに触れてはいけません。

## 編集所有の分割

実装子は一単位だけにします。

- 実装子 `registry-test`: 新規 registry と新規 test の二 file を排他的に所有。
- 親: README、D112、insight、worklog、変異 matrix、計算ノードへの test dispatch。
- registry と test を別実装子へ分けると一方だけ land した時点で意図的な赤になり、利点がありません。
- consumer、policy、contract、output を所有する実装子は起動しません。

親は計算ノードで新 node、指定された既存 2 node、関連全走を実測し、さらに `check_codex_agents.py`、`check_docs.py`、commit 後 provenance 監査を行います。本段ではいずれも未実行です。

## 親 brief への異議

P1 と P2 の組合せでは、ユーザー裁定の「shared policy をタスク別 file へ再編」は実装されません。現に最も明白な T-139 固有設定が `policy.json:22-70` に残り、全 consumer も同じ file を読み続けます。

したがって、この wave が実現するのは「既存 shared file と既存 T-126 per-task file の所在規約・索引・完全性 gate」までです。「次の task が shared policy を編集する構造的衝突を解消した」「T-249 を全面完了した」とは記録すべきではありません。実分割を行うには、consumer identity と将来 evidence binding の変更を含む別のユーザー裁定が必要です。

## 総括

- 採用: `tools/pegasus/policy_registry_v1.json` の path-only JSON registry と単一 pytest node。
- 純増検出力: 未登録 per-task file、registry path の欠落・symlink・untracked。
- 却下: Python 定数、docs-only、task/schema ID registry、hash 複写、dead-copy の task file。
- `tools/pegasus/policy.json` と `output/env/pegasus/**` は編集対象外で、既存 byte binding を維持する。
- 親 brief への異議: 本 scope は索引整備であり、shared policy の実分割や構造的衝突解消そのものではない。