---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-29
wave: worktree-dev-wave-t1933-wall-unit
seq: 2
---

## {{D:acceptance-wall-frontier}}. 受入 wall の律速は単一 unit ではなく 10〜11 unit の frontier とする

**決定:** hold 有効の現行 tip では、受入 wall を決めている単体処理は存在しないと確定する。
単一 node または単一 loadgroup を短くする提案は、その 1 本が critical shard の unit 所要分布の
上位群を単独で抜いていることを示さない限り採らない。短縮案は上位群 (97 秒以上の 10〜11 unit) の
全体へ同時に効く形で提案する。判断に使う量は `makespan >= 最長 unit の所要` という定理であり、
scheduler の挙動の模型ではない。

**理由:**
- hold 有効の 4 走 (同一 tip 2 組、tested_main `93fcb4663` と `c9f868ba`) で、critical shard の
  最長 unit を無料にしても makespan は次の unit を下回れず、その差は 2.7〜19.3 秒だった。
- 同じ 4 走で 97 秒以上の unit が 10 / 10 / 10 / 11 本、77 秒以上が 11 / 12 / 20 / 22 本ある。
  makespan を 97 秒未満にするには 10〜11 本を同時に短くする必要がある。
- D1260 の paired K=3 で +0.37% にとどまった理由はこの frontier の幅である。6 node を寄せても
  97 秒以上の unit が他に 4〜5 本残る。局所の cache hit は critical path の下に隠れる。
- 上位群は 3 機構に分かれる。`test_s8c_preregistration_invariant.py` の module fixture、
  `test_s8c_preregistration_predicates.py` の C06 到達可能性探索、
  `test_s8b_oracle_driver.py` の T-080 stub-free e2e。
  最後のものは共有処理ではなく、同じコード経路を 10 本が独立に実行している。

**却下した選択肢:**
- LPT 詰め直しの差を実 scheduler の短縮量として使う — LPT は実 makespan の下界ではない。
- `wall − max_occ` を「テストを走らせていない時間」として使う — これは上界であり、
  worker の idle、real-repo lock 待ち、scheduler、session suffix が混入する。
- 単一の最長 node を短くする — 次の unit が同じ位置を占めるので makespan は動かない。

## {{D:acceptance-wall-claims-need-hold-state}}. 受入 wall の主張には hold の opt-in 状態を明示する

**決定:** 受入 wall の律速・改善・退行を述べるときは、tested tip、K、worker 数、collection digest に加えて
**growth hold の opt-in 状態**を明示する。走の同値性を語るときも同じ 5 つを揃える。
どちらの状態に対する主張かを書かない wall の記述は採らない。

**理由:**
- `orchestrator/tests/conftest.py` の環境変数で growth hold は解除でき、解除の有無で
  wall の律速機構が入れ替わる。2026-08-29 01:52 を境に、
  `s8c-preregistration-candidate` loadgroup (5 node の直列鎖) が makespan を単独で決める regime から、
  単一 unit が決めない regime へ実際に交代した。
- 交代前の 26 走ではこの group を無料にすると LPT makespan が中央値 57.9 秒縮んだ。
  交代後は最長 unit を無料にしても中央値 3.2 秒しか縮まない。
- hold 状態は現在どの同値キーにも入っておらず、collection digest にも入らない。
  同一 tip・同一 digest でも hold の有無で別の走になる。

**却下した選択肢:**
- 時刻だけで regime を判定する — 同時刻に別 tip の走が並ぶ。
- hold 解除状態を既定として測る — 現行既定は hold 有効であり、既定でない状態の値を
  既定の主張に使うことになる。
