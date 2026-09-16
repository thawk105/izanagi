# 段 4 裁定 と plan v2 — dev-wave t2117

親が段 3 の 2 レンズを裁定した。blocker は無い。plan を採用し、追補 3 点を加えて plan v2 とする。

## 所見の裁定

| # | 所見 | real/refuted | 採否 | scope |
|---|---|---|---|---|
| A-1 | 負例が比較前の別エラーで止まる穴 | refuted (静的読解で到達を確認) | 予防として追補 1 を採用 | 内 |
| A-2 | 正例は比較恒真化を検出しない (負例だけが検出する) | real | 変異登録で期待 node を分離 | 内 |
| A-3 | 新 2 本は `verify_source_sha` の拒否能力を証明しない | real | 不採用 | **外** |
| A-4 | commit 定数差替えで歴史 patch との統合保証を失う | real | 代償として受容・記録 | 内 |
| A-5 | 親 brief の P1-a / P1-c が一般化しすぎ | real | **採用 (追補 3)** | 内 |
| A-6 | 5 変異の帰属不成立 | refuted (既存 test は到達前に止まる) | — | 内 |
| B-1 | P1-c は一般化しすぎ (A-5 と同型) | real | 追補 3 に統合 | 内 |
| B-2 | route B の patch は generator。観測で消費すると空になる | real | **採用 (追補 2)** | 内 |
| B-3 | 裁定 (D1367 / D1382 / D1615 / [T-2117]) との衝突なし | refuted | — | 内 |
| B-4 | 登録簿・xdist・所要台帳による必然の赤は無い | refuted | — | 内 |
| B-5 | helper は実在し auxiliary 差替えも可能 | refuted | — | 内 |
| B-6 | 要求外の新設なし・撤去残りは D1615 の維持対象 | refuted | — | 内 |

**A-3 を不採用にした理由.** 本 wave の scope は「復元不能な当時の bytes 一致の撤去と恒久解」。
`verify_source_sha` の拒否能力は撤去によって新たに生じた穴ではなく、既存の被覆限界である。
DW-G05 により、放置しても成果物の値・受理集合・参照は変わらない。裁定パッケージ候補に残す。

## plan v2 — 追補

**追補 1 (A-1 の予防).** 負例の fix1 patch は、**除去側の `-authored` を維持し、追加側だけを
`+golden-mismatch` に変える**。除去側を変えると patch context 不一致で
`_compare_golden_routes` へ到達する前に別の `ValidationError` が出る。
負例は `caught.value.reasons` を完全一致で固定し、到達前の失敗を mismatch 検出と
取り違えないようにする。

**追補 2 (B-2 の罠回避).** `_apply_patch_set_independent` へ渡るのは list ではなく
generator である (`tools/codex_reasoning_ab.py:965-976`)。観測 wrapper で
`recorded = list(patches)` としたら、**その `recorded` を実関数へ渡す**こと。
`patches` をそのまま渡すと既に消費済みで空になり、route B が `base` のままになって
正例が偽の mismatch で落ちる。

**追補 3 (A-5 / B-1 の限定).** 親 brief の 2 つの前提を次へ限定する。
- (P1-a) → 「`_require_pinned_rollouts` を経由して沈黙している node は 1 件だけ」。
  別 guard・別条件分岐による沈黙を排除したとは主張しない。
- (P1-c) → 「**function scope の `tmp_path` / `monkeypatch` だけを使い、
  `benchmark_snapshots` を含むどの session/module scope 共有 fixture も使わない**
  今回の構成に限り、登録簿の更新は要らない」。
  `benchmark_snapshots` を使わなければ常に登録不要、とは一般化しない。
  根拠: `orchestrator/tests/test_real_repo_serialization.py:1432-1471` の consumer 閉包は
  登録済み node を seed とし、他の共有 fixture も対象に含む。

## 採る形 (確定)

1. `test_m2_production_golden_requires_both_routes` は**関数を残す**。
   `TOOL._sessions_default()` と `_require_pinned_rollouts` の呼び出し、および
   歴史 SHA `bc3f5f95...` の assert を撤去する。
2. 合成入力で `derive_independent_golden` を最後まで走らせる正例へ改修する。
3. 隣に mismatch 負例 `test_m2_production_golden_rejects_route_mismatch` を新設する。
4. `tools/codex_reasoning_ab.py` は 1 byte も変えない。
5. 登録簿 (`conftest.py` / `test_real_repo_serialization.py`) は変えない。

## 変異事前登録 (DW-M01 / DW-M08)

本 wave は **production 差分ゼロのテスト強化 wave**である。よって DW-M08 に従い、
**新テストと変更前 HEAD 版テストの双方へ同じ変異を走らせ、新テストだけが検出する差分を示す。**

変異対象はすべて `tools/codex_reasoning_ab.py`。node 名はすべて
`orchestrator/tests/test_codex_reasoning_ab.py::` 配下。

| ID | 変異 | 新テストでの期待 node (完全集合) | 変更前 HEAD 版での期待 |
|---|---|---|---|
| M1 | `_compare_golden_routes` (`:912-922`) の比較を外し `return dict(route_a)` | `test_m2_production_golden_rejects_route_mismatch` のみ | 0 件 (m2 は skip) |
| M2 | `derive_independent_golden` 末尾 (`:978`) を `return route_a` にする | 正例 + 負例 の 2 件 | 0 件 |
| M3 | route A の `reverse=True` を `False` にする (`:960` 付近) | 正例 + 負例 の 2 件 | 0 件 |
| M4 | route B の patch 順序を author→fix1 から fix1→author へ反転 (`:969` 付近) | 正例 + 負例 の 2 件 | 0 件 |
| M5 | route B の `_apply_patch_set_independent` を `_apply_patch_set` に置換 (`:965` 付近) | 正例 + 負例 の 2 件 | 0 件 |

**単一理由性の確認は実装後に行う** (DW-M01)。期待 node が確定できない変異は登録から外し、
probe と明記して erratum を残す。

**M1 と M2 の区別が本 wave の要点である** (A-2)。M1 は比較関数の内部を恒真化する変異で、
正例は通ったままになる。M2 は比較の呼び出し自体を省く変異で、正例の到達 assert も落ちる。
この 2 つを同じ検出実績として数えない。
