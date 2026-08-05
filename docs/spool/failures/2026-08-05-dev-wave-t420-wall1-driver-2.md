---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-05
wave: dev-wave-t420-wall1-driver
seq: 2
---

## 再発

### F29

- **再発: 2026-08-05** ([T-420] wave)。段 1 の前提実測で、登録済み較正の `effective_clock`
  mapping を**そのまま** expected として consumer 述語
  (`execution_guard.effective_clock_comparison_passes`) へ渡し、「登録済み較正は自分自身の述語を
  通らない → 実行時 attestation は必敗 → 通す道は gate を緩めるか較正を取り直すかの 2 つだけ」と
  結論した。実際にはこの述語は expected に `{samples_mhz, tolerance_pct}` の**ちょうど 2 key** を
  要求し、artifact の mapping は `governor` / `method` を含む 4 key を持つ。したがって親の測定は
  **値ではなく形で** False を返しており、3 通り試した観測値のすべてが同じ理由で False だった。
  実行時と同じ射影 (`env_attestation._clock_value`) を通して測り直すと、**静穏な機械 (48 標本が
  すべて中央値) なら現行の登録済み較正のままでも受理される (True)**。すなわち gate は構造的に
  壊れておらず、親の因果説明は誤りだった。真の阻害要因は probe の観測者効果 (走行 CPU は定義上
  busy なので必ず帯外標本が出る) である。検出は段 3 の敵対 codex で、親が実行時射影で再測して撤回した。
  **教訓: gate 述語を直接呼んで前提を測るときは、引数を手で組まず production の呼び出し経路が
  使う射影関数を通して作る。** 手組みの「それらしい mapping」は shape 拒否と値拒否を区別できず、
  gate が「必ず落ちる」ように見える。F29 の再発検知行 (レンズに「親の実測は実差分を
  モデル化しているか」を含める) は今回も設計どおり機能した
