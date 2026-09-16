---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-16
wave: dev-wave-t2650-masstree-config-h
seq: 2
---

## {{D:floor-gate-offline-supply}}. 床値 campaign の condition gate へ共有 prebuild の FetchContent 定義を搬送する

**決定:** 床値 campaign が `sort_best` を含む production 走行で 1 回だけ行う masstree prebuild の
入力 (`FETCHCONTENT_BASE_DIR` と 3 依存の staged source dir) から、既存生成器
`p3_s4_loop._condition_gate_offline_configure_args` で configure 引数を作り、
`_FloorOracleDependencyBinding` の内部搬送 field で持ち回して、`floor_prepare` から
**全 cell の** `prepare_cell(condition_configure_args=...)` へ渡す。
搬送 field は `cache_receipt()` / `private_dict()` と永続 receipt に入れない。
D424 が定めた sort 限定の **cell build への** base 注入は変更しない。

**理由:**

- masstree の `config.h` は `add_custom_command` の OUTPUT で build 時生成物である。
  condition gate は使い捨て build dir へ configure を掛けるだけで build しないため、
  prebuild 済みの source dir を指さない限り `#include <config.h>` が必ず解決できない。
  official 床値 3 走行が `supply-effectuation:preprocess-failed` で止まった実体はこれである。
- 同型の欠陥は段 4 loop 経路で解決済みで、生成器と pin test が既に存在する。
  新しい共通層を作らずに再利用できる。
- D424 が限定したのは cell build への注入であり、理由は非 sort cell の cache identity と
  binary 参照を job ごとに変えないことである。gate の使い捨て configure はその両方に触れない。
- 搬送 field を永続 receipt へ入れると保存 schema と cache identity が変わる。
  gate へ渡す値は build の同一性の一部ではないので、内部搬送に留める。

**却下した選択肢:**

- **gate 自身に masstree を build させる** — 新しい `cmake --build` 起動点が増え、
  materializer 登録簿と網羅 test に波及する。campaign 側に既存の prebuild 段があるのに
  二重化する理由がない。
- **非 sort 単独 campaign にも prebuild を新設する** — 本件の欠陥は「既にある prebuild の
  結果を渡していない」ことであり、prebuild の発火条件を広げることとは別の判断である。
  別途諮る。
- **先例の「offline token はちょうど 5 本」をそのまま転用する** — 5 本目は明示
  `dependency_prefix` を持つ regime の値である。床値は prefix を argv で渡さず
  job script が環境変数で供給するため、正しい配線を誤拒否する。

## {{D:floor-gate-supply-liveness-control}}. 供給修正の生死確認は実 compiler の正例・負例で取り、base と source を分離する

**決定:** condition gate への依存供給を直す変更は、配線の argv 一致 test だけを完了根拠にしない。
実 compiler・実 CMake の最小 project で、(a) header が実在する source dir を指すと supply arm が
green、(b) その SOURCE_DIR を落とす / header の無い dir へ向けると `preprocess-failed`、
(c) **configure 引数を 1 bit も変えずに header だけを置き直すと green へ戻る**、の 3 点を取る。
**base dir と source dir は必ず別 path に置く。**

**理由:**

- argv が一致することは、compiler がその header を実際に読めたことを何も示さない。
  配線 test は生成器と campaign 側が同じ入力から同じ関数で作った値を突き合わせるので、
  供給の実効性については恒真に近い。
- 負例が reason code と detail の部分一致だけを見ると、原因を特定できない。
  fixture 自身が owner TU へ入れる `#error` 等も同じ文字列条件を満たしうる。
  引数を固定したまま header の有無だけで判定が反転することを示して初めて単一理由になる。
- base と source を一致させると CMake の既定命名 `<BASE_DIR>/<name>-src` が複製を拾い、
  `FETCHCONTENT_SOURCE_DIR_*` を 1 本落としても configure が通る。D1920 が扱った罠と同型で、
  負例が baseline から恒真に緑になる。
- この対照は gflags / glog の実 build を要さない。既存の実 compiler fixture で足りる。

**却下した選択肢:**

- **既存の失敗実測を継承して生死確認済みとする** — 失敗の実測は修正後の成功を証明しない。
- **実機 campaign の再投入を完了条件にする** — 計測枠を要する別タスクであり、
  供給実装の受入を実機の空き待ちに束縛することになる。到達範囲を記録して分ける。
