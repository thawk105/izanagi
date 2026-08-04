# [T-434] 段 4 裁定 — cap-lift receipt と consumer 結線の設計起草

wave: dev-wave-t434-cap-lift-receipt (背景 job)。裁定者 = 親。日付 = 2026-08-04。

## 総裁定

- **実装しない (起草のみ)。** 遷移は `4→7→8→9`。ユーザー裁定 (worklog (175)) が「起草して
  裁定パッケージで返す」と定めるため、段 5・6 は発火しない。実装差分ゼロのため
  **変異 matrix と受入全走は対象外** (射程は worklog fragment に明記)。
- 段 3 の全 24 所見 (レンズ A 11 件 + レンズ B 13 件) は **refuted 0 件・全件 real**。
  うち scope 内 (設計 v2 へ反映) 22 件、ユーザー裁定へ返す設計択一へ昇格 3 件
  (A3 trust root、A5/B13 revision 束縛と revocation、A6/B7 注入 seam の扱い。
  A5 と B13 は同一択一群として 1 件に統合)。
- 親 brief の provisional 前提の帰趨:
  - **(Q1) 撤回・修正** (A1/B2): receipt は「機械 gate ではない」ではなく「人間が発効する、
    機械 admission gate の policy input」。時相分離で書き直す。
  - **(Q2) 撤回・書き分け** (A7/B2): 基準集合を明記しない「狭めるだけ」は誤り。現状 cap=1 比では
    valid-receipt 多世代の受理は**拡大**、裸の定数引上げ比では**縮小**。実装 wave に D96 +
    変異事前登録 (過剰拒否の正例含む) を必須化。
  - **(Q3) 部分撤回** (A9/B5): 起草の独立は成立 (本 wave は完了できる) が、**v1 schema の凍結は
    [T-433]/V1 裁定に依存**。P6 部分は provisional/opaque と明記する。

## 所見別裁定 (全件 real)

| # | 裁定 | v2 への反映 |
|---|---|---|
| A1/B2 | 採用 | Q1 を時相分離で修正。依存順条項: 意味評価器・独立検査・境界変異が land するまで、reader/consumer が存在しても `generations > 1` は常時拒否 |
| A2 | 採用 | receipt/witness の写し一致は改竄検出のみで充足証拠ではないと明記。status は独立評価器が typed evidence から再導出する原則。評価器が存在しない P は `SATISFIED` 禁止 (s2 の同旨を強化) |
| A3 | 採用 + 択一昇格 | `AI-Agent: none` と topology は運用 trust root であり機械的本人確認ではないと明記。署名 + 鍵 registry は択一 8 としてユーザーへ |
| A4 | 採用 | 裁定 record を構造化 (decision kind / target revision / witness hash / cap / policy version / supersedes / 境界テスト manifest)。P10 は `HUMAN_RATIFIED` の別型。P4 緩和は policy version bump + D150 (2-b) |
| A5 | 採用 + 択一昇格 | v1 の既定を **exact-pin** (runtime tree = 承認 revision) に変更。descendant 再利用は択一 9 |
| A6/B7 | 採用 + 択一昇格 | 保証射程を「3 入口の `generations` 引数」に限定し D114 carve-out を逐語維持 (推奨)。admission record への provider/build mode 束縛は択一 10 |
| A7 | 採用 | Q2 の書き分け (上記)。実装 wave 必須条件に D96 + 変異事前登録 + 過剰拒否正例 |
| A8 | 採用 | 実効 cap の導出規則を変更: 承認値は receipt からだけ。`MAX_APPROVED_GENERATIONS` literal 1 は no-receipt fallback として維持し、対象 revision の定数値との「一致検査」を証拠から外す (絶対上限 `MAX_GENERATIONS` 比較のみ残す) |
| A9/B5 | 採用 | P6 部分を provisional/opaque 化。`semantic_contract_hash`・claim scope・構成 identity を予約 field として明示。s2 の「同じ union のまま使える」断言を削除 |
| A10 | 採用 | staleness は全 ledger blob でなく関連 D の canonical entry hash + 単調 supersession index の方向で記載 (v1 では exact-pin が主防壁) |
| A11 | 採用 | 機械検索可能な status marker (`status: PROPOSED_UNRATIFIED` / `machine_effect: NONE` / `MAX_APPROVED_GENERATIONS: 1` / 依存未裁定 T の列挙) を README・裁定パッケージ・worklog fragment に置く |
| B1 | 採用 | アンカー修正: 承認上限は `p3_autonomous_workload_trial.py:134`、CLI 既定は `:1720`、layer3 の search_config 消費は `layer3_report.py:416-418,434-435,459`、budget 挿入は `:510-518`。`test_autonomous_trial_completeness.py:808` は上限超過を拒否する負例 (受理テストではない) と訂正 |
| B3 | 採用 | 事前登録面の正本を `docs/phase3-8c-preregistration.md` へ差替え (同文書 69–72 行が既に多世代化の 3 条件を明記)。`docs/phase3-main-experiment.md` + S-1 freeze は no-touch。「S-1 freeze 再生成・repin」を handoff から削除 |
| B4 | 採用 | [T-435] の所有権尊重: T-434 は要求事項を渡すのみ。順序 = T-435 再事前登録 commit → その子孫で candidate G → 人間 receipt commit A |
| B6 | 採用 | 後続新 D の必須内容に D114 決定 (1) の逐語アンカー (「解除はこの定数 1 個と境界テストの同時変更だけで行い」) の明示 supersede + 遷移契約 |
| B8 | 採用 | 成果物の性格を「**blocked design memo**」に確定。再開条件を列挙 (DW-G04 整合: 発火 artifact path が現存しないため実装 wave へ直送しない) |
| B9 | 採用 | detached projection の exact envelope `{receipt_raw_sha256, receipt}` を一度だけ定義し、面ごとに「canonical bytes を持つ / SHA のみ」を固定 |
| B10 | 採用 | Layer 3 は v2/v3 の明示的 legacy 分岐 + v4 generator + 三版 reader 正負テストを実装 wave 要求に追加 |
| B11 | 採用 | cap-lift trust root は campaign `output_root` と独立の定数とし、production では repository root に固定。caller 注入 root を authority にしない |
| B12 | 採用 | witness manifest v1 は**未確定**と明記 (DW-O13)。v1 で確定するのは receipt の `witness_sha256` field の存在と形式のみ |
| B13 | 採用 + 択一統合 | revocation tombstone は裁定 6 面の外の追加 policy。v1 から外し、択一 9 に統合してユーザーへ (推奨: v1 は新 receipt 発行 + exact-pin で代替) |

## 親の独立裏取り (段 3 の主張を鵜呑みにしていない点)

- B3: `docs/phase3-8c-preregistration.md` の実在と冒頭・69–72 行を親が直接読んで確認した。
- B6: D114 決定 (1) の逐語 (`docs/decisions.md:5331-5334`) と保証外列挙 (`:5390-5398`) を親が直接確認した。
- B1: `p3_autonomous_workload_trial.py:133-134` / `:1720`、`layer3_schema.json:5`、
  `test_p3_autonomous_workload_trial.py:644` の monkeypatch、`output/README.md:24,49` を
  段 3 投入前に親が抜き取り検証済み。

## 設計 v2

本 dir の `design-v2.md` が確定版。s2-draft.md は履歴 (v1) であり規範ではない。
ユーザーへ返す設計択一は design-v2.md の「設計択一 (裁定パッケージ)」節。
