判定は **NO-GO** です。テストは実行しておらず、以下は read-only の静的読解と tracked artifact の照合結果です。

## 所見 1 — machine-only の帰属がなく、実在する非 trigger campaign の過剰拒否を見逃す — severity: blocker 候補

- 根拠: `s2-plan.md:5,107-113,117-139,165-176`、`orchestrator/campaign/wal.py:663-673`、`orchestrator/tests/test_artifact_admission.py:51-55,647-654`。machine 判定は axis・marker・proposal indicator・generator・space の連言だが、新規 corpus 6件は全条件が同値である。非 trigger 正例は `p2-2-…-f1588056` 1件だけである。
- 攻撃シナリオ: 呼び出しを `campaign_id.startswith("p3-")` に差し替える。新規6件は全て拒否され、overlay 3件は `artifact_admission.py:530-585` で先に return、post-policy は歴史枝外、既存正例は `p2-2-…` なので、予定テストは同じ結果になる。一方、snapshot と現 tree の lock/WAL が一致する実在非 trigger の `p3-s6-sort-sweep-balanced-sweep-dd25aa8c`（`campaign.lock:1`）まで拒否される。また `wal.py:668-672` の各 conjunctを単独で削除しても、現 corpus に near-miss がないため検出できない。
- 成果物影響: 受理集合は「6件だけ縮小」ではなくなり、歴史 sort campaign 等からの材料再生成・critic/replay が拒否される。既存 known-axes の source reference は拒否済み campaign を指すことになり、certified 選択の再構成と台帳参照が不整合になる。
- 提案: snapshot 内の全 admitted historical campaign を正例として parameterize する。加えて axis・marker・`reflux`・generator・space を一項目ずつ崩した synthetic truth table を設ける。厳密に6件だけが契約なら、6組の path/lock SHA/WAL SHA を production の閉じた manifest として固定するのが最小である。

変異事前登録の静的判定は次のとおりです。

| 変異 | 判定 |
|---|---|
| A1 `False` / status 差替え | 新規6件テストが検出する |
| A1 の判定条件広げ・狭め | **検出不能**。`axis` のみ、`p3-` prefix、各 conjunct 削除が反例 |
| A2 raise 除去 | `require_admitted_campaign` の例外期待が検出する |
| A3 Layer3 bypass | Layer3 rejection test が検出する |
| A4 post-policy も実際に downgrade | 既存 post-policy classification test が検出する。ただし「判定を枝外へ移す」だけでは semantic no-opにもなり、変異署名が具体的でない |
| A5 定数 `True` | `p2-2` 正例が検出する。ただし `p3-` だけを過剰拒否する部分的 broadening は検出不能 |

したがって名指しすべき欠陥は **A1 の帰属不足**と、**A4 の変異署名の曖昧さ**です。

## 所見 2 — TOCTOU 再照合は ABA を許し、snapshot の SHA と別内容の分類を組み合わせられる — severity: blocker 候補

- 根拠: `s2-plan.md:107-110` は再照合後に既存の `lock` を分類するとする。実装は最初に SHA を取る (`artifact_admission.py:527-529`)、その後 WAL と lock を読む (`587-590`)、最後に path を再 hash する (`602-605`)。分類に使う `lock` は再照合前に読んだ object のままである。予定テスト `test_exact_pre_policy_trigger_machine_sweep_is_not_admitted` は静止した repo artifact しか読まない。
- 攻撃シナリオ: 実 machine lock A を最初に hash させ、`lock_path.read_bytes()` の直前だけ非 machine lock Bへ交換し、`602` の再 hash 前に Aへ戻す。snapshot と再照合は A の SHA で通るが、predicate は Bを見て Falseとなり、Aに対して `historical-not-reclassified` / `admitted=True` を返す。WALも同様に交換すれば、decision の WAL SHA と `AdmittedCampaign.records` の内容を分離できる。Layer3 も WALを再読後に hash する同型構造を持つ (`layer3_report.py:392,422-429`)。
- 成果物影響: 実 machine sweep Aが再び admitted view を取得し、Layer3 の `admission_decision` は trusted A の SHAを掲げながら分類だけ B由来になる。raw consumer では別 WALの commit/certified 値まで trusted SHAに偽装でき、certified 選択、材料レポート、試行台帳の参照 digest が嘘になる。
- 提案: lock/WALを一度だけ bytes として読み、その同じ bytes を hash・parse・snapshot比較・consumer projection に使う。Layer3も admission view が保持する immutable lock/WAL projection を再利用する。A→B→A を決定論的に注入するテストを追加し、`602-605` 相当の防壁削除が必ず赤になるようにする。

## 所見 3 — 親 P3 の新 field は警告であって capability gate ではない — severity: blocker 候補

- 根拠: `s1-brief.md:55-58,72-80` は unbound でも受理集合を変えず field を掲載する設計である。現行の `admitted` は `admission_status != "legacy-unclassified"` という open-world allow (`artifact_admission.py:95-97`) で、`require_admitted_campaign` はその値だけで `AdmittedCampaign` を発行する (`707-721`)。例えば sweep consumer は decision を見ず、commit の存在だけで `certified=True` とする (`s8a_trigger_sweep.py:524-551`)。
- 攻撃シナリオ: `trigger_membership_evidence="machine-sweep-unbound"` の campaign を `admitted=True` のまま渡す。Layer3 が field を表示しても、sweep・critic・replayなど既存 raw-WAL consumer は `AdmittedCampaign` と commit を読み、fieldを無視して certified 材料を作れる。
- 成果物影響: certified 選択の候補集合には membership 無保証の variant が残る。材料レポートだけ警告付きでも、試行台帳と他 consumer の admission status は `admitted` のままであり、同一 campaign に相反する意味が併存する。
- 提案: field掲載ではなく capability を分離する。unbound trigger は `AdmittedCampaign` を発行せず、専用の非主張型にするか、`require_admitted_campaign(claim="trigger-membership")` のように claim scope を必須化して拒否する。`admitted` も既知値 `"admitted"` との完全一致にする。

## 所見 4 — 狭い方向 A は post-policy machine sweep の同じ嘘経路を残す — severity: must-fix

- 根拠: 親自身が `s1-brief.md:27-28,72-75` で露出を認め、プランも `s2-plan.md:57-61,176-180` で未解決とする。`validate_trigger_bindings` は proposal でなく exact machine shapeなら `{}` を返す (`wal.py:735-759`)。既存テストはこの無証拠受理を固定している (`test_artifact_admission.py:340-352`)。
- 攻撃シナリオ: exact generator/space を持つ post-policy machine lockで、source receiptには束縛されるが32集合には属さない predicate を materialize する。trigger binding record がなくても validation は通り、`admitted-new-schema/admitted` となる。
- 成果物影響: 将来の certified 選択と Layer3 v3に非正準 predicate の性能・verify結果が流れ、admission receiptと台帳はそれを `admitted` と記録する。
- 提案: machine producerについても mask→canonical predicate→materialized source の完全一致を admission 条件にする。T-474を歴史6件だけに限定するなら、この穴を別の blocking task として明示し、閉じるまで trigger machine 結果を certified 選択へ使わせない。

## 所見 5 — M2 が証明したのはレポート文字列の membership だけで、実際に build された source ではない — severity: blocker 候補

- 根拠: `s1-brief.md:19-22` と `s2-plan.md:40-46` は `entries[*].implementation` を比較している。歴史 snapshot gate が照合するのは lock/WALだけ (`artifact_admission.py:371-381`) で、machine provenance は検証対象外 (`425-430`)。provenance writer は candidate 名から現在の implementation を別ファイルへ書くだけである (`s8a_trigger_sweep.py:492-518`)。代表例でも provenance は canonical文字列を持つ一方 (`…c2d838b8/reports/s8a_trigger_sweep_provenance.json:22-27`)、WAL build_start は `genome` と `src_token` しか持たない (`…c2d838b8/runs/wal.jsonl:4`)。
- 攻撃シナリオ: build時には非正準 sourceを使い、provenance の `implementation` だけ正準文字列にする。あるいは report生成・merge後に正準値へ差し替える。freeze がその report hashを pinしても、pinされるのは嘘の reportであり、実 sourceとの等式は生まれない。`src_token` は source digestではあるが、M2には「この implementation を materialize した source digestが WALの tokenと一致する」という witness がない。
- 成果物影響: WALの `certified=true`、TPS、variant IDが別 predicate の結果なのに、材料 source reference は正準 predicate を指す。certified 選択、known-axes材料、試行台帳の variant→実装対応が誤帰属する。
- 提案: M2を「付随レポートの34文字列は正準」と狭める。実 sourceまで主張するには、pin＋implementationから materialized bytesを再構成し、WAL source digest・build receipt・binary commitmentまで照合する。歴史 evidenceが足りなければ membership は `unproven` と扱う。

## 所見 6 — 「ユーザー選択の記録がない」は一次控えと canonical worklog の双方に反する — severity: must-fix

- 根拠: `s2-plan.md:9-13` は記録なしを land blocker とする。しかし一次控えは `[T-409] = 択一 A=(a) 破棄 + C 縮小版` と明記する (`2026-08-04-rulings-session-5rulings.md:101-106`)。さらに canonical worklogにも裁定、T-474起票、縮小版採用が記録済みである (`docs/worklog.md:1036-1044,1247-1253,1342-1344`)。
- 攻撃シナリオ: 存在する裁定を欠落扱いして実装を停止する、または不要な再裁定・supersession記録を作り、権威参照を二重化する。
- 成果物影響: 停止すれば歴史6件の `decision.admitted=True` と新規材料発行が残る。二重記録なら材料レポートや台帳が参照する裁定 authority が分岐する。
- 提案: `s2-plan.md:11-13` を一次控え §11 と `docs/worklog.md` の既存裁定参照へ置き換える。必要なのはユーザー再裁定ではなく、D160との限定的な関係を実装記録に正確に説明することだけである。

## 所見 7 — P1〜P4 はいずれも少なくとも結論部分が実測ではない — severity: must-fix

- 根拠: `s1-brief.md:47-61`。

  - **P1**: validationを通らず admitted viewが出る事実は実測・静的裏取り済みだが、「読み手が混同する」「将来非正準が流れる」という実害は witness未提示の推測。
  - **P2**: 方向 Aによる新規 Layer3拒否は静的予測で、実装後の実測ではない。「既存材料を落とす」は、既存v2 bytesを保持するという `s2-plan.md:141-151` と射程が曖昧。
  - **P3**: fieldとconsumer義務は未実装の設計仮説。受理集合を変えず嘘を防げるという検証はない。
  - **P4**: ledger records=3 と authority pinは観測事実だが、「費用に見合わない」は費用見積りのない判断。F1の帰属欠陥を考えると、exact 6 manifestがむしろ最小修正になり得る。

- 攻撃シナリオ: これらを「実測済み事実」として扱うと、P3の警告fieldで防壁を代替したり、P4で唯一の exact-scope witnessを退けたりする。
- 成果物影響: 受理集合を変えないまま unbound結果が certified 材料へ残るか、逆に方向 Aの過剰拒否で無関係な歴史材料を失う。いずれも台帳の admission値と source reference の信頼性を損なう。
- 提案: 各Pを `observed / statically-derived / hypothesized / policy-judgment` に分解する。P1/P3には実 consumer witness、P2には受理集合差分、P4には exact-6 manifest案との具体的費用比較を付ける。

## 無しと判定した点

- overlay-denied 3件の巻き添え: 提案どおり gate を歴史 snapshot branch内に置く限り、`test_three_legacy_campaigns_are_denied` が classification・status・overlay参照・view拒否まで検査しており、独立所見は無し。
- 全入力に対して同じ値を返す新設 field: 方向 Aは fieldを新設せず、方向 Bは四値案なので、文字どおりの全入力恒真 field は無し。ただし対象6件に限定すると machine predicate は corpus-relativeな恒真になっており、所見1の帰属欠陥がある。
- A2・A3・A5の登録どおりの変異が生き残る証拠: 無し。問題はA1の未登録 broadeningとA4の曖昧な署名である。
- 実 artifact: 歴史 machine branchには balanced/read-heavy/write-heavy各2件の計6件が実在する。overlay trigger 1件と歴史非 trigger正例も実在する。一方、tracked repo内に post-policy `build_admission` campaignはなく、その非巻き添え保証は synthetic fixtureだけである。

## 総括

**NO-GO。**

最大の risk は TOCTOU/ABA により、trusted snapshotの lock/WAL SHAと、別bytesから得た分類・raw viewを一つの admission decisionへ合成できることです。これを塞ぎ、machine-only の帰属を near-miss正例/反例または exact 6 manifestで固定するまでは、「6件だけを安全に拒否する」という保証は成立しません。