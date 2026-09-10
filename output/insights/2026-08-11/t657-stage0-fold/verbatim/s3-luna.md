判定: **NO-GO**。blocker 3件、must-fix 2件、nit 1件です。必読ファイルはすべて読取可能でした。

### LB-001 — P2 が未裁定の失効 schema と対象を固定している

- 主張: R1 は path・exact 7 key・0/1件・UTC秒 int だけを固定しており、7 key の名前・意味は未裁定。P2 はさらに「対象は X」「schema version」「generation」「actor」「reason」「X/A 参照一致」を決めている。
- file:line 根拠: `$R/docs/calibration-freeze-authority-bundle-design.md:815-832`、`$D/s2-plan.md:49-71`、`$D/s2-plan.md:164-172`、`$D/s2-plan.md:396-408`。下位 schema も別物である (`$R/docs/freeze-permanent-design-s2.md:432-458`)。
- key 判定: `schema_version` / `authority_bundle_generation` / `revoked_by` / `reason` は R1 から導けない。`bundle_digest` は path の対象 digest という関係だけが導出可能。`revoked_active_pointer_raw_sha256` は「束を失効させるのか、Xを失効させるのか」という未裁定の択一。`revoked_at` の UTC秒 int 表現だけは裁定から導ける。
- 具体的な失敗シナリオ: 後でユーザーが bundle 対象・approval 対象・RFC3339 等を選ぶと、P2 の docs/constant を前提にした resolver が有効な失効 record を拒否する、または別対象の失効を受理する。
- 深刻度: **blocker**
- 成果物影響: 失効後の受理集合と上位 X の terminal fail-closed 判定が、ユーザー未裁定の schema に依存する。
- これはユーザー裁定が要るか: **yes** — 7 key の中身と失効対象の意味が未決定。

### LB-002 — P5 は段 0 の fixture 閉包を段 1 以降へ送っている

- 主張: 段 0 は段 1〜4・6〜8 の陽性/陰性 fixture の実体を固定する必要がある。P5 の「row/case を増やさない」は、段 6 構造 predicate と失効 schema の検証義務を回避している。
- file:line 根拠: `$R/docs/calibration-freeze-authority-bundle-design.md:638-663`、`:670-677`、`:710-715`、`:774-781`、`$D/s1-brief.md:33-36`、`:86-88`、`$D/s2-plan.md:365-377`、`:452-463`。現行 `post-cutoff-bundle-identity.json:1` も pending のままで、段 6 X 用の case は存在しない。
- 具体的な失敗シナリオ: docs の (i)〜(v) と policy gate の drift だけが検査され、X の正当な陽性や各単一変異の陰性は一度も実 entrypoint へ到達しない。後続 resolver が reject-all または不正 X を受理しても、段 0 の fixture 閉包では検出できない。
- 深刻度: **blocker**
- 成果物影響: 段 0 の完了 predicate、X の受理集合、certified proof chain の入力が未固定のまま残る。
- これはユーザー裁定が要るか: **no** — §10 の fixture 閉包が既に要求しており、S/B の裁定とは独立。

### LB-003 — §12.3 畳み込み後も前方参照と状態文が自己矛盾する

- 主張: `grep -n "§12.3"` の結果は4件であり、plan は §7.5・段6行・§10.2 blockquote の更新は示すが、冒頭の「ユーザー裁定待ち3件」を更新していない。
- file:line 根拠: `$R/docs/calibration-freeze-authority-bundle-design.md:20`、`:454`、`:683`、`:724`。計画の置換範囲は `$D/s2-plan.md:43-74`、`:76-99`、`:111-124`。
- 具体的な失敗シナリオ: 同じ正本に「裁定待ち3件」と「残るユーザー裁定はない」が同居し、後続 wave が R1 を未裁定として扱うか、P2 を確定 schema として扱うか分岐する。
- 深刻度: **blocker**
- 成果物影響: gate 状態・設計正本・後続 wave の起票条件が不一致になり、proof chain の進行判断が再現不能になる。
- これはユーザー裁定が要るか: **yes** — R1 の未裁定部分を残すのか閉じるのかを決める必要がある。単なる行の掃除だけなら no。

### MF-004 — 「exact schema」と実装子の drift 束縛が一致していない

- 主張: docs は型・長さ・NFC・参照整合・canonical bytes まで固定するが、計画の実装は key 集合だけを `frozenset` で比較する。
- file:line 根拠: `$D/s2-plan.md:191-221`、`:337-361`、`$R/orchestrator/tests/calibration_freeze_authority_contract.py:318-338`。計画自身も key 集合だけの束縛と明記している (`$D/s2-plan.md:341`)。
- 具体的な失敗シナリオ: `revoked_at` の型や `revoked_by` の制約だけを docs 側で緩めても、7 key が同じなら contract test は通る。未裁定 schema を固定したうえで、その固定内容の drift 防壁がない。
- 深刻度: **must-fix**
- 成果物影響: 将来 resolver が読む失効 record の受理集合が、独立 pin に検出されず変化する。
- これはユーザー裁定が要るか: **yes** — 全 cell を固定するなら先に R1 の schema 裁定が必要。固定しないなら docs も ruled facts だけに縮める必要がある。

### MF-005 — execution 層は名指しされているが、検証 scope から実質外れている

- 主張: `required_gates` の直接 reader は contract module/test だが、execution module/test は `load_manifest()` を通じて manifest と fixture 閉包を消費する。計画はそこを no-touch としている。
- file:line 根拠: `$R/orchestrator/tests/calibration_freeze_authority_contract.py:460-505`、`:748-862`、`:888-912`、`$R/orchestrator/tests/calibration_freeze_authority_execution.py:16-20`、`:709-733`、`$R/orchestrator/tests/test_calibration_freeze_authority_execution.py:12-20`、`:48-65`。計画の no-touch は `$D/s2-plan.md:427-450`、`:452-457`。
- 具体的な失敗シナリオ: gate 件数だけなら実装変更不要だが、段 6/revocation fixture を追加した場合、`BUILDERS` と execution test が更新されず、contract だけが整合して実 entrypoint 実行が欠落する。
- 深刻度: **must-fix**
- 成果物影響: manifest 上の新規 fixture が実行証跡へ現れず、陽性/陰性の受理結果を certified report に含められない。
- これはユーザー裁定が要るか: **no** — 実装変更が不要なら「変更なしで実行検証する」と明記すればよい。fixture を追加するなら scope に含める必要がある。

### NIT-006 — 下位 family と同名の `_REVOCATION_KEYS` が誤用を誘う

- 主張: 下位は `_REVOCATION_KEYS = {generation_sha256, revoked_by, revoked_at, reason}`、上位 plan は同名定数に7 keyを入れる。`bundle_digest` も上下で別 domain の digest である。
- file:line 根拠: `$R/orchestrator/campaign/s8b_ratified_freeze.py:87`、`:114-121`、`:1134-1144`、`$D/s2-plan.md:164-172`、`$R/docs/freeze-permanent-design-s2.md:432-458`、`:642-646`。
- 具体的な失敗シナリオ: **推測**だが、後続実装が下位の constant/canonical helper を上位 resolver に流用し、上位 path の stem を generation hash と誤解する。
- 深刻度: **nit**
- 成果物影響: 上位失効 record の schema/hash 検査が下位 semantics になり、上位 authority の受理集合が誤る。
- これはユーザー裁定が要るか: **no** — module-qualified な `_UPPER_REVOCATION_KEYS` 等にすればよい。現状は namespace/domain を守れば意味は分離されている。

盛りの検査では、revocation key pin、段 6 predicate pin、policy gate の各機構について「docs/constant drift を拒否」「blocking gate を3件から4件へ変更」「X predicate の緩和を拒否」という成果物影響を一行で書けるため、追加機構そのものを盛りとは判定しません。ただし未裁定の P2 schema は実装対象から外すべきです。

## 総括

- blocker の所見 ID: **LB-001, LB-002, LB-003**
- ユーザー裁定が要る項目の ID: **LB-001, LB-003, MF-004**
- 攻撃したが破れなかった主張: **P1 の gate 投影と profile 非追加は既存 gate の分離原則から導ける。U1→U2 の現行ファイル所有は素集合であり、P4 の X (i)〜(iv) も上位 pointer の形状/ancestry と整合する。**