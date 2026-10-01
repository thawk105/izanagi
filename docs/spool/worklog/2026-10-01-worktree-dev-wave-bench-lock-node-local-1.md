---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-10-01
wave: worktree-dev-wave-bench-lock-node-local
seq: 1
title: 計算ノードの bench lock を node ローカル既定にし、別 node の job の直列化を解く (コード + docs、branch worktree-dev-wave-bench-lock-node-local)
---

## 本文

- 依頼: SELF-REVIEW 束の md_4 (2026-10-01、land 調整役「manager: parallel land」配布)。A-2 R2 で、home 共有の `~/.izanagi/bench.lock` が
  3 job の性能検証と bench を 1 列に並べていた件。設計判断は {{D:bench-lock-node-local-default}}。
- lock の目的を先に確かめ、repo 全体の排他ではなく同一マシンの測定汚染防止と判断した (lock.py docstring、D36 決定 4-(4))。相談は不要と判断した。
- 段 3 の敵対相談 2 本と段 6 のレビュー 2 本の要点:
  - fan-out worker を node 共通 lock にする是正案は、2 job の node 集合が交差するとデッドロックするので不採用。保証範囲を限定して記録した。
  - `O_NOFOLLOW` は受理集合を変えるので不採用。
  - `/tmp` の age 掃除への対策として、取得時の mtime 更新を採用した。
  - テストの HOME 隔離と、判定器 (c) の終端の修正を fix した。
- smoke の形を依頼文 (WAL 時刻) から変更した。前提なしで 5 分以内に実 bench と WAL を通せる既存経路が無いため、land 調整役へ投入前に相談し、
  案 1 (本番 `bench_lock()` を import する probe) で GO を得た。
  - 結果: generic dispatch 2 本 (40909/40910.nqsv、bnode043/bnode042、各 Elapse 24 s)。
    - (a) 別 node の既定 lock の保持区間が 5.0 s 重なり、両者が保持中に相手の取得を観測した
    - (b) 各 node 内の 2 process は排他された
    - (c) 共有 FS 上の対照 lock は別 node でも直列 (重なり -0.049 s、busy 握手あり)
  - 判定器の総合は、時計誤差の上限を外部で確立していないため inconclusive (rc=2)。(a) は各 host ±1 s を仮定しても 3.0 s の重なりが残る。
- 焦点走: 40901.nqsv で 3561 passed, 17 skipped。fix 後の変更 test file と列挙メタテストの単独走は 40916.nqsv で 381 passed。
- 変異: lock.py に 8 変異 (正例 1、負例 7)。独立 clone (main = a6dea8eb1) の固定 commit で走らせた。
  probe 走 40918.nqsv で観測 node を集め、final 走 40923.nqsv で照合した結果は KILLED 7 (期待 node と完全一致)・SURVIVED 1 (M0)・不一致 0。
- 受入全走は、この記録 commit の後に `tools/dev_wave_wait.py acceptance` で行う。結果は receipt と land 申告に残す。
- 依頼文の数値の扱い: 6.39 node 時間は依頼資料の実測報告、約 3.3 は未実測の試算で、wall 効果は未確認。

## 次の一手差分

### 新規

- {{T:bench-lock-node-local-followups}} **P2・新規**: {{D:bench-lock-node-local-default}} の残り。
  (1) 次の A-2 実走の WAL で、別 node の bench と性能検証が並行に走ることを確かめる (本 wave の smoke は lock 機構だけ)。
  (2) fan-out を含む並走で、job 間の node 集合が交わらないことを launcher 側で検査するか判断する。
  (3) `$TMPDIR/bench.lock` を明示する job body 3 本を node 共通の既定へ揃えるか判断する (D2209 の job 固有 lock)。
  (4) 同じ node の別 job が同じ lock file を見ることと、job 終了後に lock file が残ることを実測する。
