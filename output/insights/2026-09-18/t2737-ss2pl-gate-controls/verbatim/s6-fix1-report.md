## 総括

- 両 patch の `insert()` を stock 逐語に復元：revS 913行（hunk 909行）、abort-unconditional 909行（hunk 905行）。他の patch 行は無変更。
- 2版差分は **abort ブロックのみ**。19 paths の検算・適用木比較とも確認済み。
- login-precheck：**rc=0**。S は **cmp rc=1、残差1箇所・diff 2行**（`ERR` の `__LINE__`: 97→154）。指定どおり `#line` 同期なし。
- IMPL：`reason_code=stock-inert-mismatch`、`root_diff_line_count=1`。
- selftest：**rc=0、15 PASS**。phase1 再比較：**rc=1**、差は復元した括弧のみ。他の局所5比較・raw3比較は一致。
- F1：**partial**。復元は完了しましたが、phase1 bytes 一致は未達。README 156行以降に記録済み。
- tracked 無変更。build・warm-up・trial・計算ノード cell は未実走。

成果物（`probe-t2737/` 相対、bytes／SHA256）：

| ファイル | bytes | SHA256 |
|---|---:|---|
| `patches/ss2pl-lock-protocol-study-define-only.patch` | 86721 | `8ccb4c59e467253c73f90f27b0891f5f67ba66311e9a65ca261582282580db50` |
| `patches/ss2pl-lock-protocol-study-define-only-abort-unconditional.patch` | 86612 | `f0b48d2cd66712c87974634c0ce337c03536152632a766f3772bed3ac26d0130` |
| `t2737_gate_probe.py`（無変更） | 37306 | `418448c934e4cbeb3f6d36cced22aa87526f695a644ff1711ce90f58cf832068` |
| `README-probe.md` | 16930 | `b0cdca91e3f46ac704c03736d767e8a3147393acb7852bafe5d79846137559e5` |