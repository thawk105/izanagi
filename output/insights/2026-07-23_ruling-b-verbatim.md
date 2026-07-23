# [T-001] ruling-B 逐語・裁定凍結 (dev-wave、2026-07-23)

正本 = D83・worklog 2026-07-23 (5)。変異台帳 = `2026-07-23_ruling-b-mutation-ledger.json`。
code commit = 59b0e4d (基準 1ce9a2a)。

## scope と成果
oracle report consumer (`s8b_oracle_report.py`) に、消費する WAL の session record
(SESSION_STAGE) の record-level identity 検査を追加。fail-closed で (a) 全 session record の
issuer(`variant`)==共有定数 "oracle-session"、(b) campaign 内 env_tag 一貫、(c) manifest が
run_contract.env_tag を非空 str で宣言する場合その値と一致、を検査し違反を protocol_violation へ。
untrusted/malformed WAL への構造検査 (信頼境界 規律6)。

## brief 前実測 (裁定前提の確認)
- report は session record の record-level variant/env_tag を一切読まなかった。既存 env_tag 検査は
  manifest run_contract (`_receipt_expectations`) と execution_receipt C3-10 のみで別物。
  writer=driver `_append_session` が固定 issuer "oracle-session" + 渡し env_tag で書く。
  `"oracle-session"` は driver 1 literal のみ (共有定数なし)。floor は SESSION_STAGE に書かない。
- **正直な枠組み (docstring に反映)**: 実 run では driver が run_contract.env_tag を単一変数で全
  session append に通すため、正規 producer は env/issuer が構造的に一致し本検査を踏まない。よって
  本検査は「正規だがバグりうる/改変されうる WAL への構造検査」であり真正性証明ではない (D68 と同枠)。

## 敵対相談 2 (max、両 NO-GO) の主所見と裁定
- **pipeline-env 未検査 (両相談独立収束)**: report は pipeline record (bench_done) の env を見ず TPS を
  射影。session-only では tamper した bench env が certified selection へ届く。→ **scope 外 (ruling は
  session record 限定)。裁定パッケージ PKG-1 としてユーザーへ (実装せず・黙って拡張しない)**。
- **legacy/未検証 v2 manifest の env authority 欠如**: legacy は run_contract 無しで consistency-only、
  report は manifest 自体を verify しない。→ **[T-002] P-A1(a) 担当 (PKG-2)**。ruling-B は「(未検証の)
  宣言 env と一致」までと docstring 明記。
- legacy 実在の裏取り: loader が run_contract 欠落を LegacyManifest 分類、report が受理、既存 legacy
  テスト経路あり → legacy branch は dead でない (consistency-only fallback は生きる)。
- refuted: P3 の protocol_violation 両経路結線 (terminal 有/無)・driver 定数化の WAL bytes 同値・
  循環 import なし・凍結/golden 非波及。

## 実装 (段5) と親裁定 (段4)
- unit A=production (model 定数・driver 定数化・report helper+注入+T-080 taint+docstring)、
  unit B=test (fixture compat・_rewrite_session_identity・negative/positive/authority)。A→B 逐次。
- 実測: 正規 driver→report 統合 2 本が緑 (check が正規を壊さない)、fixture positive が期待 env-mismatch で
  protocol_violation。全走 2840 passed / 退行0。

## 敵対レビュー 2 (max、両 NO-GO → fix) の must-fix と対応
1. T-080 taint が identity+元 malformed-T080 issue 併存時に元 issue を mask (規律3 anti-masking 違反)
   → `_T080CampaignObservation("unavailable", issue=元)` で provenance だけ taint、診断は保持。coexist テスト追加。
2. legacy positive が session≠receipt≠pipeline の 3-way cross-env を completed で固定 →
   `_session_identity_issues(records,legacy)==[]` の直接 assert へ (completed 主張を廃)。
3. 全 SESSION record 全称性が未 pin (boundary record しか tamper せず、scan 縮小回帰が全新テストを通過)
   → 中間 trial-result tamper テスト + 変異 M6 追加。
4. docstring が env-match を v2 条件付けせず過大 → 「manifest が run_contract.env_tag を非空 str で宣言する
   場合に限る」へ厳密化。
5. 変異ハーネスの `git checkout` が未 commit の T-001 を HEAD へ revert する欠陥 → **fix 後に統合 commit
   してから harness を走らせる** + 成功条件に red_other==[] 追加。
- 所有外波及分析: build_observations の所有外 caller は driver 統合 1 + main() のみ。静的予測の所有外
  赤 0、全走で裏取り (2842 passed)。凍結 oracle manifest なし・report.py SHA 未 pin (編集は凍結物を壊さない)。
- 焦点再レビュー: **GO**、5 must-fix 全 closed・regressed 0。

## 変異 matrix (段6、最終コード)
5 kill (M1 issuer / M2 manifest-env / M3 consistency / M5 T-080 taint / M6 全称性) + 1 diagnostic
(M4 注入点) + 1 equivalent (driver 定数化)。**全変異で red_head=[]** = HEAD 99 テストは 1 件も検出せず、
検出力は全て新テストが買った (テスト強化の実証)。詳細 = 変異台帳 JSON。

## 裁定パッケージ (ユーザー再裁定待ち、実装せず)
- **PKG-1 (新事実)**: pipeline record の env が未検査で性能証拠 (bench_done.tps) の env 整合性を
  session-only では保証できない。正規 producer は踏まないが untrusted WAL では無防備。設計択一 = (a) 別
  wave で pipeline record env を照合対象に含める / (b) oracle report に射影時 env フィルタ導入 / (c)
  [T-002] の manifest verify で上流固定。推奨 = (a) を独立 wave。正式裁定は session record のみ (worklog
  2026-07-20(14)) ゆえ黙って拡張しない。
- **PKG-2**: manifest 自体の真正性検証 (report は VerifiedManifest を要求せず reps しか検査しない) は
  [T-002] P-A1(a) Stage 1 の担当。ruling-B の env authority はそれに依存する。
- **PKG-3 (親 brief 訂正)**: 親 brief の不変条件「性能経路の env フィルタを変えない」は前提が偽 —
  oracle report に env フィルタは存在しない。記録で訂正。
