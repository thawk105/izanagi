## 実装した内容

`tools/gate_wait_probe.py` のみ新規作成しました。標準 library のみで自己完結し、ログ走査、日付復元、5 種の区間分割、条件と出所、閉門理由、同時待ち・同時 GO、飢餓候補、感度分析、JSON/MD 出力、実ログ self-check を実装しました。

commit・git command は実行していません。

## 実走した検査 (command と出力の逐語)

構文検査：rc=0、出力なし。

```bash
PYTHONPYCACHEPREFIX=/tmp/gate-wait-probe-selfrun/pycache python3 -m py_compile tools/gate_wait_probe.py
```

最終版の本走：rc=0。

```bash
python3 tools/gate_wait_probe.py --jobs-root /work/1/SFC/tanab/dev-wave-jobs --since 2026-09-19 --recent-n 20 --out-json /tmp/gate-wait-probe-selfrun/verified.json --out-md /tmp/gate-wait-probe-selfrun/verified.md --self-check
```

```text
scan directories=100 gate_logs=0
scan directories=200 gate_logs=11
scan directories=300 gate_logs=42
scan directories=400 gate_logs=42
scan directories=500 gate_logs=42
scan directories=600 gate_logs=49
scan directories=700 gate_logs=67
scan directories=800 gate_logs=102
scan directories=900 gate_logs=177
scan directories=1000 gate_logs=177
scan directories=1100 gate_logs=181
scan directories=1200 gate_logs=192
scan directories=1300 gate_logs=192
gate logs=126 waves=79 segments=389
self-check dev-wave-t2610-fig10: passed [('censored', 3021.0, 2, True, 1), ('observed-wait', 853.0, 0, False, 1)]
self-check dev-wave-t2814-cleanup-command: passed [('observed-wait', 745.0, 0, False, 1), ('observed-wait', 122.0, 0, False, 2)]
JSON: /tmp/gate-wait-probe-selfrun/verified.json
MD: /tmp/gate-wait-probe-selfrun/verified.md
```

## self-check と本走の要点 (MD の該当節を逐語)

```markdown
## 母集合と観測区間

母集合は残存門番 log の最終 mtime 順の wave。landed は選択条件にしない。日付は JST、mtime 復元は (推定)。

since は log mtime の下限。直近 wave 表は since 前も含む全起動回・attempt を保持。観測期間は選択キー期間と別掲。

| 項目 | 値 |
| --- | --- |
| since (log mtime 下限) | 2026-09-19 |
| 門番 file 数 | 126 |
| wave 数 | 79 |
| 直近 wave 数 | 20 |
| 選択キー期間 JST | ["2026-09-20T21:29:53+09:00", "2026-09-21T05:20:47+09:00"] |
| 直近の観測区間 JST | ["2026-09-20T19:45:19+09:00", "2026-09-21T04:57:50+09:00"] |
| 日付未解決 file 数 | 0 |
| mtime 日付復元 file 数 (推定) | 38 |
| observed-wait 数 | 108 |
| censored 数 | 46 |
```

```markdown
## self-check

実 log の照合。tuple = (kind, 秒, 再カウント拒否, 飢餓候補, attempt)。

| wave | 結果 | 実測 | 期待 |
| --- | --- | --- | --- |
| dev-wave-t2610-fig10 | passed | [["censored", 3021.0, 2, true, 1], ["observed-wait", 853.0, 0, false, 1]] | [["censored", 3021, 2, true, 1], ["observed-wait", 853, 0, false, 1]] |
| dev-wave-t2814-cleanup-command | passed | [["observed-wait", 745.0, 0, false, 1], ["observed-wait", 122.0, 0, false, 2]] | [["observed-wait", 745, 0, false, 1], ["observed-wait", 122, 0, false, 2]] |
```

## 波及・未実走・既知の限界

- 所有外 caller・共有 fixture・consumer test への波及：無し。既存 file・テストは変更していません。
- `--claude-jobs-root` を含む親の全走は未実走です。今回の子の実走は代替しません。
- script 条件は現存版からの読取りです。過去版・landed 状態は証明できません。
- 24 時間以上の無記録空白は時刻文字列だけでは識別できません。感度分析は効果見積りではありません。
- 出力と pycache は `/tmp/gate-wait-probe-selfrun/` 内です。worktree 内の scratch dir は作成していません。

## 総括

実装・指定範囲の本走を完了しました。正例 T-2610、負例 T-2814 はともに指定値に一致し、最終版は警告なし・rc=0 です。