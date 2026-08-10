---
schema: izanagi-spool-v1
ledger: decisions
authored: 2026-08-10
wave: dev-wave-t726-pickaxe-epoch
seq: 2
---

## {{D:ruleops-pickaxe-epoch-window}}. RuleOps の pickaxe は candidate epoch 窓に限り、窓は対象の最終変更を必ず含む

**決定:** `tools/ruleops.py` の pickaxe を全史 `git log -S` から `epoch..HEAD` の窓へ限定する。
`epoch` は candidate の required field (祖先 commit OID) で、ledger schema を
`ruleops-candidates/v2`、inspection schema を `ruleops-inspection/v2` へ上げる。
受理条件は 5 つで、いずれも満たさなければ括弧内の reason で fail-closed に拒否する。

1. 小文字 full OID (`bad-oid`)
2. local に実在し type が commit (`epoch-not-commit`)
3. 捕捉 HEAD の祖先 (`epoch-non-ancestor`)
4. 窓の commit 数が 1,000 以下 (`stale-epoch`)
5. **窓が candidate `path` の最終変更 commit を含む** (`epoch-after-target-change`)

窓外の reviewed pickaxe event は `pickaxe-event-outside-epoch` で拒否する (filter しない)。
`_compare_signals` の exact 集合一致は逐語不変で、変わるのは母集合だけである。
mutation receipt の `head` は `merge-base(epoch, receipt_head) == epoch` を要求する。
`inspect` は `--epoch` を受け、既定は「対象 path の最終変更 commit の第 1 親」を導出する。
`check` の成功出力へ candidate ごとの `epoch` と窓 commit 数を出し、監査地平を機械可読に宣言する。

**時限の失効条件を 2 段で機械化する。** カレンダー由来の猶予をやめ、走行のたびに機械が測る。

- modeled pin: `1,000 x 6 x 0.005 = 30.0 <= 45.0`、`20.0 + 1,000 x 0.035 = 55.0 < 60.0`、
  外側 preflight の 60 秒が単一 literal であることの `ast` 固定。
- 実測 guard: 最大 package の preflight を 45 秒 (外側 60 秒の 75%) で先に赤くする assertion。
  既存の 60 秒 assertion は逐語で残し、その手前に置く。

**この決定が保証しないこと**を明示する。epoch 以前は検証されないし申告も受理されない。窓は
対象の最終変更を含むが、それより前へ広げる保証はない。窓限定は pickaxe だけで、commit 数え上げと
control の path 限定 `log` は履歴長に比例したまま残る。

**理由:**
- 全史 pickaxe は約 14.6 ms/commit (実測 36.467 秒 / 2,502 commit / 6 token) で伸び、受入全走の
  最大 package preflight が外側 60 秒を決定論的に超える。**内部予算をいくら上げても直らない。**
  ユーザー裁定は履歴範囲の限定を選び、定数引き上げを不採用としている。
- 条件 5 が無いと `epoch` を捕捉 HEAD に置くだけで窓が空になり、computed も reviewed も空集合で
  exact 一致が自明に成立する。**証拠ゼロの package が構造検査を通る**。条件 5 は窓の下限を
  repo から導出した事実 (対象 path の最終変更位置) へ束縛し、宣言者が地平を任意に前進させるのを
  防ぐ。判定は窓幅で有界な `log --max-count=1` で行うため、履歴長には比例しない。
- receipt head を「窓の member」で縛るだけでは DAG で範囲が有界化しない。epoch より前で分岐した
  side branch を head にすると `receipt_head..HEAD` が窓外の古い履歴まで伸びる。epoch を head の
  祖先に要求すると、epoch から到達可能な commit は head からも到達可能になるため
  `receipt_head..HEAD ⊆ epoch..HEAD` が DAG でも成立する。
- 距離上限 1,000 は 2 つの制約から決めた。内部予算が外側 60 秒を超えないこと
  (`20.0 + cap x 0.035 < 60` ⇒ `cap < 1,142`) と、modeled 予算が外側の 75% に収まること。
  上限を 1,500 にすると内部 timeout が 72.5 秒になり、専用 reason より先に外側 timeout が発火する。
- 一点の測定から傾きと切片は分離できない。`0.005` は実測 `0.002429` 秒/(token·commit) に安全係数 2 を
  掛けた**モデルの失効 pin 専用の定数**であり、runtime 予算には使わない。実時間側は実測 guard が見る。

**却下した選択肢:**
- 既定 epoch を捕捉 HEAD にする案 — 窓が空になり自明合格を作る。敵対レンズ 2 本が独立に指摘した。
- 空窓だけを禁じる案 (`epoch != HEAD`) — 無関係な commit を 1 件入れれば抜けるため塞がらない。
- epoch を ruleops が完全に導出し宣言値を持たない案 — 既存 package の窓を再現できず、
  過去の受理を後から検証する手段が無くなる。
- receipt head を窓 membership で縛る案 — 上記のとおり DAG で範囲が有界化しない。
- 距離上限を 1,500 にする案 — 内部予算が外側 60 秒を超え、専用 reason が発火しなくなる。
- 窓外の reviewed event を filter して捨てる案 — 「検証しない申告を受理する」ことになる。
  拒否に倒し、変異でもこの形を単一理由の kill 対象として事前登録した。
- 算術 pin だけで時限を機械化する案 — 定数を積一定で入れ替えると緑のままになり、実時間が
  倍化しても発火しない。実測 guard を別に置いた。
- 全史 pickaxe を維持して外側 60 秒を引き上げる案 — ユーザー裁定で不採用。履歴長にも追随しない。
