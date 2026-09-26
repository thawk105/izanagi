/dev-wave [T-2273] [T-2560] 受入 shard-0 の律速を解く。律速は t080 共有 base の builder による Lustre の output/ 可視集合の複製で、第 4
  回診断の一次資料は output/insights/2026-09-23/t2273-shard0-bottleneck-4/README.md。着手直前の local main から fresh
  worktree。複製元を計算ノード局所の写しに差し替える実装を行う。同一 node の 1 対の対照では W_0 が −123.9 秒 (−27.3 %)
  だった。局所の写しを作る時期・担い手・未 commit の可視 file の扱いを設計し、D2068 で却下された 3 案 (whitelist / alternates / 独立 index)
  には触れない。全件性の検査 2 か所は維持する (D2044 項 15)。実装は Codex author (D95)。隣接対の実受入で効果を測ってから land
  する。性能主張は同時刻の対照で示す。規律 2 を緩めない。本題の実装だけ。仮想リスク向けの gate・検査・台帳・一般化の追加は scope 外。
