---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-10
wave: dev-wave-t714-evidence-path-ctrlchar
seq: 3
---

## 新規

### {{F:lease-claim-output-is-json}}. 受入 lease の待ち手が出力形式を取り違え、取得できないまま待ち続けた [手順漏れ] [コンテキスト浪費]

- 事象: 受入 lease の待ち手を `claim` の出力に対する `state=acquired` の文字列一致で書いた。
  `claim` が返すのは JSON (`"state": "acquired"`) なので**一致は決して起きない**。
  lease が空いても投入されず、約 40 分を空費した。Monitor の timeout で気づいて自分で発見した。
- 根本原因: runbook の例が `status` サブコマンドの key=value 出力を見せており、
  `claim` も同形だと仮定した。**同じ tool の別サブコマンドで出力形式が違う**ことを
  実行前に確認しなかった。
- 恒久対応: `docs/pegasus-runbook.md` §7.3 に「`claim` の出力は JSON、`status` は key=value。
  待ち手は JSON として parse する」を明記し、待ち手の雛形を JSON parse 版にする。
- 再発検知: 待ち手は最初の 1 回目の `claim` 出力を log へ残す (本 wave の待ち手は残していた)。
  取得状態が変わらないまま 2 周期を超えたら、log の実出力と判定条件を突き合わせる。

## 再発

### F29

- **再発: 2026-08-10** ([T-714] wave)。段 1 の前提実測で、末尾 CR 付き path と正常 path が
  同じ blob を指すことを **`len(bytes)` の一致**で確認し「同一 blob」と brief に書いた。
  長さの一致は同一性ではない。段 3 の敵対レンズ A が「親の保存済み実測 artifact 単独では
  結論を支持していない」と指摘し、親が blob OID / sha256 で測り直して結論を裏取りした
  (`1744da0e…` の一致)。結論の向きは正しかったが、**測定対象が命題と違っていた**点で F29 と同型。
  同 probe の作り直し (v2) で、NUL の同型欠陥という新事実も併せて実測できた。
