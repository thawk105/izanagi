## 所見対応表 (F1〜F5: closed / partial / regressed と根拠)

| 所見 | 判定 | 根拠 |
| --- | --- | --- |
| F1 | closed | 全 since 対象ディレクトリの走行記録を tick ごとに照合。3 field と MD の2列を追加。指定区間の最大走行数=2、GO直前=1、差=0。 |
| F2 | closed | leaders-only + both を走行数 0 / 1 / ≥2 に分類し、recent / since の tick 数・推定分・指定脚注を出力。 |
| F3 | closed | GO 時点値と同時待ち・同時 GO の両表の前に、recent / since の要約表を追加。 |
| F4 | closed | 既存候補表を保持し、直後に母集合別の長時間待ち・飢餓候補・censored 件数表を追加。 |
| F5 | closed | 時間帯表の observed-wait n=0 行を省略。指定脚注を追加し、本走出力で確認。 |

## 実装した内容

編集対象は `tools/gate_wait_probe.py` のみ。commit・git command は実行していません。self-check 4 件の期待値、既存の log 受理条件・待ち区間分割・飢餓候補判定は変更していません。

走行照合には同ディレクトリの全 `acceptance-*.started.txt` を使用し、`started ≤ tick < finished` の他 wave 数を重複排除して計算します。finished 欠落時は対応 GO 後の同 attempt の rc、それも無ければ同ディレクトリの最終観測時刻 / log mtime で打ち切ります。補完の出所は JSON に保持します。

各 tick に走行数と照合先 wave 名、区間に指定の3 field、JSON に field 説明と走行区間一覧を追加しました。censored の GO 直前値は null です。「照合可否」は当該起動の GO に対応する記録で判定します。

## 実走した検査 (command と出力の逐語)

構文検査は初回・最終版とも同じ command で実行し、終了コード 0、出力なしでした。所有外へのキャッシュ書込みを避けるため、出力先を `/tmp` に指定しました。

```bash
PYTHONPYCACHEPREFIX=/tmp/gate-wait-probe-fix2/pycache python3 -m py_compile tools/gate_wait_probe.py
```

本走も以下の同一 command を2回実行し、いずれも終了コード 0 でした。

```bash
python3 tools/gate_wait_probe.py --jobs-root /work/1/SFC/tanab/dev-wave-jobs --since 2026-09-19 --recent-n 20 --self-check --out-json /tmp/gate-wait-probe-fix2/final.json --out-md /tmp/gate-wait-probe-fix2/final.md
```

初回出力：

```text
scan directories=100 gate_logs=0
scan directories=200 gate_logs=13
scan directories=300 gate_logs=45
scan directories=400 gate_logs=45
scan directories=500 gate_logs=45
scan directories=600 gate_logs=52
scan directories=700 gate_logs=69
scan directories=800 gate_logs=105
scan directories=900 gate_logs=180
scan directories=1000 gate_logs=180
scan directories=1100 gate_logs=184
scan directories=1200 gate_logs=196
scan directories=1300 gate_logs=196
scan directories=1400 gate_logs=196
gate logs=130 waves=83 segments=473
self-check dev-wave-t2610-fig10: passed [('censored', 3021.0, 2, True, 1), ('observed-wait', 853.0, 0, False, 1)]
self-check dev-wave-t2814-cleanup-command: passed [('observed-wait', 745.0, 0, False, 1), ('observed-wait', 122.0, 0, False, 2)]
self-check dev-wave-paper-story-20260921: passed [('observed-wait', 149.0, 0, False, 1)]
self-check dev-wave-t2243-collection-diag: passed [('observed-wait', 171.0, 0, False, 1), ('observed-wait', 151.0, 0, False, 2)]
JSON: /tmp/gate-wait-probe-fix2/final.json
MD: /tmp/gate-wait-probe-fix2/final.md
```

「照合可否」修正後の最終版出力：

```text
scan directories=100 gate_logs=0
scan directories=200 gate_logs=13
scan directories=300 gate_logs=45
scan directories=400 gate_logs=45
scan directories=500 gate_logs=45
scan directories=600 gate_logs=52
scan directories=700 gate_logs=69
scan directories=800 gate_logs=105
scan directories=900 gate_logs=180
scan directories=1000 gate_logs=180
scan directories=1100 gate_logs=185
scan directories=1200 gate_logs=197
scan directories=1300 gate_logs=197
scan directories=1400 gate_logs=197
gate logs=131 waves=84 segments=474
self-check dev-wave-t2610-fig10: passed [('censored', 3021.0, 2, True, 1), ('observed-wait', 853.0, 0, False, 1)]
self-check dev-wave-t2814-cleanup-command: passed [('observed-wait', 745.0, 0, False, 1), ('observed-wait', 122.0, 0, False, 2)]
self-check dev-wave-paper-story-20260921: passed [('observed-wait', 149.0, 0, False, 1)]
self-check dev-wave-t2243-collection-diag: passed [('observed-wait', 171.0, 0, False, 1), ('observed-wait', 151.0, 0, False, 2)]
JSON: /tmp/gate-wait-probe-fix2/final.json
MD: /tmp/gate-wait-probe-fix2/final.md
```

## 本走の要点 (新しい要約表と paper-story-20260920b 区間 1 の record を逐語)

以下は最終版出力からの逐語です。

**母集合と観測区間**

母集合は残存門番 log の最終 mtime 順の wave。landed は選択条件にしない。日付は JST、mtime 復元は (推定)。

since は log mtime の下限。直近 wave 表は since 前も含む全起動回・attempt を保持。観測期間は選択キー期間と別掲。

| 項目 | 値 |
| --- | --- |
| since (log mtime 下限) | 2026-09-19 |
| 門番 file 数 | 131 |
| wave 数 | 84 |
| 直近 wave 数 | 20 |
| 選択キー期間 JST | ["2026-09-20T22:32:01+09:00", "2026-09-21T08:34:58+09:00"] |
| 直近の観測区間 JST | ["2026-09-20T21:53:51+09:00", "2026-09-21T08:34:55+09:00"] |
| 日付未解決 file 数 | 0 |
| mtime 日付復元 file 数 (推定) | 11 |
| observed-wait 数 | 149 |
| censored 数 | 10 |

**F2：閉門理由内訳の追加表**

| 母集合 | leaders-only + both の走行数 | tick 数 | 分 (推定、直前 tick 配分) |
| --- | --- | --- | --- |
| recent | 0 | 0 | 0.0 |
| recent | 1 | 0 | 0.0 |
| recent | ≥2 | 11 | 22.15 |
| since | 0 | 83 | 168.333 |
| since | 1 | 449 | 893.05 |
| since | ≥2 | 496 | 987.933 |

走行数 ≥2 は実在する走行中の受入との競合。≤1 は記録 leaders と走行数の不一致 (偽 leader・log の無い走行・started/finished の欠落のいずれか、断定しない)。走行終点の rc / 打切り補完は推定であり、競合の照合もその限界を持つ。

**F3：GO 時点値の要約**

| 母集合 | GO 数 | GO 直前 leaders 値:件数 | recount leaders 値:件数 | GO 直前 load1 中央値 | p90 | 最大 |
| --- | --- | --- | --- | --- | --- | --- |
| recent | 29 | 0.0: 16; 1.0: 13 | 0.0: 18; 1.0: 11 | 4.14 | 6.98 | 15.49 |
| since | 149 | 0.0: 50; 1.0: 93; 2.0: 6 | 0.0: 48; 1.0: 88; 2.0: 6; 欠測: 7 | 6.56 | 16.91 | 39.54 |

**F3：同時待ち・同時 GO の要約**

| 母集合 | GO 直前同時待ち 値:件数 | 区間最大同時待ち 値:件数 (打切り含む) | 同時 GO ±120秒 値:件数 | 走行数 (GO 直前) 値:件数 |
| --- | --- | --- | --- | --- |
| recent | 0: 25; 1: 4 | 0: 23; 1: 10 | 0: 25; 1: 4 | 0: 18; 1: 11 |
| since | 0: 61; 1: 20; 2: 17; 3: 17; 4: 13; 5: 12; 6: 4; 7: 2; 8: 1; 9: 2 | 0: 51; 1: 23; 2: 11; 3: 21; 4: 10; 5: 20; 6: 11; 7: 1; 8: 1; 9: 10 | 0: 95; 1: 50; 3: 4 | 0: 77; 1: 69; 2: 3 |

**F4：飢餓候補と長時間待ちの件数要約**

| 母集合 | 長時間待ち n | 飢餓候補 n | うち censored n (飢餓候補) | censored n (長時間待ち) |
| --- | --- | --- | --- | --- |
| recent | 0 | 0 | 0 | 0 |
| since | 39 | 5 | 2 | 3 |
| since-2026-09-19 | 39 | 5 | 2 | 3 |

**paper-story-20260920b 区間 1：record の識別項目と指定 field の抽出出力**

```json
{
  "wave": "dev-wave-paper-story-20260920b",
  "file": "/work/1/SFC/tanab/dev-wave-jobs/dev-wave-paper-story-20260920b/acceptance-final.chain.log",
  "segment_id": 1,
  "kind": "observed-wait",
  "start": "2026-09-20T19:45:19+09:00",
  "end": "2026-09-20T21:05:57+09:00",
  "seconds": 4838,
  "concurrent_run_max": 2,
  "concurrent_run_pre_go": 1,
  "leaders_minus_runs_pre_go": 0
}
```

**self-check**

実 log の照合。tuple = (kind, 秒, 再カウント拒否, 飢餓候補, attempt)。

| wave | 結果 | 実測 | 期待 |
| --- | --- | --- | --- |
| dev-wave-t2610-fig10 | passed | [["censored", 3021.0, 2, true, 1], ["observed-wait", 853.0, 0, false, 1]] | [["censored", 3021, 2, true, 1], ["observed-wait", 853, 0, false, 1]] |
| dev-wave-t2814-cleanup-command | passed | [["observed-wait", 745.0, 0, false, 1], ["observed-wait", 122.0, 0, false, 2]] | [["observed-wait", 745, 0, false, 1], ["observed-wait", 122, 0, false, 2]] |
| dev-wave-paper-story-20260921 | passed | [["observed-wait", 149.0, 0, false, 1]] | [["observed-wait", 149, 0, false, 1]] |
| dev-wave-t2243-collection-diag | passed | [["observed-wait", 171.0, 0, false, 1], ["observed-wait", 151.0, 0, false, 2]] | [["observed-wait", 171, 0, false, 1], ["observed-wait", 151, 0, false, 2]] |

## 波及・未実走・既知の限界

- 所有外 caller・共有 fixture・consumer test へのコード変更は無し。Python ファイルの静的検索でも本 script の参照は検出されませんでした。
- JSON に field と走行区間一覧を追加し、MD の列・要約表を変更しています。親が出力を取り込む際の変更点です。
- 最終本走で収集した走行区間はすべて finished.txt を持っていました。rc 補完・走行打切りの分岐は実装・静的確認済みですが、今回の実データでは実行されていません。
- 入力は走査中にも更新されました。親保存版や初回本走との母集合・件数差は、同一入力による比較ではありません。
- log・started/finished の欠落は走行数に影響します。leaders との差を偽 leader の断定には使用しません。
- 許可された構文検査と本走以外のテスト・受入全走は未実走です。子の実走は親の全走を代替しません。

## 総括

F1〜F5 を実装し、最終版の構文検査・本走は終了コード 0、self-check 4 件すべて passed でした。成果物は `/tmp/gate-wait-probe-fix2/final.json` と `/tmp/gate-wait-probe-fix2/final.md` です。