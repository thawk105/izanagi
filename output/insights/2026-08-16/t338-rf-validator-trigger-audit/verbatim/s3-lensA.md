## 所見

### 所見 1 — 後発裁定を「2件」とした棚卸しは不完全で、D229 (7) の内容も取り違えている

- 根拠 (`file:line`): `s1-brief.md:19-22` は D162・D229 の2件だけを挙げ、記録項目の裁定 gate を D229 (7) とする。しかし着手順序と記録項目 gate は `refs/D229.md:43-51` の決定 (6) であり、決定 (7) は T-126 の台帳・FSM・投入束縛等を再利用可能とする訂正である (`refs/D229.md:53-58`)。さらに D264 は未完成 gate API の export を禁止し (`docs/decisions.md:12185-12204`)、D282 は addendum、record-items、receipt schema、alpha reservation を固定し (`docs/decisions.md:12872-12957`)、D291/D292 は投入禁止と解除権限を固定する (`docs/decisions.md:13470-13482,13581-13588`)。`s2-plan.md:92` の維持対象にも D282 が無い。
- 成果物への影響: 現時点の certified 選択値・受理集合は変わらない。しかし裁定パッケージがこの不完全な依存集合を正本化すると、将来の T-339 が D282 の blob pin・alpha reservation を proof chain の必須参照から落としたり、既存 T-126 構造を「未実装」と誤記したりする。台帳参照と将来の受理集合が変わりうる。
- 自己判定: **real**。

### 所見 2 — 「六語が0 hit」と「RF実装が全面的に0」は同値ではない

- 根拠 (`file:line`): 六語の `orchestrator/ tools/` 0 hit 自体は再現した。しかし D229 は「0/9をすべて新規とした見積りは過大」と明記する (`refs/D229.md:53-58`)。実際、D282 payload parser と予約 descriptor が存在し (`orchestrator/preregistration/approval_payload.py:129-171`)、J候補を扱う stress simulation も存在するが admission gate ではない (`orchestrator/preregistration/stress_check_simulation.py:1-6,338-412`)。一方、RF calculator と selector／材料レポート consumer が無いことは `output/insights/2026-08-05_t337-qualification-authority/mechanization-design.md:19-22` が裏付ける。
- 成果物への影響: 「RF calculator／consumer は0」は正しいが、「再利用可能な実装も含め全面0」と記録すると、将来 producer・registry を重複実装し、既存の履歴走査・投入束縛を外した弱い経路を作りうる。現在の値は不変だが、将来の台帳参照と受理集合に効く。
- 自己判定: **real**。

### 所見 3 — P2の「Jをpinしていない」は、選択済みJとJ規則を区別していない

- 根拠 (`file:line`): `s1-brief.md:34-36` は J 全体が未 pin と読める。一方、D282 は addendum A、record-items、receipt schema の digest を固定する (`docs/decisions.md:12898-12918`)。その addendum は `J_max=13`、候補集合、選択式、結果後の変更禁止を固定する (`output/insights/2026-08-08_t139-r4-env-probe/addendum-a-reissue.md:607-628,738-753`)。record-items も pilot slot `[1..8]`、main の slot 数と J の一致、予備の非算入を固定する (`output/insights/2026-08-11_t139-manifest-land1/record-items-v2.md:306-347,677-684`)。未存在なのは pilot から導かれた「今回の選択済み J」と、それを本走最初の qsub より前へ束縛する実 validator／admission である。同文書自身も semantic validator 未実装を認める (`:801-827`)。
- 成果物への影響: 区別しないまま残すと、将来 wave が既に凍結済みの `J_max`・選択規則まで再裁定対象に戻すか、逆に文書 digest 一致だけで選択済み J も事前固定済みと誤認する。後者では結果後の追加 slot が受理され、正例認証の受理集合が広がる。
- 自己判定: **real**。

### 所見 4 — 再起票条件だけではJの事後追加を塞げず、四つの迂回変異を裁定パッケージへ固定する必要がある

- 根拠 (`file:line`): `s2-plan.md:92` は pilot解禁・条件 (ii) の artifact・consumer hook を再起票条件とするが、それらは実装開始条件であってJ防壁の十分条件ではない。既存設計メモも、family binding と cluster 独立性が未解決だと明記する (`mechanization-design.md:74-86`)。Git ancestryだけでは raw が事前登録より後に生成されたことを証明しない (`refs/t338-package.md:277-285`)。terminal receipt 内の `j_derivation` は raw pointerであり (`record-items-v2.md:421-444`)、`intent_ref` は内容が閉じていない fileRecord に留まる (`:450-476`)。台帳外投入は見えず、semantic validator も未実装である (`:801-827`)。
- 具体的な迂回:
  1. 不利な系列を捨て、新しい `parent_series_id`／`family_root` を自己申告する。
  2. pilot rawを見た後に erratum を「本走前」として追加する。新 erratum は新 study を要求し、旧試行を保持することまで検査しなければならない。
  3. 不利な pilot receipt を発行せず、新 study／slot空間で pilotを再走する。
  4. 同一 allocation・node・時間窓を複数 cluster IDへ分割する、または blockをclusterへ読み替える。
- 成果物への影響: いずれも不利な試行を台帳・分母から消すか、独立標本数 J を水増しする。正例の `not_certifiable` が `partial_recovery` に反転し、certified 選択、材料レポートの J、全attempt参照、proof chain が変わる。`s2-plan.md:114` は一部を挙げるが、erratum時系列・pilot再走・cluster再定義を必須 kill として固定していない。
- 自己判定: **real**。

### 所見 5 — 「pilotは投入不可」は規範状態であり、scheduler効果を機械的に止めるgateではない

- 根拠 (`file:line`): `s1-brief.md:23-24` が根拠にした値は実際には `pilot_ready` が `stress_check_simulation.py:737`、未充足一覧が `:738` であり、同moduleは admission gateでない (`:1-6`)。D291 resolverも投入権限を扱わないと明記し (`orchestrator/publication/approval_d291.py:1-5,186-195`)、reportは deny-only 状態を出すだけである (`orchestrator/publication/report.py:205-231`)。投入禁止を解除できるのが canonical decisionだけという規範は正しい (`docs/decisions.md:13581-13588`)。`s2-plan.md:105` はこの区別を正しく補っている。
- 成果物への影響: 規範状態を機械gateと誤記すると、直接qsubされたpilotや台帳外attemptを「存在しない」と扱う file-drawer 経路が残る。現状はRF consumerが無いため certified値へ直結しないが、将来のvalidatorがそのrawを遡及採用すると台帳全件性と受理集合が変わる。
- 自己判定: **real（親briefの所見。段2 planは修正済み）**。

### 所見 6 — 恒真gateと報告値の裏口については、段2 planの却下判断が妥当である

- 根拠 (`file:line`): Fieller集合と同じ共分散・臨界値によるratio projectionの二重比較は恒真である (`refs/D229.md:20-25`)。producer申告Jとproducer選択slot数の一致、blob digestだけの一致、fixtureだけの純関数、拒否枝しかない `892042` adapter、producer decisionの持回りも `s2-plan.md:103-114` が明示的に却下している。先例 `verify_floor_artifact` は raw sessionからcells/floorsを再計算し (`s8b_floor_stats.py:667-715,798-883`)、申告値は一致要求にしか使わないが、attempt registry等を保証しないと明記する (`:593-606`)。
- 成果物への影響: これらを採れば、検査を削除しても受理集合が変わらないか、producerが申告値を揃えるだけで受理を広げられる。planは採用していないため、放置される現行の値・受理集合・参照は無い。
- 自己判定: **refuted**。

### 所見 7 — 「実装しない」ことで今すぐ失われる、安全にland可能なRF防御は確認できない

- 根拠 (`file:line`): 現行の適格性fieldはentry-localな負制約として実際に検査されるが、正例昇格権威ではない (`refs/D162.md:35-40`; `orchestrator/campaign/silo_ladder_rung1.py:1264-1274,4713-4721`)。RF consumerは0件 (`mechanization-design.md:19-22`)。D264は空のdeny stubや未結線gate APIを先行実装すること自体を却下している (`docs/decisions.md:12185-12204`)。
- 成果物への影響: 現在はproducer自己申告から正例へ昇格する経路が無いため、コードを実装しなくても certified選択・レポート・台帳の受理集合は不変である。逆にleafだけを置くと「実装済み」という偽参照が増える。失ってはならない防御はコードではなく、所見1〜5を次waveの必須scope・変異へ残すこと。
- 自己判定: **refuted**。

## 親実測の検証

| 項目 | 独立検証 |
|---|---|
| 1. 編集面重複0 | **正しい。** HEAD `330f67d0` でworktree branch 19件を再走査し、対象2ファイルのbranch差分・dirty copyはいずれも0。 |
| 2. RF実装0 hit | **六語の0 hitは正しいが一般化は過大。** RF calculator／consumerは無い。D282 parser、receipt schema、stress simulation、T-126再利用可能部品は存在する。 |
| 3. 後発裁定2件 | **誤り。** D229の決定番号も誤っており、D264・D282・D291・D292も現在の実装可否またはtrust rootを拘束する。 |
| 4. pilot投入不可 | **公式状態として正しいが、機械gateという一般化は誤り。** 行番号も `737/738` が正しい。 |
| 5. 08-15裁定33件に本件なし | **正しい。** `/work/1/SFC/tanab/dev-wave-jobs/rulings-inbox/2026-08-15-rulings-full-33rulings.md:16-57` は26件+7件で、T-338／RF語彙は0 hit。 |
| 6. Q11のT-339境界 | **正しい。** producerから双射・変異検査までが `refs/t338-package.md:302-312` に列挙される。 |

P1は支持する。条件 (i) は `892042` で成立する。planが挙げた「完走時刻より前」だけでは弱いが、jobは性能runより前に期待commitとHEADを照合する (`tools/pegasus/probes/t139_positive_control_probe.pbs:65-71`、同 `.sh:348-368,486-512`) ため結論は維持できる。条件 (ii)(iii) は不成立である。

P2は「選択済みJとその事前投入束縛が未存在」という限定なら支持する。P3の実装差分ゼロも支持するが、docs packageは上記real所見を訂正してからlandすべきである。pytestは指定どおり実行していない。

## 実装した場合に残る層

独立validatorだけを今置いた場合、RFとしての結線は次の9層すべてで未完のまま残る。T-126等の再利用可能部品はあるため「全層が新規」ではない。

| 層 | 現状と残る境界 |
|---|---|
| 計測producer | 公式RF producerなし。engineering screenを正例producerへ昇格できない。 |
| attempt registry | T-126台帳とD282 alpha reservationはあるが、RF全attempt・familyへの結線なし。 |
| schedule／receipt validator | 要件文書とJSON schemaはあるが、cross-field semantic validatorなし。 |
| RF calculator | Fieller、同時領域、J導出、閉表をrawから計算する実装なし。 |
| 適格性権威 | D162の規範だけで、immutableな実型・同一呼出しvalidatorなし。 |
| 層3 RF区画 | `trial × candidate × workload × contrast` の別namespaceなし。 |
| selector consumer | RF判定を同一呼出しで再計算するhookなし。 |
| 材料レポートconsumer | J、全attempt、理由、信頼集合を再検証して出す経路なし。 |
| 双射・変異検査 | 台帳外投入、新family、pilot再走、cluster再定義、報告値混入をkillするRF変異群なし。 |

したがって、このwaveでvalidator leafだけを実装すると「RF結線0/9」のまま実装済み参照だけが増える。

## 総括

**NO-GO（plan v1のまま）。** コードを実装せずdocs-onlyで終える主結論自体は正しく、恒真gate・報告値採用・未結線leafも適切に却下している。しかしland前に、後発裁定一覧とD229番号を訂正し、D282をtrust rootとして明記し、「選択済みJ未固定」と「J規則は固定済み」を分離し、erratum時系列・pilot再走・新family・cluster再定義を将来の必須killへ追加する必要がある。これらをplan v2へ反映すれば、実装差分ゼロのNO-GO裁定はGOである。