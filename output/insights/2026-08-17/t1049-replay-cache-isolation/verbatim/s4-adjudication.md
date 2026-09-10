# T-1049 段 4 裁定 (2026-08-17、現 main 699c9cae)

## 決定

**(a) 実装しない。T-1049 は前提解消済みとして完了へ送る。**

理由は 3 つで、いずれも独立に成立する。

1. 起票時の失敗機序は消えている。衝突源だった定数
   `terminal_operation_id="public-origin-terminal"` は 2026-08-15 の commit `89723b89` で
   `"public-origin-terminal-" + sha256(str(tmp_path))` へ変更済み
   (`orchestrator/tests/test_p3_autonomous_workload_trial.py:6494-6497`)。
   起票時は同 helper を使う 5 test が同一 ID を異なる payload で使っており、xdist の同一 worker に
   2 本以上載れば必ず衝突した。現在は tmp_path ごとに一意。
2. 現 HEAD に残る衝突は無い。親の実測 3 走 (下記) と、独立 2 レンズの静的 call closure が一致した。
3. 共通 fixture 案 (P1/P2) は正しさ不変条件を壊すことが判明した。族一般化の条件 (DW-G03) も満たさない。

## 所見の real / refuted と採否

| # | 出所 | 所見 | 判定 | 採否 |
|---|---|---|---|---|
| 1 | plan / lens A | 実行到達閉包は親の 6 file ではなく **4 file** (`test_reflux_formal_consumer.py`, `test_reflux_origin_client.py`, `test_p3_autonomous_workload_trial.py`, `test_reflux_originless_compatibility.py`) | real | 採用。brief を訂正する。親の 6 file は安全側の過大集合であり、実測はその上位集合で行ったので結論は変わらない |
| 2 | lens A | 「`pytest-randomly` 不在なので順序はファイル順で決定的」は **false**。`--dist loadgroup` の scope 並べ替えと完了時刻による work unit 配布で、worker 同居は非決定的 | real | 採用。親 brief の推論を訂正する。ただし現行 writer の ID (`typed-terminal` / `terminal-replay` / `P(tmp_path)`) が互いに異なるため、結論 (P0) は維持される |
| 3 | lens A | 共通 conftest の `.clear()` autouse fixture は、`test_pytest_failure_digest.py:953-964` の入れ子 `pytest.main` により**外側 test の途中で発火**し、不変条件「同一 test 内の replay 検出状態を途中で消さない」を破る | real | 採用。(b) を明確に不採用とする決定打 |
| 4 | lens A | 旧定数への巻戻し変異は、既存 test 2 本 (`:6561`, `:6720`) が同一 process に載れば既に殺す。pin assertion への**排他的帰属は不成立** (DW-M01 の単一理由性を満たさない) | real | 採用。(c) の pin は事前登録変異を作れないため、検出力を実証できない |
| 5 | lens B | (519) と (535) は同一事象であり独立 2 例ではない。広い「process-local test state 汚染」族の独立例としては **F306** がある | real | 採用。ただし formal replay cache 族としては 1 例のみ。DW-G03 により族一般化 (共通 fixture) は許さない |
| 6 | lens B | brief の成果物影響 2 行は DW-G05 として不十分。実際に変わるのは主に pytest の受入判定で、certified 選択・実運用 report・台帳は不変 | real | 採用。記録では lens B の書き直し行を使う |
| 7 | lens A | `--confcutdir` を suite root 下へ向けると共通 conftest を迂回でき、受入形判定もそれを許す (`tools/run_tests.py:85-93`) | real | 採用。ただし**新規起票しない** — `tools/hold_inventory.py:124-133` が `pytest-confcutdir-below-suite` を `known-unresolved-bypass` として既に登録し、`T-930` で追跡している (親が実測確認) |
| 8 | plan / lens A | `_ISSUED_RECEIPTS` は `operation_id` を鍵にせず receipt ごとの新規 `object()` を鍵にするため、test 間で照合衝突しない | real | 採用。残留は不要な object 保持だけで、隔離の理由にならない |
| 9 | lens A | production の replay 拒否を緩める変異は既存 `test_reflux_formal_consumer.py:743-767` が既に殺す | real | 採用。本 wave の成果物へ帰属させない |

## 不採用とした案

- **(b) 共通 conftest への autouse fixture**: 所見 3 (不変条件違反)、所見 5 (DW-G03 不成立)、
  および「今回の再発そのものを緑に隠す」ため不採用。
- **(c) 定数巻戻しを殺す pin assertion**: 所見 4 により事前登録変異を作れず、検出力を実証できない。
  DW-G05 の成果物影響も「将来の CI red 復活」までしか書けないため nit とする。
- **(d) writer closed-set の AST guard**: 今回の一度限りの静的監査を suite へ複製する過剰案。nit。

## scope 外 real 所見でユーザーへ返すもの

なし。所見 7 は既存追跡 (`T-930`) に収容済み、所見 3・4 は本裁定で消化した。
production 変更を要する所見も出なかった (規律 2 の裁定返しは不要)。

## 変異事前登録 (DW-M01)

**免除。** DW-S04 の「『実装しない』と裁定済みで実装差分ゼロの wave」に該当する。
受入全走は免除しない。

## 段の進み方

`4 → 7 → 8 → 9`。段 5・6 を飛ばす。
