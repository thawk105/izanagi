## 所見

1. **`reseal_protocol()` の production caller zero は誤り**

   - 主張: issuer 自体は存在し、CLI 経路から本番相当の実行が可能。Pegasus job script からの自動呼出しは確認できない。
   - file:line: `orchestrator/campaign/s8b_floor_campaign.py:6566-6570,6689-6701`、`tools/pegasus/floor_campaign.sh:969-978`
   - 具体的な失敗シナリオ: `python3 orchestrator/campaign/s8b_floor_campaign.py reseal-protocol` → `reseal_protocol()` が実行され、versioned protocol を発行する。
   - 深刻度: must-fix

2. **M6 の `count=2` は real**

   - 主張: 現行 g1 contract と legacy anchor が一致している状態で `reseal_protocol()` を呼ぶと、同じ current contract に一致する legacy と versioned の二件が残る。
   - file:line: `orchestrator/campaign/s8b_floor_campaign.py:782-901,936-1067`、`orchestrator/tests/test_s8b_protocol_builder.py:1053-1084`
   - 具体的な失敗シナリオ: contract=`e576e9cd`、gitlink=`511c9538`、legacy pin=`d706...` → `reseal_protocol()` が `floor-protocols/e576...--511...json` を作成 → `resolve_current_floor_protocol()` が `count=2` で拒否する。
   - 深刻度: blocker

3. **凍結 hold の評価は限定的に real**

   - 主張: `HELD_CHECK_IDS` と protocol-bytes check の hold は production に存在する。一方、sealed protocol の current-head pin 検査は production caller がなく、テスト helper にしかない。
   - file:line: `orchestrator/campaign/freeze_verification_hold.py:14-48,68-75`、`orchestrator/campaign/s8b_floor_campaign.py:3628-3635`、`orchestrator/tests/test_s8b_floor_campaign.py:1210-1236`
   - 具体的な失敗シナリオ: production で current-head pin が不一致 → sealed check の production 呼出しがないため拒否されない。一方、protocol bytes 検査を通る → `held_marker("s8b-floor.protocol-bytes-expected-pin")` が返る。
   - 深刻度: must-fix

4. **(R2) の fail-closed は、記録欄を追加するだけでは成立しない**

   - 主張: plan は記録生成と再読込を意図しているが、全 production entrypoint に「記録がないと driver/build/measure に進めない」という単一の強制点を示していない。
   - file:line: `s2-plan.md:71,74,114-116,125`、`orchestrator/campaign/s8b_floor_campaign.py:5409-5452,5556,6749-6770`、`tools/pegasus/floor_campaign.sh:967-978`
   - 具体的な失敗シナリオ: valid な submit receipt と `--protocol` だけを渡し、提案された remeasurement record を作らず直接 CLI を起動 → 現行コードは record の存在を検査せず `run_campaign()` へ進む。拒否されても固定 path gate の拒否であり、record 欠落を原因とする fail-closed ではない。
   - 深刻度: blocker

5. **記録の存続と測定結果の結合が不足している**

   - 主張: plan の record は測定前に作成するが、測定後の job result や liveness result が record path/hash を必須化していない。
   - file:line: `s2-plan.md:47-64,74,79`、`tools/pegasus/floor_campaign.sh:1104-1140`、`orchestrator/campaign/floor_liveness.py:55-83`
   - 具体的な失敗シナリオ: record を検査後に削除または差し替え → job result は `protocol_path`、source commit、nonce だけで完了扱いになり、論文側で参照する record が測定結果に結び付かない。
   - 深刻度: blocker

6. **記録入力だけでは第三者による再構成が不十分**

   - 主張: plan の `source_commit` は submit 時の source identity と measurement head を区別せず、activation 世代も記録しない。`sha256` も raw bytes hash か canonical JSON hash か曖昧。
   - file:line: `s2-plan.md:55-64`、`orchestrator/campaign/floor_submit_receipt.py:90-159`、`orchestrator/campaign/s8b_floor_campaign.py:395-396,753-757,5610`、`orchestrator/campaign/s8b_holdout_admission.py:486,2086-2115`、`orchestrator/campaign/env_contract_activation.py:15-28,74-97`
   - 具体的な失敗シナリオ: `source_commit=C`、`contract_sha256=H`、`ccbench_pin=P` は同じでも、実測時の `HEAD`、activation serial、activation state hash が異なる → 第三者は「どの gitlink、どの activation、どの bytes を測ったか」を確定できない。`held_check_ids=[]` も「hold なし」と「記録欠落」を区別できない。
   - 深刻度: must-fix

7. **既存の receipt、ledger、marker との二重記録になる**

   - 主張: 新 record は必要になり得るが、既存機構との結合仕様がなく、同じ identity を別 schema で再発明している。
   - file:line: `s2-plan.md:47-64,70-80`、`orchestrator/campaign/floor_submit_receipt.py:13-19,39-98`、`tools/pegasus/floor_campaign.sh:1104-1140`、`orchestrator/campaign/s8b_holdout_admission.py:1794-1812,2086-2115,2288-2307`、`orchestrator/campaign/floor_liveness.py:35,55-83`
   - 具体的な失敗シナリオ: submit receipt は legacy path、new record は versioned path、job result は別 hash、holdout ledger は別 `measurement_head` → 各ファイル単体は妥当に見えるが、同一測定の証拠が分裂する。
   - 深刻度: must-fix

8. **新 path/schema の pin 閉包が未成立**

   - 主張: `output/env/.../floor-remeasurement-attempt.json` と `s8b-floor-remeasurement-attempt/v1` は既存の frozen manifest、chain record pattern、receipt meta-test では pin されていない。
   - file:line: `s2-plan.md:47-64`、`orchestrator/tests/test_frozen_artifacts.py:41-49,90-124`、`orchestrator/campaign/s8b_floor_campaign.py:265-272,3842-3849,3904-3911`、`orchestrator/tests/test_floor_submit_receipt.py:18,43-50,309-326`
   - 具体的な失敗シナリオ: schema 名や path を変更しても既存 checker は成功し、`output/env` の record bytes の変更も freeze chain の bytes hash に反映されない → 記録欄が存在するだけで、形式と内容の不変性を担保しない。
   - 深刻度: must-fix

9. **t657 着地後も第二の主 gate は残る**

   - 主張: t657 が activation g2 と target pair `(1346c20b,511c9538)` の versioned protocol を実際に着地させたという前提なら、resolver は通る。しかし holdout authority と Pegasus wrapper は legacy 固定のまま。
   - file:line: `orchestrator/campaign/s8b_floor_campaign.py:882-901`、`orchestrator/campaign/s8b_holdout_admission.py:64-65,463-490`、`tools/pegasus/floor_campaign.sh:954-986`
   - 具体的な失敗シナリオ: g2 versioned protocol を渡す → `_authority()` が `output/s8b-freeze/floor_protocol.json` の HEAD bytes を読み、`fixed protocol bytes do not match the supplied protocol` で拒否する。legacy path を shell から渡す → `s8b_floor_campaign.py:5556` の current contract 検査で g1 protocol が拒否される。
   - 深刻度: blocker

10. **scope は概ね守られているが、versioned path の全体置換は範囲外**

   - 主張: plan は T-419 本体、HELD の解除、frozen legacy artifact の変更を明示的に避けており、過剰実装は確認できない。ただし selector、prediction、freeze registration まで versioned path に置換すると裁定範囲を超える。
   - file:line: `s2-plan.md:75-80,124-134`、`orchestrator/campaign/s8b_prediction_runner.py:79-80,1542-1549`、`orchestrator/campaign/s8b_holdout_freeze.py:46-48,1293-1304,1647-1651`、`orchestrator/tests/test_frozen_artifacts.py:41-49`
   - 具体的な失敗シナリオ: 再測定用 protocol を selector 側へも適用 → frozen manifest や ratified freeze の固定 trust root と衝突し、再測定 lane の修正が別の凍結解除へ波及する。
   - 深刻度: nit

## 親の実測の裏取り結果

- `reseal_protocol()` の存在: **real**。`orchestrator/campaign/s8b_floor_campaign.py:1070-1072`。
- 「production caller はゼロ」: **refuted**。CLI dispatcher が `orchestrator/campaign/s8b_floor_campaign.py:6689-6701` で呼ぶ。Pegasus job script に同 CLI の呼出しはなく、そこだけは親の見立てどおり。
- `HELD_CHECK_IDS` による hold: **real**。`freeze_verification_hold.py:14-48` と protocol-bytes の production marker `s8b_floor_campaign.py:3628-3635`。
- sealed current-head pin 検査が production gate であるという意味なら: **refuted**。確認できる呼出しはテスト helper `test_s8b_floor_campaign.py:1210-1236` のみ。
- M6 の `count=2`: **real**。現行 g1 状態では reseal 後に legacy と versioned の二件が current contract に一致する。

## 実装後に床値 v2 再測定を妨げる残り条件

1. t657 の activation head と target versioned protocol が、実際に同じ repo の HEAD にあること。working tree だけの artifact では `_head_blob` 検査を通らない。
2. record の生成、strict loader、bytes hash 検査を、CLI、wrapper、driver、holdout admission の全経路で必須化すること。欠落、改変、重複、nonce 不一致は driver 起動前に停止が必要。
3. `floor_campaign.sh:954-986` の固定 legacy path を、record が選んだ versioned protocol と同一になるよう変更すること。
4. 固定 path 専用の `_authority()` とは別に、current contract、gitlink、HEAD blob、worktree bytes、record、submit receipt を同時検証する remeasurement authority が必要。
5. submit receipt の source commit、job script hash、PBS job、submission nonce、current HEAD の結合を維持すること。
6. `confirm_irreversible_pilot_holdout=True`、compute site、calibration、予約済み one-shot admission は引き続き必要。これらを外すことは裁定達成ではない。
7. `HELD_CHECK_IDS` と frozen legacy bytes は引き続き変更しないこと。hold の解除はこの wave の着手条件ではない。
8. 測定後の job result または ledger に record path と record raw hash を残し、事後削除で証拠が消えないようにすること。
9. prediction、ratified freeze、official registration は依然として固定 legacy path を使う。これは pilot 再測定の着手阻害ではないが、結果の正式登録には別途残る条件である。

## 総括

M6 は real だが、親の「production caller zero」は CLI 経路により refuted である。  
t657 着地後は resolver だけ通り、holdout authority と Pegasus wrapper の legacy 固定は残る。  
record は作るだけでは R2 を満たさず、全経路での強制、入力閉包、事後結果との結合、pin 閉包が必要である。  
したがって、この wave は存続し、最小変更面は versioned protocol に束縛された remeasurement lane である。