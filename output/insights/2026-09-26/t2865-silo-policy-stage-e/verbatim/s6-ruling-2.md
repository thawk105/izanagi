# 段 6 裁定 2 巡目 — [T-2865] (2026-09-26、親)

対象: fix commit `47d352205` + docs `cc5d8375e`。入力: 焦点再レビュー 1 (`codex/s6-focus-1.md`、NO-GO、must-fix 1・should 1)、焦点走 3 (`focus-3.log`)、親の点検 2 件。

## 裁定

| ID | 所見 | 判定 | 処置 |
|---|---|---|---|
| G1 | WAL の `reason` が自由文 (例 `eval-exception: …: {e}`、`loop.py` の例外経路) を含みうるのに、`outcome` と `verifier_digest.reason` へそのまま写す (焦点 1 must-fix) | real / must-fix | `outcome` と `verifier_digest` の reason は閉じた code 集合 (設計 §3.2 の分類 + 実コードに実在する固定 reason code) に正規化し、集合外・接頭辞つき自由文は固定 code (`eval-exception` など、接頭辞で判別できるものはその接頭辞、判別できないものは `other`) に写す。元の文字列は WAL に残るだけで coder に渡さない |
| G2 | `verifier_digest.anomalies` が verifier の anomaly を全件写す。段階 C の norw 負例では cycle が 39,124 件出ており、coder 入力が際限なく大きくなる (親) | real / must-fix | anomaly は決定的な順序で先頭の固定件数 (8 件) だけを写し、全件数を `anomaly_count` に入れる。各 anomaly の field は現行の 3 つのまま |
| G3 | preview で拒否された候補を履歴に載せる経路が無く、次の coder が自分の拒否理由を受け取れない (規律 3、親) | real / must-fix | `--record-reject <coder だけの file>` を足す: preview と同じ gate を掛け、拒否ならその結果を `L.record_diff_reject` で WAL に書き、iteration を 1 進めて履歴に追記する (outcome = `rejected`、subtype・rule id つき)。gate を通る候補は `ValueError` で止まり何も書かない。build はしない。停止判定・入口停止は run と同じ |
| G4 | runbook の preview 拒否の説明が実装と違う (焦点 1 should) | real | 親が runbook を G3 の手順へ直した (未 commit、fix-2 の後の docs commit に含める) |

## 変異の追加登録

| ID | 壊すもの | 期待 |
|---|---|---|
| M-E15 | reason の正規化を外す (自由文をそのまま写す) | G1 の test (例外自由文が coder 入力に出ない) |
| M-E16 | anomaly の件数上限を外す | G2 の test |
| M-E17 | `--record-reject` が gate を通る候補も記録する | G3 の test (通る候補は拒否して何も書かない) |
