## 署名との一致

以下、`V` = `orchestrator/submission_gate/_semantic_validator.py`、`U` = `orchestrator/tests/test_t338_submission_gate_unit3.py`、`S` = `s4-ruling.md`、`R` = `rulings-verbatim.md`、`A` = `s5-author-1.md`。行番号は点検時の現物。

**所見**: 実装が裁定 §2 の署名と異なるという懸念は反証した。
**分類**: refuted
**根拠**: S:42 と V:2054 の判定は一致し、V:2060 は `if performance_slots and not verification_failure_recorded:`、V:2068 は `len(evidence) != 6 or evidence_pairs != expected_pairs`。追加条件はない。
**影響**: nit。署名との不一致による受理集合の差は認めない。
**推奨**: gate 本体の変更は不要。

**所見**: 性能割当てを参照する slot-null attempt による誤分類は先行検査で防がれるが、これは attempt schema 単独の保証ではない。
**分類**: refuted
**根拠**: `receipt-schema-v1.json`:1111 は attempt の null を許す一方、同:461 は性能 allocation に整数 slot を要求し、V:1455 の `if slot != allocation_slot:` が不一致を拒否する。
**影響**: nit。性能 allocation を指したまま slot だけ null にして gate を回避する入力は到達しない。
**推奨**: 説明では「schema と参照整合検査の組合せによる保証」と明記し、allocation_id が null の失敗記録まで role 検証済みとは表現しない。

## 失敗記録の保全

**所見**: 指定された二種類の失敗正例は新 gate に拒否されず、correctness anomaly と性能 completed の共存は既存分岐で拒否される。
**分類**: real
**根拠**: U:575 の `pre_performance_infra_failure` は V:2036 の検査後に V:2054 の例外となり、性能 completed がなければ V:1962 の集合が空のままになる；anomaly は V:2031 の `if anomaly:` で completed を拒否する。
**影響**: 正例2の0〜5件と正例3の0〜5件について、他の既存条件を満たす受領証の受理を維持する。
**推奨**: 条件は維持し、正例3の追加試験は単体入口であることを引き続き明記する。

## §8 との関係

**所見**: completed の申告だけを正の根拠にする変更ではなく、失敗例外も変更前の受理集合を拡大しない。
**分類**: real
**根拠**: V:2019 は marker・failure・actual を検査し、V:2029 は36-run対応を検査する；失敗側も V:2037 の `failure_evidence is None` 等で拒否され、V:2364 で証拠 pointer を読む；R:54 は失敗 stage の0〜5件を許す。
**影響**: 失敗と申告するだけでは通らず、既存失敗条件を満たす記録は従来どおり受理される。
**推奨**: 本 gate を単票受理条件として維持する。

**所見**: 「失敗記録は certified にならない」は契約上の帰結であり、この差分による認証結果の保証ではない。
**分類**: real
**根拠**: R:105 は開始前 infra failure を `design_not_feasible` とし、S:126 も「本 gate は保証しない」と明記する；V:2669 の study validator は単票検査後に stage・study・検証割当て同一性を検査する。
**影響**: 単票の受理を certified 採用と同一視すると、正例2を認証済みと誤解する。現物で認証結果の誤選択は確認していない。
**推奨**: D1272 の単票 gate 部分の実装完了と、下流の certified 不採用保証を区別して報告する。

## 単一理由性

**所見**: T2/T4 は静的追跡では新 gate だけが拒否理由となり、gate 削除時には受理へ反転する。
**分類**: real
**根拠**: U:768 は検証 attempt のみを除去し、U:787 は有効な先頭 entry を複製して ordinal を修復する；V:1433 は evidence の allocation 参照だけを要求し、V:1510 は ordinal、V:1123 と V:1810 は各 entry を検査するため、空配列や正常 entry の重複対を別理由で拒否しない。
**影響**: T2の0/1件とT4の6件・5対は `correctness` で新たに拒否される；M1の受理反転は静的結論であり、実測ではない。
**推奨**: 親のM1実走で反転を確認し、静的根拠と実測結果を分けて記録する。

**所見**: 点検項目にある phase budget は実際には新 gate の後続層だが、T2/T4 の変更で追加の拒否原因にはならない。
**分類**: real
**根拠**: V:2628 の `_validate_reason_branches` の次が V:2629 の `_validate_phase_budget`；後者は allocations・actual runs・attempts の時刻を検査し、correctness の対被覆を参照しない。V:2430 の slots/counts も今回変更した evidence 被覆を検査しない。
**影響**: nit。gate 削除後の受理反転を妨げる後続拒否は静的に認めない。
**推奨**: 単一理由性の説明では phase budget を後続検査として記載する。

## 二重発火

**所見**: 検証 completed の不足入力が attempts の順序によって新 gate に先着する懸念は反証した。
**分類**: refuted
**根拠**: V:2011 は件数不足を `reason`、V:2016 は被覆不足を `cardinality` で拒否し、新 gate は attempts loop 全体の終了後の V:2054 にある。
**影響**: nit。性能 attempt が先でも後でも、検証 completed の既存拒否が優先する。
**推奨**: 配置と既存分岐を維持する。

## 裁定自身の点検

**所見**: §2の「6対未満」は異なる対の数として読めば正確だが、entry数の0〜5件と同義にするとT4を落とす。
**分類**: real
**根拠**: S:74 は「かつ6対未満」、S:96 と U:787 は「6件あるが stock/W1 が重複して5対」の新負例を定義する。
**影響**: nit。実装は正しく拒否するが、受理集合差の記述を件数だけと解釈すると監査範囲を誤る。
**推奨**: S:74 を「既存検査を満たし、6対の完全被覆を欠く（0〜5件および6件中の重複対を含む）」と明確化する。

**所見**: §1 A2の「検証 attempt は post_performance_failure のraw経路を持てない」は、現 validator の拒否保証としては強すぎる。
**分類**: real
**根拠**: S:12 の当該断定に対し、V:2040 は slot を条件にせず marker・actual・a03 のいずれかを許し、schema:1188 の post 分岐も marker-null を要求しない；V:2108 が排除するのは actual 経路。
**影響**: nit。本差分は全非completedを既に例外扱いするため署名違反はないが、「例外は必ず開始前infra failureでa10へ写る」という説明は現物から導けない。
**推奨**: S:12 を正規運用上の想定と現 validator の保証に分け、top-level の具体的受理可否は未実測と記す。

**所見**: §5の evidence-without-attempt、TU束縛、成功の3択は実装へ暗黙追加されていない。
**分類**: refuted
**根拠**: `s5-implementation.diff`:5 の validator 変更は loop 後の gate 追加だけで、V:2062 が読むのは entry の `arm` と `workload`。
**影響**: nit。裁定パッケージ候補による予定外の受理集合縮小はない。
**推奨**: scope を維持する。

## 実装子の報告の検算

**所見**: 133 passed の実走記録は存在するが、「指定コマンドで実走」という記述はログと一致しない。
**分類**: real
**根拠**: A:69 は「指定コマンド」、S:140 は `tools/run_tests.py`；author の `attempt-0001.events.jsonl`:83 は `python3 -c ... pytest.main(...)` の直接起動を記録し、同じ記録に `133 passed, 3 warnings in 794.95s` と終了コード0がある。
**影響**: nit。成功件数の捏造ではないが、指定runner経由の実行・実行場所判定をこの記録で証明できない。
**推奨**: A:69を実際の起動方法へ訂正し、指定runner経由の検証結果は親の実走記録で別途示す。

**所見**: 受理・拒否の説明と追加11ケースは差分に整合し、変異試験を実走済みとは報告していない。
**分類**: real
**根拠**: A:53 は「M1は机上評価」、A:85 は「変異M0〜M9の実走は未実施」；diff:150以降のparameter展開は正例を含め11ケースで、A:93の条件付き拒否とも一致する。
**影響**: nit。静的反転予測を変異実走の成功へ読み替えなければ、報告の検証範囲は保たれる。
**推奨**: 変異試験未実施の表記を維持する。

## 裁定パッケージ候補

**所見**: 失敗例外を利用した受領証が下流で certified 採用される可能性は、本レビューでは未確認である。
**分類**: plausible
**根拠**: S:126 は認証実装の責務として保留し、V:2057 の例外は `reason_code != "completed"` 全体を対象とする一方、R:105のa10は anomaly と開始前infra failureを明示する。
**影響**: 下流が失敗記録を認証対象から除外しなければ、証拠0件の記録が certified に選ばれ得るが、その選択経路は現物で確認していない。
**推奨**: 既存の「成功・certifiedの3択」候補に、allocation未成立・post failureを含む例外記録の認証上の扱いを併記し、本waveのmust-fixへ混ぜない。

## 総括

レンズAでは **must-fixなし**。署名一致、失敗正例の保全、既存分岐の優先、T2/T4の単一理由性を静的に確認した。

修正推奨は裁定・報告の説明にある。特に「指定コマンドで実走」は実ログと異なる。133 passed の記録は確認したが、本レビューでは pytest・変異試験を実行していない。ファイル変更も行っていない。