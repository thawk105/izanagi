---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-26
wave: dev-wave-t1759-t1742-ratification-history
seq: 4
---

## 再発

### F128

- **再発: 2026-08-26** — 上書きしたのが別の子ではなく**監視側の道具**という形で同型が出た。
  親が `tools/dev_wave_wait.py producer` の `--receipt-file` へ、待つ対象である codex 子の
  `receipt.json` の絶対 path をそのまま渡した。待ち手は完了時に自分の受領証
  (`artifact_file` / `done_file` / `pid_source` / `status` を持つ別 schema) を同じ path へ書き、
  codex の受領証を上書きした。段 2 plan 子の工数 (wall clock・model call・token) は
  この 1 回で永久に失われ、worklog には欠測として記録するしかなかった。
  他の 7 子は `--receipt-file` を渡さなかったため無傷である。
- 追加の根本原因: `--receipt-file` は「待ち手が書く受領証の出力先」であって
  「照合する既存受領証の入力元」ではない。名前からは後者にも読め、待つ対象の受領証を
  指したくなる。F128 本文の (2) の「出力 path を再利用しない」は子同士の話として
  書かれていたが、**異なる道具の間でも同じ規律が要る**。
- 対処: 待ち手の `--receipt-file` には待ち手が所有する path だけを渡す。渡す必要がなければ
  省略する (本 wave の他 7 子は省略して問題なかった)。codex の受領証は
  `<artifact-root>/<wave>/<job-id>/receipt.json` にあり、親はこれを読むだけにする。
- 再発検知: wave 末に `<artifact-root>/<wave>/*/receipt.json` を全件読み、
  `stage` field を持たない受領証があれば上書きされている。本 wave はこの検査で気付いた
  (`KeyError: 'stage'`)。
