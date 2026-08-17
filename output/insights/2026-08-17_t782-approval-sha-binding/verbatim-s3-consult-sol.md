```text
ID: A1
命題: (P1)
判定: refuted
根拠: output/s8b-freeze/holdout_freeze.json:622-623 は floor=null, budget=null。この値では orchestrator/campaign/s8b_oracle_driver.py:575-587 の非 v2 分岐に入り、ratified loader を呼ばず、manifest 指定時は同:485-500 で load_approved_spec を呼ぶ。さらにテストは orchestrator/tests/test_s8b_oracle_manifest.py:1102-1112 で ratified より先に直接 loader を呼ぶ。したがって M4 の全称と「観測可能な挙動 0 bit」は偽で、gate-check の refusal は no-approved-spec から次段の診断へ変わる。なお run-block と他 4 CLI の提示順序自体は正しい。
帰結: 現時点の certified 選択・材料レポート・台帳は依然 0 件だが、gate-check の診断値と将来の blocker 解消後の到達段は変わる。

ID: A2
命題: (P2)
判定: refuted
根拠: 「方針は新設だけ」という反証線自体は誤りで、docs/decisions.md:14532-14535 は新設と維持の双方を既定見送りとしている。しかし同:14536-14538 は正しさゲートを対象外とし、D356 の同:15585-15587 は内容束縛を健全と明記する。D302 の同:13995-14011 と orchestrator/campaign/s8b_oracle_manifest.py:1105-1129 は、approved spec から schedule、campaign、run contract、binding、除外理由を再導出して照合する。承認者同一性の欠落は、この内容束縛の無価値を意味しない。
帰結: generator_versions の live-byte 部分は縮小候補になりうるが、approved spec の存在と内容束縛を残せば、certified 選択と材料レポートが未承認の研究設計へ差し替わる経路を防げる。

ID: A3
命題: (P3)
判定: refuted
根拠: freeze_verification_hold.py:16-38 の 21 件、特に同:26-27 の 2 件は known-axes の実装・測定同一性検査である。D328 の docs/decisions.md:14784-14793 も held の対象を実装と測定の同一性に限定し、正しさゲートを除外する。一方 APPROVED_SPEC_SHA256 は s8b_oracle_spec.py:182-200 で承認済み bytes の存在を要求する。これを held として照合省略すれば、現行の受理集合空集合から、任意の schema-valid spec を s8b_oracle_manifest.py:1186-1225 が manifest 化できる集合へ広がる。ID を台帳へ足すだけなら挙動は変わらず、held 化の意味もない。
帰結: 同族扱いして bypass すると将来の certified 選択、材料レポート、台帳を未承認 spec で生成できるため、現状の不揃いは正しい。

ID: A4
命題: (P4)
判定: refuted
根拠: 実装ゼロ部分は brief.md:5-8,38-41 の scope と不変条件に適合するが、「trust root 不在が新しい状態変化」という中核は brief.md:15-17 自身と docs/archive/worklog-phase3-0813-546.md:10-15 に反する。外部 trust root を設けず自己発行可能性を明記して受容することは既決であり、blocker ではなく保証限界である。非 canonical 草案は contract test を発火させないが、既に preregistration-values.md:3,107-134 に存在する。生成 script は active artifact が無く、docs/dev-wave/core.md:60-63 の DW-G04 により設計メモ止まりであり、先行 producer 設計も package.md:198-208 に存在する。
帰結: コード差分ゼロは維持してよいが、成果物は「新しい blocker 状態」の再掲ではなく、内容 pin 維持と generator pin 縮小を分離した裁定へ直す必要がある。

ID: A5
命題: (M2)
判定: refuted
根拠: production producer 0 と canonical directory 不在は正しいが、「test fixture 3 関数のみ」は偽である。直接 writer は少なくとも s8b_oracle_spec_fixture.py:102-113,116-122、test_s8b_oracle_manifest.py:264-269,1102-1106,1148-1156 の 5 関数に存在する。
帰結: production 成果物は依然 0 件なので certified 選択等は変わらないが、writer inventory を根拠にした閉包主張は訂正が要る。

ID: A6
命題: (M3/M4)
判定: refuted
根拠: M3 は「5 production module」なら正しいが、「5 CLI 入口」ではない。driver だけで load_approved_spec の call site は orchestrator/campaign/s8b_oracle_driver.py:490,500,1258 の 3 箇所あり、gate-check と run-block は別経路である。manifest contract test の inventory は test_s8b_oracle_manifest_contract.py:18-36,87-104 で load_approved_spec の caller 集合や順序を固定していない。
帰結: 新規・部分 caller が approval を先に観測する余地があり、診断経路を「ratified に完全 mask される」と材料レポートへ記録できない。

ID: A7
命題: (M9)
判定: refuted
根拠: 5 source は s8b_oracle_manifest.py:53-61 の実値である。2026-08-01 以降の per-file 件数は 17/6/3/0/2 で合計 28 だが、同一 commit の重複を除くと 22 commit である。「28 commit」は touch 件数の二重計数である。直近 4 日に 4 source が変更された部分は成立する。
帰結: staleness の方向性は変わらないが、再発行費用の根拠値は 28 unique commits ではなく 22 と記録すべきである。

ID: A8
命題: (追加 blocker の見落とし)
判定: real
根拠: trust root は既決の限界であり blocker ではない一方、T987 package.md:103-125 は judge 集約式の未凍結と spec 層の単一 block 検査欠落、同:127-135 は contract_sha256 の世代失効を記録する。preregistration-values.md:124-139 では binding_identity が active ratified freeze なしに導出不能で、誤値は one-shot 実走後に拒否される。これらは M1-M10 に含まれていない。
帰結: active freeze ができても approved spec、材料レポート、台帳を安全に確定できないため、費用は approval pin の撤去より先にこれらへ向けるべきである。
```

## 総括

- P1〜P4 はいずれも、そのままでは採用できない。
- 特に driver の `gate-check` が M4 の全称反例であり、「観測可能な変化 0 bit」は成立しない。
- 外部 trust root 不在は既に受容済みの保証限界で、現在も残る blocker と数えるのは誤りである。
- D356 は内容束縛を健全と明記しており、承認者同一性との混同が P2 の主要な誤りである。
- approval pin を held 化して省略すると、未承認の研究設計を official 経路へ入れる受理集合拡大になる。
- したがって親の「実装ゼロ」だけなら正しさゲートは弱まらないが、P2/P3 に基づく将来の一括縮小は規律 2 上却下すべきである。
- 安全な中間物は非 canonical の草案文書だが既に存在し、生成 script は DW-G04 の発火条件を満たさない。
- pytest は実走しておらず、M7 の `4 passed` は独立確認していない。その他は静的検査と git 履歴照合による。