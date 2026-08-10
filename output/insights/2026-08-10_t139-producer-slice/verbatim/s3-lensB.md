指定された全資料と `orchestrator/qualification/` 配下は読了した。以下は静的読解のみで、pytest/build/qsub は実行していない。

### 1. N5 の矛盾を解消しないまま schema digest を固定できない

深刻度 = `blocker`

根拠: `s1-brief-addendum.md:94-110`、`addendum-a-reissue.md:266-285`、`record-items.md:128-135`、`s2-plan.md:274-285`

失敗シナリオ = preflight 最初の `a03` 観測が失敗し、marker も性能 raw も無い。`a04` は `post_performance_failure` へ写せと指定するが、record-items は marker または raw を要求する。`pre_performance_infra_failure` へ写せば a04 違反、marker を先に作れば実行順序違反、P8 の第三分岐は未裁定である。

成果物影響 1 行 = 正当な失敗 attempt の `reason_code`・証拠・置換可否が記録不能となり、receipt 受理集合が誤って狭まる。

### 2. reason enum が承認済み schema と一致していない

深刻度 = `blocker`

根拠: `s2-plan.md:281-285` は `pre_measurement_infrastructure` / `post_measurement_failure`、一方 `record-items.md:128-135` は `pre_performance_infra_failure` / `post_performance_failure` を要求する。

失敗シナリオ = 承認済みの qsub 失敗または preflight 失敗を正しい enum で出力すると plan の schema が拒否し、plan の enum で出力すると承認済み record-items 契約が拒否する。

成果物影響 1 行 = `attempts[].reason_code`、失敗集合、`retry_eligible` 判定が変わる。

### 3. N1/N2 に対する trust root が実装されていない

深刻度 = `blocker`

根拠: `erratum-core-s15.md:129-155`、`s1-brief.md:39-45`、`s1-brief-addendum.md:64-87`、`s2-plan.md:9-55,109-115,341-349`

失敗シナリオ = resolver は approval manifest ではなく caller の `addendum_a` と `F:<core path>` を読む。旧版・再発行版、または同じ core 三つ組を持つ未承認 A′ を caller が選べば、manifest 不在でも exact-key と ancestor 検査だけで通る。さらに plan の `fold_commit` は旧 D234 fold `88d68f...` であり、§51 の `approval_fold_commit = 2169a06c` と区別されていない。

成果物影響 1 行 = `PreregBinding` の追補・erratum・fold 参照が変わり、承認済みでない schedule や閾値が受理される。

### 4. schema digest が `PreregBinding` に束縛されていない

深刻度 = `blocker`

根拠: `s1-brief.md:8-14`、`record-items.md:180-199`、`s2-plan.md:85-93,248-253`

失敗シナリオ = 同じ schema path の bytes を後続 commit で変更しても、binding は `core/addendum/fold/HEAD` しか持たない。writer と verifier が異なる schema bytes を使っても検出できない。

成果物影響 1 行 = raw receipt の受理集合と `verify_receipt` の結果が schema の live bytes に依存する。

### 5. N3 を「pilot 投入不可」として機械的に止めていない

深刻度 = `blocker`

根拠: `s1-brief-addendum.md:6-33`、`addendum-a-reissue.md:825-838`、`preregistration.md:219-235`、`s2-plan.md:186-205`

失敗シナリオ = 第2 erratum が無いまま `submit_pilot(binding=...)` を呼べる。a12 の stress check を core §7 の「較正」と誤認して、pilot から `J` / `q` を導き、本走へ進める経路が残る。

成果物影響 1 行 = 型I誤り制御を「較正済み」とする誤った pilot admission と本走の受理基準が生成される。

### 6. N4 の alpha 台帳と producer の実行層が計画から欠落している

深刻度 = `blocker`

根拠: `s1-brief.md:8-16,84-90`、`s1-brief-addendum.md:35-62`、`record-items.md:163-175`、`s2-plan.md:39-55,86-90`

失敗シナリオ = 計画のファイル一覧に canonical alpha ledger、`t139_collector`、36-run の実 driver がない。二つの study が同じ `family_root` に対して `ordinal=1` を予約でき、preflight reject や qsub failure も raw の `attempts[]` へ回収されない。

成果物影響 1 行 = `reservation_commit`・ordinal 重複検査・失敗 attempt の exact coverage が無く、schema-valid な正例を生成できない。

### 7. `publish_raw_receipt` が binding を必須にしていない

深刻度 = `blocker`

根拠: `s4-adjudication.md:39-40`、`record-items.md:152-155`、`s1-brief.md:59-67`、`s2-plan.md:165-178`

失敗シナリオ = plan の署名 `publish_raw_receipt(repository_root, *, receipt)` は `PreregBinding` を受けない。caller は三つ組・HEAD・approval を照合せず、`atomic_publish` 経由で任意の receipt bytes を永続化できる。後段の `verify_receipt` は公開後であり、sink 認可にはならない。

成果物影響 1 行 = 未認可の receipt bytes が台帳・レポート候補へ残り、binding 参照の信頼境界が破れる。

### 8. P1 は §11 には整合するが、vertical slice の下流が未配線

深刻度 = `must-fix`

根拠: `preregistration.md:198-217,258-270,366-386`、`s1-brief.md:49-55,80-82`、`s2-plan.md:27-30,304,450,488-492`

失敗シナリオ = 36 run の順序・pairing・cluster 適格性が壊れた receipt でも、plan の `verify_receipt` は構造・三つ組・HEAD のみ確認する。適格性 validator、consumer、certified 選択への hook は存在しない。安全側では certified 集合が永遠に空、危険側では別 caller が raw receipt を合格扱いする。

成果物影響 1 行 = certified cluster 集合とレポート行が常に未生成、または誤って受理される。

### 9. 「e2e 正例」が resolver と手作り JSON のテストに退化している

深刻度 = `blocker`

根拠: `s1-brief.md:8-16,52-55`、`s2-plan.md:411-436,438-471`

失敗シナリオ = plan の合成 Git 正例は resolver の通過だけで、receipt テストも canonical JSON の round-trip に留まる。submission intent、PBS preflight、実 driver、collector、binding 必須 sink を通っていない。したがって stub が直接 schema-valid receipt を作っても全経路を迂回できる。

成果物影響 1 行 = 「1 本の受領証が end-to-end で出る」という判定が偽陽性になり、pilot 投入可否を証明しない。

### 10. 編集所有は素集合ではない

深刻度 = `must-fix`

根拠: 対象 `docs/spool/decisions/2026-08-08-dev-wave-t139-producer-1.md` は `s2-plan.md:53` に記載され、U0 が `s2-plan.md:477` で所有し、U5 も `s2-plan.md:482` で「必要なら決定 fragment」を編集する。にもかかわらず `s2-plan.md:484` は全所有が素集合だと宣言する。

失敗シナリオ = U0 の provisional 裁定を書いた後に U5 が同じ決定 fragment を補正し、resolver が参照する bytes・digest・fold 内容が変わる。

成果物影響 1 行 = approval manifest の参照値と `PreregBinding` の有効化条件が不安定になる。

### 11. T-126 機構の流用境界が未定義で、再発明も起きる

深刻度 = `must-fix`

根拠: `s2-plan.md:56-62,178`、`orchestrator/qualification/artifacts.py:4-5,227-243`、`atomic_publish.py:24-31`、`attempt_ledger.py:24-32,155-167`、`qsub_binding.py:55-80`、`collector.py:246-268`、`series.py:2,36-39`、`submission.py:3,21-27`、`contract.py:2,130-144`

失敗シナリオ = `QualificationRoot` は T-126 固定 root のため T-139 path を渡すと拒否する。逆に共通化を雑に行うと T-126 lineage が変わる。また `attempt_ledger` の retry 0/1、`qsub_binding` の returncode=0、T-126 collector の failure enum、`series.py` の SPRT/subject-reference semantics、`t126_*_schema.json` を流用すると、T-139 の36-run・qsub failure・alpha ordinalを表現できない。`atomic_publish` は低水準 primitive であり認可は持たない。

成果物影響 1 行 = namespace、failure enum、attempt coverage、qsub failure row、ledger semantics が T-126 側へ誤変換される。

### 12. 規模見積りがなく、1 wave に収まる根拠がない

深刻度 = `must-fix`

根拠: `s1-brief.md:73-74,84-95`、`s2-plan.md:39-55,86-90,473-484`、`s4-adjudication.md:39,52-56`

失敗シナリオ = 実装子は resolver、receipt、submission/PBS、registry に分かれるが、driver・collector・alpha ledger の実体が未定義である。先に registry・sink・前置だけ land すると、前 wave の blocker B5 と同じく「producer 実装済み」だけが台帳へ進む。

成果物影響 1 行 = 実行事実・receipt・台帳・certified 集合の間に穴が残ったまま、実装済み状態だけが進む。

## 総括

NO-GO。approval manifest、N3/N5、alpha 台帳、binding 必須 writer、schema enum が未解消で、承認済み受理集合と失敗台帳を正しく生成できない。  
P1 の段A限定は §11 と整合するが、validator→consumer→certified 選択未配線のため実効 vertical slice とは呼べない。  
2本に分ける。第1波で裁定・manifest・schema・alpha台帳を固定し、第2波で PBS/intent/collector/driver/binding sink/e2e をまとめ、最後に `submit_pilot` を公開する。