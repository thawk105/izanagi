## 所見対応表 (G1〜G3: closed / partial / regressed と根拠)

| 所見 | 状態 | 根拠 |
| --- | --- | --- |
| G1 | closed | `--until` を追加。全行の日付復元後に適用し、後続行・started/finished を制限。跨ぐ走行は `end_source=until`。直近 20 wave の集合は保存一覧と一致。 |
| G2 | closed | 全対象 dir の started.txt を独立収集。門番 log の無い `dev-wave-t2802-floor-attempt-recovery` の走行 1 本を追加。 |
| G3 | closed | 複数指定可能な `--exclude-wave` を追加。両本走の母集合・区間・走行記録に自 wave は 0 件。 |

## 実装した内容

変更対象は `tools/gate_wait_probe.py` のみ。git command・commit は実行していません。

- `--until` は JST offset 付き ISO 日時を受け付けます。指定時の選択キーは最後の門番行時刻、省略時は従来の mtime です。
- 日付復元には打切り前の全行と started 錨を使い、その後で観測を制限します。
- 全走査対象 dir から since 日付以降の走行を集め、同時走行数は引き続き wave 単位で重複排除します。
- MD に until・除外 wave・門番 log 有無別の走行区間数を追加しました。
- self-check 4 件の期待値は変更していません。

## 実走した検査 (command と出力の逐語)

構文検査。終了コード 0、出力なし。キャッシュは所有外の repo file を変更しないよう `/tmp` に出しました。

```bash
PYTHONPYCACHEPREFIX=/tmp/gate-wait-probe-fix3/pycache python3 -m py_compile tools/gate_wait_probe.py
```

本走 (1)。終了コード 0。

```bash
python3 tools/gate_wait_probe.py --jobs-root /work/1/SFC/tanab/dev-wave-jobs --since 2026-09-19 --recent-n 20 --until 2026-09-21T07:37:00+09:00 --exclude-wave dev-wave-lease-gate-wait-diagnosis --self-check --out-json /tmp/gate-wait-probe-fix3/until.json --out-md /tmp/gate-wait-probe-fix3/until.md
```

```text
scan directories=100 gate_logs=0
scan directories=200 gate_logs=11
scan directories=300 gate_logs=42
scan directories=400 gate_logs=42
scan directories=500 gate_logs=42
scan directories=600 gate_logs=49
scan directories=700 gate_logs=66
scan directories=800 gate_logs=102
scan directories=900 gate_logs=177
scan directories=1000 gate_logs=177
scan directories=1100 gate_logs=181
scan directories=1200 gate_logs=192
scan directories=1300 gate_logs=192
scan directories=1400 gate_logs=192
gate logs=126 waves=79 segments=467
self-check dev-wave-t2610-fig10: passed [('censored', 3021.0, 2, True, 1), ('observed-wait', 853.0, 0, False, 1)]
self-check dev-wave-t2814-cleanup-command: passed [('observed-wait', 745.0, 0, False, 1), ('observed-wait', 122.0, 0, False, 2)]
self-check dev-wave-paper-story-20260921: passed [('observed-wait', 149.0, 0, False, 1)]
self-check dev-wave-t2243-collection-diag: passed [('observed-wait', 171.0, 0, False, 1), ('observed-wait', 151.0, 0, False, 2)]
JSON: /tmp/gate-wait-probe-fix3/until.json
MD: /tmp/gate-wait-probe-fix3/until.md
```

本走 (2)。終了コード 0。

```bash
python3 tools/gate_wait_probe.py --jobs-root /work/1/SFC/tanab/dev-wave-jobs --since 2026-09-19 --recent-n 20 --exclude-wave dev-wave-lease-gate-wait-diagnosis --self-check --out-json /tmp/gate-wait-probe-fix3/unlimited.json --out-md /tmp/gate-wait-probe-fix3/unlimited.md
```

```text
scan directories=100 gate_logs=0
scan directories=200 gate_logs=14
scan directories=300 gate_logs=47
scan directories=400 gate_logs=47
scan directories=500 gate_logs=47
scan directories=600 gate_logs=54
scan directories=700 gate_logs=71
scan directories=800 gate_logs=107
scan directories=900 gate_logs=182
scan directories=1000 gate_logs=182
scan directories=1100 gate_logs=187
scan directories=1200 gate_logs=199
scan directories=1300 gate_logs=199
scan directories=1400 gate_logs=199
gate logs=133 waves=86 segments=478
self-check dev-wave-t2610-fig10: passed [('censored', 3021.0, 2, True, 1), ('observed-wait', 853.0, 0, False, 1)]
self-check dev-wave-t2814-cleanup-command: passed [('observed-wait', 745.0, 0, False, 1), ('observed-wait', 122.0, 0, False, 2)]
self-check dev-wave-paper-story-20260921: passed [('observed-wait', 149.0, 0, False, 1)]
self-check dev-wave-t2243-collection-diag: passed [('observed-wait', 171.0, 0, False, 1), ('observed-wait', 151.0, 0, False, 2)]
JSON: /tmp/gate-wait-probe-fix3/unlimited.json
MD: /tmp/gate-wait-probe-fix3/unlimited.md
```

保存一覧との集合照合。

```bash
jq --rawfile expected /home/SFC/tanab/.claude/jobs/c8e39534/tmp/verbatim/recent20-waves.txt '($expected | split("\n") | map(select(length > 0))) as $e | {expected_count: ($e | length), actual_count: (.recent_waves | length), expected_only: ($e - .recent_waves), actual_only: (.recent_waves - $e)}' /tmp/gate-wait-probe-fix3/until.json
```

```json
{
  "expected_count": 20,
  "actual_count": 20,
  "expected_only": [],
  "actual_only": []
}
```

## 本走の要点 (上記の節を逐語、recent20 との照合結果)

本走 (1) の直近 20 wave 集合は一致し、差分 wave はありません。選択キーを変更したため一覧の順序には差があります。

以下、本走 (1) の指定箇所を逐語で掲載します。

```markdown
## 母集合と観測区間

母集合は残存門番 log のuntil 以前の最後の門番行の時刻順の wave。landed は選択条件にしない。日付は JST、mtime 復元は (推定)。

since は log mtime の下限。直近 wave 表は since 前も含む全起動回・attempt を保持。観測期間は選択キー期間と別掲。

| 項目 | 値 |
| --- | --- |
| since (log mtime 下限) | 2026-09-19 |
| until | 2026-09-21T07:37:00+09:00 |
| exclude_wave | ["dev-wave-lease-gate-wait-diagnosis"] |
| 門番 file 数 | 126 |
| wave 数 | 79 |
| 直近 wave 数 | 20 |
| 選択キー期間 JST | ["2026-09-20T21:20:32+09:00", "2026-09-21T04:57:50+09:00"] |
| 直近の観測区間 JST | ["2026-09-20T19:45:19+09:00", "2026-09-21T04:57:50+09:00"] |
| 日付未解決 file 数 | 0 |
| mtime 日付復元 file 数 (推定) | 7 |
| observed-wait 数 | 147 |
| censored 数 | 7 |
```

```markdown
## 区間分布

秒。p90 は nearest rank。打切り・日付未解決を observed-wait 分布に混ぜない。

| 母集合/条件 | n | 中央値 | p90 | 最大 | 打切り | 欠測区間 | 拒否 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| recent/all | 34 | 152.5 | 642.0 | 4838.0 | 1 | 0 | 0 |
| recent/maxl<=1 | 33 | 153.0 | 642.0 | 4838.0 | 1 | 0 | 0 |
| recent/other-known | 1 | 141.0 | 141.0 | 141.0 | 0 | 0 | 0 |
| recent/unknown | 0 | unknown | unknown | unknown | 0 | 0 | 0 |
| since/all | 147 | 261.0 | 3157.0 | 9317.0 | 7 | 0 | 27 |
| since/maxl<=1 | 140 | 338.5 | 3157.0 | 9317.0 | 6 | 0 | 27 |
| since/other-known | 6 | 146.0 | 276.0 | 276.0 | 1 | 0 | 0 |
| since/unknown | 1 | 126.0 | 126.0 | 126.0 | 0 | 0 | 0 |
| since-2026-09-19/all | 147 | 261.0 | 3157.0 | 9317.0 | 7 | 0 | 27 |
| since-2026-09-19/maxl<=1 | 140 | 338.5 | 3157.0 | 9317.0 | 6 | 0 | 27 |
| since-2026-09-19/other-known | 6 | 146.0 | 276.0 | 276.0 | 1 | 0 | 0 |
| since-2026-09-19/unknown | 1 | 126.0 | 126.0 | 126.0 | 0 | 0 | 0 |

| 母集合 | wave 観測待ち和の分布 (秒) |
| --- | --- |
| recent | {"max": 5946.0, "median": 316.0, "min": 122.0, "n": 20, "p90": 736.0, "sum": 12507.0} |
| since | {"max": 13639.0, "median": 757.0, "min": 62.0, "n": 79, "p90": 5946.0, "sum": 169319.0} |

| 区間種類 | 分布 (秒) |
| --- | --- |
| retry-prep | {"max": 60.0, "median": 1.0, "min": 0.0, "n": 27, "p90": 60.0, "sum": 783.0} |
| submit-prep | {"max": 349.0, "median": 0.0, "min": 0.0, "n": 143, "p90": 8.0, "sum": 603.0} |
| run | {"max": 2102.0, "median": 670.0, "min": 16.0, "n": 143, "p90": 1404.0, "sum": 101221.0} |
```

F2 の小表と脚注：

```markdown
| 母集合 | leaders-only + both の走行数 | tick 数 | 分 (推定、直前 tick 配分) |
| --- | --- | --- | --- |
| recent | 0 | 0 | 0.0 |
| recent | 1 | 14 | 28.133 |
| recent | ≥2 | 38 | 77.467 |
| since | 0 | 83 | 168.333 |
| since | 1 | 419 | 834.65 |
| since | ≥2 | 526 | 1046.333 |

走行数 ≥2 は実在する走行中の受入との競合。≤1 は記録 leaders と走行数の不一致 (偽 leader・log の無い走行・started/finished の欠落のいずれか、断定しない)。走行終点の rc / 打切り補完は推定であり、競合の照合もその限界を持つ。
```

```text
走行区間の数: 門番 log のある dir 142 / 無い dir 1
```

self-check 節は両本走で同一です。

```markdown
## self-check

実 log の照合。tuple = (kind, 秒, 再カウント拒否, 飢餓候補, attempt)。

| wave | 結果 | 実測 | 期待 |
| --- | --- | --- | --- |
| dev-wave-t2610-fig10 | passed | [["censored", 3021.0, 2, true, 1], ["observed-wait", 853.0, 0, false, 1]] | [["censored", 3021, 2, true, 1], ["observed-wait", 853, 0, false, 1]] |
| dev-wave-t2814-cleanup-command | passed | [["observed-wait", 745.0, 0, false, 1], ["observed-wait", 122.0, 0, false, 2]] | [["observed-wait", 745, 0, false, 1], ["observed-wait", 122, 0, false, 2]] |
| dev-wave-paper-story-20260921 | passed | [["observed-wait", 149.0, 0, false, 1]] | [["observed-wait", 149, 0, false, 1]] |
| dev-wave-t2243-collection-diag | passed | [["observed-wait", 171.0, 0, false, 1], ["observed-wait", 151.0, 0, false, 2]] | [["observed-wait", 171, 0, false, 1], ["observed-wait", 151, 0, false, 2]] |
```

## 波及・未実走・既知の限界

- 所有外 caller・共有 fixture・consumer test の変更は無し。外部 module の追加も無し。
- 本走 (1) の JSON で until より後の event・走行区間は 0 件でした。
- この本走時刻を跨ぐ走行はなく、`end_source=until` 分岐の実データ実走証明はありません。実装と静的確認の範囲です。
- `--claude-jobs-root`、複数除外指定、異常引数は今回の許可された本走では未実走です。
- 門番 log・finished・対応 rc がすべて無く until も無指定なら、走行終点を started で打ち切ります。継続時間は確認できません。
- 走行区間数の行は dir 数ではなく区間数です。既存の区間分布の `run` は GO に対応した区間であり、同時走行数用の全走行母集合とは異なります。
- 子の検査は親の全走を代替しません。報告書 file は作成していません。

出力読取り用の Python command は自動承認レビューに拒否されました。保護パスと不透明構文の併用が理由で、`jq`・`sed` に切り替えて照合を完了しました。

## 総括

G1〜G3 を実装し、指定本走 2 本は終了コード 0、self-check は双方 4 件 passed。07:37 打切りの直近 20 wave 集合は保存一覧と完全一致しました。