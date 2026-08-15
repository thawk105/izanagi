---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t257-land-lock-wait
seq: 3
---

## 新規

### {{F:dispatch-parent-sigterm-orphans}}. dispatch 親が SIGTERM された後も job がノードを 1 時間占有し、進捗ゼロの再試行ループが孤児を積み増した [手順漏れ]

- 事象: 計算ノードの queue が滞留する時間帯に、変異 matrix を完走させるため無人再試行ループを
  回した。ループは 6 回中 5 回まで**まったく同じ理由**で失敗し、completed は 0 件のままだった。
  その間、各 run が投入した job が queue / RUN に居座った。実測で 4 本
  (912760 / 912768 / 912771 / 912782) が同時に存在し、CPU 積算 0.28〜1.51 秒に対し
  elapse は 630〜3508 秒だった。**何もせずに 48 CPU のノードを walltime 1 時間まで抱える。**
  ユーザーから「計算ノードの無駄遣いは許さない」との指示が出た。
- 根本原因: 二つが重なった。(a) dispatch 親が約 15 分で SIGTERM され
  (`outcome` が `{"kind":"infra","rc":16,"reason":"_SignalAbort: signal 15"}`)、結果を回収できない
  まま抜ける。job 自身は投入 7〜16 秒後に `result.json` を書き終えているので、
  以後は完全に無駄な占有になる。receipt の `qdel` は `attempted: false` で、
  gate が `success-request-visible` と分類して片付けを見送る。(b) 再試行ループ側に
  **前進判定が無かった**。同じ理由で失敗し続けても次の iteration を投入するため、
  16 分周期で孤児が 1 本ずつ増える。ループを書いた側は「queue が空けば通る」と仮定していたが、
  失敗理由は queue 空きではなく親の寿命だった。
- 恒久対応: auto-memory `dispatch-parent-sigterm-leaves-orphan-jobs` に固定 —
  無人再試行ループの前に 1 本だけ投入して結果を見る、同じ理由で 2 回失敗したらループを止めて
  環境障害として報告する、ループを回すなら completed 件数の増加を iteration 内で判定して
  非前進なら break する。あわせて auto-memory
  `mutation-attempt-out-semantics-flip-on-resume` に、queue 障害で壊れた record が
  `--resume` を恒久的に詰まらせること (毎回同じ位置で rc=2) を固定した。
- 再発検知: `qstat` の CPU 積算と elapse の乖離で機械判定できる
  (投入後 1 分を超えて CPU が 2 秒未満のまま横ばいなら無駄占有)。
  ラッチ (F308) との識別は receipt の `outcome.kind` で行う — `f47` ならラッチ経路、
  `infra` なら親の寿命切れであり、後者では生きた dispatch 親が残らないため qdel でラッチは立たない。
