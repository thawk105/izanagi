---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-09
wave: dev-wave-t648-fallback-ledger
seq: 2
---

## 再発

### F57

- **再発: 2026-08-09 ([T-648] 受入全走)。** 48 worker の全走 (request `896541`、1260 秒) で
  `test_ruleops.py::test_real_checkout_independent_maximum_package_and_runner_preflight@real_repo` が
  1 件落ちた (7504 passed / 1 failed / 20 skipped、gw41)。assert 不一致ではなく
  `tools/ruleops.py inventory` の子が `ruleops: git-timeout: git log timeout` で rc=2 を返した形で、
  同 node は 2026-08-08 ([T-639]) と同一、producer も同じ git である
  (ただし当時は `git cat-file`、今回は `git log`)。単独再走は **1 passed / 75.55 秒 / rc=0** で
  再現しない。本 wave の差分は `docs/spool/` の fragment のみ (実装差分ゼロ) で当該コードへ
  到達しえず、`DW-O18` により帰属しない。
  **新しい情報は 2 点。** (i) [T-639] では 2 node が同時に落ちたが、今回は同じ producer で
  1 node だけが落ちた — 同一条件下でも顕在化する node 数は揺れる。(ii) 本走行の並行度が
  台帳既載のどの再発よりも高いことを受入 lease が実測している — claim が 2 時間 15 分待ちで、
  その間に holder が 5 回交替した (`1de688eff46c` → `a04bbc9f8c4b` → `a2e0f6789afd` →
  `cc98ed71bb7e` → 自分)。「別 branch の並行 wave が同じ repo で稼働中」という [T-639] の
  見立てを、待ち行列の実測が独立に裏付ける。
  恒久対応は F57 既載のとおり失敗 artifact 保存による原因分離 ([T-190]) で、本 wave では変えない。
