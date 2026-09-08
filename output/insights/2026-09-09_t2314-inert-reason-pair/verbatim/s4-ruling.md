# 段 4 裁定 — [T-2314] inert 比較の受理条件を「組」2 つへ

## 所見の裁定

| ID | 判定 | 採否 | scope | 根拠 |
|---|---|---|---|---|
| A-01 `evidence["comparison"]` の直接添字が赤 record で `KeyError` | **real** | 採用 | 内 | `verdict_s6` は probe:2556 で例外保護されておらず、fail-closed の判定が process 失敗に変わる。`.get("comparison")` へ直す |
| A-裁定候補 JSON scalar の型非厳密 (`"admitted": 1 == True`) | real | 不採用 | **外** | 既存問題。今回の文字列境界を破らない。裁定パッケージへ |
| B-01 受入所要台帳に新規 5 nodeid が無い | **real (ただし重大度は中→低へ訂正)** | 採用 | 内 | 実測: 台帳の関門は `test_g5_real_ledger_covers_at_least_90_percent_of_real_collection` の **90% 被覆**であり、node 単位の完全性ではない (現に gate 側の `test_inert_root_location_only_difference_is_green` は台帳に無い)。`nodeid_count` は tool が導出する。よって「合わないと受入が赤」は誤り。標準手順どおり受入 JUnit から `--add-only` で追加する |
| B-02 第 3 reason の fixture は `stock_comparison=False` が必須 | **real** | 採用 | 内 | `stock_comparison=True` だと `request-contract-invalid` で evaluator 前段から落ち、負例が恒真になる |
| B-03 交叉負例は seam に加え交叉 family と一致する receipt が要る | **real** | 採用 | 内 | 渡さないと pair membership の手前 (probe:365) で恒真に拒否され、probe 述語を守らない |
| B-04 2 組目の正例 fixture に欠陥なし | — | — | — | production evaluator・完全 evidence・issuer capability を通る本物と確認 |
| B-裁定候補 receipt schema の厳密版管理 | real | 不採用 | **外** | 既発行 v1 receipt に `condition_gates` 自体が無い。別問題 |
| B-裁定候補 t316 実経路の root-location-only 到達実測 | real | 不採用 | **外** | 計算ノード probe の実走が要る。本 wave は述語の変更のみ |

## 親 brief の訂正 (相談が正しい)

1. 成果物影響は「先行条件 (attempted / walltime / toolchain / source identity) を通過した
   root-location-only 観測では `S6_CONDITION_GATE_UNPROVEN` に固定される」が正しい。
2. 到達可能性の根拠は **t316 自身の実測ではない**。`docs/archive/worklog-phase3-0907-1291-1292.md:33`
   は A-5 の `backoff_sweep` 経路が同じ evaluator で root-location-only の緑になった記録である。
   evaluator (`evaluate_define_supply_effectuation`) は共有なので値は production で到達可能だが、
   t316 driver がその環境に置かれることまでは示していない。**D1625 はこの前提の上で下された裁定**
   (「`__FILE__` が置き場所で変わる環境では probe が構造的に赤のままになる」) であり、親は
   これを不採用にせず、限界として記録する。
3. 編集面は 2 file ではなく **3 file** (production / test / 受入所要台帳)。
4. pin は literal SHA では 0 件だが、`HEAD:<path>` を key にした実行時 pin
   (`t316_sandbox_backend_probe.pbs` の `BOUND_PATHS`、probe の `_BOUND_RELATIVE_PATHS`) が
   存在する。commit 後に新 blob へ自動束縛されるので co-edit は不要。「pin は無い」とは書かない。

## プラン v2 (確定)

1. probe に `_INERT_CONDITION_GATE_PAIRS: frozenset[tuple[str, str]]` を置く。要素は 2 組だけ。
2. `_condition_gate_receipt_summary` の supply entry へ `"comparison": supply.evidence.get("comparison")`
   を足す (**添字でなく `.get`** — A-01)。`evidence` mapping 自体は出さない。
3. `_condition_gate_family_valid` の 2 行を
   `(supply.reason_code, supply.evidence.get("comparison")) in _INERT_CONDITION_GATE_PAIRS`
   に置き換える。他の条件はすべて残す。
4. test: 2 組の正例、交叉 2 方向の負例 (seam + 交叉 family 由来の receipt)、第 3 reason の負例
   (`stock_comparison=False`)。既存 fixture `_condition_gate_receipts` に `comparison` を純増。
5. 受入 JUnit から `tools/update_acceptance_duration_ledger.py --add-only` で台帳へ 5 nodeid 追加。

## 変異事前登録 (DW-M01、実装前に確定)

いずれも `tools/pegasus/probes/t316_sandbox_backend_probe.py` の 1 箇所を置換する。
期待 node は完全集合とし、`--runner-mode dispatch` で本走する。

| ID | 変異 | 期待 KILLED node (完全集合) |
|---|---|---|
| M1 | `_INERT_CONDITION_GATE_PAIRS` から root-location-only の組を削り 1 組に戻す | `test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]` |
| M2 | pair membership を直積判定 (`reason in {..} and comparison in {..}`) に置換 | `test_s6_rejects_crossed_inert_condition_gate_pair[identical_reason__root_location_comparison]`, `test_s6_rejects_crossed_inert_condition_gate_pair[root_location_reason__identity_comparison]` |
| M3 | `_INERT_CONDITION_GATE_PAIRS` へ第 3 の組 (`requested-default-preprocess-different`, `requested-default-difference`) を追加 | `test_s6_rejects_requested_default_preprocess_difference` |
| M4 | receipt summary の `comparison` を定数 `"stock-inert-identity"` に固定 | `test_s6_accepts_each_exact_inert_condition_gate_pair[root-location-only]` |

単一理由性: M1/M3/M4 は gate が admit する入力に対して probe の述語だけが判定する。M2 は gate が
交叉を先に弾くため、seam で gate を中和した test だけが殺す (DW-M02 の両層裏取りに相当)。
実装後に各 anchor が単一箇所であること、および赤理由が上記 1 つに絞れることを再確認する。
確定できなければ probe と明記し erratum を残して再登録・再走する (DW-M08)。

## 不変条件 (変えない)

- 受理集合は D1625 の 2 組を超えない。`require_condition_gate_family` の呼出し、
  `observed == expected`、`admitted is True`、receipt summary 一致、`driver_id`、`macro`、
  `terminal_status == "green"`、meaning arm の 2 条件はすべて残す。
- 既存テストの期待値を変更・緩和・反転・skip・削除しない (規律 2)。
- gate 本体、policy、hooks、official-perf allowlist は触らない。
- `condition_gates` の各 entry に `evidence` key を出さない。
