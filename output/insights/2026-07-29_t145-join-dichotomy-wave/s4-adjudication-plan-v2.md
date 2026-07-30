# T-145 段 4 裁定・plan v2・mutation 事前登録

## 裁定

- plan v1 は NO-GO。correctness R1〜R5、concurrency R1〜R7 を real 採用する
- process-wide `select.select` patch、bool 群による観測、正常経路だけの cleanup、`None` だけを拒む
  timeout 判定、無条件の timeout 無し join は不採用
- active run / WAL が repository 内で `select.select` を直接使う攻撃、SignalRelay と listener が原理的に
  区別不能という攻撃、production seam 必須という攻撃は refuted
- production wakeup channel と subprocess 化は scope 外。任意の GIL starvation / no-select spin と
  正常 starvation の無時間識別は不可能で、T-145 の「既存固定 join の機能判定」を超える
- 成果物影響: plan v1 のままでは harness が production poll を救済し、停止退行を偽緑にするか、
  primary failure 後に thread / socket / patch を残して受入結果の第一失敗帰属を失う

## plan v2

1. 編集は `orchestrator/tests/test_dev_waves_integration.py` の long-path node と test-owned helper に限定し、
   production は 0 byteとする
2. 標準 `select` module の属性を変えず、`daemon_mod.select` の module binding だけを proxy へ差し替える。
   proxy は target serve thread と exact call shape だけを観測し、foreign call は保存した実関数へ委譲する
3. 状態は順序付き enum / trace とし、listener identity、exchange 完了、parked select、shutdown Event set、
   release、serve normal return / raise を別 event として記録する。直接観測していない predicate 再評価は
   主張しない
4. target select の timeout は現行 production contract `0.25` を引数値として構造 pin する。wall timeを
   合否に使わず、巨大な有限 timeout / `None` は専用 harness failure で即赤にする
5. exchange 完了後の次回 target select を park し、main が park を観測してから shutdown Event を set、
   release する。正常 loop は次の predicate で returnし、再び select したら専用
   `ServeLoopIgnoredShutdown` を投げて `_serve` が回収する
6. outer `try/finally` は primary error を保持しつつ、全出口で shutdown Event set、release、serve thread
   回収を行う。normal return と sentinel / 他例外を分け、patch は thread 回収後だけ復元する
7. daemon=True、serve exception 回収、long-path real exchange、capability skip、xdist marker、T-136 の
   request / state / reason / side-effect contract は維持する
8. test harness 自身の任意 hang は mutation subprocess の外部 ceiling で containment し、timeout を
   KILL / green に数えず `INFRA_TIMEOUT` とする。最終受入では対象 node、関連ファイル、repository 全走を
   通す

## mutation 事前登録

各変異は final bytes で old/new anchor が exact 1 件であることを実行直前に再確認する。対象 node が
capability skip の場合は KILL / SURVIVE に数えず `NOT_RUN` とし、wave を完了しない。

| ID | 独立変異 | 変更前期待 | 修正後期待 | 帰属 |
|---|---|---|---|---|
| M1 | request 処理後、loop 次反復前に正常 return | PASS | `PARK_NOT_REACHED` または順序 trace 赤 | 純増: serve-forever 契約 |
| M2 | `while not self._shutdown.is_set()` → `while True` | 120 秒後 thread-alive 赤 | 専用 sentinel 赤 | 診断・遅延改善 |
| M3 | `shutdown()` の `_shutdown.set()` だけを除去 | 120 秒後 thread-alive 赤 | Event-not-set を第一失敗にして赤 | 診断・遅延改善 |
| M4 | target `select` timeout `0.25` → `3600.0` | 外部 ceiling または 120 秒後赤 | timeout-contract 専用赤 | 巨大有限 poll 保存 |
| M5 | test fixture の `daemon=True` → `daemon=False` | PASS | daemon invariant 赤 | T-137 preservation |
| M6 | proxy の target-thread guard を無効化し foreign call も観測 | PASS または非決定 | isolation control の専用赤 | harness 隔離 |
| M7 | park 後の main 経路へ primary assertion failure を注入 | cleanup 不在 | primary error を維持し thread / patch / socket 回収 | harness cleanup |

- M1/M5/M6/M7 はテスト強化の新旧両走を必須とする。M2〜M4 は新旧の failure node、第一失敗、
  timeout有無を比較し、旧版の timeout を KILL と数えない
- M1 の受理条件は `serve_forever` が shutdown まで複数 iteration を維持する現行 loop 契約であり、
  一要求後の正常 return を受理しない。public request / state / reason の受理集合は変えない
- T-136 preservation は既存 PM1〜PM4 の同一 state / reason node を対象受入で再走し、T-145 の純増検出に
  数えない
- mutation harness は tracked file の exact 復元、単一置換、各 subprocess の ceiling、FAILED node /
  error / skip / timeout の正規化結果を記録する

## 段 5 の所有

- author 1名が test code と focused test だけを編集する。docs / wave artifact / commit は触らない
- manager は author patch を監査・統合し、mutation harness、全受入、docs 記録、commit を担う
