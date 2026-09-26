# 採用前の一致実測 — 走行中の受入 process の argv と裁定の正規表現 (2026-09-26 14:35〜14:36 JST、login、親が実行)

## 方法

1. 出現待ち: `until pgrep -f 'dev_wave_wait\.py acceptance' > /dev/null; do sleep 30; done` (14:03 に張り、14:35:40 に成立)。
   pattern の `\.` により、待ち手自身の argv (`dev_wave_wait\.py` と逆斜線入り) は一致しない。
2. 真の leader (正規表現と独立な判定): 全 `/proc/<pid>/cmdline` を NUL で引数に分け、「argv[0] の basename が `python` で始まり、basename が
   `dev_wave_wait.py` の引数の直後の引数が `acceptance`」の pid。
3. 比較: 同じ実行の直前に取った `ps -eo pid=,args=` に、門番と同じ GNU grep (`/usr/bin/grep`) で
   `^ *[0-9]+ (python3|[^ ]*/python3?) [^ ]*dev_wave_wait\.py acceptance` (pid 列付きの ps 出力に合わせて先頭に pid を足しただけで、argv 部分は裁定の正規表現と同じ) を当てた。

## 結果

| 取得 | 時刻 (JST) | 真の leader (cmdline) | 正規表現の一致 | 見逃し | 誤検出 |
|---|---|---|---|---|---|
| 1 回目 (別々の実行) | cmdline 14:35:55、ps 14:36:14 | {2659242} | 1 行 (pid 2659242) | 0 | 0 |
| 2 回目 (同じ実行内、ps → cmdline 走査) | 14:36:23.44 〜 14:36:32.38 | {2659242} | {2659242} | 0 | 0 |

同時刻の部分文字列一致 (`grep '[d]ev_wave_wait.py' | grep ' acceptance'`) も 1 本だった (codex 子の prompt に語を含む process はこの瞬間に無かった)。

pid 2659242 の argv (先頭 300 字、process 表 2,064 行の中の 1 行):

```
python3 tools/dev_wave_wait.py acceptance --wave dev-wave-comsys2026-t2864-refs-sec7 --lease-dir /work/1/SFC/tanab/dev-wave-jobs/land-lease --lease-optional --receipt-file /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2864-comsys-refs-sec7/acceptance-receipt-final-1.json --log-file /work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2864-comsys-refs-sec7/acceptance-child-final-1.log -- python3 tools/run
```

同じ表で `dev_wave_wait` を含む他の行は、producer 待ち手 3 本 (`python3 tools/dev_wave_wait.py producer …`、正規表現は `acceptance` を要求するので数えない)
と、Claude の Bash 包み shell (`/bin/bash -c source …`、interpreter で始まらない)、親自身の静的集計の `ugrep … -rhoE [^|;&(]*dev_wave_wait\.py acceptance …`
(逆斜線入り、interpreter で始まらない。直後に停止した) だけだった。受入 leader の子 (`tools/acceptance_launcher.py`) の argv は
`dev_wave_wait.py acceptance` を含まないので、現行版の waiter では 1 本の受入が 2 本に数えられる経路は見当たらない (`tools/dev_wave_wait.py` の `_LAUNCHER_BOOTSTRAP` を読んで確認。
過去の版は確かめていない)。

process 表の全文は repo に入れず `/work/1/SFC/tanab/dev-wave-jobs/dev-wave-t2838-gate-argv-unify/probe-pre/ps-snap-143623.txt` (と 14:36:14 の `ps-snap-143614.txt`) に置いた。

## 判定

見逃し 0・誤検出 0 で、段 4 裁定の採用条件を満たした。雛形を 14:36:53 に `_shared-templates/` へ置いた (= 採用)。

## 限界

- 1 回の実測で、走っていた受入は 1 本 (起動形は `python3 tools/…` の主形) だけだった。`/usr/bin/python3 /abs/…` 形の実走は観測していない (固定 argv では一致を確認)。
- `python3 -u …`・`python3.10 …` 起動は正規表現が数えない (`regex-fixture-and-launch-forms.md`)。9/19 以降の起動形に該当は無かった。
- 真の leader の判定もテストが起動する本物の waiter (`orchestrator/tests/test_dev_wave_wait.py`・`test_dev_wave_land.py` は `sys.executable <tmp>/tools/dev_wave_wait.py acceptance …` を子で起動する。login の `sys.executable` は `/usr/bin/python3`) を leader と数える。login で焦点走をしている間は、どちらの判定でも受入でない leader が数えられうる (この実測の瞬間には無かった)。
