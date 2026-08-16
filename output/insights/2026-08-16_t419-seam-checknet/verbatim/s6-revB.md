### consumer 棚卸し

- composite callback の production 呼び手は通常 loader `orchestrator/campaign/env_contract.py:570-575`、`ident` の current chain と記録済み chain `orchestrator/campaign/ident.py:217-225,306-314`、activation 発行 tool `tools/issue_env_contract_activation.py:205-213` の 4 箇所、3 経路。
- executable fixture は `orchestrator/tests/calibration_freeze_authority_execution.py:137-140` で composite を事前確認する一方、凍結呼出し自体は意図的に構造 callback のまま `:162-168`。
- resolver の production 呼び手は floor writer admission の 1 箇所だけ `orchestrator/campaign/certified_writer_admission.py:206-224`。公開 `admit` からの dispatch は同ファイル `:400-418`。
- literal path の production consumer は floor campaign、holdout admission、holdout freeze、prediction runner、ratified freeze、floor shell の 6 ファイル。`hooks/` に該当 consumer は無い。
- `ident.verify_recorded_activation_tuple` の downstream は artifact admission `orchestrator/campaign/artifact_admission.py:826-833` と campaign resume `orchestrator/campaign/ident.py:369-377`。

### RB-01 — 4 面の拒否理由が generic bool に潰れる

主張: composite は自己整合、method、content-address、receipt の全失敗を `False` に縮退させ、activation validator は env_tag 付きの「正当な successor でない」に変換する。運用者にはどの較正面を直すべきか届かない。

証拠: `orchestrator/campaign/env_contract.py:451-478` は検証例外も各比較失敗も `False` にする。`orchestrator/campaign/env_contract_activation.py:299-329` はそれを generic な `ActivationRecordError` に変換する。通常 loader はさらに `orchestrator/campaign/env_contract.py:579-580`、campaign lock は `orchestrator/campaign/ident.py:323-328`、発行 tool は `tools/issue_env_contract_activation.py:215-216` で包む。4 面テストも `orchestrator/tests/test_env_contract_activation.py:1541-1555` では `False` だけを検査し、診断面を固定していない。

成果物影響: activation が拒否されても certified 選択、report、台帳に失敗面が残らず、実験停止理由を特定できない。

severity: land 阻止

### RB-02 — `ident.py` の 2 配線は変異を殺すテストが無い

主張: 通常 loader と issue tool は callback identity をテストしているが、campaign lock を守る `ident.py` の current chain と recorded prefix の 2 箇所には同等の配線テストが無い。構造 callback へ戻す変異が生存する。

証拠: 対象配線は `orchestrator/campaign/ident.py:217-225,306-314`。追加された identity 検査は通常 loader の `orchestrator/tests/test_env_contract_activation.py:1797-1800` と issue tool の `:2427-2440` だけ。既存の campaign-lock テストは現行 serial 1 を使い、callback は record 2 本目以降だけ呼ばれる `orchestrator/campaign/env_contract_activation.py:364-401`。直接 composite を検査する4面テスト `orchestrator/tests/test_env_contract_activation.py:1541-1555` も `ident` の配線を通らない。

成果物影響: `ident` だけ構造判定へ退行すると、不正較正を持つ future generation の campaign.lock が resume／artifact admission で真正扱いされ、台帳の受理集合が広がる。

severity: land 阻止

### RB-03 — 既知 4 赤は fixture 欠陥だが、全件「65環境由来」ではない

主張: 4 件に production 欠陥は混ざっていない。ただし親の原因分類は不正確で、2 件は 65 環境 fixture ではなく、実在 registry を一時 root へ向けながら g2 calibration をコピーしていない fixture である。

証拠: 65 環境 fixture は存在しない calibration path を合成する `orchestrator/tests/test_env_contract_activation.py:76-114`。該当するのは loader 負例 `:1826-1849` と issue 負例 `:2582-2615`。一方、success と identity は実在 `ec.GENERATIONS` を使うが `_repository_root` を空の `tmp_path` に替える `:2331-2366,2393-2438`。production composite はその root から較正を必須読込する `orchestrator/campaign/env_contract.py:450-462` ため、拒否は正しい。

成果物影響: production の certified 受理集合は変わらないが、4 件の偽赤を残すと受入結果を確定できず land の証拠が成立しない。

severity: fix

修正時は、65 環境の構造 scale テストだけ composite を構造 callback へ隔離し、実在 g2 の success／identity テストには較正 artifact を一時 root へコピーして composite を実際に通す必要がある。

### RB-04 — floor resolver と downstream path consumer はまだ分断されている

主張: resolver は preflight admission にだけ入り、同じ floor job はその後 legacy literal を driver と結果 writerへ渡す。5 Python consumer も literal のままである。これは段4で明示的に裁定へ返された残件だが、end-to-end seam が閉じたという解釈はできない。

証拠: preflight は resolver の record を検証する `orchestrator/campaign/certified_writer_admission.py:206-224`。同じ shell は preflight 成功後、`tools/pegasus/floor_campaign.sh:947-965,972-973,1093-1095` で固定 path を使う。残る Python consumer は `orchestrator/campaign/s8b_holdout_admission.py:376-386`、`s8b_holdout_freeze.py:1287-1300`、`s8b_prediction_runner.py:1542-1549`、`s8b_ratified_freeze.py:2646-2648`。

成果物影響: resolver が reseal path を選ぶ世代では preflight と実投入が別 protocol を参照し、床値実験が停止するか、freeze・selector・ratified report が旧参照を保持する。

severity: fix

### RB-05 — future activation の初回 load で較正を重複読込する

主張: 現行 serial 1 では composite は呼ばれないため現在の起動コスト増はない。しかし serial 2 以降は各 changed successor の較正 JSONを二重に読んで parse し、その後 active entry を三度目に検証する。chain 長に比例して増える。

証拠: callback は `_verify_entry_calibration` を呼んだ後に再度 `load_verified_calibration` を呼ぶ `orchestrator/campaign/env_contract.py:451-462`。前者自身も同 loader を呼ぶ `:532-559`。authority load 後は active entry を再検証する `:583-590`。transition は changed row 全件を走査する `orchestrator/campaign/env_contract_activation.py:299-324`。process 内 cache は初回 load 後だけ有効 `orchestrator/campaign/env_contract.py:624-634`。`ident` は current chain と記録 prefix を別々に検証する `orchestrator/campaign/ident.py:293-314`。

成果物影響:値や受理集合は変えないが、世代数と変更 env 数に比例して experiment 起動・campaign-lock admission が遅くなり、timeout 時は report／台帳が生成されない。

severity: fix

### 4 面負例の実効性

4 面はいずれも単一理由である。fixture は変更後 bytes の hash と content-addressed path を再導出し `orchestrator/tests/test_env_contract_activation.py:1473-1501`、構造判定が通ることも `:1549-1554` で確認する。

- 自己整合: sample だけを帯外化 `:1463-1465`。
- method: method だけを変更 `:1466-1467`。
- content-address: bytes と SHA を保ち path だけを不正化 `:1481-1487`。
- receipt: PBS job ID だけを変え `:1468-1469`、qsub ID との内部束縛 `orchestrator/calibrator/schema_v2.py:532-535` だけを壊す。

各 gate を無効化すれば最終 `False` assertion が落ちるため、実装の単なる写経で恒真にはなっていない。ただし拒否面の診断を一切検査しない問題は RB-01 のとおり。

### meta-test 判定

`orchestrator/tests/test_s8b_protocol_builder.py:998-1027` は完全に無効ではない。既知 6 assignment の値変更、削除、重複、regex から外れる変更、resolver が別 path を返す変更では落ちる。

一方で、固定された6ファイル以外への新 consumer 追加、constant を使わず別 path を読む変更、実行時に resolver record と同じ path を使うことは検査しない。したがって「将来の path 切替を test gate で止める tripwire」であり、consumer の runtime rewire 証明ではない。

## 総括

- 変更 symbol と literal path の production consumer は上記ですべて列挙した。
- 4 面の負例はそれぞれ単一理由で、gate 除去への検出力もある。
- 既知 4 赤は fixture 欠陥であり、production 欠陥ではない。
- ただし 2 件は 65 環境 fixture ではなく、実在 g2 artifact を欠く一時 root fixture である。
- composite の拒否理由は全経路で generic message に潰れ、診断可能性を満たさない。
- `ident.py` の 2 配線はテストされず、事前登録された wiring 変異が生存する。
- floor meta-test は tripwire として有効だが、runtime consumer の再配線は証明しない。
- pytest、build、campaign は実走しておらず、緑は申告しない。
- GO / NO-GO: **NO-GO**。RB-01 と RB-02を閉じ、既知4 fixture赤を是正してから再レビューが必要。