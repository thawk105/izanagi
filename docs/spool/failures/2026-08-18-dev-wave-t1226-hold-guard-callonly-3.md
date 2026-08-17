---
schema: izanagi-spool-v1
ledger: failures
authored: 2026-08-18
wave: dev-wave-t1226-hold-guard-callonly
seq: 3
---

## 新規

### {{F:force-color-leak}}. セッションの色環境が subprocess へ漏れ、bounded local の焦点走だけで赤が出た [誤前提] [手順漏れ]

- 事象: 実装差分の焦点走で `test_plain_pytest_delegating_runner_is_not_over_rejected` が赤に
  なった。保留の機能自体は正常で (「1 skipped」の assert は通っていた)、落ちたのは pytest の
  末尾サマリを読む正規表現 `(?m)(\d+) passed(?:,| in )` である。出力には
  `103 passed` があるのに一致しなかった。
- 根本原因: 親セッションの環境に `FORCE_COLOR=3` が入っており、テストが起動する subprocess へ
  そのまま渡っていた。`_clean_subprocess_env` が除くのは `PYTEST_ADDOPTS` と解除 env だけである。
  色が有効だと `passed` の直後に ANSI escape が入り、正規表現の `(?:,| in )` に届かない。
  **差分には帰属しない。** 色環境を外した単独再走で `1 passed` を実測した。
- 波及の広さ: bounded local で走る焦点走だけで起きる。`FORCE_COLOR` は
  `tools/pegasus/dispatch_compute.py` の `tests` task の env allowlist に無いため、計算ノードへ
  dispatch する変異 matrix と受入全走には現れない。したがって「焦点走で赤・受入で緑」という
  食い違いとして現れ、差分の回帰と誤認しやすい。
- 恒久対応: 親が回す焦点走・変異走行の起動 script で `unset FORCE_COLOR` / `unset COLORTERM` を
  行う (本 wave の `rerun-focus.sh`、`run-mutation-probe.sh`、`run-mutation-main.sh` がその形)。
  memory `dev-wave` 系の運用知見として `no-machine-coupling-in-shared-docs` に反しない範囲で
  session 側の運用に閉じる。
- 再発検知: 単独再走による帰属判定が現に機能した (色を外すと緑)。判定手順は
  `DW-O18` の「差分が到達しえない赤は単独再走で実測し、再現しなければ帰属せずフレーク起票する」
  に既にある。本件はその適用例であり、再走時に**環境変数を揃える**必要があることを追加する。

## 再発

### F352

- **再発: 2026-08-18** — 1 wave の中で、待ち手が出力ゼロのまま「完了」通知を出す事象が 6 回起きた
  (段 6 の fix 子 2 回、変異 probe 1 回、変異本走 2 回、レビュー待ち 1 回)。毎回 producer は
  `ps -p <pid>` で生存しており、`.done` も成果物も不在だった。通知を完了判定に使わず pid と
  `.done` で実測する既存手順が正しく機能した。前景で `--max-wait-seconds` を 10 分未満にして
  待つ形は、同じ wave 内で 1 回目から成功した。
