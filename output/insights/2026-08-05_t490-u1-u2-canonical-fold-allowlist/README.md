# [T-490] U-1/U-2 — 正準 bytes への畳み込みと prepare_cell allowlist の fail-closed 化

ユーザー裁定 (worklog (211)、2026-08-05 /rulings) に従い、[T-472] の裁定パッケージ §7 の
U-1 を択一 (b)、U-2 を択一 (a) で実装した wave の記録。
裁定の正本は `output/insights/2026-08-05_t472-canonical-predicate-consumers.md` §7。

- 実装 anchor commit: `3ebdb382`
- 本 wave で U-3 ([T-492]) / U-4 ([T-493]) は実装していない。

## 1. 段 1 前提実測

裁定の前提をコードで測り直した。probe は wave job 配下 (repo 外) に置いた使い捨てで、
結論だけをここに残す。

| # | 測ったこと | 結果 |
|---|---|---|
| P-A | `emit_predicate` 32 本の strip 恒等性 | **32/32 恒等**。正準 bytes = strip 形と一致する |
| P-B | 未 strip 出力の `CANONICAL_PREDICATES` 所属 | 32/32 所属。digest 原文と membership 集合は現状一致 |
| P-C | 外周空白 7 種 (半角空白 / タブ / CRLF / `\x0b` / `\x0c` / NBSP / U+3000) | **すべて受理**、bytes は非同一 |
| P-D | 空白付き入力の sha256 | 正準 digest と不一致 |
| P-E | 実成果物の `configuration` 値 | **ちょうど 6 種**、裁定文と完全一致 |
| P-F | 凍結 cell の述語 bytes | `gate_predicate` は exact、**`sort_best.comparator` は外周空白付き** |
| P-G | 凍結 bytes の pin | `FROZEN_MANIFEST` が 23 artifact を sha256 で pin |

### 裁定時点で未見だった事実 (P-F)

`sort_best` の `comparator` は外周空白付きで、その空白は**現行の materialized bytes と
`src_token` に既に焼き込まれている**。裁定文の「現行 6 値は exact なので既存値は不変」は
`gate_predicate` については成立するが `comparator` には成立しない。
裁定 U-1 の対象は `is_canonical_predicate` 面 (trigger 述語) であり comparator を含まないため
裁定自体は覆らないが、**「comparator の bytes に触れない」を不変条件へ格上げ**して実装した。

段 3 レンズ A は、この件数を 3 freeze 横断で数え直し **16 gate (すべて exact) / 8 comparator
(すべて外周空白付き)** であることを示した。定性的結論は変わらないが、
`measurement_freeze` だけを見た親の件数は過剰一般化だった。

## 2. 実装 (anchor `3ebdb382`)

### U-1 — 正準 bytes への畳み込み

- `orchestrator/campaign/trigger_gate_binding.py`
  - `_build_canonical_predicate_index(emitted)` を追加。`strip 形 -> emitter 未 strip 出力` の
    dict を作り、**同じ strip key が重複したら import 時に `RuntimeError`** で倒す。
  - `CANONICAL_PREDICATES` はその key 集合の frozenset とし、**公開値と受理集合を変えない**。
  - `canonicalize_predicate(text) -> str` を新設。index の**値**を返す。
    非 `str` と正準集合外は既存 `_reject()` 経路で拒否する。
  - `is_canonical_predicate` と `expected_predicate_sha256` は変更しない。
- `orchestrator/campaign/p3_s4_loop.py`
  - `quarantine` の **`marker_id == TRIGGER_MARKER_ID` の membership 検査を通った直後、
    `render_hole` より前**で畳む。sort / backoff marker には適用しない。

畳み込み点を `quarantine` 1 箇所に置ける根拠は、**`render_hole` の本番呼び出しが
`p3_s4_loop.py` の 1 箇所だけ**で、S8a sweep・trigger loop・S-1 materializer・
extime calibration・autonomous trial preview がすべてそこへ合流するため (親が独立に確認)。

### U-2 — configuration allowlist の fail-closed 化

- `orchestrator/campaign/s1_direct_comparison.py`
  - module-private の固定 frozenset (6 構成) を追加し、`prepare_cell` の型検査直後・
    flags 解釈と checkout の前に未知値を既存 `DriverError` で拒否する。
  - `stock_common` / `p2_2_flag_opt` の分岐は追加せず、従来どおり flags-only を yield する。

**producer 定数 (`s1_measurement_freeze.CONFIGURATIONS` /
`s8b_holdout_freeze.VARIANT_NAMES`) を import して流用しない。** 流用すると将来の producer 拡張を
materializer が自動認可し、U-2 が狙った独立閉包を失う (段 2 プランの反論を採用)。
独立性は behavioral なテストで固定した (§4 の M06)。

## 3. 純増の根拠 (「上流が塞いでいるので無意味」ではない)

段 3 の両レンズが独立に refuted した。

- **U-1**: `quarantine` は strip membership を通した後、raw implementation を `render_hole` に渡す。
  さらに build admission の `pipeline._require_materialized_trigger_predicate` は
  hole を `.strip()` して比較するため、**外周空白を保持した source も admission を通過する**。
  つまり空白付き述語は「拒否されて止まる」のではなく「別 `src_token` の variant として通る」。
- **U-2**: 公式 S-1 は 18 セル exact schema、S8b は ratified freeze の再構成一致で閉じているが、
  `prepare_cell` の**直接 caller**にはその閉包がない。未知値は 4 分岐を抜けて
  `source_digest.resolve` と yield に到達する。

## 4. 変異検査 (事前登録 8 件、`tools/mutation_harness.py`、runner-mode=dispatch)

baseline **PASSED**。8 件すべて赤 (kill 成立)。台帳は `mutation-ledger.json`、
spec は `mutation-spec.json`。

| ID | 変異 | 結果 |
|---|---|---|
| M01 | `quarantine` の正準化代入を削除 | KILLED |
| M02 | marker guard を外し全 marker を正準化 | KILLED (node 集合 erratum、下記) |
| M03 | `canonicalize_predicate` を `return text.strip()` に変更 | KILLED |
| M04 | index builder が重複 key を黙って上書き | KILLED |
| M05 | allowlist の拒否を削除 | KILLED |
| M06 | allowlist を producer 定数から生成 | KILLED |
| M07 | 拒否を `configuration == "system-gate"` だけに縮小 | KILLED (node 集合 erratum、下記) |
| M08 | allowlist から `stock_common` を削除 (過剰拒否検出の正例) | KILLED |

### erratum — 事前登録 node 集合の誤り 2 件

harness は rc だけでなく赤くなった node 集合を突き合わせるため、
どちらも `MISMATCH` として記録されている。初回結果は消さずここに残す (`DW-M02`)。

- **M02**: 予測 1 node に対し実際は 19 node。予測した
  `test_sort_quarantine_preserves_outer_whitespace_bytes` は実際の集合に**含まれる**。
  trigger の正準化を全 marker へ広げると、sort だけでなく backoff の quarantine テスト群も
  巻き添えで落ちる。親の予測が過小だった。
- **M07**: 予測 5 node に対し実際 4 node。欠けたのは
  `test_prepare_rejects_multiple_unknown_configurations_before_checkout[system-gate]` で、
  これは `"system-gate"` だけを拒否する変異では**正しく緑のまま**である。
  **未知値を複数並べた parametrize 設計が効いていることの実証**であり、
  単一 literal の負例だけなら M07 は生存していた。

### collection 実在検査による fail-closed

初回投入時、期待 node を parametrize なしの名前で書いたため harness が
「期待 node が pytest collection に実在しない」で停止した。偽の SURVIVED / KILLED を
作らずに止まったので、node id を実採取して再投入した。

## 5. 段 6 の敵対レビューが見つけた唯一の blocker

レビュー 2 本が独立に同じ所見へ到達した。

**MF3a のテストが禁止変異 M06 を殺せない。** テストモジュールは冒頭で
`s1_direct_comparison` を import 済みであり、allowlist は module import 時に評価される。
そのため producer 定数を後から 7 値へ monkeypatch しても、変異実装は import 時点の
6 値を snapshot したままで、テストは緑のままだった。

対処は producer を 7 値にした**後で** consumer を別 module 名で**隔離 fresh import** し、
その fresh module の `prepare_cell` が 7 個目を checkout 前に拒否し続けることを固定する形。
変異走行で M06 が KILLED になり、この修正が実効的であることを実測で確認した。

## 6. 親が実測で見つけた契約違反

新テスト `test_real_source_digest_unifies_all_outer_whitespace_tokens` の `_require_g13()` が
`pytest.fail` を呼んでおり、`g++-13` の無い全ノードでスイートが赤くなった (199 passed / 1 failed)。
リポジトリの契約 (`orchestrator/tests/README.md`、先例 `test_campaign.py`) は
**C++ toolchain 不在は skip として数える**である。fix 子が skip へ是正し、
対象 3 ファイルは 200 passed / 1 skipped になった。

検出力は落ちない。identity の構造証明は「実 `quarantine` の `edited_text` / `working_diff` が
外周空白 7 種すべてで byte-exact に同一」が担い、`source_digest.resolve` を使う end-to-end 確認は
toolchain のある環境でだけ走る。

## 7. 受入

| 対象 | 結果 |
|---|---|
| 対象 3 ファイル (fix 前) | 199 passed / 1 failed (g++-13 契約違反) |
| 対象 3 ファイル (fix 後) | **200 passed / 1 skipped** |
| 凍結 (`test_frozen_artifacts` + `test_s1_measurement_freeze`) | **15 passed** |
| 変異 baseline | **PASSED** |
| **受入全走 (スイート全体)** | **6314 passed / 20 skipped / 0 failed** (765.30s) |

段 6 レビュー A は `FROZEN_MANIFEST` の 23 対象を独立に SHA-256 再計算し、23/23 が literal と
一致することを確認した (不変条件「凍結 bytes 不変」の裏取り)。

## 8. scope 外と裁定した real 所見 (裁定パッケージ)

いずれも real だが、**裁定されていない受理集合変更**または別 T の所有面のため実装しなかった。
詳細は `s4-ruling.md` の該当節。

- **SP1** — 既 materialize 済みの source 木を `loop.run_campaign` / `pipeline.evaluate` へ
  直接渡す経路には畳み込みが無い。`pipeline._require_materialized_trigger_predicate` は
  hole を `.strip()` 比較するため、外周空白を保持した source も build admission を通る。
  閉じるには admission 側の受理集合を変える (strip 比較 → exact 比較、または
  post-materialization assertion の新設) 必要がある。[T-492] の semantic membership と同じ面。
- **SP2** — `diffq_variant_id` は raw implementation を hash するため、trigger の
  post-membership reject では exact 形と空白付き形が別 reject variant として試行台帳に残る。
  WAL の reject key 導出を変える変更で、`load_diff_rejections` / critic 参照の consumer を持つ。
- **SP3 (nit)** — `configuration` に custom `__hash__` を持つ `str` subclass を渡すと、
  現行 flags-only から新たに拒否へ変わりうる。repo 内に該当 caller は無く、
  JSON 由来の値は常に plain `str`。

## 9. 保証の正しい名前 (段 3 レンズ B の指摘を採用)

この wave が統合するのは **successful materialized source・`src_token`・`pipeline.variant_id`**
だけである。raw provenance の hash — S-1 review receipt の `item.cell` hash、
S8b binding の `entry_sha256` / `binding_sha256`、reject の `diffq-*` — は**意図的に別のまま**であり、
「材料 proof chain 全体が統合される」という親 brief の当初の書き方は過大だった。

また U-1 は **end-to-end の受理集合を変える**。従来なら preprocess / build で落ちえた
NBSP や U+3000 付きの入力が、畳み込みによって compiler 到達前に正準 bytes へ解決される。
これは裁定済み択一 (b) の当然の帰結であり、不変条件は
「`is_canonical_predicate` の membership 集合を変えない」に限定するのが正しい。
