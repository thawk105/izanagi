---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-17
wave: dev-wave-t1293-official-perf
seq: 2
---

## {{D:degraded-is-a-stricter-branch}}. degraded 測定の受理は「緩い分岐」ではなく「別の厳しい分岐」にする

**決定:** official が perf 不在の測定を受理するとき、degraded 分岐の受理条件は perf 有り分岐と
非可換な、より厳しい条件の全称とする。canonical `unavailable` receipt であること、
`counter_status == "not_required"` かつ `missing_leading_indicators == []`、
**同じ成果物の measurement argv に perf prefix が無いこと**、
**同じ成果物の perf 由来 raw 値 (IPC・LLC miss rate・raw counter) がすべて null であること**、
exact な `claim_scope` を持つこと。1 つでも欠ければ degraded 分岐からも拒否する。
perf 有り分岐の受理条件は 1 文字も変えない。

**理由:**
- 正式系列が perf 不在で進むという裁定を満たすには、`expected_use_perf=True` という
  外部定数の権威を捨てて条件を判定するしかない。素直に receipt から再導出するだけだと、
  perf 有りで counter が壊れた走を「no-perf だった」と申告して緩い分岐へ移せる。
  これは規律 2 が名指しする reward hacking の経路そのものである。
- 条件を「no-perf 走が構造的に生む形との内部整合」にすると、隠したい対象 (perf 有りで壊れた走)
  は perf prefix 付きの argv と部分的な非 null counter を必ず持つため、degraded 分岐でも弾かれる。
  受理集合の増分は「内部整合した no-perf 形の成果物」ちょうどになる。
- 独立 issuer binding (署名・attestation) の新設は、粗い provenance で足りるという既定方針と
  衝突する。判定の厳格化だけで同じ効果の相当部分が得られるなら、機構を増やさない方を採る。

**却下した選択肢:**
- receipt から `expected_use_perf` を再導出して緩い分岐へ入れるだけの案 — 偽造の利得が残る。
- degraded を evidence-only に落として floor の根拠にしない案 — refreeze が進まなくなり、
  正式系列を perf 不在で走らせるという裁定の目的を達成しない。
- 署名付き実行 transcript の新設 — 費用が大きく、既定方針に反する。ただしこの決定は
  「成果物の外に権威が無い」限界を解消しない。外部アンカーの回復は別途ユーザー裁定へ返す。

## {{D:perf-availability-decided-after-path-setup}}. perf 有無の判定は候補解決を済ませた PATH の下で行う

**決定:** 計算ノード側で perf の有無を判定するときは、先に policy 候補の走査・smoke・
symlink・`PATH` 前置を済ませ、**その `PATH` の下で** canonical probe を 1 度だけ呼ぶ。
候補が 1 本も通らなかった時点では degrade を判定せず、probe の結果だけで分岐する。
判定の入口は `use_perf_from_receipt` 1 本のままとし、`command -v` / `which` / 環境変数を
新しい判定入口にしない。

**理由:**
- canonical probe は literal `perf` だけを probe し、policy 候補は evidence としてしか実行しない。
  したがって候補解決より先に probe を呼ぶと、「literal `perf` は PATH に無いが policy 候補は
  動く」という**今日 perf 有りとして受理されている入力**を no-perf へ付け替えてしまう。
  これは受理集合の付け替えであり、緩める向きでなくても不可である。
- 候補解決を先に済ませれば、候補が 1 本でも通ったときに symlink 経由で literal `perf` が
  存在するので、probe は available を返し、以後は従来と exact 同じ経路を通る。
  候補が全滅したときだけ probe が unavailable を返す。

**却下した選択肢:**
- probe を候補解決より前に呼ぶ案 — 上記のとおり受理集合を付け替える。
- 候補全滅を直接 degrade の根拠にする案 — 判定入口が 2 本になり、canonical receipt を
  経由しない迂回路ができる。

## {{D:runtime-measurement-sidecar-for-approved-manifests}}. 実行前に凍結される manifest へ実行時の測定条件を足さない

**決定:** 実行**前**に approved spec から作られる manifest (S8b oracle の
`8b-oracle-manifest/v1` 等) には、実行時にしか分からない測定条件を追加しない。
degrade したときだけ create-only の runtime sidecar を別ファイルとして書き、
campaign 開始記録にその file record を束縛する。全 campaign が perf 有りなら sidecar を
書かず、既存成果物の key 集合を exact に保つ。

**理由:**
- approved manifest は実行ノードの perf 有無が未知の時点で確定する。そこへ availability を
  足すと approved spec・manifest ID・perf 有りの bytes がすべて変わる。
- 測定条件は下流 (report・judge・verdict) が消費する必要があるが、その要求は
  「実行後に作られ、hash で manifest と束縛された別成果物」で満たせる。
- 条件付きで足す形にすれば、perf 有りの系列は 1 byte も動かない。

**却下した選択肢:**
- approved manifest schema へ optional field を足す案 — 実行前 manifest では値が決まらず、
  optional にすると「書かなくても通る」恒真 field になる。
- 測定条件を記録しない案 — 異条件混在のまま floor 判定・verdict・certified 選択へ流れる。
