# 段 4 裁定 — [T-2076] 設計 wave

親 = dev-wave manager。段 2 は省いた (新しい設計を書かないため起草対象が無い)。
段 3 は read-only の `stage=consult` を 2 レンズ並列で走らせた。
実装面の差分はゼロなので段 5・6 を飛ばし `4→7→8→9` とする (`DW-S04`)。
同じ規定により変異 matrix を免除する。受入全走は免除しない。

## 親が実走した検査 (裁定前)

- `python3 tools/check_wave_startup.py --mode fresh --forbid-worktree-handoff --external-handoff <path>` = rc=0
- `python3 tools/check_docs.py` = rc=0 (docs 是正の前後で 2 回)
- `python3 tools/check_codex_output.py <lens-a.md>` = rc=0、`<lens-b.md>` = rc=0
- `python3 tools/spool_fold.py --base-digest '[T-2076]'` / `'[T-1700]'` = 値を取得

## 所見の裁定

| # | 出所 | 所見 | 裁定 |
|---|---|---|---|
| A1 | レンズ A | [T-2145] が自ら must-fix と裁定した現役 runbook の旧保証記述が未着地 | **real・blocker・採用 (scope 内)** |
| A2 | レンズ A | 親が job dir へ置いた D1355 の「逐語」コピーが末尾の却下選択肢を欠く | **real・must-fix・採用** |
| A3 | レンズ A | `docs/phase3.md:317-324` も同型に旧「反例探索」記述のまま | **real・採用 (親が範囲を広げた)** |
| B1 | レンズ B | 同じ着地で終端した `[T-1700]` も active のまま残っている | **real・must-fix・採用 (scope 内)** |
| P1 | 親 | 「依頼の要件は landed main で満たされ、新しい設計文書は不要」 | **後半は維持、前半は A1 により修正** |
| P2 | 親 | 「残件は `[T-2076]` の carry 是正だけ」 | **崩れた。`[T-1700]` と現役 docs 2 箇所を足す** |

refuted は無い。両レンズとも「新しい独立した設計文書をもう一本作る必要はない」で一致した。

## A1 の裁定 (blocker) — 親が現物で確認した

`output/insights/2026-09-02_t2145-sort-oracle-ir/s6-review-adjudication.md:49-55` は F4 を
「現役 docstring が旧『動的反例 gate』を名乗る」として real・must-fix と裁定し、
`p3_s4_loop_sort.py:47` と `s6_sort_sweep.py:28` を fix 子へ、
`docs/phase3-s5-sort-runbook.md:190` を **親が段 7 で書く**分として分割した。
親が現行 main を読むと、**fix 子担当の 2 docstring は正しい新保証で着地している**のに、
**親担当の runbook だけが旧記述のまま**である。落としたのは docs 側だけである。

放置すると、現役 runbook が新しい IR 実験を旧 raw C++ 実験の proof chain で説明する。
これは依頼が名指しで避けよと言った「実験同一性の主張の混同」そのものなので、本 wave の
scope 内と裁定する。docs-only であり、凍結境界により親が直接書いてよい。

**是正の内容 (landed code に合わせる):** 受理は閉じた 79 値 IR の正準 token 列との完全一致だけ。
IR が確定した経路では compile / run / timeout / 非決定性 / 実 TU 不一致を候補 finding にせず
`UNAVAILABLE` へ帰属させる。`PASS` へ倒す経路は作らない (規律 2)。保証の種類は
「動的な反例探索」ではなく「構成的 SWO + 実 TU conformance」である。

## A3 の裁定 (親が範囲を広げた)

`docs/phase3.md:317-324` は F4 の分割に名指しされていない。親が同型欠陥として自ら採用した。
2 行の局所修正で、同じ 1 文の言い直しである。新しい gate・検査・台帳・一般化は足していない。

## B1 の裁定

`[T-1700]` の実体 (entry 956) は「現行の非保証の明示を維持し、候補を副作用のない検証済み
中間形式へ制限する案は別の変更単位として比較裁定へ回す (D902)」である。
その比較裁定が D1355、実装が [T-2145] であり、いずれも着地済みなので終端している。
放置の危険は carry の古さだけではない — 文面は「非保証の明示を**維持**する」なので、
このまま拾われると landed main が既に閉じた非保証を復活させる向きに働く。

## scope 外として報告に留めた事項

- **完了で閉じた項目の親担当 must-fix が落ちた**という失敗型そのもの。段 8 で routing を裁定する。
- D344 の実験同一性の論点の再裁定。ユーザー裁定の領域であり、本 wave は触れない。
- `[T-2237]` (IR 文法版を build cache key へ一般化するか) は別の裁定事項で、`[T-2076]` の残件ではない
  (レンズ B が確認、`docs/archive/worklog-phase3-0902-1214.md:488-493`)。

## 成果物

- `docs/phase3-s5-sort-runbook.md` の限界節 1 項目を是正 (親)。
- `docs/phase3.md` の残課題 (c) を是正 (親)。
- `docs/spool/worklog/` に fragment 1 本。`完了` 節で `[T-2076]` と `[T-1700]` を
  `remaining: none` 付きで閉じる。
- 本 insight (逐語 2 本、brief、本裁定)。

実装面 (コード・テスト・probe・harness・機械設定) の差分はゼロである。
