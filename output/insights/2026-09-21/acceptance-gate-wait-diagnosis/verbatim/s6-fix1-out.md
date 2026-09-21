## 所見対応表 (M1〜M5, S1: closed / partial / regressed と根拠)

| 所見 | 判定 | 根拠 |
| --- | --- | --- |
| M1 | closed | `tip=` 型 GO 39行を認識。追加 self-check 2件 passed、両 file の日付は `anchored`。直近20の打切りは12→1件。 |
| M2 | closed | `recount after …` の実例2件を `recount` と認識。数値による拒否判定は既存経路を共有。T-2610 の拒否2回も維持。 |
| M3 | closed | GO表を recount leaders/load1 に分列。条件表を指定列へ展開し、JSONの詳細 field を保持。 |
| M4 | closed | 差を代替模型−実条件模型へ変更。基準行は全統計0秒。実GOとの差、min、合計を別掲。 |
| M5 | closed | receipt実在とland記録の単語検索を分離。yes/no/no-file と出所脚注を出力。 |
| S1 | closed | 指定情報行を `info` に分類。本走対象は info=214、other=0。逐語はJSONに保持。 |

## 実装した内容

変更は `tools/gate_wait_probe.py` のみ。commit・git command は実行していません。既存 self-check 2件の期待値は変更していません。

GO・recount の認識を拡張し、rc行の扱いを維持しました。感度分析は共通の候補tick探索処理を使い、各tickのlog/script条件から基準 `b0` を求めます。基準不明または成立機会のない区間は差の分布から除外します。

M2の実例2件は、指定された `rulings-all-*` ではなく次のfileにありました。

- `dev-wave-mocc-witlight-arm-run/acceptance-final-1.chain.log`
- `dev-wave-mocc-witlight-results/acceptance-final-1.chain.log`

両行とも leaders=1、maxl=1、拒否0として本走JSONに保持されています。

## 実走した検査 (command と出力の逐語)

構文検査。rc=0、stdout/stderrなし。bytecodeは所有外のworktree fileを作らないよう `/tmp` へ配置しました。

```bash
PYTHONPYCACHEPREFIX=/tmp/gate-wait-probe-fix1/pycache python3 -m py_compile tools/gate_wait_probe.py
```

本走。rc=0。

```bash
python3 tools/gate_wait_probe.py --jobs-root /work/1/SFC/tanab/dev-wave-jobs --since 2026-09-19 --recent-n 20 --self-check --out-json /tmp/gate-wait-probe-fix1/run-0919.json --out-md /tmp/gate-wait-probe-fix1/run-0919.md
```

stdout/stderr逐語：

```text
scan directories=100 gate_logs=0
scan directories=200 gate_logs=12
scan directories=300 gate_logs=43
scan directories=400 gate_logs=43
scan directories=500 gate_logs=43
scan directories=600 gate_logs=50
scan directories=700 gate_logs=68
scan directories=800 gate_logs=103
scan directories=900 gate_logs=178
scan directories=1000 gate_logs=178
scan directories=1100 gate_logs=182
scan directories=1200 gate_logs=193
scan directories=1300 gate_logs=193
gate logs=127 waves=80 segments=469
self-check dev-wave-t2610-fig10: passed [('censored', 3021.0, 2, True, 1), ('observed-wait', 853.0, 0, False, 1)]
self-check dev-wave-t2814-cleanup-command: passed [('observed-wait', 745.0, 0, False, 1), ('observed-wait', 122.0, 0, False, 2)]
self-check dev-wave-paper-story-20260921: passed [('observed-wait', 149.0, 0, False, 1)]
self-check dev-wave-t2243-collection-diag: passed [('observed-wait', 171.0, 0, False, 1), ('observed-wait', 151.0, 0, False, 2)]
JSON: /tmp/gate-wait-probe-fix1/run-0919.json
MD: /tmp/gate-wait-probe-fix1/run-0919.md
```

M2実例の検索：

```bash
rg --no-ignore -n 'recount after' /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/acceptance-final-1.chain.log /work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-results/acceptance-final-1.chain.log
```

```text
/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-results/acceptance-final-1.chain.log:3:07:59:32 recount after 30s: leaders=1 (cond <=1)
/work/1/SFC/tanab/dev-wave-jobs/dev-wave-mocc-witlight-arm-run/acceptance-final-1.chain.log:19:00:07:08 recount after 9s: leaders=1 (cond <=1)
```

## self-check と本走の要点 (MD の該当節を逐語)

母集合節の逐語：

```text
## 母集合と観測区間

母集合は残存門番 log の最終 mtime 順の wave。landed は選択条件にしない。日付は JST、mtime 復元は (推定)。

since は log mtime の下限。直近 wave 表は since 前も含む全起動回・attempt を保持。観測期間は選択キー期間と別掲。

| 項目 | 値 |
| --- | --- |
| since (log mtime 下限) | 2026-09-19 |
| 門番 file 数 | 127 |
| wave 数 | 80 |
| 直近 wave 数 | 20 |
| 選択キー期間 JST | ["2026-09-20T21:44:12+09:00", "2026-09-21T08:13:04+09:00"] |
| 直近の観測区間 JST | ["2026-09-20T19:45:19+09:00", "2026-09-21T08:13:04+09:00"] |
| 日付未解決 file 数 | 0 |
| mtime 日付復元 file 数 (推定) | 7 |
| observed-wait 数 | 148 |
| censored 数 | 7 |
```

直近20の分布行の逐語：

```text
| 母集合/条件 | n | 中央値 | p90 | 最大 | 打切り | 欠測区間 | 拒否 |
| --- | --- | --- | --- | --- | --- | --- | --- |
| recent/all | 33 | 152.0 | 642.0 | 4838.0 | 1 | 0 | 0 |
```

親の出力では打切り12件、本走では1件です。ただし入力は126→127 file、79→80 waveへ増加し、直近20には `dev-wave-dwm08-selfrun-probe` が加わっています。

感度分析節の逐語：

```text
## sensitivity (仮定付き参考模型、効果見積りではない)

連続2 tickと直後の記録 recount (無ければ直前 tick の leaders (推定))。b0 は各 tick の実条件 (log/script の maxl・maxload) を同じ模型へ適用した候補 tick。差は代替候補 tick − b0 秒、負なら早く開いたであろう。

実 GO − b0 は jitter + recount の実費等を含む模型と実の差として別掲。pigz、他 wave の応答、jitter・位相・FIFO の効果は模型に含めない。基準不明・成立機会なしは差の分布から除外。

| 母集合 | 条件 | n | min | 中央値 | p90 | 最大 | 合計 (秒) | 基準不明・成立機会なし |
| --- | --- | --- | --- | --- | --- | --- | --- | --- |
| recent | 実条件 = 模型基準 | 33 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 0 |
| recent | maxl=1,maxload=60 | 32 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 1 |
| recent | maxl=1,maxload=80 | 32 | -932.0 | 0.0 | 0.0 | 0.0 | -932.0 | 1 |
| recent | maxl=2,maxload=60 | 33 | -4685.0 | 0.0 | 0.0 | 0.0 | -7375.0 | 0 |
| recent | maxl=2,maxload=80 | 33 | -4685.0 | 0.0 | 0.0 | 0.0 | -7491.0 | 0 |
| recent | maxl=3,maxload=60 | 33 | -4685.0 | 0.0 | 0.0 | 0.0 | -7375.0 | 0 |
| recent | maxl=3,maxload=80 | 33 | -4685.0 | 0.0 | 0.0 | 0.0 | -7491.0 | 0 |
| recent | 実 GO − b0 | 33 | 2.0 | 20.0 | 39.0 | 44.0 | 683.0 | 0 |
| since | 実条件 = 模型基準 | 142 | 0.0 | 0.0 | 0.0 | 0.0 | 0.0 | 6 |
| since | maxl=1,maxload=60 | 136 | -602.0 | 0.0 | 0.0 | 0.0 | -602.0 | 12 |
| since | maxl=1,maxload=80 | 136 | -1881.0 | 0.0 | 0.0 | 0.0 | -5728.0 | 12 |
| since | maxl=2,maxload=60 | 142 | -9181.0 | 0.0 | 0.0 | 0.0 | -132794.0 | 6 |
| since | maxl=2,maxload=80 | 142 | -9181.0 | -114.5 | 0.0 | 0.0 | -133804.0 | 6 |
| since | maxl=3,maxload=60 | 142 | -9181.0 | -55.0 | 0.0 | 0.0 | -135276.0 | 6 |
| since | maxl=3,maxload=80 | 142 | -9181.0 | -119.5 | 0.0 | 0.0 | -136286.0 | 6 |
| since | 実 GO − b0 | 142 | 0.0 | 20.0 | 41.0 | 1046.0 | 5108.0 | 6 |
```

行分類集計の逐語：

```text
| 分類 | 行数 |
| --- | --- |
| info | 214 |
| other | 0 |
```

self-check節の逐語：

```text
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

- 所有外caller・共有fixture・consumer testへの変更波及：無し。親が複製するprobeの出力が変わります。
- pytest・受入全走・claude-jobs側の本走は未実走。今回の検査は親の全走を代替しません。
- M2新変種の実例は両方とも非拒否です。拒否経路は既存実ログのT-2610とrulings-all-20260920で各2回を確認しました。
- 感度分析は記録tick上の模型です。`実 GO − b0` をすべてjitterだけに帰属させません。
- land-logのyesは単語の存在を示し、land成功の断定ではありません。
- 出力とbytecodeは `/tmp/gate-wait-probe-fix1/`。worktree内scratchは作成していません。全rootへの補助検索は実例特定後に中断しました。

## 総括

M1〜M5・S1を修正し、許可された本走はrc=0、self-checkは4件すべてpassedです。既存期待値を維持し、打切りの減少と模型基準差0秒を確認しました。