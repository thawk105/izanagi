## 所見

[severity: must-fix] [E1-stale migration の記述が現行仕様と逆] plan は closure 内 `.py` の commit により既存 campaign が `E1-stale` になるとしているが、後発裁定 D1163 は「記録 closure と現行 committed closure の不一致」を certified 拒否条件から撤去している。実装も current closure が取得可能かだけを確認し、記録 map とは比較しない。commit 済み差分を受理する専用テストも存在する。tracked `campaign.lock` は32件（通常30、insight 2）で、`contract_loader_blob_sha256s` を持つものは0件なので、本 wave により新規 `E1-stale` になる repo 内 campaign は0件である。成果物影響: 放置すると、実際には失効しない測定を失効したと worklog に記録し、certified 選択と proof-chain provenance を事実と異なる形で説明する。[根拠 docs/decisions.md:38831; orchestrator/campaign/artifact_admission.py:953; orchestrator/tests/test_artifact_admission.py:1473; s2/plan.md:185] [提案: worklog は「D967 時点の想定は後発 D1163 により非発生、tracked 32件中 newly stale 0件」と記録し、E1-stale migration 完了とは書かない]

[severity: should-fix] [P2 は drift の exact 検査になっていない] 提案された `all(field_path in ...)` は期待13件の包含しか検査せず、契約側に14件目の未実装 field を追加しても通る。引用した C06 の `field_paths` idiom は実際には `frozenset(...) == expected` の exact equality であり、plan が借りている `all(...)` は `reachable_from` の片方向検査である。新規テストも削除変異しかなく、余分な field の生存を検出しない。成果物影響: 将来、契約だけが要求する field を正式 evaluator が検査せず、契約上の proof chain と実際の受理判定が乖離し得る。[根拠 s2/plan.md:42; s2/plan.md:45; s2/plan.md:165; orchestrator/campaign/s8c_preregistration_evidence.py:3279; orchestrator/campaign/s8c_preregistration_evidence.py:3513] [提案: literal↔contract path の単一13組 mapping から両集合を導出し、`frozenset(requirement.field_paths) == expected_paths` とする。テストへ `unexpected-extra-field-path` 変異も追加する]

[severity: should-fix] [影響テスト列挙が producer 側の既存束縛を落としている] 実 receipt の正本は既に13要素の `S8C_CROSS_BINDING_FIELDS` を持ち、生成後に bindings の exact set を照合している。既存テストには全 field 正例、no-build の全 field 列挙、13 field parameterized mutation、特に `proposal_build_source_bindings` 専用分岐があるが、plan の「完全列挙」にはない。成果物影響: C10 の token fixture だけを確認すると、実 receipt の新 field が欠落・非検証でも formal proof-chain の producer 回帰を見落とし得る。[根拠 orchestrator/campaign/autonomous_trial_completeness.py:215; orchestrator/campaign/autonomous_trial_completeness.py:4566; orchestrator/tests/test_autonomous_trial_completeness.py:4044; orchestrator/tests/test_autonomous_trial_completeness.py:4320; orchestrator/tests/test_autonomous_trial_completeness.py:4332; s2/plan.md:125] [提案: この3 node群、特に parameter `proposal_build_source_bindings` を影響テストへ明記する]

[severity: should-fix] [受入全走は commit 後と明記する必要がある] core/evaluator が dirty な間、`capture_contract_loader_binding()` は HEAD blob 不一致で失敗する。静的 call-graph 上、`test_p3_b4_raw_record_producer.py` だけでも `_writer_authority()` に到達する28 test nodeがあり、さらに HEAD と worktree 候補を比較する repository snapshot も途中状態では一致しない。commit 後は D1163 により既存 recorded closure との差は拒否されない。成果物影響: 順序を誤ると受入全走が機構どおり赤になり、acceptance proof を得られないが、既存 certified 集合の恒久失効ではない。[根拠 orchestrator/campaign/contract_loader_binding.py:348; orchestrator/tests/test_p3_b4_raw_record_producer.py:100; orchestrator/tests/test_p3_b4_raw_record_producer.py:940; orchestrator/tests/test_s8c_preregistration_predicates.py:153; s2/plan.md:88] [提案: `prepare-revision`→全変更を1 commit→clean worktree で受入全走、という順序を明記する。commit 前は tmp-repo 型の限定 nodeだけを使う]

[severity: nit] [先例の変更 file 数は7] 2b19d26b2 は freeze を含め7 fileを変更している。今回と共通する6面は core・evaluator・契約・core test・predicate test・freeze で、先例だけの7番目が invariant test である。同先例では C06 を machine-checkable に追加したため function pin 集合の編集が必要だったが、今回は C10 の `reachable_from`・entrypoint・path universeを変えず、field_paths は同 invariant の走査対象外なので編集不要である。成果物影響: 数え違い自体は certified 選択・受理集合・proof chain を変えない。[根拠 verbatim-precedent-T1421.txt:35; orchestrator/tests/test_s8c_preregistration_invariant.py:233] [提案: 「先例7 file、うち共通6 file。invariant は実走のみ」と比較表へ明記する]

## 親 brief 自身の欠陥

[severity: must-fix] [「closure 内変更で既存 campaign が E1-stale」は古い一般化] brief の事実5は D967 当時の前提を現行挙動として残している。現在は dirty closure の取得不能だけが一時的 `E1-stale/current-closure-unavailable` になり、commit 後の map 差は受理される。成果物影響: 既存 campaign の certified 可用性を実際より狭く報告し、不要な migration を proof chain に記録する。[根拠 s1-brief.md:24; docs/decisions.md:38836; orchestrator/campaign/artifact_admission.py:963] [提案: 事実5を D1163 後の二分—dirty は一時拒否、committed mismatch は許可—へ訂正する]

[severity: should-fix] [DECIDER_VERSION の「exact 比較4箇所」が誤分類] literal assertion は core test の3箇所だけで、`test_s8c_gate_report.py:84` は任意の synthetic report 値を自己投影する fixtureで production 定数を参照しない。実際の4番目の拘束は invariant test の tip/record/report と `DECIDER_VERSION` の動的比較であり、g12 発行により追随する。成果物影響: 誤って gate-report fixture を編集しても production pin は強くならず、逆に g12/tip の動的拘束を見落とすと candidate proof chain が赤になる。[根拠 s1-brief.md:26; orchestrator/tests/test_s8c_gate_report.py:78; orchestrator/tests/test_s8c_preregistration_invariant.py:449] [提案: 「literal 3箇所＋動的 invariant 1件」と訂正し、gate-report fixture は歴史値のままにする]

## (P1)〜(P4) への評価

- (P1) 賛成。JSON 追加だけでは `_evaluate_c10` の検知集合は増えず、`_C10_FIELDS` の13要素化が必要。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:2222; orchestrator/campaign/s8c_preregistration_evidence.py:2240]

- (P2) 条件付き賛成。D967 の新 field を load-bearing にする局所検査は本題だが、「drift 検査」とするなら片方向 `all(...)` ではなく exact set equality と追加・削除双方の変異が条件。[根拠 orchestrator/campaign/s8c_preregistration_evidence.py:3513]

- (P3) 賛成。condition 10 hash は §6 の当該条件文だけから算出され、evidence contract は別 hash として `protected_sha256` に入る。規範文書を変えると、不要に condition 10・section 6・normative hashまで変わる。[根拠 docs/phase3-8c-preregistration.md:257; orchestrator/campaign/s8c_preregistration.py:998; orchestrator/campaign/s8c_preregistration.py:1029]

- (P4) 賛成。既存 `proposal.path` / `proposal.sha256` の namespace 規約と、実 key `proposal_build_source_bindings` の対応から `proposal.build_source_bindings` が整合する。[根拠 orchestrator/campaign/s8c_preregistration_evidence_contract.v1.json:405; orchestrator/campaign/autonomous_trial_completeness.py:4575]

## 同意する箇所

- closure は現物でも exact 24 path。契約 JSON は外、core/evaluator は内。
- 仮想変更から再計算した hash は plan の5値すべて一致した。
- g11 raw SHA-256 は plan 記載の `8fb7802e...8a307` と一致した。
- `prepare-revision` は g11 の検証結果から generation 12 と raw supersedes hashを取り、worktree の markdown・契約・実行中の v7定数から全 g12 fieldを機械生成する。手書き経路ではない。
- §5、§6の12個別 hash、normative body は不変で、変わるのは evidence contract hash と protected hash。
- g10/g11 の v6・旧 contract hashは歴史 recordなので編集しない。

## 総括

実装の中心方針と g12 発行経路は閉じている。通す前に必要なのは、E1-stale の事実認識と記録内容の訂正、commit 後に受入全走する順序の明示である。加えて P2 を exact drift 検査へ直し、既存の実 cross-binding producer テストを影響列挙へ加えるべきである。

pytest は実走していない。上記は静的走査と read-only の hash 再計算結果であり、「緑」とは判定していない。