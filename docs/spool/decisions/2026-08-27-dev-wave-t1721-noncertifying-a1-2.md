---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-27
wave: dev-wave-t1721-noncertifying-a1
seq: 2
---

## {{D:noncertifying-type-blocked-by-lock-only-gate}}. 非認証成果物型は lock-only certified gate を閉じられない限り作らない

**決定:** 認証権限を持たない成果物型は、**campaign lock だけで certified epoch を決める経路
(lock-only gate) を閉じられるようになるまで作らない**。宣言を campaign 同一性へ入れる形だけでは
足りない。D1038 が定めた「4 層で固定できないなら作らない」の発火であり、D1028 の不採用ではない。

**理由:**
- 内側で非認証と明記した identity を、公開情報だけで組んだ v2 authority で包み直すと、
  certified 受入の gate を E1 で通ることを実測した。親と独立 context の子が同じ epoch 値を得た。
- lock 側の identity 検査は exact 5 key と型しか見ず、宣言 field を 1 度も読まない。
  lock-only の epoch gate は批准台帳を 1 度も参照せず、記録 map と現在 map の equality だけを見る。
- v2 authority の材料 (closure map、activation state、環境契約 hash) はすべて公開で、
  非認証 run に固有の秘密も発行 capability も要らない。
- 部分的に他層だけへ拒否を入れると、lock-only 経路が開いたまま「閉じた型がある」という表示だけが
  立ち、現状より危険になる。

**却下した選択肢:**
- 宣言を campaign 同一性へ入れるだけで足りるとする — 包み直しを防げない。必要条件でしかない。
- full admission 経路だけ閉じて部分実装する — 恒真な保証を新設することになる。
- 投入器だけ先に作る — D1028 が名指しで却下している。

## {{D:noncertifying-type-waits-for-ratification-broker-landing}}. 所有解除の順序待ちは D1028 が却下した着地待ちに当たらない

**決定:** 非認証成果物型を閉じられる 2 file が稼働中 wave の所有下にある間は着手せず、
**その wave の land 後に、型から最終 reader までを 1 land 単位で再設計する**。

**理由:**
- D1028 が却下したのは「執行主体設計の着地を解決策として待つだけ」であり、停止期間が設計期間と
  同じだけ伸びることが理由だった。本件は稼働 wave の受入と land を待つ順序制約で、
  時間の桁が違う。
- 「作らない」で確定させるのは早い。わかったのは編集禁止面を触らずには不可能ということであって、
  原理的に不可能だという証拠は無い。

**却下した選択肢:**
- 型を作らないで確定させる — 所有解除後も不可能だという証拠が無い。
- 今できる部分だけ進める — 投入器のみは D1028 違反、型の一部のみは D1038 の条件未達、
  凍結 provenance の先行更新は最終 hash 未確定で不可。

## {{D:noncertifying-scope-is-one-land-unit-through-final-reader}}. 非認証型の変更単位は型から最終 reader と provenance までを含む

**決定:** 再開 wave は、型・A-1 config への結線・投入器・新 terminal への collector 対応・
completion receipt の producer・materialize の起動手・限定付き観測の reader・
波及する凍結 provenance の再生成を、**分割せず 1 land 単位**にする。

**理由:**
- 型と投入器だけを作っても A-1 の有効な成果物まで経路が通らない。集計器は終端 stage を
  固定しており、completion receipt の producer は repo 内に 1 件も無く、materialize の呼び手も無い。
- 分割すると先行単位のあとに休眠 capability が残り、D1028 が却下した型をそのまま再生産する。

**却下した選択肢:**
- 型を先に land し投入器を後続 wave にする — 型だけでは production consumer がゼロになる。
