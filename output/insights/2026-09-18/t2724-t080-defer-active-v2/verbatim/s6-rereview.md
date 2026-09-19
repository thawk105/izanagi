## 対応表 (所見 ID → closed / partial / regressed、根拠)

対象は `24ede1d11..8b8bb96f2`。編集・pytest・変異注入は行っていません。対象実装ファイルの現物は `8b8bb96f2` と一致しています。

以下、`C/`＝`orchestrator/campaign/`、`T/`＝`orchestrator/tests/`、N5＝`focus-nochain-5.log`、C4＝`focus-chain-4.log`、C3＝`focus-chain-3.log`。ログの緑は指定焦点走の集計を意味し、通常受入や個別 PASS 一覧とは区別します。

| ID | 判定 | 根拠 |
|---|---|---|
| RA-1 | closed | `C/s8b_oracle_driver.py:run_block:1531` は gate 時 token を再利用。E3b の completed／同一 object assertion は `T/test_s8b_oracle_driver.py:6758` に維持。N5:42、C4:38 |
| RA-2 | closed | `T/test_s8b_ratified_freeze.py:build_production_emitter_g1:1035` で実 pin の regular blob を確認。接続正例は N5:34、全体結果は C4:38 |
| RA-3 | closed | `run_block:1531` の再解決は再 launch 成否に依存しない。changed／missing の exact epoch refusal を維持。N5:22,32,42 |
| RA-4 | partial | `T/test_s8b_oracle_driver.py:test_run_block_refuses_invalid_receipt_after_gate_seam:3283` を追加。m8b 除外も妥当。正式な kill 証拠は指定ログにない |
| RA-5 | closed | `T/test_s8b_floor_campaign.py:test_real_seal_protocol_to_floor_official_core_e2e:12626` が残存 chain record を独立列挙。C4:38 |
| RA-6 | closed | `T/test_ccbench_spawn_sites.py` の両 pin が production の1781／1794行と一致。N5:42 |
| RB-1 | closed | RA-2 と同じ。protocol 残存障害も basis 前除外で解消。N5:34,42 |
| RB-2 | closed | F1 の改訂裁定に従い再 launch／再走査を削除。missing・late-hit-file は exact epoch refusal。N5:22,30,32,42 |
| RB-3 | closed | RA-5 と同じ。preflight allowlist と digest 用集合を分離。C4:38 |
| RB-4 | closed | RA-6 と同じ。分類・件数 assertion は不変。N5:42 |
| RB-5 | closed | `T/test_s8b_oracle_driver.py:test_t080_active_v2_preserves_nonlayer2_receipt_refusal` が receipt と公開 gate の両方で trailer の単一拒否集合を要求。N5:19,42 |
| RB-6 | partial | conftest／golden は一致するが、登録解除後も emitter の親 root 読取りが残る。`T/test_s8b_ratified_freeze.py:1044,1047`。N5:42／C4:38 は競合不存在の証拠にはならない |
| RB-7 | closed | `T/test_real_repo_serialization.py:2926,5023`：正しい node 数で集合だけを壊し、旧 consumer 単独選択の不発火を確認。N5:42 |
| RB-8 | partial | N5:16–41 に duration は追加された。ただし base／copy の費用分離と通常受入300秒以内は未証明。N5:42、C4:38 |
| F1 | closed | `run_block:1531`、`C/t080_freeze_migration.py:_holdout_layer2_delegation:2221`。15 return と2回解決を維持。N5:42、C4:38 |
| F2 | closed | compiler input の引数化・regular blob 検査・source root の実 bytes hash。`T/test_s8b_ratified_freeze.py:498,1035`。N5:34,42 |
| F3 | closed | `[missing]` の epoch refusal と副作用不作成を維持。`T/test_s8b_oracle_driver.py:1795`。N5:32,42 |
| F4 | partial | m2b 観測 seam は実装済み、m8b は単独証拠から除外可能。正式 matrix は未確認 |
| F5 | closed | 独立 regex／tracked path／sha256 による期待 digest。allowlist 一致と clean_calls 2回は維持。C4:38 |
| F6 | closed | 両 sink の最終座標一致。N5:42 |
| F7 | closed | 必須の trailer 単一理由は固定。failed-launch は二つの拒否種別＋件数2。任意強化だった v1 の完全拒否集合化は未実施。N5:19,20,35,42 |
| F8 | partial | H2 指示どおり登録を戻したが、実アクセスとの不一致が残る。RB-6 と同じ |
| F9 | closed | RB-7 と同じ。N5:42 |
| F10 | closed | `C/s8b_holdout_freeze.py:1210,1247`、memo／driftguards／serialization の省略呼出しは token なしの従来経路。新 keyword は任意引数。N5:42 は補助証拠 |
| G1 | closed | `C/s8b_floor_campaign.py` の protocol 索引が既存 record に継承検査を適用する構造を確認（999行）。除外後は接続正例到達。N5:34 |
| G2 | closed | `T/test_s8b_oracle_driver.py:1438–1458` の宣言集合除外は basis commit:1525 より前。S は別集合。N5:34,42 |
| G3 | closed | fixture 自身の seed→C→G→A→X→実 load／launch／receipt 接続を確認。N5:34,42、C4:38 |
| G4 | closed | `7c007333b` は test builder のみ変更。production・S・sink pin の変更なし |
| H1 | closed | campaign layout 下の WAL、専用 marker／budget の不作成へ限定。`T/test_s8b_oracle_driver.py:1803,1823,1840,1857`。N5:22,30,32,42 |
| H2 | partial | shared-base・旧 digest・20 node pin は成立。今回 deadline は消失。ただし親 root 読取りの限定という前提が成立していない |
| H3 | closed | `8b8bb96f2` は test 3ファイルのみ。production・S・走査除外・hold・allowlist 不変 |

## F1 と E3b の整合

**改訂された F1 と実装は整合しています。**

`run_block` は最初の full launch validation の token を初回 receipt 解決と campaign-start 前の再解決に渡します。`fresh_validated`、その一致検査、campaign-start 専用の再 launch refusal 経路は残っていません。

| 境界 | 現物で確認した動作 | ログ |
|---|---|---|
| E3b disk-swap | 保持した floor artifact／同一 token を使用。既存 completed assertion は不変 | N5:42、C4:38 の失敗ゼロ |
| receipt changed | receipt raw bytes の変化で epoch identity 不一致 | N5:22,42 |
| receipt missing | 履歴検査が欠落を拒否。tracked 名称の列挙は維持され、不要な再走査が先行しない | N5:32,42 |
| late-hit-file | 非 ignored 新規 file により列挙 digest 不一致→委譲解除→通常 scan 拒否→epoch refusal | N5:30,42 |

AST から `run_block` の refusal-return を再計数して **15箇所**。成功経路の解決は初回と campaign-start 前の **2回**であり、既存 `verify_call.call_count == 2` は3970／4005行に残っています。

同名 file の内容交換は検出対象外です。これは F1 が明示的に認めた残余であり、「campaign-start でも fresh full validation 済み」とは表現できません。

## 接続 fixture と登録簿

**共有化・copy 分離は成立していますが、登録解除の根拠は部分的です。**

- `_T080SharedBases.get:924` は4要素 key に `False` を補い、digest 入力には元の4要素を使用します。旧 digest は不変です。
- active-v2 は5要素全体で区別され、不正 trailer も別 key です。
- 除外は basis commit 前。v1 holdout、known-axes、positive control、必要な実装は保持されます。
- `_t080_stub_free_e2e_repo:1012` は `copytree`、document は `deepcopy`。token は各 copy 上の実 `launch_validate` で取得し直します。
- 新 cache test:1217 は旧 digest、active／通常／不正 trailer の分離、copy の書換え独立性を要求しています。

consumer の原コードからの再計算は次のとおりです。

| 集合 | 関数 | node |
|---|---:|---:|
| 既存 consumer | 6 | 11 |
| active-v2 接続 | 7 | 8 |
| draft 負例 | 1 | 1 |
| 合計 | 14 | 20 |

したがって「接続9 node」は **接続8＋draft1** の略称です。接続だけで9ではありません。conftest から消えたのは8関数／9 node。独立 golden と inventory はともに148要素です。

一方、`build_production_emitter_g1:1044` は **各接続構築で** `_real_bytes(calibration_path)` を呼び、1047行には不足する selector 材料を親 root から読む経路もあります。base 構築自体も親 source／output／Git 履歴／共有 ccbench を読みます。cache の key lock はこの構築の重複を抑えますが、real-repo writer と共有する lock ではありません。

「実 root 読取りは base の1回だけ」は誤りです。fix-3 報告:76 の留保が正確です。

`root=ROOT` を直接渡す driver test は AST で **14関数**でした。

| test 名（`test_` を省略） | 呼出し行 | inventory |
|---|---|---|
| `t080_static_adapter_rejects_noncanonical_known_predicate_as_schema` | 2295,2322 | 未登録 |
| `run_block_refuses_invalid_receipt_after_gate_seam` | 3297 | 登録 |
| `spec_matching_gate_and_run_reach_execution_but_other_spec_refuses_without_outputs` | 3356,3361,3383 | 未登録 |
| `gate_check_rebinds_each_injected_verified_manifest_axis` | 3418,3426 | 未登録 |
| `cli_output_root_default_is_none_and_run_block_refuses_without_root` | 3642,3662 | 未登録 |
| `real_freeze_gate_lists_floor_and_budget_null` | 3766 | 登録 |
| `run_block_refusal_writes_no_campaign_or_budget_and_calls_nothing` | 4043 | 登録 |
| `nonnull_floor_without_active_generation_is_refused` | 4523 | 登録 |
| `active_resolution_and_manifest_structure_refusals_are_aggregated` | 4553 | 登録 |
| `run_block_reuses_launch_validated_and_legacy_loader_is_dead` | 5485 | 未登録 |
| `run_block_verifies_manifest_once_and_reuses_object` | 5561 | 未登録 |
| `oracle_admission_uses_verified_manifest_schedule_and_reps` | 6436 | 未登録 |
| `oracle_repeated_reservation_is_admitted` | 6481,6486 | 未登録 |
| `oracle_attempt_single_use_is_scoped_to_measurement_generation` | 6526,6531 | 未登録 |

加えて helper 内の直接呼出しが `_run:3248`、`_run_required_preflight:3484`、`_required_run_fixture:3569` にあります。直接 consumer はそれぞれ25／5／9関数です。

新規追加分で `root=ROOT` を渡すのは seam 負例だけですが、**module 全体でそれだけではありません**。既存の未登録項目を今回の新規退行とは扱いません。また literal の有無だけではアクセスを分類できず、接続8 node のような helper 経由の親読取りを別途数える必要があります。

## 両木の赤の帰属と 45 node の照合

| ログ | 結果 | FAILED／INTERNALERROR |
|---|---|---|
| N5:42 | 2672 passed、36 skipped、301.12秒 | ともに0 |
| C4:38 | 1097 passed、11 skipped、488.84秒 | ともに0 |

修正前リストは **45行・45 unique node**。全 node の test 名は現物に残っています。

| 修正前の経路 | node 数 | fix-3 後の失敗集合との交差 |
|---|---:|---:|
| T-080 copy／構築 | 10 | 0 |
| floor clone／preflight | 5 | 0 |
| memo 依存切離し | 29 | 0 |
| g7 | 1 | 0 |
| 合計 | 45 | 0 |

原リストの file 別集計も **driver 40＋floor 5＝45** と一致します。

指定された7 file 焦点走の結果として、45件の赤はすべて解消したと判断できます。ただし C4 は個別 PASS nodeid 一覧ではないため、**45件それぞれの PASS 行を照合したという意味ではありません**。N5 は stdout の17600 bytes、C4 は66 bytes が省略されています。

C3:101 の `ccbench mode=read` deadline と、C3:136 の crashitem は今回再発していません。ただし登録解除で待機者を減らした結果と、競合の root cause を安全に閉じた結果は区別が必要です。

親の派生値には訂正が必要です。

- C3:147 は **2 failed／1088 passed／7 skipped**。C3:240 の failure digest は **errors=0**。別途 INTERNALERROR はありますが、「2 errors」という pytest 集計は原ログから確認できません。
- C3 は中断走で個別 PASS 一覧もありません。「接続6 node が緑」の exact 集合は同ログだけでは確定できません。
- 接続8 node のうち campaign-start 3 node が赤なら、残りの接続は **5 node**。draft を含めれば6 nodeです。

## 受理集合の最終差分

全体は **13ファイル、796行追加・158行削除**。production の変更は driver／ratified-freeze／migration の3ファイルです。

| 境界 | 最終実装 |
|---|---|
| token 型 | exact `LaunchValidatedFreeze` のみ |
| root | resolve 済み validation root と一致 |
| HEAD | outer token／validation HEAD／実 HEAD、および ratified HEAD を照合 |
| active 世代 | live 再解決の HEAD・SHA・番号・導入 commit を照合 |
| 列挙 | live `_enumeration_digest` と一致 |
| report | full scan、C2-4 完全一致、artifact 再捕捉後に deep-freeze |
| 凍結文書束縛 | ratified document と入力 holdout document の両方に適用 |
| predicate 不成立 | 通常 scan／zero-hit 検査へ戻る |
| 非層2拒否 | receipt 履歴・bytes・導出・closure 等の既存検査を維持 |
| v1／token 省略 | 従来経路。driver から adapter への token 転送追加なし |

意図した委譲と F1 の残余以外に、受理を広げる production 経路は見つかりませんでした。

**production の走査除外・hold・allowlist・G／chain artifact bytes は変更0 byte**。test の S は official namespace＋candidate exact file の宣言集合です。active-v2 専用の初期材料除外とは分離されています。

F5 の期待 digest 更新は親の明示裁定に基づく独立 oracle の修正であり、production の chain record 束縛を緩めていません。

## 変異の帰属表

以下は現物上の照準と観測経路です。**正式な注入・kill／SURVIVED の実測結果ではありません。** 関数名と分岐を含めれば各 anchor は一意です。

| ID | anchor | fix-3 後の観測 test／帰属 |
|---|---|---|
| m0 | migration `_holdout_layer2_delegation:2231` の comment | SURVIVED 正例。未観測 |
| m1 | ratified `_launch_validate:3550` の完全一致比較 | `test_t080_failed_launch_preserves_receipt_refusal`。実 launch の拒否を直接観測 |
| m2a | driver `_make_gate_decision:200` | `test_t080_active_v2_preserves_nonlayer2_receipt_refusal`。他理由を混ぜず公開 gate の allowed を観測 |
| m2b | driver `_campaign_t080_value:219` の invalid 拒否 | `test_run_block_refuses_invalid_receipt_after_gate_seam`。先行 gate のみを開け、対象関数は実物 |
| m3 | migration `_verify_holdout_live_scan:2274–2275` | `test_t080_unactivated_chain_hit_is_invalid`。実 scan の非委譲 zero-hit 拒否。前段の scan 取得分岐とは区別 |
| m4a | migration `_assert_holdout_report_bindings:2215` | `test_delegated_scan_keeps_frozen_document_bindings[expressions]`。正常 token を保ち入力文書だけ変更 |
| m4b | 同`:2202` | 同 `[match_convention]`。実束縛比較を直接観測 |
| m5 | driver `run_block:1531` の再解決＋epoch 比較 | `test_t080_delegated_campaign_start_rechecks_receipt[changed]` と既存 `test_run_block_rejects_receipt_epoch_drift_before_campaign_start_g4` |
| m6 | migration predicate`:2236` の outer HEAD 比較 | `test_layer2_delegation_rejects_wrong_activation_head`。outer field のみ変更。実 HEAD 比較は変異後も残す |
| m7 | 同`:2247` の列挙 digest 比較 | `test_layer2_delegation_rejects_enumeration_drift`。namespace 外への追加で世代検査による代役拒否を避ける |
| m8a | floor `clean_scan_digest:5534` の search assertion | `test_clean_scan_rejects_synthetic_chain_artifacts[official|candidate|both]`。無害対照→実 hit→実 clean scan 拒否 |
| m9 | migration predicate`:2234` の root 比較 | `test_layer2_delegation_rejects_foreign_root`。同 HEAD・同列挙の最初の clone 検査が独立証拠 |
| m10 | 同`:2241–2246` の世代再解決・比較 | `test_layer2_delegation_rejects_stale_generation_token`。世代文書 bytes の変更を実 resolver が拒否 |

m8b は後段 verifier に mask されるため除外が妥当。draft 負例は実機構の負例として維持されています。m11 は F1 により対象操作自体がなくなったため除外が妥当です。m5 の missing は、指示どおり単独 kill 証拠に数えません。

## 所見 (RR-1 …)

**RR-1 — must-fix：登録解除の前提となる実 root 読取りの限定が未成立。**

[接続 emitter](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2724-t080-defer-active-v2/orchestrator/tests/test_s8b_ratified_freeze.py:1043) は copy 後にも親 calibration を読み、不足する selector 材料も親から補います。shared-base の key lock は real-repo writer を排除しません。H2 の指示形は実装されていますが、RB-6 の root cause を closed とする根拠は不足しています。既存 fixture 内の材料供給と残存アクセスの整合が必要です。

成果物影響：並列受入で親 repo の変更と接続 fixture の材料取得が競合し、焦点緑の再現性を保証できません。

**RR-2 — should：共有化後も時間目標と base／copy の費用が未確定。**

接続8 node は通常 key 7件・不正 trailer key 1件なので、xdist session 内では **2 base＋8 copy**。draft は既存通常 base を共有します。C→G→A→X と launch は各 node に残ります。

N5 の接続 call は152.84～192.65秒、draft は178.27秒。待機・構築・copy・検証を含むため、base 単独費用には使えません。N5 は301.12秒、C4 は488.84秒。prewarm も42.77／46.01秒残っています。

成果物影響：通常受入300秒以内、または共有化による削減秒数を達成値として記録できません。

**RR-3 — should：変異の実測は引き続き未完。**

m2b の観測欠落は実装修正されていますが、baseline 緑だけでは変異検出力を証明しません。指定資料には正式 matrix の結果がありません。

成果物影響：変異受入および T-2776 の完了を、このレビューだけで確定できません。

**RR-4 — should：親報告の件数と量化を原ログに合わせる必要がある。**

「接続9」はdraft込み、「base1回」はkeyごと、「2 errors」はC3の集計と不一致です。中断ログから個別 PASS 集合を確定したという表現も避ける必要があります。

成果物影響：根拠以上の完了範囲や障害件数が後続の受入記録へ伝播します。

## 総括

F1／E3b、接続構築、epoch 拒否、floor digest、sink pin の既知赤は解消しています。両木の焦点走は失敗ゼロ、修正前45 node の残存赤もゼロです。

ただし、登録解除後の親 root 読取りが残り、RB-6／F8／H2 の root cause は閉じていません。正式な変異実測と通常受入の時間評価も未完です。

NO-GO