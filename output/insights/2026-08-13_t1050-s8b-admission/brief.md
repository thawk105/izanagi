# T-1050 段 1 brief

- scope: S8b floor が生成して content-addressed store へ保存する binary record に build admission receipt を耐久束縛し、resume・floor manifest・oracle 実走の全 consumer で検証する。
- 確定済み裁定: 第 10 回 #2 と RP-4 に従い、receipt 不在・不一致・store 差し替えを fail-closed に拒否する。
- scope 外: schema 世代移行、旧 portable artifact の互換 loader、既存 artifact の遡及再取得は実装しない。必要性と影響だけ insight・handoff・worklog fragment へ返す。
- 不変条件: 規律 2 を緩めず、hash 一致だけを admission の代用にしない。build gateway が発行した canonical receipt と binary record の対応を保存時から実走直前まで切らさない。
- 不変条件: 正当な fresh build → store → portable projection → resume → oracle pre-run の経路は通る。未知 key や malformed receipt を permissive に落とさない。
- 実 anchor: `build_cells` は `BuildAdmission` を得るが built record へ保存せず、`store_binaries` と `_verify_resume_store` は binary hash だけを見る。
- 実 anchor: `_PORTABLE_BUILT_KEYS` / `_validate_portable_built` / `project_built_records` / `resolve_portable_built` が floor・manifest の portable schema 境界である。
- 実 anchor: oracle `_prepare_v2_execution` は `store_path` の存在と `binary_sha256` だけを検査し、その後 report/WAL 実走へ渡す。
- 成果物影響: 未修正では admission 未証明 binary が同一 hash の store entry と record だけで floor 測定値・manifest・oracle report の証拠鎖へ入る。修正後はその受理集合を拒否側へ狭める。
- 成果物: production code と両方向テスト、receipt 不在・receipt/source/binding 不一致・store 差し替えの変異 matrix、焦点／波及／受入検査、insight と spool worklog fragment。
- 条件 dispatch: proof/oracle gate と新規検証に触るため DW-O08/DW-O13 を適用済み。凍結済み `output/s8b-freeze` bytes 自体は変更せず、新 schema 移行も行わないため DW-O09/O10 は非成立。
- durable manifest: 既存凍結 manifest の再発行は scope 外。新規生成 record の admission 束縛のみを狭い変更面とする。
- 受入環境: Pegasus login node。pytest/build は必ず `tools/run_tests.py`、floor/oracle 本走は計算ノードでのみ行う。本 wave は実測値を生成する本走を要求せず、実走前 gate の test を行う。
- 分割: manager は brief・裁定・変異・受入・記録・commit・land、read-only Codex は plan と敵対 review、workspace-write Codex author は production/test の一枚岩 ownership を担当する。
- (P1) provisional: portable record に canonical admission receipt を exact-key field として持たせ、build 時に receipt をコピーし、全 deserialize/consumer で current policy と record binding に照合する。段 2/3 の攻撃対象。
- (P2) provisional: store 差し替えは bytes hash 不一致に加え、別 cell の valid receipt/store record の組替えも receipt-source/binding 対応で拒否すべきである。段 2/3 の攻撃対象。

