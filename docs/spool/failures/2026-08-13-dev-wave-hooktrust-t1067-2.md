---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-hooktrust-t1067
seq: 2
---

## 新規

### {{F:qdel-arms-f47-latch}}. 自分が投入した dispatch job を qdel したら、以後の dispatch が worktree 単位で全面停止した [手順漏れ]

- 事象: 2026-08-13 の dev-wave-hooktrust-t1067 で、段 6 の焦点走を計算ノードへ dispatch した直後、
  同じ worktree へ fix 子 (workspace-write) を投入する必要が生じた。走行中のテストと
  木の書き換えを併走させないため、queue 中の自分の job (909514.nqsv) を `qdel` した。
  その結果 `tools/pegasus/dispatch_compute.py` が「計算ノード marker 未観測」と判定し、
  `output/pegasus-dispatch/submission-disabled.json` (F47 型ラッチ、
  reason=`compute-marker-not-observed`) を立てた。以後 `--force-dispatch` を含む
  すべての dispatch が rc=16 で止まり、**受入全走と変異 matrix を実施できないまま wave が停止した。**
- 根本原因: ラッチの発火条件は「submit したのに marker が出ない」であり、
  **意図的な取り消しと、資格情報不整合による無効 request を区別しない。**
  qdel する側は「自分の job を片付けた」としか認識しておらず、
  それが fail-closed の防壁を武装させることを知らなかった。
  解除手順は設計上ユーザー手番 (F47 の恒久対応) であり、AI 側では戻せない。
- 恒久対応: auto-memory `dispatch-qdel-arms-f47-latch` に固定 —
  自分の dispatch job を取り消す前に、(i) 併走回避が本当に必要かを判断し、
  (ii) 必要ならまず走らせ切ってから子を投入する順序に変える。
  やむを得ず qdel するなら、ラッチが立つこととユーザー手番が要ることを
  同じ turn で報告に含める。
- 再発検知: ラッチ file の存在は `dispatch_compute.py` が起動時に検査して rc=16 を返すため、
  発火自体は機械検知済み。検知されていないのは「AI が自分で武装させた」ことの識別で、
  ラッチの `request_id` と自セッションの qdel 記録を突き合わせれば判定できる。
