# 段 1 brief — [T-2327] s1_direct_comparison の sort 軸 producer へ契約 ID を束縛する

- base main: 34af5a571def179d1c841ce6e8a1cbcaeb9e9771 / branch: worktree-dev-wave-t2327-s1-sort-contract-binding
- 起動 gate: check_wave_startup.py --mode fresh --forbid-worktree-handoff --external-handoff → OK (乖離 0)
- 版: 軽量版 (段 2・3 は省略、段 6 の敵対レビュー子 1 本は実施)
- 実測環境: Pegasus login node。テストは親が `tools/run_tests.py` の焦点走で実走し、受入は全走。

## scope

`orchestrator/campaign/s1_direct_comparison.py` の `sort_best` cell で、D1630 が用意した binder
(`source_digest.resolve_evidence(..., sort_oracle_contract_id=)` → `_resolved_src_token` →
`_bind_sort_oracle_contract_id`) を通して src_token を確定し、同じ契約 ID を `pipeline.evaluate` の
既存 keyword `sort_oracle_contract_id` へ渡す。これで sort_best の identity (variant_id)・WAL・
build cache が同じ契約 ID で束縛される (D1548 の sort 軸局所適用、T-2253 で loop 側は済み)。

**前提の実測 (main 34af5a571):** 依頼文の「campaign identity への契約 ID・comparator の materialize・
oracle」の 3 点は s1 に既に存在する (L471-481 の `sort_swo_oracle: ORACLE_CONTRACT_ID`、L846-852 の
quarantine、L874-911 の SWO oracle)。欠けているのは L925 `source_digest.resolve(...)` と L1219
`pipeline.evaluate(...)` への契約 ID であり、本 wave の差分はこの 2 点に限る (worklog 1277 の
[T-2327] 項と一致)。

## 確定済みユーザー裁定

- D1548: 文法版の cache 束縛は sort 軸へ局所適用し族へ一般化しない。束縛は campaign 由来の明示引数で渡す。
- D1630: 単一 producer + binder のドメイン分離だけで閉じる。`resolve()` / `src_token()` の public seam
  へ引数を足さない。driver 側の `sort_swo_oracle` 参照は関数内 import。入口 gate は足さない。
- D95: 実装面は Codex role=author。
- [T-2237] (文法版の三脚束縛) は本 wave で触らない (ユーザー指示)。

## 不変条件

1. `sort_best` 以外の cell (backoff_fixed_best / stock_common / system_gate / ident_all / p2_2_flag_opt) の
   src_token・variant_id・evaluate kwargs は 1 bit も変えない。従来どおり `source_digest.resolve()`。
2. `resolve()` / `src_token()` に引数を足さない (D1630)。`loop.py` を触らない。
3. 束縛に使う契約 ID の値は、oracle が attest した `contract_id` (L899 で実行中 `ORACLE_CONTRACT_ID` との
   exact 一致を既に要求) であり、`cfg.search_config["sort_swo_oracle"]` と同じ定数。新しい定数を作らない。
4. 規律 2: oracle 不通過 (REJECT) の DriverError 経路、契約 ID 不一致の DriverError 経路、
   `prepare_cell` の allowlist fail-closed は不変。gate・検査・台帳を新設しない。
5. `pipeline.evaluate` は既存 L1178 で `src_token != evidence.src_token` を fail-closed する。prepare 側の
   束縛と evaluate 側の kwarg は同時に入れる (片方だけだと sort_best が全件 abort する)。
6. 依頼の `evaluate_fn` 注入 seam (テスト用) には同じ kwargs を渡す (既存の `**kwargs` 経路)。

## 成果物 (編集面 = 実アンカー)

| path | 変更 |
|---|---|
| `orchestrator/campaign/s1_direct_comparison.py` | L161 `PreparedCell` に `sort_oracle_contract_id: Optional[str] = None`; L874-911 の oracle PASS 後に契約 ID を保持; L925 の token 確定を sort_best だけ `resolve_evidence(..., sort_oracle_contract_id=...).src_token` へ; L1205-1216 の evaluate kwargs に非 None のときだけ `sort_oracle_contract_id` を追加 |
| `orchestrator/tests/test_s1_direct_comparison.py` | 正例・負例を追加 (pytest 専用 allowlist file、自走 harness なし) |
| `orchestrator/tests/test_s8b_oracle_manifest.py` | L89 の materializer 全体 sha256 literal を新 bytes の値へ更新 (DW-O09 の pin 閉包で唯一の pin) |

pin 閉包 (DW-O09): s1 file 全体 sha256 `049642ca…` を値で検索 → test literal 1 件のみ。output/ の凍結成果物に
現行 sha の pin なし (insights の歴史記録のみ)。行番号 pin なし。producer write-path (DW-O10): 変わるのは新規
campaign の WAL/event/report の sort_best variant_id と build cache key だけで、既存凍結 bytes は変わらない。

## 割れうる前提 (親の provisional 裁定・攻撃対象)

- (P1) 依頼文の「3 点」は s1 が sort 軸 producer である根拠 (既存) で、本 wave の差分は resolve/evaluate への
  契約 ID 束縛に限る。`_search_identity` (search_config) は変えない。
- (P2) 束縛値の出所は prepare_cell 内で得られる oracle 結果の `contract_id`。`p3_s4_loop_sort._require_sort_oracle_contract(cfg)`
  を s1 から呼ぶ案は、`prepare_cell` に cfg が無く `prepare_cell_fn` seam を広げるので不採用。
- (P3) sort_best の prepare 側 token は `resolve_evidence(...).src_token`。`resolve()` の allowlist 検査
  `assert_worktree_within_allowlist` は `_assert_paths_within_allowlist(_tracked_status_paths)` と同一で、
  `resolve_evidence` も同じ検査を持つ (L2283, L2316, L2345)。evaluate 境界も再解決する。
- (P4) evaluate へ渡すのは `prepared.sort_oracle_contract_id` (非 None のときだけ kwarg を足す)。
  常に渡す (None 含む) 形にすると `evaluate_fn` 注入 double の `**kwargs` は通るが、不変条件 1 の
  「kwargs を変えない」を破るので不採用。

## 分割方針

実装子 1 本 (Codex role=author)。編集面 3 file で分割の利得なし。

## 並行 wave との重なり

稼働中 wave (ListAgents 07:00 JST) に s1_direct_comparison.py / test_s8b_oracle_manifest.py を触るものは
見当たらない。T-2237 は未起動。受入直前に main を再確認する。
