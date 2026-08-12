---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-13
wave: dev-wave-t907-t908-t910-acceptance-integrity
seq: 3
---

## 再発

### F24

- **再発: 2026-08-13** — 同型を**同一 wave 内で 5 回**独立に実測した
  (02:44 / 03:12 / 03:55 / 03:58 / 04:14 JST)。形は 2026-08-12 の再発と同じで、
  偽 green を返したのは通知ではなく **待ち手自身** (`tools/dev_wave_wait.py producer`) である。
  いずれも「`.done` 不在 + 成果物不在 + producer 生存」の状態で、
  出力ゼロ・rc=0 で投入から数十秒以内に返った。producer は `ps` で生存を確認している。
  本 wave の追加事実は **発生頻度**で、対象は codex 子 (author / review / fix)・
  変異 harness・受入全走の待ちに跨り、子の種別に依存しない。
  既存の恒久対応 (「成果物実在 + `.done` + producer 死」の 3 点照合を親が毎回行う) は
  5 回とも有効に働き、実害は出ていない。
  ただし本 wave の主題が受入 gate の fail-closed 化であることを踏まえ、
  **待ち手側の完了条件そのものを fail-closed にする恒久修正**を
  {{T:waiter-producer-completion-fail-open}} として起票した。
