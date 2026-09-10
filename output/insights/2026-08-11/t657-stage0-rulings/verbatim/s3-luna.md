## LUNA-01 / blocker

破れる具体構成: `revocations/<bundle_digest>.json` と exact 7-key schema、0/1件制約を段4で確定実装する。しかし裁定正本 §8 は namespace/schema を未選択の問いとして残し、no-fallback は推奨に留まる。

根拠: `output/insights/2026-08-11_t657-stage0/package.md:168-171`、`s1-brief.md:54-60`、`s2-plan.md:72-92`、`docs/calibration-freeze-authority-bundle-design.md:437-438`

放置すると、ユーザー未裁定の revocation 受理集合が設計正本へ固定され、certified authority の有無、fallback 可否、レポートと台帳の「resolved」が未承認の policy を表す。

## LUNA-02 / must-fix

破れる具体構成: 同じ手書き9-entry表から manifest の `entries_sha256`、`_EXPECTED_REQUIRED_GATES`、module pin を一括生成する。`stage-fixture-waves` の typo や gate status の誤りも、manifest と検査側を同時更新すれば pin 同士は一致する。

根拠: `docs/calibration-freeze-authority-bundle-design.md:610-612`、`s2-plan.md:152-160,190-197,208-231`、`calibration_freeze_authority_contract.py:345-350,412-428`

放置すると、実 file 集合・manifest literal・独立期待値の三者ではなく、manifest と同じ入力から作った二者照合になる。親の手動 `b5aae8d5…` 照合だけが最後の防壁で、機械的な pin ではない。gate の受理集合と stage 0 の阻害数が移動する。

## LUNA-03 / must-fix

破れる具体構成: `CFAB-STAGE6-COMPLETION-PREDICATE` を `resolved` にし、manifest hash と `_EXPECTED_REQUIRED_GATES` も更新する。gate schema に evidence や owner の実体参照がないため、誰も predicate を閉じていなくても宣言だけで進められる。

根拠: `s2-plan.md:165-181,241-247`、`calibration_freeze_authority_contract.py:387-428,746-805`、`docs/calibration-freeze-authority-bundle-design.md:666-675`

放置すると、現時点では pending 5件が誤りを隠し、将来それらが消えた時点で `require_stage0_complete` が無証拠の stage 0 を受理する。certified 選択、完了レポート、台帳の blocker 数が過少になる。

## LUNA-04 / must-fix

破れる具体構成: §8.1 の `CFAB-Q3-REVOCATION` の許容 selection を `allow-lower-fallback` に変更するが、`_SELECTION_ENUMS` と profile は変更しない。`_extract_ruling_ids` は ID しか抽出しないため、profile 検査は通る。

根拠: `docs/calibration-freeze-authority-bundle-design.md:468-500`、`calibration_freeze_authority_contract.py:266-284,469-508`、`s2-plan.md:94-106,148-160`

放置すると、設計正本の許容 selection と検査側の policy literal が drift する。逆に code/profile 側だけ fallback 値へ変更しても、docs の表は検出しない。certified selection、resolver の受理集合、レポートの説明が一致しない。

## LUNA-05 / must-fix

破れる具体構成: 設計 §11 に `| CFAB-11.2-02 | ... |` の行を追加する。抽出器は 11.2 の表行を拾わず、`row_coverage` と row hash は従来の10行のまま変わらない。あるいは `_DESIGN_ROW_PATTERN` を無関係な pattern に変え、manifest も同じ文字列へ変えても通る。

根拠: `docs/calibration-freeze-authority-bundle-design.md:307-308`、`calibration_freeze_authority_contract.py:42-51,251-257,310-317`

放置すると、設計に追加された不変条件が fixture 閉包から抜け、未検査の行を含む report が「全 row coverage」として受理される。`_DESIGN_ROW_PATTERN` は extraction に使われず、manifest との文字列一致だけである。

## LUNA-06 / must-fix（scope外なら裁定パッケージ候補）

破れる具体構成: profile の `selection` を実際の resolver/policy が無視し、`activation-window` と別 selection を同じ挙動にする。現行 execution module は profile を import せず、`run_all_executable` も manifest と executable case しか実行しない。上位 resolver・候補型・bundle identity の case はすべて pending のままである。

根拠: `docs/calibration-freeze-authority-bundle-design.md:323-329,456-459`、`calibration_freeze_authority_execution.py:16-20,709-738`、`s2-plan.md:183-188,203-230`、`cases/approved-freeze-reference.json:1`

放置すると、selection を exact に記録しただけで、certified 選択・authority report・実行台帳の挙動は変わらない。「段0の帳簿更新」に限定するなら、resolver policy を実装した成果物と誤認しない裁定パッケージへ返すべきである。

## LUNA-07 / must-fix

破れる具体構成と先取り:

- U-A1 を `post-activation-lease` に変える変異は、selection enum 検査 (`calibration_freeze_authority_contract.py:469-477`) が先に落とす。state pin の検出力は測れない。
- S を S2 に変える変異は、G が unresolved のままだと既存 applicability 検査 (`:494-503`) が先に落とす。S1 なら state pin まで届く。
- G を `resolved/G-a` に変える変異は既存の「SEAL unresolved 中は G も unresolved」検査 (`:505-508`) が先に落とす。
- B を未知 selection で resolved にする変異は、enum 不在検査 (`:469-477`) が先に落とす。
- stage 5 gate ID を旧値へ戻す変異は semantic set 検査 (`:412-420`) が先に落ち、module hash pin の検出ではない。
- Q3 revocation、Q3 X_f、U-A1 の `resolved → unresolved` には個別陰性変異がない。state pin から1 IDを落としても、既存 validator はその regression を許す。

根拠: `s2-plan.md:212-247`、`calibration_freeze_authority_contract.py:412-428,469-508`、`docs/calibration-freeze-authority-bundle-design.md:677-688`

放置すると、どの node が対象欠陥を検出したか帰属できず、別 blocker が status `incomplete` を維持する仮面になる。mutation ledger は「殺した」だけで、対象検査の実効性を証明しない。

## LUNA-08 / must-fix

破れる具体構成: §10 の fixture 閉包を `1–4,6–8` から `1–4,5–8` へ変更する一方、manifest の gate ID と `_EXPECTED_REQUIRED_GATES` をそのまま維持する。逆に gate ID を `...5-8...` へ変えても、owner は単なる非空文字列で、段範囲を解釈するコードがない。

根拠: `docs/calibration-freeze-authority-bundle-design.md:631-639`、`s2-plan.md:115-138,165-181`、`calibration_freeze_authority_contract.py:401-409,747-755`

放置すると、docs の「段5除外」と gate 表の宣言が別々に変更できる。status は変わらず、段5 fixture の omission/inclusion が certified completion、報告の pending 数、台帳の受理集合へ反映されない。

## 総括

NO-GO。未裁定 revocation schema、自己再計算可能な gate pin、証拠のない gate status が blocker である。  
最大の破れは、profile・gate・fixture が literal として整って見えても、policy の実行と独立した期待値へ束縛されていないこと。  
段4では schema を land せず、三者 pin・docs binding・変異帰属・scope外 resolver を先に裁定すべきである。