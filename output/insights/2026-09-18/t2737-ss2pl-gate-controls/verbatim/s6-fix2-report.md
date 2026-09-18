## 総括

- 変更行：`t2737_gate_probe.py` 483–500（負例・正例）、630–638（mkdir → resolve、receipt 検査結果、kwargs）。`README-probe.md` 35–36、219行以降を更新。
- pegasus02 の selftest：**rc=0、17 PASS**。新項目は `fetchcontent-missing-rejected`、`fetchcontent-mkdir-resolve-accepted`。
- F2：**partial**。作成漏れ修正と入口検査は完了。計算ノードでの warm-up・warm cell 回復は未確認。
- tracked file・patch 2本は無変更。commit 等なし。docs / Codex agents checker とも rc=0。
- 今回未実走：login-precheck、helper 本体、計算ノード cell、plain build、trial。

成果物（すべて `probe-t2737/` 配下）：

| ファイル | bytes | SHA256 |
|---|---:|---|
| `t2737_gate_probe.py` | 38745 | `6ffae7beaa263fca7b769a6ef90e5d0273241793451c57b917bd837bcd96a61f` |
| `README-probe.md` | 19243 | `2c41029dfaf0349cbc723805ab3e092562443556d521c4e068bf81c13079fa3a` |
| `patches/ss2pl-lock-protocol-study-define-only.patch` | 86721 | `8ccb4c59e467253c73f90f27b0891f5f67ba66311e9a65ca261582282580db50` |
| `patches/ss2pl-lock-protocol-study-define-only-abort-unconditional.patch` | 86612 | `f0b48d2cd66712c87974634c0ce337c03536152632a766f3772bed3ac26d0130` |