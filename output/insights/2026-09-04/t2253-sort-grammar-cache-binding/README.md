# [T-2253] sort 軸の campaign 由来の契約 ID を build cache の鍵へ局所束縛する

dev-wave (2026-09-04)。branch `worktree-dev-wave-t2253-sort-grammar-cache-binding`。裁定 D1548 (sort 軸へ局所適用、D1411 と同じ形)。

## 何をしたか

段 5 sort loop (`orchestrator/campaign/p3_s4_loop_sort.py`) の唯一の `run_campaign` 呼出しへ、単一 producer
`_require_sort_oracle_contract(cfg)` が返す `sort_swo_oracle.ORACLE_CONTRACT_ID` を keyword-only 引数
`sort_oracle_contract_id` で渡し、`loop.run_campaign` → `pipeline.evaluate` / `_prepare_evaluation_core` →
`source_digest.resolve_evidence` → 非 stock `src_token` のドメイン分離 hash (`sort-src-token/v1\0contract=<id>\0source=<digest>`)
→ `buildcache` の legacy / v2 両 API (`|src=` と v2 preimage の `src_token`) と四出口の `_recheck_source_evidence` まで届かせた。
既定 `None` で引数を渡さない campaign の bytes は不変。`default_cfg` / `search_config`、backoff 経路、受理集合は変えない。

## 段ごとの一次資料

| 段 | file |
|---|---|
| 1 brief | `s1-brief.md` (段 4 C0 で 6 件訂正) |
| 2 plan | `verbatim/s2-plan.md` |
| 3 敵対相談 | `verbatim/s3-lens-a.md` (識別子の意味・既定経路不変)、`verbatim/s3-lens-b.md` (全層の実効性・テスト帰属) |
| 4 裁定 | `s4-ruling.md` (C0 erratum、C1 採否表、C2 plan v2、C3 変異事前登録、C4 裁定パッケージ候補) |
| 5 実装 | `verbatim/s5-author.md` (commit 8f54a601c) |
| 6 レビュー / fix | `verbatim/s6-review-a.md`、`verbatim/s6-review-b.md`、`verbatim/s6-fix.md` (commit 590f2425f) |
| 6 変異 | `mutation-ledger.md` (要約と帰属)、`mutation-probe-spec.json`、`mutation-probe-out.json`、`mutation-final-spec.json`、`mutation-final-out.json`、`mutation-drift-mask.json`、attempt sidecar 2 件 |

## 変異の要約

18 件 (事前登録 14 + 段 6 後の再照準 4)。本走は 17/17 KILLED (期待 node と完全一致) + 等価変異 1 SURVIVED、harness rc=0。
単一理由と確認できたのは 10 件。M8 / M11 は 3 node の過剰決定、`loop.py` の M3 / M4 は contract-loader drift の冗長 gate
(58 node) に完全に吸収され owner (T5) の単独帰属は変異では示せない。`pipeline.py` の M5〜M7 は同じ mask に加えて固有の
owner node (T6) が出た。詳細は `mutation-ledger.md`。

## 裁定パッケージ候補 (実装していない)

- 契約 ID の権威境界 (checker hash は列挙 hash で挙動の閉包でない) — `s4-ruling.md` C4 / worklog の新規項。
- `s1_direct_comparison.py` の同種の identity / cache 分断 — 独立 task。
- `BUILD_START` payload への平文契約 ID の再掲 (per-attempt 監査性) — 別裁定。
