# 段 4 裁定と変異事前登録 — dev-wave-t2327-s1-sort-contract-binding

軽量版のため段 2・3 は省略。段 1 の (P1)〜(P4) を親が裁定する。

## 裁定

- (P1) **採用。** 差分は `sort_best` cell の token 確定と evaluate kwarg の 2 点。`_search_identity` は不変。
  依頼文の 3 点は既存 (brief の実測)。
- (P2) **採用。** 束縛値は oracle 結果の `contract_id`。L899 で実行中 `ORACLE_CONTRACT_ID` との exact 一致を
  既に要求しているので、束縛値 = 実行中契約 = campaign 宣言 (`_search_identity` の同じ定数)。
  `_require_sort_oracle_contract(cfg)` を s1 から呼ぶ案は seam を広げるので不採用。新しい gate も足さない。
- (P3) **採用。** sort_best だけ `source_digest.resolve_evidence(genome, pin, ccbench_dir=sub, cxx=cxx,
  sort_oracle_contract_id=<oracle の contract_id>).src_token`。他 configuration は `resolve()` のまま。
- (P4) **採用。** evaluate kwargs へは `prepared.sort_oracle_contract_id` が非 None のときだけ
  `sort_oracle_contract_id=` を足す。None のときは kwargs 集合が現行と同一。

## 変異事前登録 (DW-M01)

対象は本 wave が変える 2 面 — `prepare_cell` の sort_best token 確定と `run_role` の evaluate kwargs。
各変異は「同じ入力を拒否する層が前後にも内側にも無い」ことを実装後に確認する。

| # | 位置 | 変異 | 期待して赤になるもの |
|---|---|---|---|
| M1 | prepare_cell sort_best | 束縛を落とし `resolve()` に戻す (契約 ID を渡さない) | sort_best の正例: `resolve_evidence` が `sort_oracle_contract_id=ORACLE_CONTRACT_ID` で呼ばれ、その token が PreparedCell.src_token になる |
| M2 | prepare_cell sort_best | 契約 ID を oracle の値でなく別文字列 (例: 定数 + "-x") にする | 正例の契約 ID exact 一致 |
| M3 | prepare_cell sort_best | `PreparedCell.sort_oracle_contract_id` を None のまま返す | 正例の PreparedCell field 一致、および run_role が evaluate へ契約 ID を渡す正例 |
| M4 | run_role | evaluate kwargs への `sort_oracle_contract_id` 転送を落とす | run_role の正例: sort_best cell の evaluate_fn が `sort_oracle_contract_id=ORACLE_CONTRACT_ID` を受ける |
| M5 | run_role | 契約 ID を全 cell へ渡す (None 判定を落とす) | 負例: backoff_fixed_best / stock_common cell の evaluate_fn kwargs に `sort_oracle_contract_id` が無い |
| M6 | prepare_cell 非 sort_best | 非 sort_best の token 確定を `resolve_evidence` へ変える | 負例: 非 sort_best は `resolve()` が呼ばれ `resolve_evidence` は呼ばれない |

`DW-M08` の新旧両走は非該当 (production code の変更を伴う)。受理集合を縮小する wave ではない
(sort_best の token 値が変わるだけで、拒否経路は不変) ため、過剰拒否の正例登録は非該当。
両層同時変異 (prepare だけ束縛して evaluate へ渡さない) は `pipeline.evaluate` L1178 の既存 fail-closed が
掴む経路であり、本 wave の owner でないので登録しない。
