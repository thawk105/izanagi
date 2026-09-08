# [T-2327] s1 の sort_best cell を SWO oracle 契約 ID へ束縛する — 変異台帳と実測

- wave: dev-wave-t2327-s1-sort-contract-binding
- base main: `34af5a571def179d1c841ce6e8a1cbcaeb9e9771`
- 実装 commit: `50cfcb683` (s1 束縛)、`fe1382d62` (s8b consumer 転送 + pin/double 追随)、`84ba5850c` (テスト key 名)
- 裁定: D1548 (sort 軸局所適用)、D1630 (binder と seam 不拡張)、D95 (Codex author)
- authority: none / default_effect: no-state-change (可変状態の正本ではない)

## 何を変えたか

`s1_direct_comparison.py` は campaign identity への契約 ID (`search_config.sort_swo_oracle`)、sort_best comparator の
materialize (quarantine)、SWO oracle 実行を既に持っていた。欠けていたのは src_token の確定と `pipeline.evaluate` への
契約 ID で、sort_best の variant_id と build cache key が契約に束縛されていなかった。

| 箇所 | 変更 |
|---|---|
| `PreparedCell` | 末尾 field `sort_oracle_contract_id: Optional[str] = None` |
| `prepare_cell` (sort_best) | oracle PASS が attest した `contract_id` で `source_digest.resolve_evidence(..., sort_oracle_contract_id=).src_token` |
| `run_role` | `prepared.sort_oracle_contract_id` が非 None のときだけ `evaluate` へ同じ kwarg |
| `s8b_oracle_driver.run_block` | `prepared_for_eval` へ写し、非 None のときだけ `evaluate` へ転送 |
| `s8b_floor_campaign._build_cells_impl` | sort_best だけ `resolve_evidence` と build kwargs へ転送 (`build_v2` の既存 keyword) |

非 sort_best の token・kwargs は 1 bit も変えていない。`resolve()` / `src_token()` の seam、`loop.py`、gate は不変。

## 親が見つけた consumer の取り残し (実装前の静的閉包 + 焦点走 1 回目)

s1 の束縛だけを入れると、同じ `prepare_cell` を使う 2 consumer が壊れる形だった。

| consumer | 症状 (fix 前) | 経路 |
|---|---|---|
| `s8b_oracle_driver.py` L1731/L1788 | `PreparedCell` を作り直して契約 ID を落とし、契約無しで `pipeline.evaluate(src_token=束縛済み)` | `pipeline.evaluate` L1178 `src_token != evidence.src_token` → sort_best 全件 abort |
| `s8b_floor_campaign.py` L4383/L4497 | 契約無しで `resolve_evidence` → `build_v2(source_evidence=未束縛, src_token=束縛済み)` | `build_v2` の src_token 照合 → sort_best が build admission で全件失敗 |

どちらも既存テストは evaluate / build を double にしていて捕まえない。fix1 で転送を足し、正例・負例を固定した。

## 焦点走 (13 file、計算ノード dispatch)

| 回 | 状態 | 結果 |
|---|---|---|
| 1 | author patch のみ | 3 failed / 686 passed — `PIN_GATE_SPEC_SHA256` (派生 pin) 2、`test_sort_swo_oracle` の double 1 |
| 2 | fix1 後 | 1 failed / 1196 passed — floor テストの key 名 `configuration` (正: `configuration_id`) |
| 3 | fix2 後 | 1197 passed / 11 skipped / 0 failed |

## 敵対レビュー (codex read-only、3 本)

- A (identity / cache 意味論): must-fix 1 — comparator が stock と同一 bytes に materialize される sort_best は契約を改版しても
  token が `STOCK` のまま。**refuted・scope 外**: D1630 の binder 規約そのもので、bytes が stock なら binary も stock。
  refuted 7 件 (宣言と oracle 値の不一致経路、prepare/evaluate 不整合、受理集合拡大、非 sort 漏れ、追加 consumer 無し、
  D1630 違反無し、旧 binding の黙認無し)。
- B (テスト検出力 / pin 閉包): must-fix なし。M1〜M4 は新規検出力、**M5 / M6 は既存テストでも落ちる冗長 gate**。
  M3 は prepare 側 1 node だけが production 変異を殺す (事前登録の期待を訂正)。
- C (fix 後の焦点再レビュー): F-P1〜F-P4 すべて closed、must-fix なし、M7〜M11 は明示 assertion で殺せ冗長 gate なし。

逐語は `verbatim/` (review-a / review-b / review-c / author / fix1 / fix2)。

## 変異 matrix

事前登録 12 件 (負 11 + 等価 1)。probe 走 (全件 SURVIVED 登録、dispatch) で観測 node を集めて期待の完全集合とし、
本走を dispatch で走らせた。****baseline PASSED、KILLED 11 / SURVIVED 1 / MISMATCH 0 / PARSE_ERROR 0**、期待と完全一致 (matching 12/12)**。

| # | 位置 | 変異 | 期待 node 数 | 本走 |
|---|---|---|---|---|
| M01 | s1 prepare | 束縛を落とし `resolve()` へ戻す | 2 | KILLED |
| M02 | s1 prepare | 契約 ID を別文字列にする | 2 | KILLED |
| M03 | s1 prepare | `PreparedCell` の field を None で返す | 1 | KILLED |
| M04 | s1 run_role | evaluate への転送を落とす | 1 | KILLED |
| M05 | s1 run_role | None 判定を落とし常に渡す (冗長 gate) | 2 | KILLED |
| M06 | s1 prepare | 非 sort_best も `resolve_evidence` にする (冗長 gate) | 6 | KILLED |
| M07 | s8b driver | `prepared_for_eval` の写しを落とす | 1 | KILLED |
| M08 | s8b driver | None 判定を落とし常に渡す | 1 | KILLED |
| M09 | s8b floor | evidence への契約 ID を落とす | 1 | KILLED |
| M10 | s8b floor | build kwargs への契約 ID を落とす | 1 | KILLED |
| M11 | s8b floor | None 判定を落とし常に渡す | 18 | KILLED |
| M12 | s1 prepare | 等価変異 (`is not None` → `not (... is None)`) | 0 (SURVIVED 期待) | SURVIVED |

台帳: `evidence/spec-probe.json`、`evidence/probe-ledger.json`、`evidence/spec-final.json`、`evidence/final-ledger.json`。

## 派生 pin の見落とし (F39 再発、実害なし)

materializer 全体 sha256 の literal (`test_s8b_oracle_manifest.py` L89) は旧 hash 値の値検索で拾ったが、その literal を含む
`PIN_GATE_SPEC_RAW` bytes の sha256 (`PIN_GATE_SPEC_SHA256`) は author prompt の「他の literal は触らない」で取り残された。
親の焦点走 1 回目で赤 2 件として出た。

## dispatch の再走 (本 wave の赤ではない)

本走の M12 は 1 回目に `PARSE_ERROR` (rc=16、待ち 908 秒、stdout 空) になった。gen_S の queue 待ちが
既定上限 900 秒を超えた F762 の型で、子は 1 度も起動していない。DW-M07 に従い sidecar を新 path へ複写して
`--wrapper-attempt 2` の `--resume` で取り直し、`SURVIVED` を得た。上の matrix は resume 後の確定値である。

## 受入

受入全走は本記録の commit 後に 1 回実施する (DW-O16 に従い記録を先に置く)。結果は wave branch の
受入 commit と land の receipt が正本で、本 file には後追いで書かない。
