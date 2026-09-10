### A-01

主張: S1〜S4 の追加検査には、今日の production 経路でその検査だけが拒否する実在入力を名指しできない。

証拠:

- S1: 実在 index は legacy anchor 1 件だけで、現 active g1 と一致する。versioned directory は存在せず、`output/s8b-freeze/floor_protocol.json:1` は g1 の `e576e9cd...` を指す。
- S2: 実在する唯一の自己不整合入力は g1 だが、計画自身が例外にする。g2 は帯外 0 件である。`/work/1/SFC/tanab/dev-wave-jobs/wave-t419-seam-checknet/s2-plan.md:53-63`
- S3: production successor は実在 g2 だけで、content-address、receipt、自己整合をすべて通る。既存テストもこの正例を「DW-G04 の発火証拠には数えない」と明記する。`orchestrator/tests/test_env_contract_activation.py:1564-1568`
- S4: catalog 3 件のうち g1 の唯一の失敗は例外化され、残る 2 件は通る。負例案はすべて合成 artifact または mutation である。`/work/1/SFC/tanab/dev-wave-jobs/wave-t419-seam-checknet/s2-plan.md:99-108`

名指し不能な検査は、S1 の零選択面、S2 の非 grandfather 自己整合、S3 の self-consistency/content-address/acquisition-receipt、S4 の catalog self-consistency/policy audit の全部である。

成果物影響: 今日の certified 選択・レポート・台帳の受理集合は変わらず、検証済みという proof 参照だけが増える。

severity: **land 阻止**

### A-02

主張: S1 resolver の「複数候補拒否」は upstream が既に到達不能にしており、削除変異は production 上の等価変異になる。

証拠: index は同じ contract hash の 2 件目を resolver より前に拒否する。`orchestrator/campaign/s8b_floor_campaign.py:727-747`。legacy anchor は必ず先に 1 件登録され、versioned directory が無ければそのまま返る。`orchestrator/campaign/s8b_floor_campaign.py:783-816`。それでも計画は resolver 自身の複数候補拒否テストを追加する。`/work/1/SFC/tanab/dev-wave-jobs/wave-t419-seam-checknet/s2-plan.md:42`

成果物影響: resolver の複数候補分岐を削除しても floor 投入の受理集合は変わらず、変異 kill 件数だけが水増しされる。

severity: **実装前に直す**

### A-03

主張: S2 と S3 は計画上の S4 catalog audit に後段または前段から覆われ、単独帰属が成立しない。

証拠:

- S4 は authority snapshot 構築時に登録済み全 entry を検査する計画である。`/work/1/SFC/tanab/dev-wave-jobs/wave-t419-seam-checknet/s2-plan.md:59-64`
- historical resolver は先に `_authority_snapshot().state` を取得してから個別検証へ進む。`orchestrator/campaign/env_contract.py:690-702`。したがって安定した不整合 artifact は S4 が先に拒否し、S2 まで届かない。
- main loader では S3 callback を無効化しても、直後の S4 audit が同じ successor artifact を拒否する計画である。`/work/1/SFC/tanab/dev-wave-jobs/wave-t419-seam-checknet/s2-plan.md:30,61-71`
- issue tool は candidate chain の検証より前に `current_activation_state()` を読む。`tools/issue_env_contract_activation.py:178-211`。計画後はここでも S4 が先行する。
- DW-M01 は同じ入力を拒否する前後層が無いことを要求する。`docs/dev-wave/mutation.md:5-10`

成果物影響: S2 または S3 だけを無効化しても最終受理集合が変わらず、certified activation の保証を独立 2 gate と誤記する。

severity: **land 阻止**

### A-04

主張: g1 grandfather は規律 2 と 8/16 裁定に反し、しかも恒久化する。P1 は正当化できない。

証拠:

- 8/16 裁定は旧自己不整合較正を検証済みとして受理し続けることを止めると明記する。`/work/1/SFC/tanab/dev-wave-jobs/wave-t419-seam-checknet/refs/ruling-t419.md:5-7`
- 規律 2 は verifier が anomaly を検出した variant を即 reject とする。`CLAUDE.md:67-71`
- 計画は同じ anomaly を exact g1 組なら production で許可する。`/work/1/SFC/tanab/dev-wave-jobs/wave-t419-seam-checknet/s2-plan.md:53-63`
- `ever_active` は全 record の和集合として単調増加し、削除条件がない。`orchestrator/campaign/env_contract_activation.py:361-394,417-422`
- S1 index は将来も必ず legacy g1 anchor を歴史 resolver で検証する。`orchestrator/campaign/s8b_floor_campaign.py:783-812`。従って例外を消すと S1 自身が起動不能になり、例外が構造的に固定される。
- 例外は artifact 単位でなく resolver 全体に効くため、floor、WAL、ratified freeze、autonomous completeness、reflux closure、oracle report の全 6 consumerへ波及する。`orchestrator/campaign/s8b_floor_campaign.py:462`、`orchestrator/campaign/wal.py:1064`、`orchestrator/campaign/s8b_ratified_freeze.py:2820`、`orchestrator/campaign/autonomous_trial_completeness.py:368`、`orchestrator/campaign/reflux_source_closure.py:504`、`orchestrator/campaign/s8b_oracle_report.py:1715`

成果物影響: g1 を参照する floor protocol・COMMIT・歴史レポートが、自己不整合較正を使ったまま「検証済み」と残る。

severity: **land 阻止**

### A-05

主張: 「contract SHA と calibration SHA の exact pair」という例外鍵は過剰決定であり、calibration 側の比較を削除する変異を殺せない。

証拠: `contract_sha256` は `CalibrationRef.path` と `CalibrationRef.sha256` を含む dataclass 全 field の canonical hash である。`orchestrator/campaign/env_contract.py:73-88,154-169`。さらに contract hash は全登録世代で一意にされる。`orchestrator/campaign/env_contract.py:311-336`。従って SHA 衝突を仮定しない限り、g1 contract hash が一致して calibration SHA だけ違う有効 entry は作れない。

成果物影響: pair の片側を削除しても受理集合は変わらず、例外の狭さを変異 matrix で証明できない。

severity: **実装前に直す**

### A-06

主張: S1 は authority record の path だけを返して live filesystem から再読するため、receipt と protocol bytes の束縛が切れる。

証拠:

- 計画は resolver の引数を root だけとし、返された path を再ロードし、receipt に path/hash を追加しない。`/work/1/SFC/tanab/dev-wave-jobs/wave-t419-seam-checknet/s2-plan.md:23-24,76-79`
- index は runtime の現在 HEAD を解決する。`orchestrator/campaign/s8b_floor_campaign.py:651-668,868-874`
- `IndexedFloorProtocol` は既に authority 側の `raw_bytes` と SHA を持つが、計画はそれを捨てて path だけを使う。`orchestrator/campaign/s8b_floor_campaign.py:576-598`
- path の再ロードは通常の filesystem read で、indexed bytes との再照合がない。`orchestrator/campaign/s8b_floor_campaign.py:409-425`
- floor receipt は source commit を持つ一方、protocol path/hash field を持たない。`orchestrator/campaign/certified_writer_admission.py:27-31,196-204`
- wrapper は queued job を提出時 source commit に束縛する意図を明記している。`tools/pegasus/floor_campaign.sh:29-31,54-92`

これにより、提出後の protocol publish で同じ receipt が零候補拒否から受理へ変わり得る。また scan と再読の間の bytes 差し替えも authority record に束縛されない。

成果物影響: floor 投入の受理集合と使用 protocol 参照が、receipt bytes を変えずに後から変化する。

severity: **land 阻止**

### A-07

主張: S3 の acquisition receipt は外部取得証明ではなく、同じ JSON 内の自己申告同士の整合検査に留まる。

証拠: qsub ID、PBS ID、`pinned_clean`、`ht_off`、known-values の値はすべて calibration JSON 自身が持つ。`orchestrator/calibrator/schema_v2.py:345-469`。accepted admission は ID 同士の一致と boolean が true かだけを見る。`orchestrator/calibrator/schema_v2.py:521-544`。計画も外部 job result や human approval の束縛を追加しないと明記する。`/work/1/SFC/tanab/dev-wave-jobs/wave-t419-seam-checknet/s2-plan.md:128`

成果物影響: 内部整合した偽 receipt を持つ新世代を registry に登録すれば、activation admission は取得 provenance を独立証明できないまま certified 選択へ通す。

severity: **実装前に直す**

### A-08

主張: `(i)` 全体の差し戻しは過剰である。D329 の判断根拠は後続実測で崩れており、現在経路を壊さない第 3 の実装形もある。

証拠:

- literal `D329` の記載は旧 package から見つからなかった。しかし「ユーザーが事実を見ていない」という一般化は偽である。worklog は method 実体不一致、全 attestation が落ちる結果、裁定対象化を明記する。`docs/archive/worklog-phase3-0816-579.md:25-29,165-168`
- F339 は probe 改訂で exact 一致が全拒否になるという D329 の実質的理由まで記録している。`docs/failures.md:8327-8337`
- 元の裁定パッケージも全 Pegasus attestation が落ちることを明示した。`/work/1/SFC/tanab/dev-wave-jobs/wave-t419-seam-checknet/refs/s4-adjudication.md:175-179`
- D329 は method を単なる名前とし、両世代の中央値 2101.0 を根拠に物理量は同じとした。`/work/1/SFC/tanab/dev-wave-jobs/wave-t419-seam-checknet/refs/D329.md:12-18`
- 実際の method 定数は k、interval、CPU 選択規則を符号化したアルゴリズム ID である。`orchestrator/campaign/env_attestation.py:35-42`
- g1 は期待列自体に 3080.935 の帯外標本を持つが、判定は期待中央値から作った帯を観測列だけへ適用する。`orchestrator/campaign/execution_guard.py:400-417`。これは「method は測定の公正に無関係」という D329 の根拠を崩す。

第 3 の形は、serial 2 以降の composite activation callback で successor calibration の method と現 probe method を exact 比較する形である。serial 1 では callback 自体が呼ばれない。`orchestrator/campaign/env_contract_activation.py:395-401`。実在 g2 の method は現定数と一致するため、今日の g1 経路を変えず、未来だけを狭められる。`output/env/pegasus/calibration/registered/calibration-94a4b79fa31bba3c.json:1`

成果物影響: 現計画のままでは receipt が g1 の方式不一致を pass と記録し続け、将来の probe method drift も certified proof chain に残らない。

severity: **land 阻止**

### A-09

主張: M-G は部分的に誤りである。`FROZEN_MANIFEST` が成果物だけを pin する点は正しいが、編集面に source trust root が無いわけではない。

証拠: `campaign.lock/v2` の enforcement source closure は `env_contract.py` と `env_contract_activation.py` を明示的に含み、計画が変更する `ident.py` も含む。`orchestrator/campaign/campaign_lock.py:27-42`。binding は記録 commit blob と live disk bytes を照合する。`orchestrator/campaign/contract_loader_binding.py:324-359`。resume は不一致を `contract-loader-drift` で拒否する。`orchestrator/campaign/ident.py:365-373`

限定検索では repo 内の実 campaign に v2 lock は 0 件だったため、「現存 lock instance 0」は正しい。しかし「source pin する live trust root 0」は誤りである。

成果物影響: 既存の外部または配備済み v2 campaign.lock は resume を拒否し、新規 lock の `contract_loader_blob_sha256s` と proof 参照も変わる。

severity: **実装前に直す**

### M-A〜M-G 独立照合

| 項目 | 結果 |
|---|---|
| M-A | 一致。catalog は 3 entry、active/ever-active は linux g1 と Pegasus g1。`orchestrator/campaign/env_contract.py:245-304`、`orchestrator/campaign/env_contract_activations/00000001.json:1` |
| M-B | 一致。両方 48 標本、中央値 2101.0、帯 `[2058.98,2143.02]`、g1 は 3080.935 の 1 件、g2 は 0 件。両方 accepted。各 calibration JSON `:1` を静的再計算 |
| M-C | 一致。共有 verifier は active `:540` と history `:609` の双方から呼ばれる。`orchestrator/campaign/env_contract.py:486-516,519-544,601-612` |
| M-D | 一致。非テスト consumer は重複を除いて 6 件。WAL の resolver は `replay` 等の live COMMIT 検査に載る。`orchestrator/campaign/wal.py:1040-1085,1520-1528` |
| M-E | commit と D329 の履歴説明は一致。ただし「ユーザーが実質を見ていない」という一般化は A-08 のとおり不成立 |
| M-F | 一致。現テストは `REGISTRY` 2 件だけを走査し、required 1 件を固定する。`orchestrator/tests/test_env_contract.py:839-869` |
| M-G | 部分反証。現存 v2 lock は 0 件だが、source closure mechanism は実在する。A-09 |

pytest、build、campaign は実行していない。確認はコード精読、限定検索、SHA と JSON の静的再計算だけであり、緑は主張しない。

## 総括

- S1〜S4 のどの追加検査にも、今日それだけが拒否する production-reachable な実在入力がない。
- S2 と S3 は S4 catalog audit に覆われ、単独変異の帰属が成立しない。
- g1 例外は規律 2 と 8/16 裁定に反し、ever-active と legacy anchor により恒久化する。
- S1 は runtime HEAD と live path を読み、提出 receipt に protocol identity を残さない。
- acquisition receipt は内部自己整合であり、外部取得 authority ではない。
- D329 の根拠は g1 の帯外標本と method のアルゴリズム性で崩れている。
- `(i)` は serial 2 以降だけを strict にする第 3 の形で、今日の経路を保って実装できる。
- M-A〜M-F の数値と共有経路は概ね正しいが、M-G の source-pin 一般化は誤りである。

## 判定

**NO-GO — g1 例外が唯一の実在 anomaly を再受理し、S2/S3 は S4 に覆われ、S1 は receipt-bound authority を持たない。**