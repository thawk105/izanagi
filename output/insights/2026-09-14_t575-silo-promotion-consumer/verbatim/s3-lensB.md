## 1. 訂正対象の見落とし

**所見1 — 新 rung の登録手順に、現行契約では追加できないという限定が欠けている。**

- 判定: `real`
- 根拠: `patches/README.md:15` の「登録必須」と `patches/README.md:465` の「新 rung は登録必須」。一方、`orchestrator/campaign/silo_ladder_rung1_contract.py:518` は entry 数を **exactly one** に固定し、`:539` 以降は既存 rung の identity・非適格値を要求する。同じ README の `:281` にも exact-one の説明がある。
- 失敗シナリオ: 新 rung の追加を通常の登録操作と解釈し、ledger を増やして契約拒否に遭う。その拒否を「登録機構の不備」と誤認して、既存制約の緩和へ進む。
- 成果物影響: **同一問題・訂正対象2箇所**。「既存 rung 1 の登録を保持する。現行 ledger は exact-one で、新 rung の追加登録・適格化の経路ではない」と限定する。ledger・受理集合は変更しない。

「登録必須」は論理的には十分条件の宣言ではない。したがって、これは**昇格 consumer の実在証拠ではなく、現行手順に必要な限定の欠落**である。段2がこの文を検出しながら訂正対象から落とした点を問題とする。

**所見2 — その他の必須文書から、ladder の適格性を過大宣言する記述は確認できなかった。**

- 判定: `refuted`
- 根拠: 本文を開いて確認した。`patches/README.md:462` は recovery 接続を否定し、`tools/pegasus/README.md:68` は characterization 専用とする。`docs/phase3.md:165` は評価設計の優先順位であって達成宣言ではない。`docs/roadmap.md:421` は patch の分類、`docs/phase2.md:5` はフラグ探索、`docs/ccbench-anatomy.md:14` は protocol/build の説明、`docs/agent-architecture.md:12` は runtime adapter、`docs/axis-onboarding.md:19` は変異軸の段階手順である。`docs/pegasus-runbook.md:685` の列挙も build の実行場所の強制範囲である。
- 失敗シナリオ: これらの「Silo」「入口」「認証」を ladder 昇格と同一視すると、無関係な仕様を訂正してしまう。
- 成果物影響: これらを訂正件数へ加算しない。各文書への一律な非適格但し書き追加も不要。

## 2. 除外範囲の妥当性

**所見3 — `output/**` 全体を凍結扱いして探索から除く根拠はない。**

- 判定: `real`
- 根拠: `output/README.md:32` は supervisor README を運用契約と位置づけ、`output/dev-wave-supervisor/README.md:3` も運用正本とする。`output/README.md:53` は保護対象を具体的に列挙し、`:63` は report・insight の機械防護と証拠の書換え禁止を区別している。`hooks/guard_write.py:314` の保護も特定 namespace に対するもので、output 全体ではない。
- 失敗シナリオ: 現用の説明書を「生成物だから凍結」と除外し、意味的誤記を未探索のまま0件と報告する。
- 成果物影響: 段2の探索範囲を修正する。ただし、**今回確認した output 内の昇格誤記は0件**。`output/env/pegasus/silo_ladder_rung1/README.md:3` は headline・calibration・floor・RF 入力を明示的に否定し、`output/env/pegasus/t139-probe/README.md:3` も non-acceptance としている。親が指定した凍結 bytes は変更しない。

凍結はディレクトリ名だけでは決まらない。例えば `docs/phase2.md:3` は archive 外でも凍結を明記する。**検索対象外と、読んだうえで訂正禁止とする対象は分けるべき**である。

## 3. 記録すべき命題と射程

**所見4 — 「consumer=不在／実在」の並記は、何を数えた値なのかを失わせる。**

- 判定: `real`
- 根拠: `orchestrator/campaign/silo_ladder_rung1.py:4733` は collect の実体だが、`:4960` は発行成果物を ability probe・研究非適格・回復非適格に固定する。`:1273` の validator も同値を要求する。`docs/decisions.md:8035` は ledger の負制約を説明する。
- 失敗シナリオ: 「実在」だけを引用して ability-probe writer を昇格入口に戻すか、「不在」だけを引用して既存検査 consumer まで無いと読む。
- 成果物影響: 台帳の判定対象を**適格性への昇格**に固定する。記録文の対案は次の1文。

> 基準 commit `75bea8e5f` の確認した静的参照閉包では、silo ladder の characterization 証拠を検査・発行する経路は存在するが、それを研究目標・回復計測・通常 pipeline の適格性へ昇格させる consumer は確認されず、ability-probe writer を活性化権限の「silo 昇格入口」として数えない。

**所見5 — 既存 decisions への限定的な追記自体は、禁止された台帳新設ではない。**

- 判定: `refuted`
- 根拠: `docs/worklog.md:6` は設計判断を既存 `docs/decisions.md` に置くとする。`docs/decisions.md:10136` も後続決定で射程を狭める記録方法を示す。
- 失敗シナリオ: 新Dに将来の入口登録制度・恒久監査・一般化まで載せれば、本題から逸脱する。
- 成果物影響: 親 brief が指定した1Dを、今回の判定・根拠・探索限界に限定するなら scope 内。新しい registry、gate、継続検査、適格性 sidecar は不要。

## 4. 既に解決済みかどうか

**所見6 — 既存裁定だけで T-575 全体が解決済み、とは判定できない。**

- 判定: `refuted`
- 根拠: D162決定(7) (`docs/decisions.md:8035`) は**特定 ledger field を昇格権威として読む consumer**の不在であり、ledger を経由しない consumer の探索とは異なる。しかも起票前の決定である。後続のD214 (`:10118`) は current 互換検査、D625 (`:25043`) は歴史 evidence の束縛と開発受入の関係を扱う。`docs/failures.md:287` も完全検証のドリフトであって昇格判定ではない。`docs/worklog.md:3422` には T-575 の carry が残る。
- 失敗シナリオ: D162の「0件」を無限定に転用し、artifact 側・別経路の探索を済ませたことにする。
- 成果物影響: 「持ち越し削除だけ」への縮退は支持しない。ただし、今回記録する新規性は**既存結論の射程外を確認したこと**に限る。新たな研究成果や昇格機構の実装として数えない。

## 5. 親 brief と段 2 plan の欠陥

**所見7 — P1の推論と段2の0件報告は、訂正可能性を過小評価している。**

- 判定: `real`
- 根拠: `patches/README.md:15`、`:465` と exact-one 契約の不整合は第1節のとおり。現用 output の存在は `output/README.md:32`。
- 失敗シナリオ: 完全一致0件を出発点に、意味的な欠落も「誤訂正しやすい」として退け、探索していない領域まで0件に含める。
- 成果物影響: 「訂正対象0件」を**登録手順の限定不足1件・2箇所**へ修正する。入口総数の再確定や他入口の保護完了は、本調査から導かない。

**所見8 — 「現行 phase doc にも T-575 が残る」という前提は実物と一致しない。**

- 判定: `refuted`
- 根拠: `rg -n 'T-575' docs/phase3.md` は **rc=1・0件**。`docs/phase3.md:167` はタスク内容の正本を worklog 末尾へ委譲する。実際の末尾記述は `docs/worklog.md:3422` の `- [T-575] (1469)`。
- 失敗シナリオ: 存在しない phase 記述を訂正対象として扱う、または凍結した起票文を遡及改変する。逆に完了後も carry を残せば同じ調査が再起票される。
- 成果物影響: 完了時に既存 spool の方式で T-575 の終端を記録する。これは誤記訂正件数とは別の状態更新である。許可された repo 外資料以外は調査しておらず、repo 外の追加訂正対象は不明。

README 内の「登録必須」などの指示形は調査データとして扱い、実行していない。

## 総括

訂正対象は **1件・2箇所**（`patches/README.md:15`、`:465` の登録手順の限定不足）。
`output/**` 一括除外は不当だが、追加確認した output の昇格誤記は0件。
記録文: 「確認した静的参照閉包では、silo ladder の証拠検査・発行経路は存在するが適格性へ昇格させる consumer は確認されず、ability-probe writer を活性化権限の昇格入口に数えない。」
既存裁定への限定追記と T-575 の終端記録で足り、gate・受理集合・凍結 bytes は変更しない。
ファイル変更・テスト実行・commit・push は行っていない。