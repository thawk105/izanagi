# [T-2591] 段 1 brief — 集約成果物が材料レポートまで届く正例

## 研究前進

B-4 reflux ablation の材料レポート (`p3_b4_material_report.py`) は §5 事前登録が pin した
authoritative floor を読み、その値を解析器へ渡し、床値の出所と非保証をレポートへ投影する。
D1974 で集約版 (`p3-b4-authoritative-floor/v2`、3 成果物の保守側最大) を発行できるようにしたが、
**集約成果物がレポートへ届くことは一度も実測されていない**。届くと示せない限り、B-4 の
材料レポートは集約床値を引用できず、rr5 / rr50 / rr95 の 3 系列を 1 つの床値へ束ねる D1855 案 B の
下流が閉じない。完了判定は「実 issuer が書いた集約 artifact の bytes が、実 builder を通って
レポートの `floor` 節・`certification_scope.not_guaranteed`・markdown に現れることを
1 本のテストが実走で示す」。

## scope

1. `test_p3_b4_material_report.py` に正例を 1 本足す。実体を名指しする:
   発行 = `issuer.issue_aggregate_authoritative_floor`、解決 = `resolve_preregistered_authoritative_floor`、
   公開 builder = `R.build_material_report_document`。publication root は既存
   `immutable_publication` fixture 由来の実 prerun publication + 実 raw analysis を使う。
2. 新 node を `test_real_repo_serialization.py::_P3_B4_MATERIAL_REPORT_NODES_GOLDEN` と
   `acceptance_duration_ledger.json` へ登録する。
3. (条件) 集約が実際に builder を通らない場合だけ `p3_b4_material_report.py` を直す。
   通る場合は production を 1 文字も変えない。

scope 外: 仮想リスク向けの gate・検査・台帳・一般化。既存テストの期待値変更。
`docs/phase3-b4-reflux-ablation-preregistration.md` の編集。集約器自体の受理集合変更。

## 確定済みユーザー裁定

- D1974: 期待 spec 列は呼び出し側から受け、入力から導出しない。窓ちょうど 2 までが機械検査。
  n=62 と 24 時間分離は人手の採用責任。集約は別 schema の別経路で、単一 summary 経路は
  1 文字も変えない。既存テストの期待値を変えない。
- 依頼: 「正例の実体を名指しし、性質だけの stub で両層を通す緑にしない」。
- 依頼: 「本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外」。
- 絶対規律 2: 正しさゲートを緩める変異を採らない。テストを甘くして緑にしない。

## 不変条件

- `_ABSENT_LEGACY_JSON_SHA256` / `_ABSENT_LEGACY_MARKDOWN_SHA256` (absent 経路の golden bytes) を
  動かさない。
- 既存 `test_m9_four_authority_and_assembly_states_project_exactly` の 4 状態の期待値を変えない。
- 正例は monkeypatch で issuer / builder のどちらの層も差し替えない。差し替えてよいのは
  既存 issuer テスト群が既に使う seam (`floor_pair_driver.calibration_verify.load_verified_calibration`)
  と `R._REPOSITORY_ROOT`、`os.fsync` だけ。
- 3 入力の床値は相異なり、集約値は最大でなければならない (最大でない値で緑になる正例は無価値)。
- `GENERATOR_IDENTITY` は両モジュールとも path 文字列で content hash ではない — 編集で pin は壊れない。

## 成果物の形

- 実走緑の新テスト 1 本 (+ 必要なら負例)。node ID を 2 台帳へ登録。
- insight README に「集約 → レポート」の到達を示す逐語 (レポート `floor` 節の実値)。
- 変異 matrix: 正例が実際に何を殺すか。殺さないなら正例は恒真であり、そう記録する。

## 並列分割方針

編集面が 3〜4 file と小さく所有が素集合に割れないため、段 5 は実装子 1 本。
段 3 は 2 レンズ並列、段 6 はレビュー 2 本並列。

## (P1) 親の provisional 裁定・攻撃対象

- **(P1-a)** 既存 `_write_floor_preregistration(present=True)` は手書き dict の stub だが、
  本 wave では**置き換えない**。D1974 項 4 の「既存テストの期待値を変えない」に従い、
  実 bytes の正例は新規に足す。→ 段 3 は「stub を残すと新正例が既存 m9 の緑に隠れて
  恒真になるのではないか」を攻撃せよ。
- **(P1-b)** 集約 (schema v2) は現行 builder を**無改修で通る**と見ている
  (`_authoritative_floor_source` は `schema_version` を素通しし、
  `_apply_authoritative_floor_projection` は `authoritative_floor.non_guarantees` を素通しするため)。
  → 段 3 は「通らない具体的な field / 検査」を名指しで探せ。通らないなら scope 3 が発火する。
- **(P1-c)** 集約入力の合成は既存 `test_p3_b4_floor_artifact_issuer.py::_aggregate_public_sources` を
  test module 間 import で再利用する (同 file が既に `test_floor_pair_driver` を import する定型)。
  → 段 3 は「private helper の跨 file 参照が壊れやすい / 共有 support module へ出すべき」を攻撃せよ。
- **(P1-d)** 正例は `build_material_report_document` (document 生成) までで、
  `write_material_report` (publish) までは辿らない。
  → 段 3 は「publish まで行かないと『届く』と言えないのでは」を攻撃せよ。

## DW-G05 (成果物影響)

放置すると、材料レポートの `floor` 節が集約床値を載せたときの値・出所・非保証の投影が
未検証のまま残る。レポートは certification 成果物なので、投影が壊れていれば
「どの床値でどう判定したか」の参照が誤ったまま出る。

## 編集面の重複 (起動時実測)

- T-2293 の編集面は `p3_autonomous_workload_trial.py` とその test のみ。本 wave と重複 0。land 済み。
- 稼働中 9 worktree すべて未 commit 差分 0。
- 起動直後に別 session が floor 系 wave 5 本を作成中 (t2288-floor-spec-freeze,
  t2592-calibration-miss-floor, t2595-floor-query-legacy-symmetry, t1851-c3c-official-floor,
  t1338-floor-residual)。段 5 直前と受入直前に再検査する。
