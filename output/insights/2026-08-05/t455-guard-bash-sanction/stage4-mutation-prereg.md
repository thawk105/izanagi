# 段 4 変異事前登録 (DW-M01) — [T-455]

本 wave は**受理集合を拡大**する (login で `tools/pegasus/fetch_third_party.py` の exact 綴りを通す)。
したがって kill 期待の主軸は「拡大が実際に効いているか」と「拡大が意図より広くないか」の 2 本である。

## M1-drop-fetch-sanction (単一理由)

- **位置:** `hooks/guard_bash.py` の `_SANCTIONED_PATHS` から追加行 1 本を削除する。
- **期待赤 node:**
  - `test_bash_login_allows_fetch_third_party_sanctioned_spellings`
  - `test_bash_login_fetch_third_party_entry_is_exact`
- **単一理由性の確認:** 同じ入力を拒否する層は前後に無い。削除すると `_is_sanctioned` が False を
  返し、`_heavy_segment_violation` の `target.startswith("tools/pegasus/")` 分岐で拒否へ落ちる。
  この経路を pin する既存テストは無く (既存 `test_bash_login_sanctioned_entries_are_exact` の
  リストに fetch は入っていない)、赤理由は「sanctioned から外れた」1 つに絞れる。
- **kill 意味論 (DW-M03):** 受理集合が拡大方向から縮小方向へ戻るので kill と数える。
  診断文字列だけの赤ではない。

## M2-glob-sanction-all-pegasus (冗長 gate と明記)

- **位置:** `_is_sanctioned` の frozenset 照合を `tools/pegasus/` 前置照合へ置換する
  (= 「pegasus 配下なら何でも login で通す」への退行)。
- **期待赤 node:**
  - `test_bash_login_fetch_third_party_does_not_sanction_siblings` (本 wave の新規 control)
  - `test_bash_login_sanctioned_entries_are_exact` (既存。`exec_calibrate.py` の拒否を pin)
- **単一理由性:** 満たさない。**冗長 gate である**と明記する。既存 control と新規 control が
  同じ退行を二重に捕まえるため、この変異は「新規テスト単独の検出力」の証拠には使わない
  (DW-M03 の「冗長 gate と明記して単独変異の証拠から外す」に従う)。登録する理由は、
  受理集合の過剰拡大を検出する層が実在することを本走で確認するためである。

## 走らせ方

- harness: `tools/mutation_harness.py` (DW-M05)。`--runner-mode dispatch`。
- runner argv: `python3 tools/run_tests.py orchestrator/tests/test_hooks.py -q -rf`
  (login では pytest が hook に拒否されるため、sanctioned な runner 経由で計算ノードへ dispatch する)。
- **既知の限界 (DW-M08):** dispatch 経路では harness の赤 node 抽出が `None` を返す
  (worklog (192) 段 8 の候補 (b) として既記録、未修正)。親が job stdout から F71 手順で抽出して
  期待 node と突き合わせる。
- 所要見積り: 変異 2 本 × (dispatch 往復 ~40s + pytest 2.3s) ≈ 2 分。外側の時間上限に掛からない。
- 本走は統合 commit 後に行う (DW-O19)。anchor (old 逐語) は最終 commit で再検証する (DW-M07)。
