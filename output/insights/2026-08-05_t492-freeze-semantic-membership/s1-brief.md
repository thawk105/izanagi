# [T-492] 段 1 brief — freeze 生成・検証層の semantic membership

## scope

`orchestrator/campaign/s1_known_axes_freeze.py` の **trigger 述語面**に、
`campaign.trigger_gate_binding.is_canonical_predicate` による semantic membership 検査を入れる。
対象は 3 workload × {`system_gate.gate_predicate`, `ident_all.gate_predicate`} の 6 値。
main/remeasure 両 provenance が同じ非正準文へ連動 drift しても、非正準な known freeze を
**生成できず・検証を通せない**状態にする。

## 確定済みユーザー裁定 (覆さない)

- 2026-08-05 /rulings、[T-490] U-3 を推奨どおり採用 → [T-492] へ分離起票。択一 **(b)**。
- 正本 `output/insights/2026-08-05_t472-canonical-predicate-consumers.md` §7 U-3。
- 「次回 refreeze の前に実装する。今の凍結物は再発行しない」。

## 段 1 前提実測 (すべて本 wave で測った)

1. 現行凍結 6 述語はすべて正準かつ **exact** 一致 (strip 不要)。検査追加で現行 bytes の受理性は変わらない。
2. `s1_known_axes_freeze.py verify` は **HEAD で既に赤** — `s8a_trigger_sweep.py` の source sha256 不一致。
   本番経路は `s8b_oracle_driver._t080_adapter_refusals` (l.161-220) が T-080 receipt active 時に
   `static_gate_adapter` へ委譲し、legacy `verify` を**置換**する (l.406 の `if adapter_refusals is None`)。
3. generator を 1 行変異させて freeze 系 7 test file を実走 → **1 failed / 222 passed / 1 skipped**。
   赤は `test_s8b_oracle_driver.py::test_never_issued_generator_tamper_reaches_public_driver_gate_g7`
   ただ 1 本。known-axes leg の期待 refusal が `source sha256 不一致` から `generator sha256 不一致` へ
   変わるため。T-080 receipt gate (`_verify_metadata_closure` は H_mig blob と比較、
   `_without_generator_sha` は等値比較から除外) は**構造的に live generator drift を許容**する。
   → generator の編集は不可避 (検査呼び出しは同ファイルに要る) だが、防壁は壊れない。
4. 既存被覆は `test_reflux_ir.py` l.447-460 が凍結 6 述語を emitter 出力と exact 比較するのみ。
   これは **artifact-at-HEAD の pin** であって、producer の生成拒否でも verify 経路の拒否でもない。
   純増検出力 = (a) generate が非正準を bytes 化する前に止まる、(b) verify が任意 root/resolver で拒否する、
   (c) name→mask 表の仮定に依存しない。

## 不変条件

- 凍結成果物の bytes を 1 byte も変えない。再凍結しない (`output/s1-freeze/*.json`, `output/s8b-freeze/*.json`)。
- 現行 6 述語の受理性を変えない (正例で固定する)。
- 受理集合を拡大しない。`is_canonical_predicate` の strip 同値性 (T-490 U-1 で確定) をそのまま使い、
  新しい正規化・別の受理綴りを発明しない。
- 非正準なら `FreezeError` で fail-closed。診断文字列だけの差にしない。
- scope 外: `sort_best.comparator` の権威集合は [T-493] 所有。backoff 面も対象外。

## 成果物影響 (DW-G05)

実装しない場合、両 provenance の連動 drift で**非正準な known freeze 自体を生成でき**、
known / measurement / holdout freeze と材料 proof chain が無効になる。S-1 / S8b は判定不能、
校正 artifact は生成不能。誤 certification 自体は T-472 の sink gate が防ぐが、判定不能は残る。

## 親の provisional 裁定 (攻撃対象)

- **(P1)** 検査位置は `_trigger_entries` (l.493 `gate_predicate` / l.496 `ident_predicate` 取得直後) 1 箇所で
  生成・検証の両方を覆う (`verify_document` は `build_document` を呼び直すため)。
- **(P2)** それに加えて `verify_document` 側にも**読み込んだ doc 自体**への独立検査を置く。
  再構成等値で冗長になりうる一方、`verify_fn` 差し替え・部分 mock 経路では build 側検査が効かない。
- **(P3)** 実測 3 の赤 1 本は、期待値を緩めるのではなく `historical_bytes` で known_axes generator の
  recorded bytes を stub repo へ replay して**意図を保ったまま** live drift 非依存にする。

## 成果物の形

- production: `s1_known_axes_freeze.py` への検査追加 (最小)。
- test: 正例 (現行 6 述語が通る) + 負例 (非正準述語で generate/verify が `FreezeError`) + 実測 3 の 1 本の是正。
- docs は親が段 7 で spool fragment として書く。実装子は docs を触らない。

## 分割方針

編集面が `s1_known_axes_freeze.py` + その test に集中し、加えて `test_s8b_oracle_driver.py` 1 本。
所有が素集合にならないため **段 5 は単一 Codex 実装単位**とする (DW-S05-A の分割は不要)。
段 3 敵対と段 6 レビューは 2 本並列。本 wave は正しさ防壁に触るため DW-C00 の軽量版に該当しない。
