# [T-244] P3 分割 wave 第 2 弾 — U-4 の記録形分離 (2026-08-06)

origin ledger の member 行数と候補数を別 field へ分け、実行候補の相異数だけを下限 gate へ掛けた
wave の一次資料。台帳への記録は `docs/spool/` の fragment 経由で行い、本 directory は逐語を持つ。

## 依頼と scope の選定

依頼は「report v3 か origin-proofs sidecar (U-4)」の二択だった。親の前提実測 (`parent-measured.md`
M1) により、**どちらもそのままでは実装できない**と判定した — ledger を import する production
コードが存在せず、sidecar の batch / seal / authority field を埋める実 artifact path が無い
(`DW-G04` の発火 gate 不成立)。report v3 は sidecar への参照に依存する。

そこで、この分割項のうち今 fireable な核である **U-4 の記録形分離**だけを scope とした。
sidecar 本体と report v3 は裁定パッケージへ返す。

## ファイル

| ファイル | 内容 |
|---|---|
| `brief.md` | 段 1 brief (scope、不変条件 I1〜I6、provisional 裁定 P1〜P4、名乗りの上限) |
| `parent-measured.md` | 親の前提実測 M1〜M7 |
| `s2-plan.md` | 段 2 の file:line 粒度プラン (codex, reasoning=max, read-only) |
| `s3-lensA.md` / `s3-lensB.md` | 段 3 敵対 2 レンズ。**両者 NO-GO** |
| `s4-adjudication.md` | 段 4 裁定 (T1〜T8、plan v2、変異事前登録 13 件、末尾に T6 再裁定) |
| `s6-reviewR1.md` / `s6-reviewR2.md` | 段 6 敵対レビュー 2 本。**両者 NO-GO** |
| `s6-refocus.md` | 段 6 焦点再レビュー (所見 11 件 + F1〜F6 の対応表) |
| `mutation-spec.json` / `mutation-ledger.json` | 変異 matrix 本走 (14/14 KILLED) |
| `mutation-spec-run1-erratum.json` / `mutation-ledger-run1-erratum.json` | 初回走行の erratum |

## この wave で決まったこと

`docs/decisions.md` の該当 D が正本。要点だけ再掲する。

- count は 3 つ。`member_row_count` / `distinct_candidate_count` (全 member) /
  `sealed_distinct_candidate_count` (非 tombstone)。**下限 gate は 3 つ目**に掛ける。
- 実行候補 0 の batch (全 tombstone) は gate の対象外。既定で受理集合を狭めないため。
- `batch_distinct_candidate_count_min <= batch_member_row_count_min` を parse 時に検査する。
- count はすべて ledger 導出。producer 申告 field を入力へ足さない。

## 両レンズ・両レビューが独立に指摘したこと

- **段 3**: 到達不能な候補数下限を authority が受理できる (A-3 / B-1)。
  tombstone の扱いに境界テストが無い (A-4 / B-2)。
- **段 6**: 旧 key 拒否の負例が旧形を再現していないため alias 変異が生存する (R1-4 / R2-1)。
  liveness probe が未追随 (R1-3 / R2-2)。V18 の fixture が stale (R1-1 / R2-3)。

## 親が裁定した論点 (レンズ / レビューが割れた 2 件)

1. **tombstone を候補数へ含めるか (A-4 対 B-2)。** 含めると `A, A, B(tombstoned)` が下限 2 を
   満たし、**実行していない候補 1 点で候補多様性を名乗れる**。count を 2 つに分け、
   記録は全 member、gate は非 tombstone とした。
2. **拒否理由 anchor をどちらで直すか (R1-2 対 R2-4)。** 実装を旧語彙へ戻すのは改名の目的に反する。
   テストの期待文字列を新語彙へ更新した。**親が明示許可した唯一の期待値更新**である。

## 親が撤回した裁定

- **段 1 provisional P1** (`QueryFloorConstraint` へ候補数下限を足す) — 段 2 の指摘を受けて撤回し、
  `BudgetPolicy` の単一 field を採った。query 数の式に直交する条件を混ぜないため。
- **段 4 の T6** (`output/insights` の probe は歴史記録として書き換えない) — 撤回した。
  追跡されたテスト `test_t244_p3_liveness_probe.py` が subprocess で probe を実行しており、
  前 wave の commit `2dc107ce` も同じ理由で probe を更新していた。裁定時点で親が見ていなかった
  事実である。

## 実測

- 段 5 後の焦点走行 (request 892393.nqsv): 3 failed / 41 passed。
  実装子は sandbox から dispatch できずテスト未実走だった。
- 段 6 fix 後の焦点走行: **48 passed / 0 failed**。
- 変異 matrix (tip `16cfdc6d`): **14/14 KILLED、SURVIVED 0、baseline PASSED**。
  初回走行は 5 件が MISMATCH で、すべて**親の登録 node が実測とずれていた**側の誤りである
  (実装の穴ではなく、変異はいずれも検出されていた)。初回台帳は erratum として残した。
- 受入全走 (tip `16cfdc6d`、request 892689.nqsv、1363.20s): **6779 passed / 20 skipped**。

## 名乗りの上限

名乗ってよいのは **ledger の記録形における member 行数・凍結候補数・実行候補数の分離と、
authority が下限を明示したときの certifiable `OriginSealed` 受理での per-batch 強制**まで。

名乗らない — P3 / P4 の充足・軸 (iii) の anti-oracle・origin-proofs sidecar・report v3・
completeness・U-1〜U-3 の完了・物理 query 数の証明・production provisioning・
certified 選択・cap 引上げ。**D114 の cap=1 と D166 の P4 FAIL は不変。**

## 裁定パッケージ (本 wave では実装しない real 所見)

1. origin-proofs sidecar と report v3 は wiring 待ちで実装不能。
2. `sealed_queries` 等の origin-level row counter の改名 (段 6 A-1 の不採用部分)。
3. 候補数下限の IR 空間上限 (<= 32) 検査 (段 3 A-3 / B-1 の不採用部分)。
4. 予算 codec 包絡線がさらに狭まった。U-10 の予算値裁定はこの新包絡線を前提にする必要がある。
