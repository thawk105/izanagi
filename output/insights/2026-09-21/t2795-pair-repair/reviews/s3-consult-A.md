# 判定

**P1〜P3 は条件付き支持、P4・P5 は支持。実所見は must-fix 1、should 3、nit 1。** 最大の問題は、実 closure 検査を残した結合検査・変異検査について、編集 bytes と commit の整合を作る手順が欠けている点です。

指定必読資料は読めました。**全検査は未実走・静的読解**です。ファイル変更、pytest、変異実行、計測、job 投入はしていません。以下、`brief` は親 `s1-brief.md`、`plan` は `codex/s2-plan.md` を指します。

# R1 — real / must-fix：closure ratification 廃止から、編集後の実結合検査が通るとは導けない

**所在:** `brief:34`、`plan:198,224,345`、`orchestrator/campaign/contract_loader_binding.py:518`、`orchestrator/campaign/campaign_lock.py:53,124`、`orchestrator/tests/conftest.py:154`。
**放置時の影響:** 認可・stock 評価へ未到達の closure 拒否を、session 修復の検証結果や変異 KILLED として台帳に数える危険がある。
**型タグ:** [ドリフト] [テスト代表性] [手順漏れ]

互換 fixture が空になったことは確認できました。しかし `capture_contract_loader_binding()` は現在も **live bytes と HEAD blob の完全一致**を要求します。変更対象の `loop.py` と `p3_s4_loop.py` は、その85 path に含まれます。既存 lock の再利用にも `ident.py:392` の live closure 照合があります。

したがって「新しい走は新 sha を束縛する」は、**その bytes が参照 commit に存在し、live と一致する場合**に限ります。未 commit の実装や変異には当てはまりません。S4 は `run_campaign` より前にも `ensure_resumable_attempts` を呼ぶため、目的の session 検査より前に停止し得ます。

**推奨:** plan に次を固定してください。

- 結合正例・各変異を、変更 bytes と HEAD が整合する隔離 checkout／commit で実行する。
- 各変異の campaign root は fresh とし、旧 lock の closure を引き継がない。
- KILLED は対象の拒否点・assert まで到達したものだけ計上する。`contract-loader-drift` は検査準備失敗として分ける。
- closure 検査や resumability を stub して救済しない。

09 の「固定 SHA の更新対象ではない」という結論は支持できますが、**実行時 closure の制約が無いという意味にはできません**。

# R2 — real / should：session の発行証明と失効の具体的な契約が足りない

**所在:** `plan:31,36,46,244`、`orchestrator/campaign/execution_guard.py:56`。
**放置時の影響:** exact 型・sentinel を保持したコピーを、発行された session や失効前の session と誤認し、予定した所有期間を超える呼出しを受理し得る。
**型タグ:** [権限逸脱]

plan は辞書や `_AuthorizationResult` の偽装を拒否しますが、**同じ exact 型のコピー、状態の差替え、失効後の別名参照**をどう拒否するかは未確定です。型と private sentinel の一致だけでは「factory が発行したこの個体が現在有効」という証明にはなりません。

比較対象になる既存 `AuthorizedContract` は、PID・seal に加えて、`execution_guard.py:65` で issuer のキャッシュと **object identity** を照合しています。

これは未実装の session に実在する漏洞を断定する所見ではなく、設計契約の不足です。同 process 内の任意 Python 改変を防ぐセキュリティ境界まで要求する必要はありません。

**推奨:** factory が発行した個体と保存状態の対応、不可逆な close、例外時も close する所有範囲を明記してください。コピーを拒否するか同一の失効状態を共有させ、caller に返す receipt から内部状態を変更できないことも固定します。新しい S に古い認可情報を移して再利用する経路は認めないでください。

# R3 — real / should：重複防御を「各比較の独立 KILLED」にする設計が不十分

**所在:** `plan:241,324,325,327,345`、`orchestrator/campaign/ident.py:226`、`orchestrator/campaign/execution_guard.py:56`。
**放置時の影響:** 到達不能な内部状態でだけ赤になる unit test を、実際の持出し・fork・別 identity 拒否の証拠として報告し得る。
**型タグ:** [恒真ゲート] [テスト代表性]

plan は重複防御を認識していますが、「該当比較以外を整合させる」には限界があります。

- campaign ID の hash 部は canonical preimage の SHA-256 先頭8桁です。完全 digest 一致が成立する正常な保存状態では、ID 比較の一部は構造的に冗長です。
- 契約 SHA も bound identity に含まれるため、直接比較を消しても identity 側で拒否され得ます。
- fork 後は、新設 S の PID 検査より先に既存 `AuthorizedContract.issued_pid` が拒否し得ます。
- 同 process の S 無し二連続呼出しは leaf の one-shot 性を示しますが、実際の別 process・fork 持出しの検査ではありません。

**推奨:** 「受理集合を守る振舞い検査」と「防御的な内部整合検査」を分けてください。等価変異・冗長比較を無理に独立 KILLED にしないこと。別 process／fork の負例では、子で正規の `authorization_contract` を取得し直しても、親の S は拒否されることを確認してください。旧2 process 形も独立した負例として残すべきです。

# R4 — real / should：「claim 無しで WAL に到達しない」は既存 driver 全体には成立しない

**所在:** `brief:27`、`plan:124,249`、`orchestrator/campaign/p3_s4_loop.py:2198,2233,992`。
**放置時の影響:** claim が保護する受理集合を過大に説明し、認可前の reject WAL を、認可済み測定と同じ保証の記録として扱い得る。
**型タグ:** [ドリフト] [捏造/幻覚]

候補の検疫 reject は `record_diff_reject()` に進み、`BUILD_START → ABORT` を直接 WAL に書きます。この経路は候補の `run_campaign` より前です。plan も「reject 時の S は通常未束縛、stock が初回 claim」を採用しています。

したがって、次の区別が必要です。

- **支持できる:** single_process 下の測定用 `run_campaign` は、取得または session 所有再確認を経る。
- **支持できない:** pair driver の全 WAL 書込みが claim 所有後に行われる。

これは既存経路であり、今回 session が新設する測定バイパスではありません。reject は certified や fitness を生成しません。

**推奨:** 本 wave の保証を測定 sink に限定し、負例の「WAL 変更なし」はその sink 呼出し直前との比較としてください。reject WAL も claim の保護下へ移す要求は、今回へ混ぜず、**別の裁定パッケージ候補**として返します。

# R5 — real / nit：「時間予算の述語は無い」は限定が必要

**所在:** `brief:38`、`plan:56`、`orchestrator/campaign/reservation.py:258`、`orchestrator/campaign/loop.py:208`。
**放置時の影響:** reservation の期限確認と、両評価の完走時間保証の区別がレポートから消える。
**型タグ:** [ドリフト]

`check_reservation(required_s=1, safety_margin_s=0)` は期限までの残時間を検査します。「時間述語が無い」は逐語では誤りです。一方、候補と stock の完走時間を予約する述語はありません。

**推奨:** 「新たな完走時間予算の述語は追加しない。既存の残時間1秒以上の presence gate を各 sink 到達時に再検査する」と書き換えてください。

# claim 防壁への個別攻撃の判定

以下は、plan どおり実装する場合の静的判定です。

| 攻撃 | 判定・根拠 |
|---|---|
| 辞書・別型で S を偽造 | **refuted 候補。** `plan:46` の exact 型・発行元検査で拒否。ただし同型コピー・失効は R2。 |
| 別 process への持出し | **refuted 候補。** `plan:47` の発行 PID・record PID・starttime 比較で拒否。実 process 負例は R3。 |
| fork 後の S 再利用 | **refuted 候補。** 継承した S の PID と子 PID が不一致。子で別途認可しても拒否する検査が必要。 |
| 別 identity／別契約 | **refuted 候補。** `plan:48–51` の現在契約と完全 preimage digest の再計算。S の値だけから期待値を作らないこと。 |
| 別 output root／use class | **refuted 候補。** `plan:52–55` は現在入力から root と claim path を再構成する。空の引数文字列同士の比較ではない。 |
| claim 削除・内容改変・symlink 化 | **refuted 候補。** `plan:55` と `_read_existing_payload` の `O_NOFOLLOW`（`campaign_claim.py:216`）で、再利用時に検出可能。 |
| 同内容で claim を置換／確認後に削除 | **保証外。** record 比較は inode の連続性や確認後の改変不存在を証明しない。既存 leaf も連続監視しないため、今回だけで第三者による任意 filesystem 改変への排他を保証したとは書けない。 |
| reservation 期限切れ | **refuted 候補。** 再利用時の実 `check_reservation` が拒否する。stock 実行途中の期限到来まで防ぐ設計ではない。 |
| DEAD claim 再取得・退避の密輸 | **refuted 候補。** `plan:35,74` は失敗後の救済取得を禁じる。leaf の `O_EXCL`（`campaign_claim.py:421`）は残る。 |
| S 検査が全体として恒真 | **refuted。** 通常 pair で PID・identity が一致することと、sink が不正入力を拒否できないことは別。個別の冗長比較については R3。 |

claim leaf の現 SHA-256 は `2e9c09328078378e4c9475f53e06cd338183373922ff2d83e5bcf218f7fd2dbd` で、brief の値と一致しました。実装後にも bytes 不変を検査する必要があります。

# stock・CLI・consumer への攻撃の判定

**refuted 候補 / must-fix 相当の攻撃:** 候補 authority による stock admission。
**所在:** `p3_s4_loop.py:2005,2089,3369`、`plan:95–107`。
**影響:** 混入すれば非 STOCK の候補由来源を対照として受理し得る。
**推奨:** plan の別 context・別 checkout・STOCK 専用 resolver を維持する。

現 stock resolver は `src_token == STOCK` にだけ generator receipt を発行します。成功判定も `p3_s4_loop.py:2096` の variant 一致と BUILD_START の STOCK 性を要求し、certified・非 aborted と組み合わせています。skip／identity-skipped は `:3424` で rc 1。plan はこの集合を変更していません。

候補と stock の **policy 同値は現実装で確認できました**。`build_admission.py:499,542` は authority の有無によらず `_new_policy()` を使用し、authority は別の nonce に保持します。ただし policy 同値は「stock に authority が無い」の証明ではありません。両方の assert が必要です。

**refuted 候補 / should 相当の攻撃:** pair 解禁による CLI の組合せ漏れ・B-5 consumer の破壊。
**所在:** `p3_s4_loop.py:3175,3185,3199,3302`、`b5_generator_contrast.py:478`、`plan:80–99`。
**影響:** B-5 slot に二評価が入り、台帳の一 slot 一評価という対応を崩し得る。
**推奨:** B-5 単独 stock の既存 argv を維持し、禁止組を main 経由で固定する。

plan は B-5 の現 OR 条件だけでは pair を拒否できない点、candidate opt-in が `not a.stock_control` で消える点、stock 分岐の early return を具体的に扱っています。machine-generated-proposal は B-5 必須条件と pair×B-5 拒否の組合せで閉じられます。B-4、明示 value、emit、no-build も禁止表にあります。

job body の既定 argv は `test_p3_s4_loop_job_contract.py:1912` に exact 比較があります。この期待値を変えず、pair 時だけ一起動へ変える方針を支持します。

stock の `LoopState`・planner・checkpoint 更新経路は現 stock 関数にはありません。critic digest の更新（`:2110`）は既存動作です。候補の checkpoint が stock により書き換わらない検査は維持してください。

# 結合検査・親の根拠・全層 scope

**refuted 候補 / must-fix 相当の攻撃:** 結合正例が OTHER／single_process=False や認可 stub に逃げる。
**所在:** `plan:193–235`、`test_campaign.py:9101`、`test_p3_s4_loop.py:9669`、`conftest.py:239`。
**影響:** 実 claim を一度も検査せず、修復済みと台帳に記載し得る。
**推奨:** plan の禁止 stub 境界を維持し、R1 の実行準備を加える。

plan は main 経由、canonical site、実 Pegasus 契約、claim root provisioning、実 reservation、実 acquire、実 WAL を要求しています。既存 fixture の OTHER 固定と、`_mock_required_attestation` の無条件 matcher も認識しています。この点は十分具体的です。

ただし `_mock_pipeline` は `test_campaign.py:6005` で source allowlist 検査も無効化します。合成 SourceEvidence を使う結合検査が示すのは**認可と結果処理の接続**までです。実 compiler による STOCK 性、checkout の実隔離、condition gate の成立は証明しません。root 依存の evidence を返し、候補 root を stock に誤配線する変異を捕まえてください。

親の実測根拠は次のように整理できます。

- **claim の全8 field 実在:** 原本 `submit-tree-pair/output/env/pegasus/claims/p3-s4-loop-s4-autonomous-b24749ae.claim:1` を読み、一致を確認。条件13の入力実在を支持します。ただし新設 S の発行・失効状態まで過去 claim が証明するわけではありません。
- **closure ratification 廃止:** `conftest.py:154` で確認。live closure 照合の廃止とは異なります。
- **SHA の出現先:** loop の現 SHA は A-1 受領証、shell の現 SHA は B-5 reservation 記録で確認しました。探索範囲では p3_s4_loop の現 SHA の出現を確認できず、brief の「3 file の現 sha が当時記録に出現」という細部は全件追認できません。09 の結論を文字列検索だけで支えないでください。
- **1 call 案の却下:** 現通常経路は `loop.py:787–790` で一つの tree/context/resolver を渡すため、分離設計が別途必要です。ただし「coder 編集木だから必ず非 STOCK」は成り立ちません。plan はこの親の過剰な一般化を既に訂正しています。

全層の scope は、loop sink、S4 CLI、job body、既存 B-5 consumer の互換性までが今回の修復・検査対象です。**Pegasus production pair は本 wave で未投入**とする plan を支持します。F1019 の production 1走要件（`verbatim/F1019.md:14`）については、結合検査の追加と実機確認待ちを分けて記録してください。結合検査緑を stock 対照成立や F1019 全層完了へ昇格させてはいけません。

## 総括

**real 所見: must-fix 1 / should 3 / nit 1。**

- **must-fix:** R1 — live closure と commit を整合させる結合・変異検査手順。
- **should:** R2 — session 個体の発行証明・失効、R3 — 重複防御と実 process 負例の代表性、R4 — 認可前 reject WAL を含む保証範囲の限定。
- **nit:** R5 — reservation の時間述語の記述修正。

| provisional | 判定 |
|---|---|
| P1 | **条件付き支持**。sink 再検査は妥当。発行・失効契約と実 process 負例を具体化する。 |
| P2 | **条件付き支持**。別 context／checkout／resolver と pair 専用排他を維持する。 |
| P3 | **条件付き支持**。通常例外後の stock 試行・候補非零優先を支持。未束縛 reject WAL は別保証である。 |
| P4 | **支持**。一 driver 起動、fixture pair 拒否、既定 argv 不変。 |
| P5 | **支持**。両 outcome を出し、成立判定は実 WAL に限定する。 |

**plan に追加すべき変異・負例:**

1. S のコピー、close 後の別名参照、別 S への保存認可移植を拒否する。
2. 実 fork 子が正規契約を再取得しても親 S を使えない。旧2 process・同 root・同 identity は `ClaimError`。
3. 初回と stock の間だけ reservation を期限切れにする。欠落・別 binding と分ける。
4. stock 到達前に claim を削除・破損・symlink 化し、測定へ未到達で拒否する。
5. summary の receipt を変更しても S 内部の認可を変更できない。
6. stock に候補 checkout／authority を渡す変異を、root 依存 evidence と実 admission で捕まえる。
7. pair×B-4／value／emit／no-build／machine-generated-proposal を main 経由で拒否する。
8. 各変異は closure 整合済みの状態から実行し、目的外の closure 拒否を KILLED に数えない。

**すべて未実走・静的読解。production pair 成立は未確認のままです。**