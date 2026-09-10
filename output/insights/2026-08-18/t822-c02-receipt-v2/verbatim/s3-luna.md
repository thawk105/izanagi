必読資料4点を読了。read-onlyの静的検査のみで、pytestは未実走。

### 所見 1

**主張** C09/C10の実名整備が契約JSONだけで、実 evaluator と token-only fixture に旧名 `accept_trial` が残る。

**根拠** `orchestrator/campaign/s8c_preregistration_evidence.py:1488-1495,1531-1534`、`orchestrator/tests/test_s8c_preregistration_predicates.py:439-464`。S2 planは契約変更を `:20-27` に記すが、これらの evaluator / fixture 更新を列挙していない。親実測も旧名不在を確認している (`parent-measurements.md:24-28`)。

**成果物影響** 現在は同じ拒否理由に隠れるが、layer3/verifierが揃った後も実在する acceptance を見ず、C09/C10の判定、台帳参照、将来の受理集合を誤って拒否する。

**GO / NO-GO** NO-GO

### 所見 2

**主張** 非機械条件C03/C07/C08に残す `accept_trial` は、将来名の保存ではなく実在機構への誤参照を含むため、scope外なら裁定パッケージ化が必要である。

**根拠** 契約のC03は `orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:88-123`、C07は `:259-267`、C08は `:295-331`。実在名は `trial_registry.py:514,2556`。S2 plan自身が残置を明記している (`s2-plan.md:240-244`)。

**成果物影響** 凍結契約が不存在の関数を指し続け、将来のC03/C08/C07判定と台帳の証拠参照が旧経路へ倒れる。

**GO / NO-GO** NO-GO

### 所見 3

**主張** C02の宣言済みnegative controlと、S2 planが追加する変異が別物である。

**根拠** 契約のIDは `nc_c02_proposal_path_arm_collision` (`...evidence_contract.v1.json:65-72`)だが、計画の変異は `assert_execution_digest_chain` 等のedge削除 (`s2-plan.md:76-83`)。現行negative control mapにもC02はない (`test_s8c_preregistration_predicates.py:663-670`)し、機械条件とIDの完全一致を要求する (`:1838-1846`)。

**成果物影響** テストが先に失敗するか、IDだけ流用するとC02を実際に攻撃しない負例で理由落としを許し、評価器・契約・台帳のnegative controlが恒真になる。

**GO / NO-GO** NO-GO

### 所見 4

**主張** C02の計画はcall edgeとliteralを検査するが、契約の`field_paths`と7 sinkの完全一致を検査しない。

**根拠** 計画のC02 evaluatorは5関数の直接callと数個のliteralだけを要求する (`s2-plan.md:33-45`)。AST meta testもentrypointとfirst hop中心である (`:61-69`)。一方、C02契約のfield集合は `...evidence_contract.v1.json:47-61`、U3文書は7 sinkを要求する (`s2-plan.md:197-201`)。

**成果物影響** field名やsinkを1つ stale にしてもC02は非充足理由を返し続け、凍結契約だけが実装と異なるまま残る。

**GO / NO-GO** NO-GO

### 所見 5

**主張** P3の「g6を1回発行」は手続きとして可能だが、U2のsource bytesを凍結するという意味では成立しない。

**根拠** `s8c_preregistration.py:191-199` のprotected preimageはevidence contract hash、normative body、section5 field names、section6 hashだけで、`s8c_acceptance_receipt.py`と`trial_registry.py`のsource bytesを含まない。S2 planもこの反証を認めている (`s2-plan.md:238`)。

**成果物影響** g6の`protected_sha256`と台帳参照が同じでも、receipt schema、理由集合、producer実装が変わり、レポートと台帳の根拠が凍結記録から乖離する。

**GO / NO-GO** NO-GO

### 所見 6

**主張** T1336/T1337/T1347と同時に走る限り、T822が指定するg6を安全に発行できない。

**根拠** 並行waveは同じ `docs/phase3-8c-preregistration.md` と `condition-freeze.v1.g6.json` を成果物にする (`t1336.../s1-brief.md:68-74`, `t1336.../s2-plan.md:145-151,187-200`)。T1336はdecider v2、T822はv3を要求する (`t1336.../s2-plan.md:179-185`, `t822.../s2-plan.md:197-214`)。

**成果物影響** 先に一方がlandすると他方のg6生成が失敗し、またはg7へ再設計が必要になり、docs、condition hash、decider version、freeze chainのどれかが stale になる。

**GO / NO-GO** NO-GO

### 所見 7

**主張** T1333はT822と同じテスト・射影ファイルを変更し、producerが作るreport bytesの意味も変える。

**根拠** 重複は `test_s8c_preregistration_predicates.py` (`t1333.../s2-plan.md:511-514` と `t822.../s2-plan.md:73-89`)、`test_layer3_report.py`、`test_reflux_originless_compatibility.py`、`test_trial_registry.py` (`t1333.../s2-plan.md:516-534`, `t822.../s2-plan.md:164-191`)。さらにT1333はproducer/checkerのprofileを変更する (`t1333.../s2-plan.md:79-86`)。

**成果物影響** C01 snapshot、receipt期待値、compatibility projector、report/arm fieldsの一部だけがlandし、受理行・golden参照・レポートbytesが相互に stale になる。

**GO / NO-GO** NO-GO

### 所見 8

**主張** 規範文書はT-1311後のarm execution機構を反映しておらず、正式pilot未発効とは分けて書き直す必要がある。

**根拠** 現文書はdescriptor-onのみ、arm path衝突と記す (`docs/phase3-8c-preregistration.md:181-183`)うえ、衝突(d)をarm未束縛のままにしている (`:305-307`)。実装側にはbindingとacceptance検査がある (`trial_registry.py:1220-1255,2757-2830`)。S2 planは更新範囲を正しく列挙する (`s2-plan.md:197-203`)。

**成果物影響** 本文を直さなければ`normative_body_sha256`と`section6_condition_hashes[2]`が古いままg6へ入り、衝突(d)と実装の参照が台帳上食い違う。

**GO / NO-GO** NO-GO

### 所見 9

**主張** receipt v2の直接caller棚卸しは閉じており、v1互換射影の順序も正しい。

**根拠** mandatory理由の読者は receipt validator (`s8c_acceptance_receipt.py:225-232`)、producer (`trial_registry.py:2901-2905`)、receipt/layer3/trial tests (`test_s8c_acceptance_receipt.py:98-112`, `test_layer3_report.py:309-322`, `test_trial_registry.py:1006-1024`)、golden (`test_reflux_originless_compatibility.py:239`)。`AcceptanceReceipt`は `s8c_acceptance_receipt.py:305-358`、`VerifiedAcceptanceReceipt`は `layer3_report.py:569-589` と再検証側 `s8c_acceptance_receipt.py:638-652`、`AcceptanceSummary`は `trial_registry.py:2931-2951`。S2 planもlegacy fixture、producer期待値、projectorを列挙している (`s2-plan.md:164-191`)。

**成果物影響** v1 goldenは旧viewへ戻り、v2 producerはexecution-boundかつ`certifying=false`となり、certified選択は増えない。

**GO / NO-GO** GO

### 所見 10

**主張** U1/U2の明示編集file集合は素集合で、U3を両者の後に置く依存も正しい。

**根拠** U1の対象はpredicate/core/invariant等 (`s2-plan.md:71-95`)、U2はreceipt、registry、layer3 fixture、compatibility等 (`:164-191`)で直接交差しない。U3は最終bytes確定後に実行すると明記される (`:195-216`)。ただしU1は`trial_registry.py`を証拠として読み、U2が編集する意味依存はある。

**成果物影響** 指定順を守ればg6のcontract/docs参照とreceipt producerの最終形を同時に確定できる。

**GO / NO-GO** GO

### 所見 11

**主張** P5の実名変更は受理集合を広げないが、C02の判定理由・machine条件数・freeze参照は変える。

**根拠** 親実測はC09/C10の現理由が実名変更で変わらないとする (`parent-measurements.md:20-31`)。計画はmachine条件を6から7へし、SATISFIEDは空のままとする (`s2-plan.md:47-57,97`)。

**成果物影響** certified選択は空のままだが、C02 reason、machine count、normative body、condition hash、g6 recordが更新される。

**GO / NO-GO** GO

### 所見 12

**主張** P6は正式6 cellの証明ではなくfixture上の実producer分岐に限定するならDW-G04を満たす。

**根拠** DW-G04は既存artifact pathまたは計測IDをbriefに書ける場合だけ実装を許す (`docs/dev-wave/core.md:60-63`)。既存 `_bundle` は実際に`run_trial`と`assert_trial_registry_acceptance`を呼び、receiptを読む (`test_reflux_originless_compatibility.py:31-70,90`)。briefとplanもformal six cellを条件にしていない (`s1-brief.md:66-67`, `s2-plan.md:246`)。

**成果物影響** v2 receipt、producer、projectorのfixture検証だけが追加され、certified選択と正式受理集合は変わらない。

**GO / NO-GO** GO

## 総括

**NO-GO**

must-fix:

- C09/C10 evaluator、token-only fixture、C03/C07/C08 scopeの扱いを明示する。
- C02 negative control IDを実際の変異と一致させ、field pathsと全sinkの閉包検査を追加する。
- T1333/T1336との実行順を裁定し、g6/g7とdecider versionを一つに決める。
- §6本文、衝突(d)、`normative_body_sha256`、`section6_condition_hashes[2]`、protected hashを同じ最終bytesから再生成する。
- g6がU2 sourceまで凍結するという主張を撤回するか、source bindingを別裁定で追加する。

pytest等は未実走。