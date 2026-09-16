## 書いた file

[output/insights/2026-09-17/t2228-screening-gate-liveness/launcher/run_screening_liveness.sh](/work/1/SFC/tanab/izanagi/.claude/worktrees/dev-wave-t2228-screening-liveness/output/insights/2026-09-17/t2228-screening-gate-liveness/launcher/run_screening_liveness.sh)

117行。SHA-256:

```text
66f28ca8a1b75e447252ddd1db2a62d201837424f3b43a492d7ceab5ff47557c
```

## 仕様と行の対応

| 項目 | 行 |
|---|---|
| 共通設定・段名と日時出力 | 1–7 |
| 1. 前提検査 | 9–29 |
| 2. Python選定 | 31–42 |
| 3. 単独性の観測・拒否 | 44–67 |
| 4. env供給・cleanup | 69–99 |
| 5. exact argv出力・CLI起動・rc取得 | 101–107 |
| 6. 終了後のtree状態・CLIのrcで終了 | 109–117 |

## 検査

- `bash -n`: 成功。
- `shellcheck`: 無い。
- 130行以内、U+0300〜U+036Fなしを確認。
- 指定資料・先例との静的照合を実施。

## 総括

指定の1ファイルだけを作成しました。**実走していない**ため、計算ノード上の動作は未検証です。commit・branch操作・job投入は行っていません。