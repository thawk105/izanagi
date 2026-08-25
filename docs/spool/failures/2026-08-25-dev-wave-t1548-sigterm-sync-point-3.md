---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-25
wave: dev-wave-t1548-sigterm-sync-point
seq: 3
---

## 再発

### F350

- **再発: 2026-08-25** — 書き手が親ではなく**並行して走らせた Codex 子**だった初の例である。
  親は変異 probe 走を投入した直後、待ち時間を使って別の author 子を起動した。
  その子が worktree へ 2 file を書き、wrapper の走行後検査が
  `共有木の事後検査に失敗: source/main 共有木の観測 bytes が変化した` で `rc=125` になった。
  既載の恒久対応は「待機中に進めてよい作業から repo への書き込みを除く」だが、
  **子を起動する判断そのものが repo への書き込みになりうる**点が抜けていた。
  親が自分で書かなければ安全、という読み方が成立しない。
  変異結果自体は 6 変異とも完走しており、本走の `expected_nodes` はこの probe から採れた。
  失われたのは走行 1 回分の時間だけで、検知は fail-closed で効いている。
  **変異走行中は、親の直接編集だけでなく worktree へ書きうる子の起動も止める。**
