# 設計メモ — 修理済み hold が黙って生き残ることを検出する機構

本 wave では **実装しない**。DW-G04 に従い設計メモに留める。
理由と、次に実装すべき条件を残す。

## 問題

`orchestrator/tests/flaky_test_holds.py` の hold は、対象テストが修理されても
自動では外れない。外すのは人間か AI の記憶に頼っている。

本 wave が現物で観測した実例。

| 時刻 (JST) | commit | 内容 |
|---|---|---|
| 2026-08-25 21:22 | `26d7f74b` | hold#1 登録 (別 wave) |
| 2026-08-26 05:26 | `9cd011fe` | hold#3 登録 (さらに別の wave) |
| 2026-08-26 09:17 | `639f2f28` | **hold#1 と hold#3 のテストを修理**したが、登録行は残した |

修理した wave (T-1719) は自分が登録した hold ではなかったため、
`flaky_test_holds.py` は編集面の外だった。結果、2 node が約 6 時間、
複数回の受入全走をまたいで検査集合の外に置かれ続けた。

**害の性質**: hold は opt-in の抜け道が無く、受入だけでなく焦点走でも常に skip される
(`conftest.py` の `pytest_collection_modifyitems` が無条件に `pytest.mark.skip` を付ける)。
登録された node は**どこでも走らない**。したがって取り残しは
「受理集合が黙って単調に縮む」形の劣化になる。DW-G03 の独立 2 例は満たしている。

## 本 wave で実装しなかった理由

3 行を撤去すると `_FLAKY_TEST_HOLD_ROWS` は空になる。
機構は**発火条件を満たす既存 artifact path も計測 ID も持たない**。
次に誰かが hold を登録するまで、1 度も走らないコードになる。

DW-G04 は「条件付き機能は、発火条件を満たす既存 artifact path か計測 ID を
brief に書ける場合だけ実装する。書けなければ設計メモに留める」と定めている。
本件はこれに該当する。

コスト見積り (段 2 プランの E 節による)。

- `flaky_test_holds.py` の validator に field 1 つと解決 helper
- `test_flaky_test_holds_contract.py` の約 8 箇所
- `docs/decisions.md` の D697 追補 (「受理条件は 6 つ」が不正確になる)

## 実装すべき条件

**次に hold を 1 行でも登録する wave が、登録と同じ commit でこの field を導入する。**
そのとき初めて、機構は実データで発火する。

## 設計 (段 2 プランの推奨を採る)

`FlakyTestHold` に `test_source_sha256: str` を足し、
import 時の validator が現在の source と照合する。

- digest は **raw 行範囲ではなく、decorator と関数本体の正規化 AST projection** から取る。
  `ast.dump(..., include_attributes=False)` 相当。先頭 docstring は除外。
  行番号・列・コメント・空白は digest に入れない。
- 理由: 本 wave が観測した修理 (`join(10)` → `join(60)`、
  `hookimpl(hookwrapper=True, tryfirst=True)` の追加、`yield` 前への記録移動) は
  すべて AST を変える。一方、整形・コメント・行移動では変わらない。
  raw 行範囲だと無関係な編集でも全 hold の再正当化を強制する。
- unreadable file、syntax error、対象なし、同 scope で複数候補、digest format 不正は
  `ValueError` にする。
- 登録者向けに `flaky_test_hold_source_sha256(node_id)` を公開する。
  ただし row には関数呼び出しでなく 64 hex literal を置く
  (呼び出しを置くと恒真になる)。
- helper / fixture の変更は追わない。transitive closure まで hash すると
  偽陽性と実装量が急増する。機構の scope は
  「held test 関数自身が編集された」に限定する。

## 既存 field との関係 (二重ではない)

- `green_observation` / `red_observation` / `green_run_count`: 登録時の履歴証拠
- `failure_signature`: `docs/failures.md` の F 節との結合
- `reintroduction_task_id`: 所有先
- `test_source_sha256`: **その証拠が対象にした test 実装と、現在の実装が同じか**

## 却下した代替

- **登録から N 日を summary に出す**: 修理直後でも期限前なら黙って残り、
  未修理でも期限で警告する。因果が弱い。
- **land 時に diff を調べる**: base range と merge topology に依存し、
  通常の collection では発火しない。
- **hold を定期的に実走する**: 現行の無条件 skip とは別の実行面と権限を新設する必要がある。

## 既知の残課題

`{{T:flaky-thread-join-upper-bound}}` は `docs/spool/FOLDED.md` の allocation に現れず、
T 番号が割り当てられないまま登録されていた。他の 2 件
(`t080-output-snapshot-shard-race` → [T-1773]、`flaky-xdist-hook-order` → [T-1803]) は
割り当て済みである。**`reintroduction_task_id` が実在の T を指すことを検査する仕組みも無い。**
上記の field を入れるときに併せて検討する。
