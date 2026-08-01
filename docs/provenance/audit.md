# AI provenance — commit 前後の検査と解釈

入口の該当条件が成立したときだけ読む。

## PR-A01 — commit 前の message 検査

message file と staged path を検査し、rc=0 を確認してから commit する。

```bash
python3 tools/check_ai_provenance.py --message-file <path>
```

## PR-A02 — commit 後と範囲監査

導入 commit から `HEAD` までの欠落、排他違反、フィールド順、値と role の形式を検査する。別の範囲は
`--range <range>` を使う。

```bash
python3 tools/check_ai_provenance.py
```

Git の trailer 解釈は `git log -1 --format='%(trailers:key=AI-Agent)'` (範囲版は `--format` に
`%H %s%n` を足す) で補助確認できるが、規範 gate の代用にはしない。導入 commit より前の欠落は legacy
とし、遡及違反にしない。correction を含む範囲の権威は `PR-C03` に従う。

## PR-A03 — 観察データの解釈

この記録は観察データであって統制実験ではない。タスク難度・役割・入力コンテキストが交絡するため、
commit 数や成功率だけから製品・モデル・推論深度の優劣を断定しない。改善判断ではタスク種別を揃え、
手戻り・レビュー finding・テスト結果・所要時間と併せて評価する。
