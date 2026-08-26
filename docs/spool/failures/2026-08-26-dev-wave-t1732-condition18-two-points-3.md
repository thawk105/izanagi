---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1732-condition18-two-points
seq: 3
---

## 新規

### {{F:probe-run-serialization-parent-side}}. 親が校正用の走行を背景投入したまま次の走行を投げ、同一 worktree の並行 dispatch で orphan hold を踏んだ [手順漏れ]

- 事象: 段 6 の timeout 校正のため単一 node の走行 2 本を背景で連鎖投入し、それが計算ノードで
  実行中に焦点走 (file 全体) を投入した。後発の投入は
  `IZANAGI_DISPATCH_OUTCOME_V1 {"child_started":false,"kind":"infra","reason":"orphan-hold"}` で
  子を起動せずに終わり、焦点走の結果が 1 回失われた。
- 根本原因: `DW-O26` の「焦点走の分割投入は直列にする。同一 worktree の並行 dispatch は
  orphan hold で rc=16 になる」は**焦点走どうし**の話として読まれやすい。実際には親が校正・計測目的で
  投げる単発 node の走行も同じ dispatch 経路を使うため、種別が違っても直列化の対象である。
  親には背景投入した dispatch の在否を投入直前に確かめる習慣が無かった。
- 恒久対応: `DW-O26` が定める直列化の対象を、焦点走に限らず**同一 worktree からの dispatch 全種**と
  読む。投入直前に `qstat` と `output/pegasus-dispatch/orphan-hold.json` の不在を親が確認する。
  機械側の実体は既存の fail-closed 検査 (hold 在中は scheduler command を起動しない) であり、
  欠けていたのは親側の運用規律である。
- 再発検知: 後発投入が `reason=orphan-hold` で子を起動せずに戻る。静かに壊れることはない。
- 波及: 本件の hold は先行走行の自然終了で撤去された。手動削除も `qdel` もしていない
  (`qdel` は F47 の submission-disabled を武装させる)。

## 再発

### F24

- **再発: 2026-08-26** — `tools/dev_wave_wait.py producer` の待ち手が rc=0 で偽完了する形を
  **同一 wave で 3 回**観測した (段 6 焦点再レビュー、変異 probe、焦点走の 2 回目)。いずれも
  `.done` は不在で子は生存しており、恒久対応 (`.done` の実在で判定し、待ち手の rc も通知も信じない)
  がそのまま効いて実害はゼロだった。**本 wave の追加事実は生存判定の側にある** —
  道具名だけの `pgrep -f "mutation_worktree.py"` は**並行 wave の子を自分の子と誤認する**。
  実際に別 wave (`dev-wave-t1858`) の変異走行を自分のものと数え、本走の投入を無用に待った。
  `DW-M05` が要求する worktree path での一意化は、変異中の生存確認だけでなく
  **待ち直しのたびの生存判定にも適用する**。
