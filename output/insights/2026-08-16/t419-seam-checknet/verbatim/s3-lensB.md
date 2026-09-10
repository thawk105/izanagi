静的敵対検証のみ実施しました。M-A〜D、M-F はコードと実体が整合します。M-E は誤り、M-G は一部のみ正しいです。pytest・build・campaign は未実行です。

### B-01 — floor 実投入経路が seam の scope 外

主張: resolver を Python の admission に追加しても、計算ノードの shell と downstream consumer は literal path のままで、実投入経路に gate が届かない。

証拠: `orchestrator/campaign/certified_writer_admission.py:206-211`、`orchestrator/campaign/s8b_floor_campaign.py:167,255-260,3464-3490,3517-3523,6387-6394`、`tools/pegasus/floor_campaign.sh:947-965,972-973,1093-1095`、`orchestrator/campaign/s8b_holdout_admission.py:53,383-386`、`orchestrator/campaign/s8b_holdout_freeze.py:46,1288-1290,1430-1435`、`orchestrator/campaign/s8b_prediction_runner.py:79,1543-1547`、`orchestrator/campaign/s8b_ratified_freeze.py:76,2647-2648`。計画の所有範囲は `s2-plan.md:23-24,42-43,87-90` に限られる。hooks は `hooks/guard_write.py:268-273,380` を確認したが、path consumer ではない。

成果物影響: g2 protocol の床値投入、freeze、selector、ratified report が新 seam を通らず、g2 active 後は旧 g1 path のまま拒否または誤参照になる。

severity: land 阻止

### B-02 — resolver の6 consumer と g1 例外が live 経路を分断する

主張: `resolve_by_contract_sha256` は歴史成果物専用ではなく、WAL、floor、oracle、reflux、ratified、autonomous の実効経路に入っている。g1 例外を残せば自己不整合を受理し続け、削除すれば今日の g1 成果物を落とす。

証拠: `orchestrator/campaign/wal.py:1040-1068,1080`、`orchestrator/campaign/s8b_floor_campaign.py:457-464,549-554`、`orchestrator/campaign/s8b_oracle_report.py:1713-1718`、`orchestrator/campaign/reflux_source_closure.py:503-508`、`orchestrator/campaign/s8b_ratified_freeze.py:2816-2822,3288`、`orchestrator/campaign/autonomous_trial_completeness.py:366-373`。g1 の帯外標本は `output/env/pegasus/calibration/registered/calibration-753f535a8d024727.json:1484`、quality は `:1599-1601`。裁定は旧較正の受理停止を要求する `refs/ruling-t419.md:5-7` 一方、計画は g1 singleton を許可する `s2-plan.md:53-56`。

成果物影響: 例外を残すと certified 選択、WAL COMMIT・attempt topology、床値、oracle report、reflux closure、ratified freeze、trial completeness の全てで g1 の不整合が検証済み扱いになる。

severity: land 阻止

### B-03 — S4 catalog audit は「今日の受理集合不変」に反する

主張: inactive g2 の破損を production audit する計画は、正常な active g1 の lookup まで拒否し得るため、受理集合を変える。

証拠: 現在の production loop は active rows のみを検査する `orchestrator/campaign/env_contract.py:519-543`。g2 は registered catalog に存在する `:262-273`。計画は全3 entry を検査し、g2-only drift を拒否する `s2-plan.md:30,61-64,107-110`。

成果物影響: inactive g2 の path、hash、policy、self-consistency の異常だけで、現在の g1 campaign、WAL、floor、report の起動と台帳更新が停止する。

severity: land 阻止

### B-04 — production loader の callback 配線が明示 scope から漏れている

主張: ident と issue tool だけを変更しても、通常の `env_contract` loader は structural callback のままで、S3 admission が実際の activation lookup に発火しない。

証拠: 通常 loader は `orchestrator/campaign/env_contract.py:524-527` で `_is_valid_activation_successor` を渡す。ident は `orchestrator/campaign/ident.py:217-223,304-310`、issue tool は `tools/issue_env_contract_activation.py:205-211`。計画の production callback 記述は `s2-plan.md:33-35,68-71` にあるが、loader の実呼出し変更を明示していない。既存テストも現在の callback identity を `orchestrator/tests/test_env_contract_activation.py:1641-1661` で固定している。

成果物影響: 通常の activation state load が quality と構造だけで g2 を受理し、certified selection と activation record の根拠が分離する。

severity: land 阻止

### B-05 — P3 は path の一意性を authority と取り違えている

主張: A-07 の主張が正しい。index から一意に選べても、人間承認済み generation record や上位 authority bundle に束縛されていない。

証拠: brief の P3 は `brief.md:72-73`、計画は filesystem index から current hash に一致する record を選ぶ `s2-plan.md:76-81`。activation schema は env、generation、contract hash だけで `orchestrator/campaign/env_contract_activation.py:24-28,38-41`。index は filesystem artifact を走査する `orchestrator/campaign/s8b_floor_campaign.py:777-864`、AI reseal は current lookup から successor を作る `:909-942`。上位束の human approval と generation record が必要で未完成であることは `refs/s4-adjudication.md:23-39,71,132-133` にある。

成果物影響: 未承認の reseal artifact が certified protocol path として選ばれ、後続の authority bundle 導入時に path、receipt、report の作り直しが発生する。

severity: land 阻止

### B-06 — 裁定済みの method gate を計画が意図的に外している

主張: (i) は裁定済みなのに、計画は D329 を理由に method 比較を変更しないため、実装が裁定と矛盾する。

証拠: `refs/ruling-t419.md:5-7` は `effective_clock.method` の実体一致を要求する。計画は `s2-plan.md:49,124` で method を参照しない。現実装は `orchestrator/campaign/env_attestation.py:935-939` と `orchestrator/campaign/execution_guard.py:295-302` で非空文字列しか確認しない。g1 と g2 の方式差は `refs/parent-measurements.md:24-34` にある。

成果物影響: 期待 method と実測 method が異なっても receipt、certified report、受理判定が pass のまま残る。

severity: land 阻止

### B-07 — M-E の「全文検索0件」は現在の成果物自身が反証する

主張: 親の M-E は検索範囲の記述として成立しない。brief と plan 自身が D329、905941、c9c6da84 に言及している。

証拠: `brief.md:24-28` に D329 と commit が明記され、`s2-plan.md:49,124` に D329 が複数回ある。さらに `handoff.md:51-52` と `refs/D329.md:1` にも記載がある。

成果物影響: 「未見事実」を根拠にした (i) の差し戻しと裁定パッケージの結論が誤り、method gate の扱いを誤ったまま land 判定される。

severity: land 阻止

### B-08 — M-G は FROZEN_MANIFEST と実効 source trust を混同している

主張: FROZEN_MANIFEST に Python source がない点は正しいが、live trust root が0件という一般化は誤り。

証拠: `brief.md:33-35` は source pin 0 と主張する一方、`orchestrator/tests/test_frozen_artifacts.py:41-49,234-248` は成果物 manifest の範囲だけを示す。実際には `docs/phase3-8b-restart-runbook.md:62-63` が `source_commit` pin と imported module bytes 検査を明記し、`orchestrator/campaign/certified_writer_preflight.py:85-126` が実装している。submit receipt の commit field も `tools/pegasus/submit_floor.sh:474-485` にある。

成果物影響: source provenance の report と availability 前提を誤り、既存の source identity gate を二重実装または誤って除去する。

severity: 実装前に直す

### B-09 — 新規テストが production 自己参照と過剰決定を含む

主張: g2 activation positive は registry と fixture が同時に変わっても通り得る。また negative test は原因を一つに分離しないと、意図した gate ではなく hash/path/schema で落ちる。

証拠: serial2 fixture は `orchestrator/tests/test_env_contract_activation.py:275-295` で `ec.GENERATIONS` から hash を生成し、既存の real g2 test 自身が `:1564-1568` で DW-G04 の証拠ではないと明記する。計画はこの種の正例を `s2-plan.md:102-108` で採用する。検証順序は `orchestrator/campaign/env_contract.py:490-509` と `orchestrator/campaign/calibration_verify.py:105-137` にある。

成果物影響: composite gate を削除・弱体化した変異や、誤った rejection reason が生存し、certified 選択、activation acceptance、台帳の検査網が未証明になる。

severity: 実装前に直す

### B-10 — strict cache の TOCTOU fail-closed 主張が未証明

主張: strict cache を追加するだけでは、初回検査後に同じ path の bytes が置換された場合の再検査を保証しない。

証拠: 計画は二度読みと fail-closed を主張する `s2-plan.md:54-57` が、現 cache は hash 一致で即 return する `orchestrator/campaign/env_contract.py:601-609`。bytes の hash 検査は一回の read に依存する `orchestrator/campaign/calibration_verify.py:105-114`。提案テスト `s2-plan.md:100` は active cache bypass のみで、strict cache 充填後の置換を検査しない。

成果物影響: 同一 process 内で差し替えられた calibration が historical report、reflux closure、WAL 監査へ再供給され、検査済み表示と実 bytes が乖離する。

severity: 実装前に直す

GO / NO-GO: NO-GO

理由: 実投入 path が未配線で、resolver・catalog audit・activation gate の受理集合も同時には整合しない。

## 総括

- M-A〜D と M-F は registry、activation、calibration、consumer 件数と整合する。
- M-E の全文検索0件は brief と plan 自身により反証される。
- M-G は FROZEN_MANIFEST の範囲だけ正しく、source commit trust を見落としている。
- floor shell、driver、holdout、selector、ratified が seam の scope 外に残る。
- g1 例外を残しても削除しても、裁定と今日の経路の一方を破る。
- P3 より A-07 が実物に適合し、上位 generation record が必要である。
- pytest、build、campaign の実走はしていない。
- land 前に裁定 package と実装 scope の再確定が必要である。