---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1155-t1178-floor-receipt
seq: 3
---

## 新規

### {{F:dev-wave-waiter-spurious-completion}}. 待ち手が producer 生存中に空振り終了した [恒真ゲート]

- 事象: 2026-08-16 の本 wave 段 6 で、`tools/dev_wave_wait.py producer` が
  **producer プロセス生存中・`.done` 不在・成果物不在**のまま、出力ゼロで rc=0 終了した。
  親が 3 点照合 (pid file の pid を `ps -p` で確認 = 生存、`qstat` で計算ノード job が RUN、
  `.rc` 不在) を行って空振りと判定し、待ち手を張り直して回復した。
  arming 前に pid file の実在は確認済みで、既知の「pid file 不在で即空振り」型ではない。
- 根本原因: **未特定**。同 wave の他 8 本の待ち手は同じ手順で正常に待機しており再現していない。
- 恒久対応: 待ち手の rc=0 を完了の証拠にしない。完了判定は
  **成果物実在 + `.done` + producer 死亡**の 3 点照合に限る
  (memory `background-task-notifications-can-be-fabricated` の運用を待ち手 rc にも適用する)。
  照合せずに次段へ進むと、テスト未完了のまま commit へ進む。
- 再発検知: 本エントリへ再発を追記する。2 例目が出た時点で機序を特定し、
  待ち手側の fails-closed 検査として実装する。

## 再発

### F30

- **再発: 2026-08-16** — 本 wave の親が `DW-O09` の pin 閉包で `output/` を検索対象から除外し、
  `output/s8b-freeze/holdout_freeze.json` の `/generator/sha256` が
  `orchestrator/campaign/s8b_holdout_freeze.py` の bytes を pin している事実を落とした
  (現行 bytes は既に不一致で `freeze_verification_hold` 下)。
  F30 は「成果物を bytes で pin している台帳」を数え落とす型だったが、本件は**逆向き** —
  **成果物 JSON の中に埋まった source pin** である。段 3 の敵対レンズが検出し、親が独立に裏取りした。
  pin 閉包は成果物側 (`output/`) も検索対象に含める。
