# 段 4 裁定 (親、2026-09-05) — [T-2301][T-2272]

## 裁定
- (P1) real・採用: README §4 の発効は worklog 1275 (D1638 委任) で実施済み。T-2272(a) の locator 4 件は
  現行位置へ更新し、§4 冒頭に「実施済み (worklog 1275)」の 1 行を親が添える (docs-only)。
- (P2) real・採用: job body の「同じ形」= 38 行目の既定代入 `EXPECTED_STUDY_ID="paper-story-a1-20260826-sized-v1"`
  を撤去し、v2 の case 枝で `EXPECTED_STUDY_ID="$REQUESTED_STUDY_ID"` を設定する。env 未設定は既存の
  case `*` → `refuse "study ID differs"` が既に fail-closed に拒否しており、挙動は不変 (構造の整合のみ)。
- scope 外の real 所見 (実装せず報告): `complete --study-id` (driver 8610 行) と内部 `load_policy(study_id=STUDY_ID)`
  にも同じ既定が残る。D1619 の文言は submit のみ。ユーザー裁定へ返す。
- 軽量版: 段 2・3・段 6 review 子を省略。実装子 1 単位 (所有: driver、job body、契約テスト 2 file)。
  契約が単位を跨がないので分割しない。

## 変異の事前登録 (DW-M01、実装後の最終 commit で anchor 再検証)
- M1 (受理集合): driver `_parser()` の `submit.add_argument("--study-id", required=True)` →
  `submit.add_argument("--study-id", default=STUDY_ID)`。期待 KILLED。殺す node = 実装子が足す
  「submit で --study-id 欠落 → SystemExit(2)」の test (完全集合は実装後に親が固定)。
- M2 (fail-closed): driver `run_submit` の `study_id = args.study_id` → `study_id = getattr(args, "study_id", STUDY_ID)`。
  期待 KILLED。殺す node = 「study_id 属性を欠く namespace で run_submit が既定へ退避せず AttributeError」の test。
- M3 (構造 pin、kill には数えない = diagnostic sensitivity pin): job body に既定代入行を再挿入。
  契約テストの source pin が赤になるが挙動は不変。別枠記録。
- 過剰拒否の正例 (DW-M01): `--study-id` を明示した submit (legacy / v3-pilot / v3-sized) が parse を通る test node。

## 実装子への不変条件
- 凍結 policy JSON 3 件は 1 byte も触らない。規律 2 (拒否経路) を緩めない。新 gate・台帳を足さない。
- 行番号 pin: `orchestrator/tests/test_ccbench_spawn_sites.py` が driver の 7103 行目を exact pin。driver の編集は
  7103 行より前で行数を変えない (1:1 置換)。
