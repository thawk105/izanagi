判定は、CR/LF 限定の二重防壁としては概ね妥当ですが、「path 細工による証拠同一性破壊を閉じた」という保証では NO-GO です。pytest は実走しておらず、静的検査と read-only の Git protocol probe だけを行いました。

### 1. NUL で同じ欠陥がそのまま残る

[severity: must-fix]

[攻撃シナリオ] `required_evidence.path` を `"CLAUDE.md\u0000not-the-contract-path"` とする。NUL は `_nonempty_string` と `PurePosixPath` を通り、提案された CR/LF guard にも掛からない。`cat-file --batch-check` では NUL 後が切り捨てられ、`CLAUDE.md` の OID が返る。その後 `EvidenceRef` は偽の NUL 付き path と、別表記 `CLAUDE.md` の blob hash を組にして保持する。現 checkout の Git 2.34.1 で、plain と NUL suffix がともに OID `1744da0e…`、blob 13812 bytes を返すことを実測した。これは本 wave が塞ぐ欠陥と完全に同型である。

[根拠 file:line] `orchestrator/campaign/s8c_preregistration_evidence.py:168-188`、同`:373-380`、`orchestrator/campaign/s8c_preregistration.py:965-978`、`s2-plan.md:224-230`、`premise_probe.py:34-44`。Git の入力契約は `/usr/share/man/man1/git-cat-file.1.gz:293-297` の「1 行 1 object、行全体を rev-parse」と一致する。

[提案] この wave の実装範囲を勝手に広げず、段 4 で「NUL は tab・一般制御文字と異なり、実在 Git path になれず、現に prefix blob へ alias する」という裁定パッケージを即時起票する。裁定までは保証文を「CR/LF alias のみ閉鎖」に狭める。must-fix の対象はこの裁定・保証境界であり、「本 wave で NUL も実装せよ」という提案ではない。

### 2. `read_blob_at` 単独では `./` 系 alias が残る

[severity: should-fix]

[攻撃シナリオ] `_safe_path` を迂回して `read_blob_at(..., "./CLAUDE.md")` を呼ぶと、契約表記は `./CLAUDE.md` のままでも `CLAUDE.md` の blob が返る。`./docs/../CLAUDE.md`、`./docs//phase3.md`、`./docs/./phase3.md` も正規化後の別表記へ alias することを実測した。通常の契約 JSON 経路では `_safe_path` が拒否するため現行 loader 経路の must-fix ではないが、plan の「未知の外部 caller にも効く」という一般化は広すぎる。

[根拠 file:line] Git は `./`・`../` 始まりを cwd 相対へ変換する (`/usr/share/man/man7/gitrevisions.7.gz:411-419`)。`read_blob_at` はその構文へ path を直結する (`orchestrator/campaign/s8c_preregistration.py:963-966`)。一方 `_safe_path` は absolute、`..`、非 canonical 表記を拒否する (`orchestrator/campaign/s8c_preregistration_evidence.py:183-188`)。plan の一般化は `s2-plan.md:76-83,100-107`。

[提案] `read_blob_at` を「CR/LF framing wall」と明記し、一般の path identity validator とは呼ばない。primitive 自体にも canonical path 契約を持たせるなら、CR/LF 以外の受理集合変更になるため別途裁定する。

列挙された他の構文については次のとおり。

- `:`、先頭 `-`、path 内の `HEAD:`・`:/`・`@{...}`・`^{}`は alias しない。commit は先に完全 OIDへ解決され、最初の `:` より後は path 側になる (`s8c_preregistration.py:951-966`)。
- `a//b`、`a/./b`、末尾 `/` は `PurePosixPath` との不一致、`..` は parts 検査で契約 loader が拒否する。
- symlink は `--follow-symlinks` を指定していないため、target ではなく symlink 自身の blob を読む (`s8c_preregistration.py:966`; `/usr/share/man/man1/git-cat-file.1.gz:240-248`)。別 path への alias ではない。
- NFC/NFD、大文字小文字は Git tree の異なる byte path である。overlong UTF-8 は strict decode で拒否され、Python `str` からの encode でも生成できない (`s8c_preregistration_evidence.py:144-148`, `s8c_preregistration.py:966`)。

### 3. `isinstance(path, str)` による非文字列 bypass

[severity: should-fix]

[攻撃シナリオ] 提案 guard は非文字列を検査しない。たとえば `Path("CLAUDE.md\r")` は `isinstance(..., str)` が偽だが、後続の f-string で実 CR を含む文字列になり、既存の trailing-CR alias に到達する。型注釈は実行時境界ではなく、`RequiredEvidence` dataclass にも型検査はないため、「手組み dataclass・将来 caller も第二防壁が守る」は恒真でない。

[根拠 file:line] `s2-plan.md:13-22,76,100-105`、`orchestrator/campaign/s8c_preregistration.py:960-966`、`orchestrator/campaign/s8c_preregistration_evidence.py:93-99`。

[提案] caller-independent 保証を残すなら、builtin `str` 以外を fail-closed にするか、path を一度だけ文字列化して、その同じ値を検査・Git 入力へ使用する。非文字列拒否は brief の受理集合を越えるため、段 4 で明示的に裁定する。保証を狭めるなら「builtin str という API 前提」を書く。

### 4. 親 probe は「同一 blob」を実測できていない

[severity: should-fix]

[攻撃シナリオ] probe は plain と trailing CR の raw bytes・OID・hash を比較せず、長さだけを表示する。異なる blob が偶然同じ 13812 bytes でも、brief は「同一 blob」と誤認する。

[根拠 file:line] `brief.md:9-12` に対し、`premise_probe.py:28-32` は `len(raw)` しか出力しない。

[提案] bytes equality、SHA-256、または batch-check OID equality を直接 assert する。今回の結論自体は別途の Git probe で支持されたが、親の保存済み実測 artifact 単独では支持されていない。

### 5. `_safe_path` の既存受理集合の説明が不正確

[severity: should-fix]

[攻撃シナリオ] 「末尾 CR/LF は拒否、tab は受理、埋め込み CR/LF は受理」という文を一般則として再利用すると、テスト frontier を誤る。`strip()` は先頭・末尾の CR/LF も拒否し、tab も端なら拒否する。埋め込み CR/LF も、別途 canonical/relative/`..` 条件を満たす場合だけ受理される。

[根拠 file:line] `brief.md:13-16`、`premise_probe.py:34-43`、`orchestrator/campaign/s8c_preregistration_evidence.py:168-188`。現 Python の `strip()` 対象は U+0009–000D、U+001C–001F、U+0020、U+0085、U+00A0、U+1680、U+2000–200A、U+2028/U+2029/U+202F、U+205F、U+3000。NUL は含まれない。`PurePosixPath` は `a//b`・`./a`・`a/./b`・`a/` を canonical 化し、現コードの等値検査が拒否する一方、`a/../b` は explicit `..` 検査が拒否する。

[提案] brief を「otherwise-safe な埋め込み CR/LF/NUL/tab」に限定して書き直す。末尾テストは受理拒否ではなく、新 reason と検査順を固定するテストだと明記する。

### 6. 現行成果物への誤爆は見つからない

[severity: nit]

[攻撃シナリオ] 新 substring guard が既存の正常 path、契約、freeze、fixture を拒否する可能性を確認したが、静的には反証された。

[根拠 file:line] 定数は固定 ASCII (`orchestrator/campaign/s8c_preregistration.py:34-41`)。`generation_path` は検査済み整数を固定 template に入れるだけ (`:991-996`)。現契約の全 path は `s8c_preregistration_evidence_contract.v1.json:9-480` の ASCII canonical 相対 path。freeze record の `source_path` も `condition-freeze.v1.g1.json:1` の固定値で、loader は `SOURCE_PATH` と exact 比較する (`s8c_preregistration.py:1016-1017`)。prereg markdown は固定 `SOURCE_PATH` から読む (`:981-988,1559-1563`)。fixture も同じ定数を使用する (`test_s8c_preregistration_core.py:84-95`、`test_s8c_preregistration_predicates.py:22,43-51`、`test_s8c_preregistration_invariant.py:30-39`)。

[提案] 契約 JSON・freeze record・prereg markdown・既存 fixture は変更しないという plan を維持する。

### 7. freeze 不変でも activation identity は変わる

[severity: should-fix]

[攻撃シナリオ] 対象 2 module の bytes が変わるため、正常 path しか使わない commit でも activation report の module hash と digest は変わり、trial registry の記録値へ波及する。freeze bytes が非対象であることから「成果物値も不変」と一般化できない。

[根拠 file:line] 対象 module の blob hash は `orchestrator/campaign/s8c_preregistration.py:1555-1558,1599-1609` に格納され、report 全体が digest 化される (`:1755-1771`)。trial registry はその digest を保持する (`orchestrator/campaign/trial_registry.py:1237-1247,1311-1321`)。brief の成果物影響は非実装時だけを記している (`brief.md:31-35`)。

[提案] freeze 再発行は不要という結論を維持しつつ、段 4 の成果物影響へ「core/evaluator hash → activation report digest → trial registry 値の commit 相応の変更」を追記する。

### 8. 二層 gate の役割分担は必要で、plan は概ね正しい

[severity: nit]

[攻撃シナリオ] 片方だけを残す変異を確認した。`_safe_path` だけなら直接 caller・手組み dataclass を守れない。`read_blob_at` だけなら契約自体は valid と判定され、bad required path は個別 `commit-blob-read-error`、未使用 consumer path は汚染値のまま残る。

[根拠 file:line] `_safe_path` は required と consumer の loader だけ (`s8c_preregistration_evidence.py:220-250`)。required path の blob 解決は `:373-380`、契約不正の一括写像は `:687-694`。consumer path は構築後に production consumer がない。逆に定数 caller は `_safe_path` を通らず `read_blob_at` へ入る (`s8c_preregistration.py:987,1486-1487,1555-1561,1712`)。別実装の `_batch_oids` も `read_blob_at` を通らないが、現状は固定定数と生成 path だけである (`:1124-1152,1346-1349`)。

[提案] 二重配置を維持し、各テストがどちらの層を殺すかを受入表に残す。`test_registry_rejects_control_char_contract_before_evidence_ref_construction` は `_safe_path` 層の検査であり、`read_blob_at` guard の検査には数えない。

### 9. CR/LF 用の新規負例は恒真ではないが、正例・既存回帰は guard を検出しない

[severity: nit]

[攻撃シナリオ] trailing CR/LF テストが「例外になった」だけなら既存 `_nonempty_string` で恒真になる。しかし plan は `.reason_code == "contract-path-control-char"` を要求するため、guard 削除・後置で既存 `contract-string` が出て落ちる。埋め込み候補も `candidate == candidate.strip()` を固定しており、M01〜M12 の CR/LF 変異対応は静的には成立する。

一方、次は両 guard を削除しても緑のままであり、防壁の保証には数えられない。

- `test_contract_loader_accepts_normal_relative_paths`
- `test_predicate_registry_is_exactly_c01_through_c12`
- `test_current_repository_gap_reason_snapshot_requires_cross_wave_review`
- `test_contract_semantic_hash_ignores_formatting_but_not_values`
- `test_evidence_contract_hash_is_semantic_canonical_json`
- `test_recorded_revision_is_accepted_and_ruling_is_checked_at_revision_commit`
- `test_effective_requires_all_twelve`
- `test_candidate_freeze_matches_contract_and_generation_chain`

[根拠 file:line] `s2-plan.md:136-203,205-222`、既存 nodeid は `test_s8c_preregistration_predicates.py:89,107,150`、`test_s8c_preregistration_core.py:391,480,848`、`test_s8c_preregistration_invariant.py:125`。

[提案] 上記は regression/positive control とだけ数える。CR/LF guard の mutation evidence は plan の direct core tests と explicit-reason loader testsに限定する。NUL、`./`、非文字列 bypass は現 matrix の detector を持たない。

## 総括

- CR/LF の `_safe_path`＋`read_blob_at` 二重防壁と M01〜M12 は、静的には成立する。
- ただし NUL が現に prefix blob へ alias し、証拠同一性の欠陥は残るため、裁定・保証境界は must-fix。
- 直接 `read_blob_at` には `./` 系 alias と非文字列 bypass も残り、caller-independent という表現は狭める必要がある。
- 既存契約・freeze・markdown・fixture への誤拒否は見つからなかった。
- pytest は実走しておらず、緑は主張しない。