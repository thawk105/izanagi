判定は **NO-GO**。blocker 3 件、nit 1 件です。必読ファイルはすべて読めました。read-only のため pytest は再走せず、書込みなしの in-memory probe で抜け道を再現しました。

### SOL6-A-01

- 主張: `_read_design` は exact 3-backtick fence しか除去せず、CommonMark の `~~~` と 4 個以上の backtick、長い外側 fence 内の短い fence を権威として読む。
- file:line 根拠: 開始・終了とも 3 backtick 固定です。[contract.py:341–362](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:341)。既存の共通 scanner は `~{3,}` / `` `{3,}` `` と長さ以上の closer を扱っており、実装が不整合です。[check_docs.py:708](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/tools/check_docs.py:708)
- 具体的な失敗シナリオ: §7.5 の canonical 表、または §10 の段 6 行を `~~~text ... ~~~`／````text ... ```` 内へ移し、可視側から削除する。両方とも `validate_repository()` が `status=incomplete, pending=5, unresolved=2` を正常返却することを再現した。canonical 3-backtick の削除型は拒否され、4-space インデントも過剰拒否側なので、この抜け道は tilde・4+ backtick に限定される。
- 深刻度: **blocker**
- 成果物影響: S-B/S-C の「可視な設計正本を機械束縛した」という proof が偽になり、失効 schema と段 6 受理集合を隠れた decoy から供給できる。

### SOL6-A-02

- 主張: M1 は受理集合として KILL されていない。対応 node は raw-text mutant でも入力を拒否し、診断文字列の違いだけで赤になる。
- file:line 根拠: テストは canonical 表を fence 内へ「複製」した後、可視表を緩和します。[test_contract.py:795–819](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/test_calibration_freeze_authority_contract.py:795)。raw text では table prefix が 2 件となり、比較層より前の duplicate 判定が発火します。[contract.py:439](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:439)。これは診断文字列だけの赤を KILL に数えない `DW-M03` に反します。[mutation.md:16–20](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/dev-wave/mutation.md:16)
- 具体的な失敗シナリオ: `_read_design` を raw text へ戻すと、現 node は `revocation table is missing or duplicated` で拒否され、期待する `schema does not exactly match` と違うため失敗するだけ。一方、canonical 表を fence 内だけに置いて可視表を削除する入力は raw mutant が受理するが、その削除型 node は存在しない。
- 深刻度: **blocker**
- 成果物影響: M1 の mutation matrix を KILLED と記録できず、wave 前の既知の恒真ゲート形を閉じた証拠が成立しない。

### SOL6-A-03

- 主張: 段 6 control は最初の `。` までしか束縛されず、その直後に置いた相反する但書を無視して緑になる。
- file:line 根拠: extractor は `remainder.find("。")` で control を切り、後続については空でなく空白から始まることしか検査しません。[contract.py:495–501](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:495)。比較対象は切り出した control だけです。[contract.py:937](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/orchestrator/tests/calibration_freeze_authority_contract.py:937)
- 具体的な失敗シナリオ: canonical control 文の直後へ「ただし陰性変異は実行不要であり、reject-all でもよい。」を追加する。現行 `validate_repository()` が正常受理することを再現した。なお canonical 文の途中へ `。` を挿入する攻撃と、(i)〜(v) の省略は現行比較で拒否された。
- 深刻度: **blocker**
- 成果物影響: 段 6 の陽性・陰性 control 義務を後続 prose で無効化しても proof chain が緑になり、reject-all 防壁を空洞化できる。

### SOL6-A-04

- 主張: §12.1 の見出しだけが worklog 415 を落としており、本文の裁定由来と食い違う。
- file:line 根拠: 見出しは worklog 376/403 までです。[bundle-design.md:820](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:820)。同節の R1〜R3 は本文で worklog 415 の裁定とされています。[bundle-design.md:850](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t657-stage0-fold/docs/calibration-freeze-authority-bundle-design.md:850)
- 具体的な失敗シナリオ: 見出しだけを索引として読む監査が、R1〜R3 を 403 の裁定と誤帰属する。
- 深刻度: **nit**
- 成果物影響: 受理集合には影響しないが、裁定 provenance の索引が不正確になる。

## 総括

- 判定: **NO-GO**
- blocker の所見 ID: **SOL6-A-01, SOL6-A-02, SOL6-A-03**
- M1〜M7 を KILL する node: **M1 = 名指し不可** (`test_design_fenced_decoy_is_not_authoritative` は診断差だけの偽 KILL) / M2 = `test_design_revocation_constraint_relaxation_is_rejected` / M3 = `test_design_revocation_record_schema_matches_validator` / M4 = `test_design_stage6_structural_contract_matches_validator` / M5 = `test_adjudicated_ruling_and_gate_projection_is_exact` / M6 = `test_adjudicated_ruling_and_gate_projection_is_exact` / M7 = `test_design_revocation_record_schema_matches_validator`
- 攻撃したが破れなかった主張: **0 件・空 tuple は fail-closed、(i)〜(v) の欠落と control 途中の句点は拒否、新照合への到達順に緑抜けなし、段 0 は incomplete/pending=5/applicable_unresolved=2/blocking_gates=4、他者手番 2 gate の owner/status は不変、required-gates hash は manifest literal・canonical 再計算・module pin の三者照合、既存期待値の緩和・skip・削除・fixture hash 差し込み・揮発 payload 焼込みなし**