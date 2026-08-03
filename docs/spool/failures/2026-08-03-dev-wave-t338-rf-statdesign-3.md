---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-03
wave: dev-wave-t338-rf-statdesign
seq: 3
---

## 再発

### F77

- **再発: 2026-08-03** — 本 F の恒久対応どおり `nohup bash -c '...' &` で段 2 の codex 子を投入したが、
  **`nohup` でも子は tool 呼び出しの終了とともに死んだ** (ログは 3 分ぶん残り `.done` は不在)。
  すなわち本 F が記録した「背景 job では `nohup` で投入し」は**十分条件ではない**。
  一方で「`.done` 不在を根拠に再投入しない — 先に生存確認する」は効いた — 親は再投入前に
  `ps` で同一 artifact を書く process が 0 本であることを実測し、二重起動を起こしていない
  (1 回目のログは別名で保全した)。実際に生き残ったのは、`&` も `nohup` も使わず
  **harness 管理の background 実行へ `bash -c '<cmd>; echo $? > <log>.done'` をそのまま渡す**経路で、
  投入 20 秒後に `ps` と log 増加で生存を実測した。成果物影響ゼロ (near-miss)。
  `DW-O01` への明文化は本 F の記録どおり byte 予算に阻まれたままであり、
  必要 63 bytes に対し `operations.md` の余裕は 44 bytes、意味等価な縮約 1 件で 15 bytes 回収しても
  **4 bytes 足りない**ことを実測した (この数値を [T-341] へ足した)
