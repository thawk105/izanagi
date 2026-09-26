# 正規表現の固定 argv 検査と受入起動形の静的集計 (2026-09-26 14:1x JST、親が login で実行)

## 1. 固定 argv 8 行 (live の偽 leader は作らない。他 wave の部分文字列一致の門番に 1 本余分に数えられるため)

入力 (1 行 1 argv、`ps -eo args` と同じ空白連結):

```
1 python3 tools/dev_wave_wait.py acceptance --wave t2838-gate-argv-unify --lease-dir /x
2 /usr/bin/python3 /work/1/SFC/tanab/izanagi/.claude/worktrees/x/tools/dev_wave_wait.py acceptance --wave x
3 bash -c sleep 20 dev_wave_wait.py acceptance
4 codex exec --json -C /w 受入投入は tools/dev_wave_wait.py acceptance --lease-optional を使う
5 python3 tools/dev_wave_wait.py producer --done-file /x
6 /bin/bash /work/1/SFC/tanab/dev-wave-jobs/x/run-acceptance-gated.sh final1
7 python3 -u tools/dev_wave_wait.py acceptance --wave x
8 python3.10 tools/dev_wave_wait.py acceptance --wave x
```

| 行 | 種類 | 裁定の正規表現 `grep -E '^(python3\|[^ ]*/python3?) [^ ]*dev_wave_wait\.py acceptance'` | 部分文字列一致 `grep '[d]ev_wave_wait.py' \| grep ' acceptance'` |
|---|---|---|---|
| 1 | 正例 (相対 path 起動、現行の主形) | 数える | 数える |
| 2 | 正例 (絶対 path の interpreter と script) | 数える | 数える |
| 3 | 負例 (包み shell) | 数えない | **数える** |
| 4 | 負例 (codex 子の prompt 文字列、記憶 2026-09-20 の型) | 数えない | **数える** |
| 5 | 負例 (producer 待ち手) | 数えない | 数えない |
| 6 | 負例 (門番 script 自身) | 数えない | 数えない |
| 7 | `-u` 付き起動 | **数えない** | 数える |
| 8 | 版番号付き interpreter | **数えない** | 数える |

行 7・8 は裁定の正規表現の取りこぼしになりうる形である。下の静的集計では 9/19 以降の起動形に 0 件だった。

## 2. 受入起動形の静的集計 (job dir 直下の `*.sh` / `*.py`、全期間)

`grep -hE 'dev_wave_wait\.py +acceptance'` からコメント・grep 行を除き、先頭の `exec` / `nohup` / `setsid` を外して数えた。

- `python3 tools/dev_wave_wait.py acceptance …` (継続行・引数違いを含む): 1,259 + 38 + 32 (`exec` 付き) + 個別 slug 付きの行多数。正規表現に一致する。
- 例外の形 (正規表現との関係):
  - `/usr/bin/python3 tools/…` 3 行、`python3 /work/1/…/tools/dev_wave_wait.py acceptance` 3 行: 一致する。
  - `timeout 5400 python3 …` 2 行、`VAR=… python3 …` 3 行、`setsid bash -c "… python3 tools/de…"` 2 行: 数える対象の子 process の argv は `python3 tools/…` になり一致する (包み側の argv は interpreter で始まらないので数えない)。
  - `python3.10 tools/dev_wave_wait.py acceptance` 2 行: **一致しない**。所在は `wave-t1403-walltime-sigterm/launch-acceptance.sh` (8/21 00:42) と `launch-acceptance-retry-loop.sh` (8/21 08:32) の 2 file だけ。
  - `python3 -u … dev_wave_wait`: 0 行。
- したがって mtime が 9/19 以降の job dir 直下 script に、正規表現が取りこぼす起動形は無かった。

## 3. 現存する門番 script の leader 行 (新しい順 40 本、9/21 22:30 〜 9/26 13:07)

- 部分文字列一致 `grep '[d]ev_wave_wait.py' | grep ' acceptance'`: 22 本 (うち `count_leaders` 関数型 1 本)。直近は 9/26 10:59 の t2851-transfer-runner、9/26 10:25 の t2865-silo-small-compare。
- 裁定の正規表現 `^(python3|[^ ]*/python3?) [^ ]*dev_wave_wait\.py acceptance`: 6 本 (うち `count_leaders` 関数型 4 本、いずれも rulings-all 系)。
- 狭い先頭一致 `^python3( -u)? tools/dev_wave_wait.py acceptance`: 12 本 (絶対 path 起動を数えない)。

3 系統が並んでいた。雛形の写し元は、裁定の正規表現を使い今日 green まで通った `dev-wave-t2273-shard0-local-copy/run-acceptance-gated.sh` (9/26 13:07、sha256 ae9af50dab8f6a0add23e3ff925f8a6fccd78c566efb3069a8d05e9eb958f4db) にした。
