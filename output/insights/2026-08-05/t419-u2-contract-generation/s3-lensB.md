# 敵対レビュー（レンズ B: 整合と実効性）

**判定: NO-GO。** 静的監査のみで、pytest は実走しておらず、緑とは報告しない。以下の `brief.md` / `s2-plan.md` は指定 job directory 内を指す。

## 所見

[severity: must-fix] [攻撃シナリオ] `CurrentContract` は public な dataclass であり、権限 capability ではない。`h = resolve_by_contract_sha256(old_hash)` に対し `CurrentContract(generation=h.generation, contract=h.contract)` と再包装すれば、提案された `type(value) is CurrentContract` を通過する。計画上の constructor 検査は generation と raw contract の型だけで、現行 `REGISTRY` 由来であることを検査しない。receipt へ直列化されるのも `env_tag` と同じ raw `contract_sha256` だけなので、正規 current と偽装 current は成果物上も区別不能である。[根拠 `s2-plan.md:27-57,112-124`; `orchestrator/campaign/execution_guard.py:68-85`; `orchestrator/campaign/buildcache.py:635-650`]  
**成果物影響:** g2 activation 後でも再包装した g1 が receipt・build・pipeline certified commit に入り、receipt／WAL／レポートには旧 hash が「current issuer を通った値」として残る。  
[提案] issuer 境界で exact type に加えて `value is REGISTRY[value.env_tag]` 相当の membership/identity を検査するか、module-private seal を持つ非公開 constructor にする。A′-4/A′-5を入れないなら、今 wave では `CurrentContract` と「権限 gate」の導入自体を外す。

[severity: must-fix] [攻撃シナリオ] `REGISTRY = 各世代列の末尾` は、未 activation の g2 を source に追加しただけで current にする。独立 golden は変更時の review alarm にすぎず、g2 と golden を同時更新すれば activation receipt、bundle closure、migration epoch の検査なしに全 consumer が切り替わる。しかも提案テスト自身が「REGISTRY は末尾」を正として固定する。[根拠 `s2-plan.md:11-14,114-124,257-258`; 設計正本 `README.md:146-151`; `brief.md:35-40`]  
**成果物影響:** g2 追加 commit の import 時点から floor/oracle/T-126/P3 が g2 hash を発行し、旧 g1 protocol の受理集合が縮む一方、closure 未検証の g2 receipt・台帳行が生成可能になる。  
[提案] active pointer/activation receipt を導入するまで `len(sequence) == 1` を production 初期化でも要求するか、明示した current pointer から導出する。少なくとも「末尾=current」をテストで正当化しない。

[severity: must-fix] [攻撃シナリオ] history resolver を追加しながら production 使用箇所を **0件**にするため、T-478 の元の破断点は残る。旧 floor protocol の validator は callback が返す current hash と artifact 内 hash を比較する構造であり、`lookup` を `require_current` に置換しても意味は同じである。[根拠 `s2-plan.md:156-182`; `orchestrator/campaign/s8b_floor_campaign.py:308-322`; `orchestrator/campaign/s8b_floor_contract.py:104-150`; 設計正本 `README.md:25-43,176-195`]  
**成果物影響:** g2 activation 後、既存 `floor_protocol.json` の g1 hash は引き続き拒否され、ratified 検証・材料レポートの g1 proof-chain 参照は `unresolved` のままになる。  
[提案] current issuer/launch 用 validator と historical report/replay 用 validator を別 API にし、後者は artifact 自身の hash を `resolve_by_contract_sha256(..., expected_env_tag=...)` へ渡す。これを scope 外にするなら、「過去 proof chain を解決可能にする」という brief の成果主張を data-layer preparation まで縮める。

[severity: must-fix] [攻撃シナリオ] brief は certified 選択入口も `CurrentContract` だけを受けるとするが、計画は `None` legacy 分岐を明示的に残す。`run_campaign(env_contract=None)` は site 検査より前に return し、pipeline は legacy build から certified commit まで進める。P3 も `OTHER` site では contract を解決しながら `run_campaign` へ渡さない。[根拠 `brief.md:25-27`; `s2-plan.md:192-195`; `orchestrator/campaign/loop.py:62-87,101-106,247-271`; `orchestrator/campaign/pipeline.py:461-504,730-778,991-1004`; `orchestrator/campaign/p3_s4_loop_trigger_gating.py:560-602`; 設計正本 `README.md:78-80,152-155`]  
**成果物影響:** certified 受理集合に generation/hash 非束縛の run が残り、同じ campaign ID/WAL に g1・g2または contract 無しの値が混在できる。  
[提案] A′-3を全 certified gate と称するなら A′-6も同時に入れ、contract-bound flow では `CurrentContract` を必須化して campaign identity に hash を入れる。そうしないなら「v2 opt-in の一部入口だけ」と明記する。

[severity: must-fix] [攻撃シナリオ] executable call ではない反射 consumer が移行表から落ちている。`s8c_preregistration_evidence.py` は `env_contract.py` に関数名 `lookup` があることを AST で要求し、machine-readable evidence contract も `lookup(env_tag)` を参照する。計画の「lookup import/call が0」テストはこの文字列依存を検出しない。[根拠 `s2-plan.md:126-133,263`; `orchestrator/campaign/s8c_preregistration_evidence.py:575-595`; `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:430-460`; `orchestrator/tests/test_s8c_preregistration_predicates.py:107-131`]  
**成果物影響:** evidence contract の `field_paths`／`reachable_from` が不存在 API を指し、C12 の証拠受理集合から新 `env_contract.py` が脱落する。  
[提案] lookup を削除するなら evidence contract、C12 evaluator、negative-control fixtureを同時移行する。8c/P3 下流を scope 外に保つなら lookup 削除も延期する。

[severity: must-fix] [攻撃シナリオ] 提案テストは g1-only data のため、世代機構の重要分岐を発火させない。`is_valid_successor()` 単体テストが緑でも generation validator からその呼出しを削除する変異は、現行 tuple がすべて長さ1なので生存する。reverse index を `REGISTRY` の current entries だけから作る誤実装も、全世代=current の現状では resolver testを通る。[根拠 `s2-plan.md:112-124,255-263`; `orchestrator/campaign/env_contract.py:163-199`]  
**成果物影響:** 後続 g2 で adjacency 検査を通らない attestation/clocks変更や、旧 g1を引けない reverse index が current 化し、certified 受理集合と過去レポート参照を壊す。  
[提案] candidate mapping を引数に取る純粋な generation validator/index builder を分離し、synthetic g1→g2で連番、全 hash index、adjacency 呼出し、非current g1解決を検査する。

[severity: should-fix] [攻撃シナリオ] 既存 `test_env_contract.py` は wrapper 導入後も機械的には通し得るが、意味上は current view しか検査しない。`checked_entries == 2` / `required_entries == 1`、calibration bytes、self-inconsistency、legacy allowlist はすべて `REGISTRY.items()` を走査するため、g2後の historical g1 は検査対象から消える。[根拠 `orchestrator/tests/test_env_contract.py:434-475,518-531`; `s2-plan.md:237-249`]  
[提案] current の `2/1` は名前を明確にして維持し、別に全 `GENERATIONS` の path実在・bytes hash・schema・世代別 allowlist/self-inconsistency closure を検査する。`KNOWN_SELF_INCONSISTENT_CALIBRATIONS` は path/hash keyなので複数世代を表せるが、現状の走査では活用されない。`LEGACY_CALIBRATION_ALLOWLIST` は必要なら generation/hash keyへ拡張する。

[severity: should-fix] [攻撃シナリオ] `lookup()` 削除の test 移行規模が過少である。静的 AST 再集計では `env_contract.lookup` の executable test call は **84箇所・18 file**。計画が列挙する `test_env_contract.py` の19箇所以外に **65 call・17 file** が残るほか、callback参照4件、属性名 monkeypatch 6件がある。さらに `build_v2` 等の exact type変更は lookup を使わない raw fixture も壊す。[根拠 `s2-plan.md:128-130,225-235`; `orchestrator/tests/test_buildcache_v2.py:129-140,193-205`; `orchestrator/tests/test_build_site_gate.py:28-32,70-81`; `orchestrator/tests/test_p3_s4_loop_trigger_gating.py:334-347,476-481`; `orchestrator/tests/test_s8b_floor_campaign.py:620-628`]  
[提案] production 21件とは別に、全 test call／function-value／monkeypatch／raw contract fixture の移行表を作る。低水準 verifier test の raw contract は無理に Current 化せず、issuer testだけ権限型を使う。

[severity: should-fix] [攻撃シナリオ] transition predicate は全 env に calibration path/SHA変更を許すが、`attestation_mode="none"` の loader は単一 `GRANDFATHERED_V1_SHA256` 以外を拒否する。したがって linux-baremetal の「valid successor」は `require_current()` では選べても calibration load 不能である。[根拠 `s2-plan.md:59-68`; `orchestrator/campaign/env_contract.py:169-177`; `orchestrator/campaign/env_attestation.py:858-860`]  
[提案] 本 wave を Pegasus世代移行に限定するか、mode=none successor を明示拒否する。generic APIを維持するなら、loaderを含む synthetic successor integration testが必要である。

[severity: should-fix] [攻撃シナリオ] 子A→子Bの所有分離は成立していない。子Aは新 generation/resolver testを `test_env_contract.py` に追加する必要があり、子Bは同じファイルの19 lookup callを移行する。さらにAが先に `lookup` を削除すると、`pegasus_floor_scoping.py` の direct importとP3のmodule-level aliasがB着手前から import不能になる。[根拠 `brief.md:80-84`; `s2-plan.md:126-130,225-264`; `orchestrator/campaign/pegasus_floor_scoping.py:23,74-76`; `orchestrator/campaign/p3_s4_loop_trigger_gating.py:94-95,318-324`]  
[提案] `A1: additive API＋generation tests（lookup残置）→B: production/test移行→A2: lookup削除＋zero-reference検査` とする。`test_env_contract.py` の ownerとA2再投入を明示しない限り、「同一ファイルを触らない」は撤回する。

## 親 brief の一般化への反証

独立した `rg` と AST call 走査の結果は次のとおりである。

| production file | call数 | 根拠 |
|---|---:|---|
| `s8b_floor_campaign.py` | 4 | `:313,412,1874,2755` |
| `s8b_ratified_freeze.py` | 4 | `:960,1803,2287,2880`（最後はlambda） |
| `silo_ladder_rung1.py` | 4 | `:1936,3534,3752,4433` |
| `t126_driver.py` | 2 | `:496,868` |
| `pipeline.py` / `loop.py` | 1ずつ | `:535` / `:72` |
| oracle driver / report | 1ずつ | `s8b_oracle_driver.py:762`; `s8b_oracle_report.py:1202` |
| Pegasus scoping / P3 | 1ずつ | `pegasus_floor_scoping.py:23,75`; `p3_s4_loop_trigger_gating.py:95,324` |
| T-419 probe | 1 | `t419_probe_causality.py:3394-3396` |

合計は **21 call / 11 file**。campaign 18 + T-126 2 + T-419 probe 1 である。brief の約20/10は同じ production universeでは誤りで、列挙された `env_attestation.py` は callerではなく型 consumer、代わりに `loop.py` と probe が実 callerである。[根拠 `brief.md:28-31`; 設計正本 `README.md:42-45`]

plan の21件表は executable call自体は全件拾っている。別名はP3の `_lookup`、直接importはPegasus scoping、lambdaはratified freezeであり、現行 production に partial/getattr/re-export経由の追加 callは見つからなかった。ただし前述のS8c反射依存はcall数に入らない。

## 提案テストの帰属

| 提案テスト | 帰属不成立 |
|---|---|
| `EXPECTED_GENERATION_HASHES` | key/hash driftは捕捉するが、calibration bytes・schema・history retentionは検査しない。 |
| `REGISTRY == 列末尾` | 未 activation g2 の自動 current 化を欠陥ではなく正として固定する。 |
| synthetic successor | predicate単体は検査するが、initializerがpredicateを呼ばない欠陥はg1-onlyで生存する。 |
| resolver全g1逆引き | 全世代indexとcurrent-only indexを現データでは識別できない。 |
| `require_current` exact type | Historical rawをpublic `CurrentContract(...)` で再包装する攻撃が通る。 |
| Historical→receipt拒否 | execution_guard一入口だけで、buildcache/pipeline/loop等の型検査削除を検出しない。 |
| production AST zero lookup | direct `CurrentContract(...)`、S8cの反射依存、test call残存を検出しない。P3 alias捕捉にはcallだけでなくAttribute load/assignment解析も必要。 |

## 実装しない選択の評価

この wave はさらに削るべきである。安全に land できる最小集合は A′-1/A′-2、すなわち immutable generation data、history resolver、transition predicate、synthetic 2世代validator testまでである。`lookup()` は当面 current compatibility APIとして残し、production migration、`CurrentContract`、issuer exact-type gateはA′-4/A′-5/A′-6と同じ waveへ送るのがよい。

逆に「型による権限 gate」を本 wave の成果に残すなら、最低でも次が必要である。

- current wrapper の非偽造性またはregistry identity検査
- activation record＋全入口activation receipt
- `current` と `active` の分離
- campaign identityへのcontract hash束縛と`None`迂回閉鎖
- current validatorとhistorical validatorの分離
- 全 production/test/反射consumer移行

R-1 probe実装、実較正再取得、pin closureはentry condition未成立なので、今回入れない判断が妥当である。

## gate が効く全層

| scope外の層 | 無い間、このgateが防げないもの |
|---|---|
| A′-4/A′-5 active authority・activation receipt | wrapper偽造、末尾g2の自動current化、入口ごとのmigration epochずれ。[根拠 設計正本 `README.md:146-151`] |
| protocol blind-seal transition | contract hash以外にmaster seed・予測・partitionを同時変更した再凍結。[根拠 `README.md:120-124`] |
| A′-6 campaign identity | g1/g2の同一WAL/layout混在と`env_contract=None`迂回。[根拠 `README.md:152-155`] |
| staging resolver | pending g2をcurrent公開せずprotocol/selector closureを生成できない。[根拠 `README.md:218-230`] |
| A′-7 versioned predicate | historical hashを解決できても当時のproof chainを再計算できず、current verifier fallbackを防げない。[根拠 `README.md:156-158`] |
| A′-8 shell wrapper結線 | Python gate前に固定旧protocol pathが選ばれる。[根拠 `tools/pegasus/floor_campaign.sh:880`; `README.md:159-161`] |
| A′-9 full independent closure | 自己申告role/key集合の欠落・空集合・部分bundleをcurrent扱いすること。[根拠 `README.md:162-164`] |
| producer provenance | rejected attemptや直接コピーしたcalibrationを正規current材料として包むこと。[根拠 `README.md:273-274`] |
| 8c/P3 prereg下流 | trial registry・report・certified acceptanceがgeneration/bundleを記録しないこと。[根拠 `README.md:275`] |
| R-1/self-comparison/current eligibility | `CurrentContract` 型だけで実環境attestation済み・科学的適格と誤認すること。[根拠 `s2-plan.md:14`; `brief.md:7-15`] |

## import / leaf 監査

現プラン記載の wrapper、MappingProxy、local validatorだけなら、`env_contract.py` の「stdlibのみ・campaign内importなし」は維持でき、現時点で循環importは実証できなかった。[根拠 `orchestrator/campaign/env_contract.py:2-27`; `s2-plan.md:20-68,93-124`]

ただし上のmust-fixを解くためにactivation/attestation処理を `env_contract.py` へ逆importしてはならない。純粋な世代値・型はleafに残し、activation orchestrationは上位moduleへ分離する必要がある。

## 総括

- 最重: public `CurrentContract` とexact-type assertは権限ではなく、Historicalを再包装して全issuerを通せる。
- 次点: `REGISTRY=列末尾` とresolver利用0件により、未activation g2は自動currentになる一方、旧g1 proof chainの実破断は残る。
- 第三: `None` certified経路、campaign identity、activation receiptがscope外なので、型gateはWAL・レポート・台帳まで到達しない。
- 推奨はA′-1/A′-2へscopeを縮め、A′-3 consumer移行はA′-4/A′-5/A′-6と同時に実装すること。