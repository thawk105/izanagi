---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-09-17
wave: dev-wave-t2675-nqsv-run-membership
seq: 1
title: [T-2675] NQSV が request を RUN に留めるのは現在の session 所属 — setsid / setpgid の分離実験 2 本 (実装差分ゼロ、branch worktree-dev-wave-t2675-nqsv-run-membership、変異 matrix = 実装差分ゼロで免除)
---

## 本文

- ユーザー依頼は「NQSV が request を RUN に留める判定方式が session か process group か scheduler の追跡集合かを分離する。
  [T-2622] の実験は全記録で sid == pgid だったため分離できていない。所属を変える条件 (setsid した子、process group だけ変えた子) を
  足した実験を generic dispatch で計算ノードへ投入し、終了遅延の対策の向き (T-2676 の前提) を決める。着手直前の local main から
  fresh worktree を作る。実装差分ゼロ (probe は job dir へ保全、repo へ commit しない)。subreaper は採らない (F973)。qdel はしない。
  一次資料 output/insights/2026-09-16/t2622-compute-job-exit-hang/README.md。規律 2 を緩めない。本題の分離実験だけ」。
- **閉じた。** 一次資料は `output/insights/2026-09-17/t2675-nqsv-run-membership/README.md`。設計判断は {{D:nqsv-run-hold-is-current-session}}。
  失敗の型は F553 の再発 (親が自分で凍結した事前登録の停止条件を守らなかった)。実装面の commit 差分は 0 (probe は Codex author 作、job dir へ保全)。
- **結論 (事前登録どおり):** 実験 1 (6 条件、子の寿命 75 秒) と実験 2 (session 離脱 2 条件の寿命短縮版、段 6 レビュー後・投入前に事前登録) で、
  適格走の観測ベクトル (S0′, G0, S30′, G30) = (0, 70, 25, 70) は登録した同値類のうち **A 類 (現在の session 所属に応答するモデル) だけと一致**。
  現 pgid 基準 (G0 / G30 = 70)、fork 時に記録され保持される集合 (S0′ = 0、S30′ = 25)、即時離脱だけが効く走査集合 (S30′ = 25) は不適合。
  統制 D = −0.001 秒、陽性対照 K = 69.546 秒 (前 wave の再現)。値は `E − J` (NQSV 会計 `Ended` − trace `job-run-returned`)、8 走すべて
  `scheduler-end-state`・`qdel.attempted = false`・orphan hold 0。
- **実験 1 の S0 / S30 は不適格。** 寿命 75 秒で session を離脱した子は 2 走とも会計終了の約 35 秒後まで heartbeat を残し、次の予定
  (約 40 秒後) 以降は記録されず `child-exit` (t0+75) が無い。段 6 レビュー 2 本が「E − J の分類を救う親の読みは事後変更」と指摘し
  (A-1 / B-1)、主解析から外した。記録途絶の原因・主体 (kill / 停止 / 記録障害) は未同定で、「消えた」とは書かない。
  寿命を 35 / 60 秒にした実験 2 では子は E の約 30 秒後に自発終了して適格になった。
- **親の逸脱 (記録):** 事前登録 §3.3 (6) の「終端記録不足で追加投入停止」に反し、S0 の `child-exit` 欠落を確認した後に G0・S30・G30 を
  投入した (F553 再発)。実験 2 ではこの規則を守った。
- **段 3 で親 brief の誤り 3 点を訂正した。** (a) probe は uid 0 で走る → 誤り。bootstrap は内側 user ns で実 uid を復元して exec する
  (evidence `resuid = [31609,…]`、`uid_map = "31609 0 1"`)。(b) heartbeat で死亡時刻を上限づける → 逆。最後の heartbeat は生存時刻の下限。
  (c) 4 仮説で分離できる → 同値類 A/B/C/D に落ちるだけで、A 類内部 (照会 / イベント更新 / 周期再評価) と表外モデルは識別不能。
- **qdel の扱い:** 8 request すべて receipt 上 `qdel.attempted = false`、手動 qdel も hold の手動削除もしていない。親は「qdel はしない」を
  手動操作の禁止と解釈し、dispatcher 既存の QUE/HLD 自動取消経路 (queue-wait-timeout 後、RUN は取消不可) を変えなかった。
  この限定はユーザーが明示した例外ではなく、今回その経路が発火しなかった実績と分けて記録する。
- 実験 2 の S0′ (request 4108) は NQSV の Pre-running に約 11 分留まった (実行ホスト未割当、同時刻に親の他 session の request 4 本も PRR)。
  原因不明、待って自然に走った。
- T-2676 へ渡す 1 行: pgid 離脱だけでは短縮せず、session 離脱に終了遅延の短縮が対応した (事前登録どおり)。session 離脱・session を基準とする
  回収を検証候補とし、会計終了と残存子の終了を別々に評価する。離脱後の記録途絶は回収成功の証拠にしない。
- 段 8 (自己改善): 候補 1 件 — 「計算ノード probe の子が job 外で生き続ける条件では、事前登録の適格性 (`child-exit` の時刻) を job 終了後の
  未知の後処理より短い寿命で設計する」は F553 再発の記録と insight §5 で足り、dev-wave 文書は byte 予算満杯 (2026-09-16 実測) のため記録のみ。
- 工数: codex 子 7 本 (plan 1、consult 2、author 1、review 2、全段 `gpt-6-astra` / `medium`)。fix 子 0 (実装面の差分が無く、レビュー所見は
  docs の書き換えと実験 2 の追加で閉じた)。親の実測: selftest 1 (login、32.6 秒)、計算ノード dispatch 8 走 (実験 1 = 6、実験 2 = 2、
  Elapse 9〜80 秒)、受入全走は docs commit 後の最終 tip に land 前に 1 回 (結果は land の受領証)。

## 次の一手差分

### 完了

- [T-2675] session / process group / 追跡集合を分離した。現在の session 所属 (A 類) だけが整合、現 pgid・fork 時記録集合・即時離脱限定は不適合。
  一次資料 `output/insights/2026-09-17/t2675-nqsv-run-membership/README.md`。
  remaining: none
  base: 1239a62492ae4c5e67f340a6e125d02ea3a41d35558091c6d60bbd26a9668d23

### 更新

- [T-2676] **P2・新規**: 計算ノード job の終了遅延そのものへの対策。[T-2622] は原因同定だけで scope を切った。
  subreaper は採らない (F973)。[T-2675] の結果: NQSV は job の session に生きた process がある間 RUN に留め、
  session を離脱した process は待たない (pgid 変更では待つ)。設計入力は {{D:nqsv-run-hold-is-current-session}} —
  session 離脱・session を基準とする回収を検証候補とし、会計終了と残存子の終了を別々に評価する。
  寿命 75 秒で session を離脱した子は job 終了の約 35〜40 秒後に記録が途絶した (原因・主体未同定) ので、
  離脱後の残存子の終了は既存機構に任せず独立に検証する。元 session の列挙だけでは別 session へ移った子を拾えない。
  base: e1fa74f5a485fc1140702b1c9d09de9d099767cc63fbea7587e606aadb40457e
