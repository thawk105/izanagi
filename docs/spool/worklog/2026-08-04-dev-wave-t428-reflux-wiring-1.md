---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-04
wave: dev-wave-t428-reflux-wiring
seq: 1
title: [T-428] trigger 候補受理を 5-bit wire へ閉じた — binding/v1 と epoch 分類で E 段候補表現の P1 を充足と名乗る (コード + docs、branch worktree-dev-wave-t428-reflux-wiring)
---

## 本文

- **[T-428] を完了した。** trigger-gating 軸の E 段候補受理を「構造検疫を通る任意の 1 行 C++」
  から「5 文字 wire (32 encodings)」へ縮小し、consumer 閉包 5 面 (受理点 / proposal schema /
  materialize / build cache 束縛 / replay) と admission の epoch 分類を同一 wave で閉じた。
  設計判断は {{D:trigger-wire-only-acceptance}} (D96 手続 — 境界テスト追随と同一変更単位)。
  **D121 P1 は「E 段候補表現について」充足と名乗る** (D149 の emitter 監査との連言。機械所有
  経路・連動改変・全面再構成偽装は非主張境界として D に明記)。cap-lift は依然 FAIL、
  `MAX_APPROVED_GENERATIONS = 1` 不変
- **binding/v1 の開示設計**: raw binding (mask・predicate_sha256・nonce・source) は専用 WAL
  record にのみ置き、build_start payload / provenance / formal report へは nonce 付き
  commitment だけを流す。裁定文の commitment 式 `sha256(canonical ∥ nonce)` は実装
  (nonce を canonical JSON の field に含める) を正とする erratum を段 6 で確定
  (意味は同等。stage6-fix-ruling.md が erratum の記録)
- **段 3 敵対 2 レンズ (ともに NO-GO、22 所見) が設計を 4 点補正した**: commitment 分離
  (raw mask の report 直載せ案を却下)、汎用 sink の 32 正準 membership (caller 慣習でなく
  sink 強制)、binding 要求の proposal 駆動限定 (機械 sweep 6 件の遡及被害ゼロを列挙実証)、
  P1 主張の E 段限定。段 6 はレビュー 2 本 (13 所見、全 real) + 焦点再レビュー 2 巡 + 実走
  fix の計 8 実装単位 (P/A/B/C/D + F1-F3/F2b/C2/G1/G2/H1/H2/I1) で閉じた
- **焦点再レビューが 2 巡目 fix の過剰拒否 (I5 違反) を検出した**: 全 post-policy campaign へ
  の campaign ID gate 適用が sort/backoff の正例 fixture 群まで拒否していた — trigger
  proposal 駆動限定へ縮退して回復。「偽装 downgrade の完全防御」は receipt が認証でなく
  内部整合である以上不可能で、主張縮小で閉じた (DW-O16 の 3 巡上限適用。以後は実測で閉鎖)
- **実走が静的レビュー 4 本の見逃しを 16 件検出した**: 初回 battery 13 赤 (実装欠陥 3 =
  no-build 経路の digest 分離漏れ ×2 + coder event の raw wire 射影、fixture 縫い目 10)、
  全走でさらに 3 赤 (旧受理集合を固定していた偵察側境界テスト 1 + fixture commitment 縫い目 2)。
  最終全走 = **5675 passed / 19 skipped / 0 failed** (2026-08-04、計算ノード dispatch)
- **変異 matrix 19/19 KILLED** (mutation-matrix.md)。M-B2/B4/B6 は失敗 node が期待の上位集合と
  なる erratum (共有 validator の tamper が admission 側へも正しく波及。判定不変)。
  正例 4/4 受理 (過剰拒否なし)。初回投入は親の runner リスト漏れで fail-closed 中止
  (spec は無傷、リスト修正で完走)
- **agent 契約の wire 化 (W7、ユーザー確認事項)**: coder-v4-autonomous-trigger-gating の
  出力を C++ 1 行から 5 文字 wire へ変更した。遮断設計 (tools なし・fresh context・リーク
  遮断文言) は不変。親の独立レビュー証跡 = stage5-agent-review.md。pin (manifest/adapter/
  review_ledger) は起草者と別単位が更新し、adapter は codex sandbox が .codex/ 書込を拒否
  するため、checker renderer の期待 bytes を親が review して適用した (3 回)。権限根拠は
  ユーザーの /dev-wave T-428 起動と D149 決定 (6) — 事後確認をお願いしたい
- **裁定パッケージ (ユーザーへ返す)**: 上記 W7 のほか、witness 表 (連動改変検出、freeze 族
  新設) の要否、formal report schema への binding receipt 化と recipient 閉集合 (D121 P2 の
  一部)、epoch による予算リセットの一般則、の 3 件は新規タスクとして下記に起票し、裁定と
  同時に着手可否を決めるのを推奨する
- **運用記録**: Pegasus queue が wave 中盤に INA (全 queue RUN 0) となり、テスト・変異・
  監査が数時間停止した。ユーザー指示で一時停止し、スケジューラ回復の連絡を受けて再開した。
  停止中は queue 非依存の実装・レビューを先行させた。local main は wave 中に 2 回取り込み
  (10 commit ff / 49 commit merge、いずれも incoming 監査違反なし)。provenance full 監査は
  land 直前の再走で確定する。親の操作事故 1 件 (worktree patch の cwd 取り違え、無傷復旧、
  memory に恒久記録)
- **provenance の未定義ケース + 親の記録ミス 2 件を、ユーザー裁定の message 修正で解消した**:
  (i) 両側が同じ実装 2 ファイルを変更した auto-merge (local main 取り込み) が「実装面に
  Codex author なし」の監査赤になった (片側変更のみの先行 merge は integrator 記録で通る。
  合成内容は両側とも Codex author 済み)。(ii) その merge の message が取り込み先 main tip を
  dcd8a2a と誤記していた (fetch 後の観測が stale なまま実行、実際は 23e4363) うえ、1 回目の
  message 修正が誤記どおりの第 2 親へ付け替えてしまい、後続 merge で canonical docs に偽の
  競合が出て発覚した。ユーザー承認 (2026-08-04) のもと `git commit-tree` で message と親を
  実態 (23e4363) へ正した — rebase 不使用・**tree byte 不変を diff 0 で実証**。
  SHA 対応: merge a44c276→2d1252e、続く 2 commit d643743→5503f5c、e36cf23→c76009c。
  変異 ledger の `repo_head` は旧 SHA (a44c276) を指すが tree は 2d1252e と同一。
  両側 auto-merge の trailer 規約は未定義のまま — 明文化は {{T:provenance-automerge-rule}} に
  起票
- 逐語の正本 = `output/insights/2026-08-04_t428-reflux-wiring/` (brief / facts-map / plan /
  lens×2 / s4-ruling / agent-review / rev×2 / fix-ruling (3 巡の裁定含む) / focal×2 /
  mutation-spec / mutation-ledger / mutation-matrix)

## 次の一手差分

### 完了

- [T-428] wire-only 受理・binding/v1・epoch 分類・D96 境界テスト追随を land した。
  受入全走 5675 passed / 0 failed、変異 19/19 KILLED。P1 は E 段候補表現について充足。
  remaining: none
  base: ce65c36b3825da19697da5111c74c49ad8bcc9f54ba7e584654b31eda4743246

### 新規

- {{T:trigger-crash-resume-topology}} **P2・新規**: crash 後 resume が未終端 attempt の
  variant を再評価して二つ目の build_start を追記し、以後の replay が topology 違反で
  campaign 全体を拒否する既存欠陥 (T-428 段 3 レンズ A 所見 2。本 wave の差分と独立、
  現行テストは fake evaluate で隠れる)。同一 attempt 再開の状態機械か recovery-abort 終端を
  設計する
- {{T:source-evidence-aba-snapshot}} **P2・ユーザー裁定待ち**: SourceEvidence の pre/post
  一致検査は compile 中だけ source を差し替える ABA を閉じない (T-428 段 3 レンズ A 裁定
  パッケージ)。immutable checkout / content-addressed snapshot からの build の要否を裁定する
- {{T:trigger-witness-table}} **P3・ユーザー裁定待ち**: mask と predicate_sha256 の連動改変を
  replay/admission で検出するには 32 点凍結 witness 表 (mask→source_bytes_sha256) が要る
  (freeze 族の新設なので実装せず裁定へ。{{D:trigger-wire-only-acceptance}} の非主張境界)
- {{T:report-binding-receipt}} **P3・ユーザー裁定待ち**: formal report schema への top-level
  binding receipt の追加と、binding recipient の閉集合設計 (D121 P2 の一部。現状は
  build_start payload 経由の commitment 複写のみで、report 側 schema は無制約 object)
- {{T:epoch-budget-rule}} **P3・ユーザー裁定待ち**: search_config 変更で campaign ID が
  変わると freshness/budget が新品化する。epoch 変更による予算リセットの一般則
  (許容条件・記録義務) を裁定する
- {{T:machine-materializer-emitter}} **P3・新規**: 機械所有の trigger materializer 3 経路
  (偵察 sweep / S1 直接比較 / extime 較正) を emitter 経由へ移行する別 D96 単位。現状は
  32 正準 membership が sink で守るが、経路自体は raw 文字列を渡している
- {{T:s8b-duplicate-key-disclosure}} **P3・新規**: s8b_prediction_runner の duplicate-key
  parser が raw key 名を例外へ反射し journal に残る (T-428 focal 所見。同ファイルへの wave
  差分ゼロの既存パターン)。固定文言化する
- {{T:auditor-nits-producer-schema}} **P3・新規**: auditor の nits producer schema
  (manifest) に required/one-of が無く consumer の exact-one-key より緩い。不一致は拒否側に
  倒れるが、producer schema を閉形へ揃える (pin 再 render を伴う小変更)
- {{T:provenance-automerge-rule}} **P3・新規**: 両側が同じ実装ファイルを変更した
  auto-merge の trailer 規約が `docs/ai-provenance.md` に未定義で、監査が fail-closed に
  赤を出す (本 wave で実測、ユーザー裁定の message 修正で解消)。合成のみの merge の
  記録規則 (author 出所行 / waiver / checker の判定変更のいずれか) を明文化する。
  merge message へ取り込み先 SHA を書くときは merge 実行直後に `%P` から取る
  (fetch 後の観測は stale になりうる — 本 wave で誤記 1 件)
