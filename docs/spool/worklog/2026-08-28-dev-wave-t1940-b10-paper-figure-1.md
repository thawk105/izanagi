---
schema: izanagi-spool-v1
ledger: worklog
authored: 2026-08-28
wave: dev-wave-t1940-b10-paper-figure
seq: 1
title: [T-1940] B-10 拡張格子の有効 28 点を論文図へ変換する (コード + docs、branch worktree-dev-wave-t1940-b10-paper-figure、変異 matrix = baseline PASSED・8/8 KILLED・SURVIVED 0・MISMATCH 0)
---

## 本文

- ユーザー指定の既存計測だけを使用し、新規計測・perf・追加格子を行わず、commit `637dafa17` で図・PDF/PNG・provenance・README 導線を固定した。
- job / workload / campaign は 951689 / write-heavy / `0a386b45`、951690 / balanced / `9ded73c4`、951691 / read-heavy / `e2d75497` と receipt chain・lock identity の双方で再照合した。
- 1000 µs は F718 の符号化衝突点として測定値を provenance に保持したまま非描画とし、各 workload の有効 28 点だけを描いた。static 0 µs は no backoff と混同していない。
- 段 2 plan 1 本、段 3 consult 2 本、D95 author 1 本、段 6 review 2 本、fix 3 本、focus 1 本を実施。全 worker は Codex `gpt-5.6-sol` / reasoning `xhigh`。
- plan の「既存 generator を改訂」は既存 fig2b の source hash pin を壊すため棄却し、既存 bytes 不変の専用 generator 純増へ変更した。review の rootless closure・receipt semantic・CI 恒真化・caption所見を全て閉じ、focus は GO / 新規所見なし。
- 親焦点走は新規 38 passed、既存 fig2b 回帰・meta-testを含む関連走は 156 passed。`check_codex_agents.py` と `check_docs.py` も通過した。
- 変異本走は固定 commit `637dafa17`、計算ノード dispatch。baseline 28.234 秒、8/8 KILLED、全 failure node完全一致、SURVIVED / MISMATCH / TIMEOUT 0。raw result SHA-256=`5e76a8eac227a04a5f4c60dcf35ba0f04b93b7633ff26115c133bc5366314db0`。
- mutation wrapper は並行 main land の共有木事後検査で2回停止し、land lease取得後の同一matrix再走で rc=0 まで閉じた。collection timeout時に result無しでも無効なresume commandを示す改善候補は段8へ送る。
- commit後 provenance監査は新規違反0。履歴の既知違反54件は緑と読み替えていない。
- scope外: T-2018 の意味gate・1000符号化修正・D1094の新floor計測は実装せず、D1092に従い ADD_ANALYSIS 診断値も図から外した。
- 受入全走は本fragmentを含む記録commit後に投入するため、この時点では未実施。

## 次の一手差分

### 完了

- [T-1940] 完走済み B-10 拡張格子を、符号化衝突点を除いた有効 28 点の論文図、PDF/PNG、provenance、README 導線へ変換した。
  remaining: none
  base: 0e4c08d77a090cc3840dbd2540cc726cd169ea3bdaa3be760aff0e17df826e10
