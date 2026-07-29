# T-145 段 6 初回 review 裁定

## 裁定

- correctness B1 / concurrency 1: real blocker。proxy sentinel 前、outcome 通知後の無期限停止を現在の
  pytest process が containment できない
- correctness MF1: real must-fix。`daemon=True` の構造 assert がなく事前登録 M5 が生存する
- correctness MF2: real must-fix。reader 2 個の役割を型・identity に束縛せず duplicate listener が通る。
  tuple 等の意味等価 shape は過剰拒否する
- correctness MF3: real must-fix。exact `0.25` は functional kill でなく diagnostic pin。
  正の有限短縮を許し、長大有限値 / None を拒む意味契約へ縮める
- concurrency 3 / 4: real must-fix。cleanup が primary exception の args を変え、patch / thread ownership の
  開始・終了が一つの finally に閉じていない
- process-global binding、trace dedup、relay fd再利用、xdist marker射程、shadow contract、差分規模は
  real nit。repository 内の現 consumerでは即時成果物影響を示さないため、fixで増幅しない
- target thread identity、Condition/Event lost wakeup、lock inversion、現 happy-path trace、
  capability skip の正直な報告は refuted / closed

成果物影響: blocker を放置すると mutation / 受入の FAILED node と台帳が生成されず、cleanup 欠落を
放置すると後続 node の第一失敗が汚染され、T-145 の受入結果を認証できない。

## 単一 fix にする理由

全 real 所見は同じ test node の proxy state、thread lifecycle、process containment、cleanup ownershipに
相互依存する。ファイル所有を分けると同一制御フローを競合編集するため、段5 author worktreeの単一
workspace-write fixへ戻す。

## fix 要件

1. 実 serve harness 全体を kill/reap 可能な child process に置き、親 node が finite ceilingで containment
   する。ceiling到達は KILL / greenでなく専用 `INFRA_TIMEOUT` failureとする
2. child の assertion / traceback / skip を親へ構造化して返し、capability skip を NOT_RUN のまま保つ
3. proxy側は `daemon is True` を start 前にassertし、reader rolesを socket listener + int relayとして
   区別し、duplicate listenerを拒否する
4. timeout は `0 < timeout <= 0.25` の意味契約にして短い有限値を許し、None / bool / 非有限 / 長大値を
   拒否する。M4は diagnostic sensitivity pinとして記録する
5. patch ownershipを context/finallyの一範囲に閉じる。primary exceptionは型・argsを変更せず、cleanup
   errorはprimaryがない場合だけ独立failにする。`KeyboardInterrupt` / `SystemExit`を AssertionErrorへ
   変換しない
6. child timeout / abnormal exit時は terminate → bounded wait → kill → reapまで親が行い、child processを
   残さない。最終diffを必要最小限へ縮める
7. production、T-136/T-138、docs、output、commitはno-touch。focused nodeとisolation meta-testを再走する
