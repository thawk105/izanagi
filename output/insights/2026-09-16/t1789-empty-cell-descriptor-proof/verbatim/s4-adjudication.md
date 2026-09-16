# 段 4 裁定 — dev-wave-t1789-empty-cell-descriptor-proof

入力: s1-brief.md、codex/…/s2-plan.md (rc=0, check OK)、s3-lensA.md (正しさ境界, rc=0, check OK)、s3-lensB.md (整合・実効性, rc=0, check OK)。
裁定 inbox 再走査: wave 開始 (main 0c292eff6) 後の main e667c8c13 までに、本件 (T-1789 / s8c_acceptance_receipt / C02 / descriptor proof) に触れる新しい D・F は 0 件。関連 file の main 側変更は completeness の metric 名変更 2 行だけ (無関係)。
2 レンズは割れず、どちらも plan の 1 ブロック追加を支持した。

## 所見の裁定

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| 1 | B | 正例 P は fixture 初期値に C02 が無く、明示追加しないと mandatory-reasons で落ちる | real | 採用 (plan v2 で明記) |
| 2 | A,B | brief「全 case が do_build=False」は C4 を除く | real | 採用 (brief 訂正) |
| 3 | A,B,plan | (P3)「実行を名乗らない」は過大。terminal-failure にも observation-start があり、保証は「完了・観測成功を名乗らない」まで | real | 採用 (brief 訂正、insight/記録でもこの限定で書く) |
| 4 | A,B,plan | (P1) の status 式だけでは空 selected を排除できない。登録 trial は workload singleton に束縛 (`trial_registry.py` の登録制約) されるので、登録済み production 経路の結論は維持 | real (補足) | 採用 |
| 5 | B | brief「`_verify_v2_trial_arm_execution` は status を見ない」は不正確。report と receipt の status 一致は検査済みで、欠けているのは complete と descriptor 証明の対応 | real | 採用 (brief 訂正) |
| 6 | B | subprocess pin は静的呼出し箇所 inventory であり動的回数ではない | real | 採用 (記述の限定。変更は呼出し箇所を増減しない) |
| 7 | A | DW-G05 の「certifying 世代で B-3 の certified 選択が乗る」は断定できない (`build_accepted_report` は certifying 後も campaign 対応・admission・certified commit evidence・E1 epoch を要求、probe はそこを通していない) | real | 採用。成果物影響は「現在の verifier と v5 capability の受理集合に、descriptor 証明の無い complete 主張が残る。現在の certified 成果物への到達は確認されていない」に改める |
| 8 | A,B | 順序変異 (新ブロックを mandatory-reasons の前へ) は既存 node E が 2 条件を同時に満たすので単一理由ではない | real | 採用。受理集合を変えない診断順 pin として別枠記録し、新規検出力に数えない |
| 9 | B | 反転 `!= "complete"` と `== "partial"` は現行 status 集合で同じ振る舞い | real | 採用。反転は 1 本だけ登録 |
| 10 | A | legacy parser が任意の非空 status を受ける | real (静的) | **不採用・scope 外**。その形の実在・被害は再現されていない。値域 gate・台帳は足さない |
| 11 | A,B | v5 で partial へ書き換え attempt registry は observed のまま | refuted | 既存 `_assert_attempt_registry_consumption` の status 対応で拒否 (読解) |
| 12 | A | cells の型変更・複数化・descriptor 欠落で新条件を避ける | refuted | 既存の cells 形状 / descriptor 検査で拒否 |
| 13 | A,B,plan | 新条件は既存 gate からの恒真な照合 (D949) | refuted | C2/C3 は現行 verified を実測済み。expected digest 一致と descriptor 不在は両立する |
| 14 | A | 正規 partial / no-build / indeterminate を新たに誤拒否 | refuted | 新条件は `status == "complete"` だけ。indeterminate は formal acceptance が既に拒否 |
| 15 | B | 新 node の duration 台帳登録が必須 | refuted (読解) | conftest は未登録 node を None、acceptance_shards は 1 秒を割当て。親の受入で実測確認する |
| 16 | A,B | 共通適用 (P4) は D1757 に違反 | refuted | D1757 が退けたのは「失われた campaign 現物の追加要求」を伴う legacy leaf 再導出。本件は既に hash 済みの report bytes の status と descriptor 証明だけを見る。legacy v2 の A2/A3/B2 は実測済み |

## 確定事項

- **欠陥の定義 (P1 確定):** `status == "complete"` を名乗る trial の report に実行 descriptor が無い (cells=[]) のに、receipt が C02 を保持していれば `verify_acceptance_receipt` を通り、v5 なら `require_current_verified_receipt` まで届く。D519 の許容「descriptor を持たない部分 report」は complete に及ばない。
- **scope (P2/P5 確定):** production は `orchestrator/campaign/s8c_acceptance_receipt.py` の `verify_acceptance_receipt` に 1 判定ブロックを足すだけ。test は `orchestrator/tests/test_s8c_acceptance_receipt_v2.py` に 3 関数 4 node。`trial_registry.py`・schema・保存形式・台帳・他 gate は触らない。
- **適用世代 (P4 確定):** v2〜v5 共通 (`rederive_arm_execution` の範囲)。根拠は legacy v2 の実測反例と D1757 の却下理由の不一致であり、版分岐削減ではない。v3/v4 への効果は共通経路の読解であって実測ではないと記録する。legacy の受理集合が狭まる事実 (complete + cells=[] + C02) を記録に明記する。
- **修正後も残る形 (記録用、実装しない):** v5 partial + terminal-failure + cells=[] + C02 (D519 の正規形、正例)。legacy partial / 任意非空 status + cells=[] + C02 (current capability には届かない)。complete + descriptor 証明あり + C02 (本件の descriptor 不在ではない)。

## plan v2 (実装子への指示の正本)

### production

`verify_acceptance_receipt` の既存 `receipt-mandatory-reasons` 判定ブロックの**直後**、cross-binding aggregate 判定の**前**に次を置く (条件と文言は exact)。

```python
    if rederive_arm_execution and any(
        trial.status == "complete" and not descriptor_proven
        for trial, descriptor_proven in zip(receipt.trials, descriptor_proofs)
    ):
        _fail(
            "receipt-arm-binding",
            "complete trial lacks descriptor proof",
        )
```

- 新 helper・新 import・subprocess 呼出し箇所の増減なし。`_verify_v2_trial_arm_execution` と `_arm_execution_authorizes_reason_drop` は変更しない。
- 周辺のコメント密度に合わせ、必要なら 1 行だけ (D519 の部分 report 許容が complete に及ばない旨)。

### tests (`test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof` の直後に置く)

| node | 種別 | 組み立て | 期待 |
|---|---|---|---|
| `test_partial_receipt_cannot_claim_complete_without_descriptor_proof_even_with_c02[v2]` / `[v5]` | 負例 (再現 A2 / C2) | `_fixture` → H2/off report を cells=[] にして row の `report_sha256` 更新 → reason へ C02 を sorted unique で追加 → (v5 のみ) `_upgrade_to_current(repo, value)` → `_rewrite_receipt` | `AcceptanceReceiptError`、`^\[receipt-arm-binding\] complete trial lacks descriptor proof$`。report・row の status が complete、do_build False であることを前提 assert |
| `test_partial_receipt_cannot_hide_conflicting_descriptor_by_dropping_cells` | 負例 (再現 B1→C3) | H1/on descriptor の read_ratio_percent が int 80 を assert して 79 へ (receipt/run-start/binding の digest は変えない、`_synchronize_arm_execution` は使わない) → hash 更新 → `_rewrite_receipt` → v2 で `^\[receipt-arm-binding\] cell descriptor content digest differs from receipt$` を確認 → 同じ report を cells=[] に → hash 更新 → C02 追加 → `_upgrade_to_current` → `_rewrite_receipt` | 最後の検証が `^\[receipt-arm-binding\] complete trial lacks descriptor proof$` |
| `test_partial_receipt_with_c02_and_no_cells_passes_current_capability` | 正例 (承認外の過剰拒否の検出) | H2/off report を cells=[] → hash 更新 → **C02 を reason へ明示的に追加** → `_upgrade_to_current(repo, value, terminal_failure_trials=frozenset({row["trial_id"]}))` → `_rewrite_receipt` | verified。対象 trial の status が partial、reason に C02、certifying False。`require_current_verified_receipt(verified).sha256 == verified.sha256` |

- cells の変更は必ず `_upgrade_to_current` の**前**に行う (no-build leaf は cells 数を含む)。
- 既存テストの期待値・名前・helper は変えない。duration 台帳は編集しない。

## 変異の事前登録 (DW-M01)

走行対象: `orchestrator/tests/test_s8c_acceptance_receipt_v2.py` 全体 (file 内の完全集合で期待 node を持つ)。anchor の old 逐語は実装 commit 後に確定し、DW-M07 で再検証してから本走する。

| id | 位置 | 変異 | category | 期待 |
|---|---|---|---|---|
| m1-delete-gate | 新ブロック | 条件を `False and ...` にして判定を無効化 | negative | KILLED: N2[v2], N2[v5], N3 |
| m2-invert-status | 新ブロック | `trial.status == "complete"` → `trial.status != "complete"` | negative | KILLED: N2[v2], N2[v5], N3, P |
| m3-status-literal | 新ブロック | `"complete"` → `"completed"` | negative | KILLED: N2[v2], N2[v5], N3 |
| m4-v5-only | 新ブロック | `rederive_arm_execution` → `receipt.schema_version == SCHEMA_VERSION` | negative | KILLED: N2[v2] |
| m5-before-mandatory | ブロック順 | 新ブロックを mandatory-reasons 判定の前へ移す | both-layers | KILLED: E (`test_partial_receipt_cannot_drop_c02_reason_without_descriptor_proof`)。**診断順 pin として別枠記録、新規検出力に数えない** |
| m6-equivalent | 新ブロック | `trial.status == "complete"` → `"complete" == trial.status` | positive | SURVIVED (harness の生存検出の正例) |

期待 node の完全集合が file 内の他 node を含むかは、実装後の login selfrun probe で確認し、食い違えば本走前に erratum 付きで再登録する。

## 段 5 分割

所有 path は production 1 file + test 1 file で、正例・負例が新ブロックに依存するため 1 単位 (wave worktree 上の Codex `role=author` 1 本)。
