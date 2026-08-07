# 敵対レビュー結果

判定は **must-fix 1件 / should-fix 2件 / nit 1件**。指定された2閉包への追加自体は正しいものの、実行される module 全体の束縛としては不足がある。pytest は未実走であり、緑とは判定しない。

## must-fix

### 1. T419 の submission binding から新 leaf が脱落している

`env_attestation` は import 時に新 leaf を実行する [env_attestation.py:25](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:25)。T419 の parser crosscheck はその `env_attestation` を import する [t419_probe_causality.py:3621](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/probes/t419_probe_causality.py:3621)。

ところが `_submission_binding.related` は `env_contract.py` と `env_attestation.py` までで止まり [t419_probe_causality.py:3491](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/probes/t419_probe_causality.py:3491)、dirty 検査もこの集合だけである [t419_probe_causality.py:3498](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/probes/t419_probe_causality.py:3498)。role/module 名を key にする SHA pin も `env_attestation` だけで、新 leaf は対象外である [t419_probe_causality.py:3507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/probes/t419_probe_causality.py:3507)。

反例は、submission 後に `calibration_verify.py` だけを変更するケースである。HEAD、driver、PBS、`env_attestation` の SHA と列挙済み dirty 集合はすべて一致したまま `matched=True` になり得る。その値が `binding_verified` へ昇格し [t419_probe_causality.py:3875](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/probes/t419_probe_causality.py:3875)、preflight と最終 validity に使われる [t419_probe_causality.py:3913](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/probes/t419_probe_causality.py:3913)、[t419_probe_causality.py:838](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/probes/t419_probe_causality.py:838)。

既発行 T419 result もこの不完全な集合を記録し、`binding_verified=true` としている [result.json:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/t419-probe-causality/0_888740.nqsv/result.json:71)、[result.json:86](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/t419-probe-causality/0_888740.nqsv/result.json:86)。

最低限、新 leaf を `related_paths` に加え、できれば expected/observed SHA も独立記録すべきである。さらに「新 leaf だけを dirty にしたら `binding_verified=False`」となる負例が必要である。

**成果物への影響:** T419 は non-certifying [t419_probe_causality.py:3800](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/probes/t419_probe_causality.py:3800) なので certified 選択値を直接変えないが、未束縛コードで生成した result・manifest・試行台帳を `VALID` と誤受理し、レポートの causal verdict と provenance 参照を偽装可能にする。

## should-fix

### 2. T126 の明示的 `code_identity` 閉包にも新 leaf がない

段4自身は「identity 閉包に入れないと T126 が検証コードを pin しない」と採用している [s4-adjudication.md:37](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/insights/2026-08-07_t529-impl-reraise/s4-adjudication.md:37)。しかし `REQUIRED_CODE_IDENTITY_PATHS` は `env_contract.py` までで、`env_attestation.py` も新 leaf も含まない [contract.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/qualification/contract.py:38)。T126 は実際に抽出後の loader と probe/comparator を呼ぶ [t126_driver.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/qualification/t126_driver.py:439)。

ただし T126 は commit/tree を検証し [identity.py:112](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/qualification/identity.py:112)、submit 時に tracked dirty・index dirty・未追跡 source を拒否して commit 全体を archive する [submit_t126_qualification.sh:76](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/submit_t126_qualification.sh:76)、[submit_t126_qualification.sh:137](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/submit_t126_qualification.sh:137)。したがって series identity の alias や未束縛実行には直結せず、must-fix までは上げない。

解決は「新 leaf だけを追加」では不十分である。明示 map を真の attestation closure とするなら、少なくとも `campaign/__init__.py`、`env_attestation.py`、`calibration_verify.py`、`calibrator/__init__.py`、`schema_v2.py`、`effective_clock_policy.py`、`tsc.py` を一括して扱うべきである。そうしないなら、`code_identity` は選択的 proof map であり、完全性は `superproject_tree` が担うと正本に明記すべきである。

**成果物への影響:** T126 の受理集合は whole-tree pin により変わらないが、試行台帳の `code_identity` と監査レポートから較正検証コードへの直接 proof 参照が欠落し、series identity が何を個別再導出したかを過大表示する。

### 3. 実装報告の「成果物波及は runtime hash だけ」は事実と合わない

報告は「成果物上の波及は将来の `runtime_modules_sha256` 変更だけ」としている [s5-impl.md:66](/work/1/SFC/tanab/dev-wave-jobs/t529-impl-reraise/s5-impl.md:66)。しかし実際には次も変わる。

- T419 が role 名で pin する `env_attestation_sha256` [t419_probe_causality.py:3507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/probes/t419_probe_causality.py:3507)
- T126 の `superproject_commit`、`superproject_tree` と、それらを含む series identity [contract.py:463](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/qualification/contract.py:463)
- 将来の Silo artifact 内の path 別 `runtime_modules` proof 参照 [silo_ladder_rung1.py:4433](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:4433)

また「wrapper、2閉包を実装」とする総括 [s5-impl.md:83](/work/1/SFC/tanab/dev-wave-jobs/t529-impl-reraise/s5-impl.md:83) は、段4が言及した T126 identity と、検索で判明した T419 binding を数えていない。

**成果物への影響:** この記述を直さないと、親が T419/T126 の再束縛対象を見落とし、試行台帳・レポートに古い role SHA や不完全な proof 参照を残す。

## nit

### 4. V2 閉包の所属テストは単体では自己参照 pin にすぎない

追加テストは、実装側と同じ `V2_ENV_NEUTRAL_MODULES` に path があることだけを assert する [test_env_contract.py:1193](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_contract.py:1193)。path を残して leaf の意味論を空にしても、このテスト単体は通る。

ただし汎用 AST 検査が実ファイルを読む [test_env_contract.py:1177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_contract.py:1177) うえ、leaf の SHA・duplicate key・env・clock・escape・policy 負例が別途あるため、suite 全体が恒真という反証にはならない。

**成果物への影響:** 現状は他テストが補うため成果物値・受理集合への直接影響はないが、この所属テストだけを閉包の意味論的保証として報告すると入口被覆率を過大表示する。

## 閉包・台帳・pin の全数確認

| 面 | 判定 | 根拠 |
|---|---|---|
| Silo runtime module 閉包 | 追加済み・妥当 | production list [silo_ladder_rung1.py:254](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:254)、独立 exact-set [test_silo_ladder_rung1_driver.py:926](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_silo_ladder_rung1_driver.py:926) |
| V2 env-neutral AST 閉包 | 追加済み・妥当 | list [test_env_contract.py:82](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_contract.py:82)、全 module AST scan [test_env_contract.py:1177](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_contract.py:1177) |
| T419 path/role binding | **不足** | must-fix 1 |
| T126 selected `code_identity` | **明示 closure として不足** | should-fix 2。ただし whole-tree pin は存在 |
| `FROZEN_MANIFEST` | 追加不要 | source module pin ではなく、既発行 output 23件の byte freeze [test_frozen_artifacts.py:38](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_frozen_artifacts.py:38) |
| `source_digest` | 追加不要 | CCBench の EVOLVE_BLOCK source/allowlist 専用 [source_digest.py:73](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/source_digest.py:73) |
| calibration certification scripts | 個別追加不要 | clean commit/tree に束縛する [submit_certify.sh:71](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/submit_certify.sh:71)、[certify_calibration.sh:172](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/certify_calibration.sh:172) |

加えてはいけない面への過剰追加は見つからなかった。

## `runtime_modules_sha256` の波及

consumer は以下で尽きる。

- 生成: path別 SHA の canonical JSON hash [silo_ladder_rung1.py:275](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:275)
- submit: 計算 [submit_silo_ladder_rung1.sh:289](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/submit_silo_ladder_rung1.sh:289)、campaign root と submit receipt へ記録 [submit_silo_ladder_rung1.sh:370](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/submit_silo_ladder_rung1.sh:370)、[submit_silo_ladder_rung1.sh:486](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/tools/pegasus/submit_silo_ladder_rung1.sh:486)
- job: submit receipt と現行値を比較 [silo_ladder_rung1.py:2406](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:2406)、campaign root と比較 [silo_ladder_rung1.py:2507](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:2507)
- collect: submit 時の frozen 値と再比較 [silo_ladder_rung1.py:4554](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:4554)
- result: aggregate ではなく path別 `runtime_modules` を格納 [silo_ladder_rung1.py:4451](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:4451)、現行 binding 検査で全リスト比較 [silo_ladder_rung1.py:3512](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/silo_ladder_rung1.py:3512)
- test: historical listから aggregateを再導出 [test_silo_ladder_rung1_evidence.py:1374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1374)。driver fixture の `"a"*64` は実 SHA の golden ではない [test_silo_ladder_rung1_driver.py:2374](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_silo_ladder_rung1_driver.py:2374)。

read-only 再導出では、HEAD の19 module が `c421e791…`, 現 worktree の20 module が `e719f416…` となり、値は確実に変わる。

既発行 evidence は `6327347600…` を submit receipt [submit-receipt.json:10](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/attempts/1/submit-receipt.json:10)、identity receipt [campaign-identity-receipt.json:22](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/campaign-identity-receipt.json:22)、root receipt [campaign-root-receipt.json:31](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/env/pegasus/silo_ladder_rung1/job-staging/0_873920.nqsv/raw-bundle-attempt-1/campaign-root-receipt.json:31) に一貫して記録している。テストは historical binding が現行値と異なることを明示的に要求する [test_silo_ladder_rung1_evidence.py:1249](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_silo_ladder_rung1_evidence.py:1249)。

したがって既発行 artifact を新 hash に更新してはならない。現行固定値を期待する golden はなく、historical artifact の自己完結性とも矛盾しない。

## 目的・scope・テスト

将来辺を加えた import グラフは次で閉じる。

`env_contract → calibration_verify → calibrator.{effective_clock_policy,schema_v2} → stdlib`

新 leaf の import は2 moduleだけ [calibration_verify.py:13](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:13) で、`env_contract` や `env_attestation` へ戻る辺はない。現行 `env_contract` も stdlib のみである [env_contract.py:19](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_contract.py:19)。したがって将来 `env_contract` から import/call しても循環 import は発生せず、wave の目的は達成している。fresh-process テストもこの条件を直接検査する形になっている [test_env_attestation.py:1093](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_attestation.py:1093)。

scope 外とされた fuse、g2 registry、historical resolver、世代遷移、activation/receipt/authority loader [s4-adjudication.md:87](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/output/insights/2026-08-07_t529-impl-reraise/s4-adjudication.md:87) への変更は patch にない。定数も新 leaf の同値 [calibration_verify.py:17](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/calibration_verify.py:17) を公開 alias にしただけである [env_attestation.py:29](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/campaign/env_attestation.py:29)。scope 逸脱は認めない。

委譲テストは sentinel と生の全引数を検査するため、inline 実装へ戻せば失敗する [test_env_attestation.py:1072](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t529-impl-reraise/orchestrator/tests/test_env_attestation.py:1072)。runtime 閉包テストも production path を消せば exact-set 不一致になる。これらは恒真ではない。

実装報告は pytest が preflight で停止し未実走であることを正しく申告している [s5-impl.md:28](/work/1/SFC/tanab/dev-wave-jobs/t529-impl-reraise/s5-impl.md:28)。本レビューも read-only のため pytest を実行していない。実装の存在は確認できても、受理・拒否集合の回帰がないことを実測済みとは扱えない。

## 総括

1. **閉包は不足あり（過剰なし）。** 指示された Silo runtime と V2 AST の2追加は正しいが、T419 binding が欠落し、T126 の明示 `code_identity` も完全 closure ではない。

2. **この wave の目的は達成。** 新 leaf から `env_contract`／`env_attestation` への逆辺がなく、将来 `env_contract` 初期化中に import・呼出ししても循環しない。

3. **親が次に実測すべきこと:** `tools/run_tests.py` 経由で対象3 test module、段4の登録変異、historical Silo evidence gate を実行し、特に「新 leaf だけ dirty」で T419 が fail-closed になる負例を追加・実測すること。T126 mapを変更するなら identity 再導出テストも必要である。