# 裁定パッケージ — A-2 は関門を通ったが、その先の identity 判定と、既完走 4-cell の位置づけに裁定が要る

wave: `dev-wave-t2228-a2-gate-layers` / branch `worktree-dev-wave-t2228-a2-gate-layers`
authority: none / default_effect: no-state-change

## 何を頼まれ、どこまで済んだか

依頼は「A-2 経路で関門の 2 層目以降が一度も実行されていない件を直し、実体を名指しした正例・負例で発火を確かめ、
既完走 4-cell (reject) への影響を報告する」だった。

- 関門は T-2226 の着地で最後の赤が消え、attempt `t2228-20260904a` で両 workload とも 4 cell の admission と campaign まで発火した (README 1 節)。
- 実体を名指しした unit 正例・負例を driver に足した (README 4 節)。
- 既完走 4-cell への影響: **受ける** (README 3 節)。
- 関門の先で新しい層 (canonical variant 判定) が出た。受理集合に触るので独断で実装せず、ここで返す。

## 裁定してほしいこと 1 — adopted cell の canonical identity をどう束縛するか

**事実.** `_raw_cell_from_wal` (`paper_story_a2_certification.py:2810-2813`) は `variant_id(_genome_for_cell(policy, cell))`
= src_token `stock` を canonical とし、WAL の variant と一致しなければ `CertificationError` にする。1208 (2026-09-02) で
campaign が patch 済みの隔離木を build するようになった結果、adopted cell の src_token は patch 由来の digest
(`955b452a…`) になり、この判定は **patch が効いている場合に必ず赤**になる。逆に patch が効いていない木では `stock` になり
通る。つまり現行の判定は D1198 の型 (供給されず別条件を測る) を**通し、正しい測定を拒む**向きに倒れている。

**選択肢 (いずれも受理集合と proof 参照に触る).**

1. **canonical を「pin + patch」に束縛した src_token で計算する。** driver の関門文脈で `source_digest.resolve_evidence` を
   patch 済み隔離木に対して cell ごとに評価し、その `src_token` で `variant_id(genome, src_token)` を期待値にする。
   raw payload / certification に `src_token` を記録し、stock cell は `stock`、adopted cell は非 `stock` であることを
   fails-closed で要求する (adopted が `stock` なら patch 未適用として赤)。
   利点: 「patch が効いた木」だけを受理する向きで、D1198 と同じ側に倒れる。T-2022 型の再発を driver 自身が拒否する。
   代償: raw / report schema の追加 field と、`_raw_cell_from_wal` / materialize の契約変更。既存 attempt c の raw は
   `src_token` を持たないので、新 schema では「patch 未適用」として読まれる (規律 7: bytes は変えず、判定は追記)。
2. **WAL の build admission receipt の `src_token` をそのまま canonical に採る。** 実装は軽いが、driver が独立に
   期待値を持たない形になり、「WAL が言う通り」を受理する恒真な判定に近い。推奨しない。
3. **adopted cell だけ canonical 判定を外す。** 受理集合を広げる方向。推奨しない。

**親の推奨: 1.** 段 2 で Codex に file:line 起草させ、段 3 で正しさ境界のレンズを当てる。実装後に A-2 を取り直す
(新 attempt、2 workload × 約 1 時間)。取り直しは既存 attempt を触らない。

## 裁定してほしいこと 2 — 既完走 4-cell (T-2022 attempt `t2022-20260828c`) の位置づけ

**事実.** attempt c の adopted cell は patch 無しの木で build され (`src_token: stock`、driver は `patchharness` を呼ばず、
pipeline は patch を当てない契約)、`BACKOFF_FIXED` は CMake に無視されていた。測ったのは `BACK_OFF=1` (内蔵指数 backoff) vs
`BACK_OFF=0`。README 3 節の表。F707 の再発として failures へ記録する。

**選択肢.**

1. **追記で訂正する (規律 7)。** `output/insights/2026-08-28_t2022-a2-certification-run/README.md` と
   `output/insights/2026-08-24_paper-story-a2-certification/` に「測定条件の実体」節を追記し、reject が支持する命題を
   「内蔵指数 backoff 有効 vs 無効」に書き換える。certification.json の bytes は変えない。論文素材からは、
   正しい identity で取り直した attempt が出るまで A-2 の結論を外す。
2. **何もしない。** 現状の README は「adopted backoff fixed10 / fixed5 が stock を下回った」と読めるので、誤った命題が
   論文素材に残る。推奨しない。

**親の推奨: 1.** docs のみで、裁定 1 の実装とは独立に進められる。

## 裁定してほしいこと 3 (軽微) — receipts の campaign 前保存

driver が campaign 後に落ちると admission の canonical receipt が残らない (今回実測)。命令により本 wave では台帳を足していない。
裁定 1 の実装に同梱するか、要らないかを決めてほしい。親の推奨: 裁定 1 の wave で raw 化の前に受領証を書く (新 file 1 つ、
schema は record の canonical JSON をそのまま)。

## 裁定してほしいこと 4 (軽微、実装面) — 変異 harness の collection 段と provenance checker の queue 待ち

`tools/mutation_harness.py` の collection 段は `dispatch_compute.py` を直接呼び、queue 待ちが 900 秒固定で
D612 の opt-in 上書き (`IZANAGI_DISPATCH_*_OVERRIDE`) が届かない (runner 経由の本走には届く)。
`tools/check_ai_provenance.py` も同じ。gen_S が QUE 250〜300 の時間帯に collection が 3 回連続 rc=16 になり、
wave が約 8 時間止まった (2026-09-04 17:00〜01:30)。実装面の変更なので本 wave では触っていない。
親の推奨: harness と checker に同じ上書き env を読ませる (受理集合は変わらない、D612 の射程拡張)。
要らないなら「混雑時は待つ」を運用とする。

## 変わらないもの

- 関門本体 (`condition_meaning_gate.py`) の受理集合。本 wave の production 差分はゼロ。
- attempt c の bytes と、その当時の判定の記録。
