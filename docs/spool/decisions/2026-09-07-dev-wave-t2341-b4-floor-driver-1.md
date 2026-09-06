---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-09-07
wave: dev-wave-t2341-b4-floor-driver
seq: 1
---

## {{D:floor-pair-drop-and-count}}. 対照対 driver の欠測は標本ごとに落として数え、値を見て落とさない

**決定:** D1641 第 3 項の欠測規則を、対照対 driver へ次の形で実装する。

- 標本 = `(window_id, pair_id, sample_index)` の 3 role 組。1 role が droppable な非 complete
  (probe の competing / indeterminate、`measure_failed`、`measure_incomplete`) になったら、同じ標本の
  残り role を `not_run_sample_dropped` にし、次の標本は通常どおり実行する。
- **落とす判断は record の status だけから作り、throughput の値・D・median・順位を一切見ない。**
  finalizer は記録された status を payload から再導出して exact 一致を要求するので、status だけを
  書き換えた成果物は拒否される。
- 負値の throughput と reference の 0 は欠測ではなく protocol 不正として fatal にする。candidate の 0 は
  complete のまま保ち、gain = -1 として D に反映する。
- fatal (`binary_binding_failed` / `outside_window` / `protocol_violation`) は落とした標本に数えず、
  window 全体を止める。

**理由:**
- 規律 2。値を見て標本を落とせる経路は、そのまま「都合の悪い測定を捨てて床値を下げる」経路になる。
  status からの再導出を finalizer に置くことで、driver の外で status を書き換える偽装も塞がる。
- candidate の 0 を欠測にすると、性能が出ない候補ほど落ちやすくなり、床値が系統的に小さく歪む。
  0 は測定できた事実であって欠測ではない。
- reference の 0 は gain の分母が消えるので、落として先へ進めてよい種類の欠測ではない。

**却下した選択肢:**
- 非 complete を一律に欠測として落とす — 上の 2 つの歪みが入る。
- 値域検査を落とす判断へ組み込む (異常値を欠測とみなす) — 規律 2 に反する。
- median の有限性を完備性検査へ足す — rep が有限で median の式が overflow しなければ到達不能で、
  発火しない恒真な保証になる (規律 7)。式そのものを overflow しない形に変えた。

## {{D:floor-pair-campaign-threshold-locality}}. 5% の許容は campaign ごとに判定し、pair ごとの閾値は課さない

**決定:** 落とした標本の割合は campaign (= window、pair 合算) ごとに `dropped * 20 <= planned` で判定し、
exact 5% は受理する。1 campaign でも超えたら不採用。全 campaign が合格しても残存 0 の stratum が
あれば不採用。`(window, pair)` ごとの planned / dropped / retained は成果物へ**報告するだけ**で、
閾値は掛けない。

**理由:**
- D1641 の逐語は campaign 単位である。pair ごとの閾値は逐語より強い制約で、裁定なしに足せない。
- 一方、campaign 合算は pair 間の欠測の偏りを制限しない。件数を報告しておけば、偏りは事後に見える。
- 残存 0 の stratum は閉じた層の最大値を空列から取ることになるので、閾値とは別に塞ぐ必要がある。

**却下した選択肢:**
- `(window, pair)` にも同じ閾値を課す — 実装としては自然だが逐語を超える。ユーザー裁定へ返した。
- 全 window 合算で判定する — 片方の campaign が集中して壊れても通ってしまう。

## {{D:floor-pair-record-closure-is-part-of-status-rederivation}}. status の再導出には record と probe payload の閉包検査を含める

**決定:** finalizer が session record の status を payload から再導出するにあたり、record の field 集合の
exact 閉包、probe payload の形と型の整合、measured record の binary hash の再照合を、再導出の前提として
実装に含める。

**理由:**
- 「payload から status を再導出して exact 一致を要求する」は、payload の形が閉じていて初めて定義できる。
  未知 field を許すと、同じ status に見える別の payload を作れる。
- probe payload の整合検査 (status が competing なのに競合者が空、など) は、偽装の拒否そのものであって
  仮想リスクへの追加 gate ではない。

**却下した選択肢:**
- status に関係する field だけを見る — 何が「関係する」かを成果物の作り手が決められてしまう。
