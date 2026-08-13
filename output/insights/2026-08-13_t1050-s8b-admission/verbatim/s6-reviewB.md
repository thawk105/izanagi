## 所見

### R-B1

- 対象 file:line: [s8b_binary_admission.py:298](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_binary_admission.py:298)、[s8b_floor_stats.py:927](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_floor_stats.py:927)、[s8b_holdout_freeze.py:1377](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_holdout_freeze.py:1377)
- 主張: `expected_cell_id` が指定されると、receipt subject と record 自身の `cell_id` の不一致が隠される。段 4 が要求した subject↔record 束縛が未完である。
- 根拠: validator は subject tuple を、record tupleではなく、指定された external expected tuple と一度だけ比較する。`verify_floor_artifact` は mapping key を `expected_cell_id` に渡す一方、`rec["cell_id"] == cell_id` を検査しない。このため mapping key と receipt subject を正しいまま `rec["cell_id"]` だけ変更しても通る。holdout candidate 経路も同じ組合せである。
- 成果物影響: `binaries[K].cell_id != K` の矛盾した official floor resultを受理し、その raw SHAを `floor_source` として参照する g1 candidateを生成できる。保存から candidate生成までの subject↔record 受理集合が意図より広い。
- 重大度: must-fix

### R-B2

- 対象 file:line: [s8b_binary_admission.py:36](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_binary_admission.py:36)、[test_s8b_floor_campaign.py:5325](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_floor_campaign.py:5325)
- 主張: M1は受理集合を緩める変異ではなく、期待赤を acceptance kill と数えられない。
- 根拠: key集合から `admission_receipt` を除いても、欠落recordは後段 validatorに拒否される。テストが赤になるのは診断が「exact key」から「無い/空」に変わるためである。さらに正例recordは receiptを持つため、逆に余分なkeyとして広範囲に拒否される。
- 成果物影響: 段 6 mutation matrixの M1 を `KILLED` と記録すると、受理集合が変わっていない診断差と正例破壊を検出力として誤記録する。
- 重大度: must-fix

### R-B3

- 対象 file:line: [s8b_binary_admission.py:241](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_binary_admission.py:241)、[test_s8b_binary_admission.py:137](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_binary_admission.py:137)
- 主張: M2の `None`／空object fixtureは過剰決定であり、専用missing gateの検出力を証明しない。
- 根拠: 242〜243行を無効化しても、`None` は244〜245行のobject型検査、空objectは246行のnested exact-key検査で拒否される。テストが赤になるのは `match="無い/空"` に診断が一致しなくなるためだけで、受理集合は変わらない。
- 成果物影響: mutation matrixの M2 が acceptance killではなく診断文字列感度を記録し、missing gateの単独実効性を誤認させる。
- 重大度: must-fix

### R-B4

- 対象 file:line: [test_s8b_oracle_driver.py:4521](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_oracle_driver.py:4521)、[s8b_oracle_driver.py:973](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/campaign/s8b_oracle_driver.py:973)
- 主張: M5はproduction入力では等価変異であり、テストhelperがvalidatorのpostconditionを破ることでだけ赤になる。
- 根拠: 通常はvalidatorが `subject.binary_sha256 == record.binary_sha256` を保証し、その直後に `actual == record.binary_sha256` も要求するため、978行の比較は推移的に成立する。テストはvalidatorの返却値を後から改変して、実入力では到達不能な状態を注入している。
- 成果物影響: 978行を削除しても外部入力の受理集合は変わらないのに、mutation matrixでは M5が `KILLED` になり得る。独立gateの実効性を過大報告する。
- 重大度: must-fix

## collection 破壊の検査

pytest collection自体は未実走。AST、import先の定義、呼出signature、fixture引数を静的照合した結果は次のとおり。

- `orchestrator/tests/s8b_v2_freeze_fixture.py`: 静的に落ちない。`_synthetic_floor_result(..., root=...)` の唯一の呼出は更新済みで、公開helperのsignatureは不変。
- `orchestrator/tests/test_s8b_floor_campaign.py`: 静的に落ちない。追加された`copy`と新module importは存在し、追加fixture引数は組込みの`tmp_path`。
- `orchestrator/tests/test_s8b_materialization.py`: 静的に落ちない。`_FakeBuildResult` の唯一の呼出は新しい`out_root`へ追随済み。
- `orchestrator/tests/test_s8b_oracle_driver.py`: 静的に落ちない。`copy`、`dataclasses`、`_plain_json`はいずれも定義済み。
- `orchestrator/tests/test_s8b_ratified_freeze.py`: 静的に落ちない。変更されたfixtureが使う`hashlib`、`Genome`、`PreparedCell`は既存import済み。
- `orchestrator/tests/test_s8b_ratified_verify.py`: 静的に落ちない。新規import先は存在し、`_portable_binaries`と`_validate_manifest`の全呼出が新signatureへ追随済み。
- `orchestrator/tests/test_s8b_binary_admission.py`: 静的に落ちない。全import symbolと`tmp_path` fixtureを確認した。
- 新moduleは`build_admission`と`source_digest`だけを下向きに参照しており、新規のcollection時循環importは見つからない。

## 取り残し数え上げ

差分外に残る手書きportable binary recordは **0箇所**。

ASTで `cell_id`、`binary_sha256`、`store_path` を同時に持つdictを数えた結果、test／fixture側は次の4箇所で、すべて今回の差分内か新規ファイルだった。

- [test_s8b_floor_campaign.py:5226](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_floor_campaign.py:5226)
- [s8b_v2_freeze_fixture.py:258](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/s8b_v2_freeze_fixture.py:258)
- [test_s8b_binary_admission.py:86](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_binary_admission.py:86)
- [test_s8b_ratified_verify.py:310](/work/1/SFC/tanab/izanagi/.codex/worktrees/dev-wave-t1050-s8b-admission/orchestrator/tests/test_s8b_ratified_verify.py:310)

非Python fixtureにも該当recordはなかった。未変更の`test_s8b_holdout_freeze.py`には共有helperの呼出が7箇所あるが、recordの手書きではなく、helperの公開signatureも変わっていない。

## 正当経路の検査

fresh build、store、projection、resolve、resume、oracle pre-runの各接続は、honest receiptについて静的に整合している。root依存の`source_root`は派生receiptから除外され、source tokenとportable pathもroot非依存なので、異なるroot間のdeterministic assertionを壊す要因は見つからない。

書込みなしの同型入力でproductionの`build_cells`、receipt issuer、portable projection、manifest serializerを呼び、literal値を独立照合した。

- binding SHA: `3cc28be2200a465d44e74641c3949624718205283ba6113edb529a33e657a37a`
- manifest SHA: `4860905ed2c9bf994886564bad0b3185f3d6e512230e85db43e57503f261fbc8`

いずれも変更後のliteralと一致した。ただしpytestによる正例実測ではない。

検出力は、M3とM4は単一gateを外すと負例が受理される形を静的確認できた。M1、M2、M5は上記所見のため、acceptance killとしては成立しない。

## scope 逸脱の検査

以下へのtracked差分、untracked追加はいずれも **なし**。

- `orchestrator/campaign/buildcache.py`
- `orchestrator/campaign/s8b_oracle_report.py`
- `orchestrator/campaign/s8b_oracle_judge.py`
- tracked `output/s8b-freeze`
- `docs/`

`V1_FREEZE_PATH`と`V1_FREEZE_SHA256`にも差分はない。

## 総括

判定は現状のままland不可。blockerは0件、must-fixは4件。  
collection時の未定義名、import破壊、signature不一致は静的には見つからなかった。  
差分外の手書きportable record取り残しは0箇所。  
honestなfresh経路とroot非依存性は静的に整合している。  
literal binding SHAとmanifest SHAはproduction serializerの出力と一致した。  
一方、record自身の`cell_id`とreceipt subjectの不一致を受理する穴が残る。  
M1とM2は診断差だけをkillと数える過剰決定fixtureである。  
M5はtest helperがvalidatorのpostconditionを破ることでしか発火しない等価変異である。  
非接触ファイル、tracked freeze、V1 trust root、docsへのscope逸脱はない。  
pytestは1件も実走しておらず、緑とは判定していない。