---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-16
wave: dev-wave-t1132-model-routing-luna
seq: 3
---

## 再発

### F320

- **再発: 2026-08-16** — 同日の別 wave (`dev-wave-t324-8c-prereg`) が記録した直後に本 wave でも再現。
  `stage=preflight-submodule-ready rc=2` でテスト 0 件・log ファイル未生成のまま失敗
  (lease claim 前の preflight で止まったため lease 窓は失っていない)。
  `git -c protocol.file.allow=always submodule update --init --recursive` で
  `external/ccbench/third_party/shirakami` とその `third_party/googletest` を追加初期化し、
  `git submodule status --recursive` の全行が `-`/`U` プレフィックスなしになったことを確認して
  attempt 2 で再投入した。恒久対応 ([T-1139] 未裁定) は未実施のまま。
