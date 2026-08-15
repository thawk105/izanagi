# [T-1109] / [T-1110] / [T-1111] — 変異台帳と erratum

wave branch = `worktree-dev-wave-t1109-admission-grammar`。
変異本走は `tools/mutation_harness.py`、`--runner-mode dispatch`、runner argv に
`--force-dispatch` と `-rf` を含む (`DW-M07` / `DW-M08`)。

## 走行の履歴

本走は 3 回行った。**権威は第 3 走** (`mutation-ledger.json` はその成果物)。

| 走 | 目的 | commit | 結果 |
|---|---|---|---|
| 第 1 走 | probe (期待 node の導出) | `2e095cba` | 8 件とも検出。うち 4 件が MISMATCH (期待 node が過小) |
| 第 2 走 | 実測 node で再登録 | `2e095cba` | baseline PASSED、8/8 KILLED、期待と完全一致 |
| 第 3 走 | **最終 commit での本走** (`DW-M07`) | `d5a441b6` (main 33 commit 取り込み後) | baseline PASSED、8/8 KILLED、期待と完全一致 |

第 3 走を行った理由は、`DW-M07` が「fix 後の**最終 commit**で anchor と期待 node を再検証してから
本走する」と定めるためである。第 2 走の後に local main を取り込み、
`autonomous_trial_completeness.py` を含む実装面 5 file が結合された
(main 側は layer3 比較と `campaign_verifier_epoch`、本 wave 側は admission 失敗経路で、領域は独立)。
取り込みでテストが 3 件増えた (焦点 813 → 816) ため、期待 node 集合が変わりうる。
**8 anchor はすべて最終 commit でも一意に成立し、期待 node 集合も変化しなかった。**

## 結果 (権威走行 = 第 3 走)

- baseline: **PASSED** (rc=0)
- 変異 **8 件すべて KILLED、期待 node 完全集合と完全一致** (`matches_expectation` = true)
- harness rc = 0

| 変異 | 狙う first-failure gate | 失敗 node 数 |
|---|---|---|
| V1-grammar-revert | `is_valid_pbs_jobid` の fullmatch (実機値の再拒否) | 2 |
| V2-grammar-overwide | 同 fullmatch の過剰受理 (`1:` / `00:`) | 2 |
| V3-events-drop-error | `_check_closed_events` | 17 |
| V4-first-run-event-revert | `_check_run_envelope` | 6 |
| V5-terminal-drop-error | `_check_terminal_projection` | 6 |
| V6-coverage-drop-error | `_check_workload_coverage` | 3 |
| V7-allow-forged-receipt | `_check_transport_admission` の receipt 禁止 (新設 branch) | 3 |
| V8-site-classifier-to-other | site 分類の独立 pin | 2 |

正例変異 (受理集合の過剰拒否・過剰受理の検出) は V1 と V2 が担う。

## erratum — 第 1 走は probe である (`DW-M08`)

第 1 走 (`mutation-spec.json` の前身、sha256
`24225b7a1844e14defef8e109b172adc29af88bea51ca735cf53e0f4d70a36a6`) では
V3〜V6 の 4 件が **MISMATCH** になった。**変異は 8 件とも検出されており (rc=1)、
検出力の不足ではない。** 親が登録した期待 node 集合が過小だった。

| 変異 | 登録した件数 | 実測件数 |
|---|---|---|
| V3-events-drop-error | 2 | 17 |
| V4-first-run-event-revert | 2 | 6 |
| V5-terminal-drop-error | 2 | 6 |
| V6-coverage-drop-error | 2 | 3 |

原因は「**新設 gate が発火すると後段の検査が走らず、診断がまとめて置き換わる**」型である。
たとえば V3 は `_EVENTS` から 1 語を落とすだけだが、`_check_closed_events` が
error 形の journal を一律に落とすため、error outcome を扱う変異 matrix 14 case と
正例 2 件がすべて同じ gate で落ちる。親は「新設した検査を直接撃つ 2 件」だけを
数えていた。

第 1 走を probe と明記し、実測 node をそのまま完全集合として再登録して
第 2 走 (`mutation-spec.json`、sha256
`4baa6add59bce515fe7c87844ad9d637f363056d8025a72b7ba55afdeac4f4af`) を権威走行とした。
第 1 走の台帳は破棄していない (`mutation-ledger.json` は第 2 走のもの。
第 1 走の raw は wave job dir に保全)。

## 段 4 登録から訂正した 3 件 (段 6 敵対レビューの must-fix)

本走の前に、変異登録そのものの欠陥を 3 件直した。

1. **V3 / V5 の anchor 衝突** — `_EVENTS` と `_TERMINAL_EVENTS` は同じ literal
   `"transport-admission-error",` を持つため、裸の置換は 2 箇所に一致する。
   両方消えると V5 も `_check_closed_events` に preempt され、
   `_check_terminal_projection` の検出力を証明できない。
   frozenset 全体を含む**別々の一意 anchor** へ変更した。
2. **V7 の期待 nodeid が未確定** — 対象 parametrize に明示 `ids=` が無く、
   完全 nodeid が自動生成 ID に依存していた。段 6 fix で明示 `ids=` を付け、
   `--junitxml` の権威一覧から期待 node を採った。
3. **V8 が等価変異だった** — 当初の登録は「テスト側の独立 pin を production 定数参照へ
   置換する」もので、production が同じ文字列を持つためテストは緑のままになり、
   受理集合も変わらない。**テストを弱めるだけで必ず生存する変異**であり、
   本 wave が撃っている恒真ゲート型そのものだった。
   **production 側の compute 分類を `OTHER` へ倒す変異**へ再照準した。

## 実測環境

- 焦点走行 (fix 後): 計算ノード、7 test file、**813 passed / 9 skipped** (15.09s)
- 焦点走行 (main 取り込み後、権威): 同 7 file、**816 passed / 9 skipped** (42.85s)
- 変異本走: 同じ 7 file scope、baseline + 8 変異 = 9 走
- login node の bounded local は本 wave の走行中ずっと
  `bounded scope の memory.max / memory.oom.group を走行中に attest できない` を返し続けた
  (並行 wave の輻輳による環境障害。同一手順で直前に緑だった対象も同じ症状で落ちた)。
  他 wave と同じく `--force-dispatch` で計算ノードへ回して実走した。
