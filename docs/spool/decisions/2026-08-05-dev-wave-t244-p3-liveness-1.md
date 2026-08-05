---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-05
wave: dev-wave-t244-p3-liveness
seq: 1
---

## {{D:t244-p3-liveness-fixture-only}}. P3 の生死は fixture store 上でだけ取り、本番 authority へは 1 件も書かない

**決定:** D179 §8 が求めた生死確認を、一時 git repo の fixture store 上で成立させた。
実 E driver (`--preview-wire`) が出した wire と diff digest を載せた同一候補 R=2 の 1 batch が、
`BatchCommitted → BatchResultsPrepared → BatchSealed` の 3 event として受理され、
query counter が 0→2、iteration counter が 0→1 へ動き、seal 後に wire と evidence digest が
replicate 0/1 で復元された。負の control (2 member の candidate commitment を同一にした batch) は
`invalid batch candidate commitments` で拒否され counter は不変だった。

**本番 authority (`origins: []`) は変更しない。** 生死が取れたことは provisioning の解禁を意味しない。

**名乗りの上限:** 「一時 repo の fixture store 上で、実 driver が出した digest を evidence として
載せた single-candidate × R=2 の ledger transaction が受理され、counter が動き、seal で復元できた」
まで。P3 充足・部分 P3/P4・production provisioning・候補 batch・実 iteration の実行 outcome・
kill-before-commit 対策・科学的有効性は名乗らない。D114 の cap=1 と D166 の P4 FAIL は不変。

**理由:**
- 本番 authority へ entry を足すには 13 field manifest が要り、`budget_policy` (予算値) と
  evidence ref 2 本を含む。予算値は authority 発行の裁定として別途決まる予定で未確定である。
- ledger は evidence path を dereference せず、budget 値の意味も検査しない
  (`_authority_from_bytes` は構造・正準性・導出 hash だけを見る)。**適当な値でも機械的には通る。**
  したがってこれは機械の穴ではなく統治の穴であり、機械が止めてくれない以上、規律で止めるほかない。
- 生死確認に必要なのは受理・counter・seal の 3 点だけで、そのどれも本番 store を要求しない。

**却下した選択肢:**
- **wave branch に authority entry を commit して本番経路 (`commit_event`) で実験する。** 機械的には
  通るが、land した瞬間に未裁定の予算値で provisioning を解禁したことになる。D147 が止めた穴の再演。
- **独自の変異 harness を書く。** 使い捨ての最安確認に専用機構を作らないという原則に反する。

**残る限定 (実装しても閉じない残余とは別に、本 wave 固有):**
- probe の wire 正準性検査は ledger と同じ canonicalizer を再呼出しするため、その受理集合が
  誤って広がった場合は共動して緑のままになる。独立な IR canonicalizer は書いていない。
- fixture manifest は架空 hash と実在しない evidence ref を持ち、本番では成立しない値である。
- probe は preview JSON が実 driver の invocation 由来であることを証明しない。本 wave では
  親が実際に driver を走らせて生成したという手続き的事実で補っている。

## {{D:disposable-probe-mutation-wrapper}}. 使い捨て probe の生死主張は、probe を叩く最小 pytest node で裏取りする

**決定:** 使い捨て probe が「生死が取れた」と主張する wave では、probe を subprocess で起動して
rc と各判定を検査する最小の pytest node を 1 本作り、それを変異 harness の runner にする。
本 wave では ledger の 3 箇所 (重複 commitment の拒否・replicate ordinal の採番・
commitment 原像への wire 混入) を一時変異させ、3 件とも当該 node が赤くなることを実測した。

**理由:**
- 変異 harness は runner を pytest に束縛しており、pytest node でない probe は駆動できない。
- 「probe が緑だった」だけでは、probe が対象を実際に観測しているかは分からない。特に probe が
  対象の内部関数を使い回していると、対象を壊しても期待値が同じだけ動いて緑のままになる。
  commitment 原像から wire を落とす変異は、この共動が起きていれば検出できない。実測で赤に
  なったことが、独立実装が効いている機械的な証拠である。

**却下した選択肢:**
- **独自 harness を書く。** 固定 HEAD 束縛・復元照合・単一走行・resume・signal 復元を作り直す
  ことになり、使い捨て確認に不相応である。
- **既存の対象側テストで変異を裏取りする。** それは既存テストの検出力を測るだけで、
  本 wave が作った probe が恒真かどうかには答えない。

**一般化の射程:** 独立 2 例が揃っていないため族全体への制度化はしない。本 wave の方法として記録する。
